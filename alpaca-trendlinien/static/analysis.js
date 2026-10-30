/* Analysis cutoff and immutable automatic-line snapshots. */
function bundleKey(symbol, asOf, enabled = state.analysisEnabled) {
  return (
    symbol +
    "|" +
    (asOf || "live") +
    "|" +
    (state.datasetId || "") +
    "|random=" + (state.randomId || "") +
    "|" +
    (state.researchTrial || "") +
    "|" +
    (state.researchVariant || "") +
    "|analysis=" + (enabled ? "1" : "0") +
    (state.analysisEngine && state.analysisEngine !== "legacy" ? "|engine=" + state.analysisEngine : "") +
    (state.fanCase ? "|fan_case=" + state.fanCase + "|fan_job=" + state.fanJob : "")
  );
}
function hasToriAnalysis() {
  return !!(state.analysisEnabled && state.data &&
    state.data.analysisEnabled !== false && Object.keys(state.data.lanes || {}).length);
}
function analysisLabel(asOf) {
  return state.analysisEnabled
    ? (asOf ? "Historische Tori-Analyse" : "Tori-Analyse laden")
    : (asOf ? "Historische Kursdaten" : "Kursdaten laden");
}
function updateToriControls() {
  const ready = hasToriAnalysis();
  const button = $("#tori-analysis");
  button.textContent = `Tori-Analyse: ${state.analysisEnabled ? "An" : "Aus"}`;
  button.setAttribute("aria-pressed", String(state.analysisEnabled));
  button.title = state.analysisEnabled
    ? "Automatische Tori-Linien, Marker und Infobox ausschalten"
    : "Automatische Tori-Analyse einschalten";
  button.disabled = state.stepping || state.freezing || !$("#loading").hidden;
  $("#analysis-engine").disabled = state.stepping || state.freezing || !$("#loading").hidden || !!state.fanCase;
  $("#info-panel").hidden = !ready || !state.info;
  $("#info-button").hidden = !ready;
  $("#info-button").setAttribute("aria-pressed", String(ready && state.info));
  $("#freeze-button").hidden = !state.analysisEnabled && !state.frozen;
  $("#freeze-button").textContent = state.freezing ? "Fixiere …" : state.frozen ? "Fixierung lösen · Mitlaufen" : "Linien jetzt fixieren";
  if (state.researchJob) $("#freeze-button").textContent = state.data?.researchSetup ? "Signal fixiert" : "Forschungsfall";
  $("#freeze-button").setAttribute("aria-pressed", String(!!state.frozen));
  $("#axis-mode").hidden = !state.analysisEnabled;
  $("#freeze-button").disabled = (!ready && !state.frozen) || state.stepping || state.freezing || !$("#loading").hidden || !!state.researchJob || !!state.fanCase;
}
async function toggleToriAnalysis() {
  if (state.stepping || state.freezing) return;
  if (state.analysisEnabled) {
    const bundle = currentBundle();
    state.analysisEnabled = false;
    ++state.request;
    $("#loading").hidden = true;
    $("#error").hidden = true;
    $("#details-dialog").close();
    if (bundle) state.bundles.set(bundleKey(state.symbol, state.asOf), bundle);
    automaticLines();
    table();
    updateAnalysisControls();
    if (state.includeLines) chart.priceScale("right").applyOptions({ autoScale: true });
    updateStepButtons();
    return;
  }
  state.analysisEnabled = true;
  state.info = true;
  state.infoCollapsed = false;
  updateToriControls();
  const request = state.request + 1;
  if (!(await load(state.symbol, false, state.asOf, true)) && request === state.request) {
    state.analysisEnabled = false;
    automaticLines();
    table();
    updateAnalysisControls();
  }
}
function currentBundle() {
  return state.bundles.get(bundleKey(state.symbol, state.asOf));
}
function isoCutoff(bundle) {
  return bundle.historical
    ? new Date(bundle.analysisCutoff * 1000).toISOString()
    : null;
}
function asRay(ray) {
  return {
    a: { time: ray.a_time, price: ray.a_price, logical: ray.chartPositions?.a },
    b: { time: ray.b_time, price: ray.b_price, logical: ray.chartPositions?.b },
  };
}
function chartProjection(ray, time, axis) {
  return RayGeometry.candleValue(axis, asRay(ray), time);
}
function fixedChartPositions(ray, frozen, tf) {
  const axis = frozen.payload.charts[tf].bars.map((bar) => bar.time);
  return {
    a: RayGeometry.logicalAt(axis, ray.a_time),
    b: RayGeometry.logicalAt(axis, ray.b_time),
  };
}
function frozenBoundary(frozen) {
  return Math.max(frozen.validFrom, frozen.analysisCutoff || 0);
}
function activeFrozen() {
  return state.analysisEnabled === false ? null : state.frozen;
}
function assertFrozenCompatible(bundle, frozen) {
  if (!frozen) return;
  if ((frozen.payload.analysisEngine || "legacy") !== (bundle.analysisEngine || "legacy"))
    throw Error("Fixierung und Chart verwenden unterschiedliche Linienfinder.");
  if (frozen.symbol !== bundle.symbol || frozen.basis !== "bars")
    throw Error(
      "Dieser Stand gehört nicht zur aktuellen Aktie oder Linienbasis.",
    );
  if ((frozen.payload.datasetId || null) !== (bundle.datasetId || null) ||
      (frozen.payload.randomCase?.id || null) !== (bundle.randomCase?.id || null))
    throw Error("Fixierung und Chart gehören zu unterschiedlichen Datenbeständen oder Replay-Fällen.");
  if (frozenBoundary(frozen) > bundle.analysisCutoff)
    throw Error(
      "Der fixierte Stand enthält später abgeschlossene Kerzen als der gewählte Zeitpunkt. Bitte zuerst die Fixierung lösen oder einen früheren Stand öffnen.",
    );
  for (const tf of ["1h", "4h", "1D"]) {
    const old = frozen.payload.charts[tf].bars,
      fresh = bundle.charts[tf].bars;
    if (fresh[0].time > old.at(-1).end)
      throw Error(
        "Zwischen dem fixierten Stand und der geladenen Historie liegt eine Datenlücke. Den gespeicherten Stand zunächst über „Datum“ öffnen und einen näheren Zeitpunkt wählen.",
      );
  }
}
function snapshotChart(bundle, tf) {
  const frozen = activeFrozen();
  if (!frozen) return bundle.charts[tf];
  const locked = frozen.payload.charts[tf].bars;
  const future = bundle.charts[tf].bars.filter(
    (bar) => bar.time > locked.at(-1).time && bar.end <= bundle.analysisCutoff,
  );
  const bars = [...locked, ...future],
    last = bars.at(-1),
    before = bars.at(-2);
  return {
    bars,
    axis: bars.map((bar) => bar.time),
    reference: last.time,
    latest: {
      close: last.close,
      time: last.time,
      end: last.end,
      change: last.close - before.close,
      changePercent: (last.close / before.close - 1) * 100,
    },
  };
}
async function frozenForSymbol(symbol) {
  if (state.data && symbol === state.symbol && (state.data.analysisEngine || "legacy") === (state.analysisEngine || "legacy")) return state.frozen;
  const identity = read(frozenKey(symbol), null);
  if (!identity) return null;
  const response = await apiFetch(
    "/api/snapshots/" + encodeURIComponent(identity),
  );
  const item = await response.json();
  if (!response.ok)
    throw Error(item.error || "Gespeicherter Stand nicht lesbar.");
  return item;
}
function frozenKey(symbol) {
  return "tori-frozen:" + symbol +
    (state.randomId ? ":random:" + state.randomId : state.datasetId ? ":dataset:" + state.datasetId : "") +
    (state.analysisEngine && state.analysisEngine !== "legacy" ? ":" + state.analysisEngine : "");
}
function updateCollapsedInfo() {
  $("#info-panel").classList.toggle("collapsed", state.infoCollapsed);
  rayLayer.update();
  $("#collapse-info").textContent = state.infoCollapsed ? "＋" : "−";
  $("#collapse-info").setAttribute(
    "aria-expanded",
    String(!state.infoCollapsed),
  );
  $("#collapse-info").setAttribute(
    "aria-label",
    state.infoCollapsed ? "Infobox ausklappen" : "Infobox einklappen",
  );
  $("#collapse-info").title = state.infoCollapsed
    ? "Infobox ausklappen"
    : "Infobox einklappen";
}
function nyInput(timestamp) {
  const parts = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(timestamp * 1000));
  const values = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${values.year}-${values.month}-${values.day}T${values.hour}:${values.minute}`;
}
function renderSavedList() {
  const items = (state.snapshotLists.get(state.symbol) || []).filter(item =>
    (item.datasetId || null) === (state.datasetId || null) &&
    (item.randomCaseId || null) === (state.randomId || null) &&
    (item.analysisEngine || "legacy") === state.analysisEngine);
  const select = $("#saved-stand");
  select.replaceChildren(
    new Option(
      items.length
        ? "Gespeicherten Stand wählen …"
        : "Noch keine gespeicherten Stände",
      "",
    ),
  );
  for (const item of items) select.add(new Option(item.label, item.id));
}
async function refreshSavedList() {
  const symbol = state.symbol;
  try {
    const response = await apiFetch(
      "/api/snapshots?" + new URLSearchParams({ symbol }),
    );
    const data = await response.json();
    if (!response.ok) throw Error(data.error);
    state.snapshotLists.set(symbol, data.items);
    if (symbol === state.symbol) renderSavedList();
  } catch (e) {
    $("#saved-stand").replaceChildren(
      new Option("Verzeichnis derzeit nicht verfügbar", ""),
    );
  }
}
function updateAnalysisControls() {
  updateToriControls();
  const data = state.data;
  if (!data) return;
  const frozen = state.analysisEnabled ? state.frozen : null;
  $("#analysis-state").textContent =
    (data.historical
      ? "Historisch · " + dtLong(data.analysisCutoff) + " ET"
      : state.analysisEnabled ? "Aktuelle Analyse" : "Aktuelle Kursdaten") +
    (!state.analysisEnabled
      ? " · Manuelle Ansicht · Tori-Analyse aus"
      : frozen
      ? " · Fixiert: " + dtLong(frozen.analysisCutoff) + " ET"
      : data.researchSetup
        ? " · Signalstand"
        : " · Mitlaufend: Neuberechnung je Kerzenschritt");
  if (state.datasetId && state.analysisEnabled)
    $("#analysis-state").textContent += data.researchSetup
      ? " · Forschungsfall: ursprüngliche Signallinien fixiert"
      : " · Unveränderlicher Forschungsbestand";
  $("#analysis-state").classList.toggle(
    "frozen",
    state.analysisEnabled && (!!frozen || !!data.researchSetup),
  );
  $("#freeze-button").title = state.frozen
    ? "Automatische Linien wieder neu wählen lassen; der gespeicherte Stand bleibt erhalten"
    : "Automatische Linien mit Datenbasis lokal speichern und fixieren";
  $("#analysis-at").value = nyInput(data.analysisCutoff);
  $("#axis-note").textContent = !state.analysisEnabled
    ? "Handelspausen ausgeblendet"
    : frozen
    ? "Fixierter Linienstand"
    : "Handelskerzen · gerade Linien";
  updateCollapsedInfo();
  updateStepButtons();
}
function updateStepButtons() {
  const disabled = !state.data || state.stepping || state.freezing || !$("#loading").hidden;
  document
    .querySelectorAll("[data-tf]")
    .forEach((button) => (button.disabled = state.stepping || state.freezing || !!(state.data && !state.data.charts?.[button.dataset.tf])));
  $("#symbol-button").disabled = state.stepping || state.freezing;
  $("#history-button").disabled = disabled;
  $("#refresh-button").disabled = disabled;
  $("#freeze-button").disabled = disabled || !hasToriAnalysis() || !!state.researchJob;
  if (state.researchJob)
    $("#freeze-button").textContent = state.data?.researchSetup
      ? "Signal fixiert"
      : "Forschungsfall";
  $("#replay-interval").textContent = state.timeframe;
  $("#step-back").disabled =
    disabled ||
    !!(state.analysisEnabled && state.frozen && state.data.analysisCutoff <= frozenBoundary(state.frozen));
  $("#step-next").disabled = disabled;
  updateToriControls();
  if (typeof updateRandomUI === 'function') updateRandomUI();
}
async function stepAnalysis(direction) {
  if (!state.data || state.stepping || state.freezing || !$("#loading").hidden) return;
  state.stepping = true;
  updateStepButtons();
  setTool(false);
  $("#error").hidden = true;
  $("#replay-status").textContent =
    `Eine ${state.timeframe}-Kerze ${direction === "back" ? "zurück" : "weiter"} …`;
  const request = state.request,
    symbol = state.symbol,
    tf = state.timeframe;
  try {
    const params = new URLSearchParams({
      symbol,
      timeframe: tf,
      asof: new Date((direction==='back' ? state.data.latest.end : state.data.analysisCutoff) * 1000).toISOString(),
      direction,
    });
    if (state.datasetId) params.set("dataset", state.datasetId);
    const response = await apiFetch((state.randomId ? '/api/random/cases/'+encodeURIComponent(state.randomId)+'/step?' : "/api/step?") + params),
      target = await response.json();
    if (
      request !== state.request ||
      symbol !== state.symbol ||
      tf !== state.timeframe
    )
      return;
    if (!response.ok)
      throw Error(target.error || "Kerzenschritt nicht verfügbar.");
    if (state.analysisEnabled && state.frozen && target.closedAt < frozenBoundary(state.frozen))
      throw Error(
        "Vor den fixierten Datenstand geht es nur nach dem Lösen der Fixierung.",
      );
    const range = chart.timeScale().getVisibleLogicalRange();
    if (await load(symbol, false, target.asof, true)) {
      if (range)
        chart
          .timeScale()
          .setVisibleLogicalRange(
            RayGeometry.latest(
              { from: 0, to: range.to - range.from },
              state.data.axis.length,
            ),
          );
      else latestView();
      $("#replay-status").textContent =
        `Kerzenschluss: ${dtLong(target.closedAt)} ET`;
    } else
      $("#replay-status").textContent =
        "Schritt nicht ausgeführt; bisheriger Stand bleibt sichtbar.";
  } catch (e) {
    if (request === state.request) $("#replay-status").textContent = e.message;
  } finally {
    state.stepping = false;
    updateStepButtons();
  }
}
async function toggleFreeze() {
  if (state.stepping || state.freezing || !$("#loading").hidden || state.researchJob || state.fanCase) return;
  if (!hasToriAnalysis() && !state.frozen) return;
  const bundle = currentBundle();
  if (!bundle) return;
  $("#error").hidden = true;
  if (state.frozen) {
    state.frozen = null;
    write(frozenKey(state.symbol), null);
    render(bundle, true);
    return;
  }
  state.freezing = true;
  updateStepButtons();
  const request = state.request,
    symbol = state.symbol;
  try {
    const response = await apiFetch("/api/snapshots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysisId: bundle.analysisId }),
    });
    const snapshot = await response.json();
    if (!response.ok)
      throw Error(snapshot.error || "Stand konnte nicht gespeichert werden.");
    if (request !== state.request || symbol !== state.symbol) return;
    assertFrozenCompatible(bundle, snapshot);
    state.frozen = snapshot;
    write(frozenKey(state.symbol), snapshot.id);
    render(bundle, true);
    await refreshSavedList();
  } catch (e) {
    if (request === state.request) showError(e.message);
  } finally {
    state.freezing = false;
    if (request === state.request) updateStepButtons();
  }
}
async function openSavedSnapshot(identity) {
  if (!identity) return;
  if (state.fanCase) { showError("Der Forschungsfall ist bereits an seinen Originalstand gebunden. Gespeicherte eigene Stände im normalen Chart öffnen."); return; }
  $("#history-dialog").close();
  $("#error").hidden = true;
  const request = ++state.request;
  try {
    const response = await apiFetch(
      "/api/snapshots/" + encodeURIComponent(identity),
    );
    const snapshot = await response.json();
    if (request !== state.request) return;
    if (!response.ok) throw Error(snapshot.error);
    const bundle = { ...snapshot.payload, historical: true };
    if (snapshot.symbol !== state.symbol)
      throw Error("Dieser Stand gehört zu einer anderen Aktie.");
    if ((snapshot.payload.randomCase?.id || null) !== (state.randomId || null))
      throw Error("Dieser Stand gehört zu einem anderen Replay-Fall. Im passenden Zufallsfall öffnen.");
    if(!snapshot.payload.charts[state.timeframe])throw Error('Dieses Intervall fehlt im alten gespeicherten Stand. Zuerst auf 1D oder 4h wechseln.');
    state.analysisEngine = bundle.analysisEngine || "legacy";
    state.datasetId = bundle.datasetId || null;
    $("#analysis-engine").value = state.analysisEngine;
    state.frozen = snapshot;
    state.asOf = isoCutoff(bundle);
    write(frozenKey(state.symbol), snapshot.id);
    state.bundles.set(bundleKey(state.symbol, state.asOf), bundle);
    state.bundles.set(bundleKey(state.symbol, state.asOf, true), bundle);
    render(bundle, false);
    resetView();
  } catch (e) {
    if (request === state.request) showError(e.message);
  }
}
function setupAnalysisUI() {
  updateToriControls();
  updateCollapsedInfo();
  $("#collapse-info").onclick = () => {
    state.infoCollapsed = !state.infoCollapsed;
    write("tori-info-collapsed", state.infoCollapsed);
    updateCollapsedInfo();
  };
  $("#history-button").onclick = () => {
    if (state.data)
      $("#analysis-at").value = nyInput(state.data.analysisCutoff);
    $("#history-dialog").showModal();
    refreshSavedList();
  };
  $("#history-form").onsubmit = (event) => {
    event.preventDefault();
    const cutoff = $("#analysis-at").value;
    if (!cutoff) return;
    $("#history-dialog").close();
    load(state.symbol, false, cutoff);
  };
  $("#live-analysis").onclick = () => {
    $("#history-dialog").close();
    load(state.symbol, false, null);
  };
  $("#freeze-button").onclick = toggleFreeze;
  $("#step-back").onclick = () => stepAnalysis("back");
  $("#step-next").onclick = () => stepAnalysis("next");
  $("#saved-stand").onchange = () => openSavedSnapshot($("#saved-stand").value);
}
