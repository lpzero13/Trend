/* Execute the actual chart controller without a browser or provider.
 * DOM/chart-library surfaces are test doubles; this is interaction/state QA,
 * not a visual layout test. Geometry remains the real candle-axis helper.
 */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const { RayGeometry } = require("../static/drawings.js");

const times = [1750000000, 1750003600, 1750007200];
const manualRay = { id: "own-ray", timeframe: "4h",
  a: { time: times[0], price: 95 }, b: { time: times[1], price: 96 } };
function payload(analyzed, research = false) {
  const bars = times.map((time) => ({ time, end: time + 3600,
    open: 100, high: 102, low: 98, close: 101, volume: 5 }));
  const latest = { close: 101, time: times.at(-1), end: times.at(-1) + 3600,
    change: 0, changePercent: 0 };
  const ray = (a, b) => ({ a_time: times[0], b_time: times[1], a_price: a,
    b_price: b, value: b, contacts: 2, span_days: 8 });
  return { symbol: "TEST", company: "Test company", currency: "USD", timeframe: "4h",
    bars, axis: times, latest, reference: times.at(-1), analysisCutoff: latest.end,
    historical: false, generatedAt: new Date().toISOString(), analysisEnabled: analyzed,
    charts: Object.fromEntries(["1h", "4h", "1D", "1W"].map((tf) => [tf, { bars, latest, reference: times.at(-1) }])),
    sources: Object.fromEntries(["1h", "4h", "1D", "1W"].map((tf) => [tf, { cached: true, mode: "cache" }])),
    lanes: analyzed ? Object.fromEntries(["1h", "4h", "1D", "1W"].map((tf) => [tf,
      { red: ray(110, 109), green: ray(95, 96), outerRed: [], outerGreen: [],
        distance: 3, status: "Vorläufig", event: null }])) : {},
    ...(analyzed ? { analysisId: "known-analysis" } : {}),
    ...(analyzed && research ? { researchSetup: { entryAt: times.at(-1)+300,
      entryPrice: 101, initialStop: 96, validRisk: true, variant: "breakout" } } : {}),
  };
}

