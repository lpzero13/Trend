const {test}=require('node:test');
const assert=require('node:assert/strict');
const {Prefetch,updateSeries}=require('../static/replay-buffer.js');
const flush=()=>new Promise(setImmediate);
function series(){const s={rows:[],calls:[],setData(rows){s.rows=[...rows];s.calls.push('replace');},update(row){s.rows.push(row);s.calls.push('append');},pop(n){s.rows.splice(-n);s.calls.push('remove');}};return s;}
test('one candle appends or pops; earlier OHLC corrections and interval resets replace safely',()=>{
 const s=series(),a=[{time:1,open:10,high:12,low:9,close:11}],b=[...a,{time:2,open:11,high:13,low:10,close:12}];
 assert.equal(updateSeries(s,a),'replace');assert.equal(updateSeries(s,b),'append');
 assert.equal(updateSeries(s,b),'unchanged');assert.equal(updateSeries(s,a),'remove');assert.deepEqual(s.rows,a);
 assert.equal(updateSeries(s,[{...a[0],high:14}]),'replace');assert.equal(updateSeries(s,a,true),'replace');
});
test('whitespace/SMA value changes also invalidate the incremental prefix',()=>{
 const s=series();updateSeries(s,[{time:1}]);assert.equal(updateSeries(s,[{time:1,value:100}]),'replace');
 assert.equal(updateSeries(s,[{time:1,value:100},{time:2,value:101}]),'append');
});
function harness(){
 let context='AAPL|4h|master',displayed=10;
 const pending=[],stored=[],calls=[];
 const h=new Prefetch({context:()=>context,radius:2,schedule:f=>pending.push(f),
  target:async(base,dir)=>{calls.push([base.analysisCutoff,dir]);const at=base.analysisCutoff+(dir==='back'?-1:1);return {closedAt:at,asof:String(at)};},
  fetch:async target=>({analysisCutoff:target.closedAt}),store:(target,data)=>stored.push(data.analysisCutoff)});
 return {h,pending,stored,calls,setContext:v=>context=v,displayed:()=>displayed};
}
test('preparation is bounded and never changes the displayed cutoff; prepared targets need no step request',async()=>{
 const x=harness();x.h.prime({analysisCutoff:10});await x.pending.shift()();
 assert.deepEqual([...x.stored].sort((a,b)=>a-b),[8,9,11,12]);assert.equal(x.displayed(),10);
 const count=x.calls.length;assert.equal((await x.h.resolve({analysisCutoff:10},'next')).closedAt,11);assert.equal(x.calls.length,count);
 x.h.prime({analysisCutoff:10});assert.equal(x.pending.length,0);
});
test('another symbol/model/dataset discards an in-flight prepared view',async()=>{
 const y=harness();let unlock;const barrier=new Promise(r=>unlock=r);y.h.fetch=async t=>{await barrier;return {analysisCutoff:t.closedAt};};
 y.h.prime({analysisCutoff:10});const run=y.pending.shift()();await flush();y.setContext('OTHER');unlock();await run;
 assert.deepEqual(y.stored,[]);
});
test('refresh invalidates prepared targets and failures do not replace the chart',async()=>{
 const x=harness();x.h.fetch=async()=>{throw Error('offline');};x.h.prime({analysisCutoff:10});await x.pending.shift()();
 assert.deepEqual(x.stored,[]);x.h.clear();assert.equal(x.h.cachedTarget({analysisCutoff:10},'next'),null);
});
test('rapid stepping queues only the newest preparation and at most two background requests',async()=>{
 const x=harness();let running=0,max=0,unlock;const barrier=new Promise(r=>unlock=r);
 x.h.fetch=async t=>{running++;max=Math.max(max,running);await barrier;running--;return {analysisCutoff:t.closedAt};};
 x.h.prime({analysisCutoff:10});const first=x.pending.shift()();await flush();
 for(const at of [11,12,13]){x.h.prime({analysisCutoff:at});await x.pending.shift()();}
 assert.equal(max,2);unlock();await first;
 assert.equal(x.pending.length,1);await x.pending.shift()();assert.equal(max,2);
});
