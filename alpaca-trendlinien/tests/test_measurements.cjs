const { test } = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const Store = require("../static/measurements.js");
const { RayLayer } = require("../static/drawings.js");
const item = (id = "one") => ({
  id,
  timeframe: "1h",
  createdAt: 1792000000,
  a: { time: 1791990000, price: 100 },
  b: { time: 1791993600, price: 110 },
});

test("multiple measurements and active selection round-trip through browser JSON storage", () => {
  let archive = Store.add(null, item());
  archive = Store.add(archive, item("two"));
  assert.deepEqual(
    Store.normalize(JSON.parse(JSON.stringify(archive))),
    archive,
  );
  assert.equal(archive.items.length, 2);
  assert.equal(archive.activeId, "two");
});
test("delete and restore survive serialization without changing stored endpoints", () => {
  const archive = Store.add(Store.add(null, item()), item("two")),
    before = JSON.stringify(archive);
  const deleted = Store.remove(archive, "two");
  assert.equal(JSON.stringify(archive), before);
  assert.equal(deleted.activeId, "one");
  assert.equal(deleted.items.length, 1);
  assert.equal(deleted.trash.length, 1);
  const restored = Store.undo(JSON.parse(JSON.stringify(deleted)));
  assert.deepEqual(restored.items, archive.items);
  assert.equal(restored.activeId, "two");
  assert.equal(restored.trash.length, 0);
});
test("delete of a non-selected measurement retains the selected one", () => {
  const archive = Store.add(Store.add(null, item()), item("two"));
  assert.equal(Store.remove(archive, "one").activeId, "two");
});
test("invalid saved points, duplicate IDs and duplicate trash entries are filtered", () => {
  const archive = Store.normalize({
    items: [
      item(),
      item(),
      { ...item("bad"), a: { time: NaN, price: 10 } },
      { ...item("huge"), b: { time: 1e30, price: 10 } },
      { ...item("zero"), b: { time: 100, price: 0 } },
    ],
    trash: [item(), item("trash")],
    activeId: "missing",
  });
  assert.deepEqual(archive.items, [item()]);
  assert.deepEqual(archive.trash, [item("trash")]);
  assert.equal(archive.activeId, null);
});
test("failed browser write leaves the prior archive and its active measurement intact", () => {
  const archive = Store.add(null, item()),
    errors = [];
  const context = vm.createContext({
    state: { measurementArchive: archive, symbol: "TEST" },
    rayLayer: { measurement: archive.items[0] },
    write: () => false,
    showError: (message) => errors.push(message),
  });
  vm.runInContext(fs.readFileSync("static/measurements.js", "utf8"), context);
  assert.equal(
    context.commitMeasurementState(Store.remove(archive, "one")),
    false,
  );
  assert.equal(context.state.measurementArchive, archive);
  assert.equal(context.rayLayer.measurement, archive.items[0]);
  assert.match(errors[0], /bisher gespeicherte Bestand bleibt erhalten/);
});
test("network failure is explained separately from a provider HTTP error", async () => {
  const context = vm.createContext({
    fetch: () => Promise.reject(new TypeError("Failed to fetch")),
  });
  vm.runInContext(fs.readFileSync("static/api.js", "utf8"), context);
  await assert.rejects(context.apiFetch("/api/chart"), /Start-Tori.ps1/);
  const providerResponse = { ok: false, status: 502 };
  context.fetch = () => Promise.resolve(providerResponse);
  assert.equal(await context.apiFetch("/api/chart"), providerResponse);
});

function drawingContext() {
  const layer = Object.assign(Object.create(RayLayer.prototype), {
    items: [],
    undoStack: [],
    update() {},
    onChange() {},
  });
  let writable = true;
  const context = vm.createContext({
    structuredClone,
    state: { measurementArchive: Store.normalize(null), symbol: "TEST" },
    rayLayer: layer,
    write: () => writable,
    showError() {},
    updateMeasurementSummary() {},
    updateDrawingSummary() {},
    renderMeasurementList() {},
  });
  vm.runInContext(fs.readFileSync("static/measurements.js", "utf8"), context);
  context.renderMeasurementList = () => {};
  return {
    context,
    layer,
    setWritable(value) {
      writable = value;
    },
  };
}

test("undo follows mixed ray and measurement edits in chronological order", () => {
  const { context, layer } = drawingContext();
  layer.remember();
  layer.items.push({ id: "ray" });
  context.commitMeasurementState(Store.add(null, item()), true);
  layer.selected = "ray";
  layer.remove();
  assert.equal(layer.items.length, 0);
  layer.undo();
  assert.equal(layer.items.length, 1);
  assert.equal(context.state.measurementArchive.items.length, 1);
  layer.undo();
  assert.equal(context.state.measurementArchive.items.length, 0);
  assert.equal(layer.items.length, 1);
  layer.undo();
  assert.equal(layer.items.length, 0);
  assert.equal(layer.undoStack.length, 0);
});

test("measurement deletion is undoable; failed writes preserve the undo action for retry", () => {
  const { context, layer, setWritable } = drawingContext();
  context.commitMeasurementState(Store.add(null, item()), true);
  context.commitMeasurementState(
    Store.remove(context.state.measurementArchive, "one"),
    true,
  );
  assert.equal(context.state.measurementArchive.trash.length, 1);
  setWritable(false);
  layer.undo();
  assert.equal(layer.undoStack.length, 2);
  assert.equal(context.state.measurementArchive.items.length, 0);
  setWritable(true);
  layer.undo();
  assert.equal(layer.undoStack.length, 1);
  assert.equal(layer.measurement.id, "one");
  assert.equal(layer.measurementSelected, true);
  assert.equal(context.state.measurementArchive.trash.length, 0);
  setWritable(false);
  assert.equal(
    context.commitMeasurementState(
      Store.remove(context.state.measurementArchive, "one"),
      true,
    ),
    false,
  );
  assert.equal(layer.undoStack.length, 1);
  assert.equal(layer.measurement.id, "one");
});

test("measurement selection only hits the visible border and cannot select future measurements", () => {
  const layer = Object.assign(Object.create(RayLayer.prototype), {
    measurement: item(),
    measurementEnd: 1791993600,
    point: (anchor) =>
      anchor.price === 100 ? { x: 100, y: 200 } : { x: 300, y: 100 },
  });
  assert.equal(layer.hitMeasurement({ x: 102, y: 150 }), true);
  assert.equal(layer.hitMeasurement({ x: 200, y: 100 }), true);
  assert.equal(layer.hitMeasurement({ x: 200, y: 150 }), false);
  layer.measurementEnd--;
  assert.equal(layer.hitMeasurement({ x: 102, y: 150 }), false);
});
