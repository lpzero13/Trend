/* Pure coordinate math: straight rays use logical candle positions. */
const axisSteps = new WeakMap();
const RayGeometry = {
  validBasis(basis) {
    return basis?.version === 'drawing-axis-2' && Array.isArray(basis.axis) && basis.axis.length >= 2 &&
      basis.axis.every((t,i,a)=>Number.isFinite(t) && (!i || t>a[i-1]));
  },
  capture(axis) { return {version:'drawing-axis-2',axis:[...axis]}; },
  color(value) { return /^#[0-9a-f]{6}$/i.test(value || '') ? value.toLowerCase() : '#3988ee'; },
  pixelAt(scale, logical) {
    if (!Number.isFinite(logical)) return null;
    // Bundled Lightweight Charts returns 0 for fractional logicalToCoordinate
    // arguments. Interpolate between supported integer candle coordinates.
    const i=Math.floor(logical),a=scale.logicalToCoordinate(i);
    if(logical===i || a===null)return a;
    const b=scale.logicalToCoordinate(i+1);
    return b===null ? null : a+(b-a)*(logical-i);
  },
  logicalAtPixel(scale,pixel) {
    const guess=scale.coordinateToLogical(pixel);
    if(guess===null)return null;
    const i=Math.floor(guess),a=scale.logicalToCoordinate(i),b=scale.logicalToCoordinate(i+1);
    return a===null || b===null || a===b ? guess : i+(pixel-a)/(b-a);
  },
  bounds(extension, a, b, from, to) {
    const left = Math.min(a,b), right = Math.max(a,b);
    const start = ['left','both','horizontal'].includes(extension) ? from : Math.max(from,left);
    const end = ['right','both','horizontal',undefined].includes(extension) ? to : Math.min(to,right);
    return start < end ? {start,end} : null;
  },
  step(axis) {
    if (axisSteps.has(axis)) return axisSteps.get(axis);
    const counts = new Map();
    for (let i = 1; i < axis.length; i++) {
      const step = axis[i] - axis[i - 1];
      if (step > 0) counts.set(step, (counts.get(step) || 0) + 1);
    }
    const step =
      [...counts].sort((a, b) => b[1] - a[1] || a[0] - b[0])[0]?.[0] || 1;
    axisSteps.set(axis, step);
    return step;
  },
  logicalAt(axis, time) {
    if (axis.length < 2) return null;
    if (time < axis[0]) return (time - axis[0]) / this.step(axis);
    if (time > axis.at(-1))
      return axis.length - 1 + (time - axis.at(-1)) / this.step(axis);
    let lo = 0,
      hi = axis.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (axis[mid] <= time) lo = mid;
      else hi = mid;
    }
    if (time < axis[0]) {
      lo = 0;
      hi = 1;
    } else if (time > axis.at(-1)) {
      lo = axis.length - 2;
      hi = axis.length - 1;
    }
    return lo + (time - axis[lo]) / (axis[hi] - axis[lo]);
  },
  timeAt(axis, logical) {
    if (axis.length < 2) return null;
    if (logical < 0) return axis[0] + logical * this.step(axis);
    if (logical > axis.length - 1)
      return axis.at(-1) + (logical - axis.length + 1) * this.step(axis);
    const i = Math.max(0, Math.min(axis.length - 2, Math.floor(logical)));
    return axis[i] + (logical - i) * (axis[i + 1] - axis[i]);
  },
  candleValue(axis, ray, time) {
    return this.valueAtLogical(axis,ray,this.logicalAt(axis,time));
  },
  valueAtLogical(axis,ray,logical) {
    // The two saved time/price anchors are authoritative. Reproject them into
    // the displayed interval and join them with one straight line. Replaying
    // the original interval's per-candle prices here would create a stairway.
    // Legacy basis metadata is retained for compatibility, never resampled.
    const a = ray.a.logical ?? this.logicalAt(axis, ray.a.time),
      b = ray.b.logical ?? this.logicalAt(axis, ray.b.time);
    if (a === null || b === null || Math.abs(b - a) < 1e-10) return null;
    return (
      ray.a.price +
      ((ray.b.price - ray.a.price) * (logical - a)) / (b - a)
    );
  },
  drawingPoints(axis, ray, start, end) {
    return [start,end];
  },
  measure(axis, a, b) {
    return {
      delta: b.price - a.price,
      percent: ((b.price - a.price) / a.price) * 100,
      steps: Math.round(
        Math.abs(this.logicalAt(axis, b.time) - this.logicalAt(axis, a.time)),
      ),
    };
  },
  zoom(range, factor, count) {
    const center = (range.from + range.to) / 2;
    const width = Math.max(
      6,
      Math.min(count * 1.3, (range.to - range.from) * factor),
    );
    if (range.from <= count - 1 && range.to >= count - 1) {
      return { from: range.to - width, to: range.to };
    }
    return { from: center - width / 2, to: center + width / 2 };
  },
  latest(range, count, padding = 8) {
    const width = range.to - range.from;
    return { from: count - 1 + padding - width, to: count - 1 + padding };
  },
};

