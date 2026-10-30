(function(){
  'use strict';
  const $=id=>document.getElementById(id),V=ToriCandidates;
  let run='',studies=[],research='',offset=0,recordOffset=0,paperOffset=0,eventCursor=null,selection=null,chart=null,series=[],request=0;
  const stamp=t=>t?new Date(t*1000).toLocaleString('de-DE',{timeZone:'America/New_York'})+' ET':'—';
  const error=e=>{$('cw-error').hidden=false;$('cw-error').textContent=e.message;};
  async function api(route,params={}){const r=await apiFetch('/api/candidates/'+route+'?'+new URLSearchParams(params));const b=await r.json();if(!r.ok)throw Error(b.error||'Anfrage fehlgeschlagen');return b;}
  const safe=fn=>async()=>{try{$('cw-error').hidden=true;await fn();}catch(e){error(e);}};
  function el(tag,text){const e=document.createElement(tag);if(text!=null)e.textContent=text;return e;}
  function table(id,heads,rows,append=false){const host=$(id);if(!append)host.replaceChildren();const t=el('table'),h=el('tr');heads.forEach(x=>h.append(el('th',x)));t.append(h);rows.forEach(row=>{const tr=el('tr');row.forEach(x=>tr.append(el('td',x)));t.append(tr);});host.append(t);}
  function options(id,items){$(id).replaceChildren(...items.map(([v,t])=>{const o=el('option',t);o.value=v;return o;}));}
  function theme(){const dark=document.documentElement.dataset.theme==='dark';document.documentElement.dataset.theme=dark?'dark':'light';if(chart)chart.applyOptions({layout:{background:{color:dark?'#11151d':'#fff'},textColor:dark?'#dde3ec':'#252b34'},grid:{vertLines:{color:dark?'#252b34':'#edf0f3'},horzLines:{color:dark?'#252b34':'#edf0f3'}}});}
  async function showCase(){if(!selection)return;const token=++request,params={id:selection.id,future:$('cw-future').checked?'1':'0'};if(selection.kind==='record')params.research=selection.research;else params.run=run;
    const p=await api(selection.kind==='record'?'record':'case',params);if(token!==request)return;
    $('cw-title').textContent=p.case.symbol+' · ursprüngliche 4h-Linien';$('cw-chart-meta').textContent='Signalstand: '+stamp(p.cutoff)+' · Ansicht bis '+stamp(p.viewAsOf)+(p.futureShown?' · Spätere Kurse sichtbar':' · Nur damals bekannte Kerzen');
    if(!chart){chart=LightweightCharts.createChart($('cw-chart'),{autoSize:true,rightPriceScale:{borderVisible:false},timeScale:{timeVisible:true},handleScroll:true,handleScale:true});new ResizeObserver(()=>chart.resize($('cw-chart').clientWidth,500)).observe($('cw-chart'));}
    series.forEach(s=>chart.removeSeries(s));series=[];
    const candles=chart.addSeries(LightweightCharts.CandlestickSeries,{upColor:'#00ad83',downColor:'#ff375f',borderVisible:false,wickUpColor:'#00ad83',wickDownColor:'#ff375f'});candles.setData(p.bars);series.push(candles);
    for(const r of p.rays){const s=chart.addSeries(LightweightCharts.LineSeries,{color:r.role==='red'?'#ff375f':'#00b785',lineWidth:2,priceLineVisible:false,lastValueVisible:false,title:'4h · '+(r.role==='red'?'Rot':'Grün')});s.setData(ToriWorkbench.points(r.ray,p.bars));series.push(s);}
    chart.timeScale().setVisibleLogicalRange({from:Math.max(0,p.bars.length-160),to:p.bars.length+8});theme();
    $('cw-detail').textContent=JSON.stringify(p.evaluation||p.case,null,2);
  }
  function card(host,title,detail,onClick){const b=el('button');b.className='cw-case';b.append(el('strong',title),el('span',detail));b.onclick=safe(onClick);host.append(b);}
  async function cases(reset=true){if(!run)return;if(reset){offset=0;$('cw-cases').replaceChildren();}const p=await api('cases',{run,state:$('cw-state').value,symbol:$('cw-symbol').value,offset,limit:30});
    for(const g of p.items)card($('cw-cases'),g.symbol+' · '+V.states[g.state],`${stamp(g.firstKnownAt)} · ${g.contacts} Kontakte · ${V.value(g.ageDays,' Tage')} · Safety ${V.value(g.riskPct,'%')} / ${V.value(g.riskATR,' ATR')} · ${g.alternativeCount} ähnliche Varianten. ${g.bootstrap?'Bestand beim Start. ':''}${g.warnings.join(' · ')}`,async()=>{selection={id:g.id,kind:'candidate'};$('cw-future').checked=false;await showCase();});
    offset+=p.items.length;$('cw-more').hidden=!p.page.hasMore;$('cw-order').textContent=`${p.page.total} Strukturen · ${p.meaning}`;
  }
  async function events(reset=true){if(!run)return;if(reset){eventCursor=null;$('cw-journal').replaceChildren();}const p=await api('events',{run,...(eventCursor?{cursor:eventCursor}:{})});table('cw-journal',['Zeit','Aktie','Art','Zustand'],p.items.map(e=>[stamp(e.knownAt),e.symbol,e.kind+(e.bootstrap?' · Bestand':''),V.states[e.state]||e.model||'']),!reset);eventCursor=p.page.nextCursor;$('cw-events-more').hidden=!eventCursor;}
  async function refresh(){run=$('cw-run').value;if(!run){$('cw-status').textContent='Noch kein SIP-Beobachter registriert. Einrichtung über die lokale CLI.';return;}const s=await api('status',{run});
    $('cw-status').textContent=`Registriert ${stamp(s.registeredAt)} · ${s.phase} · ${s.progress}/${s.total} · Worker ${s.workerLockHeld?'aktiv':'nicht aktiv'}${s.stalled?' / Herzschlag veraltet':''} · letzter erfolgreicher Import ${stamp(s.lastSuccessfulImportAt)}`;
    table('cw-lanes',['Aktie','Quellschluss','Import','Status'],s.lanes.map(l=>[l.symbol,stamp(l.sourceClose),stamp(l.lastImportAt),l.error||(l.blocked?'gesperrt':'OK')]));await cases();await events();
    await papers();
  }
  async function papers(reset=true){if(!run)return;if(reset){paperOffset=0;$('cw-papers').replaceChildren();}const p=await api('papers',{run,offset:paperOffset,limit:50});
    table('cw-papers',['Aktie','Einstieg','Stoppmodell','Zustand','R / Bewertung'],p.items.flatMap(p=>Object.entries(p.paths).map(([m,v])=>[p.symbol,stamp(p.entry.entryAt),m,v.status,v.status==='closed'?V.value(v.netR,' R realisiert'):v.status==='open'?V.value(v.markNetR,' R offen'):'unbekannt'])),!reset);
    paperOffset+=p.items.length;$('cw-papers-count').textContent=`${paperOffset} von ${p.page.total||0} Papierpositionen geladen`;$('cw-papers-more').hidden=!p.page.hasMore;
  }

  async function records(reset=true){if(!research)return;if(reset){recordOffset=0;$('cw-records').replaceChildren();}const p=await api('records',{research,offset:recordOffset,limit:20});p.items.forEach(r=>card($('cw-records'),r.symbol+' · '+stamp(r.entryAt),JSON.stringify(r.features),async()=>{selection={id:r.id,kind:'record',research};$('cw-future').checked=false;await showCase();}));recordOffset+=p.items.length;$('cw-record-more').hidden=!p.page.hasMore;}
  function metrics(){research=$('cw-research').value;const study=studies.find(s=>s.id===research);if(!study)return;const phase=$('cw-phase').value,h=Number($('cw-horizon').value),rows=V.metricRows(study.summary,phase,h);
    const label={market:'Kurs nach Kosten (Prozentpunkte)',fixed:'Fixierte Safety (R)',higher_low:'Bestätigte höhere Tiefs (R)'};
    table('cw-metrics',['Bewertung','Bekannt / alle','Mittel Einstieg','Vollständige Panels','Vorteil ggü. Kontrollen','Unsicherheitsband'],rows.map(r=>[label[r.kind],`${r.knownEntries} / ${study.summary.groups[phase].entries}`,V.value(r.meanActual),r.pairedPanels,V.value(r.meanExcess),V.interval(r)]));
    table('cw-features',['Merkmal','Fälle','Panels','Kursvorteil','Band'],Object.entries(study.summary.groups).filter(([key])=>key.startsWith(phase+'/')).map(([key,g])=>{const m=g.horizons[String(h)].market;return [key.slice(phase.length+1),g.entries,m.pairedPanels,V.value(m.meanExcess,' pp'),V.interval(m)];}));
  }
  async function studyChanged(){metrics();await records();if(!research)return;const cash=await api('cash',{research});table('cw-cash',['Phase / Gruppe','Modell','Status','Positionen / offen','Depotbewertung','Realisierter P/L'],cash.items.map(x=>[x.phase+' / '+x.cohort,x.model,x.status,`${x.accepted} / ${x.open}`,V.value(x.markedReturnPct,'%'),V.value(x.realizedNetPnl,' USD')]));}
  async function init(){try{const saved=JSON.parse(localStorage.getItem('tori-theme'));if(['dark','light'].includes(saved))document.documentElement.dataset.theme=saved;}catch{}theme();const r=await api('runs');options('cw-run',r.items.map(r=>[r.id,stamp(r.registeredAt)+' · SIP · '+Object.keys(r.dataset_ids).length+' Aktien · '+r.status]));const s=await api('research');studies=s.items;options('cw-research',s.items.map(s=>[s.id,'SIP · '+s.summary.groups.all.entries+' Retests · '+stamp(s.createdAt)]));await refresh();await studyChanged();const packs=await apiFetch('/api/workbench/packs');if(packs.ok){const pack=(await packs.json()).items.find(p=>p.label.startsWith('SIP · 20'));if(pack)$('cw-review').href='/pruefung?pack='+encodeURIComponent(pack.id);}}
  $('cw-theme').onclick=()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=next;try{localStorage.setItem('tori-theme',JSON.stringify(next));}catch{}theme();};
  $('cw-run').onchange=safe(refresh);$('cw-refresh').onclick=safe(refresh);$('cw-state').onchange=safe(cases);$('cw-symbol').onchange=safe(cases);$('cw-more').onclick=safe(()=>cases(false));$('cw-future').onchange=safe(showCase);$('cw-fit').onclick=()=>chart?.timeScale().fitContent();$('cw-events-more').onclick=safe(()=>events(false));$('cw-papers-more').onclick=safe(()=>papers(false));$('cw-record-more').onclick=safe(()=>records(false));$('cw-research').onchange=safe(studyChanged);$('cw-phase').onchange=metrics;$('cw-horizon').onchange=metrics;
  safe(init)();
})();
