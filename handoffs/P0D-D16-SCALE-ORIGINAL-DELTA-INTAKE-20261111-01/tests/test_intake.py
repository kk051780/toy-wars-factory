import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE=Path(__file__).resolve().parents[1]/'tools'/'verify_original_scale_delta.py'
spec=importlib.util.spec_from_file_location('intake',MODULE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def run(*argv):
    return subprocess.check_output(list(argv),stderr=subprocess.DEVNULL)

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name)/'repo'
        self.repo.mkdir()
        run('git','init','-q',str(self.repo))
        run('git','-C',str(self.repo),'config','user.email','test@example.invalid')
        run('git','-C',str(self.repo),'config','user.name','Test')
        self.root='handoffs/'+m.PACKET
        self.pkg=self.repo/self.root
        (self.pkg/'src').mkdir(parents=True)
        (self.pkg/'src'/'ScaleFxCore.luau').write_text('function M.new(matchId) end\nfunction M.begin(s, matchId, eventId, kind, actorId, roster, now) end\n',encoding='utf8')
        self.data=(self.pkg/'src'/'ScaleFxCore.luau').read_bytes()
        self.file={'path':'src/ScaleFxCore.luau','size':len(self.data),'sha256':m.digest(self.data)}
        self.build_manifest()
        self.commit()
    def build_manifest(self, **kwargs):
        doc=dict(m.EXPECTED)
        doc['files']=[self.file]
        doc.update(kwargs)
        self.mbytes=(json.dumps(doc,sort_keys=True)+'\n').encode()
        (self.pkg/'BUILD_MANIFEST.json').write_bytes(self.mbytes)
        self.mhash=m.digest(self.mbytes)
    def commit(self):
        run('git','-C',str(self.repo),'add','-A')
        run('git','-C',str(self.repo),'commit','-qm','fixture')
        self.sha=run('git','-C',str(self.repo),'rev-parse','HEAD').decode().strip()
    def verify(self):
        old=m.ORIGINAL_LUAU_SHA256
        try:
            m.ORIGINAL_LUAU_SHA256=self.file['sha256']
            return m.verify(self.repo,commit=self.sha,root=self.root,manifest_hash=self.mhash)
        finally:
            m.ORIGINAL_LUAU_SHA256=old
    def test_positive_manifest_and_source(self):
        self.assertEqual(set(self.verify()),{'BUILD_MANIFEST.json','src/ScaleFxCore.luau'})
    def test_stage_external_receipt(self):
        old=m.ORIGINAL_LUAU_SHA256
        m.ORIGINAL_LUAU_SHA256=self.file['sha256']
        try:
            dest=Path(self.tmp.name)/'out'
            rc=m.stage(self.repo,dest,commit=self.sha,root=self.root,manifest_hash=self.mhash)
            self.assertEqual(rc['file_count'],2)
            self.assertEqual((dest/'src'/'ScaleFxCore.luau').read_bytes(),self.data)
            self.assertEqual(rc['status'],'SOURCE_BYTE_VERIFIED__NO_STUDIO_CLAIM')
            with self.assertRaises(m.IntakeError):
                m.stage(self.repo,dest,commit=self.sha,root=self.root,manifest_hash=self.mhash)
        finally:
            m.ORIGINAL_LUAU_SHA256=old
    def test_wrong_manifest_hash(self):
        with self.assertRaisesRegex(m.IntakeError,'manifest hash'):
            m.verify(self.repo,commit=self.sha,root=self.root,manifest_hash='0'*64)
    def test_wrong_sha_ref(self):
        with self.assertRaisesRegex(m.IntakeError,'40-character'):
            m.verify(self.repo,commit='main',root=self.root,manifest_hash=self.mhash)
    def test_traversal_paths(self):
        for s in ['../test','/tmp/evil','hidden/../bad','C:/bad','folder\\bad','.secret']:
            with self.subTest(s=s),self.assertRaises(m.IntakeError):m.safe_path(s)
    def test_manifest_wrong_identity(self):
        self.build_manifest(game_id='OTHER')
        self.commit()
        with self.assertRaisesRegex(m.IntakeError,'wrong game'):
            self.verify()
    def test_manifest_duplicate(self):
        self.build_manifest(files=[self.file,self.file])
        self.commit()
        with self.assertRaisesRegex(m.IntakeError,'duplicate'):
            self.verify()
    def test_digest_tamper(self):
        self.file['sha256']='0'*64
        self.build_manifest()
        self.commit()
        with self.assertRaisesRegex(m.IntakeError,'byte/SHA mismatch'):
            self.verify()
    def test_wrong_original_core(self):
        with self.assertRaisesRegex(m.IntakeError,'wrong/incompatible'):
            m.verify(self.repo,commit=self.sha,root=self.root,manifest_hash=self.mhash)
    def test_existing_target_rejected(self):
        dest=self.repo/'somewhere'
        with self.assertRaisesRegex(m.IntakeError,'outside'):
            m.stage(self.repo,dest,commit=self.sha,root=self.root,manifest_hash=self.mhash)
    def test_symlink_rejected(self):
        (self.pkg/'src'/'ScaleFxCore.luau').unlink()
        (self.pkg/'src'/'ScaleFxCore.luau').symlink_to('target.txt')
        self.commit()
        with self.assertRaisesRegex(m.IntakeError,'non-regular'):
            self.verify()
    def test_contract_guard(self):
        self.assertIn('function M.begin(s, matchId, eventId, kind, actorId, roster, now)',self.data.decode())
    def test_commit_is_actual_commit(self):
        self.assertEqual(m.git(self.repo,'cat-file','-t',self.sha).strip(),b'commit')

if __name__=='__main__':unittest.main()
