/* Quote transport is separate from the causal view. No line finder in JavaScript. */
(function(root){
  'use strict';
  function upper(rows,at){
    let lo=0,hi=rows.length;
    while(lo<hi){const mid=(lo+hi)>>>1;if(rows[mid].end<=at)lo=mid+1;else hi=mid;}
    return lo;
  }
  class Client {
    constructor(fetch){this.fetch=fetch;this.current=null;this.pending=new Map();this.epoch=0;this.openTicket=0;}
    clear(){this.epoch++;this.current=null;this.pending.clear();}
    scope(config){return JSON.stringify([config.symbol,config.dataset || null,config.random || null]);}
    target(base,tf,direction){
      const current=this.current;
      if(!current || current.window.id!==base.replaySession)return null;
      const rows=current.window.bars[tf];if(!rows)return null;
      let i=upper(rows,base.analysisCutoff);
      if(direction==='back'){if(i && rows[i-1].end===base.analysisCutoff)i--;i--;}
      if(i<0 || i>=rows.length)return null;
      const closedAt=rows[i].end;
      if(['1h','4h','1D'].some(tf=>upper(current.window.bars[tf],closedAt)<3))return null;
      return {closedAt,asof:new Date(closedAt*1000).toISOString(),timeframe:tf};
    }
    hydrate(compact,window){
      if(compact.replaySession!==window.id)throw Error('Replay-Datenstand stimmt nicht überein.');
      const charts={},lanes=structuredClone(compact.lanes || {});
      for(const [tf,count] of Object.entries(compact.chartCounts)){
        const all=window.bars[tf];
        if(!all || !Number.isInteger(count) || count!==upper(all,compact.analysisCutoff))throw Error('Ungültige Replay-Zukunftsgrenze.');
        const bars=all.slice(0,count),axis=bars.map(b=>b.time);
        charts[tf]={...compact.charts[tf],bars,axis};
        // Canonical SMA whitespace marks a source-gap reset. Retain only known
        // resets so the independent chart overlay follows the research context.
        charts[tf].smaGaps=(window.smas?.[tf]?.['200'] || [])
          .filter(row=>row.time<=bars.at(-1).time && !Number.isFinite(row.value)).map(row=>row.time);
        if(lanes[tf]){
          lanes[tf].sourceTimes=axis;
          if(lanes[tf].context?.seriesCounts){
            const context=lanes[tf].context;context.series={};
            for(const [n,count] of Object.entries(context.seriesCounts)){
              const values=window.smas?.[tf]?.[n];
              if(!values || count>values.length)throw Error('Replay-SMA-Daten fehlen.');
              context.series[n]=values.slice(0,count);
              if(context.series[n].some(v=>v.time>bars.at(-1).time))throw Error('Ungültige Replay-SMA-Zukunftsgrenze.');
            }
            delete context.seriesCounts;
          }
        }
      }
      const result={...compact,charts,lanes,...charts[compact.timeframe],replaySourceId:window.id};
      if(compact.drawingAxisTails){
        result.drawingAxes=Object.fromEntries(Object.entries(compact.drawingAxisTails).map(([tf,tail])=>
          [tf,[...charts[tf].axis,...tail]]));
        delete result.drawingAxisTails;
      }
      return result;
    }
    async request(config){
      const scope=this.scope(config),epoch=this.epoch,at=config.asof?Date.parse(config.asof)/1000:null;
      const active=this.current;
      const covered=active && active.scope===scope && (at===null || at<=active.window.through) &&
        (at===null || ['1h','4h','1D'].every(tf=>upper(active.window.bars[tf],at)>=3));
      if(!covered || config.refresh==='1' || at===null && Date.now()-active.openedAt>=300000){
        const ticket=++this.openTicket;
        const opened=await this.fetch('/api/replay/open?'+new URLSearchParams(config));
        if(epoch===this.epoch && ticket===this.openTicket)this.current={scope,window:opened.window,at:opened.view.analysisCutoff,openedAt:Date.now()};
        return this.hydrate(opened.view,opened.window);
      }
      const params=new URLSearchParams({session:active.window.id,timeframe:config.timeframe,
        asof:config.asof || new Date(active.at*1000).toISOString(),analysis:config.analysis,
        historical:config.asof?'1':'0',engine:config.engine || 'legacy'});
      const key=params.toString();
      if(this.pending.has(key))return this.pending.get(key);
      const task=(async()=>{
        try{return this.hydrate(await this.fetch('/api/replay/view?'+params),active.window);}
        catch(error){
          if(error.status!==410)throw error;
          if(this.current===active)this.current=null;
          try{return await this.request(config);}
          catch(failure){if(this.current===null)this.current=active;throw failure;}
        }
      })();
      this.pending.set(key,task);
      try{return await task;}finally{if(this.pending.get(key)===task)this.pending.delete(key);}
    }
  }
  const api={Client,upper};
  if(typeof module!=='undefined')module.exports=api;
  root.ReplayWindow=api;
})(typeof globalThis!=='undefined'?globalThis:window);
