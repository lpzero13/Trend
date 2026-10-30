"use strict";
const $=s=>document.querySelector(s);
const escapeHtml=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let selected=new Set(),polling=false,previewSequence=0,legacySources=new Map();
async function request(url,options){const response=await apiFetch(url,options);const data=await response.json();if(!response.ok)throw Error(data.error||"Anfrage fehlgeschlagen");return data;}
function error(message){$("#collector-error").hidden=!message;$("#collector-error").textContent=message;}
function post(url,body={}){return request(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});}
async function renderUniverses(){const data=await request("/api/archive/universes");$("#universe-list").innerHTML=data.items.map(u=>`<p><label style="flex-direction:row;align-items:center"><input type="checkbox" data-universe="${escapeHtml(u.id)}" ${selected.has(u.id)?"checked":""} ${u.ready?"":"disabled"}>${escapeHtml(u.name)} · ${u.ready?`${u.count} Titel · ${escapeHtml(u.asOf)}`:"Liste noch nicht geladen"}${u.unmappedHoldings?` · ${u.unmappedHoldings} ausgenommene Sonderpositionen`:""}</label></p>`).join("");}
function duration(seconds){const minutes=Math.max(1,Math.round(seconds/60));return minutes>=60?`${Math.floor(minutes/60)} Std. ${minutes%60} Min.`:`${minutes} Min.`;}
function utcEnd(value){return value.length===16?value+":00Z":value+"Z";}
async function preview(){
 const seq=++previewSequence;
 if(!selected.size){$("#collector-preview").textContent="Bitte Universum auswählen.";$("#collector-estimate").textContent="";return;}
 const query=new URLSearchParams({ids:[...selected].join(",")});
 if($("#collector-start").value)query.set("start",$("#collector-start").value+"T00:00:00Z");
 if($("#collector-end").value)query.set("end",utcEnd($("#collector-end").value));
 const p=await request("/api/archive/preview?"+query);if(seq!==previewSequence)return;
 $("#collector-preview").textContent=`${p.uniqueStocks} verschiedene Aktien · ${p.existingStocks} bereits mit lokalem SIP-Bestand · ${p.newStocks} ohne solchen Bestand. Zeitraum und Wiederverwendbarkeit werden geprüft.`;
 const e=p.estimate;
 $("#collector-estimate").textContent=e?`Schätzung für vollständigen Erstimport: ${duration(e.seconds)} (Planungsband ${duration(e.lowSeconds)}–${duration(e.highSeconds)}). Rund ${(e.combinedBytes/1073741824).toFixed(2)} GiB für Kursbestände und Monatsdateien, zuzüglich Betriebsdaten und Speicherreserve. Grundlage: lokaler Fünf-Aktien-Test, längere Historien; keine garantierte Containerlaufzeit. Vorhandene Bestände sind noch nicht abgezogen.`:"";
}
$("#collector-start").onchange=$("#collector-end").onchange=()=>preview().catch(e=>error(e.message));
$("#collector-adopt").onchange=async()=>{
 const source=legacySources.get($("#collector-adopt").value);
 $("#collector-start").disabled=$("#collector-end").disabled=!!source;
 if(source){$("#collector-start").value=source.start.slice(0,10);$("#collector-end").value=new Date(source.end).toISOString().slice(0,19);}
 try{await preview();}catch(e){error(e.message);}
};
$("#universe-list").onchange=async e=>{const id=e.target.dataset.universe;if(!id)return;e.target.checked?selected.add(id):selected.delete(id);try{await preview();}catch(e){error(e.message);}};
$("#refresh-universes").onclick=async()=>{const button=$("#refresh-universes");button.disabled=true;error("");$("#source-status").textContent="Offizielle Bestandsdateien werden geladen …";try{await post("/api/archive/universes/refresh");await renderUniverses();$("#source-status").textContent="Bestandslisten aktualisiert. Es wurden keine Aktienkurse heruntergeladen.";}catch(e){error(e.message);$("#source-status").textContent="Aktualisierung nicht vollständig; gespeicherte Listen bleiben erhalten.";await renderUniverses();}finally{button.disabled=false;}};
$("#collector-form").onsubmit=async e=>{e.preventDefault();error("");if(!selected.size){error("Bitte mindestens ein Universum auswählen.");return;}$("#collector-submit").disabled=true;try{const body={universes:[...selected],start:$("#collector-start").value+"T00:00:00Z",adopt_from:$("#collector-adopt").value};if($("#collector-end").value)body.end=utcEnd($("#collector-end").value);const job=await post("/api/archive/jobs",body);await post(`/api/archive/jobs/${job.id}/start`);await refresh();}catch(e){error(e.message);}finally{$("#collector-submit").disabled=false;}};
async function refresh(){if(polling)return;polling=true;try{const data=await request("/api/archive/jobs");const current=$("#collector-adopt").value;legacySources=new Map(data.legacy.map(j=>[j.id,j]));$("#collector-adopt").innerHTML='<option value="">Keinen Altauftrag übernehmen</option>'+data.legacy.filter(j=>j.finished>0).map(j=>`<option value="${escapeHtml(j.id)}">${escapeHtml(j.name)} · ${j.finished}/${j.total} · ${escapeHtml(j.status)}</option>`).join("");$("#collector-adopt").value=current;$("#collector-legacy").textContent=data.legacy.filter(j=>j.finished>0).map(j=>`Altbestand: ${j.name} · ${j.finished}/${j.total} fertig · ${j.status}. Übernahme über die linke Auswahl.`).join("\n");$("#collector-empty").hidden=!!data.items.length;$("#collector-jobs").innerHTML=data.items.map(j=>`<article style="border-top:1px solid var(--border);padding:14px 0"><b>${escapeHtml(j.universe.name)}</b><p>${escapeHtml(j.status)} · ${j.finished}/${j.total} Aktien · ${j.checkpointMonths} Monate · ${(j.stagingBytes/1048576).toFixed(1)} MiB Monatsdateien</p><p><small>${escapeHtml(j.phase)} · ${(j.metrics||{}).pages||0} Antwortseiten · Aktualisierung ${escapeHtml(new Date(j.updatedAt*1000).toLocaleTimeString())}</small></p>${j.error?`<p role="alert">${escapeHtml(j.error)}</p>`:""}${(j.failures||[]).map(f=>`<p role="alert">${escapeHtml(f.symbol)}: ${escapeHtml(f.error)}</p>`).join("")}${["pending","paused","partial","failed"].includes(j.status)?`<button data-action="start" data-id="${j.id}">Starten / fortsetzen</button>`:""}${(j.status==="running"||j.phase==="adopting")?`<button data-action="pause" data-id="${j.id}">Pause · Fortschritt behalten</button>`:""}</article>`).join("");}finally{polling=false;}}
$("#collector-jobs").onclick=async e=>{if(!e.target.dataset.action)return;e.target.disabled=true;try{await post(`/api/archive/jobs/${e.target.dataset.id}/${e.target.dataset.action}`);await refresh();}catch(e){error(e.message);}finally{e.target.disabled=false;}};
Promise.all([renderUniverses(),refresh()]).catch(e=>error(e.message));
setInterval(()=>refresh().catch(e=>error(e.message)),5000);
