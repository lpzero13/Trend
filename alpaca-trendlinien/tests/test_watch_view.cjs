const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const view=require('../static/watch-view.js');

test('frozen source ray remains straight across weekends and nonuniform timestamp gaps',()=>{
  const points=view.rayPoints({a_index:20,a_price:100,slope:.5},[{time:100},{time:900},{time:300000}],21);
  assert.deepEqual(points.map(p=>p.value),[100.5,101,101.5]);
  assert.deepEqual(points.map(p=>p.time),[100,900,300000]);
});

test('unknown paths and phase-boundary observations are never labelled as profits',()=>{
  const records=[{entry:{entryAt:100,entryPrice:100,initialStop:95},history:{complete:false},paths:{fixed:{status:'censored',reason:'phase_boundary'},atr_gain_stop:{status:'censored',reason:'missing_fine_path'}}}];
  const text=view.outcomeText(records);
  assert.match(text,/noch offen/);assert.match(text,/ungeklärt/);assert.match(text,/eingeschränkte Aussage/);
  assert.doesNotMatch(text,/NaN|undefined/);
});

test('actual controller opens original state first and remembers revealed future after toggling back',async()=>{
  const elements=new Map();const requests=[];const candleRows=[];
  function el(key){if(!elements.has(key))elements.set(key,{value:'',checked:false,hidden:false,disabled:false,dataset:{},textContent:'',children:[],replaceChildren(){this.children=[];},append(...children){this.children.push(...children);}});return elements.get(key);}
  const c={id:'a'.repeat(64),symbol:'TEST',model:'hull_exact',phase:'retest',knownAt:100,daily:'up',weekly:'mixed',explanation:'<script>untrusted</script>',red:{a_index:0,a_price:110,slope:-1},green:{a_index:0,a_price:90,slope:1}};
  const data={case:c,datasetId:'dataset',asOf:100,firstIndex:0,bars:[{time:1,end:2,open:100,high:101,low:99,close:100}],records:[]};
  const context=vm.createContext({document:{querySelector:el,createElement:tag=>el('element-'+elements.size),documentElement:{dataset:{}}},
    WatchView:view,URLSearchParams,Date,JSON,localStorage:{getItem(){return '"dark"';},setItem(){}},setInterval(){},
    LightweightCharts:{CandlestickSeries:'candles',LineSeries:'line',createChart(){return {addSeries(type){return {setData(rows){if(type==='candles')candleRows.push(rows);}};},timeScale(){return {fitContent(){}};},remove(){}};}},
    apiFetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/api/watch/status'?{configured:false}:url.endsWith('/review')?{saved:true}:{...data,view:url.includes('latest')?'latest':'signal'}};}});
  vm.runInContext(fs.readFileSync(require.resolve('../static/watch.js'),'utf8'),context);
  await vm.runInContext('openCase('+JSON.stringify(c)+')',context);
  assert.match(requests.at(-1).url,/view=signal$/);
  assert.equal(el('#watch-outcomes').hidden,true);
  assert.equal(el('#watch-explanation').textContent,c.explanation);
  assert.equal(candleRows.length,1);
  el('#watch-latest').checked=true;await el('#watch-latest').onchange();
  el('#watch-latest').checked=false;await el('#watch-latest').onchange();
  el('#watch-verdict').value='interesting';el('#watch-note').value='manual';
  await el('#watch-review').onsubmit({preventDefault(){}});
  assert.equal(JSON.parse(requests.at(-1).options.body).unblinded,true);
  assert.equal(el('#watch-saved').textContent,' Gespeichert');
  assert.equal(context.document.documentElement.dataset.theme,'dark');
});