async function boot({ query = "?symbol=TEST", failAnalysis = false, deferred = false, path='/', moving=false, failFreeze=false, deferredFreeze=false, themePreference=null } = {}) {
  const elements = new Map();
  function element(selector) {
    if (!elements.has(selector)) elements.set(selector, { hidden: true, disabled: false,
      checked: false, value: "", dataset: {}, attributes: {}, textContent: "", innerHTML: "",
      classList: { toggle() {} }, addEventListener() {}, close() {}, showModal() {},
      setAttribute(k, v) { this.attributes[k] = v; },
      replaceChildren() { this.innerHTML = ""; },
      add() {},
    });
    return elements.get(selector);
  }
  const tfButtons = ["1h", "4h", "1D", "1W"].map((tf) => Object.assign(element(tf), { dataset: { tf } }));
  const requests = [], markerCalls = [], stored = new Map([
    ["tori-analysis-enabled", "true"], ["tori-info", "true"],
    ["tori-frozen:TEST", '"old-snapshot"'], ["tori-rays:TEST", JSON.stringify([manualRay])],
  ]);
  if(themePreference)stored.set('tori-theme',JSON.stringify(themePreference));
  let range = null, candleData = [], resolveAnalysis, resolveFreeze, lastAnalysis, randomSerial=0; const smaData={}, snapshots=new Map();
  const scale = { getVisibleLogicalRange: () => range, setVisibleLogicalRange: (r) => { range = r; },
    subscribeVisibleLogicalRangeChange() {}, applyOptions() {} };
  const price = { applyOptions() {}, options: () => ({ autoScale: true }) };
  const chart = { applyOptions() {}, timeScale: () => scale, priceScale: () => price,
    subscribeCrosshairMove() {}, addSeries(type, options) {
      if(type!=="line")chart.autoScale = options.autoscaleInfoProvider;
      return { applyOptions() {}, setData(rows) { if(type==="line")smaData[options.color]=rows;else candleData = rows; } };
    } };
  class Layer {
    constructor(chart,series,axis,onChange) { this.items = []; this.automatic = []; this.undoStack = [];this.onChange=onChange; }
    update() {}
    load(items) { this.items = items; }
    setMode(mode) { this.active = mode === true; this.measureActive = mode === "measure"; }
  }
  const context = vm.createContext({ console, URLSearchParams, Intl, Date, Map, structuredClone, Option: class {},
    RayGeometry, RayLayer: Layer, matchMedia: () => ({ matches: false }),
    location: { search: query,pathname:path }, history: { replaceState(a,b,url) { context.renderedUrl=url; } },encodeURIComponent,
    localStorage: { getItem: (k) => stored.get(k) ?? null, setItem: (k, v) => stored.set(k, v) },
    performance: { now: () => 0 }, queueMicrotask, requestAnimationFrame: (fn) => fn(),
    setTimeout, clearTimeout,
    document: { documentElement: { dataset: {} }, querySelector: element, addEventListener() {},
      querySelectorAll: (s) => s === "[data-tf]" ? tfButtons : [] },
    LightweightCharts: { createChart: () => chart, CandlestickSeries: {},LineSeries:"line",
      CrosshairMode: { Normal: 0 }, TickMarkType: { Time: 0 },
      createSeriesMarkers: () => ({ setMarkers(markers) { markerCalls.push(markers); } }) },
    apiFetch: async (url,opts) => {
      requests.push(url);
      if(url.startsWith('/api/snapshots?'))return {ok:true,json:async()=>({items:[]})};
      if(url==='/api/snapshots' && opts?.method==='POST') {
        if(deferredFreeze)await new Promise(resolve=>{resolveFreeze=resolve;});
        if(failFreeze)return {ok:false,json:async()=>({error:'Disk full'})};
        const data=structuredClone(lastAnalysis), snapshot={id:data.analysisId,symbol:data.symbol,basis:'bars',
          analysisCutoff:data.analysisCutoff,validFrom:data.latest.end,payload:data};
        snapshots.set(snapshot.id,snapshot);
        return {ok:true,json:async()=>snapshot};
      }
      if(url.startsWith('/api/snapshots/') && snapshots.has(url.split('/').at(-1)))
        return {ok:true,json:async()=>structuredClone(snapshots.get(url.split('/').at(-1)))};
      if(url==='/api/random/cases' || /^\/api\/random\/cases\/[a-f0-9]{32}$/.test(url)){
        if(opts?.method==='POST')randomSerial++;
        const id=url==='/api/random/cases'?String(randomSerial).repeat(32):url.split('/').at(-1);
        return {ok:true,json:async()=>({id,symbol:'TEST',datasetId:'c'.repeat(64),startAt:times.at(-1)+3600})};
      }
      if(url.startsWith('/api/step?') || url.includes('/api/random/cases/') && url.includes('/step?')){
        const q=new URL(url,'http://localhost').searchParams;
        const closedAt=Date.parse(q.get('asof'))/1000+(q.get('direction')==='next'?3600:-3600);
        return {ok:true,json:async()=>({closedAt,asof:new Date(closedAt*1000).toISOString(),timeframe:q.get('timeframe')})};
      }
      if (url === "/api/snapshots/saved" || url === "/api/snapshots/old-snapshot") {
        const data = payload(true);
        return { ok: true, json: async () => ({ id: "saved", symbol: "TEST", basis: "bars",
          analysisCutoff: data.analysisCutoff, validFrom: data.analysisCutoff, payload: data }) };
      }
      if (url.startsWith("/api/chart?") || url.startsWith("/api/dataset-chart?") || url.startsWith("/api/fan/chart?") || url.includes('/api/random/cases/') && url.includes('/chart?')) {
        const analyzed = new URL(url, "http://localhost").searchParams.get("analysis") === "1";
        if (analyzed && deferred) await new Promise((resolve) => { resolveAnalysis = resolve; });
        const data = payload(analyzed, query.includes("trial=") || query.includes("fan_case="));
        if (data.researchSetup && query.includes("fan_case=")) Object.assign(data.researchSetup,{entryMode:"fan", sourceTimeframe:"4h"});
        data.analysisEngine = new URL(url, "http://localhost").searchParams.get("engine") || "legacy";
        if(analyzed && data.analysisEngine==='fan_master')for(const lane of Object.values(data.lanes)) {
          lane.context={sma50:101,sma200:100,series:{'50':times.map(time=>({time,value:101})),'200':times.map(time=>({time,value:100}))}};
          Object.assign(lane.green,{algorithm:'master',color:'#1e88e5',level:1,qualified:true,contacts:3});lane.mainSafety=structuredClone(lane.green);
          lane.cleanCloseThreshold=110;lane.closeModel={capital:2000,riskFraction:.01,quantity:2,stop:95};
        }
        data.historical = new URL(url, "http://localhost").searchParams.has("asof");
        const params=new URL(url,'http://localhost').searchParams;
        if(moving){
          const at=params.has('asof')?Date.parse(params.get('asof'))/1000:data.analysisCutoff;
          const count=Math.floor((at-times[0])/3600), all=Array.from({length:count},(_,i)=>({...data.bars[0],time:times[0]+i*3600,end:times[0]+(i+1)*3600,close:101+i}));
          data.bars=all;data.axis=all.map(b=>b.time);data.latest={...data.latest,...all.at(-1)};data.reference=all.at(-1).time;
          for(const chart of Object.values(data.charts))Object.assign(chart,{bars:all,latest:data.latest,reference:data.reference});
          if(analyzed)for(const lane of Object.values(data.lanes)){lane.red.b_price+=count-3;lane.green.b_price+=count-3;}
          data.analysisId='analysis-'+at;
        }
        if(params.has('asof'))data.analysisCutoff=Date.parse(params.get('asof'))/1000;
        if(params.has('dataset'))data.datasetId=params.get('dataset');
        if(path==='/zufall')data.randomCase={id:url.split('/')[4]};
        if(analyzed)lastAnalysis=structuredClone(data);
        return { ok: !(analyzed && failAnalysis), json: async () => analyzed && failAnalysis
          ? { error: "Analysis failed" } : structuredClone(data) };
      }
      throw Error("Unexpected request: " + url);
    },
  });
  vm.runInContext(fs.readFileSync("static/analysis.js", "utf8"), context);
  // Measurement persistence has its own tests; keep the real chart controller.
  vm.runInContext("function setupMeasurements() {} function renderMeasurementList() {} function restoreMeasurements(s) { state.measurementSymbol = s; }", context);
  vm.runInContext(fs.readFileSync("static/app.js", "utf8"), context);
  const flush = () => new Promise((resolve) => setImmediate(resolve));
  await flush();
  return { context, element, requests, markerCalls, stored, chart, tfButtons, flush, smaData,
    eval: (code) => vm.runInContext(code, context), candles: () => candleData,
    resolveAnalysis: () => resolveAnalysis(), resolveFreeze: () => resolveFreeze() };
}

