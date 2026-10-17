/* Per-symbol measurement archive. Deleted entries remain recoverable. */
const MeasurementStore = {
  normalize(value) {
    const valid = (item) =>
      item &&
      typeof item.id === "string" &&
      item.id.length > 0 &&
      item.id.length <= 80 &&
      ["1h", "4h", "1D"].includes(item.timeframe) &&
      Number.isFinite(item.createdAt) &&
      ["a", "b"].every(
        (key) =>
          item[key] &&
          Number.isFinite(item[key].time) &&
          item[key].time > 0 &&
          item[key].time < 4102444800 &&
          Number.isFinite(item[key].price) &&
          item[key].price > 0,
      );
    const unique = (items) => [
      ...new Map(
        (Array.isArray(items) ? items : [])
          .filter(valid)
          .map((item) => [item.id, item]),
      ).values(),
    ];
    const items = unique(value?.items),
      ids = new Set(items.map((item) => item.id));
    return {
      items,
      trash: unique(value?.trash).filter((item) => !ids.has(item.id)),
      activeId: ids.has(value?.activeId) ? value.activeId : null,
    };
  },
  add(value, item) {
    const current = this.normalize(value);
    return this.normalize({
      ...current,
      items: [...current.items, item],
      activeId: item.id,
    });
  },
  remove(value, id) {
    const current = this.normalize(value),
      item = current.items.find((m) => m.id === id);
    if (!item) return current;
    const items = current.items.filter((m) => m.id !== id);
    return {
      ...current,
      items,
      trash: [...current.trash, item],
      activeId:
        current.activeId === id ? items.at(-1)?.id || null : current.activeId,
    };
  },
  undo(value) {
    const current = this.normalize(value),
      item = current.trash.at(-1);
    return item
      ? {
          items: [...current.items, item],
          trash: current.trash.slice(0, -1),
          activeId: item.id,
        }
      : current;
  },
};
if (typeof module !== "undefined") module.exports = MeasurementStore;

