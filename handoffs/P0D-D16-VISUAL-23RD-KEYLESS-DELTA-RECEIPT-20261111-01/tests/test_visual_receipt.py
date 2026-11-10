import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'tools'/'verify_visual_original.py'
spec=importlib.util.spec_from_file_location('receipt',SCRIPT)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def run(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()

class VisualReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.repo=self.base/'git';self.repo.mkdir()
        run(self.repo,'init','-q');run(self.repo,'config','user.name','Synthetic Test');run(self.repo,'config','user.email','test@example.invalid')
        self.file='src/ScaleFxClientPolicy.luau';self.code=b'function P.accept(state, packet, expectedMatchId, now)\nfunction P.tick(state, expectedMatchId, now)\n'
        self.commit=self.make_commit()
        self.expect={self.file:m.sha(self.code)}
        self.api={self.file:['function P.accept(state, packet, expectedMatchId, now)']}
    def make_commit(self,*,path=None,code=None,declared_path=None,packet=None,entry_override=None):
        src=path or self.file;payload=code or self.code
        pack=self.repo/m.ROOT; dest=pack/src;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload)
        e={'path':declared_path or src,'sha256':m.sha(payload),'size':len(payload)}
        if entry_override:e.update(entry_override)
        manifest={**m.META,'files':[e]}
        if packet is not None:manifest['packet_id']=packet
        (pack/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True)+'\n')
        run(self.repo,'add','.');run(self.repo,'commit','-q','-m','synthetic test')
        return run(self.repo,'rev-parse','HEAD')
    def msha(self):return m.sha((self.repo/m.ROOT/'BUILD_MANIFEST.json').read_bytes())
    def check(self,**kwargs):
        return m.verify(self.repo,commit=kwargs.get('commit',self.commit),manifest_sha=kwargs.get('manifest_sha',self.msha()),code_hashes=kwargs.get('code_hashes',self.expect),required_api=kwargs.get('required_api',self.api))
    def test_valid_fixture(self):self.assertEqual(self.check()[self.file],self.code)
    def test_receipt_stage(self):
        target=self.base/'fresh'
        x=m.stage(self.repo,target,commit=self.commit,manifest_sha=self.msha(),code_hashes=self.expect,required_api=self.api)
        self.assertEqual(x['file_count'],2)
        self.assertEqual((target/self.file).read_bytes(),self.code)
        self.assertEqual(json.loads((target/'SOURCE_RECEIPT.json').read_text())['status'],'PINNED_ORIGINAL_SOURCE_RECEIVED__NOT_STUDIO_TESTED')
    def test_existing_stage_rejected(self):
        x=self.base/'existing';x.mkdir()
        with self.assertRaises(m.ReceiptError):m.stage(self.repo,x,commit=self.commit,manifest_sha=self.msha(),code_hashes=self.expect,required_api=self.api)
    def test_inside_repo_rejected(self):
        with self.assertRaises(m.ReceiptError):m.stage(self.repo,self.repo/'out',commit=self.commit,manifest_sha=self.msha(),code_hashes=self.expect,required_api=self.api)
    def test_wrong_manifest_sha_rejected(self):
        with self.assertRaises(m.ReceiptError):self.check(manifest_sha='0'*64)
    def test_wrong_commit_rejected(self):
        with self.assertRaises(m.ReceiptError):self.check(commit='0'*40)
    def test_short_ref_rejected(self):
        with self.assertRaises(m.ReceiptError):self.check(commit=self.commit[:10])
    def test_wrong_code_sha_rejected(self):
        with self.assertRaises(m.ReceiptError):self.check(code_hashes={self.file:'0'*64})
    def test_wrong_code_api_rejected(self):
        with self.assertRaises(m.ReceiptError):self.check(required_api={self.file:['function FakeRemote()']})
    def test_path_traversal_rejected(self):
        with self.assertRaises(m.ReceiptError):m.safe_path('../fake')
    def test_absolute_path_rejected(self):
        with self.assertRaises(m.ReceiptError):m.safe_path('/tmp/file')
    def test_hidden_rejected(self):
        with self.assertRaises(m.ReceiptError):m.safe_path('.env')
    def test_windows_path_rejected(self):
        with self.assertRaises(m.ReceiptError):m.safe_path('foo\\secret')
    def test_colon_rejected(self):
        with self.assertRaises(m.ReceiptError):m.safe_path('c:secret')
    def test_utf8_path_accept(self):self.assertEqual(str(m.safe_path('src/x.luau')),'src/x.luau')
    def test_manifest_wrong_packet(self):
        commit=self.make_commit(packet='OTHER-PACKET');
        with self.assertRaises(m.ReceiptError):self.check(commit=commit)
    def test_manifest_duplicate_entries(self):
        mf=self.repo/m.ROOT/'BUILD_MANIFEST.json';j=json.loads(mf.read_text());j['files'].append(j['files'][0]);mf.write_text(json.dumps(j));run(self.repo,'add','.');run(self.repo,'commit','-q','-m','dup');
        with self.assertRaises(m.ReceiptError):self.check(commit=run(self.repo,'rev-parse','HEAD'))
    def test_nonregular_symlink_rejected(self):
        import os
        target=self.repo/m.ROOT/self.file;target.unlink();target.symlink_to(self.repo/m.ROOT/'BUILD_MANIFEST.json')
        run(self.repo,'add','.');run(self.repo,'commit','-q','-m','symlink')
        with self.assertRaises(m.ReceiptError):self.check(commit=run(self.repo,'rev-parse','HEAD'))
    def test_mutated_source_rejected(self):
        target=self.repo/m.ROOT/self.file;target.write_text('changed');run(self.repo,'add','.');run(self.repo,'commit','-q','-m','tamper')
        with self.assertRaises(m.ReceiptError):self.check(commit=run(self.repo,'rev-parse','HEAD'))

if __name__=='__main__':unittest.main()
