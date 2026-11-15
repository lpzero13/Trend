"use strict";

const byId = id => document.getElementById(id);
const clock = new Intl.DateTimeFormat("de-DE", {
  dateStyle: "short", timeStyle: "medium", timeZone: "Europe/Berlin",
});
const date = at => at ? clock.format(at * 1000) : "–";
const usd = value => new Intl.NumberFormat("de-DE", {
  style: "currency", currency: "USD", maximumFractionDigits: 2,
}).format(Number(value));
const labels = {
  draft: "Entwurf", watching: "Beobachtet", pending: "Einstieg vorgemerkt",
  open: "Position offen", closed: "Abgeschlossen", rejected: "Entry abgelehnt",
  expired: "Abgelaufen", invalidated: "Safety verletzt", cancelled: "Beendet",
  unresolved: "Unvollständig beendet",
  ambiguous: "Stop und Ziel in derselben Minute", waiting: "Wartet",
  market_closed: "Markt geschlossen", error: "Abruffehler", polling: "Ruft ab",
  catching_up: "Holt Marktzeit nach", attention: "Prüfung erforderlich", stopped: "Gestoppt",
  missing_or_no_trade: "Erwartete Minute fehlt", revision: "Verarbeiteter Kurs wurde revidiert",
  corporate_action: "Kapitalmaßnahme", ambiguous_stop_target: "Intraminütige Reihenfolge offen",
};
const label = key => labels[key] || key || "–";
let shown = null;
let journal = { after: 0, through: null };
let submitId = null;

function requestId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, "0")).join("");
}

function paragraph(parent, text) {
  const node = document.createElement("p");
  node.textContent = text;
  parent.append(node);
}

function button(parent, text, handler) {
  const node = document.createElement("button");
  node.type = "button";
  node.textContent = text;
  node.addEventListener("click", () => safe(handler));
  parent.append(node);
}

async function request(path, body) {
  const options = body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const response = await fetch("/api/paper/" + path, options);
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.error || "Anfrage fehlgeschlagen (" + response.status + ").");
  }
  return response.json();
}

async function safe(action) {
  try { await action(); }
  catch (error) { byId("message").textContent = error.message; }
}

function payload(item, extra = {}) {
  return { request_id: requestId(), expected_updated: item.updated, ...extra };
}

async function command(item, action, extra) {
  await request("plans/" + item.id + "/" + action, payload(item, extra));
  await refreshStatus();
}

function renderAccount(state) {
  const root = byId("account-view");
  root.replaceChildren();
  byId("account-form").hidden = Boolean(state.account);
  if (!state.account) {
    paragraph(root, "Lege zuerst das USD-Simulationskonto an.");
    return;
  }
  paragraph(root, "Cash " + usd(state.cash) + " · Equity " + usd(state.equity) +
    " · Realisiert " + usd(state.realized_pnl) + " · Offene Buch-P/L " + usd(state.open_pnl));
  paragraph(root, "Marktzeit verarbeitet bis " + date(state.cursor) + " · Letzter Abruf " +
    date(state.worker.last_import) + " · Worker " + (state.worker.heartbeat_stale ? "offline / veraltet" : label(state.worker.phase)));
  if (state.worker.market_lag_seconds != null && state.worker.phase !== "market_closed") {
    paragraph(root, "Verarbeiteter Marktstand beim letzten Worker-Lauf " +
      Math.floor(state.worker.market_lag_seconds / 60) + " Minuten zurück.");
  }
  if (!state.valuation_complete) paragraph(root, "Gezeigt wird der letzte sichere Bewertungsstand.");
  if (state.worker.error) paragraph(root, state.worker.error);
  for (const issue of state.issues) paragraph(root, issue.symbol + " · " + label(issue.kind) + " · " + date(issue.at));
}

