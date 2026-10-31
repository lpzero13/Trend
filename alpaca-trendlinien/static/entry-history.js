/* Immutable historical events: source 4h detection, projection only in other views. */
(function(root){
  'use strict';
  const labels={breakout:'Ausbruch',red_retest:'Roter Retest',safety_bounce:'Safety-Bounce'};
  const colors={breakout:'#2875dc',red_retest:'#9c55c8',safety_bounce:'#008878'};
  const darkColors={breakout:'#82b1ff',red_retest:'#cf9eff',safety_bounce:'#42d3b7'};
  function signalBar(bars, at){
    let lo=0,hi=bars.length;
    while(lo<hi){const mid=(lo+hi)>>1;if(bars[mid].end<at)lo=mid+1;else hi=mid;}
    const b=bars[lo];return b && b.time<at && at<=b.end ? b : null;
  }
  function markers(items,bars,cutoff,theme='light'){
    const seen=new Set();return items.flatMap(c=>{
      const key=c.episode_id+'|'+c.family;
      if(seen.has(key) || c.signal_at>cutoff)return [];
      seen.add(key);const b=signalBar(bars,c.signal_at);
      return b ? [{id:'entry:'+c.id,time:b.time,position:'belowBar',color:(theme==='dark'?darkColors:colors)[c.family],shape:'arrowUp',text:labels[c.family],size:1}] : [];
    }).sort((a,b)=>a.time-b.time || a.id.localeCompare(b.id));
  }
  function fixedLines(detail,cutoff,theme='light'){
    if(!detail?.signal || detail.signal.signalAt>cutoff)return [];
    const s=detail.signal;
    const dark=theme==='dark',red=dark?'#ff7189':'#ed4665',green=dark?'#37d6a1':'#059669';
    const lines=[{line:s.line,color:s.family==='safety_bounce'?green:red,label:s.family==='safety_bounce'?'4h · ursprüngliche Bounce-Safety':'4h · ursprüngliche Signallinie'}];
    if(s.safety && s.safety.id!==s.line.id)lines.push({line:s.safety,color:green,label:'4h · ursprüngliche Safety'});
    const out=lines.filter(v=>v.line).map(({line,color,label})=>({
      a:{time:line.a_time,price:line.a_price},b:{time:line.b_time,price:line.b_price},
      color,width:2.5,dash:[],label:label+' · fixiert',labelColor:color===green?'#08734f':'#9d2441',labelEdge:true,
      id:'fixed:'+line.id
    }));
    if(s.initialStop>0)out.push({a:{time:s.signalAt,price:s.initialStop},b:{time:s.signalAt+14400,price:s.initialStop},
      color:dark?'#ffc166':'#c17a12',width:1.5,dash:[5,5],label:'Anfangsstop · fixiert',labelColor:'#80500a',labelEdge:true});
    return out;
  }
  function contacts(detail,bars,cutoff,theme='light'){
    if(!detail?.signal || detail.signal.signalAt>cutoff)return [];
    const s=detail.signal,seen=new Set(),out=[];
    for(const [ln,green] of [[s.line,s.family==='safety_bounce'],[s.safety,true]]){
      if(!ln)continue;
      for(const point of ln.contactPoints || []){
        if(point.known_at>cutoff)continue;
        const bar=signalBar(bars,point.time+1),key=ln.id+'|'+bar?.time;
        if(!bar || seen.has(key))continue;seen.add(key);
        out.push({id:'contact:'+key,time:bar.time,position:green?'belowBar':'aboveBar',shape:'circle',color:green?(theme==='dark'?'#37d6a1':'#059669'):(theme==='dark'?'#ff7189':'#ed4665'),size:.5});
      }
    }
    return out;
  }
  function attach(ctx){
    const $=id=>document.getElementById(id), {state,esc,fmt,dtLong}=ctx;
    if(location.pathname==='/zufall'){$('entry-history-toggle').hidden=true;return null;}
    const profileIds=['all','qualified','risk','trend','mature','convergent','both_qualified','balanced','strict'];
    const requestedProfile=new URLSearchParams(location.search).get('entry_profile');
    $('entry-quality').value=profileIds.includes(requestedProfile)?requestedProfile:'qualified';
    let enabled=!!state.entryRun,run=null,runs=[],items=[],selected=null,selectedId=new URLSearchParams(location.search).get('entry_case'),
      activeSymbol=null,loadedKey=null,generation=0,loadingRuns=false,job=null,pollTimer=null,switchSerial=0;
    const drafts=new Map();
    function frozenRays(){
      return fixedLines(selected,state.data.analysisCutoff,state.theme).map(r=>{
        const key='tori-entry-anchors:'+run.id+':'+selectedId+':'+state.timeframe+':'+(r.id || r.label);
        let positions;
        try{positions=JSON.parse(localStorage.getItem(key));}catch{}
        if(!positions || ![positions.a,positions.b].every(Number.isFinite)){
          positions={a:RayGeometry.logicalAt(state.data.axis,r.a.time),b:RayGeometry.logicalAt(state.data.axis,r.b.time)};
          try{localStorage.setItem(key,JSON.stringify(positions));}catch{}
        }
        return {...r,a:{...r.a,logical:positions.a},b:{...r.b,logical:positions.b}};
      });
    }
    const iso=at=>new Date(at*1000).toISOString();
    const message=text=>{$('entry-history-status').textContent=text;};
    async function api(path,body){
      const response=await apiFetch('/api/entries/'+path,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data=await response.json();if(!response.ok)throw Error(data.error || 'Entryanfrage fehlgeschlagen.');return data;
    }
    function current(){return enabled && run && state.entryRun===run.id && state.data?.datasetId===run.datasetId;}
    function update(){
      $('entry-history-panel').hidden=!enabled;
      $('entry-history-toggle').setAttribute('aria-pressed',String(enabled));
      $('entry-history-toggle').textContent=enabled?'Historische Einstiege: An':'Historische Einstiege';
      $('workspace').classList.toggle('entry-open',enabled && $('entry-history-panel').querySelector('details').open);
    }
    function drawList(){
      $('entry-case-list').innerHTML=[...items].reverse().map(c=>`<button type="button" data-entry-case="${esc(c.id)}" aria-pressed="${c.id===selectedId}"><b>${esc(labels[c.family])}</b> · ${esc(dtLong(c.signal_at))} ET <small>${esc(c.cohort==='qualified'?'qualifiziert':c.cohort==='two'?'2 Kontakte':'noch jung')} · feste Episode</small></button>`).join('');
    }
    function drawDetail(){
      const visible=current() && selected?.state==='available' && selected.signal.signalAt<=state.data.analysisCutoff;
      $('entry-case-detail').hidden=!visible;
      if(!visible)return;
      const s=selected.signal,e=selected.entry,ln=s.line;
      $('entry-case-facts').innerHTML=`<h3>${esc(labels[s.family])} · 4h · fixiert</h3><p>Signal: ${esc(dtLong(s.signalAt))} ET<br>Linie: ${ln.contacts} Kontakte · ${fmt(ln.span_days)} Tage<br>Anfangsstop: ${fmt(s.initialStop)} USD<br>${e.status==='filled'?`Modell-Entry: ${esc(dtLong(e.entryAt))} ET · ${fmt(e.entryPrice)} USD (Open), ${fmt(e.entryFill)} USD mit Kosten`:e.status==='pending'?'Entry-Open zu diesem Zeitpunkt noch nicht bekannt.':`Kein ausführbarer Entry: ${esc(e.reason || e.status)}`}</p><p class="entry-muted">${esc(s.episodeReason==='two_new_confirmed_contacts'?'Neue Episode durch zwei neue bestätigte Kontakte.':'Feste Strukturherkunft; keine erneuten täglichen Entries.')} Linien und Kontakte entsprechen dem gespeicherten Signal, nicht der heutigen Analyse.</p>`;
      if(selected.screen){
        const f=selected.screen.features;
        const daily=Number.isFinite(f.dailySma200)?`Letzter Tages-Schluss: ${fmt(f.dailyClose)} · SMA200: ${fmt(f.dailySma200)}<br><small>Kontext vom ${esc(dtLong(f.dailyAsOf))} ET.</small>`:'<small>SMA200 unbekannt; dieses Profil verlangt keinen Tagestrend.</small>';
        $('entry-case-facts').innerHTML+=`<p>Strukturprofil: ${esc(selected.screen.label)}<br>Abstand am Signalschluss: ${fmt(f.signalStopPct)} % / ${fmt(f.signalStopATR)} ATR4h<br>${daily}<br><small>Kriterien beim Signal erfüllt; späterer Erfolg unbekannt.</small></p>`;
      }
      const draft=drafts.get(run.id+'|'+selectedId);
      $('entry-verdict').value=draft?.verdict || selected.review?.verdict || 'unclear';
      $('entry-note').value=draft?.note ?? selected.review?.note ?? '';
      $('entry-review-status').textContent=selected.review?'Gespeicherte Bewertung geladen.':'';
    }
    async function chooseCase(id,center=true){
      selectedId=id;selected=null;$('entry-case-detail').hidden=true;ctx.redraw();drawList();
      const token=generation,at=state.data?.analysisCutoff,whichRun=run?.id;
      try{
        const result=await api('case?'+new URLSearchParams({run:whichRun,case:id,asof:iso(at),quality:$('entry-quality').value}));
        if(token!==generation || whichRun!==run?.id || id!==selectedId || at!==state.data?.analysisCutoff)return;
        selected=result;drawDetail();ctx.redraw();
        if(center && selected.signal){const b=signalBar(state.data.bars,selected.signal.signalAt),i=state.data.bars.indexOf(b);if(i>=0)ctx.chart.timeScale().setVisibleLogicalRange({from:i-60,to:i+25});}
        history.replaceState(null,'',location.pathname+'?'+new URLSearchParams({...Object.fromEntries(new URLSearchParams(location.search)),entry_case:id,entry_profile:$('entry-quality').value}));
      }catch(e){if(token===generation)message(e.message);}
    }
    async function refresh(){
      if(!current())return;
      const cutoff=state.data.analysisCutoff;
      const filters={run:run.id,asof:iso(cutoff),family:$('entry-family').value,cohort:$('entry-cohort').value,filled:$('entry-filled').checked?'1':'0',quality:$('entry-quality').value,limit:'250'};
      const key=JSON.stringify(filters);if(key===loadedKey)return;
      loadedKey=key;const token=++generation;items=[];selected=null;drawDetail();ctx.redraw();message('Gespeicherte feste Einstiege laden …');
      try{
        let offset=0,total=0,all=[],excluded=0;
        while(true){
          const page=await api('cases?'+new URLSearchParams({...filters,offset:String(offset)}));
          if(token!==generation)return;
          all.push(...page.items);total=page.total;excluded=page.screen?.excluded || 0;offset+=page.items.length;
          if(!page.hasMore)break;
        }
        if(token!==generation)return;
        items=all;if(selectedId && !items.some(c=>c.id===selectedId))selectedId=null;
        drawList();message(`${total} feste Signalpunkte bis zum Chartzeitpunkt · ${excluded} durch das Strukturprofil ausgeschlossen. Je Episode und Entrytyp einmal; kein Filter nach späterem Gewinn.`);
        ctx.redraw();if(selectedId)await chooseCase(selectedId,false);
      }catch(e){if(token===generation){loadedKey=null;message(e.message);}}
    }
    async function openRun(id,asof=null){
      const next=runs.find(r=>r.id===id);if(!next)return;
      const serial=++switchSerial;
      const before=run;run=next;loadedKey=null;items=[];selected=null;generation++;
      const opened=await ctx.open(run,asof);
      if(serial!==switchSerial || run?.id!==next.id)return;
      if(!opened){run=before;message('Gespeicherter Datenbestand konnte nicht geöffnet werden.');return;}
      $('entry-run').value=id;
      const date=x=>typeof x==='number'?dtLong(x):x;
      $('entry-coverage').textContent=`${run.symbol} · ${run.feed.toUpperCase()} / ${run.adjustment} · Quellsignale 4h. Entryfenster: ${run.windows.map(w=>date(w.start)+' bis '+date(w.end)+(run.eligibility?.[w.name]===false?' (nicht auswertbar: zu wenig Vorgeschichte)':'')).join('; ')}. Andere Zeiträume enthalten in dieser Version keine berechneten Entries.`;
      await refresh();
    }
    async function loadRuns(preferred=null,focusEnd=false){
      if(loadingRuns)return;
      loadingRuns=true;activeSymbol=state.symbol;const symbol=state.symbol;
      if(job && !pollTimer)poll();
      selected=null;selectedId=preferred?selectedId:null;items=[];run=null;loadedKey=null;generation++;drawDetail();drawList();ctx.redraw();
      message('Gespeicherte Untersuchungen suchen …');
      try{
        const response=await api('runs?'+new URLSearchParams({symbol}));
        if(symbol!==state.symbol || !enabled)return;
        runs=response.items;
        $('entry-run').innerHTML=runs.length?runs.map(r=>`<option value="${esc(r.id)}">${esc(r.source==='event_case_study'?'Backtest':'Lokale Signalsuche')} · ${r.caseCount} Fälle · ${esc(r.id.slice(0,8))}</option>`).join(''):'<option>Keine gespeicherte Untersuchung</option>';
        if(!runs.length){$('entry-coverage').textContent='Noch keine gespeicherten Einstiege. Unten eine lokale Berechnung starten.';message('Noch keine Untersuchung für diese Aktie.');return;}
        const chosen=runs.find(r=>r.id===preferred)?.id || runs[0].id;
        if(chosen!==state.entryRun)selectedId=null;
        const picked=runs.find(r=>r.id===chosen);
        await openRun(chosen,focusEnd && typeof picked.windows.at(-1).end==='number'?iso(picked.windows.at(-1).end):state.asOf);
      }catch(e){message(e.message);}finally{loadingRuns=false;}
    }
    async function toggle(){
      enabled=!enabled;update();
      if(enabled)await loadRuns(state.entryRun);
      else{generation++;items=[];selected=null;selectedId=null;loadedKey=null;ctx.redraw();await ctx.disable();}
    }
    async function poll(){
      if(!job)return;
      pollTimer=null;
      try{
        const v=await api('search?'+new URLSearchParams({id:job}));
        $('entry-build-status').textContent=v.error || `${v.progress.phase}${v.progress.total?' · '+v.progress.done+' / '+v.progress.total:''}`;
        const active=['queued','running','cancelling'].includes(v.status);
        $('entry-build').disabled=active;$('entry-cancel').hidden=!active;
        if(active){pollTimer=setTimeout(poll,1000);return;}
        job=null;localStorage.removeItem('tori-entry-search');
        if(v.status==='completed' && enabled && v.request.symbol===state.symbol)await loadRuns(v.run_id,true);
      }catch(e){$('entry-build-status').textContent=e.message;$('entry-build').disabled=false;}
    }
    $('entry-history-toggle').onclick=toggle;
    $('entry-history-panel').querySelector('details').addEventListener('toggle',update);
    function draft(){if(run && selectedId)drafts.set(run.id+'|'+selectedId,{verdict:$('entry-verdict').value,note:$('entry-note').value});}
    $('entry-note').oninput=draft;$('entry-verdict').onchange=draft;
    $('entry-run').onchange=()=>{selectedId=null;openRun($('entry-run').value,state.asOf);};
    for(const id of ['entry-family','entry-cohort','entry-filled','entry-quality'])$(id).onchange=()=>{selectedId=null;selected=null;loadedKey=null;refresh();};
    $('entry-case-list').onclick=e=>{const b=e.target.closest('[data-entry-case]');if(b)chooseCase(b.dataset.entryCase);};
    $('entry-replay').onclick=async()=>{
      if(!selected?.signal)return;ctx.setTool(false);state.timeframe='4h';
      document.querySelectorAll('[data-tf]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tf==='4h')));
      await ctx.open(run,iso(selected.signal.signalAt));
    };
    async function saveReview(remove=false){
      if(!selectedId || !run)return;
      const id=selectedId,whichRun=run.id;
      try{
        await api('review',{run:whichRun,case:id,verdict:$('entry-verdict').value,note:$('entry-note').value,delete:remove});
        if(id!==selectedId || run.id!==whichRun)return;
        drafts.delete(whichRun+'|'+id);
        if(remove){$('entry-note').value='';$('entry-verdict').value='unclear';}
        if(selected)selected.review=remove?null:{verdict:$('entry-verdict').value,note:$('entry-note').value};
        $('entry-review-status').textContent=remove?'Bewertung gelöscht.':'Bewertung dauerhaft gespeichert.';
      }catch(e){$('entry-review-status').textContent=e.message;}
    }
    $('entry-review-save').onclick=()=>saveReview();$('entry-review-delete').onclick=()=>saveReview(true);
    $('entry-build').onclick=async()=>{
      try{
        $('entry-build').disabled=true;
        const result=await api('search',{symbol:state.symbol,start:$('entry-start').value || null,end:$('entry-end').value || null});
        job=result.id;localStorage.setItem('tori-entry-search',job);await poll();
      }catch(e){$('entry-build-status').textContent=e.message;$('entry-build').disabled=false;}
    };
    $('entry-cancel').onclick=async()=>{if(job){await api('cancel',{id:job});$('entry-build-status').textContent='Abbruch angefordert; laufender Rechenschritt wird beendet.';}};
    ctx.chart.subscribeClick?.(p=>{
      if(!current() || ctx.rayLayer.active || ctx.rayLayer.measureActive)return;
      const id=String(p.hoveredObjectId || '');if(id.startsWith('entry:'))chooseCase(id.slice(6));
    });
    update();
    try{job=localStorage.getItem('tori-entry-search');if(job)poll();}catch{}
    return {
      selectedId:()=>selectedId,
      priceBounds(from,to){
        if(!current() || !selected?.signal || selected.signal.signalAt<from || selected.signal.signalAt>to)return [];
        return frozenRays().filter(r=>to>=r.a.time).flatMap(r=>[Math.max(from,r.a.time),to].map(t=>RayGeometry.candleValue(state.data.axis,r,t))).filter(v=>v>0 && Number.isFinite(v));
      },
      decorate(output){
        if(!current())return;
        output.push(...markers(items,state.data.bars,state.data.analysisCutoff,state.theme));
        output.push(...contacts(selected,state.data.bars,state.data.analysisCutoff,state.theme));
        output.sort((a,b)=>a.time-b.time);
        ctx.rayLayer.automatic.push(...frozenRays());
      },
      onRender(){
        if(!enabled)return;
        if(activeSymbol!==state.symbol && !loadingRuns){loadRuns(state.entryRun);return;}
        if(run && state.entryRun!==run.id){items=[];selected=null;drawDetail();return;}
        drawDetail();refresh();
      }
    };
  }
  const api={attach,markers,signalBar,fixedLines,contacts};
  if(typeof module!=='undefined')module.exports=api;
  root.EntryHistory=api;
})(typeof globalThis!=='undefined'?globalThis:window);
