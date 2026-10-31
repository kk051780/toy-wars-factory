"""A14: fail-first synthetic checks for read-only GitHub artifact admission.
No real GitHub/Roblox execution is asserted from these local fixtures.
"""
import hashlib, io, json, sys, tempfile, unittest, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from github_artifact_admission import Expected, verify_metadata, verify_zip, AdmissionError, REPO, WORKFLOW, ARTIFACT, BINARY, RECEIPT, MAGIC
HEAD='a'*40
RUN=123456789
ART=987654321
BLOB=MAGIC+b'\0'*80

def good():
    run={'id':RUN,'head_sha':HEAD,'head_branch':'main','event':'workflow_dispatch','status':'completed','conclusion':'success','run_attempt':1,'repository':{'full_name':REPO},'path':WORKFLOW+'@refs/heads/main'}
    jobs={'total_count':1,'jobs':[{'id':4321,'name':'rojo-build-only','run_id':RUN,'run_attempt':1,'head_sha':HEAD,'status':'completed','conclusion':'success'}]}
    arts={'total_count':1,'artifacts':[{'id':ART,'name':ARTIFACT,'expired':False,'size_in_bytes':1234,'digest':'sha256:'+'f'*64,'workflow_run':{'id':RUN,'head_sha':HEAD,'head_branch':'main'}}]}
    return run,jobs,arts

def zip_blob(edit=None):
    receipt={'repository':REPO,'source_main_sha':HEAD,'rbxl_sha256':hashlib.sha256(BLOB).hexdigest(),'rbxl_bytes':len(BLOB),'build_only':True,'engine_verified':False}
    if edit:edit(receipt)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(BINARY,BLOB)
        z.writestr(RECEIPT,json.dumps(receipt))
    return stream.getvalue()

class ConnectedEvidenceContract(unittest.TestCase):
    def attempt(self,edit=None):
        r,j,a=good()
        if edit:edit(r,j,a)
        return verify_metadata(Expected(HEAD,RUN,ART),r,j,a)
    def test_synthetic_good_is_not_authenticated(self):
        out=self.attempt()
        self.assertFalse(out['provider_authenticated'])
        self.assertFalse(out['roblox_saved_authorized'])
    def test_reject_wrong_repository(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:r['repository'].update(full_name='other/repo'))
    def test_reject_forged_workflow(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:r.update(path='other.yml@main'))
    def test_reject_wrong_event(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:r.update(event='pull_request'))
    def test_reject_stale_source(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:r.update(head_sha='b'*40))
    def test_reject_failed_job(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:j['jobs'][0].update(conclusion='failure'))
    def test_reject_partial_jobs(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:j.update(total_count=2))
    def test_reject_wrong_job_attempt(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:j['jobs'][0].update(run_attempt=2))
    def test_reject_wrong_artifact_name(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:a['artifacts'][0].update(name='unreviewed'))
    def test_reject_missing_archive_digest(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:a['artifacts'][0].pop('digest'))
    def test_reject_expired_artifact(self):
        with self.assertRaises(AdmissionError):self.attempt(lambda r,j,a:a['artifacts'][0].update(expired=True))
    def test_reject_bool_run_id(self):
        with self.assertRaises(AdmissionError):verify_metadata(Expected(HEAD,True,ART),*good())

class ActualArchiveGate(unittest.TestCase):
    def verify(self,blob,override=None):
        md={'repository':REPO,'source_sha':HEAD,'archive_sha256':hashlib.sha256(blob).hexdigest(),'archive_bytes':len(blob),'build_run_id':RUN,'artifact_id':ART}
        if override:md.update(override)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'artifact.zip';path.write_bytes(blob)
            return verify_zip(path,md)
    def test_good_untrusted_archive(self):
        out=self.verify(zip_blob())
        self.assertFalse(out['rbxl_origin_authenticated'])
        self.assertFalse(out['roblox_saved_authorized'])
        self.assertEqual(out['rbxl_sha256'],hashlib.sha256(BLOB).hexdigest())
    def test_archive_sha_mismatch(self):
        with self.assertRaises(AdmissionError):self.verify(zip_blob(),{'archive_sha256':'0'*64})
    def test_wrong_binary_hash(self):
        with self.assertRaises(AdmissionError):self.verify(zip_blob(lambda r:r.update(rbxl_sha256='1'*64)))
    def test_wrong_main_sha(self):
        with self.assertRaises(AdmissionError):self.verify(zip_blob(lambda r:r.update(source_main_sha='f'*40)))
    def test_false_engine_claim(self):
        with self.assertRaises(AdmissionError):self.verify(zip_blob(lambda r:r.update(engine_verified=True)))
    def test_unrecognized_extra_member(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr(BINARY,BLOB)
            z.writestr(RECEIPT,json.dumps({'repository':REPO}))
            z.writestr('extra.lua','print(1)')
        with self.assertRaises(AdmissionError):self.verify(out.getvalue())
    def test_symlink_archive_rejected(self):
        blob=zip_blob()
        md={'repository':REPO,'source_sha':HEAD,'archive_sha256':hashlib.sha256(blob).hexdigest(),'archive_bytes':len(blob)}
        with tempfile.TemporaryDirectory() as d:
            real=Path(d)/'real.zip';real.write_bytes(blob)
            link=Path(d)/'artifact.zip';link.symlink_to(real)
            with self.assertRaises(AdmissionError):verify_zip(link,md)

if __name__=='__main__':unittest.main()
