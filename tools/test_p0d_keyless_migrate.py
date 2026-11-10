"""Isolated tests for owner-local P0-D keyless packet migration."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
import stat

modfile = Path(__file__).with_name('p0d_keyless_migrate.py')
spec = importlib.util.spec_from_file_location('p0d_keyless_migrate', modfile)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class KeylessLegacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.inbox = self.base / 'inbox'
        self.inbox.mkdir()
        self.out = self.base / 'out'
        self.out.mkdir()
        self.id = 'P0D-D07-SYNTH-TEST-01'
        self.original = self.inbox / (self.id + '.zip')
        self._make_source({'luau/mock.luau':b'return {value = 123}\n','tests/spec.py':b'assert 1+1==2\n'})
        self.good_sha = M.sha_file(self.original)
        self.reg = self._registry(self.good_sha)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_source(self, members, symlinks=()):
        with zipfile.ZipFile(self.original, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in members.items():
                z.writestr(name, data)
            for name in symlinks:
                i=zipfile.ZipInfo(name)
                i.create_system=3
                i.external_attr=(stat.S_IFLNK | 0o777) << 16
                z.writestr(i,'target')

    def _registry(self, digest):
        return [{'packet_id':self.id,'feature_id':'D07','original_zip_sha256':digest,'source_commit':'0'*40}]

    def _pack(self):
        return M.package_originals(self.reg,self.inbox,self.out/'bundle.zip',False)

    def test_01_good_source_integrity(self):
        items=M.read_original_zip(self.original,self.good_sha)
        self.assertEqual(len(items),2)
        self.assertIn('luau/mock.luau',dict(items))

    def test_02_source_sha_rejects_tamper(self):
        self.original.write_bytes(self.original.read_bytes()+b'bad')
        with self.assertRaisesRegex(M.MigrationError,'SHA_MISMATCH'):
            M.read_original_zip(self.original,self.good_sha)

    def test_03_no_source_does_not_make_bundle(self):
        self.original.unlink()
        with self.assertRaisesRegex(M.MigrationError,'NO_VERIFIED_ORIGINAL_ZIPS'):
            self._pack()

    def test_04_source_zip_slip_rejected(self):
        self._make_source({'../escape.txt':b'bad'})
        self.reg=self._registry(M.sha_file(self.original))
        with self.assertRaisesRegex(M.MigrationError,'TRAVERSAL'):
            M.read_original_zip(self.original,self.reg[0]['original_zip_sha256'])

    def test_05_source_symlink_rejected(self):
        self._make_source({'a.py':b'ok'}, symlinks=('link',))
        self.reg=self._registry(M.sha_file(self.original))
        with self.assertRaisesRegex(M.MigrationError,'SYMLINK'):
            M.read_original_zip(self.original,self.reg[0]['original_zip_sha256'])

    def test_06_case_collision_rejected(self):
        self._make_source({'Foo.py':b'a','foo.py':b'b'})
        self.reg=self._registry(M.sha_file(self.original))
        with self.assertRaisesRegex(M.MigrationError,'CASE_COLLIDING'):
            M.read_original_zip(self.original,self.reg[0]['original_zip_sha256'])

    def test_07_good_bundle_only_verified_original(self):
        result=self._pack()
        self.assertEqual(result['converted'],[self.id])
        self.assertEqual(result['pending'],[])
        self.assertTrue(result['sha256'])
        self.assertNotIn(b'keyfile', (self.out/'bundle.zip').read_bytes())

    def test_08_bundle_sha_rejects_tamper(self):
        result=self._pack()
        with self.assertRaisesRegex(M.MigrationError,'BUNDLE_SHA_MISMATCH'):
            M.verify_bundle(self.out/'bundle.zip','f'*64,self.reg)
        self.assertEqual(M.verify_bundle(self.out/'bundle.zip',result['sha256'],self.reg)['members'],2)

    def test_09_output_never_overwritten(self):
        self._pack()
        with self.assertRaisesRegex(M.MigrationError,'NO_OVERWRITE'):
            self._pack()

    def test_10_strict_all_rejects_missing(self):
        missing={'packet_id':'P0D-D14-UNAVAILABLE','feature_id':'D14','original_zip_sha256':'f'*64,'source_commit':'1'*40}
        with self.assertRaisesRegex(M.MigrationError,'STRICT_ALL_FAILED'):
            M.package_originals(self.reg+[missing],self.inbox,self.out/'bundle.zip',True)
        self.assertFalse((self.out/'bundle.zip').exists())

    def test_11_partial_ledger_truthful(self):
        missing={'packet_id':'P0D-D14-UNAVAILABLE','feature_id':'D14','original_zip_sha256':'f'*64,'source_commit':'1'*40}
        result=M.package_originals(self.reg+[missing],self.inbox,self.out/'bundle.zip',False)
        self.assertEqual(len(result['pending']),1)
        verdict=M.verify_bundle(self.out/'bundle.zip',result['sha256'],self.reg+[missing])
        self.assertTrue(verdict['partial'])
        self.assertEqual(verdict['pending_count'],1)

    def test_12_stage_safely_and_no_second_overwrite(self):
        result=self._pack()
        stage=self.base/'stage'
        r=M.stage_bundle(self.out/'bundle.zip',result['sha256'],self.reg,stage)
        self.assertEqual(r['status'],'KEYLESS_BUNDLE_VERIFIED')
        target=Path(r['stage'])
        self.assertEqual((target/'packets'/self.id/'luau'/'mock.luau').read_bytes(),b'return {value = 123}\n')
        with self.assertRaisesRegex(M.MigrationError,'STAGE_ALREADY_EXISTS'):
            M.stage_bundle(self.out/'bundle.zip',result['sha256'],self.reg,stage)

    def test_13_wrong_registry_source_hash_rejects_bundle(self):
        result=self._pack()
        with self.assertRaisesRegex(M.MigrationError,'SHA_NOT_IN_REGISTRY'):
            M.verify_bundle(self.out/'bundle.zip',result['sha256'],self._registry('f'*64))

    def test_14_duplicate_packet_registry_rejected(self):
        p=self.base/'registry.json'
        p.write_text(json.dumps({'schema':M.REGISTRY_SCHEMA,'game_id':'TRAP_RAIDERS','work_id':'p0d-siege-v19','packets':self.reg+self.reg}))
        with self.assertRaisesRegex(M.MigrationError,'DUPLICATE_OR_UNSAFE_PACKET'):
            M.read_registry(p)

    def test_15_received_bundle_member_sha_rejected(self):
        result=self._pack()
        orig=self.out/'bundle.zip'
        bad=self.out/'bad.zip'
        with zipfile.ZipFile(orig) as z:
            members={name:z.read(name) for name in z.namelist()}
        payload=json.loads(members[M.RECEIPT_NAME])
        payload['members'][0]['sha256']='0'*64
        members[M.RECEIPT_NAME]=M.json_bytes(payload)
        with zipfile.ZipFile(bad,'w') as z:
            for name,b in members.items():
                z.writestr(name,b)
        with self.assertRaisesRegex(M.MigrationError,'MEMBER_SHA_MISMATCH'):
            M.verify_bundle(bad,M.sha_file(bad),self.reg)

    def test_16_source_non_ascii_and_nested_paths_safe(self):
        self._make_source({'説明/見た目.md':'日本語'.encode(), 'Assets/x.luau':b'local x=1'})
        h=M.sha_file(self.original)
        actual=dict(M.read_original_zip(self.original,h))
        self.assertEqual(actual['説明/見た目.md'],'日本語'.encode())

    def test_17_misleading_dotdot_rejected(self):
        self._make_source({'a/../../x':b'bad'})
        with self.assertRaises(M.MigrationError):
            M.read_original_zip(self.original,M.sha_file(self.original))


if __name__=='__main__':
    unittest.main(verbosity=2)