function renderPlan(plan) {
  const row = document.createElement("article");
  row.className = "plan";
  const spec = plan.spec;
  const data = plan.data;
  paragraph(row, spec.symbol + " · " + spec.timeframe + " · " + label(plan.state) +
    " · Ablauf " + date(spec.expires_at));
  if (plan.next_check_at) paragraph(row, "Nächster Strategieschluss " + date(plan.next_check_at));
  if (plan.next_entry_at) paragraph(row, "Vorgemerkte Einstiegsminute " + date(plan.next_entry_at));
  const position = data.position;
  if (position) {
    const openPnl = usd(Number(position.mark) * position.quantity - Number(position.entry_cost));
    paragraph(row, position.quantity + " Stück · Entry " + usd(position.fill) + " am " + date(position.at) +
      (spec.hard_stop ? " · Stop " + usd(position.stop) : "") + (position.target ? " · Ziel " + usd(position.target) : ""));
    if (data.exit) {
      paragraph(row, "Exit " + usd(data.exit.fill) + " · " + date(data.exit.at) +
        " · Netto " + usd(data.exit.pnl) + " · " + data.exit.r + " R · " + data.exit.reason);
    } else if (plan.state === "open") {
      paragraph(row, "Buch-P/L " + openPnl + " · Kurszeit " + date(position.mark_at));
    }
  }
  for (const [sessions, mark] of Object.entries(data.horizon_marks || {})) {
    paragraph(row, "Buch-P/L nach " + sessions + " Sitzungen · " + usd(mark.pnl) + " · " + date(mark.at));
  }
  const actions = document.createElement("div");
  actions.className = "actions";
  row.append(actions);
  button(actions, "Planvorschau", () => openPreview(plan.id));
  if (["draft", "watching", "pending"].includes(plan.state)) {
    if (data.cancel_at) {
      paragraph(row, "Beendigung angefordert um " + date(data.cancel_at));
      button(actions, "Bei Datenblockade als unvollständig beenden", async () => {
        if (confirm("Den blockierten Plan ohne Anlage eines Trades als unvollständig beenden?")) await command(plan, "abandon");
      });
    }
    else button(actions, "Plan beenden", async () => {
      if (confirm("Diesen Plan beenden?")) await command(plan, "cancel");
    });
  }
  if (plan.state === "open" && !data.manual_at) button(actions, "Paper-Exit anfordern", async () => {
    if (confirm("Paper-Exit ab jetzt zum nächsten regulären Minuten-Open anfordern?")) await command(plan, "exit");
  });
  if (plan.state === "ambiguous") {
    for (const side of ["stop", "target"]) {
      const name = side === "stop" ? "Stop" : "Ziel";
      button(actions, name + " als Szenario verbuchen", async () => {
        if (confirm(name + " als dokumentierte Auflösung dieser Minute übernehmen?")) await command(plan, "resolve_" + side);
      });
    }
  }
  return row;
}

async function refreshStatus() {
  const state = await request("status");
  renderAccount(state);
  byId("plans").replaceChildren(...state.plans.map(renderPlan));
}

function plot(rows) {
  const canvas = byId("preview-chart");
  canvas.hidden = !rows.length;
  if (!rows.length) return;
  const bounds = canvas.getBoundingClientRect();
  const width = Math.max(1, bounds.width);
  const height = 230;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  const values = rows.flatMap(row => [Number(row.action), Number(row.safety), ...(row.ohlc || []).map(Number)]);
  const low = Math.min(...values);
  const range = Math.max(Math.max(...values) - low, .01);
  const distance = Math.max(rows.at(-1).ordinal, 1);
  const x = i => 20 + (width - 85) * rows[i].ordinal / distance;
  const y = v => height - 22 - (Number(v) - low) / range * (height - 44);
  ctx.font = "11px system-ui";
  ctx.fillStyle = getComputedStyle(canvas).color;
  ctx.fillText(String((low + range).toFixed(2)), width - 55, 22);
  ctx.fillText(String(low.toFixed(2)), width - 55, height - 22);
  for (const [i, row] of rows.entries()) {
    if (!row.ohlc) continue;
    const [open, high, lowPrice, close] = row.ohlc;
    ctx.fillStyle = Number(close) >= Number(open) ? "#087e67" : "#cb4653";
    ctx.fillRect(x(i), y(high), 1, Math.max(1, y(lowPrice)-y(high)));
    ctx.fillRect(x(i)-5, Math.min(y(open), y(close)), 11, Math.max(1, Math.abs(y(open)-y(close))));
  }
  for (const [key, color] of [["action", "#f24561"], ["safety", "#16a474"]]) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    rows.forEach((row, i) => i ? ctx.lineTo(x(i), y(row[key])) : ctx.moveTo(x(i), y(row[key])));
    ctx.stroke();
  }
}

