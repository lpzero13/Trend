"""Versioned present-day US universes from issuer holdings, not historical membership.

GET-style inventory is offline. Refresh is explicit, bounded and fixed-host.
ETF proxies are labelled as such; no claim of licensed exact index membership.
"""
from datetime import datetime, timezone
import hashlib
import html
import io
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from database import connection
from models import DataError
import archive_state as state

SS = '{urn:schemas-microsoft-com:office:spreadsheet}'
X = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
BASE = 'https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?appSubType=ISHARES&appType=PRODUCT_PAGE&component=fundDownload&locale=en_US&portfolioId={}&targetSite=us-ishares&userType=individual'
DEFINITIONS = {
    'dow30': {'name': 'Dow Jones · DIA-Bestand', 'url': 'https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-dia.xlsx', 'sizeRange': (30, 30), 'kind': 'xlsx'},
    'sp100': {'name': 'S&P 100 · OEF-Bestand', 'url': BASE.format(239723), 'sizeRange': (95, 110), 'kind': 'xml'},
    'nasdaq100': {'name': 'Nasdaq-100 · CNDX-Bestand', 'url': 'https://www.blackrock.com/varnish-api/uk-retail01-product-data/product-data/api/v1/get-fund-document?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=ishares-uk&locale=en_GB&portfolioId=253741&component=fundDownloadV2&userType=individual', 'sizeRange': (95, 110), 'kind': 'xml'},
    'sp500': {'name': 'S&P 500 · IVV-Bestand', 'url': BASE.format(239726), 'sizeRange': (480, 520), 'kind': 'xml'},
    'russell1000': {'name': 'Russell 1000 · IWB-Bestand', 'url': BASE.format(239707), 'sizeRange': (900, 1100), 'kind': 'xml'},
    'russell2000': {'name': 'Russell 2000 · IWM-Bestand', 'url': BASE.format(239710), 'sizeRange': (1800, 2200), 'kind': 'xml'},
    'dow_plus70': {'name': 'Dow-30 + 70 aus dem S&P 100', 'components': ('dow30', 'sp100'), 'sizeRange': (100, 100)},
}


def symbol(value):
    value = str(value or '').strip().replace(' ', '.')
    if not re.fullmatch('[A-Z][A-Z0-9./-]{0,29}', value): raise ValueError('symbol')
    return value


def date_text(value):
    value = str(value or '').strip().replace('As of ', '').replace('Sept', 'Sep')
    for fmt in ('%d-%b-%Y', '%b %d, %Y', '%m/%d/%Y', '%d/%b/%Y', '%Y-%m-%d'):
        try: return datetime.strptime(value, fmt).date().isoformat()
        except ValueError: pass
    raise ValueError('source date')


def xml(raw):
    text = raw.decode('utf-8-sig')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): raise ValueError('external XML entity')
    # Some issuer exports contain unescaped ampersands in hyperlink attributes.
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[\da-fA-F]+;)', '&amp;', text)
    return ET.fromstring(text)


def xml_rows(raw):
    root = xml(raw)
    sheet = next((s for s in root.findall(SS+'Worksheet') if s.get(SS+'Name') in ('Holdings', 'Positions')), None)
    if sheet is None: raise ValueError('holdings sheet')
    rows = []
    for row in sheet.findall(SS+'Table/'+SS+'Row'):
        cells = []
        for cell in row.findall(SS+'Cell'):
            index = int(cell.get(SS+'Index', len(cells)+1))-1
            while len(cells) < index: cells.append('')
            node = cell.find(SS+'Data')
            cells.append(node.text or '' if node is not None else '')
        rows.append(cells)
    return rows


def xlsx_rows(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist()) > 50_000_000: raise ValueError('oversized workbook')
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(X+'si')]
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in root.findall(X+'sheetData/'+X+'row'):
            cells = []
            for cell in row.findall(X+'c'):
                letters = re.match('[A-Z]+', cell.get('r')).group()
                column = 0
                for c in letters: column = column*26+ord(c)-64
                while len(cells) < column: cells.append('')
                node = cell.find(X+'v')
                val = node.text if node is not None else ''
                if cell.get('t') == 's': val = strings[int(val)]
                elif cell.get('t') == 'inlineStr': val = ''.join(cell.find(X+'is').itertext())
                cells[column-1] = val
            rows.append(cells)
    return rows