test('visible light/dark switch persists choice without changing candles, drawings or fetching data',async()=>{
  const h=await boot();
  const before=h.eval('JSON.stringify({bars:state.data.bars,rays:rayLayer.items})'),requests=h.requests.length;
  assert.match(h.element('#theme-button').textContent,/Hell/);
  h.element('#theme-button').onclick();
  assert.match(h.element('#theme-button').textContent,/Dunkel/);
  assert.equal(h.element('#theme-button').attributes['aria-pressed'],'true');
  assert.equal(h.eval('document.documentElement.dataset.theme'),'dark');
  assert.equal(h.stored.get('tori-theme'),'"dark"');
  assert.equal(h.eval('JSON.stringify({bars:state.data.bars,rays:rayLayer.items})'),before);
  assert.equal(h.requests.length,requests);
  const again=await boot({themePreference:JSON.parse(h.stored.get('tori-theme'))});
  assert.equal(again.eval('document.documentElement.dataset.theme'),'dark');
  again.element('#theme-button').onclick();
  assert.equal(again.eval('document.documentElement.dataset.theme'),'light');
});

test('random page uses its pinned case, separate drawings, all intervals and replay without live provider routes',async()=>{
  const h=await boot({path:'/zufall'});await h.flush();
  assert.equal(h.eval('state.randomId'),'1'.repeat(32));assert.equal(h.eval('state.analysisEnabled'),false);
  assert.equal(h.eval('rayLayer.items.length'),0); // the main chart drawing is not imported
  assert.equal(h.eval('state.measurementSymbol'),'random:'+'1'.repeat(32));
  h.eval('rayLayer.onChange([{id:"practice"}])');
  assert.ok(h.stored.has('tori-rays:random:'+'1'.repeat(32)));
  assert.equal(JSON.parse(h.stored.get('tori-rays:TEST'))[0].id,'own-ray');
  h.tfButtons[0].onclick();assert.equal(h.eval('state.timeframe'),'1h');
  const start=h.eval('state.randomStartAt');await h.element('#step-next').onclick();
  assert.match(h.requests.at(-2),/\/api\/random\/cases\/.*\/step\?/);
  assert.equal(h.eval('state.data.analysisCutoff'),start+3600);
  await h.element('#random-reset').onclick();assert.equal(h.eval('state.data.analysisCutoff'),start);
  await h.element('#random-new').onclick();assert.equal(h.eval('state.randomId'),'2'.repeat(32));
  assert.equal(h.eval('rayLayer.items.length'),0);
  assert.ok(!h.requests.some(u=>u.startsWith('/api/chart?')||u.startsWith('/api/dataset-chart?')));
});

