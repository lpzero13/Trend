const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../static/collector.js'),'utf8');
const html=fs.readFileSync(require.resolve('../static/collector.html'),'utf8');
function app(){
 const nodes=new Map();const calls=[];
 const node=s=>{if(!nodes.has(s))nodes.set(s,{value:'',innerHTML:'',textContent:'',hidden:false,disabled:false});return nodes.get(s);};
 const context={document:{querySelector:node},console,URL,Date,Set,Map,URLSearchParams,Promise,setInterval:()=>0,
  apiFetch:async(url,options)=>{calls.push({url,options});let data={};if(url==='/api/archive/universes')data={items:[{id:'dow30',name:'Dow <x>',ready:true,count:30,asOf:'2026-10-28'}]};else if(url==='/api/archive/jobs'&&!options)data={items:[],legacy:[]};else if(url.startsWith('/api/archive/preview'))data={uniqueStocks:30,existingStocks:10,newStocks:20,estimate:{seconds:600,lowSeconds:420,highSeconds:840,combinedBytes:1073741824}};return{ok:true,json:async()=>data};}};
 vm.createContext(context);vm.runInContext(source,context);
 return{context,calls,node};
}
test('collector starts offline with unselected universes and never starts an import automatically',async()=>{
 const a=app();await new Promise(setImmediate);
 assert.ok(a.calls.every(c=>!c.options));assert.ok(!a.calls.some(c=>c.url.endsWith('/start')));
 assert.ok(!a.node('#universe-list').innerHTML.includes('<x>'));assert.match(a.node('#universe-list').innerHTML,/&lt;x&gt;/);
 assert.match(html,/datetime-local/);assert.match(html,/id="collector-adopt"/);
});
test('empty submit is blocked; selection previews only and cannot trigger a price download',async()=>{
 const a=app();await new Promise(setImmediate);
 await a.node('#collector-form').onsubmit({preventDefault(){}});
 assert.match(a.node('#collector-error').textContent,/mindestens ein Universum/);
 await a.node('#universe-list').onchange({target:{dataset:{universe:'dow30'},checked:true}});
 assert.match(a.node('#collector-preview').textContent,/30 verschiedene/);
 assert.match(a.node('#collector-estimate').textContent,/10 Min/);
 assert.match(a.node('#collector-estimate').textContent,/1.00 GiB/);
 assert.ok(a.calls.every(c=>!c.options));
});
