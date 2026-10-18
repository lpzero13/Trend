(function (root) {
  "use strict";
  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const number = (value) => value == null ? "—" : new Intl.NumberFormat("de-DE", { maximumFractionDigits: 2 }).format(value);
  function rayPoints(ray, bars) {
    if (!ray) return [];
    const a = bars.findIndex((b) => b.time === ray.a_time), b = bars.findIndex((b) => b.time === ray.b_time);
    if (a < 0 || b <= a) return [];
    const slope = (ray.b_price - ray.a_price) / (b - a);
    return bars.slice(a).map((bar, i) => ({ time: bar.time, value: ray.a_price + slope * i }));
  }
  function groupsFor(summary, section, horizon, kind) {
    return Object.values(summary.sections?.[section]?.groups || {}).filter((g) => g.kind === kind).map((g) => ({...g, outcome:g.horizons[String(horizon)] || {}}));
  }
  const helpers = { escape, number, rayPoints, groupsFor };
  if (typeof module !== "undefined" && module.exports) module.exports = helpers;
  root.ToriLab = helpers;
  if (typeof document === "undefined") return;

  const $ = (id) => document.getElementById(id), LC = root.LightweightCharts;
  const date = (at) => at ? new Date(at * 1000).toLocaleString("de-DE", {timeZone:"America/New_York", dateStyle:"short", timeStyle:"short"}) + " NY" : "—";
  const text = (id, value) => { $(id).textContent = value; };
  const json = (id, value) => text(id, JSON.stringify(value, null, 2));
  const statusNames = {queued:"Wartet",running:"Läuft",succeeded:"Abgeschlossen",failed:"Fehler",partial:"Teilweise",cancelled:"Abgebrochen",cancel_requested:"Wird abgebrochen"};
  const familyNames = {breakout:"Ausbruch",horizontal:"Horizontal",retest:"Retest"};
  const entryNames = {observed:"Einstieg",rejected:"Abgelehnt",expired:"Abgelaufen",censored:"Unvollständig",pending:"Offen"};
  const qualityNames = {provisional:"Vorläufig",qualified:"Qualifiziert"};
  let profiles = {}, experiment = null, job = null, result = null, jobs = [], offset = 0, reportStamp = "";
  let reviewPack = null, reviewCase = null, own = {red:null,green:null}, dirty = false, draw = null, firstAnchor = null;
  let reviewChart = null, dailyChart = null, equityChart = null, reviewCandles = null, ownSeries = [], auditPage = null;
  let refreshing = false, pendingRefresh = null, experimentStamp = "";
  async function request(url, body) {
    const response = await apiFetch(url, body === undefined ? undefined : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Anfrage fehlgeschlagen");
    return data;
  }
  function error(e) { text("lab-error", e.message || String(e)); $("lab-error").hidden = false; }
  function action(fn) { return async (event) => { event?.preventDefault(); $("lab-error").hidden = true; try { await fn(event); } catch (e) { error(e); } }; }
  function options(id, items, selected) {
    const el = $(id), value = selected === undefined ? el.value : selected;
    const html = items.map((item) => `<option value="${escape(item.value)}">${escape(item.label)}</option>`).join("");
    if (el.innerHTML !== html) el.innerHTML = html;
    if (items.some((item) => item.value === value)) el.value = value;
  }
  function table(headers, rows) {
    return `<table><thead><tr>${headers.map((h) => `<th>${escape(h)}</th>`).join("")}</tr></thead><tbody>${rows.length ? rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("") : `<tr><td colspan="${headers.length}">Keine vollständigen Beobachtungen in dieser Auswahl.</td></tr>`}</tbody></table>`;
  }
  function profileName(id) { return profiles[id]?.label || id; }
  const value = (id) => $(id).value, numeric = (id) => Number(value(id));
  function newSpec() {
    const chosen = [...document.querySelectorAll("[data-profile]:checked")].map((el) => el.dataset.profile);
    const lab = {hypothesis:value("lab-hypothesis"),profiles:chosen,variant_budget:numeric("lab-budget"),
      primary_family:value("lab-family"),primary_horizon:numeric("lab-horizon"),primary_metric:value("lab-metric"),
      feed:value("lab-feed"),adjustment:value("lab-adjustment"),benchmark_symbol:value("lab-benchmark").trim().toUpperCase(),
      development_fraction:numeric("lab-dev-fraction"),analysis_start:value("lab-start"),analysis_end:value("lab-end"),
      development_end:value("lab-dev-end"),validation_end:value("lab-val-end"),random_controls:numeric("lab-controls"),
      walk_train_sessions:numeric("lab-walk-train"),walk_test_sessions:numeric("lab-walk-test"),min_train_events:numeric("lab-min-events"),
      allow_native:$("lab-native").checked,membership:JSON.parse(value("lab-membership")),
      execution:{enabled:$("lab-execution").checked,capital:numeric("lab-capital"),risk_fraction:numeric("lab-risk"),allocation_fraction:numeric("lab-allocation"),
        max_positions:numeric("lab-positions"),exit:value("lab-exit"),holding_days:numeric("lab-holding"),target_r:numeric("lab-target"),
        fee_per_order:numeric("lab-fee"),spread_bps:numeric("lab-spread"),slippage_bps:numeric("lab-slippage"),fractional:$("lab-fractional").checked}};
    return {entry_mode:"lab",symbols:value("lab-symbols").toUpperCase().split(/[\s,]+/).filter(Boolean),universe:value("lab-universe"),history_days:numeric("lab-history"),
      seed:numeric("lab-seed"),horizons:[5,10,20],dataset_ids:JSON.parse(value("lab-datasets")),lab};
  }
  async function loadExperiments(selected) {
    const response = await request("/api/lab/experiments");
    options("lab-experiments", response.items.map((e) => ({value:e.id,label:`${e.id.slice(0,8)} · ${e.status} · ${date(e.created)}`})), selected);
    await loadExperiment();
  }
  async function loadExperiment() {
    const id = value("lab-experiments");
    experiment = id ? await request(`/api/lab/experiments/${id}`) : null;
    if (!experiment) { text("lab-experiment-info", "Ein Entwicklungslauf registriert Regeln und Daten für spätere Prüfungen."); return; }
    const plan = experiment.plan?.phases;
    text("lab-experiment-info", `${experiment.id} · ${experiment.status} · ${experiment.spec.lab.hypothesis}${plan ? " · " + Object.entries(plan).map(([name,p]) => `${name}: ${p.startDate}–${p.endDate}`).join(" · ") : " · Datenbindung noch nicht abgeschlossen"}`);
    json("lab-contract", experiment);
    options("lab-candidate", experiment.spec.lab.profiles.map((p) => ({value:p,label:profileName(p)})), experiment.selection?.profile);
    const succeeded = (stage) => experiment.attempts.some((a) => a.stage === stage && a.status === "succeeded");
    $("lab-validation").disabled = !succeeded("development"); $("lab-walk").disabled = !experiment.plan;
    $("lab-seal-form").querySelector("button").disabled = !!experiment.selection || !succeeded("validation"); updateFinalButton();
  }
  function updateFinalButton() {
    $("lab-final").disabled = !experiment?.selection || !$("lab-final-confirm").checked || experiment.finalOpened;
  }
  async function runStage(stage) {
    if (!experiment) throw new Error("Zuerst ein Experiment auswählen.");
    const created = await request(`/api/lab/experiments/${experiment.id}/run`, {stage,confirm_final_test:stage === "holdout" && $("lab-final-confirm").checked});
    await refresh(created.id, true); await loadExperiment();
  }
  async function refresh(selected, force = false) {
    if (refreshing) { if (selected) pendingRefresh = {selected,force}; return; } refreshing = true;
    try {
      const response = await request("/api/research/jobs"); jobs = response.items.filter((j) => j.spec.entry_mode === "lab");
      if (selected && !jobs.some((j) => j.id === selected)) {
        const fetched = await request(`/api/research/jobs/${selected}`);
        if (fetched.spec.entry_mode !== "lab") throw new Error("Dieser Auftrag gehört zur bisherigen Forschung, nicht zum Labor.");
        jobs.unshift(fetched);
      }
      options("lab-jobs", jobs.map((j) => ({value:j.id,label:`${j.id.slice(0,8)} · ${j.spec.lab.stage} · ${statusNames[j.status] || j.status} · ${(j.universe || j.spec.symbols).slice(0,5).join(", ")}`})), selected);
      text("lab-state", response.operations?.worker?.state === "working" ? "● Worker arbeitet" : response.workerActive ? "● Worker bereit" : "⚠ Kein Worker aktiv");
      await loadJob(force);
      const stamp = job ? `${job.id}|${job.updated}|${job.status}` : "";
      if (experiment && job?.spec.lab.experiment_id === experiment.id && stamp !== experimentStamp) { await loadExperiment(); experimentStamp = stamp; }
    } finally {
      refreshing = false;
      if (pendingRefresh) { const pending = pendingRefresh; pendingRefresh = null; await refresh(pending.selected,pending.force); }
    }
  }
  async function loadJob(force = false) {
    const id = value("lab-jobs"); if (!id) return;
    if (job?.id !== id) {
      offset = 0; reportStamp = "";
      const url = new URL(location.href); url.searchParams.set("job",id); history.replaceState(null,"",url);
    }
    job = jobs.find((j) => j.id === id) || await request(`/api/research/jobs/${id}`);
    const stamp = [id,job.updated,job.status,offset,value("lab-entry-filter")].join("|");
    const progress = ["running","cancel_requested"].includes(job.status) ? job.progress : null;
    const progressText = progress ? ` · ${{preparing:"Vorbereiten",lab_import:"Daten einlesen",lab_scan:progress.detail?.unit==="outcomes"?"Verläufe bewerten":"Linien prüfen"}[progress.phase] || progress.phase} ${progress.detail?.symbol || ""} ${progress.detail?.profile || ""}${progress.detail?.total!=null?` ${progress.detail.completed ?? 0}/${progress.detail.total}`:""}` : "";
    text("lab-job-info", `${statusNames[job.status] || job.status} · ${job.spec.lab.stage} · ${job.completedTrials} Linienpaare · ${job.eventCount} Ereignisse${progressText}${job.error ? " · " + job.error : ""}`);
    $("lab-cancel").disabled = !["queued","running"].includes(job.status);
    $("lab-review-create").querySelector("button").disabled = job.status!=="succeeded" || job.spec.lab.stage!=="development";
    if (!force && stamp === reportStamp) return;
    const url = `/api/research/jobs/${id}/report?limit=50&offset=${offset}&entry_filter=${value("lab-entry-filter")}`;
    const fetched = await request(url);
    if (value("lab-jobs") !== id || stamp !== [id,job.updated,job.status,offset,value("lab-entry-filter")].join("|")) return;
    result = fetched; reportStamp = stamp; $("lab-json").href = url;
    options("lab-section", Object.keys(result.summary.sections).map((s) => ({value:s,label:s})));
    options("lab-result-horizon", job.spec.horizons.map((h) => ({value:String(h),label:String(h)})), value("lab-result-horizon") || String(job.spec.lab.primary_horizon));
    options("lab-review-profile", job.spec.lab.profiles.map((p) => ({value:p,label:profileName(p)})));
    renderResults(); renderCases(); renderPortfolios();
  }
  function renderResults() {
    if (!result) return;
    const section = value("lab-section"), horizon = value("lab-result-horizon");
    const groups = groupsFor(result.summary, section, horizon, value("lab-kind"));
    $("lab-results").innerHTML = table(["Profil","Familie / Qualität","n / unvollständig","Mittel / Median %","Mehrentwicklung zu Kontrollen %","Mehrentwicklung zum Markt %","MFE / MAE %","Vollständige Pfade"], groups.map((g) => {
      const o = g.outcome;
      return [escape(profileName(g.profile)),`${escape(familyNames[g.family] || g.family)} / ${escape(qualityNames[g.quality] || g.quality)}`,`${number(o.n)} / ${number(o.incomplete)}`,
        `${number(o.mean_return_pct)} / ${number(o.median_return_pct)}`,`${number(o.mean_excess_pct)} <small>(n=${number(o.controlMatchedEntries)})</small>`,`${number(o.mean_market_excess_pct)} <small>(n=${number(o.marketMatchedEntries)})</small>`,`${number(o.mean_mfe_pct)} / ${number(o.mean_mae_pct)}`,number(o.completePaths)];
    }));
    const diagnostics = result.summary.sections[section]?.diagnostics || {};
    $("lab-diagnostics").innerHTML = Object.entries(diagnostics).map(([profile,d]) => `<details><summary>${escape(profileName(profile))} · ${number(d.evaluations)} diagnostische Prüfungen</summary>${table(["Kriterium","Fehlgeschlagen","Unbekannt","Einziger Pflichtblocker"], [...new Set([...Object.keys(d.failed),...Object.keys(d.unknown),...Object.keys(d.soleBlocker)])].sort().map((name) => [escape(name),number(d.failed[name] || 0),number(d.unknown[name] || 0),number(d.soleBlocker[name] || 0)]))}<pre>${escape(JSON.stringify({combinations:d.combinations,terminalReasons:d.terminalReasons},null,2))}</pre></details>`).join("");
    json("lab-stat-details", {complete:result.summary.complete,section,details:result.summary.sections[section],coverage:result.job.symbols.map((s) => ({symbol:s.symbol,plan:s.plan,error:s.error})),walkSelections:result.summary.walkSelections});
  }
  function chartLink(c,e) {
    return "/?" + new URLSearchParams({symbol:c.symbol,tf:"4h",dataset:c.datasetId,asof:new Date((e.signalAt || c.startAt)*1000).toISOString(),job:job.id,trial:c.id,variant:e.variant});
  }
  function renderCases() {
    const rows = [];
    for (const c of result.trials) for (const e of c.variants) {
      if (value("lab-entry-filter") === "entries" && e.status !== "observed") continue;
      const checks = [...(e.checks || []),...(e.executionChecks || [])];
      rows.push([`${escape(c.symbol)} · ${escape(profileName(c.profile))}<br><small>${escape(c.labPhase)}</small>`,`${escape(familyNames[e.variant] || e.variant)} · ${escape(entryNames[e.status] || e.status)}<br><small>${escape(e.reason || "")}</small>`,`${date(e.signalAt)}<br>${e.entryAt ? date(e.entryAt) + " · " + number(e.entryPrice) : "—"}`,
        `<details><summary>Prüfwerte / Verlauf</summary><pre>${escape(JSON.stringify({checks,forward:e.forward,hypothetical:e.hypothetical,controls:e.controls},null,2))}</pre></details>`,
        `<a href="${escape(chartLink(c,e))}" target="_blank" rel="noopener">Damals bekannte Linien ↗</a>`]);
    }
    $("lab-cases").innerHTML = table(["Aktie / Profil","Variante / Ergebnis","Signal / Einstieg","Prüfung","Chart"],rows);
    text("lab-page", `${result.page.total ? offset+1 : 0}–${offset+result.trials.length} von ${result.page.total} Linienpaaren`);
    $("lab-prev").disabled = offset === 0; $("lab-next").disabled = !result.page.hasMore;
  }
  function renderPortfolios() {
    const portfolios = result.summary.portfolios || [];
    $("lab-portfolios").innerHTML = table(["Abschnitt / Profil","Familie","Geschlossen / offen / ausgelassen","Realisiertes Netto","Markierter Depotwert","Markierter Rückgang %","Details"],portfolios.map((p,i) => [
      `${escape(p.section)} / ${escape(profileName(p.profile))}`,escape(familyNames[p.family]),`${p.summary.closed} / ${p.summary.open} / ${p.summary.skipped}`,number(p.summary.realizedNetPnl),number(p.summary.finalMarkedEquity),number(p.summary.maxMarkedDrawdownPct),`<button data-portfolio="${i}">Depot ansehen</button>`]));
    document.querySelectorAll("[data-portfolio]").forEach((button) => button.onclick = action(async () => {
      const p = portfolios[Number(button.dataset.portfolio)];
      const query = new URLSearchParams({job:job.id,section:p.section,profile:p.profile,family:p.family,limit:"1000"});
      const data = await request("/api/lab/portfolio?" + query);
      $("lab-portfolio-detail").hidden = false; json("lab-portfolio-detail", {summary:data.summary,assumptions:data.assumptions,pages:data.pages,trades:data.trades,skipped:data.skipped});
      $("lab-equity-chart").hidden = false; equityChart?.remove(); equityChart = makeChart("lab-equity-chart");
      const series = equityChart.addSeries(LC.LineSeries,{color:"#2765d5",priceLineVisible:false});
      series.setData(data.equity.map((p) => ({time:p.at,value:p.equity}))); equityChart.timeScale().fitContent();
      if (data.pages.equity.hasMore) text("lab-state", "Depotgrafik zeigt die erste Seite; weitere Punkte sind über die paginierte API/CLI verfügbar.");
    }));
  }
  function themeOptions() {
    const dark = document.documentElement.dataset.theme === "dark";
    return {layout:{background:{type:"solid",color:dark?"#11151e":"#ffffff"},textColor:dark?"#cbd5e1":"#334155"},grid:{vertLines:{color:dark?"#202632":"#f0f2f5"},horzLines:{color:dark?"#202632":"#f0f2f5"}}};
  }
  function makeChart(id) {
    const format = (time, withTime) => new Intl.DateTimeFormat("de-DE",{timeZone:"America/New_York",...(withTime?{hour:"2-digit",minute:"2-digit"}:{day:"2-digit",month:"2-digit",year:"2-digit"})}).format(new Date(time*1000));
    return LC.createChart($(id),{autoSize:true,...themeOptions(),localization:{locale:"de-DE",timeFormatter:(time)=>date(time)},
      timeScale:{timeVisible:true,secondsVisible:false,tickMarkFormatter:(time,type)=>format(time,type>=3)},rightPriceScale:{borderVisible:false}});
  }
  async function loadReviewPacks(selected) {
    const response = await request("/api/lab/reviews");
    options("lab-review-packs",response.items.map((p) => ({value:p.id,label:`${p.id.slice(0,8)} · ${p.manifest.count} Fälle · ${date(p.created)}`})),selected);
    if (value("lab-review-packs")) await loadReviewPack();
  }
  function assertSaved() { if (dirty) throw new Error("Bitte die aktuelle Beurteilung zuerst speichern, damit Anker und Text erhalten bleiben."); }
  async function loadReviewPack() {
    assertSaved(); reviewPack = await request(`/api/lab/reviews/${value("lab-review-packs")}?limit=100`);
    reviewCaseOptions();
    if (value("lab-review-cases")) await openReviewCase();
  }
  function reviewCaseOptions(selected) {
    options("lab-review-cases",reviewPack.cases.map((c,i) => ({value:c.id,label:`${i+1}. ${c.symbol} · ${date(c.cutoff)} · ${c.tainted?"beeinflusst":c.revealed?"aufgedeckt":c.labelled?"beurteilt":"offen"}`})),selected);
  }
  function reviewInfo() {
    text("lab-review-info", `${reviewCase.dataKind==="synthetic"?"SYNTHETISCHE TESTDATEN · keine Börsenkurse · ":""}${reviewCase.symbol} · Bekannt bis ${date(reviewCase.cutoff)} · ${reviewCase.feed} / ${reviewCase.adjustment} · ${reviewCase.tainted?"Nach Offenlegung geändert – vom Vergleich ausgeschlossen":reviewCase.revealed?"Aufgedeckt":"Verblindet"}`);
  }
  function storedReviewState() {
    const item=reviewPack.cases.find((c)=>c.id===reviewCase.id);
    if (item) Object.assign(item,{labelled:!!reviewCase.label,revealed:reviewCase.revealed,tainted:reviewCase.tainted});
    reviewCaseOptions(reviewCase.id); reviewInfo();
  }
  async function openReviewCase() {
    assertSaved(); reviewCase = await request(`/api/lab/reviews/${reviewPack.id}/${value("lab-review-cases")}`);
    own = {red:reviewCase.label?.red || null,green:reviewCase.label?.green || null}; draw = firstAnchor = null;
    $("lab-human-entry").value = reviewCase.label?.entry || "wait"; $("lab-human-reason").value = reviewCase.label?.reason || "";
    renderReview(); dirty = false;
  }
  function renderReview() {
    if (!reviewCase) return;
    $("lab-label-form").querySelector("button[type='submit']").disabled = false;
    reviewInfo();
    $("lab-reveal").disabled = !reviewCase.label || dirty; $("lab-review-engine-raw").hidden = !reviewCase.revealed;
    $("lab-review-outcomes").hidden = !reviewCase.revealed;
    if (reviewCase.revealed) {
      json("lab-review-revealed",reviewCase.engine);
      const rows=(reviewCase.engine.case?.variants || []).map((e) => {
        const point=e.status==="observed"?e:e.hypothetical;
        return [escape(familyNames[e.variant] || e.variant),escape(entryNames[e.status] || e.status)+(e.hypothetical?" · hypothetischer Vergleich":""),point?`${date(point.entryAt)} · ${number(point.entryPrice)}`:"—",...[5,10,20].map((h) => point?.forward?.[h]?.complete?number(point.forward[h].return_pct):"unvollständig")];
      });
      const reviewPath=reviewCase.engine.reviewPath;
      if (reviewPath?.available) rows.push(["Eigene Sichtprüfung","Hypothetischer Vergleich, kein Engine-Entry",`${date(reviewPath.entryAt)} · ${number(reviewPath.entryPrice)}`,...[5,10,20].map((h)=>reviewPath.forward?.[h]?.complete?number(reviewPath.forward[h].return_pct):"unvollständig")]);
      $("lab-review-outcomes").innerHTML = `<p>Engine-Signal am Sichtzeitpunkt bestätigt: <strong>${reviewCase.engine.signal?"Ja":"Nein"}</strong></p>` + table(["Variante","Zustand","Einstieg","5 Tage %","10 Tage %","20 Tage %"],rows);
    }
    text("lab-review-legend",reviewCase.revealed ? "Eigene Linien durchgezogen · ursprüngliche Engine-Linien gestrichelt. Rot: Widerstand, Grün: Safety." : "Nur eigene Linien sichtbar; Engine und spätere Ergebnisse bleiben verborgen.");
    reviewChart?.remove(); dailyChart?.remove(); ownSeries = [];
    reviewChart = makeChart("lab-review-chart"); dailyChart = makeChart("lab-review-daily");
    reviewCandles = reviewChart.addSeries(LC.CandlestickSeries,{upColor:"#089981",downColor:"#f23645",borderVisible:false,wickUpColor:"#089981",wickDownColor:"#f23645"}); reviewCandles.setData(reviewCase.bars["4h"]);
    const daily = dailyChart.addSeries(LC.CandlestickSeries,{upColor:"#089981",downColor:"#f23645",borderVisible:false}); daily.setData(reviewCase.bars["1D"]);
    latestReview(); dailyChart.timeScale().fitContent(); drawOwnLines();
    reviewChart.subscribeClick((param) => {
      if (!draw || !param.point) return;
      const stamp=typeof param.time === "number" ? param.time : typeof param.logical === "number" ? reviewCase.bars["4h"][Math.round(param.logical)]?.time : null;
      if (stamp==null) return;
      const price = reviewCandles.coordinateToPrice(param.point.y); if (!(price>0)) return;
      if (!firstAnchor) { firstAnchor = {time:stamp,price}; text("lab-draw-state", "Erster Anker gesetzt. Zweiten Anker in einer anderen Kerze wählen."); return; }
      if (firstAnchor.time === stamp) return;
      const points = [firstAnchor,{time:stamp,price}].sort((a,b) => a.time-b.time);
      own[draw] = {a_time:points[0].time,a_price:points[0].price,b_time:points[1].time,b_price:points[1].price};
      draw = firstAnchor = null; changed(); drawOwnLines(); text("lab-draw-state", "Linie gesetzt. Beurteilung speichern, um die Anker zu erhalten.");
    });
  }
  function drawOwnLines() {
    if (!reviewChart || !reviewCase) return;
    ownSeries.forEach((s) => reviewChart.removeSeries(s)); ownSeries = [];
    for (const color of ["red","green"]) if (own[color]) {
      const series = reviewChart.addSeries(LC.LineSeries,{color:color==="red"?"#ff4564":"#0bbb78",lineWidth:2,priceLineVisible:false,lastValueVisible:false});
      series.setData(rayPoints(own[color],reviewCase.bars["4h"])); ownSeries.push(series);
    }
    if (reviewCase.revealed) for (const color of ["red","green"]) {
      const ray=reviewCase.engine?.case?.frozen?.[color];
      if (!ray?.a_time || !ray?.b_time) continue;
      const series=reviewChart.addSeries(LC.LineSeries,{color:color==="red"?"#ff4564":"#0bbb78",lineWidth:2,lineStyle:2,priceLineVisible:false,lastValueVisible:false});
      series.setData(rayPoints(ray,reviewCase.bars["4h"])); ownSeries.push(series);
    }
  }
  function changed() { dirty = true; $("lab-reveal").disabled = true; }
  function latestReview() {
    if (!reviewChart || !reviewCase) return;
    const length=reviewCase.bars["4h"].length;
    reviewChart.timeScale().setVisibleLogicalRange({from:Math.max(0,length-120),to:length+5});
  }
  async function nextReview() {
    assertSaved(); if (!reviewPack) return;
    const items = reviewPack.cases, current = items.findIndex((c) => c.id === reviewCase?.id);
    if (current+1>=items.length) { text("lab-draw-state", "Letzter Fall im Paket erreicht."); return; }
    $("lab-review-cases").value = items[current+1].id; await openReviewCase();
  }
  async function loadAudit(reset) {
    if (!experiment) throw new Error("Zuerst ein Experiment auswählen.");
    const query = reset || !auditPage ? "?limit=50" : `?limit=50&after=${auditPage.nextAfter}&through=${auditPage.through}`;
    const data = await request(`/api/lab/experiments/${experiment.id}/audit${query}`);
    if (reset) json("lab-audit-content",data); else $("lab-audit-content").textContent += "\n" + JSON.stringify(data,null,2);
    auditPage = data.page; $("lab-audit-next").disabled = !auditPage.hasMore;
  }

  $("lab-form").onsubmit = action(async () => { const created = await request("/api/research/jobs",newSpec()); await refresh(created.id,true); await loadExperiments(created.spec.lab.experiment_id); });
  $("lab-refresh").onclick = action(async () => { assertSaved(); await refresh(undefined,true); await loadExperiments(); await loadReviewPacks(); });
  $("lab-experiments").onchange = action(async () => { auditPage = null; text("lab-audit-content", ""); await loadExperiment(); });
  $("lab-validation").onclick = action(() => runStage("validation")); $("lab-walk").onclick = action(() => runStage("walk_forward"));
  $("lab-final-confirm").onchange = updateFinalButton; $("lab-final").onclick = action(() => runStage("holdout"));
  $("lab-seal-form").onsubmit = action(async () => { if (!experiment) throw new Error("Experiment fehlt."); await request(`/api/lab/experiments/${experiment.id}/seal`,{profile:value("lab-candidate"),rationale:value("lab-rationale")}); await loadExperiment(); });
  $("lab-audit").onclick = action(() => loadAudit(true)); $("lab-audit-next").onclick = action(() => loadAudit(false));
  $("lab-jobs").onchange = action(() => loadJob(true));
  $("lab-cancel").onclick = action(async () => { await request(`/api/research/jobs/${job.id}/cancel`,{}); await refresh(undefined,true); });
  for (const id of ["lab-section","lab-result-horizon","lab-kind"]) $(id).onchange = renderResults;
  $("lab-entry-filter").onchange = action(async () => { offset = 0; await loadJob(true); });
  $("lab-prev").onclick = action(async () => { offset = Math.max(0,offset-50); await loadJob(true); });
  $("lab-next").onclick = action(async () => { offset += 50; await loadJob(true); });
  $("lab-review-create").onsubmit = action(async () => { assertSaved(); if (!job) throw new Error("Entwicklungsauftrag auswählen."); const pack = await request("/api/lab/reviews",{job:job.id,count:numeric("lab-review-count"),seed:numeric("lab-review-seed"),profile:value("lab-review-profile")}); await loadReviewPacks(pack.id); });
  $("lab-review-packs").onchange = action(async () => { if (dirty) { $("lab-review-packs").value = reviewPack.id; assertSaved(); } await loadReviewPack(); });
  $("lab-review-cases").onchange = action(async () => { if (dirty) { $("lab-review-cases").value = reviewCase.id; assertSaved(); } await openReviewCase(); });
  $("lab-review-next").onclick = action(nextReview);
  for (const color of ["red","green"]) $("lab-draw-"+color).onclick = () => { draw = color; firstAnchor = null; text("lab-draw-state", `${color==="red"?"Rote":"Grüne"} Linie: ersten und zweiten Anker im 4h-Chart anklicken.`); };
  $("lab-draw-clear").onclick = () => { own = {red:null,green:null}; changed(); drawOwnLines(); };
  $("lab-review-fit").onclick = () => { reviewChart?.timeScale().fitContent(); dailyChart?.timeScale().fitContent(); };
  $("lab-review-latest").onclick = latestReview;
  $("lab-human-entry").onchange = changed; $("lab-human-reason").oninput = changed;
  $("lab-label-form").onsubmit = action(async () => { if (!reviewCase) throw new Error("Prüffall auswählen."); reviewCase = await request(`/api/lab/reviews/${reviewPack.id}/${reviewCase.id}/label`,{entry:value("lab-human-entry"),reason:value("lab-human-reason"),...own}); dirty = false; storedReviewState(); $("lab-reveal").disabled = false; text("lab-draw-state",reviewCase.tainted ? "Gespeichert; nach Offenlegung geändert und vom Vergleich ausgeschlossen." : "Beurteilung und Anker gespeichert."); });
  $("lab-reveal").onclick = action(async () => { assertSaved(); reviewCase = await request(`/api/lab/reviews/${reviewPack.id}/${reviewCase.id}/reveal`,{}); storedReviewState(); renderReview(); });
  $("lab-review-compare").onclick = action(async () => { if (!reviewPack) throw new Error("Fallpaket auswählen."); json("lab-review-comparison",await request(`/api/lab/reviews/${reviewPack.id}/compare`)); });
  $("lab-review-daily").closest("details").addEventListener("toggle",(e) => { if (e.currentTarget.open) dailyChart?.timeScale().fitContent(); });
  try { document.documentElement.dataset.theme = JSON.parse(localStorage.getItem("tori-theme")) || "light"; } catch {}
  $("lab-theme").onclick = () => { const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = theme; try { localStorage.setItem("tori-theme",JSON.stringify(theme)); } catch {} [reviewChart,dailyChart,equityChart].filter(Boolean).forEach((c) => c.applyOptions(themeOptions())); };
  action(async () => {
    const config = await request("/api/lab/profiles"); profiles = config.profiles;
    $("lab-profiles").innerHTML = Object.entries(profiles).map(([id,p]) => `<label class="lab-check"><input type="checkbox" data-profile="${escape(id)}" ${config.defaults.profiles.includes(id)?"checked":""}><span>${escape(p.label)}<small>${escape(p.description)}</small></span></label>`).join("");
    await refresh(new URLSearchParams(location.search).get("job") || undefined,true); await loadExperiments(job?.spec?.lab?.experiment_id); await loadReviewPacks();
  })();
  setInterval(() => { if (document.visibilityState === "visible") refresh().catch(error); },5000);
})(globalThis);
