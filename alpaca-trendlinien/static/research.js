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
  return {
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
}
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
    future && completed.length
      ? Math.max(...completed.map((x) => x.closedAt))
      : entry?.signalAt || trial.startAt;
  return (
    "/?" +
    new URLSearchParams({
      symbol: trial.symbol,
      tf: "4h",
      dataset: trial.datasetId,
      asof: new Date(at * 1000).toISOString(),
      ...(entry
        ? { job: selected, trial: trial.id, variant: entry.variant }
        : {}),
    })
  );
}
function renderReport(data) {
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
  html += `<div class="table-wrap"><table><thead><tr><th>Testgruppe</th><th>Starts mit Entry / eindeutige Signale</th>${job.spec.horizons.map((h) => `<th>Nach ${h} Kerzen · Median netto</th>`).join("")}</tr></thead><tbody>`;
  for (const variant of ["breakout", "retest"])
    for (const quality of ["provisional", "qualified"]) {
      const group = summary.groups[`${variant}_${quality}`];
      html += `<tr><td>${variant === "breakout" ? "Ausbruch" : "Retest"} · ${quality === "qualified" ? "qualifiziert" : "vorläufig"}</td><td>${group?.observed || 0} / ${group?.uniqueSignals || 0}</td>${job.spec.horizons
        .map((h) => {
          const result = group?.horizons[String(h)];
          return `<td class="${valueClass(result?.median_net_pct)}">${number(result?.median_net_pct)}${result?.n ? ` % <small>(n=${result.n}; ${result.positive} positiv)</small>` : ""}</td>`;
        })
        .join("")}</tr>`;
    }
  html +=
    '</tbody></table></div><p class="note">Netto = Kursänderung ab beobachtetem Einstieg abzüglich Kostenannahme je Seite. n zählt vollständige, eindeutige Einstiege. Keine Stop-Ausführung und keine Portfoliorendite. „Vorläufig“ enthält auch andere nicht vollständig qualifizierte Linienpaare; die exakten Kontakte stehen im Fallprotokoll.</p>';
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
      ? `Automatik aktiv · alle ${schedule.interval_hours} Stunden · ${schedule.spec.universe === "all" ? "gesamter Katalog" : schedule.spec.symbols.join(", ")} · ${schedule.spec.samples} Starts je Aktie · nächster Auftrag ${date(schedule.next_run)}. Läuft auch bei geschlossenem Browser.`
      : "Automatik pausiert. Bereits gestartete Aufträge laufen weiter.";
    $("#background-status").textContent = !data.workerActive
      ? "⚠ Kein Worker verbunden"
      : jobsCache.some((j) => j.status === "running")
        ? "● Untersuchung läuft"
        : schedule.enabled
          ? "● Automatik aktiv"
          : "Automatik pausiert";
    if (!selected && jobsCache.length) selected = jobsCache[0].id;
    $("#jobs-list").innerHTML = jobsCache.length
      ? jobsCache
          .map(
            (job) =>
              `<button class="job-row ${job.id === selected ? "selected" : ""}" data-job="${job.id}"><b>${escapeHtml((job.universe || job.spec.symbols).slice(0, 3).join(", "))}${(job.universe || job.spec.symbols).length > 3 ? " …" : ""}</b><span class="status-pill ${job.status}">${labels[job.status] || job.status}</span><small>${date(job.created)} · ${job.automatic ? "Automatisch" : "Manuell"}<br>${job.completedTrials} Starts · ${job.current_symbol || `${job.symbols.filter((s) => s.done).length} Aktien bearbeitet`}</small></button>`,
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
      const stamp = `${job.id}|${job.status}|${job.completedTrials}|${job.eventCount}|${pageOffset}|${job.symbols.map((s) => s.dataset_id + String(s.done) + s.error).join()}`;
      if (stamp !== reportStamp) {
        renderReport(
          await request(
            `/api/research/jobs/${selected}/report?offset=${pageOffset}`,
          ),
        );
        reportStamp = stamp;
      }
    }
    $("#research-error").hidden = true;
  } catch (e) {
    showError(e);
  } finally {
    busy = false;
  }
}
refresh();
setInterval(() => {
  if (!document.hidden) refresh();
}, 4000);
