const test = require('node:test');
const assert = require('node:assert/strict');
const {escape,rayPoints,groupsFor} = require('../static/lab.js');

test('manual review rays remain straight across closed sessions on the candle axis', () => {
  const bars = [{time:1},{time:2},{time:200},{time:201}];
  const points = rayPoints({a_time:1,a_price:100,b_time:200,b_price:104},bars);
  assert.deepEqual(points.map(p => p.value),[100,102,104,106]);
  assert.deepEqual(points.map(p => p.time),[1,2,200,201]);
  assert.deepEqual(rayPoints({a_time:200,a_price:100,b_time:2,b_price:104},bars),[]);
  assert.deepEqual(rayPoints(null,bars),[]);
});

test('development, final test and hypothetical rejections never share the selected result group', () => {
  const entry = {kind:'entries',horizons:{10:{n:1,mean_return_pct:2}}};
  const rejected = {kind:'hypothetical_rejected',horizons:{10:{n:1,mean_return_pct:20}}};
  const summary = {sections:{development:{groups:{a:entry,b:rejected}},holdout:{groups:{a:{...entry,horizons:{10:{n:1,mean_return_pct:-8}}}}}}};
  assert.equal(groupsFor(summary,'development',10,'entries')[0].outcome.mean_return_pct,2);
  assert.equal(groupsFor(summary,'holdout',10,'entries')[0].outcome.mean_return_pct,-8);
  assert.equal(groupsFor(summary,'development',10,'hypothetical_rejected')[0].outcome.mean_return_pct,20);
  assert.deepEqual(groupsFor(summary,'missing',10,'entries'),[]);
});

test('research labels and provider strings cannot inject markup into tables', () => {
  assert.equal(escape('<img src=x onerror="bad()">'), '&lt;img src=x onerror=&quot;bad()&quot;&gt;');
  assert.equal(escape(null),'');
});
