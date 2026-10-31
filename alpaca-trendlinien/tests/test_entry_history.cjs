const {test}=require('node:test');
const assert=require('node:assert/strict');
const {markers,signalBar,fixedLines}=require('../static/entry-history.js');
const bars=[{time:10,end:20},{time:20,end:30},{time:40,end:50}];
const s={id:'c1',episode_id:'episode',family:'breakout',signal_at:20};
test('fixed episode produces one marker; separate entry families retain shared origin',()=>{
  const out=markers([s,{...s,id:'repeat'}, {...s,id:'ret',family:'red_retest'}],bars,50);
  assert.equal(out.length,2);assert.equal(out[0].time,10);assert.equal(out[0].shape,'arrowUp');
});
test('future signals and missing source intervals are not moved onto neighboring candles',()=>{
  assert.equal(markers([s],bars,19).length,0);
  assert.equal(signalBar(bars,35),null);
  assert.equal(signalBar(bars,20),bars[0]);
});
test('MTF display maps same event to containing daily candle and never invents a new signal',()=>{
  const daily=[{time:1,end:100}];
  assert.equal(markers([s],daily,100)[0].id,markers([s],bars,100)[0].id);
  assert.equal(markers([s],daily,100)[0].time,1);
  assert.equal(markers([s],daily,19).length,0);
});
const detail={signal:{signalAt:20,family:'breakout',initialStop:90,
  line:{id:'red',a_time:1,b_time:10,a_price:110,b_price:105},
  safety:{id:'green',a_time:2,b_time:12,a_price:85,b_price:91}}};
test('selected original geometry is immutable when replay advances and hidden before its signal',()=>{
  const before=structuredClone(detail), atSignal=fixedLines(detail,20);
  assert.deepEqual(fixedLines(detail,1000),atSignal);
  assert.deepEqual(detail,before);
  assert.equal(fixedLines(detail,19).length,0);
  assert.equal(atSignal.length,3);
});
test('safety bounce draws its green support once instead of a false red resistance',()=>{
  const bounce=structuredClone(detail);bounce.signal.family='safety_bounce';bounce.signal.line=bounce.signal.safety;
  const lines=fixedLines(bounce,20);
  assert.equal(lines.length,2);assert.equal(lines[0].color,'#059669');
});
test('dark colors improve visibility without changing historical event identity or frozen geometry',()=>{
  const light=markers([s],bars,50,'light')[0],dark=markers([s],bars,50,'dark')[0];
  assert.equal(light.id,dark.id);assert.equal(light.time,dark.time);assert.notEqual(light.color,dark.color);
  const a=fixedLines(detail,50,'light'),b=fixedLines(detail,50,'dark');
  assert.deepEqual(a.map(r=>({a:r.a,b:r.b,id:r.id})),b.map(r=>({a:r.a,b:r.b,id:r.id})));
  assert.notEqual(a[0].color,b[0].color);
});

