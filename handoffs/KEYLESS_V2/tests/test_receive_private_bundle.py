import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

TOOLS=Path(__file__).resolve().parents[1]/'tools'
def load(name):
    spec=importlib.util.spec_from_file_location(name,TOOLS/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
import sys
sys.path.insert(0,str(TOOLS))
h=load('keyless_handoff_v2');b=load('build_migration_bundle');r=load('receive_private_bundle')

class ReceiveTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.d=Path(self.t.name);self.s=self.d/'source';self.s.mkdir()
        self.n='TRAP_RAIDERS_v39_ChatLead.zip'
        with zipfile.ZipFile(self.s/self.n,'w') as z:
            z.writestr('hi.txt',b'hi')
            z.writestr('BUILD_MANIFEST.json',json.dumps({'files':[{'path':'hi.txt','sha256':h.sha(b'hi')}]}))
        self.bundle=self.d/'bundle.zip';self.catalog=self.d/'catalog.json'
        b.build(self.s,self.bundle,self.catalog)
    def test_receive_verifies_and_stages(self):
        out=self.d/'out';a=r.receive(self.bundle,out)
        self.assertEqual(a['source_zips'],1)
        self.assertEqual((out/self.n).read_bytes(),(self.s/self.n).read_bytes())
    def test_no_overwrite_existing_stage(self):
        out=self.d/'out';r.receive(self.bundle,out)
        with self.assertRaises(FileExistsError):r.receive(self.bundle,out)
    def test_corrupt_private_bundle_rejects(self):
        with zipfile.ZipFile(self.bundle,'a') as z:z.writestr('arbitrary','x')
        out=self.d/'out'
        with self.assertRaises(ValueError):r.receive(self.bundle,out)
        self.assertFalse(out.exists())
    def test_only_staging_not_studio(self):
        out=self.d/'out';r.receive(self.bundle,out)
        self.assertEqual(set(p.name for p in out.iterdir()),{self.n,'MIGRATION_CATALOG.json'})

if __name__=='__main__':unittest.main()
