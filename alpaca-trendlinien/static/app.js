const $ = (selector) => document.querySelector(selector);
const LC = LightweightCharts;
const fmt = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("de-DE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(n);
const dt = (n) =>
  new Intl.DateTimeFormat("de-DE", {
    timeZone: "America/New_York",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(n * 1000));
const dtLong = (n) =>
  new Intl.DateTimeFormat("de-DE", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(n * 1000));
const esc = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const read = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
};
let storageWarning = false;
const write = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    storageWarning = true;
    $("#connection").textContent = "Browserspeicher nicht verfügbar";
    return false;
  }
};
const query = new URLSearchParams(location.search);
const randomMode = location.pathname === '/zufall';
const drawingScope = () => state.randomId ? 'random:'+state.randomId : state.symbol;
const state = {
  symbol: query.get("symbol") || "MSFT",
  timeframe: ["1h", "4h", "1D", "1W"].includes(query.get("tf"))
    ? query.get("tf")
    : "4h",
  range: 30,
  data: null,
  analysisEnabled: false,
  analysisEngine: ["fan_extreme", "fan_local", "fan_master"].includes(query.get("engine")) ? query.get("engine") : "legacy",
  fanJob: query.get("fan_job") || null,
  fanCase: query.get("fan_case") || null,
  bundles: new Map(),
  visible: { "1D": true, "4h": true, "1h": true, "1W":true },
  request: 0,
  theme: read(
    "tori-theme",
    matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  ),
  favorites: read("tori-favorites", [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "TSLA",
    "SPY",
  ]),
  favoriteOnly: false,
  assetOffset: 0,
  assetRequest: 0,
  assetRows: [],
  info: true,
  infoCollapsed: false,
  axisMode: "trading",
  asOf: query.get("asof") || null,
  datasetId: query.get("dataset") || null,
  randomId: randomMode ? query.get('case') : null,
  randomStartAt: null,
  randomPicking: false,
  drawingScope: null,
  researchJob: query.get("job") || null,
  researchTrial: query.get("trial") || null,
  researchVariant: query.get("variant") || null,
  stepping: false,
  freezing: false,
  frozen: null,
  snapshotLists: new Map(),
  measurementSymbol: null,
  measurementArchive: { items: [], trash: [], activeId: null },
  includeLines: read("tori-fit-lines", false),
  showSma: read("tori-master-sma", true),
  showDateMarker: read("tori-master-date", true),
  contextSeries: {},
};
const chart = LC.createChart($("#chart"), {
  autoSize: true,
  layout: { attributionLogo: true, fontFamily: "Arial", fontSize: 12 },
  rightPriceScale: {
    borderVisible: false,
    minimumWidth: 70,
    scaleMargins: { top: 0.13, bottom: 0.1 },
  },
  timeScale: {
    borderVisible: false,
    timeVisible: true,
    rightOffset: 14,
    barSpacing: 9,
    lockVisibleTimeRangeOnResize: true,
    minBarSpacing: 0.02,
    maxBarSpacing: 90,
  },
  crosshair: { mode: LC.CrosshairMode.Normal },
  localization: { locale: "de-DE", priceFormatter: fmt, timeFormatter: dt },
  handleScroll: {
    mouseWheel: false,
    pressedMouseMove: true,
    horzTouchDrag: true,
    vertTouchDrag: true,
  },
  handleScale: {
    mouseWheel: true,
    pinch: true,
    axisPressedMouseMove: { time: true, price: true },
    axisDoubleClickReset: { time: true, price: true },
  },
});
const candles = chart.addSeries(LC.CandlestickSeries, {
  borderVisible: false,
  autoscaleInfoProvider: (base) => {
    const info = base();
    if (!info || !state.data) return info;
    const p = [info.priceRange.minValue, info.priceRange.maxValue];
    const visible = chart.timeScale().getVisibleLogicalRange();
    const axis = state.data.axis;
    const from = visible
      ? RayGeometry.timeAt(axis, Math.max(0, visible.from))
      : state.data.reference;
    const to = visible
      ? RayGeometry.timeAt(axis, Math.min(axis.length + 7, visible.to))
      : state.data.reference;
    for (const tf of state.includeLines && hasToriAnalysis() ? lanes() : []) {
      if (!state.visible[tf]) continue;
      for (const kind of ["red", "green"]) {
        const r = state.data.lanes[tf][kind];
        if (r && to >= r.a_time) {
          for (const time of [Math.max(from, r.a_time), to]) {
            const value = chartProjection(r, time, axis);
            if (value > 0 && Number.isFinite(value)) p.push(value);
          }
        }
      }
    }
    return {
      ...info,
      priceRange: { minValue: Math.min(...p), maxValue: Math.max(...p) },
    };
  },
});
const markerPlugin = LC.createSeriesMarkers(candles, []);
chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
  if (range) $("#chart").dataset.visibleRange = JSON.stringify(range);
});
const rayLayer = new RayLayer(
  chart,
  candles,
  () => state.data?.axis || [],
  (items) => {
    write("tori-rays:" + drawingScope(), items);
    updateDrawingSummary();
  },
);
rayLayer.labelObstacles = () => {
  const host = $("#chart").getBoundingClientRect();
  return [$("#info-panel"), $(".instrument"), $(".view-tools")]
    .filter((el) => el && !el.hidden)
    .map((el) => {
      const r = el.getBoundingClientRect();
      return {
        x: r.left - host.left - 5,
        y: r.top - host.top - 5,
        w: r.width + 10,
        h: r.height + 10,
      };
    });
};
function lanes() {
  return ["1D", "4h", ...(["1h","1W"].includes(state.timeframe) ? [state.timeframe] : [])].filter(tf=>state.data?.lanes?.[tf]);
}
function theme() {
  document.documentElement.dataset.theme = state.theme;
  const dark = state.theme === "dark";
  chart.applyOptions({
    layout: {
      background: { type: "solid", color: dark ? "#11151e" : "#ffffff" },
      textColor: dark ? "#aeb9cb" : "#5c6777",
    },
    grid: {
      vertLines: { color: dark ? "#202632" : "#f0f2f5" },
      horzLines: { color: dark ? "#202632" : "#f0f2f5" },
    },
    crosshair: {
      vertLine: {
        color: "#8b98aa",
        labelBackgroundColor: dark ? "#3b465b" : "#576376",
      },
      horzLine: {
        color: "#8b98aa",
        labelBackgroundColor: dark ? "#3b465b" : "#576376",
      },
    },
  });
  candles.applyOptions({
    upColor: dark ? "#20b998" : "#00a483",
    downColor: dark ? "#f05a70" : "#f23752",
    wickUpColor: dark ? "#20b998" : "#00a483",
    wickDownColor: dark ? "#f05a70" : "#f23752",
  });
  $("#theme-button").textContent = dark ? "☀" : "☾";
  $("#theme-button").title = dark
    ? "Zum Hellmodus wechseln"
    : "Zum Dunkelmodus wechseln";
  rayLayer.update();
}
function setTool(active) {
  rayLayer.setMode(active);
  $("#ray-tool").setAttribute("aria-pressed", String(active === true));
  $("#measure-tool").setAttribute("aria-pressed", String(active === "measure"));
  $("#cursor-tool").setAttribute("aria-pressed", String(!active));
  $("#drawing-hint").hidden = !active;
  if (active)
    $("#drawing-hint").textContent =
      active === "measure"
        ? "Messung: Startpreis setzen · dann Endpreis · Escape zum Abbrechen"
        : "Ersten Punkt setzen · dann zweiten Punkt · Escape zum Abbrechen";
}
rayLayer.onMeasure = () => {
  updateMeasurementSummary();
  updateDrawingSummary();
};
function updateMeasurementSummary() {
  const m = rayLayer.measureDraft || rayLayer.measurement,
    data = state.data;
  const visible =
    m && data && m.a.time <= data.reference && m.b.time <= data.reference;
  $("#measurement-result").hidden = !visible;
  if (!visible) return;
  const result = RayGeometry.measure(data.axis, m.a, m.b);
  $("#measurement-result").classList.toggle("loss", result.delta < 0);
  $("#measurement-text").textContent =
    `${result.delta >= 0 ? "+" : ""}${fmt(result.delta)} ${data.currency} pro Aktie (${result.percent >= 0 ? "+" : ""}${fmt(result.percent)} %) · ${result.steps} Kerzenschritte · ${fmt(m.a.price)} → ${fmt(m.b.price)}${m.unsaved ? " · nur diese Sitzung" : ""}`;
}
rayLayer.onHint = (text) => {
  $("#drawing-hint").textContent = text;
};
rayLayer.onDone = () => setTool(false);
rayLayer.onSelection = () => {
  const selected=rayLayer.items.find(r=>r.id===rayLayer.selected);
  if(selected) $('#line-extension').value=selected.extend || 'right';
  if(selected) {
    $('#line-color').value=RayGeometry.color(selected.color);
    rayLayer.color=$('#line-color').value;
  }
  updateDrawingSummary();
};
function updateDrawingSummary() {
  $("#drawing-summary").textContent =
    `Eigene Rays: ${rayLayer.items.length} · Messungen: ${state.measurementArchive.items.length}${storageWarning ? " · Speicherung fehlgeschlagen" : ""}`;
  const measurementSelected =
    rayLayer.measurementSelected &&
    rayLayer.measurement &&
    !$("#measurement-result").hidden;
  const draft = rayLayer.draft || rayLayer.measureDraft;
  $("#delete-tool").disabled = !(
    rayLayer.selected ||
    measurementSelected ||
    draft
  );
  $("#delete-tool").title = draft
    ? "Angefangene Zeichnung abbrechen (Entf)"
    : measurementSelected
      ? "Ausgewählte Messung löschen (Entf)"
      : "Ausgewählte Linie löschen (Entf)";
  $("#undo-tool").disabled = !(rayLayer.undoStack.length || draft);
}
function deleteDrawing() {
  if (rayLayer.draft || rayLayer.measureDraft) setTool(false);
  else if (rayLayer.selected) rayLayer.remove();
  else if (rayLayer.measurementSelected && !$("#measurement-result").hidden)
    $("#clear-measurement").onclick();
  updateDrawingSummary();
}
function undoDrawing() {
  if (rayLayer.draft || rayLayer.measureDraft) setTool(false);
  else rayLayer.undo();
  updateDrawingSummary();
}
// Selection can change without changing stored geometry.
$("#chart").addEventListener("pointerup", () =>
  queueMicrotask(updateDrawingSummary),
);
function storedRays(symbol) {
  return read("tori-rays:" + symbol, []).filter(
    (r) =>
      r &&
      typeof r.id === "string" &&
      r.a &&
      r.b &&
      [r.a.time, r.b.time, r.a.price, r.b.price].every(Number.isFinite) &&
      r.a.time < r.b.time &&
      r.a.price > 0 &&
      r.b.price > 0,
  ).map(r=>{
    if(r.basis && !RayGeometry.validBasis(r.basis)) { const copy={...r};delete copy.basis;return copy; }
    return r;
  });
}
function updateMasterDateMarker() {
  const active=hasToriAnalysis() && state.analysisEngine==='fan_master';
  $('#master-date-control').hidden=!active;$('#master-date').checked=state.showDateMarker;
  const visible=active && state.showDateMarker && state.data.historical;
  const x=visible ? chart.timeScale().logicalToCoordinate?.(state.data.axis.length-1) : null;
  $('#master-date-line').hidden=!visible || !Number.isFinite(x) || x<0;
  if(visible && Number.isFinite(x)) {
    $('#master-date-line').setAttribute('style',`left:${x}px`);
    $('#master-date-line span').textContent=`Ausgewerteter Schluss · ${dtLong(state.data.latest.end)} ET`;
  }
}
$('#master-date').onchange=()=>{state.showDateMarker=$('#master-date').checked;write('tori-master-date',state.showDateMarker);updateMasterDateMarker();};
chart.timeScale().subscribeVisibleLogicalRangeChange(updateMasterDateMarker);
function updateMasterContext() {
  updateMasterDateMarker();
  const active=hasToriAnalysis() && state.analysisEngine==='fan_master';
  $('#master-sma-control').hidden=!active;$('#master-sma').checked=state.showSma;
  if(!LC.LineSeries)return;
  for(const period of ['50','200']) {
    // Context can end before the replay candle (warm-up, gaps, frozen stand).
    // Keep every plotted series on exactly the candle grid, including whitespace.
    const known = new Map((state.data?.lanes[state.timeframe]?.context?.series?.[period] || []).map(row=>[row.time,row]));
    const rows=active && state.showSma ? state.data.bars.map(bar=>known.get(bar.time) || {time:bar.time}) : [];
    if(rows.length && !state.contextSeries[period])state.contextSeries[period]=chart.addSeries(LC.LineSeries,{color:period==='50'?'#a855f7':'#8b939f',lineWidth:period==='50'?1:2,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});
    state.contextSeries[period]?.setData(rows);
  }
}
$('#master-sma').onchange=()=>{state.showSma=$('#master-sma').checked;write('tori-master-sma',state.showSma);updateMasterContext();};
function automaticLines() {
  updateMasterContext();
  rayLayer.automatic = [];
  if (!hasToriAnalysis()) {
    markerPlugin.setMarkers([]);
    rayLayer.update();
    return;
  }
  const markers = [];
  for (const tf of lanes()) {
    if (!state.visible[tf]) continue;
    const lane = state.data.lanes[tf];
    const add = (r, kind, outer = false, retest = false) => {
      if (!r) return;
      const master = r.algorithm === "master";
      const color = retest ? "#f48200" : master ? r.color : kind === "red" ? "#ff4564" : "#0bbb78";
      rayLayer.automatic.push({
        ...asRay(r),
        color: outer && !master ? color + "44" : color,
        width: master && !retest ? (outer ? 2 : 3) : outer ? 1 : tf === state.timeframe ? 2.5 : 2,
        dash: retest
          ? tf === "1D"
            ? [2, 5]
            : [13, 9]
          : master ? (r.qualified ? [] : [8,5]) : tf === "1D"
            ? []
            : tf === "4h"
              ? [8, 5]
              : [2, 4],
        label: outer && !master
          ? ""
          : retest
            ? `${tf} Bruch · ${dt(lane.retest.closedAt)}`
            : master ? `${tf} · ${kind === "red" ? "Widerstand" : "Safety"} ${r.level}${r.provisionalEnvelope ? " · Hülle" : ""} · ${r.contacts} K${r.qualified ? " · A+" : ""}` : `${tf} · ${kind === "red" ? "Rot" : "Grün"}`,
        labelColor: retest ? "#985000" : master ? r.color : kind === "red" ? "#b72642" : "#087847",
        labelEdge: !retest,
        labelAt: retest
          ? {
              time: lane.retest.time,
              price: chartProjection(r, lane.retest.time, state.data.axis),
            }
          : null,
      });
    };
    if ($("#outer-lines").checked) {
      lane.outerRed.forEach((r) => add(r, "red", true));
      lane.outerGreen.filter(r=>r.id!==lane.mainSafety?.id).forEach((r) => add(r, "green", true));
    }
    add(lane.red, "red");
    if(lane.mainSafety && lane.mainSafety.id!==lane.green?.id)add(lane.mainSafety,"green",true);
    if(lane.tightSafety && lane.tightSafety.id!==lane.green?.id && lane.tightSafety.id!==lane.mainSafety?.id)add(lane.tightSafety,"green",true);
    add(lane.green, "green");
    if (lane.retest) add(lane.retest.ray, "red", false, true);
    if (tf === state.timeframe) {
      for (const kind of ["red", "green"]) {
        const r = lane[kind];
        if (!r) continue;
        for (const time of r.algorithm === "master" && r.contactPoints ? r.contactPoints.map(p=>p.time) : [r.a_time, r.b_time]) {
          const b = state.data.bars.findLast((b) => b.time <= time && time < b.end);
          if (b)
            markers.push({
              time: b.time,
              position: kind === "red" ? "aboveBar" : "belowBar",
              color: kind === "red" ? "#ff4564" : "#0bbb78",
              shape: "circle",
              size: 0.6,
            });
        }
      }
    }
  }
  const setup = state.data.researchSetup;
  if (setup?.entryAt && setup.entryAt <= state.data.analysisCutoff) {
    const at = state.data.bars.findLast((b) => b.time <= setup.entryAt && setup.entryAt < b.end);
    if (at)
      markers.push({
        time: at.time,
        position: "belowBar",
        color: "#2765d5",
        shape: "arrowUp",
        text: `${setup.variant === "retest" ? "Retest" : setup.variant === "horizontal" ? "Horizontal bestätigt" : "Ausbruch"} · Entry ${fmt(setup.entryPrice)}`,
      });
    if (setup.validRisk && setup.initialStop) {
      rayLayer.automatic.push({
        a: { time: setup.entryAt, price: setup.initialStop },
        b: {
          time: Math.max(setup.entryAt + 3600, state.data.reference),
          price: setup.initialStop,
        },
        color: "#b96b1b",
        width: 1.5,
        dash: [4, 4],
        label: `Schutzmarke · ${fmt(setup.initialStop)}`,
        labelColor: "#985000",
        labelEdge: true,
      });
    }
  }
  markerPlugin.setMarkers(markers.sort((a, b) => a.time - b.time));
  rayLayer.update();
}
function table() {
  const data = state.data;
  if (!hasToriAnalysis()) {
    $("#line-table").replaceChildren();
    $("#layer-controls").replaceChildren();
    return;
  }
  const tfs = lanes();
  const extraRows=[];
  const rows = [
    [
      "Rot",
      (tf) => `<span class="red">${fmt(data.lanes[tf].red?.value)}</span>`,
    ],
    [
      state.analysisEngine === "fan_master" ? "Safety (gewählt)" : "Grün",
      (tf) => `<span class="green">${fmt(data.lanes[tf].green?.value)}</span>`,
    ],
    [
      "Abstand¹",
      (tf) =>
        data.lanes[tf].distance == null
          ? "—"
          : fmt(data.lanes[tf].distance) + " %",
    ],
    [
      state.frozen ? "Stand bei Fixierung" : "Zustand",
      (tf) =>
        esc(
          data.lanes[tf].partial ? "Historie begrenzt" : data.lanes[tf].status,
        ),
    ],
    [
      state.frozen ? "Kontakte (fixiert)" : "Kontakte",
      (tf) =>
        `R: ${data.lanes[tf].red?.contacts ?? "—"} / G: ${data.lanes[tf].green?.contacts ?? "—"}`,
    ],
    [
      state.frozen ? "Bruch bis Fixierung" : "Bruch",
      (tf) => {
        const e = data.lanes[tf].event;
        return e
          ? `${e.kind === "fan_break" || tf === "4h" && data.researchSetup?.entryMode === "tori" ? "Rot, ursprünglicher Bruch" : e.kind === "green_break" ? "Grün" : e.kind === "long_break" ? "Rot, qualifiziert" : "Rot, Filter fehlt"}<br><small>${dt(e.closedAt)}</small>`
          : "—";
      },
    ],
  ];
  if(state.analysisEngine==='fan_master') {
    rows.push(['Haupt-Safety (blau)',tf=>`<span class="master-blue">${fmt(data.lanes[tf].mainSafety?.value)}</span>`]);
    rows.push(['SMA 50 / 200',tf=>`${fmt(data.lanes[tf].context?.sma50)} / ${fmt(data.lanes[tf].context?.sma200)}`]);
    extraRows.push(['Clean-Close / Quelle',tf=>fmt(data.lanes[tf].cleanCloseThreshold)]);
    extraRows.push(['Pine-Prüffenster¹',tf=>esc(data.lanes[tf].checkWindow?.status||'—')]);
    if(!data.researchSetup)extraRows.push(['Schlusskursmodell¹',tf=>{const m=data.lanes[tf].closeModel;return m?.quantity==null?'—':`${m.quantity} Stück · Stop ${fmt(m.stop)}<br><small>${fmt(m.capital)} Kapital · ${fmt(m.riskFraction*100)}% Risiko · ohne Kosten</small>`;}]);
  }
  if (data.researchSetup?.entryMode === "fan") {
    const setup = data.researchSetup;
    rows.push(["Signalstop (fixiert)", tf => tf === setup.sourceTimeframe ? fmt(setup.initialStop) : "—"]);
    rows.push(["Modell-Einstieg", tf => tf === setup.sourceTimeframe ? fmt(setup.entryPrice) : "—"]);
  }
  $("#line-table").innerHTML =
    `<table><thead><tr><th>${esc(data.symbol)}</th>${tfs.map((tf) => `<th>${tf} | Linie</th>`).join("")}</tr></thead><tbody>${rows.map(([title, fn]) => `<tr><th>${title}</th>${tfs.map((tf) => `<td>${fn(tf)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  if(extraRows.length)$('#line-table').innerHTML+=`<details class="master-extra"><summary>Master-Details</summary><table><tbody>${extraRows.map(([title,fn])=>`<tr><th>${title}</th>${tfs.map(tf=>`<td>${fn(tf)}</td>`).join('')}</tr>`).join('')}</tbody></table><small>¹ Prüffenster: Rückblick, kein neues Handelssignal. Größenmodell: hypothetischer Quellschluss ohne Kosten/Gaps.</small></details>`;
  $("#layer-controls").innerHTML = tfs
    .map(
      (tf) =>
        `<label><input type="checkbox" data-layer="${tf}" ${state.visible[tf] ? "checked" : ""}>${tf}</label>`,
    )
    .join("");
  document.querySelectorAll("[data-layer]").forEach(
    (el) =>
      (el.onchange = () => {
        state.visible[el.dataset.layer] = el.checked;
        automaticLines();
        chart.priceScale("right").applyOptions({ autoScale: true });
      }),
  );
}
function ohlc(bar) {
  $("#ohlc").textContent = bar
    ? `${dt(Number(bar.time))}   O ${fmt(bar.open)}   H ${fmt(bar.high)}   L ${fmt(bar.low)}   C ${fmt(bar.close)}`
    : "—";
}
chart.subscribeCrosshairMove((p) => {
  const b = p.seriesData.get(candles);
  ohlc(b?.open ? b : state.data?.bars.at(-1));
});
function setRange(days) {
  state.range = days;
  document
    .querySelectorAll("[data-range]")
    .forEach((b) =>
      b.setAttribute("aria-pressed", String(Number(b.dataset.range) === days)),
    );
  if (!state.data) return;
  const axis = state.data.axis,
    end = state.data.bars.at(-1).time;
  const first = days ? Math.max(axis[0], end - days * 86400) : axis[0];
  chart.timeScale().setVisibleLogicalRange({
    from: Math.max(0, RayGeometry.logicalAt(axis, first)),
    to: axis.length - 1 + 8,
  });
}
function zoomView(factor) {
  if (!state.data) return;
  const range = chart.timeScale().getVisibleLogicalRange();
  if (range)
    chart
      .timeScale()
      .setVisibleLogicalRange(
        RayGeometry.zoom(range, factor, state.data.axis.length),
      );
}
function latestView() {
  if (!state.data) return;
  const range = chart.timeScale().getVisibleLogicalRange();
  if (range)
    chart
      .timeScale()
      .setVisibleLogicalRange(
        RayGeometry.latest(range, state.data.axis.length),
      );
}
function resetView() {
  if (!state.data) return;
  setTool(false);
  chart.priceScale("right").applyOptions({ autoScale: true });
  setRange(state.timeframe === "1D" ? 90 : state.timeframe==='1W' ? 730 : 30);
  $("#auto-scale").setAttribute("aria-pressed", "true");
}
function view(bundle, tf) {
  const frozen = activeFrozen();
  const source = frozen ? frozen.payload : bundle;
  const selected = snapshotChart(bundle, tf);
  const data = {
    ...bundle,
    ...selected,
    timeframe: tf,
    lanes: structuredClone(source.lanes || {}),
  };
  data.axis = data.bars.map((bar) => bar.time);
  for (const lane of Object.values(data.lanes)) {
    for (const r of [
      lane.red,
      lane.green,
      lane.mainSafety,
      ...lane.outerRed,
      ...lane.outerGreen,
      lane.retest?.ray,
    ]) {
      if (r) {
        if (frozen)
          r.chartPositions = fixedChartPositions(r, frozen, tf);
        r.sourceValue = r.value;
        r.value = chartProjection(r, data.reference, data.axis);
      }
    }
    lane.sourceDistance = lane.distance;
    lane.distance = lane.green
      ? ((data.latest.close - lane.green.value) / data.latest.close) * 100
      : null;
  }
  return data;
}
function render(bundle, preserve = false) {
  const hadData = !!state.data;
  const symbolChanged = state.symbol !== bundle.symbol;
  const oldRange =
    preserve && hadData && !symbolChanged
      ? chart.timeScale().getVisibleLogicalRange()
      : null;
  const windowTimes = oldRange
    ? {
        from: RayGeometry.timeAt(state.data.axis, oldRange.from),
        to: RayGeometry.timeAt(state.data.axis, oldRange.to),
      }
    : null;
  state.symbol = bundle.symbol;
  state.data = view(bundle, state.timeframe);
  const data = state.data;
  const scope=drawingScope();
  if (state.measurementSymbol !== scope)
    restoreMeasurements(scope);
  rayLayer.cutoff=data.analysisCutoff;
  rayLayer.measurementEnd = data.reference;
  updateMeasurementSummary();
  rayLayer.timeframe = state.timeframe;
  if (symbolChanged || !hadData || state.drawingScope!==scope) rayLayer.load(storedRays(scope));
  rayLayer.bindAxes?.(bundle.drawingAxes || Object.fromEntries(Object.entries(bundle.charts).map(([tf,c])=>[tf,c.bars.map(b=>b.time)])));
  state.drawingScope=scope;
  $("#ticker").textContent = data.symbol;
  $("#company").textContent = data.company;
  const synthetic = data.dataKind === "synthetic";
  $("#synthetic-notice").hidden = !synthetic;
  $("#feed-label").textContent = synthetic ? "Testmodell" : (data.feed || "iex").toUpperCase();
  $("#interval-label").textContent = state.timeframe;
  history.replaceState(
    null,
    "",
    (randomMode ? '/zufall?' : '/?') +
      new URLSearchParams({
        symbol: data.symbol,
        tf: state.timeframe,
        ...(state.randomId ? {case:state.randomId} : {}),
        ...(state.asOf ? { asof: state.asOf } : {}),
        ...(state.datasetId ? { dataset: state.datasetId } : {}),
        ...(state.analysisEngine !== "legacy" ? {engine: state.analysisEngine} : {}),
        ...(state.fanCase ? {fan_job:state.fanJob, fan_case:state.fanCase} : {}),
        ...(state.researchJob
          ? {
              job: state.researchJob,
              trial: state.researchTrial,
              variant: state.researchVariant,
            }
          : {}),
      }),
  );
  const byTime = new Map(data.bars.map((b) => [b.time, b]));
  candles.setData(
    data.axis.map((time) => {
      const b = byTime.get(time);
      return b
        ? { time, open: b.open, high: b.high, low: b.low, close: b.close }
        : { time };
    }),
  );
  chart.timeScale().applyOptions({
    timeVisible: !['1D','1W'].includes(state.timeframe),
    tickMarkFormatter: (time, type) =>
      new Intl.DateTimeFormat("de-DE", {
        timeZone: "America/New_York",
        ...(type === LC.TickMarkType.Time
          ? { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }
          : { day: "2-digit", month: "2-digit" }),
      }).format(new Date(Number(time) * 1000)),
  });
  table();
  automaticLines();
  ohlc(data.bars.at(-1));
  if (windowTimes)
    chart.timeScale().setVisibleLogicalRange({
      from: RayGeometry.logicalAt(data.axis, windowTimes.from),
      to: RayGeometry.logicalAt(data.axis, windowTimes.to),
    });
  else setRange(state.timeframe === "1D" ? 90 : state.timeframe==='1W' ? 730 : 30);
  $("#axis-mode").value = state.axisMode;
  $("#fit-lines").checked = state.includeLines;
  $("#axis-note").textContent =
    state.axisMode === "trading"
      ? "Handelspausen ausgeblendet"
      : "Kalenderzeit";
  updateDrawingSummary();
  updateAnalysisControls();
  renderMeasurementList();
  const meta = data.sources[state.timeframe];
  $("#connection").textContent = synthetic ? "● Synthetischer Offline-Test" : Object.values(data.sources).some(
    (m) => m.warning,
  )
    ? "⚠ Gespeicherter Stand"
    : `● ${data.provider || "Alpaca"} · ${(data.feed || "iex").toUpperCase()}`;
  $("#source-status").textContent =
    `Letzte Kerze: ${dt(data.latest.time)} ET · ${data.bars.length.toLocaleString("de-DE")} Kerzen · ${meta.mode === "incremental" ? "Ergänzt" : meta.cached ? "Lokaler Cache" : "Geladen"}`;
  const warnings = Object.values(data.sources)
    .map((m) => m.warning)
    .filter(Boolean);
  if (warnings.length) showError(warnings[0]);
  updateRandomUI();
}
function showError(text) {
  $("#error").textContent = text;
  $("#error").hidden = false;
}
async function load(
  symbol,
  force = false,
  asOf = state.asOf,
  preserveView = false,
) {
  const previousContext = {
    datasetId: state.datasetId,
    fanJob: state.fanJob,
    fanCase: state.fanCase,
    researchJob: state.researchJob,
    researchTrial: state.researchTrial,
    researchVariant: state.researchVariant,
  };
  if (symbol !== state.symbol && !state.randomId) {
    state.datasetId = null;
    state.fanJob = null;
    state.fanCase = null;
    state.researchJob = null;
    state.researchTrial = null;
    state.researchVariant = null;
  }
  const id = ++state.request;
  setTool(false);
  $("#error").hidden = true;
  $("#loading").hidden = false;
  if (!state.stepping) $("#replay-status").textContent = "";
  updateStepButtons();
  $("#loading-text").textContent =
    `${symbol}: ${analysisLabel(asOf)} …`;
  $("#refresh-button").disabled = true;
  $("#freeze-button").disabled = true;
  $("#history-button").disabled = true;
  const started = performance.now(),
    analysis = state.analysisEnabled,
    key = bundleKey(symbol, asOf, analysis);
  try {
    const frozen = analysis ? await frozenForSymbol(symbol) : symbol === state.symbol ? state.frozen : null;
    let data = state.bundles.get(key);
    let fetched = false;
    if (
      !data ||
      force ||
      (!data.historical && Date.now() - Date.parse(data.generatedAt) >= 300000)
    ) {
      const params = new URLSearchParams({
        symbol,
        timeframe: state.timeframe,
        refresh: force ? "1" : "0",
        analysis: analysis ? "1" : "0",
      });
      if (asOf) params.set("asof", asOf);
      if (state.datasetId) params.set("dataset", state.datasetId);
      if (state.analysisEngine !== "legacy") params.set("engine", state.analysisEngine);
      if (state.fanCase) {
        params.set("fan_job", state.fanJob);
        params.set("fan_case", state.fanCase);
      }
      if (state.researchJob) {
        params.set("job", state.researchJob);
        params.set("trial", state.researchTrial);
        params.set("variant", state.researchVariant);
      }
      const response = await apiFetch(
        (state.fanCase ? "/api/fan/chart?" : state.randomId ? '/api/random/cases/'+encodeURIComponent(state.randomId)+'/chart?' : state.datasetId ? "/api/dataset-chart?" : "/api/chart?") + params,
      );
      data = await response.json();
      if (!response.ok) throw Error(data.error || "Datenabruf fehlgeschlagen.");
      fetched = true;
    }
    if (id !== state.request) return false;
    if (!analysis && fetched) {
      // A new manual import invalidates older overlays for the same view.
      state.bundles.delete(bundleKey(symbol, asOf, true));
      state.bundles.delete(bundleKey(symbol, isoCutoff(data), true));
    }
    if (analysis) assertFrozenCompatible(data, frozen);
    const preserve =
      symbol === state.symbol &&
      (preserveView || state.asOf === isoCutoff(data));
    state.frozen = frozen;
    state.asOf = isoCutoff(data);
    const asset = state.assetRows.find((a) => a.symbol === symbol);
    if (asset && data.dataKind !== "synthetic") data.company = asset.name;
    state.bundles.set(key, data);
    state.bundles.set(bundleKey(symbol, state.asOf), data);
    while (state.bundles.size > 32)
      state.bundles.delete(state.bundles.keys().next().value);
    render(data, preserve);
    $("#connection").title =
      `Ladezeit: ${((performance.now() - started) / 1000).toFixed(2)} s`;
    return true;
  } catch (e) {
    if (id !== state.request) return false;
    Object.assign(state, previousContext);
    showError(e.message);
    if (!state.data) $("#company").textContent = `${symbol} · Keine Kursdaten`;
    $("#connection").textContent = state.data
      ? "⚠ Bisherige Chartansicht bleibt sichtbar"
      : "Keine Kursdaten";
    return false;
  } finally {
    if (id === state.request) {
      $("#loading").hidden = true;
      $("#refresh-button").disabled = false;
      $("#freeze-button").disabled = !state.data || !!state.researchJob;
      $("#history-button").disabled = false;
      updateStepButtons();
      updateToriControls();
    }
  }
}
async function searchAssets(append = false) {
  const id = ++state.assetRequest;
  if (!append) {
    state.assetOffset = 0;
    state.assetRows = [];
    $("#asset-results").innerHTML = "";
  }
  $("#asset-count").textContent = "Verzeichnis wird durchsucht …";
  $("#more-assets").hidden = true;
  const params = new URLSearchParams({
    q: $("#asset-search").value,
    exchange: $("#exchange-filter").value,
    offset: state.assetOffset,
  });
  if (state.favoriteOnly) params.set("symbols", state.favorites.join(","));
  try {
    const r = await apiFetch("/api/assets?" + params);
    const data = await r.json();
    if (!r.ok) throw Error(data.error);
    if (id !== state.assetRequest) return;
    if ($("#exchange-filter").options.length === 1)
      for (const exchange of data.exchanges) {
        const option = new Option(exchange, exchange);
        $("#exchange-filter").add(option);
      }
    state.assetRows.push(...data.items);
    $("#asset-count").textContent =
      `${data.total.toLocaleString("de-DE")} Treffer · ${data.catalogTotal.toLocaleString("de-DE")} US-Börsentitel im Verzeichnis${data.stale ? " · gespeicherter Verzeichnisstand" : ""}`;
    renderAssets();
    $("#more-assets").hidden = state.assetRows.length >= data.total;
  } catch (e) {
    if (id !== state.assetRequest) return;
    $("#asset-count").textContent = e.message;
    $("#asset-results").innerHTML =
      '<button id="retry-assets">Erneut versuchen</button>';
    $("#retry-assets").onclick = () => searchAssets();
  }
}
function renderAssets() {
  const container = $("#asset-results");
  const scroll = container.scrollTop;
  container.innerHTML = state.assetRows.length
    ? state.assetRows
        .map(
          (a) =>
            `<div class="asset-row"><button class="asset-pick" data-symbol="${esc(a.symbol)}" aria-label="${esc(a.name)} (${esc(a.symbol)}) laden"><span><b>${esc(a.symbol)}</b><small>${esc(a.name)}</small></span><span class="asset-exchange">${esc(a.exchange)}</span></button><button class="star-button ${state.favorites.includes(a.symbol) ? "saved" : ""}" data-star="${esc(a.symbol)}" aria-label="${esc(a.symbol)} ${state.favorites.includes(a.symbol) ? "aus Favoriten entfernen" : "zu Favoriten hinzufügen"}">${state.favorites.includes(a.symbol) ? "★" : "☆"}</button></div>`,
        )
        .join("")
    : '<div class="empty-results">Keine passenden Werte.<br>Suche oder Börsenfilter ändern.</div>';
  container.scrollTop = scroll;
  container.querySelectorAll("[data-symbol]").forEach(
    (b) =>
      (b.onclick = () => {
        $("#asset-dialog").close();
        load(b.dataset.symbol);
      }),
  );
  container.querySelectorAll("[data-star]").forEach(
    (b) =>
      (b.onclick = () => {
        const s = b.dataset.star;
        state.favorites = state.favorites.includes(s)
          ? state.favorites.filter((x) => x !== s)
          : [...state.favorites, s];
        write("tori-favorites", state.favorites);
        if (state.favoriteOnly) searchAssets();
        else renderAssets();
      }),
  );
}
function details() {
  if (!hasToriAnalysis()) return;
  const data = state.data;
  $("#detail-symbol").textContent = `${data.symbol} · ${data.company}`;
  $("#details-content").innerHTML =
    lanes()
      .map((tf) => {
        const l = data.lanes[tf],
          meta = (state.frozen?.payload || data).sources[tf];
        return `<section><h2>${tf} · ${esc(l.status)}</h2>${["red", "green"]
          .map((k) => {
            const r = l[k];
            return r
              ? `<p class="${k}"><b>${k === "red" ? "Rot" : "Grün"} · ${r.qualified ? "qualifiziert" : "vorläufig"}</b><br>A: ${dtLong(r.a_time)} ET / ${fmt(r.a_price)}<br>B: ${dtLong(r.b_time)} ET / ${fmt(r.b_price)}<br>Quellwert: ${fmt(r.sourceValue)} · Chart: ${fmt(r.value)}<br>${r.contacts} Kontakte / ${fmt(r.span_days)} Tage</p>`
              : "";
          })
          .join(
            "",
          )}<p>${meta.count} Kerzen · Quellschluss ${dt(l.sourceClose)} ET<br>Abruf ${dt(new Date(meta.fetchedAt).getTime() / 1000)} ET · ${meta.mode || "Cache"} · ${meta.pages} API-Seiten beim letzten Abruf<br>Rückblick ${l.lookbackDays} Tage · ${l.selection === "quality" ? "Qualität zuerst" : "Innerste Linie"}</p></section>`;
      })
      .join("") +
    `<section><h2>Eigene Rays · ${rayLayer.items.length}</h2>${rayLayer.items.map((r) => `<p data-ray-id="${esc(r.id)}"><b>${esc(r.timeframe)}</b><br><code>A: ${r.a.time} / ${r.a.price.toFixed(8)}<br>B: ${r.b.time} / ${r.b.price.toFixed(8)}</code></p>`).join("")}</section>` +
    "<p>¹ Abstand: prozentualer Abstand vom letzten Chartschluss zur grünen Chartprojektion; kein Gesamtrisiko. Qualifiziert ab 3 Kontakten über mindestens 7 Tage. Kontakt-Toleranz 0,01 USD. Brüche werden nur im begrenzten Suchabschnitt untersucht.</p>";
  $("#details-dialog").showModal();
}
$("#symbol-button").onclick = () => {
  $("#asset-dialog").showModal();
  $("#asset-search").focus();
  searchAssets();
};
let searchTimer;
$("#asset-search").oninput = () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => searchAssets(), 160);
};
$("#exchange-filter").onchange = () => searchAssets();
for (const [id, favorite] of [
  ["all-assets", false],
  ["favorite-assets", true],
])
  $("#" + id).onclick = () => {
    state.favoriteOnly = favorite;
    $("#all-assets").setAttribute("aria-pressed", String(!favorite));
    $("#favorite-assets").setAttribute("aria-pressed", String(favorite));
    searchAssets();
  };
$("#more-assets").onclick = () => {
  state.assetOffset = state.assetRows.length;
  searchAssets(true);
};
$("#asset-search").onkeydown = async (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    clearTimeout(searchTimer);
    await searchAssets();
    $("#asset-results [data-symbol]")?.click();
  }
};
document
  .querySelectorAll("[data-close]")
  .forEach((b) => (b.onclick = () => $("#" + b.dataset.close).close()));
document.querySelectorAll("dialog").forEach((d) =>
  d.addEventListener("click", (e) => {
    if (e.target === d) {
      const r = d.getBoundingClientRect();
      if (
        e.clientX < r.left ||
        e.clientX > r.right ||
        e.clientY < r.top ||
        e.clientY > r.bottom
      )
        d.close();
    }
  }),
);
$("#theme-button").onclick = () => {
  state.theme = state.theme === "dark" ? "light" : "dark";
  write("tori-theme", state.theme);
  theme();
};
$("#info-panel").hidden = true;
$("#info-button").setAttribute("aria-pressed", String(state.info));
$("#info-button").onclick = () => {
  if (!hasToriAnalysis()) return;
  state.info = !state.info;
  write("tori-info", state.info);
  updateToriControls();
  $("#info-button").setAttribute("aria-pressed", String(state.info));
  rayLayer.update();
};
$("#details-button").onclick = details;
$("#refresh-button").onclick = () => load(state.symbol, true);
$("#outer-lines").onchange = automaticLines;
$("#ray-tool").onclick = () => {
  if (state.data) setTool(!rayLayer.active);
};
$('#line-extension').onchange=()=>{
  setTool(false);
  rayLayer.changeExtension($('#line-extension').value);
  updateDrawingSummary();
};
$('#line-color').value=RayGeometry.color(read('tori-line-color','#3988ee'));
rayLayer.color=$('#line-color').value;
$('#line-color').onchange=()=>{
  setTool(false);
  const color=RayGeometry.color($('#line-color').value);
  write('tori-line-color',color);
  rayLayer.changeColor(color);
  updateDrawingSummary();
};
$("#cursor-tool").onclick = () => setTool(false);
$("#measure-tool").onclick = () => {
  if (state.data) setTool(rayLayer.measureActive ? false : "measure");
};
$("#delete-tool").onclick = deleteDrawing;
$("#undo-tool").onclick = undoDrawing;
document.querySelectorAll("[data-tf]").forEach(
  (b) =>
    (b.onclick = () => {
      if (state.timeframe === b.dataset.tf) return;
      const bundle = currentBundle();
      if(!bundle?.charts[b.dataset.tf] || state.frozen && !state.frozen.payload.charts[b.dataset.tf]) {
        showError('Dieses Intervall fehlt im angezeigten Bestand oder alten fixierten Stand. Gegebenenfalls Fixierung lösen und Daten neu laden.');return;
      }
      state.timeframe = b.dataset.tf;
      state.range = state.timeframe === "1D" ? 90 : state.timeframe==='1W' ? 730 : 30;
      document
        .querySelectorAll("[data-tf]")
        .forEach((btn) => btn.setAttribute("aria-pressed", String(btn === b)));
      setTool(false);
      rayLayer.timeframe = state.timeframe;
      if (bundle) render(bundle, true);
    }),
);
document
  .querySelectorAll("[data-range]")
  .forEach((b) => (b.onclick = () => setRange(Number(b.dataset.range))));
$("#zoom-in").onclick = () => zoomView(0.75);
$("#zoom-out").onclick = () => zoomView(1 / 0.75);
$("#latest-view").onclick = latestView;
$("#reset-view").onclick = resetView;
$("#auto-scale").onclick = () => {
  const enabled = !chart.priceScale("right").options().autoScale;
  chart.priceScale("right").applyOptions({ autoScale: enabled });
  $("#auto-scale").setAttribute("aria-pressed", String(enabled));
};
$("#chart").addEventListener("pointerup", () =>
  requestAnimationFrame(() => {
    $("#auto-scale").setAttribute(
      "aria-pressed",
      String(chart.priceScale("right").options().autoScale),
    );
  }),
);
$("#axis-mode").value = state.axisMode;

$("#fit-lines").onchange = () => {
  state.includeLines = $("#fit-lines").checked;
  write("tori-fit-lines", state.includeLines);
  chart.priceScale("right").applyOptions({ autoScale: true });
  $("#auto-scale").setAttribute("aria-pressed", "true");
};
document.addEventListener("keydown", (e) => {
  if (
    document.querySelector("dialog[open]") ||
    /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)
  )
    return;
  if (!e.ctrlKey && !e.metaKey && !e.altKey) {
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      stepAnalysis(e.key === "ArrowLeft" ? "back" : "next");
    }
    if (e.key === "+" || e.key === "=") {
      e.preventDefault();
      zoomView(0.75);
    }
    if (e.key === "-") {
      e.preventDefault();
      zoomView(1 / 0.75);
    }
    if (e.key === "0") {
      e.preventDefault();
      resetView();
    }
    if (e.key === "Home") {
      e.preventDefault();
      latestView();
    }
  }
  if (e.key === "Escape") {
    setTool(false);
    rayLayer.selected = null;
    rayLayer.measurementSelected = false;
    rayLayer.update();
    updateDrawingSummary();
  }
  if (e.key.toLowerCase() === "r" && !e.ctrlKey && !e.metaKey && state.data)
    setTool(true);
  if (e.key.toLowerCase() === "v") setTool(false);
  if (e.key.toLowerCase() === "m" && !e.ctrlKey && !e.metaKey && state.data)
    setTool("measure");
  if (e.key === "Delete" || e.key === "Backspace") {
    e.preventDefault();
    deleteDrawing();
  }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
    e.preventDefault();
    undoDrawing();
  }
});
document
  .querySelectorAll("[data-tf]")
  .forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.tf === state.timeframe)),
  );
$("#ticker").textContent = state.symbol;
theme();
updateDrawingSummary();
setupAnalysisUI();
$("#tori-analysis").onclick = toggleToriAnalysis;
$("#analysis-engine").value = state.analysisEngine;
$("#analysis-engine").onchange = async () => {
  if (state.stepping || state.freezing || !$("#loading").hidden) {
    $("#analysis-engine").value = state.analysisEngine;
    return;
  }
  const before = state.analysisEngine;
  if (state.fanCase) {
    $("#analysis-engine").value = before;
    showError("Dieser Forschungsfall ist an seine ursprüngliche Geometrie gebunden. Für einen Vergleich den normalen Chart öffnen.");
    return;
  }
  state.analysisEngine = $("#analysis-engine").value;
  state.frozen = null;
  if (state.analysisEnabled && !await load(state.symbol, false, state.asOf, true)) {
    state.analysisEngine = before;
    $("#analysis-engine").value = before;
  }
};
setupMeasurements();
function updateRandomUI(){
  if(!randomMode)return;
  $('#random-controls').hidden=false;$('#random-note').hidden=false;
  $('#random-new').disabled=state.randomPicking || state.stepping || state.freezing || !$('#loading').hidden;
  $('#random-reset').disabled=!state.data || state.randomPicking || state.stepping || state.freezing || !$('#loading').hidden;
  $('#symbol-button').disabled=true;
  $('#random-note').textContent=state.randomStartAt
    ? 'Zufallsfall · Start '+dtLong(state.randomStartAt)+' ET · Eigene Zeichnungen nur für diesen Fall'
    : 'Zufällige Aktie und Zeitpunkt aus lokal gespeicherten Daten · keine Signalauswahl';
}
async function pickRandom(resume=false){
  if(state.randomPicking || state.stepping || state.freezing)return;
  state.randomPicking=true;updateRandomUI();$('#error').hidden=true;
  const before={randomId:state.randomId,datasetId:state.datasetId,randomStartAt:state.randomStartAt,asOf:state.asOf,
    analysisEnabled:state.analysisEnabled,frozen:state.frozen,researchJob:state.researchJob,researchTrial:state.researchTrial,researchVariant:state.researchVariant};
  let applied=false;
  try{
    const response=await apiFetch(resume && state.randomId ? '/api/random/cases/'+encodeURIComponent(state.randomId) : '/api/random/cases',
      resume && state.randomId ? undefined : {method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    const item=await response.json();if(!response.ok)throw Error(item.error || 'Zufallsauswahl fehlgeschlagen.');
    state.randomId=item.id;state.datasetId=item.datasetId;state.randomStartAt=item.startAt;
    state.researchJob=state.researchTrial=state.researchVariant=null;state.frozen=null;state.analysisEnabled=false;
    const asOf=resume && query.get('asof') ? query.get('asof') : new Date(item.startAt*1000).toISOString();
    applied=await load(item.symbol,false,asOf);
  }catch(e){showError(e.message);}
  finally{if(!applied){Object.assign(state,before);updateAnalysisControls();}state.randomPicking=false;updateRandomUI();}
}
if(randomMode){
  document.title='Tori · Zufall';
  document.querySelector('.app-navigation a[href="/"]')?.setAttribute('aria-current','false');
  document.querySelector('.app-navigation a[href="/zufall"]')?.setAttribute('aria-current','page');
  $('#random-new').onclick=()=>pickRandom();
  $('#random-reset').onclick=()=>{if(state.randomStartAt && !state.stepping)load(state.symbol,false,new Date(state.randomStartAt*1000).toISOString());};
  $('#history-button').title='Datum innerhalb dieses Zufallsfalls wählen';
  $('#live-analysis').hidden=true;
  $('#symbol-button').onclick=()=>{};
  pickRandom(!!state.randomId);
}else load(state.symbol);