/* Timestamp/price based ray primitive, independent from automatically calculated series. */
class RayLayer {
  constructor(chart, series, axis, onChange) {
    Object.assign(this, {
      chart,
      series,
      axis,
      onChange,
      items: [],
      automatic: [],
      wedge: null,
      tradeZones: null,
      selected: null,
      draft: null,
      undoStack: [],
      active: false,
      measureActive: false,
      measurement: null,
      measureDraft: null,
      drag: null,
      magnet: false,
      bars: () => [],
      horizontalActive: false,
      rectActive: false,
      longActive: false,
      hoverPrice: null,
    });
    this.renderer = {
      draw: (target) =>
        target.useMediaCoordinateSpace((scope) =>
          this.paint(scope.context, scope.mediaSize),
        ),
    };
    this.view = { renderer: () => this.renderer, zOrder: () => "top" };
    series.attachPrimitive(this);
    const host = document.querySelector("#chart");
    host.addEventListener("pointerdown", (e) => this.down(e), true);
    host.addEventListener(
      "mousedown",
      (e) => {
        if (this.active || this.measureActive || this.horizontalActive || this.rectActive || this.longActive || this.drag) {
          e.preventDefault();
          e.stopImmediatePropagation();
        }
      },
      true,
    );
    window.addEventListener("pointermove", (e) => this.move(e), true);
    window.addEventListener("pointerup", (e) => this.up(e), true);
    this.host = host;
  }
  attached({ requestUpdate }) {
    this.requestUpdate = requestUpdate;
  }
  paneViews() {
    return [this.view];
  }
  updateAllViews() {}
  update() {
    this.requestUpdate?.();
  }
  logicalAt(time) {
    return RayGeometry.logicalAt(this.axis(), time);
  }
  timeAt(logical) {
    return RayGeometry.timeAt(this.axis(), logical);
  }
  axisFor(ray) {
    return ray?.basis ? this.drawingAxes?.[this.timeframe] || this.axis() : this.axis();
  }
  point(anchor, axis=this.axis()) {
    return {
      x: RayGeometry.pixelAt(this.chart.timeScale(),anchor.logical ?? RayGeometry.logicalAt(axis,anchor.time)),
      y: this.series.priceToCoordinate(anchor.price),
    };
  }
  anchor(point) {
    const logical = RayGeometry.logicalAtPixel(this.chart.timeScale(),point.x),
      price = this.series.coordinateToPrice(point.y);
    if (
      logical === null ||
      price === null ||
      !Number.isFinite(price) ||
      price <= 0
    )
      return null;
    const axis=this.measureActive ? this.axis() : this.drawingAxes?.[this.timeframe] || this.axis();
    if (this.magnet && (!this.drag || this.drag.key !== "line")) {
      const bars = typeof this.bars === "function" ? this.bars() : [];
      const idx = Math.round(logical);
      if (bars && idx >= 0 && idx < bars.length) {
        const bar = bars[idx];
        const cands = [bar.high, bar.low, bar.close, bar.open].filter((v) => Number.isFinite(v) && v > 0);
        let best = null;
        let bestDist = 28;
        for (const v of cands) {
          const y = this.series.priceToCoordinate(v);
          if (y !== null && Number.isFinite(y)) {
            const d = Math.abs(point.y - y);
            if (d < bestDist) {
              bestDist = d;
              best = v;
            }
          }
        }
        if (best !== null) return { time: bar.time, price: best };
      }
    }
    return { time: RayGeometry.timeAt(axis,logical), price };
  }
  coords(event) {
    // Pane coordinates can differ from the host after borders, scaling or layouts.
    const canvas=this.host.querySelector?.('canvas');
    const r = (canvas || this.host).getBoundingClientRect();
    const width=this.chart.timeScale().width(),height=this.chart.panes()[0].getHeight();
    return { x:(event.clientX-r.left)*(canvas && r.width?width/r.width:1),
             y:(event.clientY-r.top)*(canvas && r.height?height/r.height:1) };
  }
  inside(p) {
    const pane = this.chart.panes()[0];
    return (
      p.x >= 0 &&
      p.x < this.chart.timeScale().width() &&
      p.y >= 0 &&
      p.y < pane.getHeight()
    );
  }
  line(ray) {
    const axis=this.axisFor(ray),a = this.point(ray.a,axis),
      b = this.point(ray.b,axis);
    return [a, b];
  }
  hit(p) {
    for (const ray of [...this.items].reverse()) {
      if (!this.visible(ray)) continue;
      if (ray.kind === "rect") {
        const [a, b] = this.line(ray);
        for (const key of ["a", "b"]) {
          const q = key === "a" ? a : b;
          if (q.x !== null && q.y !== null && Math.hypot(p.x - q.x, p.y - q.y) < 11)
            return { ray, key };
        }
        if ([a.x, a.y, b.x, b.y].every(Number.isFinite)) {
          const left = Math.min(a.x, b.x), right = Math.max(a.x, b.x);
          const top = Math.min(a.y, b.y), bottom = Math.max(a.y, b.y);
          if (p.x >= left - 6 && p.x <= right + 6 && p.y >= top - 6 && p.y <= bottom + 6)
            return { ray, key: "line" };
        }
        continue;
      }
      if (ray.kind === "longbox") {
        const axis = this.axisFor(ray);
        const pa = this.point(ray.a, axis);
        const pb = this.point(ray.b, axis);
        const tPrice = Number.isFinite(ray.targetPrice)
          ? ray.targetPrice
          : ray.a.price + 2 * Math.max(0.01, ray.a.price - ray.b.price);
        const pt = this.point({ time: ray.b.time, price: tPrice }, axis);
        if (pt.x !== null && pt.y !== null && Math.hypot(p.x - pt.x, p.y - pt.y) < 12)
          return { ray, key: "target" };
        if (pb.x !== null && pb.y !== null && Math.hypot(p.x - pb.x, p.y - pb.y) < 12)
          return { ray, key: "b" };
        if (pa.x !== null && pa.y !== null && Math.hypot(p.x - pa.x, p.y - pa.y) < 12)
          return { ray, key: "a" };
        if ([pa.x, pa.y, pb.x, pb.y, pt.y].every(Number.isFinite)) {
          const left = Math.min(pa.x, pb.x), right = Math.max(pa.x, pb.x);
          const top = Math.min(pt.y, pa.y, pb.y), bottom = Math.max(pt.y, pa.y, pb.y);
          if (p.x >= left - 6 && p.x <= right + 6 && p.y >= top - 6 && p.y <= bottom + 6)
            return { ray, key: "line" };
        }
        continue;
      }
      const [a, b] = this.line(ray);
      for (const key of ["a", "b"]) {
        const q = key === "a" ? a : b;
        if (q.x === null || q.y === null) continue;
        if (Math.hypot(p.x - q.x, p.y - q.y) < 10) return { ray, key };
      }
      const logical = RayGeometry.logicalAtPixel(this.chart.timeScale(),p.x);
      const axis=this.axisFor(ray),time = RayGeometry.timeAt(axis,logical);
      const y = this.series.priceToCoordinate(
        RayGeometry.candleValue(axis, ray, time),
      );
      const bounds=RayGeometry.bounds(ray.extend, RayGeometry.logicalAt(axis,ray.a.time),RayGeometry.logicalAt(axis,ray.b.time),logical-.01,logical+.01);
      if (bounds && y !== null && Math.abs(p.y - y) < 8)
        return { ray, key: "line" };
    }
    return null;
  }
  visible(ray) {
    return !Number.isFinite(this.cutoff) || !Number.isFinite(ray.observedAt) || ray.observedAt <= this.cutoff;
  }
  changeExtension(extension) {
    if (!['right','left','both','segment','horizontal'].includes(extension)) return;
    this.extension=extension;
    const ray=this.items.find(r=>r.id===this.selected);
    if (ray) {
      this.remember();ray.extend=extension;
      ray.observedAt=this.cutoff;
      if (extension==='horizontal') ray.b.price=ray.a.price;
      this.commit();
    }
  }
  snapshot() {
    return JSON.stringify(this.items);
  }
  remember(action = this.snapshot()) {
    this.undoStack.push(action);
    if (this.undoStack.length > 40) this.undoStack.shift();
  }
  commit() {
    this.onChange(this.items);
    this.update();
  }
  setMode(active) {
    this.active = active === true;
    this.measureActive = active === "measure";
    this.horizontalActive = active === "horizontal";
    this.rectActive = active === "rect";
    this.longActive = active === "longbox";
    this.hoverPrice = null;
    this.draft = null;
    this.measureDraft = null;
    this.onMeasure?.();
    this.drag = null;
    this.chart.applyOptions({
      handleScroll: {
        pressedMouseMove: !active,
        horzTouchDrag: !active,
        vertTouchDrag: !active,
      },
    });
    this.host.style.cursor = active ? "crosshair" : "";
    this.update();
  }
  load(items) {
    this.items = items;
    this.selected = null;
    this.draft = null;
    this.undoStack = [];
    this.update();
  }
  bindAxes(axes) {
    this.drawingAxes=axes;
    let changed=false;
    for(const ray of this.items) {
      if (RayGeometry.validBasis(ray.basis)) continue;
      const axis=axes[ray.timeframe];
      // Never reinterpret an old 1D drawing using the currently selected 1h axis.
      if (!axis || axis.length<2) continue;
      ray.basis=RayGeometry.capture(axis);changed=true;
    }
    if(changed) this.commit();
  }
  changeColor(value) {
    const color=RayGeometry.color(value);
    this.color=color;
    if (this.draft) this.draft.color = color;
    const ray=this.items.find(r=>r.id===this.selected);
    if(ray && ray.color!==color) {
      this.remember();ray.color=color;this.commit();
    } else this.update();
  }
  remove() {
    if (!this.selected) return;
    this.remember();
    this.items = this.items.filter((r) => r.id !== this.selected);
    this.selected = null;
    this.commit();
  }
  undo() {
    const prev = this.undoStack.at(-1);
    if (typeof prev === "function") {
      if (prev() === false) return;
      this.undoStack.pop();
      this.onSelection?.();
    } else if (prev) {
      this.undoStack.pop();
      this.items = JSON.parse(prev);
      this.selected = null;
      this.measurementSelected = false;
      this.commit();
    }
  }
  hitMeasurement(p) {
    const m = this.measurement;
    if (!m || m.a.time > this.measurementEnd || m.b.time > this.measurementEnd)
      return false;
    const a = this.point(m.a),
      b = this.point(m.b);
    if (![a.x, a.y, b.x, b.y].every(Number.isFinite)) return false;
    const left = Math.min(a.x, b.x),
      right = Math.max(a.x, b.x),
      top = Math.min(a.y, b.y),
      bottom = Math.max(a.y, b.y);
    return (
      p.x >= left - 8 &&
      p.x <= right + 8 &&
      p.y >= top - 8 &&
      p.y <= bottom + 8 &&
      (Math.min(Math.abs(p.x - left), Math.abs(p.x - right)) <= 8 ||
        Math.min(Math.abs(p.y - top), Math.abs(p.y - bottom)) <= 8)
    );
  }
  down(event) {
    if (event.button !== 0) return;
    const p = this.coords(event);
    if (!this.inside(p)) return;
    const anchor = this.anchor(p);
    if (!anchor) return;
    if (this.measureActive) {
      event.preventDefault();
      event.stopImmediatePropagation();
      const axis = this.axis(),
        i = Math.max(
          0,
          Math.min(
            axis.length - 1,
            Math.round(RayGeometry.logicalAtPixel(this.chart.timeScale(),p.x)),
          ),
        );
      anchor.time = axis[i];
      if (!this.measureDraft) {
        this.selected = null;
        this.measurementSelected = false;
        this.measureDraft = { a: anchor, b: anchor };
      } else {
        this.measurement = { a: this.measureDraft.a, b: anchor };
        this.measureDraft = null;
        this.onMeasureCommit?.(this.measurement);
        this.onDone?.();
      }
      this.onMeasure?.();
      this.update();
      return;
    }
    if (this.rectActive) {
      event.preventDefault();
      event.stopImmediatePropagation();
      const axis = this.drawingAxes?.[this.timeframe] || this.axis();
      const step = axis.length >= 2 ? Math.max(60, Math.round(axis[axis.length - 1] - axis[axis.length - 2])) : 3600;
      if (!this.draft) {
        this.draft = {
          kind: "rect",
          a: anchor,
          b: { time: anchor.time + step, price: anchor.price },
          color: RayGeometry.color(this.color),
          basis: RayGeometry.capture(axis),
        };
        this.onHint?.("Zweite Ecke setzen · Escape zum Abbrechen");
      } else {
        this.remember();
        let a = this.draft.a, b = anchor;
        if (Math.abs(b.time - a.time) < 1) b = { time: a.time + step * 4, price: b.price };
        if (b.time < a.time) { const tmp = a; a = b; b = tmp; }
        const rect = {
          id: crypto.randomUUID(),
          kind: "rect",
          a,
          b,
          timeframe: this.timeframe,
          basis: RayGeometry.capture(axis),
          color: RayGeometry.color(this.color),
          observedAt: this.cutoff,
        };
        this.items.push(rect);
        this.selected = rect.id;
        this.measurementSelected = false;
        this.draft = null;
        this.commit();
        this.onSelection?.();
        this.onDone?.();
      }
      this.update();
      return;
    }
    if (this.longActive) {
      event.preventDefault();
      event.stopImmediatePropagation();
      const axis = this.drawingAxes?.[this.timeframe] || this.axis();
      const step = axis.length >= 2 ? Math.max(60, Math.round(axis[axis.length - 1] - axis[axis.length - 2])) : 3600;
      if (!this.draft) {
        const stopInit = Math.max(0.01, anchor.price * 0.97);
        this.draft = {
          kind: "longbox",
          a: anchor,
          b: { time: anchor.time + step * 14, price: stopInit },
          targetPrice: anchor.price + 2 * (anchor.price - stopInit),
          color: "#26a69a",
          basis: RayGeometry.capture(axis),
        };
        this.onHint?.("Stop-Loss-Niveau anklicken · Escape zum Abbrechen");
      } else {
        this.remember();
        let entryPrice = this.draft.a.price;
        let stopPrice = anchor.price;
        if (stopPrice >= entryPrice) {
          if (Math.abs(stopPrice - entryPrice) < 0.0001) {
            stopPrice = Math.max(0.01, entryPrice * 0.97);
          } else {
            const tmp = entryPrice; entryPrice = stopPrice; stopPrice = tmp;
          }
        }
        const risk = Math.max(0.01, entryPrice - stopPrice);
        const endTime = Math.max(anchor.time, this.draft.a.time + step * 12);
        const box = {
          id: crypto.randomUUID(),
          kind: "longbox",
          a: { time: this.draft.a.time, price: entryPrice },
          b: { time: endTime, price: stopPrice },
          targetPrice: entryPrice + 2 * risk,
          timeframe: this.timeframe,
          basis: RayGeometry.capture(axis),
          color: "#26a69a",
          observedAt: this.cutoff,
        };
        this.items.push(box);
        this.selected = box.id;
        this.measurementSelected = false;
        this.draft = null;
        this.commit();
        this.onSelection?.();
        this.onDone?.();
      }
      this.update();
      return;
    }
    if (this.horizontalActive) {
      event.preventDefault();
      event.stopImmediatePropagation();
      this.remember();
      const axis = this.drawingAxes?.[this.timeframe] || this.axis();
      const step = axis.length >= 2 ? Math.max(60, Math.round(axis[axis.length - 1] - axis[axis.length - 2])) : 3600;
      const ray = {
        id: crypto.randomUUID(),
        a: { time: anchor.time, price: anchor.price },
        b: { time: anchor.time + step, price: anchor.price },
        timeframe: this.timeframe,
        basis: RayGeometry.capture(axis),
        color: RayGeometry.color(this.color),
        extend: "horizontal",
        observedAt: this.cutoff,
      };
      this.items.push(ray);
      this.selected = ray.id;
      this.measurementSelected = false;
      this.hoverPrice = null;
      this.commit();
      this.onSelection?.();
      this.onDone?.();
      return;
    }
    if (this.active) {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (!this.draft) {
        this.draft = { a: anchor, b: anchor, extend:this.extension || 'right',
          basis:RayGeometry.capture(this.drawingAxes?.[this.timeframe] || this.axis()) };
        this.onHint?.("Zweiten Punkt setzen · Escape zum Abbrechen");
      } else if (Math.abs(anchor.time - this.draft.a.time) >= 1) {
        this.remember();
        const points = [this.draft.a, anchor].sort((a, b) => a.time - b.time);
        const ray = {
          id: crypto.randomUUID(),
          a: points[0],
          b: points[1],
          timeframe: this.timeframe,
          basis: RayGeometry.capture(this.drawingAxes?.[this.timeframe] || this.axis()),
          color: RayGeometry.color(this.color),
          extend:this.extension || 'right',
          observedAt:this.cutoff,
        };
        if (ray.extend==='horizontal') ray.b.price=ray.a.price;
        this.items.push(ray);
        this.selected = ray.id;
        this.measurementSelected = false;
        this.draft = null;
        this.commit();
        this.onDone?.();
      }
      this.update();
      return;
    }
    const hit = this.hit(p);
    this.selected = hit?.ray.id || null;
    this.measurementSelected = !hit && this.hitMeasurement(p);
    this.update();
    this.onSelection?.();
    if (hit) {
      this.drag = {
        ...hit,
        start: anchor,
        original: structuredClone(hit.ray),
        before: this.snapshot(),
        changed: false,
      };
      this.chart.applyOptions({
        handleScroll: {
          pressedMouseMove: false,
          horzTouchDrag: false,
          vertTouchDrag: false,
        },
      });
      event.preventDefault();
      event.stopImmediatePropagation();
      this.host.setPointerCapture(event.pointerId);
    }
  }
  move(event) {
    const p = this.coords(event);
    if (this.measureActive && this.measureDraft && this.inside(p)) {
      const b = this.anchor(p),
        axis = this.axis();
      if (b) {
        const i = Math.max(
          0,
          Math.min(
            axis.length - 1,
            Math.round(RayGeometry.logicalAtPixel(this.chart.timeScale(),p.x)),
          ),
        );
        b.time = axis[i];
        this.measureDraft.b = b;
        this.onMeasure?.();
        this.update();
      }
    }
    if (this.horizontalActive && this.inside(p)) {
      const a = this.anchor(p);
      this.hoverPrice = a ? a.price : null;
      this.update();
      return;
    }
    if (this.draft && (this.active || this.rectActive || this.longActive) && this.inside(p)) {
      const a = this.anchor(p);
      if (a) {
        if (this.draft.kind === "longbox") {
          const axis = this.drawingAxes?.[this.timeframe] || this.axis();
          const step = axis.length >= 2 ? Math.max(60, Math.round(axis[axis.length - 1] - axis[axis.length - 2])) : 3600;
          const entry = this.draft.a.price;
          const stop = a.price < entry ? a.price : Math.max(0.01, entry - Math.abs(a.price - entry));
          this.draft.b = { time: Math.max(a.time, this.draft.a.time + step * 12), price: stop };
          this.draft.targetPrice = entry + 2 * Math.max(0.01, entry - stop);
        } else {
          this.draft.b = a;
          if (this.draft.extend==='horizontal') this.draft.b.price=this.draft.a.price;
        }
        this.update();
      }
    }
    if (!this.drag) {
      if (!this.active && !this.measureActive && !this.horizontalActive && !this.rectActive && !this.longActive && this.inside(p))
        this.host.style.cursor = this.hit(p)
          ? "grab"
          : this.hitMeasurement(p)
            ? "pointer"
            : "";
      return;
    }
    const anchor = this.anchor(p);
    if (!anchor) return;
    const d = this.drag;
    if (d.key === "line") {
      const axis=this.drawingAxes?.[this.timeframe] || this.axis(),
        delta=RayGeometry.logicalAt(axis,anchor.time)-RayGeometry.logicalAt(axis,d.start.time),
        dp = anchor.price - d.start.price;
      if (Math.min(d.original.a.price, d.original.b.price) + dp <= 0) return;
      d.ray.a = {
        time: RayGeometry.timeAt(axis,RayGeometry.logicalAt(axis,d.original.a.time)+delta),
        price: d.original.a.price + dp,
      };
      d.ray.b = {
        time: RayGeometry.timeAt(axis,RayGeometry.logicalAt(axis,d.original.b.time)+delta),
        price: d.original.b.price + dp,
      };
      if (d.ray.kind === "longbox" && Number.isFinite(d.original.targetPrice)) {
        d.ray.targetPrice = Math.max(d.ray.a.price + 0.01, d.original.targetPrice + dp);
      }
    } else if (d.ray.kind === "longbox") {
      if (d.key === "target") {
        if (anchor.price <= d.ray.a.price || anchor.time <= d.ray.a.time) return;
        d.ray.targetPrice = anchor.price;
        d.ray.b = { time: anchor.time, price: d.ray.b.price };
      } else if (d.key === "b") {
        if (anchor.price >= d.ray.a.price || anchor.time <= d.ray.a.time) return;
        d.ray.b = anchor;
      } else if (d.key === "a") {
        const tPrice = Number.isFinite(d.ray.targetPrice) ? d.ray.targetPrice : Infinity;
        if (anchor.price <= d.ray.b.price || anchor.price >= tPrice || anchor.time >= d.ray.b.time) return;
        d.ray.a = anchor;
      }
    } else {
      const other = d.key === "a" ? d.ray.b : d.ray.a;
      if (
        (d.key === "a" && anchor.time >= other.time) ||
        (d.key === "b" && anchor.time <= other.time)
      )
        return;
      d.ray[d.key] = anchor;
      if (d.ray.extend==='horizontal') other.price=anchor.price;
    }
    d.changed = true;
    // Rebase only after an intentional edit, never on load/zoom/interval switch.
    d.ray.basis=RayGeometry.capture(this.drawingAxes?.[this.timeframe] || this.axis());
    d.ray.timeframe=this.timeframe;
    event.preventDefault();
    event.stopImmediatePropagation();
    this.update();
  }
  up(event) {
    if (!this.drag) return;
    if (this.drag.changed) {
      this.remember(this.drag.before);
      this.drag.ray.observedAt=this.cutoff;
      this.commit();
    }
    this.drag = null;
    this.chart.applyOptions({
      handleScroll: {
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
    });
    event.stopImmediatePropagation();
  }
  paint(ctx, size) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, size.width, size.height);
    ctx.clip();
    const measurement = this.measureDraft || this.measurement;
    if (
      measurement &&
      measurement.a.time <= this.measurementEnd &&
      measurement.b.time <= this.measurementEnd
    ) {
      const a = this.point(measurement.a),
        b = this.point(measurement.b);
      if ([a.x, a.y, b.x, b.y].every(Number.isFinite)) {
        const loss = measurement.b.price < measurement.a.price,
          color = loss ? "#dc2626" : "#2563eb";
        const left = Math.min(a.x, b.x),
          top = Math.min(a.y, b.y),
          width = Math.abs(b.x - a.x),
          height = Math.abs(b.y - a.y);
        ctx.fillStyle = loss ? "#dc262622" : "#2563eb22";
        ctx.fillRect(left, top, width, height);
        ctx.strokeStyle = color;
        ctx.lineWidth = this.measurementSelected ? 2.5 : 1.5;
        ctx.setLineDash([5, 4]);
        ctx.strokeRect(left, top, width, height);
        ctx.setLineDash([]);
        const x = (a.x + b.x) / 2;
        ctx.beginPath();
        ctx.moveTo(x, a.y);
        ctx.lineTo(x, b.y);
        const sign = b.y >= a.y ? 1 : -1;
        ctx.moveTo(x - 5, b.y - sign * 7);
        ctx.lineTo(x, b.y);
        ctx.lineTo(x + 5, b.y - sign * 7);
        ctx.stroke();
        for (const p of [a, b]) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
        }
      }
    }
    const labels = [];
    if (this.horizontalActive && Number.isFinite(this.hoverPrice)) {
      const hy = this.series.priceToCoordinate(this.hoverPrice);
      if (hy !== null && Number.isFinite(hy)) {
        ctx.save();
        ctx.strokeStyle = RayGeometry.color(this.color) + "aa";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(0, hy);
        ctx.lineTo(size.width, hy);
        ctx.stroke();
        ctx.restore();
      }
    }
    const draw = (ray, color, width, dash, label) => {
      if (ray.a.time === ray.b.time) return;
      const scale = this.chart.timeScale();
      const axis=this.axisFor(ray);
      const from = RayGeometry.logicalAtPixel(scale,0),
        to = RayGeometry.logicalAtPixel(scale,size.width);
      if (from === null || to === null) return;
      const bounds=RayGeometry.bounds(ray.extend,ray.a.logical ?? RayGeometry.logicalAt(axis,ray.a.time),ray.b.logical ?? RayGeometry.logicalAt(axis,ray.b.time),from,to);
      if (!bounds) return;
      const {start,end}=bounds;
      const points = RayGeometry.drawingPoints(axis,ray,start,end).map((logical) => ({
        logical,
        price: RayGeometry.valueAtLogical(axis, ray, logical),
      }));
      ctx.beginPath();
      let started = false;
      points.forEach((point, i) => {
        const x = RayGeometry.pixelAt(scale,point.logical),
          y = this.series.priceToCoordinate(point.price);
        if (x === null || y === null || !Number.isFinite(y)) return;
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.setLineDash(dash);
      ctx.stroke();
      ctx.setLineDash([]);
      if (label) {
        ctx.font = "600 12px Arial";
        const w = ctx.measureText(label).width + 14;
        const labelPoint = this.point(ray.labelAt || ray.b,axis);
        let x = ray.labelEdge
          ? size.width - w - 12
          : Math.max(45, Math.min(size.width - w - 6, labelPoint.x + 10));
        const visibleStart = RayGeometry.pixelAt(scale,start) ?? 0;
        const priceY = (x) =>
          this.series.priceToCoordinate(
            RayGeometry.candleValue(
              axis,
              ray,
              RayGeometry.timeAt(axis,RayGeometry.logicalAtPixel(scale,Math.max(x, visibleStart))),
            ),
          );
        // If the right endpoint is outside the price pane, label the visible segment.
        let y = priceY(x);
        if (!Number.isFinite(y) || y < 12 || y > size.height - 12) {
          for (
            let candidate = x;
            candidate >= Math.max(45, RayGeometry.pixelAt(scale,start));
            candidate -= 24
          ) {
            const value = priceY(candidate);
            if (
              Number.isFinite(value) &&
              value >= 24 &&
              value <= size.height - 24
            ) {
              x = candidate;
              y = value;
              break;
            }
          }
        }
        if (Number.isFinite(y) && y >= 0 && y <= size.height)
          labels.push({
            text: label,
            x,
            y,
            w,
            h: 24,
            color: ray.labelColor || color,
            priceY,
            visibleStart,
          });
      }
    };
    const baseScale = this.chart.timeScale();
    const baseAxis = this.axis();
    const baseFrom = RayGeometry.logicalAtPixel(baseScale, 0);
    const baseTo = RayGeometry.logicalAtPixel(baseScale, size.width);
    // 1) Optional subtle compression wedge fill between active red & green lines
    if (this.wedge && this.wedge.red && this.wedge.green && baseAxis.length >= 2 && baseFrom !== null && baseTo !== null) {
      const wRed = this.wedge.red, wGreen = this.wedge.green;
      const aR = wRed.a.logical ?? RayGeometry.logicalAt(baseAxis, wRed.a.time);
      const aG = wGreen.a.logical ?? RayGeometry.logicalAt(baseAxis, wGreen.a.time);
      const startL = Math.max(baseFrom, aR ?? baseFrom, aG ?? baseFrom);
      const endL = Math.min(baseTo, baseAxis.length - 1 + 4);
      if (Number.isFinite(startL) && Number.isFinite(endL) && endL > startL) {
        const x1 = RayGeometry.pixelAt(baseScale, startL);
        const x2 = RayGeometry.pixelAt(baseScale, endL);
        const r1 = RayGeometry.valueAtLogical(baseAxis, wRed, startL);
        const r2 = RayGeometry.valueAtLogical(baseAxis, wRed, endL);
        const g1 = RayGeometry.valueAtLogical(baseAxis, wGreen, startL);
        const g2 = RayGeometry.valueAtLogical(baseAxis, wGreen, endL);
        if ([x1, x2, r1, r2, g1, g2].every(Number.isFinite) && r1 > g1 && r2 > 0 && g2 > 0) {
          const yr1 = this.series.priceToCoordinate(r1);
          const yr2 = this.series.priceToCoordinate(r2);
          const yg1 = this.series.priceToCoordinate(g1);
          const yg2 = this.series.priceToCoordinate(g2);
          if ([yr1, yr2, yg1, yg2].every(Number.isFinite)) {
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x1, yr1);
            ctx.lineTo(x2, yr2);
            ctx.lineTo(x2, yg2);
            ctx.lineTo(x1, yg1);
            ctx.closePath();
            ctx.fillStyle = "rgba(59, 130, 246, 0.055)";
            ctx.fill();
            ctx.restore();
          }
        }
      }
    }
    // 2) Optional Risk / +2R Target shading for active backtest or setup case
    if (this.tradeZones && baseAxis.length >= 2 && baseFrom !== null && baseTo !== null) {
      const tz = this.tradeZones;
      const startL = RayGeometry.logicalAt(baseAxis, tz.startTime);
      const endL = tz.endTime ? RayGeometry.logicalAt(baseAxis, tz.endTime) : (baseAxis.length - 1 + 6);
      if (Number.isFinite(startL) && Number.isFinite(endL) && endL >= startL) {
        const x1 = RayGeometry.pixelAt(baseScale, Math.max(baseFrom, startL));
        const x2 = RayGeometry.pixelAt(baseScale, Math.min(baseTo, Math.max(startL + 1, endL)));
        const yEntry = this.series.priceToCoordinate(tz.entry);
        const yStop = tz.stop ? this.series.priceToCoordinate(tz.stop) : null;
        const yTarget = tz.target2r ? this.series.priceToCoordinate(tz.target2r) : null;
        if (Number.isFinite(x1) && Number.isFinite(x2) && x2 > x1 && Number.isFinite(yEntry)) {
          ctx.save();
          if (Number.isFinite(yStop)) {
            ctx.fillStyle = "rgba(239, 83, 80, 0.085)";
            ctx.fillRect(x1, Math.min(yEntry, yStop), x2 - x1, Math.abs(yStop - yEntry));
          }
          if (Number.isFinite(yTarget)) {
            ctx.fillStyle = "rgba(38, 166, 154, 0.08)";
            ctx.fillRect(x1, Math.min(yEntry, yTarget), x2 - x1, Math.abs(yEntry - yTarget));
          }
          ctx.restore();
        }
      }
    }
    const fmtDe = (v, d = 2) => Number(v).toFixed(d).replace(".", ",");
    const pill = (text, x, y, bg, fg = "#fff") => {
      ctx.save();
      ctx.font = "600 11px system-ui, -apple-system, sans-serif";
      const tw = ctx.measureText(text).width;
      const pw = tw + 12, ph = 19, rad = 5;
      const px = Math.max(6, Math.min(size.width - pw - 6, x));
      const py = Math.max(6, Math.min(size.height - ph - 6, y));
      ctx.fillStyle = bg;
      ctx.beginPath();
      if (typeof ctx.roundRect === "function") ctx.roundRect(px, py, pw, ph, rad);
      else ctx.rect(px, py, pw, ph);
      ctx.fill();
      ctx.fillStyle = fg;
      ctx.textBaseline = "middle";
      ctx.fillText(text, px + 6, py + ph / 2 + 0.5);
      ctx.restore();
    };
    const drawHandle = (hx, hy, stroke) => {
      if (!Number.isFinite(hx) || !Number.isFinite(hy)) return;
      ctx.save();
      ctx.beginPath();
      ctx.arc(hx, hy, 5, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    };
    const drawRect = (r, selected, isDraft = false) => {
      const axis = this.axisFor(r);
      const pa = this.point(r.a, axis);
      const pb = this.point(r.b, axis);
      if (![pa.x, pa.y, pb.x, pb.y].every(Number.isFinite)) return;
      const x = Math.min(pa.x, pb.x), y = Math.min(pa.y, pb.y);
      const w = Math.max(2, Math.abs(pb.x - pa.x)), h = Math.max(2, Math.abs(pb.y - pa.y));
      const col = RayGeometry.color(r.color);
      ctx.save();
      ctx.fillStyle = col + (selected ? "34" : "22");
      ctx.fillRect(x, y, w, h);
      ctx.strokeStyle = col;
      ctx.lineWidth = selected ? 2.2 : 1.5;
      if (isDraft) ctx.setLineDash([5, 4]);
      ctx.strokeRect(x, y, w, h);
      ctx.restore();
      if (selected || isDraft) {
        const hi = Math.max(r.a.price, r.b.price), lo = Math.min(r.a.price, r.b.price);
        pill(`Zone ${fmtDe(lo)} – ${fmtDe(hi)}`, x + 4, y - 22, col);
        drawHandle(pa.x, pa.y, col);
        drawHandle(pb.x, pb.y, col);
      }
    };
    const drawLongBox = (r, selected, isDraft = false) => {
      const axis = this.axisFor(r);
      const entry = r.a.price;
      const stop = r.b.price;
      const risk = Math.max(0.0001, entry - stop);
      const target = Number.isFinite(r.targetPrice) ? r.targetPrice : entry + 2 * risk;
      const pa = this.point(r.a, axis);
      const pb = this.point(r.b, axis);
      const pt = this.point({ time: r.b.time, price: target }, axis);
      if (![pa.x, pa.y, pb.x, pb.y, pt.y].every(Number.isFinite)) return;
      const x1 = Math.min(pa.x, pb.x), x2 = Math.max(pa.x, pb.x);
      const bw = Math.max(12, x2 - x1);
      const riskPct = (risk / entry) * 100;
      const reward = Math.max(0, target - entry);
      const rewardPct = (reward / entry) * 100;
      const rr = reward / risk;
      const qty = 1000 / entry;
      const riskEur = 1000 * (risk / entry);
      ctx.save();
      if (isDraft) ctx.setLineDash([5, 4]);
      // Green target zone
      ctx.fillStyle = selected ? "rgba(38, 166, 154, 0.26)" : "rgba(38, 166, 154, 0.18)";
      ctx.fillRect(x1, Math.min(pa.y, pt.y), bw, Math.abs(pa.y - pt.y));
      ctx.strokeStyle = "#26a69a";
      ctx.lineWidth = selected ? 2 : 1.4;
      ctx.strokeRect(x1, Math.min(pa.y, pt.y), bw, Math.abs(pa.y - pt.y));
      // Red risk zone
      ctx.fillStyle = selected ? "rgba(239, 83, 80, 0.28)" : "rgba(239, 83, 80, 0.20)";
      ctx.fillRect(x1, Math.min(pa.y, pb.y), bw, Math.abs(pb.y - pa.y));
      ctx.strokeStyle = "#ef5350";
      ctx.lineWidth = selected ? 2 : 1.4;
      ctx.strokeRect(x1, Math.min(pa.y, pb.y), bw, Math.abs(pb.y - pa.y));
      // Entry divider line
      ctx.setLineDash([]);
      ctx.strokeStyle = "rgba(226, 232, 240, 0.85)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x1, pa.y);
      ctx.lineTo(x1 + bw, pa.y);
      ctx.stroke();
      ctx.restore();
      // Crisp TradingView-style badges
      pill(`Ziel ${fmtDe(target)} (+${fmtDe(rewardPct)} % · +${fmtDe(rr, 1)} R)`, x1 + 6, Math.min(pa.y, pt.y) - 22, "#0f766e");
      pill(`Einstieg ${fmtDe(entry)} · 1.000 € ≈ ${fmtDe(qty, 2)} Stk. · Risiko ${fmtDe(riskEur, 1)} €`, x1 + 6, pa.y - 9.5, "rgba(19, 26, 36, 0.92)", "#e6edf3");
      pill(`Stop ${fmtDe(stop)} (−${fmtDe(riskPct)} %)`, x1 + 6, Math.max(pa.y, pb.y) + 4, "#b91c1c");
      if (selected || isDraft) {
        drawHandle(pa.x, pa.y, "#e2e8f0");
        drawHandle(pb.x, pb.y, "#ef5350");
        drawHandle(pt.x, pt.y, "#26a69a");
      }
    };
    for (const r of this.automatic) draw(r, r.color, r.width, r.dash, r.label);
    for (const r of this.items) {
      if (!this.visible(r)) continue;
      if (r.kind === "rect") {
        drawRect(r, r.id === this.selected, false);
        continue;
      }
      if (r.kind === "longbox") {
        drawLongBox(r, r.id === this.selected, false);
        continue;
      }
      draw(
        r,
        RayGeometry.color(r.color),
        r.id === this.selected ? 2.5 : 2,
        [],
        `${r.timeframe} · Eigen`,
      );
      if (r.id === this.selected) {
        for (const anchor of [r.a, r.b]) {
          const p = this.point(anchor,this.axisFor(r));
          drawHandle(p.x, p.y, RayGeometry.color(r.color));
        }
      }
    }
    if (this.draft) {
      if (this.draft.kind === "rect") drawRect(this.draft, true, true);
      else if (this.draft.kind === "longbox") drawLongBox(this.draft, true, true);
      else draw(this.draft, RayGeometry.color(this.color), 2, [5, 4], "");
    }
    const occupied = this.labelObstacles?.() || [];
    const overlaps = (a, b) =>
      a.x < b.x + b.w + 5 &&
      a.x + a.w + 5 > b.x &&
      a.y < b.y + b.h + 5 &&
      a.y + a.h + 5 > b.y;
    for (const label of labels) {
      const columns = [
        label.x,
        ...occupied.map((r) => r.x - label.w - 8),
      ].filter((x) => x >= 8 && x + label.w <= size.width - 4);
      let box = null;
      for (const [columnIndex, x] of [...columns, columns[0]].entries()) {
        const preferred = label.priceY(x) - label.h - 4;
        for (
          let shift = 0;
          shift < (columnIndex === columns.length ? size.height : 87);
          shift += 29
        ) {
          for (const dy of shift === 0 ? [0] : [shift, -shift]) {
            const candidate = {
              x,
              y: Math.max(
                8,
                Math.min(size.height - label.h - 8, preferred + dy),
              ),
              w: label.w,
              h: label.h,
            };
            if (!occupied.some((r) => overlaps(candidate, r))) {
              box = candidate;
              break;
            }
          }
          if (box) break;
        }
        if (box) break;
      }
      if (!box) continue;
      const lineX = Math.max(box.x, label.visibleStart),
        lineY = label.priceY(lineX);
      ctx.strokeStyle = label.color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(lineX, lineY);
      ctx.lineTo(
        lineX > box.x + box.w / 2 ? box.x + box.w : box.x,
        box.y + box.h / 2,
      );
      ctx.stroke();
      ctx.fillStyle = label.color;
      if (typeof ctx.roundRect === "function") {
        ctx.beginPath();
        ctx.roundRect(box.x, box.y, box.w, box.h, 5);
        ctx.fill();
      } else {
        ctx.fillRect(box.x, box.y, box.w, box.h);
      }
      ctx.font = "600 11.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif";
      ctx.fillStyle = "#fff";
      ctx.fillText(label.text, box.x + 7, box.y + 16);
      occupied.push(box);
    }
    ctx.restore();
  }
}
if (typeof window !== "undefined") {
  window.RayLayer = RayLayer;
  window.RayGeometry = RayGeometry;
}
if (typeof module !== "undefined") module.exports = { RayGeometry, RayLayer };
