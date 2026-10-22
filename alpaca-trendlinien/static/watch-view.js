(function(root){
  const models={hull_exact:"Strenge Hülle",swing_zone:"Kontaktzone"};
  const phases={near:"Annäherung",breakout:"Ausbruch",pullback:"Rücklauf",retest:"Retest bestätigt",bounce:"Grün-Reaktion"};
  function label(key){return models[key]||phases[key]||({interesting:"Interessant",unclear:"Unklar",reject:"Ablehnen"})[key]||key;}
  function rayPoints(ray,bars,firstIndex){
    if(!ray)return [];
    return bars.map((bar,i)=>({time:bar.time,value:ray.a_price+ray.slope*(firstIndex+i-ray.a_index)}));
  }
  function clock(at){return at==null?"—":new Date(at*1000).toLocaleString("de-DE",{timeZone:"America/New_York",hour12:false})+" ET";}
  function verdictContext(everUnblinded){return everUnblinded?"Späterer Verlauf wurde in dieser Sicht bereits geöffnet.":"Urteil ohne spätere Verlaufssicht.";}
  function outcomeText(records){
    if(!records.length)return "Noch kein nach Beobachtungsbeginn ausgeführter Retest-Entry für diese Linie.";
    return records.map(r=>["Entry: "+clock(r.entry.entryAt)+" · "+r.entry.entryPrice.toFixed(2)+" USD · Stop "+r.entry.initialStop.toFixed(2),
      "Vollständige relevante Vorgeschichte: "+(r.history.complete?"ja":"nein – eingeschränkte Aussage"),
      ...Object.entries(r.paths).map(([name,p])=>(name==="fixed"?"Feste Safety":"ATR-Schutz")+": "+(p.status==="closed"?p.netR.toFixed(3)+"R · "+p.netReturnPct.toFixed(2)+" % · "+p.exitReason:p.reason==="phase_boundary"?"noch offen / unvollständig beobachtet":"ungeklärt · "+(p.reason||p.status)))].join("\n")).join("\n\n");
  }
  const api={label,rayPoints,clock,verdictContext,outcomeText};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  root.WatchView=api;
})(typeof window!=="undefined"?window:globalThis);
