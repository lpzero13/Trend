const { test } = require("node:test");
const assert = require("node:assert/strict");
const { RayGeometry: G, RayLayer } = require("../static/drawings.js");

const hour = 3600;
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-7, `${a} != ${b}`);

test("measurement uses the first price as percentage base in either time direction", () => {
  const axis = [0, hour, 20 * hour];
  const gain = G.measure(
    axis,
    { time: 0, price: 100 },
    { time: 20 * hour, price: 110 },
  );
  assert.deepEqual(gain, { delta: 10, percent: 10, steps: 2 });
  const loss = G.measure(
    axis,
    { time: 20 * hour, price: 110 },
    { time: 0, price: 100 },
  );
  near(loss.percent, -100 / 11);
  assert.equal(loss.delta, -10);
  assert.equal(loss.steps, 2);
  assert.deepEqual(
    G.measure(axis, { time: hour, price: 100 }, { time: hour, price: 100 }),
    { delta: 0, percent: 0, steps: 0 },
  );
});

test("timestamps round-trip on a compressed session axis, including inside gaps", () => {
  const axis = [0, hour, 2 * hour, 20 * hour, 21 * hour, 87 * hour, 88 * hour];
  for (const time of [
    -hour,
    0,
    hour / 2,
    2 * hour,
    7 * hour,
    20 * hour,
    55 * hour,
    88 * hour,
    90 * hour,
  ])
    near(G.timeAt(axis, G.logicalAt(axis, time)), time);
});

test("one unit per candle across overnight and weekend gaps", () => {
  const axis = [0, hour, 2 * hour, 20 * hour, 21 * hour, 87 * hour, 88 * hour];
  const ray = { a: { time: 0, price: 100 }, b: { time: 2 * hour, price: 102 } };
  axis.forEach((time, i) => near(G.candleValue(axis, ray, time), 100 + i));
  near(G.candleValue(axis, ray, ray.a.time), ray.a.price);
  near(G.candleValue(axis, ray, ray.b.time), ray.b.price);
});

test("anchors between chart bars are preserved exactly", () => {
  const axis = [0, 4 * hour, 8 * hour, 24 * hour];
  const ray = {
    a: { time: hour, price: 10 },
    b: { time: 7 * hour, price: 16 },
  };
  near(G.candleValue(axis, ray, ray.a.time), 10);
  near(G.candleValue(axis, ray, ray.b.time), 16);
  near(G.candleValue(axis, ray, 4 * hour), 13);
});

test("appending candles cannot move prices on the frozen axis prefix", () => {
  const old = [0, hour, 20 * hour, 21 * hour],
    extended = [...old, 87 * hour, 88 * hour];
  const ray = {
    a: { time: hour / 2, price: 10 },
    b: { time: 20 * hour, price: 12 },
  };
  for (const time of old)
    near(G.candleValue(old, ray, time), G.candleValue(extended, ray, time));
});

test("normal interval, not last weekend gap, is used outside loaded history", () => {
  const axis = [0, hour, 2 * hour, 20 * hour, 21 * hour, 87 * hour];
  near(G.timeAt(axis, 6), 88 * hour);
  near(G.logicalAt(axis, 88 * hour), 6);
  const daily = [0, 86400, 2 * 86400, 3 * 86400 - 3600, 4 * 86400 - 3600];
  near(G.step(daily), 86400);
});

test("zoom is symmetric and bounded; latest preserves zoom width", () => {
  const original = { from: 20, to: 120 };
  const zoomed = G.zoom(original, 0.75, 300);
  near(zoomed.to - zoomed.from, 75);
  near((zoomed.to + zoomed.from) / 2, 70);
  const restored = G.zoom(zoomed, 1 / 0.75, 300);
  near(restored.from, original.from);
  near(restored.to, original.to);
  const latest = G.latest(zoomed, 300);
  near(latest.to, 307);
  near(latest.to - latest.from, 75);
  near(
    G.zoom({ from: 0, to: 7 }, 0.1, 300).to -
      G.zoom({ from: 0, to: 7 }, 0.1, 300).from,
    6,
  );
});

test("zooming the latest view keeps the last candle visible and preserves the right margin", () => {
  const initial = { from: 120, to: 307 };
  const zoomed = G.zoom(initial, 0.75, 300);
  near(zoomed.to, 307);
  assert.ok(zoomed.from < 299);
  const restored = G.zoom(zoomed, 1 / 0.75, 300);
  near(restored.from, initial.from);
  near(restored.to, initial.to);
});

