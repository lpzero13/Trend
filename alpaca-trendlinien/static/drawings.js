/* Pure coordinate math: straight rays use logical candle positions. */
const axisSteps = new WeakMap();
const RayGeometry = {
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
    const a = ray.a.logical ?? this.logicalAt(axis, ray.a.time),
      b = ray.b.logical ?? this.logicalAt(axis, ray.b.time);
    if (a === null || b === null || Math.abs(b - a) < 1e-10) return null;
    return (
      ray.a.price +
      ((ray.b.price - ray.a.price) * (this.logicalAt(axis, time) - a)) / (b - a)
    );
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
      selected: null,
      draft: null,
      undoStack: [],
      active: false,
      measureActive: false,
      measurement: null,
      measureDraft: null,
      drag: null,
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
        if (this.active || this.measureActive || this.drag) {
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
  point(anchor) {
    return {
      x: this.chart
        .timeScale()
        .logicalToCoordinate(anchor.logical ?? this.logicalAt(anchor.time)),
      y: this.series.priceToCoordinate(anchor.price),
    };
  }
  anchor(point) {
    const logical = this.chart.timeScale().coordinateToLogical(point.x),
      price = this.series.coordinateToPrice(point.y);
    if (
      logical === null ||
      price === null ||
      !Number.isFinite(price) ||
      price <= 0
    )
      return null;
    return { time: Math.round(this.timeAt(logical)), price };
  }
  coords(event) {
    const r = this.host.getBoundingClientRect();
    return { x: event.clientX - r.left, y: event.clientY - r.top };
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
    const a = this.point(ray.a),
      b = this.point(ray.b);
    return [a, b];
  }
  hit(p) {
    for (const ray of [...this.items].reverse()) {
      const [a, b] = this.line(ray);
      for (const key of ["a", "b"]) {
        const q = key === "a" ? a : b;
        if (q.x === null || q.y === null) continue;
        if (Math.hypot(p.x - q.x, p.y - q.y) < 10) return { ray, key };
      }
      const logical = this.chart.timeScale().coordinateToLogical(p.x);
      const time = this.timeAt(logical);
      const y = this.series.priceToCoordinate(
        RayGeometry.candleValue(this.axis(), ray, time),
      );
      if (time >= ray.a.time && y !== null && Math.abs(p.y - y) < 8)
        return { ray, key: "line" };
    }
    return null;
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
            Math.round(this.chart.timeScale().coordinateToLogical(p.x)),
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
    if (this.active) {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (!this.draft) {
        this.draft = { a: anchor, b: anchor };
        this.onHint?.("Zweiten Punkt setzen · Escape zum Abbrechen");
      } else if (Math.abs(anchor.time - this.draft.a.time) >= 1) {
        this.remember();
        const points = [this.draft.a, anchor].sort((a, b) => a.time - b.time);
        const ray = {
          id: crypto.randomUUID(),
          a: points[0],
          b: points[1],
          timeframe: this.timeframe,
        };
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
            Math.round(this.chart.timeScale().coordinateToLogical(p.x)),
          ),
        );
        b.time = axis[i];
        this.measureDraft.b = b;
        this.onMeasure?.();
        this.update();
      }
    }
    if (this.draft && this.active && this.inside(p)) {
      const a = this.anchor(p);
      if (a) {
        this.draft.b = a;
        this.update();
      }
    }
    if (!this.drag) {
      if (!this.active && !this.measureActive && this.inside(p))
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
      const dt = anchor.time - d.start.time,
        dp = anchor.price - d.start.price;
      if (Math.min(d.original.a.price, d.original.b.price) + dp <= 0) return;
      d.ray.a = {
        time: d.original.a.time + dt,
        price: d.original.a.price + dp,
      };
      d.ray.b = {
        time: d.original.b.time + dt,
        price: d.original.b.price + dp,
      };
    } else {
      const other = d.key === "a" ? d.ray.b : d.ray.a;
      if (
        (d.key === "a" && anchor.time >= other.time) ||
        (d.key === "b" && anchor.time <= other.time)
      )
        return;
      d.ray[d.key] = anchor;
    }
    d.changed = true;
    event.preventDefault();
    event.stopImmediatePropagation();
    this.update();
  }
  up(event) {
    if (!this.drag) return;
    if (this.drag.changed) {
      this.remember(this.drag.before);
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
    const draw = (ray, color, width, dash, label) => {
      if (ray.a.time === ray.b.time) return;
      const scale = this.chart.timeScale();
      const from = scale.coordinateToLogical(0),
        to = scale.coordinateToLogical(size.width);
      if (from === null || to === null) return;
      const start = Math.max(from, ray.a.logical ?? this.logicalAt(ray.a.time));
      if (start >= to) return;
      const points = [start, to].map((logical) => ({
        logical,
        price: RayGeometry.candleValue(this.axis(), ray, this.timeAt(logical)),
      }));
      ctx.beginPath();
      let started = false;
      points.forEach((point, i) => {
        const x = scale.logicalToCoordinate(point.logical),
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
        const labelPoint = this.point(ray.labelAt || ray.b);
        let x = ray.labelEdge
          ? size.width - w - 12
          : Math.max(45, Math.min(size.width - w - 6, labelPoint.x + 10));
        const visibleStart = scale.logicalToCoordinate(start) ?? 0;
        const priceY = (x) =>
          this.series.priceToCoordinate(
            RayGeometry.candleValue(
              this.axis(),
              ray,
              this.timeAt(scale.coordinateToLogical(Math.max(x, visibleStart))),
            ),
          );
        // If the right endpoint is outside the price pane, label the visible segment.
        let y = priceY(x);
        if (!Number.isFinite(y) || y < 12 || y > size.height - 12) {
          for (
            let candidate = x;
            candidate >= Math.max(45, scale.logicalToCoordinate(start));
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
    for (const r of this.automatic) draw(r, r.color, r.width, r.dash, r.label);
    for (const r of this.items) {
      draw(
        r,
        "#3988ee",
        r.id === this.selected ? 2.5 : 2,
        [],
        `${r.timeframe} · Eigen`,
      );
      if (r.id === this.selected) {
        for (const anchor of [r.a, r.b]) {
          const p = this.point(anchor);
          ctx.beginPath();
          ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
          ctx.fillStyle = "#fff";
          ctx.fill();
          ctx.strokeStyle = "#3988ee";
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
    }
    if (this.draft) draw(this.draft, "#3988ee", 2, [5, 4], "");
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
      ctx.fillRect(box.x, box.y, box.w, box.h);
      ctx.font = "600 12px Arial";
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
