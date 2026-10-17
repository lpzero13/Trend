/* Analysis cutoff and immutable automatic-line snapshots. */
function bundleKey(symbol, asOf) {
  return (
    symbol +
    "|" +
    (asOf || "live") +
    "|" +
    (state.datasetId || "") +
    "|" +
    (state.researchTrial || "") +
    "|" +
    (state.researchVariant || "")
  );
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
function assertFrozenCompatible(bundle, frozen) {
  if (!frozen) return;
  if (frozen.symbol !== bundle.symbol || frozen.basis !== "bars")
    throw Error(
      "Dieser Stand gehört nicht zur aktuellen Aktie oder Linienbasis.",
    );
  if (frozen.validFrom > bundle.analysisCutoff)
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
  if (!state.frozen) return bundle.charts[tf];
  const locked = state.frozen.payload.charts[tf].bars;
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
  if (state.datasetId) return null;
  if (state.data && symbol === state.symbol) return state.frozen;
  const identity = read("tori-frozen:" + symbol, null);
  if (!identity) return null;
  const response = await apiFetch(
    "/api/snapshots/" + encodeURIComponent(identity),
  );
  const item = await response.json();
  if (!response.ok)
    throw Error(item.error || "Gespeicherter Stand nicht lesbar.");
  return item;
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
  const items = state.snapshotLists.get(state.symbol) || [];
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
  const data = state.data;
  if (!data) return;
  const frozen = state.frozen;
  $("#analysis-state").textContent =
    (data.historical
      ? "Historisch · " + dtLong(data.analysisCutoff) + " ET"
      : "Aktuelle Analyse") +
    (frozen
      ? " · Fixiert: " + dtLong(frozen.analysisCutoff) + " ET"
      : data.researchSetup
        ? " · Signalstand"
        : " · Automatik");
  if (state.datasetId)
    $("#analysis-state").textContent += data.researchSetup
      ? " · Forschungsfall: ursprüngliche Signallinien fixiert"
      : " · Unveränderlicher Forschungsbestand";
  $("#analysis-state").classList.toggle(
    "frozen",
    !!frozen || !!data.researchSetup,
  );
  $("#freeze-button").textContent = frozen ? "Fixierung lösen" : "Fixieren";
  $("#freeze-button").setAttribute("aria-pressed", String(!!frozen));
  $("#freeze-button").disabled = false;
  $("#freeze-button").title = frozen
    ? "Automatische Linien wieder neu wählen lassen; der gespeicherte Stand bleibt erhalten"
    : "Automatische Linien mit Datenbasis lokal speichern und fixieren";
  $("#analysis-at").value = nyInput(data.analysisCutoff);
  $("#axis-note").textContent = frozen
    ? "Fixierter Linienstand"
    : "Handelskerzen · gerade Linien";
  updateCollapsedInfo();
  updateStepButtons();
}
function updateStepButtons() {
  const disabled = !state.data || state.stepping || !$("#loading").hidden;
  document
    .querySelectorAll("[data-tf]")
    .forEach((button) => (button.disabled = state.stepping));
  $("#symbol-button").disabled = state.stepping;
  $("#history-button").disabled = state.stepping || !$("#loading").hidden;
  $("#refresh-button").disabled = state.stepping || !$("#loading").hidden;
  $("#freeze-button").disabled = disabled || !!state.researchJob;
  if (state.researchJob)
    $("#freeze-button").textContent = state.data?.researchSetup
      ? "Signal fixiert"
      : "Forschungsfall";
  $("#replay-interval").textContent = state.timeframe;
  $("#step-back").disabled =
    disabled ||
    !!(state.frozen && state.data.analysisCutoff <= state.frozen.validFrom);
  $("#step-next").disabled = disabled;
}
async function stepAnalysis(direction) {
  if (!state.data || state.stepping) return;
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
      asof: new Date(state.data.analysisCutoff * 1000).toISOString(),
      direction,
    });
    if (state.datasetId) params.set("dataset", state.datasetId);
    const response = await apiFetch("/api/step?" + params),
      target = await response.json();
    if (
      request !== state.request ||
      symbol !== state.symbol ||
      tf !== state.timeframe
    )
      return;
    if (!response.ok)
      throw Error(target.error || "Kerzenschritt nicht verfügbar.");
    if (state.frozen && target.closedAt < state.frozen.validFrom)
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
  if (!state.data) return;
  const bundle = currentBundle();
  if (!bundle) return;
  $("#error").hidden = true;
  if (state.frozen) {
    state.frozen = null;
    write("tori-frozen:" + state.symbol, null);
    render(bundle, true);
    return;
  }
  $("#freeze-button").disabled = true;
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
    write("tori-frozen:" + state.symbol, snapshot.id);
    render(bundle, true);
    await refreshSavedList();
  } catch (e) {
    if (request === state.request) showError(e.message);
  } finally {
    if (request === state.request) $("#freeze-button").disabled = false;
  }
}
async function openSavedSnapshot(identity) {
  if (!identity) return;
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
    state.frozen = snapshot;
    state.asOf = isoCutoff(bundle);
    write("tori-frozen:" + state.symbol, snapshot.id);
    state.bundles.set(bundleKey(state.symbol, state.asOf), bundle);
    render(bundle, false);
    resetView();
  } catch (e) {
    if (request === state.request) showError(e.message);
  }
}
function setupAnalysisUI() {
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
