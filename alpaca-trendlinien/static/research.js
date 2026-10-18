const $ = (s) => document.querySelector(s);
const escapeHtml = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const number = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("de-DE", { maximumFractionDigits: 2 }).format(n);
const date = (n) =>
  n
    ? new Date(n * 1000).toLocaleString("de-DE", {
        timeZone: "Europe/Berlin",
        dateStyle: "short",
        timeStyle: "short",
      })
    : "—";
const labels = {
  queued: "Wartet",
  running: "Läuft",
  succeeded: "Abgeschlossen",
  failed: "Fehler",
  cancel_requested: "Wird abgebrochen",
  cancelled: "Abgebrochen",
  partial: "Teilweise abgeschlossen",
};
const phaseLabels = {
  preparing: "Auftrag vorbereiten",
  importing: "Kursdaten importieren",
  validating: "Datenbestand prüfen",
  events: "Linienereignisse berechnen",
  entries: "Tori-Einstiege kerzenweise prüfen",
  saving_events: "Ereignisse speichern",
  trials: "Zufallsstarts auswerten",
  symbol_error: "Fehler bei einer Aktie",
  ...labels,
};
function age(seconds) {
  if (seconds == null) return "unbekannt";
  if (seconds < 60) return `${Math.floor(seconds)} s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
  if (seconds < 86400) return `${number(seconds / 3600)} h`;
  return `${number(seconds / 86400)} Tagen`;
}
function bytes(value) {
  return value == null
    ? "unbekannt"
    : value < 1048576
      ? `${number(value / 1024)} KiB`
      : value < 1073741824
        ? `${number(value / 1048576)} MiB`
        : `${number(value / 1073741824)} GiB`;
}
function progressText(progress) {
  const d = progress?.detail || {};
  const unit =
    { candles: "Kerzen", trials: "Starts", events: "Ereignisse" }[d.unit] || "";
  if (d.total != null)
    return `${d.symbol || ""} · ${number(d.completed)} / ${number(d.total)} ${unit}`;
  if (d.pages != null)
    return `${d.symbol} · ${d.interval} · ${number(d.pages)} Seiten · ${number(d.rows)} Kerzen geladen`;
  return d.symbol || "—";
}
function renderOperations(ops) {
  if (!ops) {
    $("#ops-worker").textContent = "Server für Betriebsanzeige neu starten";
    return;
  }
  const w = ops.worker,
    p = w.progress;
  const names = {
    absent: "Kein Worker aktiv",
    unverified: "Worker noch ohne bestätigtes Lebenszeichen",
    unresponsive: "Lebenszeichen überfällig",
    stalled: "Länger kein Arbeitsfortschritt",
    working: "Arbeitet",
    idle: "Bereit · wartet auf Aufträge",
  };
  $("#ops-worker").textContent = names[w.state] || w.state;
  $("#background-status").textContent =
    `${["working", "idle"].includes(w.state) ? "●" : "⚠"} ${names[w.state] || w.state}`;
  $("#ops-heartbeat").textContent = w.heartbeatAt
    ? `${date(w.heartbeatAt)} · vor ${age(w.heartbeatAgeSeconds)}`
    : "Noch nicht erfasst";
  $("#ops-phase").textContent = p
    ? `${phaseLabels[p.phase] || p.phase} · seit ${date(p.phase_started)}`
    : w.state === "idle"
      ? "Wartet auf Auftrag"
      : "—";
  $("#ops-progress").textContent = progressText(p);
  const imported = ops.lastSuccessfulImport;
  $("#ops-import").textContent = imported
    ? `${imported.symbol} · ${date(imported.checkedAt)} · ${imported.feed} / ${imported.adjustment}`
    : "Noch nicht erfasst";
  const dataset = ops.lastDataset;
  const storage = ops.storage;
  $("#ops-storage").textContent = storage
    ? `${bytes(storage.totalBytes)} belegt · ${bytes(storage.freeBytes)} frei${storage.warning ? " · wenig freier Speicher" : ""}`
    : "Noch nicht erfasst";
  $("#storage-details").textContent = storage
    ? `Datenbankschema ${ops.databaseVersion} · Stand ${date(storage.observedAt)} · ` +
      Object.entries(storage.categories)
        .map(
          ([name, item]) =>
            `${name}: ${bytes(item.bytes)} (${number(item.files)} Dateien)`,
        )
        .join(" · ")
    : "Speicherübersicht nach Serverupdate verfügbar.";
  $("#ops-data").textContent = dataset
    ? `${dataset.symbol} · ` +
      Object.entries(ops.dataAge)
        .map(
          ([tf, d]) =>
            `${tf}: Abruf vor ${age(d.fetchAgeSeconds)}, letzter Schluss vor ${age(d.lastCloseAgeSeconds)}`,
        )
        .join(" · ")
    : "Noch kein Datenbestand erfasst";
  $("#ops-warning").hidden = ![
    "stalled",
    "unresponsive",
    "unverified",
    "absent",
  ].includes(w.state);
  $("#ops-warning").textContent =
    w.state === "stalled"
      ? `Seit ${age(w.progressAgeSeconds ?? w.loopAgeSeconds)} kein bestätigter Fortschritt. Das ist ein Prüfhinweis, kein sicherer Stillstandsnachweis; der Auftrag wird nicht automatisch beendet.`
      : `${names[w.state]}. Dienst und Worker-Protokoll prüfen.`;
  const error = ops.lastError;
  $("#ops-error").hidden = !error;
  $("#ops-error").textContent = error
    ? `Letzter protokollierter Fehler · ${date(error.updated)} · Auftrag ${error.id.slice(0, 8)}${error.symbol && !error.error ? " · " + error.symbol : ""}: ${error.error || error.symbol_error}`
    : "";
}
const reasons = {
  search_timeout: "Kein Ausbruch im Suchfenster",
  search_censored: "Suchfenster am Reservierungsrand abgeschnitten",
  retest_invalidated: "Retest-Linie wieder unterschritten",
  retest_censored: "Retest-Beobachtung unvollständig",
  no_retest: "Kein bestätigter Retest",
  execution_censored: "Kein späterer Ausführungskurs im Abschnitt",
};
let selected = null,
  jobsCache = [],
  busy = false,
  reportStamp = null;
let pageOffset = 0;
let entryFilter = "entries";
try {
  document.documentElement.dataset.theme =
    JSON.parse(localStorage.getItem("tori-theme")) || "light";
} catch {}
$("#research-theme").onclick = () => {
  const theme =
    document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem("tori-theme", JSON.stringify(theme));
  } catch {}
};
async function request(url, body) {
  const response = await apiFetch(
    url,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "Anfrage fehlgeschlagen");
  return data;
}
function showError(e) {
  $("#research-error").textContent = e.message;
  $("#research-error").hidden = false;
}
function spec() {
  const result = {
    symbols: $("#study-symbols")
      .value.toUpperCase()
      .replaceAll(",", " ")
      .split(/\s+/)
      .filter(Boolean),
    universe: $("#universe").value,
    samples: +$("#study-samples").value,
    history_days: +$("#study-history").value,
    search_bars: +$("#study-search").value,
    seed: +$("#study-seed").value,
    horizons: $("#study-horizons")
      .value.split(/[,\s]+/)
      .filter(Boolean)
      .map(Number),
    retest_bps: +$("#study-retest-bps").value,
    retest_bars: +$("#study-retest-bars").value,
    cost_bps: +$("#study-cost").value,
  };
  if ($("#entry-mode").value === "tori") {
    result.entry_mode = "tori";
    result.tori = {
      sampling: $("#tori-sampling").value,
      observe_forward: $("#tori-observe").value === "yes",
      line_policy: $("#tori-policy").value,
      safety_selection: $("#tori-safety").value,
      start_date: $("#tori-start").value,
      end_date: $("#tori-end").value,
      context: $("#tori-context").value,
      setup_bars: +$("#tori-setup-bars").value,
      min_contacts: +$("#tori-contacts").value,
      contact_gap_bars: +$("#tori-contact-gap").value,
      min_age_days: +$("#tori-age").value,
      breakout_bps: +$("#tori-buffer").value,
      max_safety_pct: +$("#tori-risk-pct").value,
      max_safety_atr: +$("#tori-risk-atr").value,
      min_body_atr: +$("#tori-body-atr").value,
      min_body_fraction: +$("#tori-body-fraction").value,
      min_close_location: +$("#tori-close-location").value,
      horizontal_bars: +$("#tori-horizontal-bars").value,
      min_room_r: +$("#tori-room").value,
    };
  }
  return result;
}
const originalCopy = Object.fromEntries(
  ["research-intro-copy", "observation-note", "method-copy"].map((id) => [
    id,
    $("#" + id).textContent,
  ]),
);
$("#entry-mode").onchange = () => {
  const tori = $("#entry-mode").value === "tori";
  $("#tori-settings").hidden = !tori;
  $("#tori-settings")
    .querySelectorAll("input,select")
    .forEach((el) => (el.disabled = !tori));
  const random = tori && $("#tori-sampling").value === "random";
  for (const id of ["study-samples", "study-seed", "study-search"])
    $("#" + id).disabled = tori && !random;
  $("#study-horizons").disabled = tori && $("#tori-observe").value !== "yes";
  $("#study-cost").disabled = tori;
  $("#horizon-label").textContent = tori ? "Auswertung nach Handelstagen (nach Einstiegstag)" : "Auswertung nach 4h-Kerzen";
  $("#research-intro-copy").textContent = tori
    ? "Tori-Kriterien in zufälligen Zeiträumen oder einem vollständigen Zeitraum prüfen. Linienpaare festhalten; Ausbruch, horizontale Bestätigung und Retest getrennt beobachten."
    : originalCopy["research-intro-copy"];
  $("#observation-note").textContent = tori
    ? "Die Horizonte zählen Börsensitzungen nach dem Einstiegstag, keine 4h-Kerzen. Angezeigt wird die reine Kursänderung zum jeweiligen Tagesschluss, ohne Kosten, Stop-Ausführung oder Take-Profit. Unvollständige Beobachtungen werden separat gezählt."
    : originalCopy["observation-note"];
  $("#method-copy").textContent = tori
    ? "365 Tage Linienvorlauf. Zufallsfenster werden vor der Signalsuche per Seed gezogen, ohne Überlappung der Suchzeiträume; bei wenig Historie sind weniger Fenster möglich. Je Fenster/Variante wird der erste Einstieg zur Kursbeobachtung ausgewählt. Auch Fenster ohne Einstieg bleiben sichtbar. Der spätere Holdout bleibt reserviert. Fixierte Setups bleiben bestehen; spätere Kursbeobachtungen und Einstiegsvarianten können abhängig sein."
    : originalCopy["method-copy"];
};
$("#tori-sampling").onchange = () => $("#entry-mode").onchange();
$("#tori-observe").onchange = () => $("#entry-mode").onchange();
$("#entry-mode").onchange();
$("#universe").onchange = () => {
  $("#study-symbols").disabled = $("#universe").value === "all";
};
$("#use-favorites").onclick = () => {
  try {
    $("#study-symbols").value = (
      JSON.parse(localStorage.getItem("tori-favorites")) || []
    ).join(", ");
    $("#universe").value = "list";
    $("#study-symbols").disabled = false;
  } catch {}
};
$("#study-form").onsubmit = async (e) => {
  e.preventDefault();
  $("#research-error").hidden = true;
  try {
    const job = await request("/api/research/jobs", spec());
    selected = job.id;
    pageOffset = 0;
    reportStamp = null;
    await refresh();
  } catch (e) {
    showError(e);
  }
};
$("#enable-schedule").onclick = async () => {
  if (!$("#study-form").reportValidity()) return;
  try {
    await request("/api/research/schedule", {
      enabled: true,
      interval_hours: +$("#schedule-hours").value,
      spec: spec(),
    });
    await refresh();
  } catch (e) {
    showError(e);
  }
};
$("#pause-schedule").onclick = async () => {
  try {
    await request("/api/research/schedule", { enabled: false });
    await refresh();
  } catch (e) {
    showError(e);
  }
};
$("#cancel-job").onclick = async () => {
  try {
    await request(`/api/research/jobs/${selected}/cancel`, {});
    await refresh();
  } catch (e) {
    showError(e);
  }
};
$("#refresh-jobs").onclick = () => {
  reportStamp = null;
  refresh();
};
function valueClass(n) {
  return n > 0 ? "positive" : n < 0 ? "negative" : "";
}
function chartLink(trial, entry, future = false) {
  const completed = Object.values(entry?.outcomes || {}).filter(
    (x) => x.complete,
  );
  const at =
    future && trial.mode && entry?.entryAt
      ? entry.entryAt + 3600
      : future && completed.length
        ? Math.max(...completed.map((x) => x.closedAt))
        : entry?.signalAt || trial.startAt;
  return (
    "/?" +
    new URLSearchParams({
      symbol: trial.symbol,
      tf: future && trial.mode ? "1h" : "4h",
      dataset: trial.datasetId,
      asof: new Date(at * 1000).toISOString(),
      ...(entry
        ? { job: selected, trial: trial.id, variant: entry.variant }
        : {}),
    })
  );
}
const entryNames = {
  breakout: "Ausbruch",
  horizontal: "Ausbruch + Horizontalhoch",
  retest: "Retest",
};
const entryStates = {
  observed: "Einstieg beobachtet",
  pending: "Wartet",
  rejected: "Abgelehnt",
  expired: "Abgelaufen",
  censored: "Beobachtung endet",
};
const checkNames = {
  confirmed_anchors: "Bestätigte Anker",
  red_contacts: "Eigenständige rote Kontakte",
  green_contacts: "Eigenständige grüne Kontakte",
  line_age: "Alter bis zur Bestätigung (Tage)",
  ordered_safety: "Grün unter Rot, unverletzt",
  close_above_red: "Schluss mit Puffer über Rot",
  positive_body: "Positiver Kerzenkörper",
  body_atr: "Körper / ATR",
  body_fraction: "Körper / Kerzenspanne",
  close_location: "Schlussposition in der Kerze",
  context: "Übergeordnete Swing-Struktur",
  safety_distance_pct: "Abstand Grün (%)",
  safety_distance_atr: "Abstand Grün / ATR",
  room: "Raum zum bekannten Widerstand",
  horizontal_confirmed: "Horizontalhoch überwunden",
  retest_held: "Ursprüngliche Linie hält im Retest",
  execution_above_trigger: "Eröffnung über Auslöser",
  interim_safety: "Grün vor Ausführung unverletzt",
  execution_room: "Raum an der Eröffnung",
  setup_expired: "Setup-Laufzeit erreicht",
  confirmation_expired: "Bestätigung nicht rechtzeitig",
  green_violated: "Grün verletzt",
  red_lost: "Schluss unter ursprünglicher roter Zone",
  window_end: "Zeitraum-/Holdout-Grenze",
};
function entryReason(reason) {
  return String(reason || "")
    .split(",")
    .map((s) =>
      s.startsWith("execution:")
        ? "Eröffnung: " + (checkNames[s.slice(10)] || s.slice(10))
        : checkNames[s] || s,
    )
    .join(" · ");
}
function renderToriReport(data) {
  const { job, summary, trials } = data;
  $("#report-subtitle").textContent =
    `${job.id.slice(0, 8)} · ${labels[job.status] || job.status} · Tori-Einstiege · ${job.spec.tori.line_policy === "snapshot" ? "Fixierung zu X" : "Linienpaare verfolgen"}`;
  $("#report-actions").hidden = false;
  $("#export-report").href = `/api/research/jobs/${job.id}/report`;
  $("#export-events").href = `/api/research/jobs/${job.id}/events?limit=250`;
  $("#cancel-job").disabled = !["queued", "running"].includes(job.status);
  const observing = !!summary.observations;
  let html = `<p class="note"><b>${observing ? "Einstiege und spätere Schlusskurse" : "Nur Einstiege"}, keine Take-Profits oder Ausstiege.</b> ${summary.setups} archivierte Linienpaare. ${job.spec.tori.sampling === "random" ? "Zufallsfenster werden ohne Sicht auf spätere Signale gewählt. Für die Kursbeobachtung zählt je Fenster und Variante der erste Einstieg; zeitgleiche Linienpaare werden dedupliziert." : "Jede abgeschlossene 4h-Kerze im gewählten Entwicklungszeitraum wird geprüft."} Linien zu X bzw. bei Aufnahme eines Setups bleiben fest. Varianten und parallele Linienpaare sind keine unabhängigen Trades.</p>`;
  for (const item of job.symbols) {
    const p = item.plan;
    html += `<p class="note">${escapeHtml(item.symbol)} · ${p ? `${date(p.scanStartAt)} bis ${date(p.scanEndAt)} · ${p.coverage?.candles ?? 0}/${p.candles} Kerzen geprüft · Holdout ab ${date(p.holdout_start)}` : "Wartet auf Daten"}${item.error ? " · " + escapeHtml(item.error) : ""}</p>`;
    if (p?.windows) {
      const complete = (p.coverage?.windows || []).filter(w => w.complete);
      const empty = complete.filter(w => !w.entryVariants.length).length;
      html += `<p class="note">${p.actual_samples}/${p.requested_samples} nicht überlappende Suchfenster verfügbar · ${complete.length} abgeschlossen · ${empty} ohne Einstieg. Seed ${job.spec.seed}. Beobachtungsverläufe können trotzdem überlappen.</p><details><summary>Gezogene Zeiträume und Varianten</summary><ul>${p.windows.map(w => { const done = complete.find(c => c.id === w.id); return `<li>${date(w.scanStartAt)} – ${date(w.scanEndAt)} · ${done ? done.entryVariants.map(v => entryNames[v]).join(", ") || "kein Einstieg" : "noch nicht vollständig geprüft"}</li>`; }).join("")}</ul></details>`;
    }
  }
  if (job.error) html += `<p class="error-note">${escapeHtml(job.error)}</p>`;
  html +=
    '<div class="table-wrap"><table><thead><tr><th>Variante / Qualität</th><th>Linienpaare</th><th>Entries / eindeutige Zeitpunkte</th><th>Abgelehnt</th><th>Abgelaufen</th><th>Unvollständig / wartet</th></tr></thead><tbody>';
  for (const variant of Object.keys(entryNames))
    for (const quality of ["provisional", "qualified"]) {
      const g = summary.groups[variant + "_" + quality] || {};
      html += `<tr><td>${entryNames[variant]} · ${quality === "qualified" ? "≥3 Kontakte / ≥7 Tage" : "vorläufig"}</td><td>${g.setups || 0}</td><td>${g.entries || 0} / ${g.uniqueEntries || 0}</td><td>${g.rejected || 0}</td><td>${g.expired || 0}</td><td>${g.censored || 0} / ${g.pending || 0}</td></tr>`;
    }
  html +=
    '</tbody></table></div><p class="note">Die Qualitätsgruppe verwendet eigenständige Kontakte beider Linien. Keine A+/A-/B-Zertifizierung. Tageskontext im Standard: bestätigte Struktur darf nicht fallen; „gemischt“ ist erlaubt. Pflichtkontext unbekannt → kein Entry. Fehlender bekannter Widerstand bleibt unbekannt. IEX/Rohkurse und heutiges Universum bleiben Datenbegrenzungen.</p>';
  if (observing) {
    html += `<h3>Kursentwicklung nach dem Einstieg</h3><p class="note">${summary.observations.uniqueEntriesAcrossVariants} eindeutige Einstiegszeitpunkte über alle Varianten. Je Gruppe wird Dataset + Einstiegszeit einmal gezählt. Handelstag 1 ist die erste Börsensitzung nach dem Einstiegstag. Kursänderung = (Tagesschluss / Einstiegskurs − 1) × 100. Rohkurse ohne Dividenden-/Splitbereinigung; keine Depot-Rendite. Positive Verläufe sind keine Strategie-Trefferquote.</p><div class="table-wrap"><table><thead><tr><th>Variante / Qualität</th>${job.spec.horizons.map(h => `<th>Nach ${h} Handelstagen</th>`).join("")}</tr></thead><tbody>`;
    for (const variant of Object.keys(entryNames)) for (const quality of ["provisional", "qualified"]) {
      const g = summary.observations.groups[variant+"_"+quality];
      if (!g?.uniqueEntries) {
        html += `<tr><td>${entryNames[variant]} · ${quality === "qualified" ? "qualifiziert" : "vorläufig"}</td><td colspan="${job.spec.horizons.length}">Keine ausgewählten Kursbeobachtungen</td></tr>`;
        continue;
      }
      html += `<tr><td>${entryNames[variant]} · ${quality === "qualified" ? "qualifiziert" : "vorläufig"}</td>${job.spec.horizons.map(h => {
        const o = g?.horizons[String(h)];
        return `<td><b class="${valueClass(o?.median_pct)}">${number(o?.median_pct)}${o?.n ? " % Median" : ""}</b><br><small>Ø ${number(o?.mean_pct)} % · n=${o?.n || 0}<br>${o?.positive || 0} höher / ${o?.negative || 0} tiefer / ${o?.flat || 0} gleich<br>${o?.incomplete || 0} unvollständig · ${o?.overlapping_entries || 0} überlappend</small></td>`;
      }).join("")}</tr>`;
    }
    html += `</tbody></table></div>`;
  }
  html += `<p class="note">Linienpaare ${data.page.total ? data.page.offset + 1 : 0}–${data.page.offset + trials.length} von ${data.page.total}. Die Zusammenfassung umfasst den ganzen Auftrag. Ausführung verwendet die erste verfügbare 1h-Eröffnung nach Schluss plus ${job.spec.latency_seconds} s; keine Garantie eines handelbaren Fills.</p><div class="table-wrap"><table><thead><tr><th>Aktie / Fixierung</th><th>Variante / Zustand</th><th>Bestätigung / Einstieg</th><th>Prüfung</th><th>Chart</th></tr></thead><tbody>`;
  for (const trial of trials)
    for (const v of trial.variants) {
      const checks = [...(v.checks || []), ...(v.executionChecks || [])];
      html += `<tr><td>${escapeHtml(trial.symbol)}<br><small>${date(trial.startAt)}</small></td><td class="case-reason">${entryNames[v.variant]}<br><small>${entryStates[v.status] || escapeHtml(v.status)}${v.reason ? " · " + escapeHtml(entryReason(v.reason)) : v.waitingFor ? " · wartet auf " + escapeHtml(entryReason(v.waitingFor)) : ""}</small></td><td>${date(v.signalAt)}<br>${v.entryAt ? `${date(v.entryAt)} · ${number(v.entryPrice)}` : "—"}</td><td class="entry-checks"><details><summary>${checks.length ? `${checks.filter((c) => c.required && c.state !== "pass").length} offene/fehlgeschlagene Pflichtprüfungen` : "Wartet auf Ausbruch"}</summary><ul>${checks.map((c) => `<li>${c.state === "pass" ? "✓" : c.state === "fail" ? "✕" : "?"} ${checkNames[c.name] || escapeHtml(c.name)}${c.required ? "" : " (Hinweis)"}: ${escapeHtml(typeof c.value === "object" ? JSON.stringify(c.value) : number(c.value))}</li>`).join("")}</ul></details></td><td><a href="${chartLink(trial, v)}" target="_blank" rel="noopener">Linienstand ↗</a>${v.entryAt ? ` · <a href="${chartLink(trial, v, true)}" target="_blank" rel="noopener">Entry-Kerze ↗</a>` : ""}</td></tr>`;
    }
  html += '</tbody></table></div>';
  if (observing) {
    html += `<h3>Einzelne Kursbeobachtungen · aktuelle Ergebnisseite</h3><div class="table-wrap"><table><thead><tr><th>Aktie / Variante</th><th>Einstieg</th>${job.spec.horizons.map(h => `<th>+${h} Handelstage</th>`).join("")}</tr></thead><tbody>`;
    const seen = new Set();
    for (const t of trials) for (const v of t.variants) if (v.observationSelected) {
      const key = `${t.datasetId}|${v.variant}|${v.quality}|${v.entryAt}`;
      if (seen.has(key)) continue;
      seen.add(key);
      html += `<tr><td>${escapeHtml(t.symbol)} · ${entryNames[v.variant]}</td><td>${date(v.entryAt)}<br>${number(v.entryPrice)}</td>${job.spec.horizons.map(h => {const o = v.forward?.[String(h)]; return `<td class="${valueClass(o?.return_pct)}">${o?.complete ? `${number(o.return_pct)} %<br>${number(o.close)}` : o?.reason === "missing_daily_sessions" ? "Datenlücke" : "Unvollständig"}<br><small>${escapeHtml(o?.targetDate || "")}</small></td>`;}).join("")}</tr>`;
    }
    html += '</tbody></table></div>';
  }
  html += '<details class="case-details"><summary>Fixierte Anker und vollständige Prüfprotokolle</summary><pre id="case-json"></pre></details><details class="case-details"><summary>Versionierte Tori-Annahmen dieses Auftrags</summary><pre id="tori-spec-json"></pre></details>';
  $("#report-content").innerHTML = html;
  const filter = document.createElement("select");
  filter.setAttribute("aria-label", "Tori-Fälle anzeigen");
  filter.innerHTML =
    '<option value="entries">Nur Setups mit Einstieg</option><option value="all">Alle Setups einschließlich Ablehnungen</option>';
  filter.value = entryFilter;
  filter.onchange = () => {
    entryFilter = filter.value;
    pageOffset = 0;
    reportStamp = null;
    refresh();
  };
  $("#report-content").prepend(filter);
  $("#case-json").textContent = JSON.stringify(trials, null, 2);
  $("#tori-spec-json").textContent = JSON.stringify(job.manifest, null, 2);
  if (data.page.offset > 0 || data.page.hasMore) {
    const nav = document.createElement("div");
    nav.className = "study-actions";
    for (const [text, offset, disabled] of [
      ["Vorherige Linienpaare", Math.max(0, pageOffset - 50), pageOffset === 0],
      ["Weitere Linienpaare", pageOffset + 50, !data.page.hasMore],
    ]) {
      const button = document.createElement("button");
      button.textContent = text;
      button.disabled = disabled;
      button.onclick = () => {
        pageOffset = offset;
        reportStamp = null;
        refresh();
      };
      nav.append(button);
    }
    $("#report-content").append(nav);
  }
}
function renderReport(data) {
  if (data.job.spec.entry_mode === "tori") return renderToriReport(data);
  $("#export-events").href =
    `/api/research/jobs/${data.job.id}/events?limit=250`;
  const { job, summary, trials } = data;
  $("#report-subtitle").textContent =
    `${job.id.slice(0, 8)} · ${labels[job.status] || job.status} · ${job.manifest.studyVersion}`;
  $("#report-actions").hidden = false;
  $("#export-report").href = `/api/research/jobs/${job.id}/report`;
  $("#cancel-job").disabled = !["queued", "running"].includes(job.status);
  let html = `<div class="stat-row"><div><strong>${summary.trials}</strong><span>Zufällige Startpunkte</span></div><div><strong>${summary.no_entry}</strong><span>Ohne beobachteten Einstieg</span></div><div><strong>${job.eventCount}</strong><span>Archivierte Linienereignisse</span></div></div>`;
  const errors = [
    ...(job.error ? [job.error] : []),
    ...job.symbols.filter((s) => s.error).map((s) => `${s.symbol}: ${s.error}`),
  ];
  if (errors.length)
    html += `<p class="note error-note">${errors.map(escapeHtml).join("<br>")}</p>`;
  html += `<div class="table-wrap"><table><thead><tr><th>Testgruppe</th><th>Versuche mit Entry / eindeutige Einstiege</th>${job.spec.horizons.map((h) => `<th>Nach ${h} Kerzen · Median netto</th>`).join("")}</tr></thead><tbody>`;
  for (const variant of ["breakout", "retest"])
    for (const quality of ["provisional", "qualified"]) {
      const group = summary.groups[`${variant}_${quality}`];
      html += `<tr><td>${variant === "breakout" ? "Ausbruch" : "Retest"} · ${quality === "qualified" ? "qualifiziert" : "vorläufig"}</td><td>${group?.observed || 0} / ${group?.uniqueEntries ?? group?.uniqueSignals ?? 0}<br><small>${group?.withoutEntry ?? 0} Versuche ohne Entry</small></td>${job.spec.horizons
        .map((h) => {
          const result = group?.horizons[String(h)];
          return `<td class="${valueClass(result?.median_net_pct)}">${number(result?.median_net_pct)}${result?.n ? ` % <small>(n=${result.n}; ${result.positive} positiv)</small>` : ""}<br><small>${result?.n_incomplete ?? 0} unvollständig · ${result?.overlapping_entries ?? 0} überlappend</small></td>`;
        })
        .join("")}</tr>`;
    }
  html +=
    '</tbody></table></div><p class="note">Netto = Kursänderung ab beobachtetem Einstieg abzüglich Kostenannahme je Seite. n zählt vollständige, eindeutige Einstiege. Keine Stop-Ausführung und keine Portfoliorendite. „Vorläufig“ enthält auch andere nicht vollständig qualifizierte Linienpaare; die exakten Kontakte stehen im Fallprotokoll.</p>';
  html +=
    '<p class="note"><b>Nur Entwicklungszeitraum; Holdout bleibt unberührt.</b> Wiederholte Starts können denselben Einstieg treffen. Auch eindeutige Einstiege sind keine unabhängigen Stichproben: „überlappend“ zählt zeitlich überlappende Beobachtungsfenster desselben Datasets. Andere Abhängigkeiten bleiben möglich. Unvollständige Fenster gehen nicht als Gewinn oder Verlust in den Median ein.</p>';
  const qualityGroups = new Map();
  let unknownQuality = 0;
  for (const item of job.symbols) {
    if (!item.dataQuality) {
      unknownQuality++;
      continue;
    }
    for (const issue of item.dataQuality.issues) {
      const entry = qualityGroups.get(issue.kind) || {
        message: issue.message || issue.kind,
        count: 0,
        symbols: [],
      };
      entry.count++;
      if (entry.symbols.length < 10) entry.symbols.push(item.symbol);
      qualityGroups.set(issue.kind, entry);
    }
  }
  html += `<details class="case-details"><summary>Datenqualität & Grenzen</summary><p class="note">Beschreibendes Audit des gesamten Datenbestands, kein damaliger Einstiegsfilter. Rohkurse und Bereinigung, IEX-Einzelplatzdaten, heutiges Aktienuniversum und mögliche Kapitalmaßnahmen bleiben zu berücksichtigen. Kein automatischer Nachweis von Splits oder Dividenden. ${unknownQuality} Aktien ohne gespeichertes Audit.</p>${[...qualityGroups.values()].map((q) => `<p class="note">${escapeHtml(q.message)} · ${q.count} Aktien (${escapeHtml(q.symbols.join(", "))}${q.count > q.symbols.length ? ", …" : ""})</p>`).join("")}</details>`;
  html += `<p class="note">Einzelfälle ${data.page.total ? data.page.offset + 1 : 0}–${data.page.offset + trials.length} von ${data.page.total}. Gruppenergebnisse berücksichtigen alle Fälle.</p><div class="table-wrap"><table><thead><tr><th>Aktie / Start (Berlin)</th><th>Variante / Ergebnis</th><th>Entry</th><th>Verlauf / Gegenlauf</th><th>Chart</th></tr></thead><tbody>`;
  for (const trial of [...trials].sort(
    (a, b) => a.symbol.localeCompare(b.symbol) || a.startAt - b.startAt,
  )) {
    const entries = trial.variants.length ? trial.variants : [null];
    for (const entry of entries) {
      const outcome = entry
        ? Object.values(entry.outcomes || {})
            .filter((x) => x.complete)
            .at(-1)
        : null;
      html += `<tr><td>${escapeHtml(trial.symbol)}<br><small>${date(trial.startAt)}</small></td><td class="case-reason">${entry ? (entry.variant === "breakout" ? "Ausbruch" : "Retest") : "Kein Einstieg"}<br><small>${escapeHtml(reasons[entry?.reason || trial.reason] || (entry?.quality === "qualified" ? "Qualifiziert" : "Vorläufig"))}</small></td><td>${number(entry?.entryPrice)}</td><td>${outcome ? `<span class="positive">${number(outcome.mfe_pct)} %</span> / <span class="negative">${number(outcome.mae_pct)} %</span>` : "—"}</td><td><a href="${chartLink(trial, entry)}" target="_blank" rel="noopener">${entry ? "Signal" : "Start"} ↗</a>${outcome ? ` · <a href="${chartLink(trial, entry, true)}" target="_blank" rel="noopener">Verlauf ↗</a>` : ""}</td></tr>`;
    }
  }
  html +=
    '</tbody></table></div><details class="case-details"><summary>Merkmale, ursprüngliche Linien und Einzelwerte</summary><p class="note">R = Einstiegskurs minus ursprüngliche grüne Schutzmarke; nur bei positiver Distanz. +1R/+2R vor Schutzmarke wird bei gleichzeitiger Berührung innerhalb einer Kerze nicht als Erfolg gewertet. MFE/MAE beschreiben den besten/schlechtesten Verlauf innerhalb des vollständigen Fensters.</p><pre id="case-json"></pre></details>';
  html += `<details class="case-details"><summary>Datenstände & reservierter Zeitraum</summary><div class="note">${job.symbols.map((s) => `${escapeHtml(s.symbol)} · Dataset ${escapeHtml(s.dataset_id?.slice(0, 12) || "noch nicht importiert")} · ${s.plan ? `${s.plan.actual_samples}/${s.plan.requested_samples} Starts; reserviert ab ${date(s.plan.holdout_start)}` : escapeHtml(s.error || "Wartet")}`).join("<br>")}</div></details>`;
  $("#report-content").innerHTML = html;
  if (data.page.offset > 0 || data.page.hasMore) {
    const nav = document.createElement("div");
    nav.className = "study-actions";
    for (const [text, offset, disabled] of [
      ["Vorherige Fälle", Math.max(0, pageOffset - 250), pageOffset === 0],
      ["Weitere Fälle", pageOffset + 250, !data.page.hasMore],
    ]) {
      const button = document.createElement("button");
      button.textContent = text;
      button.disabled = disabled;
      button.onclick = () => {
        pageOffset = offset;
        reportStamp = null;
        refresh();
      };
      nav.append(button);
    }
    $("#report-content").append(nav);
  }
  $("#case-json").textContent = JSON.stringify(trials, null, 2);
}
async function refresh() {
  if (busy) return;
  busy = true;
  try {
    const data = await request("/api/research/jobs");
    jobsCache = data.items;
    const schedule = data.schedule;
    $("#schedule-state").textContent = schedule.enabled
      ? `Automatik aktiv · alle ${schedule.interval_hours} Stunden · ${schedule.spec.universe === "all" ? "gesamter Katalog" : schedule.spec.symbols.join(", ")} · ${schedule.spec.entry_mode === "tori" ? "Tori-Einstiege im Zeitraum" : `${schedule.spec.samples} Starts je Aktie`} · nächster Auftrag ${date(schedule.next_run)}. Läuft auch bei geschlossenem Browser.`
      : "Automatik pausiert. Bereits gestartete Aufträge laufen weiter.";
    $("#background-status").textContent = !data.workerActive
      ? "⚠ Kein Worker verbunden"
      : jobsCache.some((j) => j.status === "running")
        ? "● Untersuchung läuft"
        : schedule.enabled
          ? "● Automatik aktiv"
          : "Automatik pausiert";
    renderOperations(data.operations);
    if (!selected && jobsCache.length) selected = jobsCache[0].id;
    $("#jobs-list").innerHTML = jobsCache.length
      ? jobsCache
          .map(
            (job) =>
              `<button class="job-row ${job.id === selected ? "selected" : ""}" data-job="${job.id}"><b>${escapeHtml((job.universe || job.spec.symbols).slice(0, 3).join(", "))}${(job.universe || job.spec.symbols).length > 3 ? " …" : ""}</b><span class="status-pill ${job.status}">${labels[job.status] || job.status}</span><small>${date(job.created)} · ${job.automatic ? "Automatisch" : "Manuell"}<br>${job.completedTrials} ${job.spec.entry_mode === "tori" ? "Linienpaare" : "Starts"} · ${escapeHtml(job.current_symbol || `${job.symbols.filter((s) => s.done).length} Aktien bearbeitet`)}${job.progress && ["running", "cancel_requested"].includes(job.status) ? `<br>${escapeHtml(phaseLabels[job.progress.phase] || job.progress.phase)} · ${escapeHtml(progressText(job.progress))}` : ""}</small></button>`,
          )
          .join("")
      : '<p class="note">Noch keine Aufträge.</p>';
    document.querySelectorAll("[data-job]").forEach(
      (button) =>
        (button.onclick = () => {
          selected = button.dataset.job;
          pageOffset = 0;
          reportStamp = null;
          refresh();
        }),
    );
    if (!selected && jobsCache.length) selected = jobsCache[0].id;
    const job = jobsCache.find((j) => j.id === selected);
    if (job) {
      const stamp = `${job.id}|${job.updated}|${job.status}|${job.completedTrials}|${job.eventCount}|${pageOffset}|${entryFilter}|${job.symbols.map((s) => s.dataset_id + String(s.done) + s.error).join()}`;
      if (stamp !== reportStamp) {
        renderReport(
          await request(
            `/api/research/jobs/${selected}/report?offset=${pageOffset}${job.spec.entry_mode === "tori" ? `&limit=50&entry_filter=${entryFilter}` : ""}`,
          ),
        );
        reportStamp = stamp;
      }
    }
    $("#research-error").hidden = true;
  } catch (e) {
    $("#ops-worker").textContent =
      "Aktualisierung fehlgeschlagen · letzter Stand möglicherweise veraltet";
    $("#background-status").textContent = "⚠ Aktualisierung fehlgeschlagen";
    showError(e);
  } finally {
    busy = false;
  }
}
refresh();
setInterval(() => {
  if (!document.hidden) refresh();
}, 4000);
