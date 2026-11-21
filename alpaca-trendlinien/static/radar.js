/* Client logic for /radar: Top-10 daily Tori scan, Watchlist & 1.000-EUR papertrades. */
const $ = (sel) => document.querySelector(sel);

const radarState = {
  scan: null,
  watchlist: [],
  updates: [],
  summary: null,
};

function fmt(val, dec = 2, suffix = "") {
  if (val === null || val === undefined || !Number.isFinite(Number(val))) return "–";
  return Number(val).toFixed(dec).replace(".", ",") + suffix;
}

function fmtSigned(val, dec = 2, suffix = "") {
  if (val === null || val === undefined || !Number.isFinite(Number(val))) return "–";
  const n = Number(val);
  return (n > 0 ? "+" : "") + n.toFixed(dec).replace(".", ",") + suffix;
}

function esc(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showStatus(msg, kind = "") {
  const el = $("#radar-status");
  if (!msg) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.className = "radar-banner" + (kind ? " " + kind : "");
  el.textContent = msg;
}

function scenarioBadge(scenario) {
  const map = {
    "1A_CLEAN_BREAKOUT": ["1A · Ausbruch bestätigt", "b-clean"],
    "1B_ARMED_WAIT_CLEAN": ["1B · Knapp über Rot", "b-armed"],
    "2_IMMEDIATE_TEST": ["2 · Direkt am Widerstand", "b-imm"],
    "3_APPROACH_WATCH": ["3 · Vorwarnung (1–2T)", "b-appr"],
    "4A_RETEST_TRIGGER": ["4A · Retest bestätigt", "b-retest"],
    "4B_RETEST_APPROACH": ["4B · Retest im Anflug", "b-retest"],
    "5_FAST_A_PLUS": ["5 · Fast-A+ (vor 3K)", "b-fast"],
    "6_SAFETY_BOUNCE": ["6 · Safety-Abpraller", "b-watch"],
  };
  const [label, cls] = map[scenario] || [scenario, "b-watch"];
  return `<span class="badge ${cls}">${esc(label)}</span>`;
}

function statusBadge(status) {
  const map = {
    watching: ["Beobachtung", "b-watch"],
    pending_entry: ["Einstieg vorgemerkt", "b-armed"],
    open: ["Papertrade offen", "b-open"],
    closed: ["Geschlossen", "b-closed"],
    expired: ["Abgelaufen", "b-closed"],
    cancelled: ["Abgesagt (Gap)", "b-warn"],
    censored: ["Datenlücke", "b-warn"],
  };
  const [label, cls] = map[status] || [status, "b-watch"];
  return `<span class="badge ${cls}">${esc(label)}</span>`;
}

function reasonLabel(reason) {
  const map = {
    added_to_watchlist: "Neu aufgenommen",
    waiting_for_tori_trigger: "Wartet auf Tori-Signal",
    entry_next_open_pending: "Kauf am nächsten US-Open",
    awaiting_next_session_open: "Wartet auf US-Eröffnung",
    data_end: "Laufend (offen)",
    open: "Laufend (offen)",
    stop: "Hard-Stop ausgelöst",
    stop_gap: "Stop-Gap zur Eröffnung",
    safety_broken_before_entry: "Unter Safety gefallen (kein Kauf)",
    watch_window_expired: "Beobachtungsfrist abgelaufen",
    opening_gap_through_stop: "Eröffnung unter Stop (abgesagt)",
    missing_path: "Fehlende 5m-Kerzen",
    missing_expected_entry_open: "Fehlende 5m-Einstiegskerze",
    user_archived: "Manuell archiviert",
  };
  return map[reason] || reason || "";
}

function strategyLabel(tag, aboveSma200) {
  if (tag === "TREND_FOLLOW") return "Trendfolge (>SMA200)";
  if (tag === "REVERSAL") return "Trendwende (<SMA200)";
  if (aboveSma200 === true) return "Trendfolge (>SMA200)";
  if (aboveSma200 === false) return "Trendwende (<SMA200)";
  return "SMA200 offen";
}

function policyLabel(policy) {
  const map = {
    r2_fan: "Original bis +2R",
    qualified_fan: "Nur 3K-Safety",
    original_safety: "Urspr. Safety",
  };
  return map[policy] || policy || "";
}

function eventLabel(evType) {
  const map = {
    added: "Aufgenommen",
    signal_triggered: "Signal ausgelöst",
    papertrade_opened: "Papertrade eröffnet",
    papertrade_closed: "Papertrade geschlossen",
    r2_activated: "+2R-Meilenstein",
    stop_raised: "Stop nachgezogen",
    daily_update: "Tages-Update",
    watch_update: "Beobachtung",
    watch_expired: "Beobachtung beendet",
    entry_cancelled: "Einstieg abgesagt",
    data_gap_censored: "Datenlücke",
    archived: "Archiviert",
  };
  return map[evType] || evType || "";
}

function originLabel(origin) {
  return origin === "pivot" ? "Pivot" : origin === "refit" ? "Hüll-Anpassung" : origin || "";
}

function pnlClass(val) {
  if (val === null || val === undefined || !Number.isFinite(Number(val))) return "";
  return Number(val) > 0 ? "pos" : Number(val) < 0 ? "neg" : "";
}

function renderSummary(s) {
  if (!s) return;
  $("#kpi-watching").textContent = String((s.counts?.watching || 0) + (s.counts?.pending_entry || 0));
  $("#kpi-open").textContent = String(s.counts?.open || 0);
  $("#kpi-open-cap").textContent = `${fmt(s.openCapitalEur, 0, " €")} Kapital`;

  const openPnlEl = $("#kpi-open-pnl");
  openPnlEl.textContent = fmtSigned(s.openPnlEur, 2, " €");
  openPnlEl.className = pnlClass(s.openPnlEur);
  $("#kpi-open-pct").textContent = fmtSigned(s.openReturnPct, 2, " %");

  const realEl = $("#kpi-real-pnl");
  realEl.textContent = fmtSigned(s.realizedPnlEur, 2, " €");
  realEl.className = pnlClass(s.realizedPnlEur);
  $("#kpi-winrate").textContent =
    s.closedCount > 0
      ? `Geschlossen: ${s.closedCount} (${fmt(s.closedWinRatePct, 1, "%")} Treffer)`
      : "Geschlossen: 0";

  const totEl = $("#kpi-total-pnl");
  totEl.textContent = fmtSigned(s.totalPnlEur, 2, " €");
  totEl.className = pnlClass(s.totalPnlEur);
  $("#kpi-avg-r").textContent = `Ø R: ${s.avgClosedR !== null ? fmtSigned(s.avgClosedR, 2, " R") : "–"}`;

  if (s.modelNote) $("#model-note").textContent = s.modelNote;
}

function renderMarketRegime(regime) {
  const bar = $("#market-regime-bar");
  if (!bar) return;
  if (!regime || !regime.status || regime.status === "UNAVAILABLE") {
    bar.hidden = true;
    return;
  }
  bar.hidden = false;
  const dot = $("#regime-dot");
  dot.className = "regime-dot regime-" + String(regime.status).toLowerCase();
  $("#regime-label").textContent = regime.label || "US-Marktlage";
  $("#regime-hint").textContent = regime.hint || "";
  const bench = regime.benchmarks || {};
  const chips = ["SPY", "QQQ"]
    .map((sym) => {
      const b = bench[sym];
      if (!b || !b.available) return "";
      const cls = b.aboveSma200 === true ? "b-open" : b.aboveSma200 === false ? "b-warn" : "b-watch";
      const sign = b.distSma200Pct !== null && b.distSma200Pct !== undefined ? fmtSigned(b.distSma200Pct, 1, "%") : "–";
      return `<div class="regime-chip">
        <strong>${sym}</strong> ${fmt(b.close, 2, " $")}
        <span class="badge ${cls}">SMA200: ${fmt(b.sma200, 2, " $")} (${sign})</span>
        <small class="muted">SMA50: ${fmt(b.sma50, 2, " $")} · Stand ${esc(b.asofSession || "")}</small>
      </div>`;
    })
    .filter(Boolean)
    .join("");
  $("#regime-metrics").innerHTML = chips;
}

function inferTier(item) {
  if (item.signal_tier) return item.signal_tier;
  const direct = item.scenario === "1A_CLEAN_BREAKOUT" || item.scenario === "4A_RETEST_TRIGGER";
  const active = Boolean(item.active_approach);
  const mature = Number(item.red_age_days || 0) >= 21 || Number(item.red_contacts || 0) >= 4;
  const quiet = Boolean(item.low_daily_volatility);
  if (direct && active && mature && quiet) return "C";
  if (active && mature && quiet) return "B";
  if (quiet) return "4";
  if (direct && active && mature) return "A";
  return "BASIS";
}

function tierBadge(tier) {
  const map = {
    C: ["Stufe C · Premium", "t-c"],
    B: ["Stufe B · Stark", "t-b"],
    "4": ["Stufe 4 · Ruhig", "t-4"],
    A: ["Stufe A · 3/3-Kern", "t-a"],
    BASIS: ["Basis", "t-basis"],
  };
  const [label, cls] = map[tier] || ["Basis", "t-basis"];
  return `<span class="tier-pill ${cls}">${esc(label)}</span>`;
}

function renderScan(scan) {
  const body = $("#top10-body");
  const fastBox = $("#fast-a-box");
  const fastList = $("#fast-a-list");
  if (!scan) {
    renderMarketRegime(null);
    $("#scan-meta").textContent = "Noch kein Scan gespeichert.";
    $("#scan-audit").textContent = "";
    fastBox.hidden = true;
    return;
  }
  renderMarketRegime(scan.marketRegime || null);
  const c = scan.counts || {};
  const a = scan.audit || {};
  $("#scan-meta").textContent =
    `Zielsitzung: ${scan.session} · Geprüft: ${c.checkedSymbols}/${c.totalSymbols} · Qualifiziert (Tore 1–6): ${c.qualifiedMain} · Laufzeit: ${fmt(scan.elapsedSeconds, 1, " s")}`;
  $("#scan-audit").textContent =
    `Datenprüfung: ${a.warmupShortCount || 0} Vorlauf<320T | ${a.staleCount || 0} veraltet | ${a.missing4hCount || 0} fehl. 4H | ${a.dataProblemCount || 0} 5m-Lücken`;

  const activeSymbols = new Set(
    (radarState.watchlist || [])
      .filter((it) => ["watching", "pending_entry", "open"].includes(it.status))
      .map((it) => it.symbol),
  );

  const rows = scan.top10 || [];
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="13" class="empty">Für Zielsitzung ${esc(scan.session)} erfüllt aktuell keine Aktie alle 6 Pflicht-Tore (oder Daten sind veraltet).</td></tr>`;
  } else {
    body.innerHTML = rows
      .map((item, idx) => {
        const inWatch = activeSymbols.has(item.symbol);
        const tier = inferTier(item);
        const tierRowCls = "tier-row-" + String(tier).toLowerCase();
        const volBadge = item.low_daily_volatility ? ' <span class="badge b-clean">Ruhige Vola</span>' : "";
        const roof = item.overhead_roof_near ? ' <span class="badge b-warn">Widerstand nah</span>' : "";
        const earn = item.earnings_days !== null && item.earnings_days !== undefined
          ? ` <span class="badge b-warn">Quartalszahlen ${item.earnings_days}T</span>` : "";
        return `<tr class="${tierRowCls}">
          <td><strong>${idx + 1}</strong><br>${tierBadge(tier)}</td>
          <td><strong>${esc(item.symbol)}</strong><br><small class="muted">${esc(item.universes)}</small></td>
          <td>${scenarioBadge(item.scenario)}</td>
          <td><strong>${item.score}/10</strong></td>
          <td>${fmt(item.close_4h, 2, " $")}</td>
          <td>${fmt(item.dist_to_red_atr, 2, " ATR")}<br><small class="muted">${fmt(item.dist_to_red_pct, 1, "%")}</small></td>
          <td><strong>${fmt(item.clean_trigger_next1, 2, " $")}</strong><br><small class="muted">Kerze 2: ${fmt(item.clean_trigger_next2, 2, " $")}</small></td>
          <td><strong>${fmt(item.stop_0_3_pct, 2, " $")}</strong></td>
          <td>${fmt(item.risk_pct, 1, "%")}<br><small class="muted">${fmt(item.risk_atr, 1, " ATR")}</small></td>
          <td>${fmt(item.target_plus_2r_price, 2, " $")}</td>
          <td>Rot: ${item.red_contacts}K / ${fmt(item.red_age_days, 0, "T")} (${esc(originLabel(item.red_origin))})<br><small class="muted">Grün: ${item.green_contacts}K / ${fmt(item.green_age_days, 0, "T")}</small></td>
          <td>${esc(strategyLabel(item.strategy_tag, item.above_sma200))}${volBadge}${roof}${earn}</td>
          <td>
            <div class="action-row">
              <a class="btn-mini" href="${esc(item.chart_path)}" target="_blank" rel="noopener">Chart</a>
              <button class="btn-mini accent" data-add="${esc(item.symbol)}" ${inWatch ? "disabled" : ""}>
                ${inWatch ? "Auf Watchlist" : "+ Watchlist (1.000 €)"}
              </button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  const fast = scan.fastAPlus || [];
  if (!fast.length) {
    fastBox.hidden = true;
  } else {
    fastBox.hidden = false;
    fastList.innerHTML = fast
      .map((item) => {
        const inWatch = activeSymbols.has(item.symbol);
        return `<div class="fast-a-card">
          <strong>${esc(item.symbol)}</strong>
          <span>${item.score}/10 Pkt. · ${fmt(item.dist_to_red_atr, 2, " ATR")} · 2K / ${fmt(item.red_age_days, 0, "T")}</span>
          <a class="btn-mini" href="${esc(item.chart_path)}" target="_blank" rel="noopener">Chart</a>
          <button class="btn-mini accent" data-add="${esc(item.symbol)}" ${inWatch ? "disabled" : ""}>
            ${inWatch ? "Beobachtet" : "+ Watchlist"}
          </button>
        </div>`;
      })
      .join("");
  }
}

function renderWatchlist(items) {
  const body = $("#watch-body");
  if (!items || !items.length) {
    body.innerHTML = `<tr><td colspan="10" class="empty">Noch keine Aktien auf der Watchlist. Klicke bei einem Top-10-Kandidaten auf „+ Watchlist (1.000 €)“.</td></tr>`;
    return;
  }
  body.innerHTML = items
    .map((it) => {
      const t = it.trade || {};
      const pnlEur = t.pnlEur;
      const pnlPct = t.pnlPct;
      const cls = pnlClass(pnlEur);
      const entryText = t.entryPrice
        ? `${fmt(t.entryPrice, 2, " $")}<br><small class="muted">${esc(t.entrySession || "")}</small>`
        : t.triggerProjected
          ? `Wartet<br><small class="muted">Schwelle ${fmt(t.triggerProjected, 2, " $")}</small>`
          : "Wartet";
      const stopText = `${fmt(t.stopCurrent ?? t.initialStop ?? t.initialStopPlanned, 2, " $")}<br><small class="muted">${esc(policyLabel(it.stop_policy))}${t.r2ActivatedAt ? " (+2R aktiv)" : ""}</small>`;
      const rText =
        t.rMultiple !== null && t.rMultiple !== undefined
          ? `<span class="${cls}"><strong>${fmtSigned(t.rMultiple, 2, " R")}</strong></span><br><small class="muted">Max ${fmtSigned(t.mfeR, 1, "R")} / Min ${fmtSigned(t.maeR, 1, "R")}</small>`
          : "–";
      const chartLink = t.chartPath
        ? `<a class="btn-mini" href="${esc(t.chartPath)}" target="_blank" rel="noopener">Chart</a>`
        : "";
      return `<tr>
        <td><strong>${esc(it.symbol)}</strong><br><small class="muted">${fmt(it.capital_eur, 0, " €")}</small></td>
        <td>${statusBadge(it.status)}<br><small class="muted">${esc(reasonLabel(it.status_reason))}</small></td>
        <td>${esc(it.source_session)}<br><small class="muted">${scenarioBadge(it.source_scenario)}</small></td>
        <td>${entryText}</td>
        <td>${fmt(t.lastClose, 2, " $")}<br><small class="muted">${esc(it.last_session || "")}</small></td>
        <td>${stopText}</td>
        <td class="${cls}"><strong>${fmtSigned(pnlEur, 2, " €")}</strong><br><small>${fmtSigned(pnlPct, 2, "%")}</small></td>
        <td>${rText}</td>
        <td>
          <input class="note-input" data-note-id="${esc(it.id)}" value="${esc(it.note || "")}" placeholder="Sichtprüfung …" />
        </td>
        <td>
          <div class="action-row">
            ${chartLink}
            <button class="btn-mini danger" data-archive="${esc(it.id)}">Archivieren</button>
          </div>
        </td>
      </tr>`;
    })
    .join("");
}

function renderUpdates(updates) {
  const list = $("#updates-list");
  if (!updates || !updates.length) {
    list.innerHTML = `<li class="empty">Noch keine Entwicklungs-Updates vorhanden.</li>`;
    return;
  }
  list.innerHTML = updates
    .map(
      (u) => `<li>
        <div><strong>${esc(u.symbol)}</strong> · ${esc(u.summary)}</div>
        <div class="upd-meta">${esc(u.session)} · ${esc(eventLabel(u.event_type))}</div>
      </li>`,
    )
    .join("");
}

async function apiJson(url, opts = {}) {
  const resp = await apiFetch(url, opts);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
  return data;
}

async function loadState() {
  try {
    const data = await apiJson("/api/radar/state");
    radarState.scan = data.scan;
    radarState.watchlist = data.watchlist || [];
    radarState.updates = data.updates || [];
    radarState.summary = data.summary;
    renderSummary(radarState.summary);
    renderScan(radarState.scan);
    renderWatchlist(radarState.watchlist);
    renderUpdates(radarState.updates);
  } catch (err) {
    showStatus(`Fehler beim Laden: ${err.message}`, "error");
  }
}

async function runScan() {
  const btn = $("#btn-scan");
  btn.disabled = true;
  showStatus("Führe streng kausalen Top-10-Scan über das lokale SIP-Archiv aus …");
  try {
    const data = await apiJson("/api/radar/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session: $("#inp-session").value.trim() || "latest",
        universe: $("#sel-universe").value,
        scenario: $("#sel-scenario").value,
        minScore: Number($("#sel-min-score").value || 0),
        qualityFilter: $("#sel-quality") ? $("#sel-quality").value : "all",
        topN: 10,
      }),
    });
    radarState.scan = data.scan;
    renderScan(radarState.scan);
    showStatus(
      `Scan abgeschlossen (${data.scan.session}): ${data.scan.counts.topCount} Top-Kandidaten aus ${data.scan.counts.checkedSymbols} geprüften Aktien in ${fmt(data.scan.elapsedSeconds, 1, " s")}.`,
      "ok",
    );
  } catch (err) {
    showStatus(`Scan fehlgeschlagen: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

async function addToWatchlist(symbol) {
  showStatus(`Übernehme ${symbol} mit 1.000 € Kapital auf die Watchlist …`);
  try {
    const data = await apiJson("/api/radar/watchlist/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        capitalEur: 1000,
        stopPolicy: $("#sel-stop-policy").value,
      }),
    });
    radarState.watchlist = data.watchlist || [];
    radarState.summary = data.summary;
    radarState.updates = data.updates || [];
    renderSummary(radarState.summary);
    renderScan(radarState.scan);
    renderWatchlist(radarState.watchlist);
    renderUpdates(radarState.updates);
    showStatus(
      data.created
        ? `${symbol} wurde mit 1.000 € Kapital auf die Watchlist aufgenommen (Status: ${reasonLabel(data.item.status_reason) || data.item.status}).`
        : `${symbol} ist bereits aktiv auf der Watchlist.`,
      "ok",
    );
  } catch (err) {
    showStatus(`Aufnahme fehlgeschlagen: ${err.message}`, "error");
  }
}

async function evaluateWatchlist() {
  const btn = $("#btn-eval");
  btn.disabled = true;
  showStatus("Prüfe alle Watchlist- und 1.000-€-Papertrade-Positionen kausal gegen die lokalen Daten …");
  try {
    const data = await apiJson("/api/radar/watchlist/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    radarState.watchlist = data.watchlist || [];
    radarState.summary = data.summary;
    radarState.updates = data.updates || [];
    renderSummary(radarState.summary);
    renderWatchlist(radarState.watchlist);
    renderUpdates(radarState.updates);
    showStatus(
      `Aktualisierung fertig: ${data.evaluated} Einträge geprüft, ${data.newUpdates.length} neue Entwicklungs-Updates.`,
      "ok",
    );
  } catch (err) {
    showStatus(`Aktualisierung fehlgeschlagen: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("#btn-scan").addEventListener("click", runScan);
  $("#btn-eval").addEventListener("click", evaluateWatchlist);

  document.body.addEventListener("click", async (ev) => {
    const addBtn = ev.target.closest("button[data-add]");
    if (addBtn) {
      addBtn.disabled = true;
      await addToWatchlist(addBtn.dataset.add);
      return;
    }
    const archBtn = ev.target.closest("button[data-archive]");
    if (archBtn) {
      try {
        const data = await apiJson("/api/radar/watchlist/archive", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: archBtn.dataset.archive }),
        });
        radarState.watchlist = data.watchlist || [];
        radarState.summary = data.summary;
        radarState.updates = data.updates || [];
        renderSummary(radarState.summary);
        renderScan(radarState.scan);
        renderWatchlist(radarState.watchlist);
        renderUpdates(radarState.updates);
      } catch (err) {
        showStatus(`Archivierung fehlgeschlagen: ${err.message}`, "error");
      }
    }
  });

  document.body.addEventListener("change", async (ev) => {
    const inp = ev.target.closest("input[data-note-id]");
    if (!inp) return;
    try {
      await apiJson("/api/radar/watchlist/note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: inp.dataset.noteId, note: inp.value }),
      });
    } catch (err) {
      showStatus(`Notiz konnte nicht gespeichert werden: ${err.message}`, "error");
    }
  });

  loadState();
});
