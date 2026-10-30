(function(root){
  'use strict';
  const $=id=>document.getElementById(id), V=root.ToriWorkbench, LC=root.LightweightCharts;
  let current=null, drawings=V.model(), dirty=false, tool=null, first=null, chart=null, candle=null, lines=[], markers=null, offset=0, page=null;
  const roles={red:'Rot',green:'Grün',resistance:'Widerstand'},colors={red:'#ff4569',green:'#00b883',resistance:'#3687ff'};
  async function request(path,body){const r=await apiFetch(path,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(d.error||'Anfrage fehlgeschlagen');return d;}
  function action(fn){return async e=>{e?.preventDefault?.();$('wb-error').hidden=true;try{await fn(e)}catch(err){$('wb-error').textContent=err.message;$('wb-error').hidden=false}}}
  function options(id,items,selected){const el=$(id);el.replaceChildren(...items.map(x=>{const o=document.createElement('option');o.value=x.value;o.textContent=x.label;return o}));if(items.some(x=>x.value===selected))el.value=selected;}
  function stop(){tool=null;first=null;document.querySelectorAll('[data-tool]').forEach(b=>b.setAttribute('aria-pressed','false'));}
  function guard(){if(dirty)throw Error('Bitte die Bewertung zuerst speichern. Ungespeicherte Änderungen werden nicht verworfen.');}
  function selected(){return $('wb-ray').value;}
  function render(){
    const id=selected();options('wb-ray',drawings.rays.map(r=>({value:r.id,label:`${roles[r.role]} · ${r.contacts.length} Kontaktmarkierungen`})),id);
    $('wb-undo').disabled=!drawings.canUndo;$('wb-delete').disabled=!drawings.rays.length;
    $('wb-reveal').disabled=!current||!current.label||dirty||current.revealed;
    $('wb-state').textContent=`${dirty?'Ungespeicherte Änderungen · ':''}${current?.revealed?'Engine aufgedeckt':'Engine verborgen'}${current?.tainted?' · spätere Bewertung beeinflusst':''}`;
    if(!chart)return;lines.forEach(s=>chart.removeSeries(s));lines=[];
    function draw(r,color,dash){const p=V.points(r,current.bars);if(!p.length)return;const s=chart.addSeries(LC.LineSeries,{color,lineWidth:2,lineStyle:dash?2:0,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});s.setData(p);lines.push(s)}
    drawings.rays.forEach(r=>draw(r,colors[r.role],false));
    (current?.engine?.rays||[]).forEach(r=>draw(r.ray,colors[r.role],true));
    (current?.engine?.resistances||[]).forEach((price,i)=>{if(current.bars.length>1)draw({a_time:current.bars[0].time,b_time:current.bars[1].time,a_price:price,b_price:price},'#3687ff',true)});
    const ownMarks=drawings.rays.flatMap(r=>r.contacts.filter(t=>current.bars.some(b=>b.time===t)).map(t=>({time:t,position:r.role==='green'?'belowBar':'aboveBar',color:colors[r.role],shape:'circle',text:roles[r.role]})));
    if(first)ownMarks.push({time:first.time,position:'aboveBar',color:'#3687ff',shape:'circle',text:'Erster Anker'});
    ownMarks.sort((a,b)=>a.time-b.time);
    markers?.setMarkers(ownMarks);
  }
  function makeChart(){
    chart?.remove();lines=[];const dark=document.documentElement.dataset.theme==='dark';
    chart=LC.createChart($('wb-chart'),{autoSize:true,layout:{background:{color:dark?'#10151e':'#ffffff'},textColor:dark?'#d8dfe9':'#273143'},grid:{vertLines:{color:dark?'#242b38':'#edf0f4'},horzLines:{color:dark?'#242b38':'#edf0f4'}},timeScale:{timeVisible:true},rightPriceScale:{borderVisible:false}});
    candle=chart.addSeries(LC.CandlestickSeries,{upColor:'#00aa83',downColor:'#ff4569',wickUpColor:'#00aa83',wickDownColor:'#ff4569',borderVisible:false});candle.setData(current.bars);
    markers=LC.createSeriesMarkers(candle,[]);chart.subscribeClick(action(p=>{
      if(!tool||!p.point)return;let bar=current.bars.find(b=>b.time===p.time);
      if(!bar&&Number.isFinite(p.logical))bar=current.bars[Math.round(p.logical)];if(!bar)return;
      if(tool==='contact'){if(!selected())throw Error('Zuerst eine eigene Linie auswählen.');if(drawings.rays.find(r=>r.id===selected()).contacts.length>=24&&!drawings.rays.find(r=>r.id===selected()).contacts.includes(bar.time))throw Error('Höchstens 24 Kontaktmarkierungen.');drawings.contact(selected(),bar.time);dirty=true;render();return}
      const price=candle.coordinateToPrice(p.point.y);if(price==null||price<=0)return;
      if(!first){first={time:bar.time,price};$('wb-help').textContent='Jetzt den zweiten Anker rechts vom ersten anklicken.';render();return}
      if(drawings.rays.length>=16)throw Error('Höchstens 16 eigene Linien.');
      const r=V.ray(tool,first,{time:bar.time,price},'r_'+root.crypto.randomUUID());drawings.change([...drawings.rays,r]);dirty=true;stop();render();$('wb-ray').value=r.id;$('wb-help').textContent='Linie hinzugefügt. Weitere Kontakte über „Kontakt markieren“ anklicken; erneuter Klick entfernt die Markierung.';
    }));chart.timeScale().fitContent();render();
  }
  async function comparison(){if(!$('wb-pack').value)return;const data=await request(`/api/workbench/packs/${$('wb-pack').value}/compare`);$('wb-comparison').textContent=JSON.stringify(data,null,2);}
  async function loadCase(){guard();const p=$('wb-pack').value,c=$('wb-case').value;if(!p||!c){$('wb-meta').textContent='Noch keine vorbereiteten Fälle. Pakete werden per CLI aus gespeicherten Daten registriert.';return}
    current=await request(`/api/workbench/packs/${p}/${c}`);drawings=V.model(current.label?.rays||[]);dirty=false;stop();$('wb-verdict').value=current.label?.verdict||'unclear';$('wb-note').value=current.label?.note||'';
    $('wb-meta').textContent=`${current.symbol} · ${current.timeframe} · ${current.feed.toUpperCase()} · ${current.adjustment} · bis ${new Date(current.cutoff*1000).toLocaleString('de-DE',{timeZone:'America/New_York'})} New York · ${current.bars.length} bekannte Kerzen${current.dataKind==='synthetic'?' · SYNTHETISCHE TESTDATEN':''}`;makeChart();await comparison();
  }
  async function loadPage(){guard();const p=$('wb-pack').value;if(!p){$('wb-meta').textContent='Noch keine Sichtprüfpakete registriert.';return}page=await request(`/api/workbench/packs/${p}?offset=${offset}&limit=50`);options('wb-case',page.items.map(c=>({value:c.id,label:`${c.symbol} · ${c.timeframe} · ${new Date(c.cutoff*1000).toISOString().slice(0,10)}${c.labelled?' · bewertet':''}${c.revealed?' · aufgedeckt':''}`})));$('wb-previous').disabled=offset===0;$('wb-next').disabled=!page.page.hasMore;await loadCase();}
  async function refresh(){guard();const old=$('wb-pack').value||new URLSearchParams(root.location?.search||'').get('pack'),d=await request('/api/workbench/packs');options('wb-pack',d.items.map(p=>({value:p.id,label:`${p.label} · ${p.count} Fälle`})),old);await loadPage();}
  document.querySelectorAll('[data-tool]').forEach(b=>b.addEventListener('click',()=>{stop();tool=b.dataset.tool;b.setAttribute('aria-pressed','true');$('wb-help').textContent=tool==='contact'?'Linie unten auswählen, dann Kontaktkerze anklicken. Erneuter Klick entfernt die Markierung.':'Zwei Anker von links nach rechts anklicken.';render()}));
  $('wb-cancel').onclick=()=>{stop();render()};$('wb-fit').onclick=()=>chart?.timeScale().fitContent();$('wb-delete').onclick=()=>{drawings.remove(selected());dirty=true;render()};$('wb-undo').onclick=()=>{drawings.undo();dirty=true;render()};
  $('wb-note').oninput=$('wb-verdict').onchange=()=>{dirty=true;render()};$('wb-form').onsubmit=action(async()=>{if(!current)throw Error('Zuerst einen Fall laden.');current=await request(`/api/workbench/packs/${current.packId}/${current.id}/label`,{revision:current.revision,verdict:$('wb-verdict').value,note:$('wb-note').value,rays:drawings.rays});dirty=false;render();await comparison()});
  $('wb-reveal').onclick=action(async()=>{guard();if(!current)return;current=await request(`/api/workbench/packs/${current.packId}/${current.id}/reveal`,{revision:current.revision});render();await comparison()});
  $('wb-pack').onchange=action(async()=>{offset=0;await loadPage()});$('wb-case').onchange=action(loadCase);$('wb-refresh').onclick=action(refresh);$('wb-next').onclick=action(async()=>{guard();offset+=50;await loadPage()});$('wb-previous').onclick=action(async()=>{guard();offset=Math.max(0,offset-50);await loadPage()});
  try{const saved=JSON.parse(root.localStorage.getItem('tori-theme'));if(['light','dark'].includes(saved))document.documentElement.dataset.theme=saved}catch{}
  $('wb-theme').onclick=()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;try{root.localStorage.setItem('tori-theme',JSON.stringify(theme))}catch{}if(current)makeChart()};
  root.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});action(refresh)();
})(globalThis);