test('random page reload resumes the saved case and position without rolling a new case',async()=>{
  const at=new Date((times.at(-1)+7200)*1000).toISOString();
  const h=await boot({path:'/zufall',query:'?case='+'a'.repeat(32)+'&asof='+encodeURIComponent(at)});await h.flush();
  assert.equal(h.eval('state.randomId'),'a'.repeat(32));assert.equal(h.eval('state.asOf'),at);
  assert.ok(!h.requests.includes('/api/random/cases'));assert.equal(h.eval('state.randomPicking'),false);
});

test('weekly view reuses known bundle, preserves random origin and tools, and supports weekly measurements',async()=>{
  const h=await boot({path:'/zufall'});await h.flush();const count=h.requests.length;
  h.tfButtons[3].onclick();assert.equal(h.eval('state.timeframe'),'1W');assert.equal(h.requests.length,count);
  h.element('#ray-tool').onclick();assert.equal(h.eval('rayLayer.active'),true);
  h.element('#measure-tool').onclick();assert.equal(h.eval('rayLayer.measureActive'),true);
  assert.equal(h.eval('rayLayer.timeframe'),'1W');
  const origin=h.eval('state.randomStartAt');await h.element('#step-next').onclick();
  assert.match(h.requests.at(-2),/timeframe=1W/);assert.equal(h.eval('state.randomStartAt'),origin);
});

test("every page starts manual despite storage, URL flags and a saved freeze; tools work", async () => {
  const h = await boot({ query: "?symbol=TEST&analysis=1" });
  assert.equal(h.eval("state.analysisEnabled"), false);
  assert.equal(h.requests.length, 1);
  assert.match(h.requests[0], /analysis=0/);
  assert.equal(h.candles().length, 3);
  assert.equal(h.element("#info-panel").hidden, true);
  assert.equal(h.element("#freeze-button").hidden, true);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  assert.equal(h.markerCalls.at(-1).length, 0);
  h.element("#ray-tool").onclick();
  assert.equal(h.eval("rayLayer.active"), true);
  h.element("#measure-tool").onclick();
  assert.equal(h.eval("rayLayer.measureActive"), true);
  assert.equal(h.eval("rayLayer.items[0].id"), "own-ray");
});