async function openPreview(identity) {
  const value = await request("plans/" + identity);
  shown = value;
  const draft = value.plan.state === "draft";
  byId("preview").hidden = false;
  const spec = value.plan.spec;
  const config = value.account;
  const summary = byId("preview-summary");
  summary.replaceChildren();
  const anchors = points => points.map(point => date(point.at) + " / " + usd(point.price)).join(" → ");
  for (const [name, text] of [
    ["Plan", spec.symbol + " · " + spec.timeframe + " · " + label(value.plan.state)],
    ["Rote Linie", anchors(spec.action)], ["Grüne Linie", anchors(spec.safety)],
    ["Gültigkeit", (spec.effective_from ? date(spec.effective_from) : "Ab Aktivierung") + " bis " + date(spec.expires_at)],
    ["Einstieg", "Bestätigtes Kreuzen über Rot · nächstes reguläres Minuten-Open" +
      (spec.max_entry ? " · maximal " + usd(spec.max_entry) : "")],
    ["Schutz", "Safety-Schluss-Exit" + (spec.hard_stop ? " plus fester Stop" : "") +
      " · Puffer für die Risikorechnung " + spec.buffer_pct + " %"],
    ["Weitere Exits", [spec.target_price ? "Ziel " + usd(spec.target_price) : "",
      spec.time_exit_sessions ? "Zeitexit nach " + spec.time_exit_sessions + " Sitzungen" : ""].filter(Boolean).join(" · ") || "–"],
    ["Konto", usd(config.capital) + " Startkapital · " + spec.risk_pct + " % Zielrisiko · " +
      usd(config.fee) + " Gebühr und " + config.slippage_bps + " bp Slippage pro Seite"],
  ]) {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = name;
    description.textContent = text;
    summary.append(term, description);
  }
  byId("preview-json").textContent = JSON.stringify({
    plan: value.plan.spec, account: value.account, reference_at: date(value.reference_at),
    reference_close: value.reference_close, action: value.action_price, safety: value.safety_price,
    sample: value.sample,
  }, null, 2);
  const warning = value.above_action === true ? "Der Referenzschluss liegt bereits über Rot. Der Plan wartet auf einen neuen Kreuzungsfall." :
    value.above_action === false ? "Der Referenzschluss liegt auf oder unter Rot." : "Für den Referenzschluss liegt noch kein vollständiger Balken in der Vorschau vor.";
  const source = value.sample?.error || (value.sample?.rows.length
    ? "Die Vorschau zeigt die Ankerkerzen und den Referenzschluss auf der Handelskerzenachse."
    : "Eine Kursvorschau kann der Worker auf ausdrückliche Anforderung abrufen.");
  byId("preview-note").textContent = warning + " " + source;
  plot(value.sample?.rows || []);
  byId("prepare").hidden = !draft;
  byId("activate").hidden = !draft;
  byId("preview").scrollIntoView({ block: "nearest" });
}

async function loadJournal(reset) {
  if (reset) byId("journal").replaceChildren();
  const params = new URLSearchParams({ limit: "30", after: String(reset ? 0 : journal.after) });
  if (!reset && journal.through !== null) params.set("through", journal.through);
  const page = await request("events?" + params);
  for (const event of page.items) {
    const node = document.createElement("li");
    node.textContent = date(event.at) + " · " + (event.symbol || "Konto") + " · " + label(event.kind);
    byId("journal").append(node);
  }
  journal = { after: page.next, through: page.through };
  byId("journal-next").disabled = journal.after >= journal.through;
}

byId("account-form").addEventListener("submit", event => {
  event.preventDefault();
  safe(async () => {
    const values = new FormData(event.currentTarget);
    await request("account", { capital: values.get("capital"), fee: values.get("fee"), slippage_bps: Number(values.get("slippage")) });
    await refreshStatus();
  });
});
byId("plan-form").addEventListener("submit", event => {
  event.preventDefault();
  const form = event.currentTarget;
  safe(async () => {
    const values = new FormData(form);
    const setup = Object.fromEntries(["symbol", "timeframe", "expires_at", "buffer_pct", "risk_pct", "note"]
      .map(key => [key, values.get(key).trim()]));
    setup.symbol = setup.symbol.toUpperCase();
    for (const key of ["effective_from", "max_entry", "target_price"]) setup[key] = values.get(key).trim() || null;
    setup.priority = Number(values.get("priority"));
    setup.time_exit_sessions = values.get("time_exit_sessions") ? Number(values.get("time_exit_sessions")) : null;
    setup.horizons = values.get("horizons").trim() ? values.get("horizons").split(",").map(Number) : [];
    setup.hard_stop = values.has("hard_stop");
    for (const line of ["action", "safety"]) setup[line] = [1, 2].map(i => ({
      at: values.get(line + "_at_" + i).trim(), price: values.get(line + "_price_" + i),
    }));
    const key = JSON.stringify(setup);
    if (submitId?.key !== key) submitId = { key, id: requestId() };
    const plan = await request("plans", { request_id: submitId.id, setup });
    await refreshStatus();
    await openPreview(plan.id);
  });
});
byId("prepare").addEventListener("click", () => safe(async () => {
  await command(shown.plan, "prepare");
  await openPreview(shown.plan.id);
}));
byId("preview-refresh").addEventListener("click", () => safe(() => openPreview(shown.plan.id)));
byId("activate").addEventListener("click", () => safe(async () => {
  if (!confirm("Die angezeigten Linien, Exitregeln und Kontoannahmen für diesen Plan bestätigen?")) return;
  await command(shown.plan, "activate", { confirmation: shown.confirmation });
  await openPreview(shown.plan.id);
}));
byId("refresh").addEventListener("click", () => safe(async () => { await refreshStatus(); await loadJournal(true); }));
byId("journal-next").addEventListener("click", () => safe(() => loadJournal(false)));
window.addEventListener("resize", () => plot(shown?.sample?.rows || []));
safe(async () => { await refreshStatus(); await loadJournal(true); });
