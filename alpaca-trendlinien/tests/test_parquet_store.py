import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from datasets import save_dataset, read_dataset, path_for, digest, stored_bytes
from models import DataError
from parquet_store import hydrate, migrate, FORMAT
from test_research import fixture_sources
from test_weekly_chart import days
import maintenance
from database import connection


class ParquetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'runtime'
        self.env=patch.dict(os.environ,{'TORI_DATA_DIR':str(self.root),'TORI_AUTO_ENABLED':'0'})
        self.env.start()
        self.sources={tf:(bars[:100],meta) for tf,(bars,meta) in fixture_sources().items()}

    def tearDown(self):
        self.env.stop();self.temp.cleanup()

    def manifest(self,identity):return json.loads(path_for(identity).read_text('utf-8'))

    def test_exact_roundtrip_preserves_numeric_types_checksums_and_large_integer_volume(self):
        sources=copy.deepcopy(self.sources)
        rows,meta=sources['1h']
        rows[0]=replace(rows[0],open=100,high=101.0,low=99,close=100.125,volume=2**53+1)
        identity=save_dataset('TEST',sources)
        m=self.manifest(identity)
        self.assertEqual(m['storage']['format'],FORMAT)
        self.assertEqual(m['material']['bars'],{})
        value=read_dataset(identity)
        b=value['material']['bars']['1h'][0]
        self.assertIs(type(b['open']),int);self.assertIs(type(b['high']),float)
        self.assertEqual(b['volume'],2**53+1)
        self.assertEqual(digest(value['material']),identity)
        self.assertGreater(stored_bytes(identity),path_for(identity).stat().st_size)

    def test_revision_reuses_unchanged_months_and_old_id_keeps_old_values(self):
        first=save_dataset('TEST',self.sources);before=read_dataset(first)
        sources=copy.deepcopy(self.sources)
        rows,meta=sources['1D'];rows[-1]=replace(rows[-1],volume=201)
        second=save_dataset('TEST',sources)
        a={b['path'] for b in self.manifest(first)['storage']['blocks']}
        b={b['path'] for b in self.manifest(second)['storage']['blocks']}
        self.assertTrue(a&b);self.assertEqual(len(b-a),1)
        self.assertEqual(read_dataset(first),before)
        self.assertEqual(save_dataset('TEST',self.sources),first)

    def test_week_cache_contains_only_complete_exchange_weeks(self):
        daily=days('2025-03-03','2025-04-08')
        sources={tf:(daily,{'normalization':'test'}) for tf in ('1h','4h','1D')}
        identity=save_dataset('WEEK',sources)
        payload,weekly=hydrate(self.manifest(identity),self.root,include_weekly=True)
        self.assertEqual(len(weekly),5)
        self.assertEqual(weekly[-1]['end'],daily[-3].end)
        self.assertNotIn('1W',payload['material']['bars']) # old engine API/identity intact

    def test_missing_corrupt_or_traversing_chunk_fails_closed(self):
        identity=save_dataset('TEST',self.sources);m=self.manifest(identity)
        path=self.root/m['storage']['blocks'][0]['path'];original=path.read_bytes()
        path.write_bytes(b'bad')
        with self.assertRaises(DataError):read_dataset(identity)
        path.write_bytes(original)
        m['storage']['blocks'][0]['path']='../private.parquet'
        path_for(identity).write_text(json.dumps(m),'utf-8')
        with self.assertRaises(DataError):read_dataset(identity)

    def test_migration_retains_identity_metadata_and_restart_is_idempotent(self):
        identity=save_dataset('TEST',self.sources);before=read_dataset(identity)
        # A real old JSON payload, not a changed logical dataset.
        path_for(identity).write_text(json.dumps(before),'utf-8')
        stamp=path_for(identity).stat().st_mtime_ns
        with patch('alpaca._request',side_effect=AssertionError('no provider')):
            self.assertEqual(migrate(identity)['status'],'converted')
            self.assertEqual(migrate(identity)['status'],'already_parquet')
        self.assertEqual(read_dataset(identity),before)
        self.assertEqual(path_for(identity).stat().st_mtime_ns,stamp)
        self.assertEqual(json.loads((self.root/'datasets/legacy-json'/path_for(identity).name).read_text('utf-8')),before)

    def test_failed_conversion_leaves_original_and_atomic_manifest_unpublished(self):
        identity=save_dataset('TEST',self.sources);before=read_dataset(identity)
        path_for(identity).write_text(json.dumps(before),'utf-8')
        with patch('parquet_store.prepare',side_effect=ValueError('test write failure')):
            with self.assertRaises(ValueError):migrate(identity)
        self.assertEqual(json.loads(path_for(identity).read_text('utf-8')),before)
        self.assertEqual(read_dataset(identity),before)

    def test_backup_restore_copies_shared_blocks_once_and_preserves_references(self):
        first=save_dataset('TEST',self.sources)
        sources=copy.deepcopy(self.sources);rows,meta=sources['1D'];rows[-1]=replace(rows[-1],volume=201)
        second=save_dataset('TEST',sources)
        with connection() as db:
            db.execute('INSERT INTO settings VALUES(?,?)',('test',json.dumps({'dataset_ids':{'a':first,'b':second}})))
        target=Path(self.temp.name)/'backup';maintenance.backup(target)
        checked=maintenance.verify(target)
        expected={b['path'] for x in (first,second) for b in self.manifest(x)['storage']['blocks']}
        self.assertEqual({p for p in checked['files'] if p.endswith('.parquet')},expected)
        restored=Path(self.temp.name)/'restore';maintenance.restore(target,restored)
        before=read_dataset(first)
        with patch.dict(os.environ,{'TORI_DATA_DIR':str(restored)}):self.assertEqual(read_dataset(first),before)
        missing=target/next(iter(expected));missing.unlink()
        with self.assertRaises(DataError):maintenance.verify(target)

    def test_legacy_json_backup_schema_remains_restorable(self):
        identity=save_dataset('TEST',self.sources);before=read_dataset(identity)
        path_for(identity).write_text(json.dumps(before),'utf-8')
        with connection():pass
        target=Path(self.temp.name)/'old-backup';maintenance.backup(target)
        path=target/'manifest.json';manifest=json.loads(path.read_text('utf-8'))
        self.assertFalse(any(name.endswith('.parquet') for name in manifest['files']))
        manifest['schema']='tori-backup-1';path.write_text(json.dumps(manifest),'utf-8')
        restored=Path(self.temp.name)/'old-restore';maintenance.restore(target,restored)
        with patch.dict(os.environ,{'TORI_DATA_DIR':str(restored)}):self.assertEqual(read_dataset(identity),before)


if __name__=='__main__':unittest.main()
