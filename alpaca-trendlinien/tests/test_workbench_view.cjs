const test=require('node:test'),assert=require('node:assert/strict');
const V=require('../static/workbench-view.js');
const fs=require('node:fs'),vm=require('node:vm');
test('rays stay straight across calendar pauses on compressed source positions',()=>{
 const bars=[{time:1},{time:5},{time:100},{time:1000}];
 const r=V.ray('red',{time:1,price:100},{time:5,price:99},'x');
 assert.deepEqual(V.points(r,bars).map(p=>p.value),[100,99,98,97]);
});
test('actual review controller saves drawings, deletes/undoes, then explicitly reveals without future bars',async()=>{
 const elements=new Map(),requests=[],tools=['red','green','resistance','contact'].map(t=>({dataset:{tool:t},setAttribute(){},addEventListener(e,fn){this.click=fn}}));
 function el(id){if(!elements.has(id))elements.set(id,{value:'',textContent:'',hidden:false,disabled:false,dataset:{},children:[],replaceChildren(...children){this.children=children;this.value=children[0]?.value||''}});return elements.get(id)}
 let clicks,drawn=[],serial=0;
 let data={id:'c'.repeat(24),packId:'a'.repeat(32),symbol:'TEST',timeframe:'1D',feed:'sip',adjustment:'split',cutoff:20,label:null,blindLabel:null,revision:0,revealed:false,tainted:false,bars:[{time:1,end:10,open:99,high:101,low:98,close:100},{time:10,end:20,open:100,high:102,low:99,close:101}],futureAvailable:false};
 const context=vm.createContext({document:{getElementById:el,createElement(){return {value:'',textContent:''}},querySelectorAll(){return tools},documentElement:{dataset:{}}},ToriWorkbench:V,
  LightweightCharts:{CandlestickSeries:'candles',LineSeries:'line',createSeriesMarkers(){return {setMarkers(){}}},createChart(){return {addSeries(type){return {setData(rows){drawn.push({type,rows})},coordinateToPrice(y){return y}}},removeSeries(){},remove(){},subscribeClick(fn){clicks=fn},timeScale(){return {fitContent(){}}}}}},
  Date,JSON,Number,Math,URLSearchParams,location:{search:'?pack='+data.packId},crypto:{randomUUID(){return 'test'+(++serial)}},localStorage:{getItem(){return '"dark"'},setItem(){}},addEventListener(){},
  apiFetch:async(url,opts)=>{requests.push({url,opts});let out;
   if(url==='/api/workbench/packs')out={items:[{id:data.packId,label:'Test',count:1}]};
   else if(url.includes('?offset='))out={items:[{id:data.id,symbol:'TEST',timeframe:'1D',cutoff:20}],page:{hasMore:false}};
   else if(url.endsWith('/compare'))out={humanLabels:data.label?1:0,geometry:[]};
   else if(url.endsWith('/label')){const b=JSON.parse(opts.body);data={...data,revision:data.revision+1,label:{verdict:b.verdict,note:b.note,rays:b.rays}};out=data;}
   else if(url.endsWith('/reveal')){data={...data,revealed:true,revision:data.revision+1,engine:{rays:[],resistances:[105]}};out=data;}
   else out=data;return {ok:true,json:async()=>JSON.parse(JSON.stringify(out))};}});
 vm.runInContext(fs.readFileSync(require.resolve('../static/workbench.js'),'utf8'),context);
 const flush=()=>new Promise(r=>setImmediate(r));await flush();await flush();
 assert.equal(el('wb-error').hidden,true);assert.match(el('wb-meta').textContent,/1D.*SIP/);
 assert.equal(drawn.filter(x=>x.type==='line').length,0);assert.equal(el('wb-reveal').disabled,true);
 tools.find(t=>t.dataset.tool==='green').click();await clicks({time:1,point:{y:98}});await clicks({time:10,point:{y:99}});
 assert.equal(el('wb-ray').children.length,1);el('wb-delete').onclick();assert.equal(el('wb-ray').children.length,0);
 el('wb-undo').onclick();assert.equal(el('wb-ray').children.length,1);
 el('wb-note').value='Dritter Kontakt fehlt noch';el('wb-note').oninput();await el('wb-form').onsubmit({preventDefault(){}});
 const body=JSON.parse(requests.find(r=>r.url.endsWith('/label')).opts.body);assert.equal(body.rays.length,1);assert.equal(body.rays[0].role,'green');assert.equal(body.revision,0);
 assert.equal(el('wb-reveal').disabled,false);await el('wb-reveal').onclick();assert.match(el('wb-state').textContent,/aufgedeckt/);
 assert.ok(drawn.filter(x=>x.type==='candles').every(x=>x.rows.every(b=>b.end<=20)));
 assert.equal(context.document.documentElement.dataset.theme,'dark');
});
test('horizontal resistance, contact toggle, delete and multi-step undo preserve exact anchors',()=>{
 const r=V.ray('resistance',{time:1,price:100},{time:5,price:110},'x');
 assert.equal(r.b_price,100);const m=V.model([r]);
 m.contact('x',10);assert.deepEqual(m.rays[0].contacts,[1,5,10]);
 m.contact('x',10);assert.deepEqual(m.rays[0].contacts,[1,5]);
 m.remove('x');assert.equal(m.rays.length,0);m.undo();m.undo();assert.deepEqual(m.rays[0].contacts,[1,5,10]);
 m.undo();assert.deepEqual(m.rays,[r]);assert.equal(m.canUndo,false);
 const copy=m.rays;copy[0].a_price=1000;assert.equal(m.rays[0].a_price,100);
 assert.throws(()=>V.ray('red',{time:5,price:100},{time:1,price:99},'x'));
});
