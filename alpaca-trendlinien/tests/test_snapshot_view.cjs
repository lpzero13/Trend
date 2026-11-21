const { test } = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const { RayGeometry } = require("../static/drawings.js");
const context = vm.createContext({
  state: { frozen: null },
  console,
  RayGeometry,
});
vm.runInContext(fs.readFileSync("static/analysis.js", "utf8"), context);

test('SMA200 uses only closed source candles; future prices and the viewport cannot affect its known prefix', () => {
  const rows=Array.from({length:205},(_,i)=>({time:i*3600,end:(i+1)*3600,close:i+1}));
  assert.equal(context.chartSma200(rows,199*3600).value,undefined);
  const known=context.chartSma200(rows,200*3600);
  assert.equal(known.rows.length,200);assert.equal(known.count,200);assert.equal(known.value,100.5);
  assert.equal(known.rows[198].value,undefined);
  assert.equal(context.chartSma200(rows,201*3600).value,101.5);
  const shocked=rows.map((r,i)=>({...r,close:i>=200?999999:r.close}));
  assert.equal(JSON.stringify(context.chartSma200(shocked,200*3600)),JSON.stringify(known));
  assert.equal(context.chartSma200(rows,200*3600-1).rows.length,199);
  assert.equal(context.chartSma200([],200*3600).count,0);
});

test('SMA200 never propagates an invalid close as a value or silently uses a shorter average',()=>{
  const rows=Array.from({length:405},(_,i)=>({time:i,end:i+1,close:10}));
  rows[200].close=NaN;
  assert.equal(context.chartSma200(rows,400).value,undefined);
  assert.equal(context.chartSma200(rows,401).value,10);
});

test('SMA200 honors known canonical source-gap resets, not ordinary overnight trading breaks',()=>{
  const rows=Array.from({length:405},(_,i)=>({time:i*86400,end:(i+1)*86400,close:i+1}));
  const gaps=[rows[200].time];
  assert.equal(context.chartSma200(rows,200*86400,gaps).value,100.5);
  assert.equal(context.chartSma200(rows,399*86400,gaps).count,199);
  assert.equal(context.chartSma200(rows,399*86400,gaps).value,undefined);
  assert.equal(context.chartSma200(rows,400*86400,gaps).value,300.5);
});
const bar = (time, close = 10) => ({
  time,
  end: time + 1,
  open: close,
  high: close + 1,
  low: close - 1,
  close,
});
function fixture() {
  const old = [bar(10), bar(20), bar(30)];
  const charts = Object.fromEntries(
    ["1h", "4h", "1D"].map((tf) => [tf, { bars: old }]),
  );
  const frozen = {
    symbol: "TEST",
    basis: "bars",
    validFrom: 31,
    payload: { charts },
  };
  const fresh = Object.fromEntries(
    ["1h", "4h", "1D"].map((tf) => [
      tf,
      {
        bars: [
          bar(10, 999),
          bar(20, 999),
          bar(30, 999),
          bar(40, 12),
          bar(50, 13),
        ],
      },
    ]),
  );
  return {
    frozen,
    bundle: { symbol: "TEST", analysisCutoff: 41, charts: fresh },
  };
}
test("frozen view retains archived candles despite provider revisions and excludes later bars", () => {
  const { frozen, bundle } = fixture();
  context.state.frozen = frozen;
  const original = JSON.stringify(frozen);
  context.assertFrozenCompatible(bundle, frozen);
  const view = context.snapshotChart(bundle, "1h");
  assert.deepEqual(
    Array.from(view.bars, (b) => [b.time, b.close]),
    [
      [10, 10],
      [20, 10],
      [30, 10],
      [40, 12],
    ],
  );
  assert.equal(view.latest.close, 12);
  assert.equal(JSON.stringify(frozen), original);
});

test('a frozen chart retains its original SMA gap resets and appends only known later resets',()=>{
  const {frozen,bundle}=fixture();
  frozen.payload.charts['1h'].smaGaps=[20];bundle.charts['1h'].smaGaps=[10,40,50];
  context.state.frozen=frozen;
  assert.deepEqual(Array.from(context.snapshotChart(bundle,'1h').smaGaps),[20,40]);
  assert.deepEqual(frozen.payload.charts['1h'].smaGaps,[20]);
});
test("future snapshot, wrong symbol and missing bridge are rejected", () => {
  const { frozen, bundle } = fixture();
  assert.throws(
    () =>
      context.assertFrozenCompatible({ ...bundle, analysisCutoff: 30 }, frozen),
    /später/,
  );
  assert.throws(
    () =>
      context.assertFrozenCompatible({ ...bundle, symbol: "OTHER" }, frozen),
    /Aktie/,
  );
  bundle.charts["1h"].bars = [bar(100), bar(110)];
  assert.throws(
    () => context.assertFrozenCompatible(bundle, frozen),
    /Datenlücke/,
  );
});
test("automatic view returns current data after unlocking", () => {
  const { bundle } = fixture();
  context.state.frozen = null;
  assert.equal(context.snapshotChart(bundle, "1h"), bundle.charts["1h"]);
});

test("frozen MTF projection stays fixed even when a source anchor initially lies beyond the last chart candle", () => {
  const { frozen } = fixture();
  const ray = { a_time: 10, a_price: 10, b_time: 60, b_price: 20 };
  ray.chartPositions = context.fixedChartPositions(ray, frozen, "1D");
  const old = [10, 20, 30],
    extended = [10, 20, 30, 40, 50, 100];
  assert.equal(context.chartProjection(ray, 20, old), 12);
  assert.equal(context.chartProjection(ray, 20, extended), 12);
  assert.equal(context.chartProjection(ray, 100, extended), 20);
});

test('freeze cannot leak across datasets, replay cases or an earlier analysis cutoff',()=>{
  const {frozen,bundle}=fixture();
  frozen.payload.datasetId='one';bundle.datasetId='two';
  assert.throws(()=>context.assertFrozenCompatible(bundle,frozen),/Datenbeständen/);
  bundle.datasetId='one';frozen.payload.randomCase={id:'a'};bundle.randomCase={id:'b'};
  assert.throws(()=>context.assertFrozenCompatible(bundle,frozen),/Replay/);
  bundle.randomCase={id:'a'};frozen.analysisCutoff=42;
  assert.throws(()=>context.assertFrozenCompatible(bundle,frozen),/später/);
});
