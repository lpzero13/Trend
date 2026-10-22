const $=s=>document.querySelector(s), V=WatchView;
let active=null,everUnblinded=false,chart=null,queryPage=null,selection=0,listed=0,loading=false;
let theme;
try{theme=JSON.parse(localStorage.getItem("tori-theme"))||"light";}catch{theme="light";}
document.documentElement.dataset.theme=theme;
async function json(url,options){const r=await apiFetch(url,options);const data=await r.json();if(!r.ok)throw new Error(data.error||"Anfrage fehlgeschlagen");return data;}
function text(id,value){$(id).textContent=value;}
async function health(){
  const s=await json("/api/watch/status");
  text("#watch-status",!s.configured?"Noch keine Beobachtung registriert.":!s.enabled?"Beobachtung gestoppt":!s.workerLock?"Beobachtung eingerichtet, Dienst läuft nicht":s.staleHeartbeat?"Kein aktuelles Lebenszeichen – Dienst prüfen":s.phase==="attention"?"Beobachtung benötigt Aufmerksamkeit":"Beobachtung läuft");
  text("#watch-progress",s.configured?`Beginn: ${V.clock(s.fromAt)} · ${s.symbols.length} Aktien · ${V.label(s.models[0])} + ${V.label(s.models[1])} · ${s.progress}/${s.symbols.length} · ${s.phase} · ${s.cases} Fälle / ${s.reviewed} geprüft`:"Mit dem lokalen CLI init und run einrichten.");
  text("#watch-error",s.error||"");
  const rows=$("#watch-imports");rows.replaceChildren();
  for(const item of s.items||[]){const p=document.createElement("p");p.textContent=`${item.symbol}: ${item.status} · geprüft bis ${V.clock(item.checked)}${item.error?" · "+item.error:""}`;rows.append(p);}
  return s;
}
async function list(reset=false){
  if(loading)return;loading=true;
  try{
    if(reset){queryPage=null;listed=0;$("#watch-cases").replaceChildren();}
    const q=new URLSearchParams({limit:"30",model:$("#watch-model").value,phase:$("#watch-phase").value});
    if(queryPage){q.set("through",queryPage.through);q.set("offset",queryPage.nextOffset);}
    const data=await json("/api/watch/cases?"+q);queryPage=data;
    for(const item of data.items){
      const b=document.createElement("button");b.className="watch-case";
      const title=document.createElement("strong");title.textContent=`${item.symbol} · ${V.label(item.model)} · ${V.label(item.phase)}`;
      const line=document.createElement("small");line.textContent=`${V.clock(item.knownAt)}${item.review?" · Urteil: "+V.label(item.review.verdict):" · ungeprüft"}`;
      b.append(title,line);b.onclick=()=>openCase(item);$("#watch-cases").append(b);listed++;
    }
    text("#watch-count",listed?`${listed} Fälle dieser festen Listensicht. Neue Fälle über „Liste aktualisieren“.`:"Noch keine neuen Fälle nach Beobachtungsbeginn. Es wird kein Einstieg erzwungen.");
    $("#watch-more").hidden=data.nextOffset==null;
  }finally{loading=false;}
}
async function openCase(item){
  active=item;everUnblinded=!!item.revealed||!!item.review?.unblinded;$("#watch-latest").checked=false;$("#watch-latest").disabled=false;
  $("#watch-verdict").value=item.review?.verdict||"unclear";$("#watch-note").value=item.review?.note||"";
  for(const id of ["#watch-verdict","#watch-note","#watch-save"])$(id).disabled=false;
  text("#watch-saved","");await renderCase();
}
async function renderCase(){
  if(!active)return;const ticket=++selection;
  const latest=$("#watch-latest").checked;
  const data=await json(`/api/watch/cases/${active.id}?view=${latest?"latest":"signal"}`);
  if(ticket!==selection)return;
  if(latest)everUnblinded=true;
  text("#watch-case-title",`${data.case.symbol} · ${V.label(data.case.model)} · ${V.label(data.case.phase)}`);
  text("#watch-explanation",data.case.explanation);
  text("#watch-case-meta",`Originalstand ${V.clock(data.case.knownAt)} · Sicht bis ${V.clock(data.asOf)} · Tageskontext ${data.case.daily} · Wochenkontext ${data.case.weekly}`);
  text("#watch-review-context",V.verdictContext(everUnblinded)+" Die Bewertung verändert keine Berechnung.");
  $("#watch-outcomes").hidden=!latest;text("#watch-outcomes",latest?V.outcomeText(data.records):"");
  const link=$("#watch-open-chart");link.hidden=false;link.href="/?"+new URLSearchParams({symbol:data.case.symbol,tf:"4h",dataset:data.datasetId,asof:new Date(data.asOf*1000).toISOString()});
  if(chart)chart.remove();
  chart=LightweightCharts.createChart($("#watch-chart"),{autoSize:true,layout:{background:{color:theme==="dark"?"#11151e":"#ffffff"},textColor:theme==="dark"?"#dce1eb":"#263242"},timeScale:{timeVisible:true},rightPriceScale:{borderVisible:false}});
  chart.addSeries(LightweightCharts.CandlestickSeries,{upColor:"#089981",downColor:"#f23645",borderVisible:false,wickUpColor:"#089981",wickDownColor:"#f23645"}).setData(data.bars.map(({time,open,high,low,close})=>({time,open,high,low,close})));
  for(const [kind,color] of [["red",["breakout","pullback","retest"].includes(data.case.phase)?"#ef8500":"#ff385d"],["green","#00b978"]]){
    const points=V.rayPoints(data.case[kind],data.bars,data.firstIndex);if(!points.length)continue;
    chart.addSeries(LightweightCharts.LineSeries,{color,lineWidth:2,priceLineVisible:false,lastValueVisible:false,autoscaleInfoProvider:()=>null,title:kind==="green"?"Ursprüngliche Safety":"Ursprüngliche Aktion"}).setData(points);
  }
  chart.timeScale().fitContent();
}
function fail(e){text("#watch-error",e.message||String(e));}
$("#watch-review").onsubmit=async e=>{e.preventDefault();if(!active)return;const item=active;
  try{await json(`/api/watch/cases/${item.id}/review`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({verdict:$("#watch-verdict").value,note:$("#watch-note").value,unblinded:everUnblinded})});text("#watch-saved"," Gespeichert");}catch(error){fail(error);}};
$("#watch-latest").onchange=()=>renderCase().catch(fail);
$("#watch-refresh").onclick=()=>list(true).catch(fail);$("#watch-more").onclick=()=>list().catch(fail);
for(const id of ["#watch-model","#watch-phase"])$(id).onchange=()=>list(true).catch(fail);
$("#watch-theme").onclick=()=>{theme=theme==="dark"?"light":"dark";document.documentElement.dataset.theme=theme;try{localStorage.setItem("tori-theme",JSON.stringify(theme));}catch{}renderCase().catch(fail);};
health().then(s=>s.configured?list(true):null).catch(fail);
setInterval(()=>health().catch(fail),10000);