function restoreMeasurements(symbol) {
  state.measurementSymbol = symbol;
  state.measurementArchive = MeasurementStore.normalize(
    read("tori-measurements:" + symbol, null),
  );
  rayLayer.measurement =
    state.measurementArchive.items.find(
      (m) => m.id === state.measurementArchive.activeId,
    ) || null;
  rayLayer.measurementSelected = !!rayLayer.measurement;
}
function commitMeasurementState(next, remember = false) {
  next = MeasurementStore.normalize(next);
  const previous = remember ? structuredClone(state.measurementArchive) : null;
  if (!write("tori-measurements:" + state.symbol, next)) {
    showError(
      "Messungen konnten nicht gespeichert werden. Bitte den Browserspeicher prüfen; der bisher gespeicherte Bestand bleibt erhalten.",
    );
    return false;
  }
  if (remember) rayLayer.remember(() => commitMeasurementState(previous));
  state.measurementArchive = next;
  rayLayer.measurement = next.items.find((m) => m.id === next.activeId) || null;
  rayLayer.selected = null;
  rayLayer.measurementSelected = !!rayLayer.measurement;
  updateMeasurementSummary();
  updateDrawingSummary();
  renderMeasurementList();
  rayLayer.update();
  return true;
}
function saveCompletedMeasurement(measurement) {
  const item = {
    ...measurement,
    id: crypto.randomUUID(),
    timeframe: state.timeframe,
    createdAt: Date.now() / 1000,
    analysisCutoff: state.data.analysisCutoff,
    provider: state.data.provider,
    feed: state.data.feed,
    adjustment: state.data.adjustment,
  };
  try {
    if (
      commitMeasurementState(
        MeasurementStore.add(state.measurementArchive, item),
        true,
      )
    )
      return;
  } catch (e) {
    showError(e.message);
  }
  rayLayer.measurement = { ...item, unsaved: true };
  rayLayer.selected = null;
  rayLayer.measurementSelected = true;
  rayLayer.remember(() => {
    restoreMeasurements(state.symbol);
    updateMeasurementSummary();
    rayLayer.update();
  });
  updateMeasurementSummary();
  updateDrawingSummary();
}
function deleteMeasurement(id) {
  if (
    commitMeasurementState(
      MeasurementStore.remove(state.measurementArchive, id),
      true,
    )
  )
    $("#measurements-note").textContent =
      "Messung gelöscht. Über „Wiederherstellen“ kannst du sie zurückholen.";
}
function openMeasurement(id) {
  const item = state.measurementArchive.items.find((m) => m.id === id);
  if (
    !item ||
    !commitMeasurementState({ ...state.measurementArchive, activeId: id })
  )
    return;
  $("#measurements-dialog").close();
  setTool(false);
  $("#error").hidden = true;
  const from = Math.min(item.a.time, item.b.time),
    to = Math.max(item.a.time, item.b.time),
    axis = state.data.axis;
  if (from < axis[0] || to > state.data.reference) {
    showError(
      "Diese Messung liegt außerhalb des gewählten Datenstands. Bitte über „Datum“ einen passenden Zeitpunkt öffnen. Die Messung bleibt gespeichert.",
    );
    return;
  }
  chart.timeScale().setVisibleLogicalRange({
    from: RayGeometry.logicalAt(axis, from) - 8,
    to: RayGeometry.logicalAt(axis, to) + 8,
  });
  chart.priceScale("right").applyOptions({ autoScale: true });
}
function renderMeasurementList() {
  const archive = state.measurementArchive || { items: [], trash: [] };
  $("#measurements-symbol").textContent =
    state.symbol + " · lokal in diesem Browser";
  $("#measurements-list").innerHTML = archive.items.length
    ? archive.items
        .map((m, i) => {
          const known = Math.max(m.a.time, m.b.time) <= state.data.reference;
          const result = RayGeometry.measure(state.data.axis, m.a, m.b);
          const description = known
            ? `${result.delta >= 0 ? "+" : ""}${fmt(result.delta)} ${state.data.currency} (${result.percent >= 0 ? "+" : ""}${fmt(result.percent)} %)`
            : "Liegt nach dem gewählten Chartzeitpunkt";
          return `<div class="measurement-row"><button data-measure-open="${esc(m.id)}" aria-label="Messung ${i + 1} öffnen"><b>${esc(m.timeframe)} · ${esc(description)}</b><small>${esc(dtLong(m.a.time))} → ${esc(dtLong(m.b.time))} ET</small></button><button data-measure-delete="${esc(m.id)}" aria-label="Messung ${i + 1} löschen" title="Messung löschen">×</button></div>`;
        })
        .join("")
    : '<p class="catalog-note">Noch keine Messungen gespeichert. Mit ↕ oder M zwei Punkte im Chart setzen.</p>';
  document
    .querySelectorAll("[data-measure-open]")
    .forEach((b) => (b.onclick = () => openMeasurement(b.dataset.measureOpen)));
  document
    .querySelectorAll("[data-measure-delete]")
    .forEach(
      (b) => (b.onclick = () => deleteMeasurement(b.dataset.measureDelete)),
    );
  $("#undo-measure-delete").disabled = !archive.trash.length;
  $("#measurements-note").textContent =
    `${archive.items.length} gespeichert · ${archive.trash.length} gelöscht und wiederherstellbar`;
  $("#measurements-tool").title =
    `Gespeicherte Messungen (${archive.items.length})`;
}
function setupMeasurements() {
  $("#measurements-tool").onclick = () => {
    if (!state.data) return;
    renderMeasurementList();
    $("#measurements-dialog").showModal();
  };
  $("#undo-measure-delete").onclick = () =>
    commitMeasurementState(
      MeasurementStore.undo(state.measurementArchive),
      true,
    );
  $("#clear-measurement").onclick = () => {
    if (rayLayer.measureDraft) {
      setTool(false);
      return;
    }
    const id = rayLayer.measurement?.id;
    if (id && state.measurementArchive.items.some((m) => m.id === id))
      deleteMeasurement(id);
    else {
      const previous = rayLayer.measurement;
      if (previous)
        rayLayer.remember(() => {
          rayLayer.measurement = previous;
          rayLayer.measurementSelected = true;
          updateMeasurementSummary();
          rayLayer.update();
        });
      rayLayer.measurement = null;
      rayLayer.measurementSelected = false;
      updateMeasurementSummary();
      updateDrawingSummary();
      rayLayer.update();
    }
  };
  rayLayer.onMeasureCommit = saveCompletedMeasurement;
}
