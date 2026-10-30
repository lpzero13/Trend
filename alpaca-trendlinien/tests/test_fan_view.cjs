const {test}=require('node:test');
const assert=require('node:assert/strict');
const V=require('../static/fan-view.js');
test('case chart links carry pinned dataset, engine, case and explicit source time',()=>{
 const c={id:'a'.repeat(64),datasetId:'b'.repeat(64),symbol:'MSFT',timeframe:'4h',geometry:'local',signal:{signalAt:1700000000}};
 const u=new URL(V.chartLink(c,'c'.repeat(32)),'http://localhost');
 assert.equal(u.searchParams.get('engine'),'fan_local');assert.equal(u.searchParams.get('fan_case'),c.id);
 assert.equal(Date.parse(u.searchParams.get('asof'))/1000,c.signal.signalAt);
 assert.equal(Date.parse(new URL(V.chartLink({...c,signal:undefined},'job',1600000000),'http://localhost').searchParams.get('asof'))/1000,1600000000);
});
test('result rendering distinguishes trials and unique signals, unknown paths and escapes provider text',()=>{
 const text=V.groups({groups:[{geometry:'extreme',variant:'retest',cohort:'qualified',uniqueSignals:1,entryStates:{filled:1},origins:42,selectedUniqueSignals:1,originStates:{filled:42},paths:{'fixed:20':{states:{censored:1},closedOnlyMeanReturnPct:null,ambiguous:0}}}]});
 assert.match(text,/42 Starts \/ 1 verschiedene Signale/);assert.match(text,/Verlauf unvollständig/);assert.match(text,/— %/);
 assert.equal(V.esc('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;');
 const c={kind:'origin',id:'x',datasetId:'b'.repeat(64),symbol:'<script>',geometry:'extreme',timeframe:'4h',startAt:1700000000,atStart:{trackedScenarios:0},selections:[{variant:'breakout',cohort:'two',status:'unknown_source_gap',entryId:null}]};
 const html=V.cases([c],'job');assert.ok(!html.includes('<script>'));assert.match(html,/Datenlücke ungeklärt/);
});
