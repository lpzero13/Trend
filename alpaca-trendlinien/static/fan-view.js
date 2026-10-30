(function (root) {
  "use strict";
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const number = value => value == null ? "—" : new Intl.NumberFormat("de-DE", {maximumFractionDigits:2}).format(value);
  const date = value => value ? new Date(value*1000).toLocaleString("de-DE", {timeZone:"America/New_York", dateStyle:"short", timeStyle:"short"})+" ET" : "—";
  const labels = {two:"2 Kontakte",three_young:"3+ Kontakte, noch zu jung",qualified:"3+ Kontakte und Mindestalter",
    breakout:"Ausbruch",retest:"Retest der roten Linie",master:"Pine Master 29.10.",extreme:"Pine-Fächer",local:"Mehrere Startanker",
    filled:"Modell-Einstieg",rejected:"Größe/Risiko nicht ausführbar",cancelled:"Am Open verworfen",pending:"Ausführung noch offen",
    unavailable:"Ausführungsdaten fehlen",closed:"Geschlossen",open:"Noch offen",censored:"Verlauf unvollständig",
    no_signal_before_boundary:"Kein Signal bis Datenende",unknown_source_gap:"Suche durch Datenlücke ungeklärt",
    queued:"Wartet",running:"Läuft",succeeded:"Abgeschlossen",partial:"Teilweise abgeschlossen",failed:"Fehler",cancel_requested:"Abbruch angefordert"};
  const label = value => labels[value] || value;
  function chartLink(item, job, asof) {
    return "/?"+new URLSearchParams({dataset:item.datasetId,symbol:item.symbol,tf:item.timeframe,
      engine:"fan_"+item.geometry,fan_job:job,fan_case:item.id,
      asof:new Date((asof ?? item.signal.signalAt)*1000).toISOString()});
  }
  function groups(summary) {
    return (summary.groups || []).map(g => `<tr><td>${esc(label(g.geometry))}<br><small>${esc(label(g.variant))}<br>${esc(g.dataKind === "synthetic" ? "SYNTHETISCH" : g.feed || "")} / ${esc(g.adjustment || "")}</small></td><td>${esc(label(g.cohort))}</td><td>${g.uniqueSignals}<br><small>${esc(Object.entries(g.entryStates).map(([k,v])=>`${label(k)}: ${v}`).join(" · "))}</small></td><td>${g.origins} Starts / ${g.selectedUniqueSignals} verschiedene Signale<br><small>${esc(Object.entries(g.originStates).map(([k,v])=>`${label(k)}: ${v}`).join(" · "))}</small></td><td>${Object.entries(g.paths).map(([name,p])=>`<div>${esc(name)}: ${esc(Object.entries(p.states).map(([k,v])=>`${label(k)} ${v}`).join(" / "))}; Mittel geschlossener Fälle ${number(p.closedOnlyMeanReturnPct)} %${p.ambiguous?`; ${p.ambiguous} OHLC-mehrdeutig`:""}</div>`).join("") || "—"}</td></tr>`).join("");
  }
  function cases(items, job) {
    return items.map(c => {
      if(c.kind === "origin") return `<details data-case="${esc(c.id)}"><summary>${esc(c.symbol)} · Start ${esc(date(c.startAt))} · ${esc(label(c.geometry))}</summary><p>Damals ${c.atStart.trackedScenarios} beobachtete Linien. Die Auswahl lief danach kerzenweise weiter.</p><ul>${c.selections.map(s=>`<li>${esc(label(s.variant))} / ${esc(label(s.cohort))}: ${esc(label(s.status))}${s.entryId?` · <a href="${esc(chartLink({...c,id:s.entryId},job,c.startAt))}" target="_blank" rel="noopener">Ab Startpunkt im Chart prüfen</a>`:""}</li>`).join("")}</ul></details>`;
      const e=c.entry, signal=c.signal;
      return `<details data-case="${esc(c.id)}"><summary>${esc(c.symbol)} · ${esc(date(signal.signalAt))} · ${esc(label(c.geometry))} · ${esc(label(c.variant))} · ${esc(label(c.cohort))} · ${esc(label(e.status))}</summary><p><a href="${esc(chartLink(c,job))}" target="_blank" rel="noopener">Signal im Chart öffnen</a> – dort die Tori-Analyse einschalten. Originalsignal und Stop bleiben gebunden.</p><p>${c.dataKind==="synthetic"?"<strong>Synthetischer Technikfall.</strong> ":""}Signal-Schluss ${number(signal.signalClose)}, geplanter Stop ${number(signal.initialStop)}, nächstes Modell-Open ${esc(date(e.entryAt))}: ${number(e.entryPrice)}. ${number(e.quantity)} ganze Kurseinheiten, geplantes Kursrisiko ${number(e.plannedRisk)}.</p><p>Kontakte ${signal.line.contacts}, Reaktionskontakte ${signal.line.reactionContacts}. ${c.alternativeSignalIds?.length||0} weitere Linienmeldungen dieses Zeitpunkts zusammengefasst. Ausführungsstatus: ${esc(e.reason || label(e.status))}.</p><table><thead><tr><th>Beobachtung</th><th>Schlusskursänderung</th><th>Pfad vollständig?</th></tr></thead><tbody>${Object.entries(c.observations).map(([h,o])=>`<tr><td>${esc(h)} Sitzungen</td><td>${number(o.return_pct ?? o.returnPct)} %</td><td>${o.pathComplete===true?"Ja":o.pathComplete===false?"Nein":"Unbekannt"}</td></tr>`).join("")}</tbody></table><table><thead><tr><th>Stopmodell / Sitzungen</th><th>Status</th><th>Ergebnis / Kurseinheit</th><th>Nachziehen</th></tr></thead><tbody>${Object.entries(c.paths).map(([name,p])=>`<tr><td>${esc(name)}</td><td>${esc(label(p.status))} · ${esc(p.reason)}</td><td>${number(p.netReturnPct)} %${p.intrabarAmbiguous?" · Stop zuerst (OHLC-mehrdeutig)":""}</td><td>${p.stopEvents.length} bestätigte Anpassungen</td></tr>`).join("")}</tbody></table><small>Einzelmodell ohne gemeinsame Depotverwaltung; verwendete Bereinigung und Kurswährung beachten.</small></details>`;
    }).join("");
  }
  const api={esc,number,date,label,chartLink,groups,cases};
  if(typeof module!=="undefined"&&module.exports) module.exports=api;
  else root.FanView=api;
})(typeof globalThis!=="undefined"?globalThis:this);
