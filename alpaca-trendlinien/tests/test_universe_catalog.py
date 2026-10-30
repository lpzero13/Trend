import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import universe_catalog as u
from database import connection
import archive_state as state
from models import DataError


def workbook(rows):
    import html
    body=''.join('<ss:Row>'+''.join('<ss:Cell><ss:Data ss:Type="String">'+html.escape(str(v))+'</ss:Data></ss:Cell>' for v in row)+'</ss:Row>' for row in rows)
    return ('<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><ss:Worksheet ss:Name="Holdings"><ss:Table>'+body+'</ss:Table></ss:Worksheet></ss:Workbook>').encode()


class UniverseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'TORI_DATA_DIR':self.temp.name});self.env.start()
    def tearDown(self):self.env.stop();self.temp.cleanup()

    def test_xml_asset_filter_class_mapping_dates_and_excluded_positions(self):
        raw=workbook([['Fund Holdings as of','Oct 28, 2026'],['Ticker','Name','Asset Class','Weight (%)'],
                      ['BRK B','BERKSHIRE','Equity','2.0'],['USD','CASH','Cash','1'],
                      ['--','NO TICKER','Equity','0'],['ADRO','CHINOOK CVR','Equity','0']])
        day,members,excluded=u.parse(raw,'xml')
        self.assertEqual(day,'2026-10-28');self.assertEqual([m['symbol'] for m in members],['BRK.B'])
        self.assertEqual(len(excluded),2)

    def test_uk_nasdaq_date_and_ticker_header(self):
        raw=workbook([['as of','28/Oct/2026'],['Issuer Ticker','Name','Asset Class','Weight (%)'],['AAPL','Apple','Equity','7']])
        self.assertEqual(u.parse(raw,'xml')[1][0]['symbol'],'AAPL')

    def test_duplicate_ordinary_ticker_and_external_entity_rejected(self):
        raw=workbook([['as of','28/Oct/2026'],['Ticker','Name','Asset Class','Weight (%)'],['AAA','A','Equity','1'],['AAA','A','Equity','2']])
        with self.assertRaises(ValueError):u.parse(raw,'xml')
        with self.assertRaises(ValueError):u.xml(b'<!DOCTYPE abc SYSTEM "file:///secret"><root/>')

    def test_minimal_native_xlsx_without_office_dependency(self):
        main='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        strings=['Holdings:','As of 28-Oct-2026','Name','Ticker','Weight','Apple','AAPL','US DOLLAR','-']
        shared='<sst xmlns="'+main+'">'+''.join('<si><t>'+s+'</t></si>' for s in strings)+'</sst>'
        sheet='<worksheet xmlns="'+main+'"><sheetData><row><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row><row><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c><c r="C2" t="s"><v>4</v></c></row><row><c r="A3" t="s"><v>5</v></c><c r="B3" t="s"><v>6</v></c><c r="C3"><v>2</v></c></row><row><c r="A4" t="s"><v>7</v></c><c r="B4" t="s"><v>8</v></c></row></sheetData></worksheet>'
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('xl/sharedStrings.xml',shared);z.writestr('xl/worksheets/sheet1.xml',sheet)
        self.assertEqual(u.parse(out.getvalue(),'xlsx')[1][0]['symbol'],'AAPL')

    def test_union_frozen_sources_deduplicated_and_offline_inventory(self):
        for key,members in [('dow30',['AAPL','MSFT']),('sp100',['AAPL','NVDA'])]:
            with connection() as db:state.put(db,'universe:v1:'+key,{'name':key,'members':[{'symbol':s} for s in members],
                    'sources':[{'url':key,'sha256':'abc','asOf':'2026-10-28'}],'asOf':'2026-10-28'})
        with patch('universe_catalog.urllib.request.urlopen',side_effect=AssertionError('GET must stay offline')):
            selected=u.combine(['dow30','sp100','dow30']);catalog=u.catalog()
        self.assertEqual(selected['symbols'],['AAPL','MSFT','NVDA'])
        self.assertEqual(catalog['marketProviderCalls'],0)
        self.assertEqual(len(selected['universe']['sources']),2)

    def test_source_failure_retains_old_catalog_and_unknown_id_rejected(self):
        with connection() as db:state.put(db,'universe:v1:dow30',{'members':[{'symbol':'AAPL'}]})
        with patch('universe_catalog.urllib.request.urlopen',side_effect=OSError('offline')):
            with self.assertRaises(DataError):u.refresh('dow30')
        self.assertEqual(u.read('dow30')['members'][0]['symbol'],'AAPL')
        with self.assertRaises(DataError):u.combine(['not-a-universe'])
