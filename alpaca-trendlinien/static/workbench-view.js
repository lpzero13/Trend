(function(root){
  'use strict';
  const clone=x=>JSON.parse(JSON.stringify(x));
  function points(ray,bars){
    const a=bars.findIndex(b=>b.time===ray.a_time), b=bars.findIndex(b=>b.time===ray.b_time);
    if(a<0||b<=a)return [];
    const slope=(ray.b_price-ray.a_price)/(b-a);
    return bars.slice(a).map((bar,i)=>({time:bar.time,value:ray.a_price+i*slope}));
  }
  function model(initial=[]){
    let rays=clone(initial), history=[];
    return {get rays(){return clone(rays)},get canUndo(){return history.length>0},
      change(next){history.push(clone(rays));rays=clone(next)},
      remove(id){if(rays.some(r=>r.id===id))this.change(rays.filter(r=>r.id!==id))},
      contact(id,time){const r=rays.find(r=>r.id===id);if(!r)return;
        const next=clone(rays), n=next.find(r=>r.id===id);n.contacts=n.contacts.includes(time)?n.contacts.filter(t=>t!==time):[...n.contacts,time];this.change(next)},
      undo(){if(history.length)rays=history.pop()}};
  }
  function ray(role,a,b,id){
    if(!a||!b||a.time>=b.time||!Number.isFinite(a.price)||!Number.isFinite(b.price)||Math.min(a.price,b.price)<=0)throw Error('Zweiten Anker rechts vom ersten wählen.');
    return {id,role,a_time:a.time,a_price:a.price,b_time:b.time,b_price:role==='resistance'?a.price:b.price,contacts:[a.time,b.time]};
  }
  const api={points,model,ray};root.ToriWorkbench=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