test("toggle adds/removes the analysis without losing drawings, candles or zoom; off fetches nothing", async () => {
  const h = await boot();
  h.eval("state.measurementArchive.items.push({id: 'own-measurement'})");
  const candles = JSON.stringify(h.candles());
  const range = JSON.stringify(h.chart.timeScale().getVisibleLogicalRange());
  await h.element("#tori-analysis").onclick();
  assert.equal(h.eval("state.analysisEnabled"), true);
  assert.equal(h.element("#info-panel").hidden, false);
  assert.ok(h.eval("rayLayer.automatic.length") > 0);
  assert.ok(h.markerCalls.at(-1).length > 0);
  assert.equal(JSON.stringify(h.candles()), candles);
  assert.equal(JSON.stringify(h.chart.timeScale().getVisibleLogicalRange()), range);
  const count = h.requests.length;
  await h.element("#tori-analysis").onclick();
  assert.equal(h.requests.length, count);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  assert.equal(h.markerCalls.at(-1).length, 0);
  assert.equal(h.element("#info-panel").hidden, true);
  assert.equal(h.eval("rayLayer.items[0].id"), "own-ray");
  assert.equal(h.eval("state.measurementArchive.items[0].id"), "own-measurement");
  h.tfButtons[0].onclick();
  assert.equal(h.eval("state.analysisEnabled"), false);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  await h.element("#tori-analysis").onclick();
  assert.equal(h.element("#info-panel").hidden, false);
  assert.equal(h.requests.length, count); // analyzed bundle reused
});

test("research deep links still start without original signal markers", async () => {
  const h = await boot({ query: "?symbol=TEST&dataset=pinned&job=job&trial=trial" });
  assert.match(h.requests[0], /dataset-chart/);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  assert.equal(h.markerCalls.at(-1).length, 0);
  await h.element("#tori-analysis").onclick();
  assert.ok(h.markerCalls.at(-1).some((m) => m.shape === "arrowUp"));
  await h.element("#tori-analysis").onclick();
  assert.equal(h.markerCalls.at(-1).length, 0);
});

test("analysis error leaves a usable manual chart and permits retry", async () => {
  const h = await boot({ failAnalysis: true });
  await h.element("#tori-analysis").onclick();
  assert.equal(h.eval("state.analysisEnabled"), false);
  assert.equal(h.element("#tori-analysis").disabled, false);
  assert.equal(h.element("#info-panel").hidden, true);
  assert.equal(h.candles().length, 3);
  assert.match(h.element("#error").textContent, /Analysis failed/);
  h.element("#ray-tool").onclick();
  assert.equal(h.eval("rayLayer.active"), true);
});

test("a late analyzed response cannot restore overlays after switching off", async () => {
  const h = await boot({ deferred: true });
  const pending = h.element("#tori-analysis").onclick();
  await h.flush();
  await h.eval("toggleToriAnalysis()");
  h.resolveAnalysis();
  await pending;
  assert.equal(h.eval("state.analysisEnabled"), false);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  assert.equal(h.element("#info-panel").hidden, true);
  assert.equal(h.element("#loading").hidden, true);
});

test("refreshing manual candles invalidates the previously cached analysis", async () => {
  const h = await boot();
  await h.element("#tori-analysis").onclick();
  await h.element("#tori-analysis").onclick();
  const count = h.requests.filter((u) => u.includes("analysis=1")).length;
  await h.element("#refresh-button").onclick();
  assert.match(h.requests.at(-1), /analysis=0/);
  assert.equal(h.eval("state.analysisEnabled"), false);
  await h.element("#tori-analysis").onclick();
  assert.equal(h.requests.filter((u) => u.includes("analysis=1")).length, count + 1);
});

