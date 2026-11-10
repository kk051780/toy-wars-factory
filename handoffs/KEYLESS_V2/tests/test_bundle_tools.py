import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile

TOOLS=pathlib.Path(__file__).resolve().parents[1]/'tools'

def load(stem):
    p=TOOLS/(stem+'.py')
    s=importlib.util.spec_from_file_location(stem,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m

b=load('build_migration_bundle')
v=load('verify_local_bundle')
h=load('keyless_handoff_v2')
m=load('seal_all_from_private_bundle')

class BundleTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.r=pathlib.Path(self.d.name)
        self.s=self.r/'sources';self.s.mkdir()
        self.name='TRAP_RAIDERS_v39_ChatLead.zip'
        with zipfile.ZipFile(self.s/self.name,'w') as z:
            z.writestr('a.txt',b'abc')
            z.writestr('BUILD_MANIFEST.json',json.dumps({'files':[{'path':'a.txt','sha256':h.sha(b'abc')}]},sort_keys=True))
        self.out=self.r/'PRIVATE.zip';self.catalog=self.r/'CATALOG.json'
    def build(self):return b.build(self.s,self.out,self.catalog)
    def test_verifies_private_bundle(self):
        self.assertEqual(self.build()['count'],1)
        self.assertEqual(v.check(self.out)['verified_manifest'],1)
    def test_refuses_overwrite(self):
        self.build()
        with self.assertRaises(FileExistsError):self.build()
    def test_detects_extra_hidden_item(self):
        self.build()
        with zipfile.ZipFile(self.out,'a') as z:z.writestr('bad.txt','secret')
        with self.assertRaises(ValueError):v.check(self.out)
    def test_detects_corruption(self):
        self.build()
        with zipfile.ZipFile(self.out,'a') as z:z.writestr('source_zips/ghost.zip',b'extra')
        with self.assertRaises(ValueError):v.check(self.out)
    def test_batch_seal_restore_without_manual_key(self):
        self.build()
        ident=self.r/'identity.json';pub=self.r/'public.json'
        h.enroll(ident,pub)
        manifest=m.run(self.out,pub,self.r/'sealed')
        self.assertEqual(len([x for x in manifest['items'] if x['status']=='SEALED_FOR_OWNER_RECIPIENT']),1)
        row=next(x for x in manifest['items'] if x['status']=='SEALED_FOR_OWNER_RECIPIENT')
        restored=self.r/'restored.zip'
        h.restore(self.r/'sealed'/row['sealed_filename'],ident,restored,
                  expected_zip_sha=row['plaintext_sha256'],expected_packet_id=row['packet_id'])
        self.assertEqual(restored.read_bytes(),(self.s/self.name).read_bytes())
    def test_no_manifest_is_marked_legacy(self):
        with zipfile.ZipFile(self.s/self.name,'w') as z:z.writestr('a.txt',b'abc')
        self.build()
        self.assertEqual(v.check(self.out)['legacy_missing_manifest'],1)
        ident=self.r/'identity.json';pub=self.r/'public.json';h.enroll(ident,pub)
        res=m.run(self.out,pub,self.r/'sealed')
        self.assertEqual(res['items'][0]['status'],'HOLD_LEGACY_NO_MANIFEST')

if __name__=='__main__':unittest.main()
