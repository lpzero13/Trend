const { test } = require("node:test");
const assert = require("node:assert/strict");
const { RayGeometry: G, RayLayer } = require("../static/drawings.js");

const hour = 3600;
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-7, `${a} != ${b}`);

test('fractional MTF anchors interpolate integer-only library coordinates instead of jumping to the left edge',()=>{
  const scale={logicalToCoordinate:n=>Number.isInteger(n)?n*100+20:0,coordinateToLogical:x=>Math.ceil((x-20)/100)};
  for(const n of [-.75,0,.1,.5,1,7.25]) {
    near(G.pixelAt(scale,n),n*100+20);
    near(G.logicalAtPixel(scale,G.pixelAt(scale,n)),n);
  }
  const target=[0,7*24*hour,14*24*hour];
  const source=[0,24*hour,2*24*hour,3*24*hour,4*24*hour,7*24*hour,8*24*hour,9*24*hour];
  const ray={a:{time:24*hour,price:100},b:{time:8*24*hour,price:105},basis:G.capture(source)};
  const xs=G.drawingPoints(target,ray,G.logicalAt(target,ray.a.time),2).map(n=>G.pixelAt(scale,n));
  assert.ok(xs.every((x,i)=>!i || x>=xs[i-1]));assert.ok(xs.every(x=>x>20));
});

test('personal daily lines stay straight through the same saved anchors in every interval',()=>{
  const daily=[0,24*hour,48*hour,120*hour,144*hour];
  const hourly=[0,hour,2*hour,24*hour,25*hour,48*hour,49*hour,120*hour,121*hour,144*hour];
  const four=[0,4*hour,24*hour,28*hour,48*hour,52*hour,120*hour,124*hour,144*hour];
  const weekly=[0,120*hour,240*hour];
  const ray={a:{time:0,price:100},b:{time:48*hour,price:110},basis:G.capture(daily)};
  const before=JSON.stringify(ray);
  for(const axis of [daily,hourly,four,weekly,[...hourly,145*hour,200*hour]]) {
    near(G.candleValue(axis,ray,ray.a.time),ray.a.price);
    near(G.candleValue(axis,ray,ray.b.time),ray.b.price);
    const a=G.logicalAt(axis,ray.a.time),b=G.logicalAt(axis,ray.b.time);
    for(const fraction of [-.5,0,.25,.5,.75,1,2]) {
      const logical=a+(b-a)*fraction;
      near(G.candleValue(axis,ray,G.timeAt(axis,logical)),ray.a.price+(ray.b.price-ray.a.price)*fraction);
    }
    assert.deepEqual(G.drawingPoints(axis,ray,a,b+3),[a,b+3]);
  }
  assert.equal(JSON.stringify(ray),before);
});

test('renderer and hit test use one straight segment for legacy 1D rays in 4h and weekly views',()=>{
  const daily=[0,24*hour,48*hour,120*hour,144*hour];
  const ray={id:'daily',timeframe:'1D',a:{time:24*hour,price:100},b:{time:120*hour,price:120},basis:G.capture(daily),extend:'both'};
  const original=JSON.stringify(ray);
  for(const axis of [[0,4*hour,24*hour,28*hour,48*hour,52*hour,120*hour,124*hour,144*hour],[0,168*hour,336*hour]]) {
    const path=[];
    const scale={logicalToCoordinate:n=>Number.isInteger(n)?n*100:0,coordinateToLogical:x=>Math.ceil(x/100)};
    const layer=Object.assign(Object.create(RayLayer.prototype),{
      timeframe:'4h',axis:()=>axis,chart:{timeScale:()=>scale},series:{priceToCoordinate:p=>p},
      automatic:[{...ray,color:'blue',width:2,dash:[]}],items:[],
    });
    const ctx={save(){},restore(){},beginPath(){},rect(){},clip(){},setLineDash(){},stroke(){},
      moveTo(x,y){path.push([x,y])},lineTo(x,y){path.push([x,y])}};
    layer.paint(ctx,{width:550,height:300});
    assert.equal(path.length,2,'a ray is never a sampled per-candle polyline');
    near(path[0][0],0);near(path[1][0],550);
    const a=layer.point(ray.a),b=layer.point(ray.b);
    for(const p of path) near((p[1]-a.y)*(b.x-a.x),(p[0]-a.x)*(b.y-a.y));
    layer.items=[ray];
    const x=430,y=a.y+(b.y-a.y)*(x-a.x)/(b.x-a.x);
    assert.equal(layer.hit({x,y})?.ray.id,'daily');
    assert.equal(layer.hit({x,y:y+15}),null);
  }
  assert.equal(JSON.stringify(ray),original);
});