test("opening a saved stand keeps Tori off until clicked and then uses its original lines", async () => {
  const h = await boot();
  await h.eval("openSavedSnapshot('saved')");
  assert.equal(h.eval("state.frozen.id"), "saved");
  assert.equal(h.eval("state.analysisEnabled"), false);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  assert.equal(h.element("#info-panel").hidden, true);
  assert.equal(h.element("#step-back").disabled, false); // manual history remains accessible
  const count = h.requests.length;
  await h.element("#tori-analysis").onclick();
  assert.equal(h.eval("state.frozen.id"), "saved");
  assert.equal(h.requests.length, count);
  assert.ok(h.eval("rayLayer.automatic.length") > 0);
  assert.equal(h.element("#step-back").disabled, true); // archive boundary is active again
});

test("manual historical loading never enables the analysis", async () => {
  const h = await boot();
  await h.eval("load(state.symbol, false, new Date(state.data.analysisCutoff * 1000).toISOString())");
  assert.match(h.requests.at(-1), /analysis=0/);
  assert.match(h.requests.at(-1), /asof=/);
  assert.equal(h.eval("state.analysisEnabled"), false);
  assert.equal(h.eval("rayLayer.automatic.length"), 0);
  assert.match(h.element("#analysis-state").textContent, /Historisch.*Tori-Analyse aus/);
});


test('fan engine stays optional and keeps caches and snapshots separate', async()=>{
 const h=await boot(); const count=h.requests.length;
 h.element('#analysis-engine').value='fan_extreme';await h.element('#analysis-engine').onchange();
 assert.equal(h.eval('state.analysisEnabled'),false);assert.equal(h.requests.length,count);
 assert.notEqual(h.eval('frozenKey("TEST")'),'tori-frozen:TEST');
 await h.element('#tori-analysis').onclick();
 assert.match(h.requests.at(-1),/engine=fan_extreme/);assert.match(h.requests.at(-1),/analysis=1/);
 const key=h.eval('bundleKey("TEST",null)');
 h.element('#analysis-engine').value='fan_local';await h.element('#analysis-engine').onchange();
 assert.match(h.requests.at(-1),/engine=fan_local/);assert.notEqual(h.eval('bundleKey("TEST",null)'),key);
 h.element('#analysis-engine').value='legacy';await h.element('#analysis-engine').onchange();
 assert.equal(h.eval('frozenKey("TEST")'),'tori-frozen:TEST');
 assert.doesNotMatch(h.requests.at(-1),/engine=/);
});

test('fan case manual and analyzed loads stay pinned and engine cannot change',async()=>{
 const h=await boot({query:'?symbol=TEST&dataset=pinned&engine=fan_extreme&fan_job=job&fan_case=case'});
 assert.equal(h.eval('state.analysisEnabled'),false);assert.match(h.requests.at(-1),/api\/fan\/chart/);
 assert.match(h.requests.at(-1),/analysis=0/);assert.match(h.requests.at(-1),/fan_case=case/);
 assert.match(h.context.renderedUrl,/engine=fan_extreme/);assert.match(h.context.renderedUrl,/fan_case=case/);
 assert.equal(h.element('#analysis-engine').disabled,true);
 await h.element('#tori-analysis').onclick();assert.match(h.requests.at(-1),/api\/fan\/chart/);
 assert.match(h.requests.at(-1),/analysis=1/);assert.equal(h.element('#freeze-button').disabled,true);
 assert.ok(h.markerCalls.at(-1).some(m=>m.shape==='arrowUp'));
 assert.match(h.element('#line-table').innerHTML,/Signalstop \(fixiert\)/);
 h.element('#analysis-engine').value='fan_local';await h.element('#analysis-engine').onchange();
 assert.equal(h.eval('state.analysisEngine'),'fan_extreme');
 await h.eval('load("OTHER", false)');assert.equal(h.eval('state.fanCase'),null);assert.equal(h.eval('state.fanJob'),null);
 assert.doesNotMatch(h.requests.at(-1),/api\/fan\/chart/);
});


