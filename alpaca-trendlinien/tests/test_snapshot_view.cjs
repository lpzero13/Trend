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