def parse(raw, kind):
    rows = xlsx_rows(raw) if raw[:2] == b'PK' else xml_rows(raw)
    asof = None
    header = None
    members = []
    exclusions = []
    for row in rows:
        if not header:
            for i, v in enumerate(row):
                if str(v).strip() in ('Holdings:', 'Fund Holdings as of', 'as of') and i+1 < len(row):
                    asof = date_text(row[i+1])
            if 'Ticker' in row or 'Issuer Ticker' in row:
                header = {str(v).strip(): i for i, v in enumerate(row)}
            continue
        def get(*names):
            return next((row[header[n]] for n in names if n in header and header[n] < len(row)), '')
        if 'Asset Class' in header and get('Asset Class') != 'Equity': continue
        if not get('Ticker', 'Issuer Ticker'): continue
        if get('Name') == 'US DOLLAR': continue
        if re.search(r'\b(CVR|RESTR|PRVT)\b',get('Name'),re.IGNORECASE):
            exclusions.append({'name':get('Name'),'reason':'Restricted/private/contingent-value position; not an ordinary listed equity quote'})
            continue
        if get('Ticker', 'Issuer Ticker') in ('--', '-'):
            exclusions.append({'name': get('Name'), 'reason': 'Issuer supplies no queryable ticker (e.g. restricted/private/CVR position)'})
            continue
        try:
            ticker = symbol(get('Ticker', 'Issuer Ticker'))
            if ticker in ('USD', 'CASH'): continue
            members.append({'symbol': ticker, 'name': get('Name'), 'weight': float(get('Weight (%)', 'Weight') or 0)})
        except ValueError: raise ValueError('unmapped equity ticker') from None
    if not asof or not members or len({m['symbol'] for m in members}) != len(members): raise ValueError('date/members/duplicates')
    return asof, members, exclusions


def read(key):
    if key not in DEFINITIONS: raise DataError('Unbekanntes Universum.', 400)
    with connection() as db: return state.value(db, 'universe:v1:'+key)


def catalog():
    items = []
    for key, definition in DEFINITIONS.items():
        cached = read(key)
        items.append({'id': key, 'name': definition['name'], 'ready': cached is not None,
                      'count': len(cached['members']) if cached else None,
                      'asOf': cached.get('asOf') if cached else None,
                      'unmappedHoldings': len(cached.get('excludedHoldings', [])) if cached else 0,
                      'definition': 'current ETF equity holdings; no historical index membership'})
    return {'items': items, 'marketProviderCalls': 0}


def refresh(key):
    if key not in DEFINITIONS: raise DataError('Unbekanntes Universum.', 400)
    definition = DEFINITIONS[key]
    if 'components' in definition:
        dow = read('dow30') or refresh('dow30')
        sp = read('sp100') or refresh('sp100')
        members = list(dow['members']); seen = {m['symbol'] for m in members}
        for m in sorted(sp['members'], key=lambda m: (-m['weight'], m['symbol'])):
            if m['symbol'] not in seen and m['symbol'] != 'GOOG':
                members.append(m); seen.add(m['symbol'])
            if len(members) == 100: break
        sources = dow['sources']+sp['sources']
        asof = min(dow['asOf'], sp['asOf'])
        exclusions = dow.get('excludedHoldings', [])+sp.get('excludedHoldings', [])
    else:
        request = urllib.request.Request(definition['url'], headers={'User-Agent': 'Mozilla/5.0 ToriUniverse/1'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response: raw = response.read(30_000_001)
            if len(raw) > 30_000_000: raise ValueError('oversized source')
            asof, members, exclusions = parse(raw, definition['kind'])
        except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile):
            raise DataError('Universumsquelle nicht vollständig lesbar; alter Stand bleibt erhalten.', 502) from None
        sources = [{'url': definition['url'], 'asOf': asof, 'sha256': hashlib.sha256(raw).hexdigest()}]
    low, high = definition['sizeRange']
    if not low <= len(members) <= high: raise DataError('Unerwartete Universumsgröße; keine unvollständige Liste übernommen.', 502)
    result = {'name': definition['name'], 'asOf': asof, 'members': members, 'sources': sources,
              'excludedHoldings': exclusions,
              'definition': 'ETF equity holdings proxy, current membership; all share classes except custom Dow+70 rule',
              'fetchedAt': datetime.now(timezone.utc).isoformat()}
    with connection() as db: state.put(db, 'universe:v1:'+key, result)
    return result


def combine(keys):
    if not isinstance(keys, list) or not keys or any(k not in DEFINITIONS for k in keys):
        raise DataError('Mindestens ein bekanntes Universum auswählen.', 400)
    members = {}; sources = []; names = []
    for key in dict.fromkeys(keys):
        item = read(key)
        if not item: raise DataError('Universumslisten zuerst aktualisieren.', 409)
        names.append(item['name']); sources.extend(item['sources'])
        for member in item['members']: members[member['symbol']] = member
    unique_sources = {s['url']+s['sha256']: s for s in sources}
    return {'symbols': sorted(members), 'universe': {'name': ' + '.join(names), 'ids': list(dict.fromkeys(keys)),
            'members': list(members.values()), 'sources': list(unique_sources.values()),
            'definition': 'Deduplicated union of frozen current ETF equity holdings'}}
