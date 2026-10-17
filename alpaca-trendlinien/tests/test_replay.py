import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from alpaca import next_bar_close, DataError, NY
from server import step_payload, chart_payload
from test_history import dataset, metadata, NOW


class ReplayTests(unittest.TestCase):
    def cache(self, root, tf, rows, end=NOW):
        path=Path(root)/f'data/market/TEST_{tf}_iex_raw.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'symbol':'TEST','timeframe':tf,'feed':'iex','adjustment':'raw',
            'requested_start':'2025-01-01T00:00:00+00:00','requested_end':end.isoformat(),
            'fetched_at':NOW.timestamp(),'bars':rows}),'utf-8')

    def test_next_close_skips_weekend_for_each_timeframe_without_network(self):
        for tf in ['1h','4h','1D']:
            with self.subTest(tf=tf),tempfile.TemporaryDirectory() as root,patch('alpaca.ROOT',Path(root)):
                bars=dataset(tf)
                rows=[{'t':datetime.fromtimestamp(b.time,timezone.utc).isoformat(),'o':b.open,'h':b.high,'l':b.low,'c':b.close,'v':b.volume} for b in bars]
                self.cache(root,tf,rows)
                friday=[b for b in bars if datetime.fromtimestamp(b.time,NY).day==9][-1]
                monday=[b for b in bars if datetime.fromtimestamp(b.time,NY).day==12][0]
                with patch('alpaca._request') as network:
                    target=next_bar_close('TEST',tf,datetime.fromtimestamp(friday.end,timezone.utc),now=NOW)
                    network.assert_not_called()
                self.assertEqual(target,monday.end)

    def test_no_future_unfinished_bar_can_be_a_step_target(self):
        with tempfile.TemporaryDirectory() as root,patch('alpaca.ROOT',Path(root)):
            self.cache(root,'1h',[{'t':'2026-10-17T11:00:00Z','o':100,'h':101,'l':99,'c':100,'v':10}])
            with patch('alpaca._request') as network, self.assertRaises(DataError) as error:
                next_bar_close('TEST','1h',datetime(2026,10,17,10,tzinfo=timezone.utc),now=NOW)
            self.assertEqual(error.exception.status,404)
            network.assert_not_called()

    def test_forward_narrow_window_paginates_and_reuses_its_cache(self):
        rows=[{'t':f'2026-10-12T{hour}:00:00Z','o':100,'h':101,'l':99,'c':100,'v':10} for hour in ['14','15']]
        cutoff=datetime(2026,10,9,20,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as root,patch('alpaca.ROOT',Path(root)),patch('alpaca.credentials',return_value=('fake','fake')):
            with patch('alpaca._request',side_effect=[{'bars':{'TEST':rows[:1]},'next_page_token':'p2'},{'bars':{'TEST':rows[1:]}}]) as network:
                target=next_bar_close('TEST','1h',cutoff,now=NOW)
                self.assertEqual(network.call_count,2)
                params=network.call_args_list[0].args[0]
                self.assertGreater(datetime.fromisoformat(params['start']),cutoff.replace(day=1))
            with patch('alpaca._request') as network:
                second=next_bar_close('TEST','1h',datetime.fromtimestamp(target,timezone.utc),now=NOW)
                network.assert_not_called()
            self.assertEqual(second-target,3600)

    def test_back_and_forward_target_reconstruct_exactly_one_additional_bar(self):
        loader=lambda symbol,tf,**kw:(dataset(tf),metadata(dataset(tf)))
        for tf in ['1h','4h','1D']:
            with self.subTest(tf=tf),patch('server.load_bars',side_effect=loader):
                cutoff=datetime(2026,10,14,20,tzinfo=timezone.utc)
                before=chart_payload('TEST',tf,as_of=cutoff.isoformat())
                target=step_payload('TEST',tf,cutoff.isoformat(),'back')
                after=chart_payload('TEST',tf,as_of=target['asof'])
                self.assertEqual(before['charts'][tf]['bars'][:-1],after['charts'][tf]['bars'])
                with patch('server.next_bar_close',return_value=before['charts'][tf]['bars'][-1]['end']):
                    following=step_payload('TEST',tf,target['asof'],'next')
                    restored=chart_payload('TEST',tf,as_of=following['asof'])
                self.assertEqual(before['charts'],restored['charts'])
                self.assertEqual(before['lanes'],restored['lanes'])

    def test_invalid_direction_symbol_and_cutoff_are_rejected_before_network(self):
        with patch('server.load_bars') as loader,patch('server.next_bar_close') as forward:
            for symbol,tf,stamp,direction in [('TEST','1h','bad','back'),('../TEST','1h',NOW.isoformat(),'next'),('TEST','1m',NOW.isoformat(),'next'),('TEST','1h',NOW.isoformat(),'other')]:
                with self.assertRaises(DataError):step_payload(symbol,tf,stamp,direction)
            loader.assert_not_called();forward.assert_not_called()


if __name__=='__main__':unittest.main()