test('new Master profile draws blue main Safety and SMA context, toggle clears series and keeps manual chart',async()=>{
 const h=await boot({query:'?symbol=TEST&engine=fan_master'});
 assert.equal(h.eval('state.analysisEnabled'),false);assert.equal(h.candles().length,3);
 await h.element('#tori-analysis').onclick();assert.match(h.requests.at(-1),/engine=fan_master/);
 assert.equal(h.element('#master-sma-control').hidden,false);
 assert.equal(h.smaData['#a855f7'].length,3);assert.equal(h.smaData['#8b939f'].length,3);
 assert.equal(h.candles().length,3);assert.match(h.element('#line-table').innerHTML,/Haupt-Safety \(blau\)/);
 assert.ok(h.eval('rayLayer.automatic.some(r=>r.color==="#1e88e5" && r.label.includes("Safety"))'));
 h.element('#master-sma').checked=false;h.element('#master-sma').onchange();assert.equal(h.smaData['#8b939f'].length,0);
 h.element('#master-sma').checked=true;h.element('#master-sma').onchange();assert.equal(h.smaData['#8b939f'].length,3);
 await h.element('#tori-analysis').onclick();assert.equal(h.smaData['#a855f7'].length,0);
 assert.equal(h.element('#master-sma-control').hidden,true);assert.equal(h.candles().length,3);
});


test('MTF entry markers never fall back into an already closed candle before entry',async()=>{
 const h=await boot({query:'?symbol=TEST&dataset=pinned&engine=fan_master&fan_job=job&fan_case=case'});
 await h.element('#tori-analysis').onclick();assert.ok(h.markerCalls.at(-1).some(m=>m.shape==='arrowUp'));
 h.eval('state.data.researchSetup.entryAt=state.data.analysisCutoff+300;state.data.analysisCutoff+=3600;automaticLines()');
 assert.ok(!h.markerCalls.at(-1).some(m=>m.shape==='arrowUp'));
});

for(const variant of [
  {name:'normal chart',query:'?symbol=TEST&engine=fan_master'},
  {name:'local dataset',query:'?symbol=TEST&dataset=pinned&engine=fan_master'},
  {name:'random replay',path:'/zufall',query:'?engine=fan_master'},
])test(variant.name+': dynamic step, freeze, future candles, interval switch, unlock and back',async()=>{
  const h=await boot({...variant,moving:true});await h.flush();
  await h.element('#tori-analysis').onclick();
  assert.equal(h.element('#freeze-button').hidden,false);
  assert.match(h.element('#analysis-state').textContent,/Mitlaufend/);
  const initial=h.eval('state.data.lanes["4h"].red.b_price');
  await h.element('#step-next').onclick();
  assert.equal(h.candles().length,4);
  assert.notEqual(h.eval('state.data.lanes["4h"].red.b_price'),initial);
  await h.element('#freeze-button').onclick();
  assert.equal(h.element('#step-back').disabled,true);
  assert.equal(h.element('#freeze-button').textContent,'Fixierung lösen · Mitlaufen');
  const fixed=h.eval('JSON.stringify(state.frozen)'), cutoff=h.eval('state.frozen.analysisCutoff');
  const anchors=h.eval('JSON.stringify(state.data.lanes["4h"].red)');
  await h.element('#step-next').onclick();
  assert.equal(h.candles().length,5);
  assert.equal(h.eval('JSON.stringify(state.frozen)'),fixed);
  assert.equal(h.eval('state.data.lanes["4h"].red.b_price'),JSON.parse(anchors).b_price);
  assert.match(h.element('#analysis-state').textContent,/Fixiert:/);
  h.tfButtons[2].onclick();assert.equal(h.eval('state.timeframe'),'1D');
  assert.equal(h.eval('state.frozen.analysisCutoff'),cutoff);
  await h.element('#tori-analysis').onclick();
  assert.equal(h.eval('state.analysisEnabled'),false);assert.equal(h.eval('rayLayer.automatic.length'),0);
  await h.element('#step-next').onclick();
  assert.equal(h.eval('JSON.stringify(state.frozen)'),fixed); // hiding analysis keeps the freeze
  await h.element('#tori-analysis').onclick();
  assert.equal(h.eval('state.data.lanes["4h"].red.b_price'),JSON.parse(anchors).b_price);
  await h.element('#freeze-button').onclick();
  assert.equal(h.eval('state.frozen'),null);
  assert.notEqual(h.eval('state.data.lanes["4h"].red.b_price'),JSON.parse(anchors).b_price);
  assert.match(h.element('#analysis-state').textContent,/Mitlaufend/);
  await h.element('#step-back').onclick();assert.equal(h.candles().length,5);
});

