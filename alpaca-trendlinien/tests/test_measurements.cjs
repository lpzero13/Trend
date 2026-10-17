const { test } = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const Store = require("../static/measurements.js");
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
