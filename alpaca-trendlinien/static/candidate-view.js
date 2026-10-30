(function(root){
  'use strict';
  const states={approaching:'Annäherung',breakout:'Ausbruch',retest:'Retest',bounce:'Safety-Reaktion',invalid:'Ungültige Geometrie',unclear:'Unklar / ausgesetzt'};
  function value(n,suffix=''){return Number.isFinite(n)?new Intl.NumberFormat('de-DE',{maximumFractionDigits:2}).format(n)+suffix:'unbekannt';}
  function interval(m){return m?.interval?.low==null?'Unsicherheit nicht bestimmbar':`${value(m.interval.low)} bis ${value(m.interval.high)}`;}
  function metricRows(summary,phase,horizon){
    const group=summary?.groups?.[phase];if(!group)return [];
    return ['market','fixed','higher_low'].map(kind=>({kind,...group.horizons[String(horizon)][kind]}));
  }
  function selected(groups,id){return groups.find(g=>g.id===id)||null;}
  const api={states,value,interval,metricRows,selected};root.ToriCandidates=api;
  if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
