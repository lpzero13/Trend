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
    charts: Object.fromEntries(["1h", "4h", "1D"].map((tf) => [tf, { bars, latest, reference: times.at(-1) }])),
    sources: Object.fromEntries(["1h", "4h", "1D"].map((tf) => [tf, { cached: true, mode: "cache" }])),
    lanes: analyzed ? Object.fromEntries(["1h", "4h", "1D"].map((tf) => [tf,
      { red: ray(110, 109), green: ray(95, 96), outerRed: [], outerGreen: [],
        distance: 3, status: "Vorläufig", event: null }])) : {},
    ...(analyzed ? { analysisId: "known-analysis" } : {}),
    ...(analyzed && research ? { researchSetup: { entryAt: times.at(-1),
      entryPrice: 101, initialStop: 96, validRisk: true, variant: "breakout" } } : {}),
  };
}

async function boot({ query = "?symbol=TEST", failAnalysis = false, deferred = false } = {}) {
  const elements = new Map();
  function element(selector) {
    if (!elements.has(selector)) elements.set(selector, { hidden: true, disabled: false,
      checked: false, value: "", dataset: {}, attributes: {}, textContent: "", innerHTML: "",
      classList: { toggle() {} }, addEventListener() {}, close() {}, showModal() {},
      setAttribute(k, v) { this.attributes[k] = v; },
      replaceChildren() { this.innerHTML = ""; },
    });
    return elements.get(selector);
  }
  const tfButtons = ["1h", "4h", "1D"].map((tf) => Object.assign(element(tf), { dataset: { tf } }));
  const requests = [], markerCalls = [], stored = new Map([
    ["tori-analysis-enabled", "true"], ["tori-info", "true"],
    ["tori-frozen:TEST", '"old-snapshot"'], ["tori-rays:TEST", JSON.stringify([manualRay])],
  ]);
  let range = null, candleData = [], resolveAnalysis;
  const scale = { getVisibleLogicalRange: () => range, setVisibleLogicalRange: (r) => { range = r; },
    subscribeVisibleLogicalRangeChange() {}, applyOptions() {} };
  const price = { applyOptions() {}, options: () => ({ autoScale: true }) };
  const chart = { applyOptions() {}, timeScale: () => scale, priceScale: () => price,
    subscribeCrosshairMove() {}, addSeries(type, options) {
      chart.autoScale = options.autoscaleInfoProvider;
      return { applyOptions() {}, setData(rows) { candleData = rows; } };
    } };
  class Layer {
    constructor() { this.items = []; this.automatic = []; this.undoStack = []; }
    update() {}
    load(items) { this.items = items; }
    setMode(mode) { this.active = mode === true; this.measureActive = mode === "measure"; }
  }
  const context = vm.createContext({ console, URLSearchParams, Intl, Date, Map, structuredClone,
    RayGeometry, RayLayer: Layer, matchMedia: () => ({ matches: false }),
    location: { search: query }, history: { replaceState() {} },
    localStorage: { getItem: (k) => stored.get(k) ?? null, setItem: (k, v) => stored.set(k, v) },
    performance: { now: () => 0 }, queueMicrotask, requestAnimationFrame: (fn) => fn(),
    setTimeout, clearTimeout,
    document: { documentElement: { dataset: {} }, querySelector: element, addEventListener() {},
      querySelectorAll: (s) => s === "[data-tf]" ? tfButtons : [] },
    LightweightCharts: { createChart: () => chart, CandlestickSeries: {},
      CrosshairMode: { Normal: 0 }, TickMarkType: { Time: 0 },
      createSeriesMarkers: () => ({ setMarkers(markers) { markerCalls.push(markers); } }) },
    apiFetch: async (url) => {
      requests.push(url);
      if (url === "/api/snapshots/saved") {
        const data = payload(true);
        return { ok: true, json: async () => ({ id: "saved", symbol: "TEST", basis: "bars",
          analysisCutoff: data.analysisCutoff, validFrom: data.analysisCutoff, payload: data }) };
      }
      if (url.startsWith("/api/chart?") || url.startsWith("/api/dataset-chart?")) {
        const analyzed = new URL(url, "http://localhost").searchParams.get("analysis") === "1";
        if (analyzed && deferred) await new Promise((resolve) => { resolveAnalysis = resolve; });
        const data = payload(analyzed, query.includes("trial="));
        data.historical = new URL(url, "http://localhost").searchParams.has("asof");
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
  return { context, element, requests, markerCalls, stored, chart, tfButtons, flush,
    eval: (code) => vm.runInContext(code, context), candles: () => candleData,
    resolveAnalysis: () => resolveAnalysis() };
}

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
