"use strict";
const $=s=>document.querySelector(s), V=FanView;
let catalog=[], selected=new Map(), jobId=new URLSearchParams(location.search).get("job"), offset=0, pageSize=20, busy=false, refreshTimer, reportSignature="", refreshAgain=false;
function error(message){$("#fan-error").textContent=message;$("#fan-error").hidden=!message;}
async function request(url,options){const response=await apiFetch(url,options);const data=await response.json();if(!response.ok)throw Error(data.error||"Anfrage fehlgeschlagen");return data;}
function groups(){const by=new Map();for(const item of catalog){if(!by.has(item.symbol))by.set(item.symbol,[]);by.get(item.symbol).push(item);}return by;}
function renderCatalog(){
 const term=$("#fan-search").value.trim().toLowerCase();
 $("#fan-datasets").innerHTML=[...groups()].filter(([symbol,items])=>`${symbol} ${items.map(i=>i.feed+" "+i.dataKind).join(" ")}`.toLowerCase().includes(term)).map(([symbol,items])=>{
  items.sort((a,b)=>b.importedAt.localeCompare(a.importedAt));const chosen=selected.get(symbol)||items[0].id;
  return `<div class="fan-stock"><label><input type="checkbox" data-symbol="${V.esc(symbol)}" ${selected.has(symbol)?"checked":""}>${V.esc(symbol)}</label><select data-source="${V.esc(symbol)}" aria-label="Datenbestand ${V.esc(symbol)}">${items.map(i=>`<option value="${i.id}" ${i.id===chosen?"selected":""}>${V.esc(i.feed.toUpperCase()+" / "+i.adjustment+" / "+i.importedAt.slice(0,10)+(i.dataKind==="synthetic"?" / SYNTHETISCH":""))}</option>`).join("")}</select></div>`;
 }).join("")||"<p>Keine passenden lokalen Bestände.</p>";
 $("#fan-catalog-status").textContent=`${groups().size} Aktien mit regulären Feindaten · ${selected.size} ausgewählt`;
}
$("#fan-search").oninput=renderCatalog;
$("#fan-datasets").onchange=e=>{const symbol=e.target.dataset.symbol||e.target.dataset.source;if(!symbol)return;if(e.target.dataset.symbol){const source=[...$("#fan-datasets").querySelectorAll("select")].find(s=>s.dataset.source===symbol);if(e.target.checked)selected.set(symbol,source.value);else selected.delete(symbol);}else if(selected.has(symbol))selected.set(symbol,e.target.value);renderCatalog();};
$("#fan-sampling").onchange=()=>{$("#fan-samples").disabled=$("#fan-sampling").value==="full";};
function number(id){return Number($(id).value);}
$("#fan-form").onsubmit=async e=>{
 e.preventDefault();error("");if(!selected.size){error("Bitte mindestens eine Aktie mit lokalem Datenbestand auswählen.");return;}
 const models=[...document.querySelectorAll('[name="fan-model"]:checked')].map(x=>x.value), horizons=[...document.querySelectorAll('[name="fan-horizon"]:checked')].map(x=>Number(x.value));if(!models.length||!horizons.length){error("Mindestens ein Stopmodell und einen Beobachtungshorizont auswählen.");return;}
 const geometry=$("#fan-geometry").value;
 const spec={entry_mode:"fan",symbols:[...selected.keys()],dataset_ids:Object.fromEntries(selected),samples:number("#fan-samples"),seed:number("#fan-seed"),horizons,holdout_fraction:.2,
  fan:{timeframe:$("#fan-tf").value,geometry_variants:geometry==="all"?["master","extreme","local"]:geometry==="both"?["extreme","local"]:[geometry],sampling:$("#fan-sampling").value,warmup_bars:number("#fan-warmup"),origin_start:$("#fan-from").value||null,origin_end:$("#fan-until").value||null,models,
   geometry:{pivot_side:number("#fan-pivot"),contact_gap:number("#fan-gap"),contact_atr:number("#fan-contact"),wick_atr:number("#fan-wick"),min_age_days:number("#fan-age"),lookback_days:number("#fan-safety-days"),action_lookback_days:number("#fan-action-days"),body_atr:number("#fan-body")},
   watch:{clean_atr:number("#fan-clean"),stop_buffer_pct:number("#fan-buffer"),safety_choice:$("#fan-safety-choice").value},
   execution:{capital:number("#fan-capital"),risk_fraction:number("#fan-risk")/100,latency_seconds:number("#fan-latency"),spread_bps:number("#fan-spread"),slippage_bps:number("#fan-slippage"),fee_per_order:number("#fan-fee"),target_r:number("#fan-target"),trailing_buffer_pct:number("#fan-buffer"),pivot_side:number("#fan-pivot")}}};
 $("#fan-submit").disabled=true;try{const job=await request("/api/research/jobs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(spec)});jobId=job.id;offset=0;history.replaceState(null,"","/faecher?job="+jobId);await refresh();}catch(e){error(e.message);}finally{$("#fan-submit").disabled=false;}
};
async function refresh(){
 if(busy){refreshAgain=true;return;}busy=true;try{
  const all=await request("/api/research/jobs");$("#fan-worker").textContent=all.workerActive?"Forschungsworker erreichbar. Aufträge werden nacheinander bearbeitet.":"Kein Forschungsworker aktiv. Neue Aufträge bleiben in der Warteschlange, bis der Worker gestartet wird.";
  const items=all.items.filter(j=>j.spec.entry_mode==="fan");if(!jobId&&items.length)jobId=items[0].id;$("#fan-jobs").innerHTML=items.map(j=>`<button type="button" data-job="${j.id}" aria-pressed="${j.id===jobId}">${V.esc(V.label(j.status))} · ${V.esc(j.spec.symbols.slice(0,3).join(", "))} · ${j.id.slice(0,6)}</button>`).join("")||"<p>Noch kein Fächer-Auftrag.</p>";
  if(jobId){const requestedJob=jobId, requestedOffset=offset, requestedFilter=$("#fan-filter").value;
   const result=await request(`/api/research/jobs/${encodeURIComponent(requestedJob)}/report?offset=${requestedOffset}&limit=${pageSize}&entry_filter=${requestedFilter}`), job=result.job;
   if(jobId!==requestedJob || offset!==requestedOffset || $("#fan-filter").value!==requestedFilter){refreshAgain=true;return;}
   $("#fan-progress").textContent=`${V.label(job.status)} · ${job.current_symbol||""} · ${job.progress?.detail?.completed??"—"}/${job.progress?.detail?.total??"—"} Quellkerzen · ${job.eventCount} Ereignisse`;
   const failures=job.symbols.filter(s=>s.error);if(failures.length)$("#fan-progress").textContent+=" · "+failures.map(s=>s.symbol+": "+s.error).join("; ");
   $("#fan-summary").textContent=`${result.summary.originCount} Startversuche · ${result.summary.uniqueSignals} Signalfälle im gesamten Verlauf (je Variante und Kontaktgruppe dedupliziert). Mehrere Starts können dasselbe Signal erreichen.`;
   const kinds=result.summary.dataKinds||[];
   $("#fan-data-note").hidden=!kinds.includes("synthetic");
   $("#fan-data-note").textContent="SYNTHETISCHE TECHNIKDATEN: Diese Ergebnisse prüfen die Software und sind kein Nachweis einer Handelsstrategie.";
   const signature=JSON.stringify([job.id,job.status,job.eventCount,result.page.snapshot,requestedOffset,requestedFilter]);
   if(signature!==reportSignature){
    const opened=new Set([...$("#fan-cases").querySelectorAll("details[open][data-case]")].map(e=>e.dataset.case));
    $("#fan-groups").innerHTML=V.groups(result.summary);$("#fan-cases").innerHTML=V.cases(result.trials,job.id)||"<p>Für diesen Filter bisher keine Fälle.</p>";
    for(const item of $("#fan-cases").querySelectorAll("details[data-case]"))if(opened.has(item.dataset.case))item.open=true;
    reportSignature=signature;
   }
   $("#fan-page").textContent=`${result.page.total?offset+1:0}–${offset+result.trials.length} von ${result.page.total}`;$("#fan-prev").disabled=offset===0;$("#fan-next").disabled=!result.page.hasMore;$("#fan-cancel").hidden=!["queued","running"].includes(job.status);
  }
 }catch(e){error(e.message);}finally{busy=false;clearTimeout(refreshTimer);refreshTimer=setTimeout(refresh,refreshAgain?0:4000);refreshAgain=false;}
}
$("#fan-jobs").onclick=e=>{const id=e.target.closest("[data-job]")?.dataset.job;if(id){jobId=id;offset=0;history.replaceState(null,"","/faecher?job="+id);refresh();}};
$("#fan-filter").onchange=()=>{offset=0;refresh();};$("#fan-prev").onclick=()=>{offset=Math.max(0,offset-pageSize);refresh();};$("#fan-next").onclick=()=>{offset+=pageSize;refresh();};$("#fan-refresh").onclick=refresh;
$("#fan-cancel").onclick=async()=>{try{await request(`/api/research/jobs/${encodeURIComponent(jobId)}/cancel`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});refresh();}catch(e){error(e.message);}};
let theme;try{theme=JSON.parse(localStorage.getItem("tori-theme"));}catch{}document.documentElement.dataset.theme=theme|| (matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");$("#fan-theme").onclick=()=>{const next=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=next;try{localStorage.setItem("tori-theme",JSON.stringify(next));}catch{}};
(async()=>{try{catalog=(await request("/api/fan/datasets")).items;renderCatalog();}catch(e){error(e.message);}await refresh();})();
