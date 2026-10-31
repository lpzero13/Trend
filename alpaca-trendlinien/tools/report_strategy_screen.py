"""Read only completed study artifacts; never opens untested market blocks."""
import argparse
from collections import Counter
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy_screen import read


def report(root):
    root=Path(root);plan=read(root/'plan.json')
    lines=['# Technische Strategiesuche – Ergebnis', '',f"Plan-ID: `{plan['id']}`",'',
           'Vorhandene Aktien: '+', '.join(plan['symbols']),
           '', str(len(plan['policies']))+' vorab festgelegte Varianten; 2.000 USD endliches Depot, ganze Stückzahlen, maximal drei Positionen, 25 % Allokation und 1 % geplantes Entry-Risiko. Preisgewinne nach modellierten Handelskosten; ohne Dividenden, Cashzinsen, Steuern und EUR-Umrechnung.',
           '', 'Historisch getrennte Prüfblöcke dieses Versuchs sind kein Beweis vorher völlig unbekannter Marktdaten. Keine Orders oder Profitgarantie.']
    p=root/'selection.json'
    if not p.exists():return '\n'.join(lines+['','Entwicklung noch nicht abgeschlossen.'])+'\n'
    selection=read(p)
    lines+=['','## Entwicklung / übernommene Regel','',
            'Jeder Entwicklungsfold beginnt mit eigenem Kapital; Mittelwerte sind keine zusammengesetzte Mehrjahresrendite. Bei einem zusätzlichen Aktienkorb wird die bereits eingefrorene Regel übernommen und nicht neu ausgewählt.', '',
            '| Variante | Zugelassen | Ø Fold netto % | Max. 5m-Drawdown % | Trades | Fold-Erträge % |',
            '|---|---|---:|---:|---:|---|']
    ranked=sorted(selection.get('allDevelopment',[]),key=lambda x:-(x['meanFoldReturnPct'] if x['meanFoldReturnPct'] is not None else -1e9))
    for r in ranked:
        avg='—' if r['meanFoldReturnPct'] is None else f"{r['meanFoldReturnPct']:.3f}"
        fold=', '.join('—' if v['markedReturnPct'] is None else f"{v['markedReturnPct']:.2f}" for v in r['folds'])
        lines.append(f"| {r['policy']['id']} | {r['eligible']} | {avg} | {r['worstDrawdownPct']:.3f} | {r['trades']} | {fold} |")
    primary=selection['primary']
    lines+=['', 'Primäre eingefrorene Variante: '+(f"`{primary['id']}`" if primary else '**keine**; '+selection['reason'])]
    for name in ('validation','confirmation'):
        file=root/(name+'-summary.json')
        lines+=['','## '+name,'']
        if not file.exists():lines+=['Kein Ergebnisblock geöffnet/abgeschlossen.'];continue
        result=read(file)
        lines+=['Primäres vorab festgelegtes Tor bestanden: **'+str(result['primaryPassed'])+'**','',
                '| Festgelegter Familiensieger | Netto % | Doppelte Kosten % | 5m-Drawdown % | Trades | Positive Aktien | Tor |',
                '|---|---:|---:|---:|---:|---:|---|']
        for r in result['items']:
            a,b=r['base'],r['doubleCosts']
            fmt=lambda x:'—' if x is None else f'{x:.3f}'
            lines.append(f"| {r['policy']['id']} | {fmt(a['markedReturnPct'])} | {fmt(b['markedReturnPct'])} | {fmt(a['max5mSampledDrawdownPct'])} | {a['accepted']} | {a['positiveSymbols']} | {r['gate']['passed']} |")
        lines+=['','Primäre Einzelprüfungen: '+str(result['primary']['gate']['checks']),
                '',f"39 Kontrollportfolios: vollständig `{result['controls']['complete']}`, 90%-Quantil `{result['controls']['q90ReturnPct']}`, primäre Variante darüber `{result['controls']['aboveQ90']}`.",
                '', 'Kontrollen sind monatlich/aktienweise und nach Safety-/Tagesfilter bedingt; rote Kontaktqualität wird nicht gematcht. Der Rang ist explorativ und kein korrigierter p-Wert.']
    file=root/'leave-one-symbol-out.json'
    if file.exists():
        items=read(file)['items']
        lines+=['','## Weglassen einzelner Aktien in der Entwicklung','',
                '| Weggelassen | Ø Fold netto % |','|---|---:|']
        lines += [f"| {v['excluded']} | {v['meanFoldReturnPct']:.3f} |" for v in items]
    file=root/'combined-summary.json'
    if file.exists():
        c=read(file)
        lines+=['','## Gemeinsames Depot aller 16 Aktien','',
                f"Dasselbe Kapital von 2.000 USD: netto {c['base']['markedReturnPct']:.3f} %, doppelte Kosten {c['doubleCosts']['markedReturnPct']:.3f} %, 5m-Drawdown {c['base']['max5mSampledDrawdownPct']:.3f} %.",
                'Keine Summe zweier Achterdepots; alle Signale konkurrieren um dieselben Positionsplätze. Dieser Korbvergleich ist keine neue unabhängige zeitliche Validierung.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();Path(args.output).write_text(report(args.root),encoding='utf-8')