test('failed freeze leaves dynamic mode usable and does not change stored stands',async()=>{
  const h=await boot({moving:true,failFreeze:true});await h.element('#tori-analysis').onclick();
  await h.element('#freeze-button').onclick();
  assert.equal(h.eval('state.frozen'),null);assert.equal(h.eval('state.freezing'),false);
  assert.match(h.element('#error').textContent,/Disk full/);
  assert.equal(h.element('#step-next').disabled,false);
  await h.element('#step-next').onclick();assert.equal(h.candles().length,4);
});

test('pending freeze blocks concurrent candle steps and model changes',async()=>{
  const h=await boot({moving:true,deferredFreeze:true});await h.element('#tori-analysis').onclick();
  const saving=h.element('#freeze-button').onclick();await h.flush();
  assert.equal(h.element('#step-next').disabled,true);assert.equal(h.element('#tori-analysis').disabled,true);
  const count=h.requests.length;await h.element('#step-next').onclick();assert.equal(h.requests.length,count);
  h.element('#analysis-engine').value='fan_master';await h.element('#analysis-engine').onchange();
  assert.equal(h.eval('state.analysisEngine'),'legacy');
  h.resolveFreeze();await saving;assert.ok(h.eval('state.frozen'));
  assert.equal(h.element('#step-next').disabled,false);
});

test('different random cases of the same stock have distinct freeze keys and no inherited lines',async()=>{
  const h=await boot({path:'/zufall',moving:true});await h.flush();
  await h.element('#tori-analysis').onclick();await h.element('#freeze-button').onclick();
  const oldKey=h.eval('frozenKey(state.symbol)');
  await h.element('#random-new').onclick();
  assert.equal(h.eval('state.frozen'),null);assert.equal(h.eval('state.analysisEnabled'),false);
  assert.notEqual(h.eval('frozenKey(state.symbol)'),oldKey);
  assert.ok(h.stored.get(oldKey));
});

test('sparse or frozen SMA context shares the entire candle grid without later values or off-grid points',async()=>{
  const h=await boot({query:'?symbol=TEST&engine=fan_master',moving:true});
  await h.element('#tori-analysis').onclick();
  h.eval('state.data.lanes["4h"].context.series["50"]=[{time:state.data.bars[0].time,value:100},{time:1,value:999}];updateMasterContext()');
  assert.deepEqual(h.smaData['#a855f7'].map(r=>r.time),h.candles().map(r=>r.time));
  assert.equal(h.smaData['#a855f7'].at(-1).value,undefined);
  await h.element('#freeze-button').onclick();await h.element('#step-next').onclick();
  assert.deepEqual(h.smaData['#a855f7'].map(r=>r.time),h.candles().map(r=>r.time));
  assert.equal(h.smaData['#a855f7'].at(-1).value,undefined);
});