test('old drawings bind once to their original interval; zoom, extra history and interval switches do not rebase',()=>{
  const daily=[0,24*hour,48*hour],hourly=[0,hour,2*hour,24*hour,48*hour];
  let changes=0;
  const layer=Object.assign(Object.create(RayLayer.prototype),{items:[{id:'d',timeframe:'1D',a:{time:0,price:100},b:{time:48*hour,price:110}}],onChange(){changes++},update(){}});
  layer.bindAxes({'1D':daily,'1h':hourly});
  const stored=JSON.stringify(layer.items);
  layer.bindAxes({'1D':[-24*hour,...daily,72*hour],'1h':hourly});
  assert.equal(JSON.stringify(layer.items),stored);assert.equal(changes,1);
  assert.notEqual(layer.items[0].basis.axis,daily);
});

test('a deliberate edit on another interval rebases only the selected drawing and can be undone',()=>{
  const daily=[0,24*hour,48*hour],hourly=[0,hour,2*hour,24*hour,48*hour];
  const ray={id:'d',timeframe:'1D',a:{time:0,price:100},b:{time:48*hour,price:110},basis:G.capture(daily)};
  const before=JSON.stringify([ray]);
  const layer=Object.assign(Object.create(RayLayer.prototype),{items:[ray],axis:()=>hourly,timeframe:'1h',cutoff:50*hour,undoStack:[],
    coords:()=>({x:1,y:105}),anchor:()=>({time:hour,price:105}),update(){},onChange(){},
    chart:{applyOptions(){}},drag:{key:'a',ray,original:structuredClone(ray),before,changed:false}});
  layer.move({preventDefault(){},stopImmediatePropagation(){}});
  assert.equal(ray.timeframe,'1h');assert.deepEqual(ray.basis.axis,hourly);
  layer.up({stopImmediatePropagation(){}});layer.undo();
  assert.equal(JSON.stringify(layer.items),before);
});

test('line color persists per drawing; undo restores the old color without changing geometry',()=>{
  const ray={id:'r',timeframe:'1D',a:{time:0,price:100},b:{time:hour,price:110},basis:G.capture([0,hour])};
  let saved;
  const layer=Object.assign(Object.create(RayLayer.prototype),{items:[ray],selected:'r',undoStack:[],update(){},onChange(items){saved=JSON.stringify(items)}});
  layer.changeColor('#DC2626');assert.equal(ray.color,'#dc2626');
  assert.equal(JSON.parse(saved)[0].color,'#dc2626');
  layer.undo();assert.deepEqual(layer.items,[{id:'r',timeframe:'1D',a:{time:0,price:100},b:{time:hour,price:110},basis:G.capture([0,hour])}]);
  layer.selected=null;layer.changeColor('#16a34a');assert.equal(layer.color,'#16a34a');
  assert.equal(layer.items[0].color,undefined);
});

test('left rays, full lines and segments draw to their actual endpoints and hit on the correct side',()=>{
  const axis=[0,hour,2*hour,3*hour,4*hour];
  const ray={id:'r',a:{time:hour,price:100},b:{time:2*hour,price:101}};
  const lines=[];const layer=Object.assign(Object.create(RayLayer.prototype),{
    axis:()=>axis,chart:{timeScale:()=>({logicalToCoordinate:n=>n*100,coordinateToLogical:x=>x/100})},
    series:{priceToCoordinate:p=>p},items:[],automatic:['left','both','segment'].map(extend=>({...ray,extend,color:'blue',width:2,dash:[]}))
  });
  const ctx={save(){},restore(){},beginPath(){},rect(){},clip(){},setLineDash(){},stroke(){},
    moveTo(x,y){lines.push(['start',x,y]);},lineTo(x,y){lines.push(['end',x,y]);}};
  layer.paint(ctx,{width:400,height:300});
  assert.deepEqual(lines.map(x=>x.slice(0,2)),[['start',0],['end',200],['start',0],['end',400],['start',100],['end',200]]);
  for(const extend of ['left','right','both','segment']){
    layer.items=[{...ray,extend}];
    assert.equal(!!layer.hit({x:0,y:99}),['left','both'].includes(extend));
    assert.equal(!!layer.hit({x:400,y:103}),['right','both'].includes(extend));
  }
  layer.items=[{...ray,extend:'both',observedAt:50}];layer.cutoff=49;
  assert.equal(layer.hit({x:0,y:99}),null);
});

test('changing a selected line to horizontal is persisted and undo restores both price and extension',()=>{
  const layer=Object.assign(Object.create(RayLayer.prototype),{items:[{id:'r',a:{time:1,price:100},b:{time:2,price:105},extend:'right'}],selected:'r',undoStack:[],update(){},onChange(){}});
  layer.changeExtension('horizontal');assert.equal(layer.items[0].b.price,100);assert.equal(layer.items[0].extend,'horizontal');
  layer.undo();assert.equal(layer.items[0].b.price,105);assert.equal(layer.items[0].extend,'right');
});

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
