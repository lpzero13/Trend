/* Client logic for /backtest: Filterable PIT Backtest Explorer & 1-Click Replay Training. */
const $ = (sel) => document.querySelector(sel);

async function apiJson(url, opts = {}) {
  const resp = await apiFetch(url, opts);
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.error || `HTTP ${resp.status}`);
  }
  return data;
}

const btState = {
  page: 1,
  pages: 1,
  yearsLoaded: false,
  blind: false,
  revealedIds: new Set(),
  lastData: null,
};

function esc(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmt(val, dec = 2, suffix = "") {
  if (val === null || val === undefined || !Number.isFinite(Number(val))) return "–";
  return Number(val).toFixed(dec).replace(".", ",") + suffix;
}

function fmtSigned(val, dec = 2, suffix = "") {
  if (val === null || val === undefined || !Number.isFinite(Number(val))) return "–";
  const n = Number(val);
  return (n > 0 ? "+" : "") + n.toFixed(dec).replace(".", ",") + suffix;
}

function pnlClass(v) {
  if (v === null || v === undefined || !Number.isFinite(Number(v))) return "";
  if (Number(v) > 0) return "pos";
  if (Number(v) < 0) return "neg";
  return "";
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

function scenarioLabel(s) {
  const map = {
    "1A_CLEAN_BREAKOUT": ["1A · Ausbruch", "b-clean"],
    "1B_ARMED_WAIT_CLEAN": ["1B · Knapp über Rot", "b-armed"],
    "2_IMMEDIATE_TEST": ["2 · Direkt am Wid.", "b-imm"],
    "3_APPROACH_WATCH": ["3 · Vorwarnung", "b-appr"],
    "4A_RETEST_TRIGGER": ["4A · Retest", "b-retest"],
    "4B_RETEST_APPROACH": ["4B · Retest-Anflug", "b-retest"],
  };
  const [label, cls] = map[s] || [s || "–", "b-watch"];
  return `<span class="badge ${cls}">${esc(label)}</span>`;
}

function outcomeReasonLabel(out) {
  if (!out || !out.status) return "–";
  if (out.status === "censored") return "Datenlücke (5m)";
  if (out.status === "open") return "Offen am Studienende";
  const map = {
    stop: "Hard-Stop",
    stop_gap: "Stop-Gap (Open)",
    data_end: "Studienende",
  };
  const base = map[out.reason] || out.reason || "Geschlossen";
  return out.r2Activated ? `${base} · +2R aktiv` : base;
}

function showStatus(msg, kind = "") {
  const el = $("#bt-status");
  if (!msg) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.className = "radar-banner" + (kind ? " " + kind : "");
  el.textContent = msg;
}

function renderSummary(data) {
  const s = data.summary || {};
  const study = data.study || {};
  $("#bt-kpi-count").textContent = `${s.totalSignals ?? 0} (${s.evaluated ?? 0})`;
  $("#bt-kpi-cens").textContent = `Geschl.: ${s.closed ?? 0} · Offen: ${s.open ?? 0} · Lücke: ${s.censored ?? 0}`;

  if (btState.blind) {
    $("#bt-kpi-win").textContent = "Verdeckt";
    $("#bt-kpi-r2").textContent = "Blind-Training aktiv";
    $("#bt-kpi-pnl").textContent = "Verdeckt";
    $("#bt-kpi-pnl").className = "";
    $("#bt-kpi-avgeur").textContent = "Klicke „Im Replay starten“";
    $("#bt-kpi-avgr").textContent = "Verdeckt";
    $("#bt-kpi-avgr").className = "";
    $("#bt-kpi-medr").textContent = "–";
    $("#bt-kpi-ex3").textContent = "Verdeckt";
    $("#bt-kpi-ex3").className = "";
  } else {
    $("#bt-kpi-win").textContent = fmt(s.winRatePct, 1, " %");
    $("#bt-kpi-r2").textContent = `+2R Quote: ${fmt(s.r2RatePct, 1, " %")}`;
    const pnlEl = $("#bt-kpi-pnl");
    pnlEl.textContent = fmtSigned(s.totalPnlEur, 2, " €");
    pnlEl.className = pnlClass(s.totalPnlEur);
    $("#bt-kpi-avgeur").textContent = `Ø €: ${fmtSigned(s.avgPnlEur, 2, " €")}`;

    const rEl = $("#bt-kpi-avgr");
    rEl.textContent = fmtSigned(s.avgR, 3, " R");
    rEl.className = pnlClass(s.avgR);
    $("#bt-kpi-medr").textContent = `Median R: ${fmtSigned(s.medianR, 3, " R")}`;

    const exEl = $("#bt-kpi-ex3");
    exEl.textContent = fmtSigned(s.avgRExTop3, 3, " R");
    exEl.className = pnlClass(s.avgRExTop3);
  }
  $("#bt-kpi-study").textContent = `${study.id || ""} (${study.symbolCount || 0} Aktien${study.pointInTime ? ", PIT" : ""})`;
}

function renderTable(data) {
  const body = $("#bt-body");
  const pg = data.pagination || { page: 1, pages: 1, total: 0 };
  btState.page = pg.page;
  btState.pages = pg.pages;
  $("#bt-page-info").textContent = `Seite ${pg.page} / ${pg.pages} (${pg.total} Treffer)`;
  $("#bt-prev").disabled = pg.page <= 1;
  $("#bt-next").disabled = pg.page >= pg.pages;

  const tc = (data.summary && data.summary.tierCounts) || {};
  $("#bt-meta").textContent =
    `Stufen im aktuellen Filter: C: ${tc.C || 0} · B: ${tc.B || 0} · 4: ${tc["4"] || 0} · A: ${tc.A || 0} · Basis: ${tc.BASIS || 0}`;

  const items = data.items || [];
  if (!items.length) {
    body.innerHTML = `<tr><td colspan="11" class="empty">Keine historischen Signale für diese Filterauswahl gefunden.</td></tr>`;
    return;
  }

  body.innerHTML = items
    .map((it) => {
      const out = it.outcome || {};
      const rowCls = "tier-row-" + String(it.tier || "basis").toLowerCase();
      const hidden = btState.blind && !btState.revealedIds.has(it.id);
      const cls = pnlClass(out.pnlEur);
      const watchNote =
        it.watchDay && it.watchDay !== it.entryDay
          ? `<br><small class="muted">Vorw.: ${esc(it.watchDay)}</small>`
          : "";
      const volBadge = it.lowVol ? ' <span class="badge b-clean">Ruhig</span>' : "";
      const outcomeCols = hidden
        ? `<td colspan="3" class="blind-cell">
             <span class="muted">Verdeckt</span>
             <button class="btn-mini" data-reveal="${esc(it.id)}">Aufdecken</button>
           </td>`
        : `<td class="${cls}"><strong>${fmtSigned(out.pnlEur, 2, " €")}</strong><br><small class="muted">${fmtSigned(out.returnPct, 2, " %")}</small></td>
           <td class="${cls}"><strong>${fmtSigned(out.netR, 2, " R")}</strong><br><small class="muted">${fmtSigned(out.mfeR, 1, "R")} / ${fmtSigned(out.maeR, 1, "R")}</small></td>
           <td>${esc(outcomeReasonLabel(out))}<br><small class="muted">${out.holdingDays != null ? fmt(out.holdingDays, 0, " Tage") : "–"}</small></td>`;

      const watchBtn =
        it.watchDay && it.watchDay !== it.entryDay
          ? `<a class="btn-mini" href="${esc(it.watchReplayUrl)}" target="_blank" rel="noopener" title="Ab Vorwarnungstag ${esc(it.watchDay)} im Chart starten">Vorw.</a>`
          : "";

      return `<tr class="${rowCls}">
        <td>${tierBadge(it.tier)}<br><small class="muted">${esc(it.split)}</small></td>
        <td><strong>${esc(it.entryDay)}</strong>${watchNote}</td>
        <td><strong>${esc(it.symbol)}</strong><br><small class="muted">${esc(it.universes)}</small></td>
        <td>
          <div class="action-row">
            <a class="btn-mini accent" href="${esc(it.replayUrl)}" target="_blank" rel="noopener" title="4H-Chart exakt am Ende von ${esc(it.entryDay)} ohne Zukunftsspoiler öffnen">▶ Replay</a>
            ${watchBtn}
          </div>
        </td>
        ${outcomeCols}
        <td>${scenarioLabel(it.scenario)}<br><small class="muted">${it.score ?? "–"}/10 Pkt.</small></td>
        <td>${fmt(it.entryPrice, 2, " $")}<br><small class="muted">Stop ${fmt(it.initialStop, 2, " $")}</small></td>
        <td>${fmt(it.riskPct, 1, "%")} / ${fmt(it.riskAtr, 1, " ATR")}<br><small class="muted">ATR: ${fmt(it.atr1dPct, 2, "%")}</small>${volBadge}</td>
        <td>${it.redContacts ?? "–"}K / ${fmt(it.redAgeDays, 0, "T")}<br><small class="muted">${it.redOrigin === "pivot" ? "Pivot" : "Nachjust."}</small></td>
      </tr>`;
    })
    .join("");
}

async function fetchTrades(page = 1) {
  const params = new URLSearchParams({
    tier: $("#bt-tier").value,
    split: $("#bt-split").value,
    year: $("#bt-year").value,
    scenario: $("#bt-scenario").value,
    outcome: $("#bt-outcome").value,
    policy: $("#bt-policy").value,
    sort: $("#bt-sort").value,
    symbol: $("#bt-symbol").value.trim(),
    page: String(page),
    limit: "100",
  });
  showStatus("Lade gefilterte Backtest-Signale …");
  try {
    const data = await apiJson("/api/backtest/trades?" + params.toString());
    if (!btState.yearsLoaded && Array.isArray(data.years)) {
      const sel = $("#bt-year");
      const cur = sel.value;
      sel.innerHTML = `<option value="all">Alle Jahre</option>` +
        data.years.map((y) => `<option value="${esc(y)}">${esc(y)}</option>`).join("");
      sel.value = cur;
      btState.yearsLoaded = true;
    }
    btState.lastData = data;
    renderSummary(data);
    renderTable(data);
    showStatus("");
  } catch (err) {
    showStatus(`Fehler beim Laden der Backtest-Daten: ${err.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  for (const id of ["#bt-tier", "#bt-split", "#bt-year", "#bt-scenario", "#bt-outcome", "#bt-policy", "#bt-sort"]) {
    $(id).addEventListener("change", () => fetchTrades(1));
  }
  let symTimer = null;
  $("#bt-symbol").addEventListener("input", () => {
    clearTimeout(symTimer);
    symTimer = setTimeout(() => fetchTrades(1), 260);
  });
  $("#bt-prev").addEventListener("click", () => {
    if (btState.page > 1) fetchTrades(btState.page - 1);
  });
  $("#bt-next").addEventListener("click", () => {
    if (btState.page < btState.pages) fetchTrades(btState.page + 1);
  });
  $("#chk-blind").addEventListener("change", (ev) => {
    btState.blind = Boolean(ev.target.checked);
    btState.revealedIds.clear();
    if (btState.lastData) {
      renderSummary(btState.lastData);
      renderTable(btState.lastData);
    }
  });
  $("#bt-body").addEventListener("click", (ev) => {
    const btn = ev.target.closest("button[data-reveal]");
    if (!btn) return;
    btState.revealedIds.add(btn.dataset.reveal);
    if (btState.lastData) renderTable(btState.lastData);
  });

  fetchTrades(1);
});
