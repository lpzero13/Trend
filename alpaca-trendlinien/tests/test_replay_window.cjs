const {test}=require('node:test');
const assert=require('node:assert/strict');
const {Client}=require('../static/replay-window.js');
function fixture(id='a'.repeat(32),symbol='TEST'){
  const rows=Array.from({length:40},(_,i)=>({time:1000+i*3600,end:4600+i*3600,open:i+100,high:i+102,low:i+99,close:i+101,volume:1}));
  const window={id,symbol,through:rows.at(-1).end,bars:Object.fromEntries(['1h','4h','1D'].map(tf=>[tf,rows]))};
  const compact=(at,analysis=true)=>{
    const count=rows.filter(b=>b.end<=at).length;
    return {symbol,replaySession:id,analysisCutoff:at,timeframe:'4h',analysisEnabled:analysis,
      charts:Object.fromEntries(['1h','4h','1D'].map(tf=>[tf,{reference:rows[count-1].time}])),
      chartCounts:Object.fromEntries(['1h','4h','1D'].map(tf=>[tf,count])),
      lanes:analysis?{'4h':{green:{value:rows[count-1].low}}}:{}};
  };
  return {window,compact,rows};
}
const config=(at,extra={})=>({symbol:'TEST',timeframe:'4h',analysis:'1',engine:'legacy',...(at?{asof:new Date(at*1000).toISOString()}:{}),...extra});

test('one quote window supports distant jumps and repeated per-candle movement without step/data downloads',async()=>{
  const f=fixture(),calls=[];
  const client=new Client(async path=>{
    calls.push(path);const q=new URL(path,'http://local').searchParams;
    const at=q.has('asof')?Date.parse(q.get('asof'))/1000:f.rows[20].end;
    return path.includes('/open?')?{window:f.window,view:f.compact(at)}:f.compact(at);
  });
  let view=await client.request(config(f.rows[20].end));
  assert.equal(view.bars.length,21);assert.equal(view.lanes['4h'].sourceTimes.length,21);
  for(const i of [5,6,7,12,18,17,25,24,23,22,21]){
    view=await client.request(config(f.rows[i].end));
    assert.equal(view.bars.length,i+1);assert.equal(view.lanes['4h'].green.value,f.rows[i].low);
    assert.ok(Object.values(view.charts).every(c=>c.bars.every(b=>b.end<=view.analysisCutoff)));
  }
  assert.equal(calls.filter(p=>p.includes('/open?')).length,1);
  assert.equal(client.target(view,'4h','next').closedAt,f.rows[22].end);
  assert.equal(client.target(view,'4h','back').closedAt,f.rows[20].end);
  assert.equal(client.target({...view,analysisCutoff:f.rows[21].end+1},'4h','back').closedAt,f.rows[21].end);
});

test('preloaded future quotes and future SMA values never enter a causal view; malformed counts rejected',()=>{
  const f=fixture(),client=new Client(()=>{}),p=f.compact(f.rows[10].end);
  f.window.smas={'4h':{'50':f.rows.map(b=>({time:b.time,value:b.close}))}};
  p.lanes['4h'].context={seriesCounts:{'50':11}};
  const view=client.hydrate(p,f.window);
  assert.equal(view.lanes['4h'].context.series['50'].length,11);
  p.chartCounts['1D']=12;assert.throws(()=>client.hydrate(p,f.window),/Zukunftsgrenze/);
  p.chartCounts['1D']=11;p.lanes['4h'].context.seriesCounts['50']=12;
  assert.throws(()=>client.hydrate(p,f.window),/SMA-Zukunftsgrenze/);
});

test('manual views retain only known canonical SMA gap resets without enabling analysis',()=>{
  const f=fixture(),client=new Client(()=>{}),p=f.compact(f.rows[10].end,false);
  f.window.smas={'4h':{'200':[{time:f.rows[2].time},{time:f.rows[5].time,value:105},{time:f.rows[20].time}]}};
  const view=client.hydrate(p,f.window);
  assert.deepEqual(view.smaGaps,[f.rows[2].time]);
  assert.deepEqual(view.lanes,{});
  assert.deepEqual(client.hydrate(f.compact(f.rows[1].end,false),f.window).smaGaps,[]);
});

test('turning analysis on for an already loaded live stock reuses its quote window',async()=>{
  const f=fixture(),calls=[];
  const client=new Client(async path=>{calls.push(path);return path.includes('/open?')?{window:f.window,view:f.compact(f.rows[20].end,false)}:f.compact(f.rows[20].end);});
  await client.request(config(null,{analysis:'0'}));await client.request(config(null));
  assert.equal(calls.filter(p=>p.includes('/open?')).length,1);
  assert.match(calls[1],/historical=0/);
});

test('evicted server session reacquires a whole version and never merges revised quotes',async()=>{
  const a=fixture(),b=fixture('b'.repeat(32));b.rows[0].close=999;
  let opens=0;
  const client=new Client(async path=>{
    if(path.includes('/open?')){const f=opens++?b:a;return {window:f.window,view:f.compact(f.rows[20].end)};}
    const error=Error('expired');error.status=410;throw error;
  });
  await client.request(config(a.rows[20].end));const view=await client.request(config(a.rows[21].end));
  assert.equal(opens,2);assert.equal(view.replaySourceId,b.window.id);assert.equal(view.bars[0].close,999);
});

test('a delayed old stock response cannot replace the newer active quote window',async()=>{
  const a=fixture(),b=fixture('b'.repeat(32),'OTHER');let release;
  const client=new Client(async path=>{
    if(path.includes('symbol=TEST'))await new Promise(resolve=>release=resolve);
    const f=path.includes('symbol=TEST')?a:b;return {window:f.window,view:f.compact(f.rows[20].end)};
  });
  const old=client.request(config(a.rows[20].end));
  await client.request(config(b.rows[20].end,{symbol:'OTHER'}));release();await old;
  assert.equal(client.current.window.symbol,'OTHER');
});

test('a failed refresh keeps the previous usable quote window',async()=>{
  const f=fixture();let fail=false;
  const client=new Client(async path=>{if(fail)throw Error('offline');return {window:f.window,view:f.compact(f.rows[20].end)};});
  await client.request(config(f.rows[20].end));fail=true;
  await assert.rejects(client.request(config(f.rows[20].end,{refresh:'1'})),/offline/);
  assert.equal(client.current.window.id,f.window.id);
});