const fs=require('node:fs'),vm=require('node:vm');
async function boot(){
  const elements=new Map(),requests=[],opens=[],storage=new Map();let controller,drawn=[],click;
  function element(id){
    if(!elements.has(id))elements.set(id,{hidden:false,disabled:false,checked:true,value:'',innerHTML:'',textContent:'',
      open:true,classList:{toggle(){}},setAttribute(){},addEventListener(){},querySelector(){return element('details');}});
    return elements.get(id);
  }
  element('entry-family').value='all';element('entry-cohort').value='all';
  const storedRun={id:'run',datasetId:'dataset',symbol:'TEST',feed:'sip',adjustment:'split',source:'event_case_study',caseCount:1,windows:[{start:'2023-01-01',end:'2023-12-31'}]};
  const state={symbol:'TEST',entryRun:null,timeframe:'4h',asOf:null,data:{datasetId:'other',analysisCutoff:100,bars,axis:bars.map(b=>b.time)}};
  const c={...structuredClone(detail),id:'c1',state:'available',entry:{status:'filled',entryAt:25,entryPrice:100,entryFill:101},review:null};
  Object.assign(c.signal,{family:'breakout',cohort:'qualified',episodeReason:'first_structure'});
  c.signal.line.contacts=3;c.signal.line.span_days=9;
  const layer={automatic:[]};
  const context=vm.createContext({console,URLSearchParams,Date,Map,Number,Set,JSON,structuredClone,
    RayGeometry:require('../static/drawings.js').RayGeometry,
    location:{search:'',pathname:'/'},history:{replaceState(){}},setTimeout,clearTimeout,
    localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    document:{getElementById:element,querySelectorAll:()=>[]},
    apiFetch:async(url,opts)=>{
      requests.push({url,opts});const params=new URLSearchParams(url.split('?')[1]);let data;
      if(url.includes('/runs?'))data={items:[storedRun]};
      else if(url.includes('/cases?'))data=params.get('quality')==='strict'?{items:[],total:0,hasMore:false,screen:{excluded:1}}:{items:[s],total:1,hasMore:false};
      else if(url.includes('/case?')){
        data=structuredClone(c);const cutoff=Date.parse(params.get('asof'))/1000;
        if(cutoff<20)data={id:'c1',state:'before_signal'};
        else if(cutoff<25)data.entry={status:'pending'};
      }else if(url.endsWith('/review'))data={saved:!JSON.parse(opts.body).delete};
      else if(url.endsWith('/search') && opts?.method==='POST')data={id:'job'};
      else if(url.includes('/search?id='))data={status:'completed',run_id:storedRun.id,request:{symbol:'TEST'},progress:{phase:'Fertig',done:1,total:1}};
      else throw Error('Unexpected '+url);
      return {ok:true,json:async()=>data};
    }});
  vm.runInContext(fs.readFileSync(require.resolve('../static/entry-history.js'),'utf8'),context);
  const ctx={state,rayLayer:layer,chart:{subscribeClick(fn){click=fn;},timeScale:()=>({setVisibleLogicalRange(){}})},
    esc:String,fmt:String,dtLong:String,setTool(){},showError(){},
    redraw(){layer.automatic=[];drawn=[];controller?.decorate(drawn);},
    async open(run,asof){opens.push({run:run.id,asof});state.entryRun=run.id;state.data.datasetId=run.datasetId;state.data.analysisCutoff=asof?Date.parse(asof)/1000:100;state.asOf=asof;controller.onRender();return true;},
    async disable(){state.entryRun=null;}};
  controller=context.EntryHistory.attach(ctx);
  await element('entry-history-toggle').onclick();await new Promise(setImmediate);
  return {elements,element,state,controller,requests,opens,layer,ctx,c,storedRun,get drawn(){return drawn;},click};
}
test('real history controller loads stored events without starting calculation; interval change reuses events',async()=>{
  const ui=await boot();assert.equal(ui.drawn.length,1);
  assert.equal(ui.requests.filter(r=>r.opts?.method==='POST').length,0);
  const before=ui.requests.length;ui.state.timeframe='1D';ui.controller.onRender();await new Promise(setImmediate);
  assert.equal(ui.requests.length,before);
});
test('chart defaults to causal structure profile and changing profile removes excluded markers and frozen lines',async()=>{
  const ui=await boot();assert.equal(ui.element('entry-quality').value,'qualified');
  assert.ok(ui.requests.some(r=>r.url.includes('/cases?') && r.url.includes('quality=qualified')));
  ui.click({hoveredObjectId:'entry:c1'});await new Promise(setImmediate);
  assert.equal(ui.layer.automatic.length,3);
  ui.element('entry-quality').value='strict';await ui.element('entry-quality').onchange();await new Promise(setImmediate);
  assert.equal(ui.drawn.length,0);assert.equal(ui.layer.automatic.length,0);
  assert.match(ui.element('entry-history-status').textContent,/1 durch das Strukturprofil ausgeschlossen/);
  ui.element('entry-quality').value='all';await ui.element('entry-quality').onchange();await new Promise(setImmediate);
  assert.equal(ui.drawn.length,1);
});
test('real controller selects original lines, jumps to signal and keeps later fill hidden',async()=>{
  const ui=await boot();
  await ui.element('entry-case-list').onclick({target:{closest:()=>({dataset:{entryCase:'c1'}})}});await new Promise(setImmediate);
  assert.equal(ui.layer.automatic.length,3);
  await ui.element('entry-replay').onclick();await new Promise(setImmediate);
  assert.equal(ui.state.timeframe,'4h');assert.equal(ui.state.data.analysisCutoff,20);
  assert.match(ui.element('entry-case-facts').innerHTML,/noch nicht bekannt/);
  assert.doesNotMatch(ui.element('entry-case-facts').innerHTML,/Modell-Entry/);
  ui.state.data.analysisCutoff=19;ui.controller.onRender();await new Promise(setImmediate);
  assert.equal(ui.layer.automatic.length,0);assert.equal(ui.element('entry-case-detail').hidden,true);
});
test('review survives candle stepping, supports save/delete and does not change signal drawing',async()=>{
  const ui=await boot();ui.click({hoveredObjectId:'entry:c1'});await new Promise(setImmediate);
  ui.element('entry-note').value='My finding';ui.element('entry-note').oninput();
  ui.state.data.analysisCutoff=200;ui.controller.onRender();await new Promise(setImmediate);
  assert.equal(ui.element('entry-note').value,'My finding');
  await ui.element('entry-review-save').onclick();assert.match(ui.element('entry-review-status').textContent,/gespeichert/);
  await ui.element('entry-review-delete').onclick();assert.equal(ui.element('entry-note').value,'');
  assert.equal(ui.layer.automatic.length,3);
});
test('projection anchors remain frozen when a later irregular axis would change extrapolation',async()=>{
  const ui=await boot();ui.c.signal.signalAt=50;ui.c.signal.line.b_time=45;
  ui.click({hoveredObjectId:'entry:c1'});await new Promise(setImmediate);
  const before=structuredClone(ui.layer.automatic[0]);
  ui.state.data.axis.push(80);ui.state.data.bars.push({time:80,end:90});
  ui.state.data.analysisCutoff=200;ui.controller.onRender();await new Promise(setImmediate);
  assert.equal(ui.layer.automatic[0].b.logical,before.b.logical);
  assert.equal(ui.layer.automatic[0].a.price,before.a.price);
  assert.equal(ui.layer.automatic[0].b.time,before.b.time);
});
test('a completed free-range calculation opens its own end instead of the previous replay date',async()=>{
  const ui=await boot();ui.state.asOf=new Date(20*1000).toISOString();
  ui.storedRun.windows=[{start:30,end:70}];
  await ui.element('entry-build').onclick();await new Promise(setImmediate);
  assert.equal(ui.state.data.analysisCutoff,70);
  assert.equal(ui.element('entry-build').disabled,false);
});
test('random practice keeps its isolated replay instead of mixing another dataset run',()=>{
  const toggle={hidden:false};
  const c=vm.createContext({location:{pathname:'/zufall'},document:{getElementById:()=>toggle}});
  vm.runInContext(fs.readFileSync(require.resolve('../static/entry-history.js'),'utf8'),c);
  assert.equal(c.EntryHistory.attach({state:{}}),null);
  assert.equal(toggle.hidden,true);
});
