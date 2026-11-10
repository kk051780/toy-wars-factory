from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tools'))
import p0d_d14_preflight as p

ROOT=Path(__file__).resolve().parents[1]

def make_fixture():
    m=json.loads((ROOT/'d14_packets.json').read_text())
    db={}
    for row in m['packets']:
        env=(json.dumps({'packet_id':row['packet_id'],'zip_sha256':row['restored_zip_sha256']},sort_keys=True)+'\n').encode()
        readme=(row['packet_id']+'\n'+row['restored_zip_sha256']+'\n').encode()
        row['encrypted_git_blob_sha1']=p.git_blob_sha(env)
        row['readme_git_blob_sha1']=p.git_blob_sha(readme)
        db[(row['commit'],row['encrypted_path'])]=env
        db[(row['commit'],row['readme_path'])]=readme
    def load(repo,sha,path):
        if repo!=p.EXPECTED_REPO: raise AssertionError('unexpected repo')
        return db[(sha,path)]
    return m,db,load

class PrefightTests(unittest.TestCase):
    def setUp(self): self.m,self.db,self.loader=make_fixture()
    def run_good(self):return p.preflight(self.m,self.loader)
    def bad(self,code):
        with self.assertRaisesRegex(p.PreflightError,code):p.preflight(self.m,self.loader)
    def test_01_valid_manifest_all_five_roles(self):
        self.assertEqual([x['role'] for x in p.validate_manifest(self.m)],list(p.ROLE_ORDER))
    def test_02_good_five_packet_preflight(self):
        results,data=self.run_good();self.assertEqual(len(results),5);self.assertEqual(len(data),5)
    def test_03_receipt_never_says_restored(self):
        receipts,_=self.run_good();self.assertTrue(all(x['status']=='CIPHERTEXT_READBACK_PASS_NO_RESTORE' for x in receipts))
    def test_04_strict_no_duplicate_json(self):
        with self.assertRaisesRegex(p.PreflightError,'DUPLICATE_KEY'):p.strict_json(b'{"x":1,"x":2}')
    def test_05_strict_no_nan(self):
        with self.assertRaisesRegex(p.PreflightError,'NONFINITE'):p.strict_json(b'{"x":NaN}')
    def test_06_wrong_game(self):self.m['game_id']='FAKE';self.bad('WRONG_MANIFEST_ID')
    def test_07_wrong_work(self):self.m['work_id']='no';self.bad('WRONG_MANIFEST_ID')
    def test_08_wrong_repository(self):self.m['repository']='evil/repo';self.bad('WRONG_MANIFEST_ID')
    def test_09_wrong_schema(self):self.m['schema']='other';self.bad('WRONG_MANIFEST_ID')
    def test_10_missing_required_core(self):self.m['packets'].pop(0);self.bad('WRONG_PACKET_ORDER')
    def test_11_extra_packet(self):self.m['packets'].append(copy.deepcopy(self.m['packets'][-1]));self.bad('WRONG_PACKET_ORDER')
    def test_12_reordered_roles(self):self.m['packets'][0],self.m['packets'][1]=self.m['packets'][1],self.m['packets'][0];self.bad('WRONG_PACKET_ORDER')
    def test_13_changed_core_roles(self):self.m['core_cart'][1]='RAFT';self.bad('BAD_ROLE_ORDER')
    def test_14_superseded_cart_3d_commit_rejected(self):self.m['packets'][1]['commit']='cae5691b622045af57674d922a08a96764354412';self.bad('SUPERSEDED_OR_UNPINNED')
    def test_15_superseded_old_seats_commit_rejected(self):self.m['packets'][0]['commit']='250658457392e016c668de8d3c368499f39714bc';self.bad('SUPERSEDED_OR_UNPINNED')
    def test_16_deleting_superseded_entry_rejected(self):self.m['superseded_commits'].pop();self.bad('BAD_SUPERSEDED_SET')
    def test_17_duplicate_packet_id_rejected(self):self.m['packets'][1]['packet_id']=self.m['packets'][0]['packet_id'];self.bad('BAD_PACKET_ID')
    def test_18_path_traversal_encrypted_rejected(self):self.m['packets'][0]['encrypted_path']='handoffs/../secrets';self.bad('BAD_ENVELOPE_PATH')
    def test_19_absolute_readme_path_rejected(self):self.m['packets'][0]['readme_path']='/etc/passwd';self.bad('BAD_README_PATH')
    def test_20_wrong_hash_format(self):self.m['packets'][0]['encrypted_git_blob_sha1']='a'*39;self.bad('BAD_EXPECTED_HASH')
    def test_21_unknown_packet_field_rejected(self):self.m['packets'][0]['key']='secret';self.bad('BAD_PACKET_SHAPE')
    def test_22_envelope_byte_flip_rejected(self):
        row=self.m['packets'][0];self.db[(row['commit'],row['encrypted_path'])]=b'X'+self.db[(row['commit'],row['encrypted_path'])][1:]
        self.bad('ENCRYPTED_GIT_BLOB_MISMATCH')
    def test_23_readme_byte_flip_rejected(self):
        row=self.m['packets'][0];self.db[(row['commit'],row['readme_path'])]=b'X'+self.db[(row['commit'],row['readme_path'])][1:]
        self.bad('README_GIT_BLOB_MISMATCH')
    def test_24_envelope_packet_wrong_even_with_forged_blob(self):
        row=self.m['packets'][1];enc=json.dumps({'packet_id':'wrong','zip_sha256':row['restored_zip_sha256']}).encode()
        row['encrypted_git_blob_sha1']=p.git_blob_sha(enc);self.db[(row['commit'],row['encrypted_path'])]=enc
        self.bad('ENVELOPE_IDENTITY_MISMATCH')
    def test_25_envelope_zip_wrong_even_with_forged_blob(self):
        row=self.m['packets'][1];enc=json.dumps({'packet_id':row['packet_id'],'zip_sha256':'f'*64}).encode()
        row['encrypted_git_blob_sha1']=p.git_blob_sha(enc);self.db[(row['commit'],row['encrypted_path'])]=enc
        self.bad('ENVELOPE_IDENTITY_MISMATCH')
    def test_26_readme_missing_identity_even_with_forged_blob(self):
        row=self.m['packets'][0];b=row['restored_zip_sha256'].encode();row['readme_git_blob_sha1']=p.git_blob_sha(b)
        self.db[(row['commit'],row['readme_path'])]=b;self.bad('README_PACKET_ID_MISMATCH')
    def test_27_readme_missing_zip_even_with_forged_blob(self):
        row=self.m['packets'][0];b=row['packet_id'].encode();row['readme_git_blob_sha1']=p.git_blob_sha(b)
        self.db[(row['commit'],row['readme_path'])]=b;self.bad('README_ZIP_SHA_MISMATCH')
    def test_28_failing_loader_prevents_stage(self):
        with tempfile.TemporaryDirectory() as d:
            def fail(repo,sha,path):raise IOError('no network')
            with self.assertRaises(IOError): p.preflight(self.m,fail)
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_29_staging_preverified_five_pairs(self):
        _,data=self.run_good()
        with tempfile.TemporaryDirectory() as d:
            count=p.stage_verified(Path(d),data)
            self.assertEqual(count,10)
            self.assertEqual(len(list(Path(d).iterdir())),10)
            self.assertTrue((Path(d)/'SEATS_encrypted.json').exists())
    def test_30_refuses_nonempty_staging(self):
        _,data=self.run_good()
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'keep').write_text('HOLD')
            with self.assertRaisesRegex(p.PreflightError,'NOT_EMPTY'):p.stage_verified(Path(d),data)
            self.assertEqual((Path(d)/'keep').read_text(),'HOLD')
    def test_31_refuses_symlink_directory(self):
        _,data=self.run_good()
        with tempfile.TemporaryDirectory() as d:
            parent=Path(d);(parent/'real').mkdir();(parent/'alias').symlink_to('real',target_is_directory=True)
            with self.assertRaisesRegex(p.PreflightError,'SYMLINK'):p.stage_verified(parent/'alias',data)
    def test_32_refuses_invalid_fetch_host(self):
        with self.assertRaisesRegex(p.PreflightError,'UNSAFE_FETCH_ARGUMENT'):p.fetch_raw('evil/repo','a'*40,'handoffs/x.json')
    def test_33_refuses_invalid_fetch_commit(self):
        with self.assertRaisesRegex(p.PreflightError,'UNSAFE_FETCH_ARGUMENT'):p.fetch_raw(p.EXPECTED_REPO,'main','handoffs/x.json')
    def test_34_refuses_invalid_fetch_path(self):
        with self.assertRaisesRegex(p.PreflightError,'UNSAFE_FETCH_ARGUMENT'):p.fetch_raw(p.EXPECTED_REPO,'a'*40,'../SECRET')
    def test_35_unstage_rollback_does_not_delete_foreign_files(self):
        _,data=self.run_good()
        with tempfile.TemporaryDirectory() as d:
            original=os.open
            calls=[0]
            def fail_third(path,*args,**kw):
                calls[0]+=1
                if calls[0]==3:raise OSError('disk full')
                return original(path,*args,**kw)
            with patch.object(p.os,'open',side_effect=fail_third):
                with self.assertRaises(OSError):p.stage_verified(Path(d),data)
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_36_reject_wrong_extra_top_field_readme_content_not_source(self):
        row=self.m['packets'][0]
        b=b'not content';row['readme_git_blob_sha1']=p.git_blob_sha(b)
        self.db[(row['commit'],row['readme_path'])]=b
        self.bad('README_PACKET_ID_MISMATCH')
    def test_37_no_network_in_mocked_full_preflight(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('network used')):
            receipts,_=self.run_good();self.assertEqual(len(receipts),5)
    def test_38_staging_does_not_touch_private_keys(self):
        _,data=self.run_good()
        with tempfile.TemporaryDirectory() as d:
            p.stage_verified(Path(d),data)
            self.assertTrue(all('KEY' not in f.name.upper() for f in Path(d).iterdir()))
    def test_39_expected_manifest_real_has_five_pinned(self):
        rows=p.validate_manifest(json.loads((ROOT/'d14_packets.json').read_text()))
        self.assertEqual(len(rows),5)
        self.assertEqual(rows[1]['packet_id'],'P0D-D14-CART-RAIL-MOTION-20261110-02B')
    def test_40_cli_block_if_bad_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'m.json';file.write_text('{}')
            self.assertEqual(p.main(['--manifest',str(file)]),2)
    def test_41_fetch_invalid_redirect(self):
        class Reply:
            def __enter__(self):return self
            def __exit__(self,*_):return False
            def geturl(self):return 'https://evil.example/'
            def read(self,*_):return b'{}'
        with patch.object(p,'urlopen',return_value=Reply()):
            with self.assertRaisesRegex(p.PreflightError,'UNEXPECTED_REDIRECT'):p.fetch_raw(p.EXPECTED_REPO,'a'*40,'handoffs/x.json')

if __name__=='__main__':unittest.main()