test("renderer draws one straight segment across compressed overnight pauses", () => {
  const axis = [0, hour, 2 * hour, 20 * hour, 21 * hour];
  const layer = Object.create(RayLayer.prototype);
  const lines = [];
  Object.assign(layer, {
    axis: () => axis,
    chart: {
      timeScale: () => ({
        logicalToCoordinate: (n) => n * 10,
        coordinateToLogical: (x) => x / 10,
      }),
    },
    series: { priceToCoordinate: (p) => p },
    automatic: [
      {
        a: { time: 0, price: 100 },
        b: { time: 2 * hour, price: 102 },
        color: "red",
        width: 2,
        dash: [],
      },
    ],
    items: [],
  });
  const ctx = {
    save() {},
    restore() {},
    beginPath() {},
    rect() {},
    clip() {},
    setLineDash() {},
    stroke() {},
    moveTo(x, y) {
      lines.push([x, y]);
    },
    lineTo(x, y) {
      lines.push([x, y]);
    },
  };
  layer.paint(ctx, { width: 40, height: 200 });
  assert.deepEqual(lines, [
    [0, 100],
    [40, 104],
  ]);
});

test("visible line segments render even when source anchors are outside the viewport", () => {
  const axis = Array.from({ length: 30 }, (_, i) => i * hour);
  const layer = Object.create(RayLayer.prototype),
    lines = [];
  Object.assign(layer, {
    axis: () => axis,
    chart: {
      timeScale: () => ({
        logicalToCoordinate: (n) => (n < 10 ? null : (n - 10) * 10),
        coordinateToLogical: (x) => 10 + x / 10,
      }),
    },
    series: { priceToCoordinate: (p) => (p > 200 ? null : p) },
    automatic: [
      {
        a: { time: 0, price: 300 },
        b: { time: 2 * hour, price: 280 },
        color: "red",
        width: 2,
        dash: [],
      },
    ],
    items: [],
  });
  const ctx = {
    save() {},
    restore() {},
    beginPath() {},
    rect() {},
    clip() {},
    setLineDash() {},
    stroke() {},
    moveTo(x, y) {
      lines.push([x, y]);
    },
    lineTo(x, y) {
      lines.push([x, y]);
    },
  };
  layer.paint(ctx, { width: 40, height: 200 });
  assert.deepEqual(lines, [
    [0, 200],
    [40, 160],
  ]);
});

test("labels for nearly coincident intervals avoid each other and the info panel", () => {
  const boxes = [],
    texts = [];
  const obstacle = { x: 190, y: 0, w: 110, h: 90 };
  const layer = Object.create(RayLayer.prototype);
  Object.assign(layer, {
    axis: () => [0, hour, 2 * hour],
    chart: {
      timeScale: () => ({
        logicalToCoordinate: (n) => n * 100,
        coordinateToLogical: (x) => x / 100,
      }),
    },
    series: { priceToCoordinate: (p) => p },
    labelObstacles: () => [obstacle],
    automatic: ["1D", "4h", "1h"].map((tf, i) => ({
      a: { time: 0, price: 100 + i },
      b: { time: hour, price: 101 + i },
      color: "red",
      width: 2,
      dash: [],
      label: tf + " · Rot",
      labelEdge: true,
    })),
    items: [],
  });
  const ctx = {
    save() {},
    restore() {},
    beginPath() {},
    rect() {},
    clip() {},
    setLineDash() {},
    stroke() {},
    moveTo() {},
    lineTo() {},
    measureText: () => ({ width: 50 }),
    fillRect: (x, y, w, h) => boxes.push({ x, y, w, h }),
    fillText: (text) => texts.push(text),
  };
  layer.paint(ctx, { width: 300, height: 220 });
  assert.deepEqual(texts, ["1D · Rot", "4h · Rot", "1h · Rot"]);
  const intersects = (a, b) =>
    a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  boxes.forEach((a, i) => {
    assert.ok(a.y >= 0 && a.y + a.h <= 220);
    assert.ok(!intersects(a, obstacle));
    boxes.slice(i + 1).forEach((b) => assert.ok(!intersects(a, b)));
  });
});
