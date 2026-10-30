const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const V=require('../static/candidate-view.js'),W=require('../static/workbench-view.js');
test('unknown values and intervals remain unknown, phase and horizon selected explicitly',()=>{
 assert.equal(V.value(null),'unbekannt');assert.match(V.interval({interval:{low:-1,high:2}}),/-1 bis 2/);
 assert.equal(V.interval({interval:{low:null,high:null}}),'Unsicherheit nicht bestimmbar');
 const s={groups:{all:{horizons:{20:{market:{meanExcess:1},fixed:{meanExcess:0},higher_low:{meanExcess:-1}}}}}};
 assert.deepEqual(V.metricRows(s,'all',20).map(r=>r.meanExcess),[1,0,-1]);assert.deepEqual(V.metricRows(s,'missing',20),[]);
});
test('actual candidate controller opens original chart first, future only on toggle; GET and theme survive',async()=>{
 const elements=new Map(),requests=[],drawn=[];let future=false;
 function node(){return {value:'',textContent:'',children:[],hidden:false,checked:false,clientWidth:800,append(...c){this.children.push(...c)},replaceChildren(...c){this.children=c;if(c[0]?.value)this.value=c[0].value;}};}
 function el(id){if(!elements.has(id))elements.set(id,node());return elements.get(id);}
 el('cw-state').value='active';el('cw-phase').value='all';el('cw-horizon').value='20';
 const g={id:'case',symbol:'TEST',state:'retest',contacts:3,ageDays:20,riskPct:2,riskATR:1,alternativeCount:1,bootstrap:true,warnings:['Events unbekannt']};
 const context=vm.createContext({document:{getElementById:el,createElement:node,documentElement:{dataset:{}}},ToriCandidates:V,ToriWorkbench:W,
 Date,JSON,Number,Math,Intl,URLSearchParams,encodeURIComponent,ResizeObserver:class{observe(){}},localStorage:{getItem(){return '"dark"'},setItem(){}},
 LightweightCharts:{CandlestickSeries:'candles',LineSeries:'line',createChart(){return {applyOptions(){},resize(){},removeSeries(){},addSeries(type){return {setData(rows){drawn.push({type,rows})}}},timeScale(){return {fitContent(){},setVisibleLogicalRange(){}}}}}},
 apiFetch:async(url)=>{requests.push(url);let p={items:[],page:{hasMore:false}};
 if(url==='/api/workbench/packs')p={items:[]};
 else {const u=new URL(url,'http://localhost');switch(u.pathname.split('/').pop()){
 case 'runs':p={items:[{id:'run',registeredAt:100,dataset_ids:{TEST:'dataset'}}]};break;
 case 'status':p={registeredAt:100,phase:'Wartet',progress:1,total:1,workerLockHeld:true,lanes:[]};break;
 case 'cases':p={items:[g],page:{hasMore:false,total:1},meaning:'Kein Gewinn-Score'};break;
 case 'papers':p={items:[{symbol:'TEST',entry:{entryAt:20},paths:{fixed:{status:'open',markNetR:.2}}}],page:{total:2,hasMore:Number(u.searchParams.get('offset'))===0}};break;
 case 'case':future=u.searchParams.get('future')==='1';p={case:g,cutoff:20,viewAsOf:future?30:20,futureShown:future,rays:[],bars:[{time:1,end:10},{time:10,end:20},...(future?[{time:20,end:30}]:[])]};break;
 }}return {ok:true,json:async()=>p};}});
 vm.runInContext(fs.readFileSync(require.resolve('../static/candidates.js'),'utf8'),context);
 const flush=()=>new Promise(r=>setImmediate(r));await flush();await flush();await flush();
 assert.equal(el('cw-error').hidden,true);assert.match(el('cw-status').textContent,/Worker aktiv/);
 assert.equal(context.document.documentElement.dataset.theme,'dark');
 assert.equal(el('cw-papers-count').textContent,'1 von 2 Papierpositionen geladen');
 assert.equal(el('cw-papers-more').hidden,false);await el('cw-papers-more').onclick();
 assert.equal(el('cw-papers-count').textContent,'2 von 2 Papierpositionen geladen');assert.equal(el('cw-papers-more').hidden,true);
 await el('cw-cases').children[0].onclick();assert.equal(future,false);assert.equal(drawn.at(-1).rows.length,2);
 el('cw-future').checked=true;await el('cw-future').onchange();assert.equal(future,true);assert.equal(drawn.at(-1).rows.length,3);
 el('cw-theme').onclick();assert.equal(context.document.documentElement.dataset.theme,'light');
 assert.ok(requests.every(u=>u.startsWith('/api/')));assert.ok(!requests.some(u=>u.includes('/api/chart')));
});
