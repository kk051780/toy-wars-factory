#!/usr/bin/env python3
"""Public-safe, synthetic-only regression suite. No game data, keys or IP in fixtures."""
from __future__ import annotations
import hashlib
import io
import json
import pathlib
import tempfile
import unittest
import zipfile
import warnings
from p0d_d18_receive_no_key import IntakeError,validate_archive,stage_validated,resolve_archive,FILENAME

def h(x):return hashlib.sha256(x).hexdigest()

def bundle_bytes(*,bad_path=False, bad_digest=False, duplicate=False):
    entries=[]
    for i in range(648):
        is_curated=i<66
        item={'id':f'SYNTH-{i:04d}','is_hero':i<60}
        if is_curated:item['editorial']={'synthetic':True}
        entries.append(item)
    content={
        'catalog_flat_648_v7.json':json.dumps({'metadata':{'individual_editorial':66},'entries':entries}).encode(),
        'wave5_12_hero_editorial_v7.json':json.dumps({'items':[{'id':f'SYNTH-{i:04d}'} for i in range(12)]}).encode(),
        'summary.json':b'{}',
    }
    manifest={'schema_version':'P0D_D18_V7_KEYLESS_SELF_CONTAINED','game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19','revision':'WAVE5_NO_KEY_HANDOFF_V7','files':[]}
    for name,b in content.items():manifest['files'].append({'path':name,'bytes':len(b),'sha256':h(b)})
    if bad_digest:manifest['files'][0]['sha256']='0'*64
    content['BUILD_MANIFEST.json']=json.dumps(manifest).encode()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name,b in content.items():
            z.writestr('../wrong.json' if bad_path and name=='summary.json' else name,b)
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                z.writestr('summary.json',b'{}')
    return buf.getvalue()

class ReceiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=pathlib.Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def save(self,data):
        p=self.root/FILENAME;p.write_bytes(data);return p
    def test_good_bundle(self):
        b=bundle_bytes();m,items,manifest=validate_archive(self.save(b),h(b))
        self.assertEqual(len(items),3)
        self.assertEqual(m['schema_version'],'P0D_D18_V7_KEYLESS_SELF_CONTAINED')
    def test_refuses_wrong_outer_sha(self):
        b=bundle_bytes()
        with self.assertRaisesRegex(IntakeError,'OUTER_SHA_MISMATCH'):validate_archive(self.save(b),'f'*64)
    def test_refuses_bad_inner_digest(self):
        b=bundle_bytes(bad_digest=True)
        with self.assertRaisesRegex(IntakeError,'MANIFEST_MEMBER_HASH_MISMATCH'):validate_archive(self.save(b),h(b))
    def test_refuses_traversal(self):
        b=bundle_bytes(bad_path=True)
        with self.assertRaisesRegex(IntakeError,'UNSAFE_MEMBER_PATH'):validate_archive(self.save(b),h(b))
    def test_refuses_duplicate(self):
        b=bundle_bytes(duplicate=True)
        with self.assertRaisesRegex(IntakeError,'DUPLICATE_MEMBER_NAME'):validate_archive(self.save(b),h(b))
    def test_refuses_invalid_sha_syntax(self):
        b=bundle_bytes()
        with self.assertRaisesRegex(IntakeError,'EXPECTED_SHA_INVALID'):validate_archive(self.save(b),'BAD')
    def test_refuses_missing_archive(self):
        with self.assertRaisesRegex(IntakeError,'ARCHIVE_NOT_FOUND'):resolve_archive(None,self.root)
    def test_single_known_candidate_downloads(self):
        p=self.root/'Downloads'/FILENAME;p.parent.mkdir(parents=True);p.write_bytes(b'abc')
        self.assertEqual(resolve_archive(None,self.root),p)
    def test_refuses_ambiguous_two_known_paths(self):
        p=self.root/'Downloads'/FILENAME;p.parent.mkdir(parents=True);p.write_bytes(b'x')
        p2=self.root/'TRAP_RAIDERS'/'handoff'/'inbox'/FILENAME;p2.parent.mkdir(parents=True);p2.write_bytes(b'x')
        with self.assertRaisesRegex(IntakeError,'AMBIGUOUS_ARCHIVES'):resolve_archive(None,self.root)
    def test_stages_isolated(self):
        b=bundle_bytes();m,items,manifest=validate_archive(self.save(b),h(b))
        stage=stage_validated(items,manifest,h(b),self.root)
        self.assertTrue((stage/'RECEIVE_STATUS.txt').is_file())
        self.assertFalse((self.root/'game').exists())
    def test_refuses_existing_stage(self):
        b=bundle_bytes();m,items,manifest=validate_archive(self.save(b),h(b))
        stage_validated(items,manifest,h(b),self.root)
        with self.assertRaisesRegex(IntakeError,'STAGE_ALREADY_EXISTS'):stage_validated(items,manifest,h(b),self.root)

if __name__=='__main__':unittest.main()