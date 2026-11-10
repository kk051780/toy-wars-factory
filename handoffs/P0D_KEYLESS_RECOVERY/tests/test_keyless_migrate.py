import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import keyless_migrate as km

ROOT=Path(__file__).resolve().parents[1]

class TestMigrate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'bundle'
        self.root.mkdir()
        (self.root/'source_packages'/'TEST-PACKET').mkdir(parents=True)
        data=b'print("hello")\n'
        (self.root/'source_packages'/'TEST-PACKET'/'main.luau').write_bytes(data)
        self.doc={'format':'P0D_KEYLESS_BATCH_V1','target_private_repo':km.EXPECTED_REPO,'packets':[{'packet_id':'TEST-PACKET','files':[{'path':'main.luau','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}]}
        self.write()
    def write(self):
        (self.root/'migration_manifest.json').write_text(json.dumps(self.doc)+'\n')
    def test_good(self):self.assertEqual(len(km.load_manifest(self.root)['packets']),1)
    def test_real_four_pack(self):
        if not (ROOT/'source_packages').exists(): self.skipTest('source material is private, unavailable in PUBLIC repo')
        real=km.load_manifest(ROOT)
        self.assertEqual(len(real['packets']),4)
        self.assertEqual(sum(len(p['files']) for p in real['packets']),35)
    def test_source_tamper(self):
        (self.root/'source_packages'/'TEST-PACKET'/'main.luau').write_bytes(b'bye')
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_source_extra(self):
        (self.root/'source_packages'/'TEST-PACKET'/'extra.luau').write_text('x')
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_extra_packet(self):
        (self.root/'source_packages'/'UNEXPECTED').mkdir()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_duplicate_packet(self):
        self.doc['packets'].append(self.doc['packets'][0]);self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_duplicate_file(self):
        self.doc['packets'][0]['files'].append(self.doc['packets'][0]['files'][0]);self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_wrong_target(self):
        self.doc['target_private_repo']='kk051780/toy-wars-factory';self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_path_traversal(self):
        self.doc['packets'][0]['files'][0]['path']='../main.luau';self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_backslash(self):
        self.doc['packets'][0]['files'][0]['path']='a\\b.luau';self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_hidden_git(self):
        self.doc['packets'][0]['files'][0]['path']='.git/config.py';self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_bad_suffix(self):
        self.doc['packets'][0]['files'][0]['path']='secret.exe';self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_unexpected_sha(self):
        self.doc['packets'][0]['files'][0]['sha256']='0'*64;self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_invalid_sha_shape(self):
        self.doc['packets'][0]['files'][0]['sha256']='g'*64;self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_bool_size_rejected(self):
        self.doc['packets'][0]['files'][0]['bytes']=True;self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_oversized_file(self):
        self.doc['packets'][0]['files'][0]['bytes']=km.MAX_FILE+1;self.write()
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_duplicate_json_key(self):
        (self.root/'migration_manifest.json').write_text('{"format":"x","format":"y"}')
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_manifest_symlink(self):
        m=self.root/'migration_manifest.json';orig=self.root/'original.json';m.rename(orig);m.symlink_to(orig)
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_source_symlink(self):
        d=self.root/'source_packages'/'TEST-PACKET';f=d/'main.luau';original=d/'real.luau';f.rename(original);f.symlink_to(original)
        with self.assertRaises(km.PolicyError):km.load_manifest(self.root)
    def test_public_repo_rejected(self):
        with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name), 'kk051780/toy-wars-factory')
    def test_missing_checkout_rejected(self):
        with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name)/'missing',km.EXPECTED_REPO)
    def test_private_visibility_required(self):
        with mock.patch.object(km,'shell',return_value='{"nameWithOwner":"kk051780/trap-raiders-private-source","visibility":"PUBLIC"}'):
            with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name),km.EXPECTED_REPO)
    def test_wrong_owner_rejected(self):
        with mock.patch.object(km,'shell',return_value='{"nameWithOwner":"attacker/replica","visibility":"PRIVATE"}'):
            with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name),km.EXPECTED_REPO)
    def test_wrong_remote_rejected(self):
        calls=iter(['{"nameWithOwner":"kk051780/trap-raiders-private-source","visibility":"PRIVATE"}',str(Path(self.tmp.name).resolve()),'https://github.com/kk051780/toy-wars-factory.git'])
        with mock.patch.object(km,'shell',side_effect=lambda x:next(calls)):
            with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name),km.EXPECTED_REPO)
    def test_main_branch_rejected(self):
        calls=iter(['{"nameWithOwner":"kk051780/trap-raiders-private-source","visibility":"PRIVATE"}',str(Path(self.tmp.name).resolve()),'git@github.com:kk051780/trap-raiders-private-source.git','main'])
        with mock.patch.object(km,'shell',side_effect=lambda x:next(calls)):
            with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name),km.EXPECTED_REPO)
    def test_dirty_branch_rejected(self):
        calls=iter(['{"nameWithOwner":"kk051780/trap-raiders-private-source","visibility":"PRIVATE"}',str(Path(self.tmp.name).resolve()),'git@github.com:kk051780/trap-raiders-private-source.git','handoff/test',' M file.luau'])
        with mock.patch.object(km,'shell',side_effect=lambda x:next(calls)):
            with self.assertRaises(km.PolicyError):km.require_private_repo(Path(self.tmp.name),km.EXPECTED_REPO)
    def test_gh_not_available_fails_closed(self):
        with mock.patch.object(km.subprocess,'run',side_effect=FileNotFoundError()):
            with self.assertRaises(km.PolicyError):km.shell(['gh','repo','view','foo'])
    def test_stage_nominal_no_push(self):
        repo=Path(self.tmp.name)/'repo';repo.mkdir()
        with mock.patch.object(km,'require_private_repo') as permit:
            n=km.stage(self.root,repo,km.EXPECTED_REPO)
        self.assertEqual(n,1)
        self.assertEqual((repo/'handoffs/keyless-v1/TEST-PACKET/main.luau').read_text(),'print("hello")\n')
        self.assertTrue((repo/'handoffs/keyless-v1/KEYLESS_MIGRATION_MANIFEST.json').is_file())
    def test_no_overwrite(self):
        repo=Path(self.tmp.name)/'repo';(repo/'handoffs/keyless-v1/TEST-PACKET').mkdir(parents=True)
        (repo/'handoffs/keyless-v1/TEST-PACKET/main.luau').write_text('old')
        with mock.patch.object(km,'require_private_repo'):
            with self.assertRaises(km.PolicyError):km.stage(self.root,repo,km.EXPECTED_REPO)
        self.assertEqual((repo/'handoffs/keyless-v1/TEST-PACKET/main.luau').read_text(),'old')
    def test_symlink_parent_block(self):
        repo=Path(self.tmp.name)/'repo';repo.mkdir();outside=Path(self.tmp.name)/'outside';outside.mkdir();(repo/'handoffs').symlink_to(outside,target_is_directory=True)
        with mock.patch.object(km,'require_private_repo'):
            with self.assertRaises(km.PolicyError):km.stage(self.root,repo,km.EXPECTED_REPO)
        self.assertFalse((outside/'keyless-v1').exists())
    def test_no_network_when_verify_only(self):
        with mock.patch.object(km,'shell',side_effect=AssertionError('network invocation')):
            self.assertEqual(km.load_manifest(self.root)['format'],'P0D_KEYLESS_BATCH_V1')

if __name__=='__main__':unittest.main()
