/* Prepared views stay separate from the displayed cutoff. No signal calculation here. */
(function(root){
  'use strict';
  const previous=new WeakMap();
  const fields=['time','open','high','low','close','value'];
  function updateSeries(series,rows,reset=false){
    const old=previous.get(series);
    let same=!!old && !reset;
    if(same)for(let i=0;i<Math.min(old.length,rows.length);i++){
      if(fields.some(k=>old[i][k]!==rows[i][k])){same=false;break;}
    }
    let mode='replace';
    if(same && old.length===rows.length)mode='unchanged';
    else if(same && rows.length===old.length+1 && typeof series.update==='function'){
      series.update(rows.at(-1));mode='append';
    }else if(same && rows.length===old.length-1 && typeof series.pop==='function'){
      series.pop(1);mode='remove';
    }else series.setData(rows);
    previous.set(series,rows);
    return mode;
  }

  class Prefetch {
    constructor({context,target,fetch,store,status=()=>{},schedule=fn=>setTimeout(fn,80),radius=3}){
      Object.assign(this,{context,target,fetch,store,status,schedule,radius});
      this.targets=new Map();this.epoch=0;this.task=0;this.last=null;
      this.running=false;this.queued=null;
    }
    clear(){this.epoch++;this.task++;this.last=null;this.targets.clear();this.queued=null;}
    // Context is a stable string. The cutoff and current interval are supplied by the caller.
    targetKey(base,direction){return this.context()+'|'+base.analysisCutoff+'|'+direction;}
    cachedTarget(base,direction){return this.targets.get(this.targetKey(base,direction)) || null;}
    async resolve(base,direction){
      const key=this.targetKey(base,direction),rootContext=this.context(),epoch=this.epoch;
      if(this.targets.has(key))return this.targets.get(key);
      const target=await this.target(base,direction);
      if(epoch!==this.epoch || rootContext!==this.context())return null;
      this.targets.set(key,target);
      while(this.targets.size>64)this.targets.delete(this.targets.keys().next().value);
      return target;
    }
    prime(base){
      if(!base)return;
      const rootContext=this.context(),key=rootContext+'|'+base.analysisCutoff;
      if(key===this.last)return;
      this.last=key;const ticket=++this.task,epoch=this.epoch;
      const active=()=>epoch===this.epoch && ticket===this.task && rootContext===this.context();
      this.schedule(async()=>{
        if(!active())return;
        if(this.running){this.queued={base,rootContext,epoch};return;}
        this.running=true;
        this.status('preparing');let preparedCount=0;
        await Promise.all(['back','next'].map(async direction=>{
          let source=base;
          for(let i=0;i<this.radius && active();i++){
            try{
              const target=await this.resolve(source,direction);
              if(!target || !active())break;
              const prepared=await this.fetch(target);
              // A navigation inside the same instrument may reuse completed work;
              // another symbol/model/dataset or refresh may not publish stale work.
              if(epoch!==this.epoch || rootContext!==this.context())break;
              if(prepared.analysisCutoff!==target.closedAt)throw Error('Replay-Zeitpunkt stimmt nicht überein.');
              this.store(target,prepared);source=prepared;preparedCount++;
              if(active())this.status('preparing',preparedCount);
            }catch{break;} // Preparation never replaces the current chart with an error.
          }
        }));
        if(active())this.status(preparedCount?'ready':'idle',preparedCount);
        this.running=false;
        const queued=this.queued;this.queued=null;
        if(queued && queued.rootContext===this.context() && queued.epoch===this.epoch){this.last=null;this.prime(queued.base);}
      });
    }
  }
  const api={Prefetch,updateSeries};
  if(typeof module!=='undefined')module.exports=api;
  root.ReplayBuffer=api;
})(typeof globalThis!=='undefined'?globalThis:window);
