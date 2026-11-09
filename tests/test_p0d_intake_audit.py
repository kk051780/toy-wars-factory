import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import p0d_intake_audit as m


def load():
    return json.loads((ROOT/'docs'/'P0D_INTAKE_REGISTRY.json').read_text('utf-8'))


def build_fixture(p):
    # Fake envelope with valid ciphertext *shape* but no real encryption/key.
    # The public intake auditor never authenticates/decrypts a ZIP; PC must do so.
    msg=b'example-ciphertext-and-tag-not-actual-aes'
    aad=f'TRAP_RAIDERS|p0d-siege-v19|{p["packet_id"]}|zip_sha256={p["zip_sha256"]}'.encode()
    envelope={'format':'P0D_AES256_GCM_HANDOFF_V1','game_id':'TRAP_RAIDERS',
              'work_id':'p0d-siege-v19','packet_id':p['packet_id'],
              'zip_sha256':p['zip_sha256'],'private_key_not_included':True,
              'nonce_b64':base64.b64encode(b'123456789012').decode(),
              'aad_b64':base64.b64encode(aad).decode(),
              'ciphertext_b64':[base64.b64encode(msg).decode()],
              'ciphertext_sha256':hashlib.sha256(msg).hexdigest()}
    enc=(json.dumps(envelope,sort_keys=True)*3).encode()
    # For test make valid JSON but long enough; ensure proper 1 JSON object.
    enc=(json.dumps({**envelope,'padding':'X'*250},sort_keys=True)+'\n').encode()
    note=b'PUBLIC SAFE README TEST ONLY\n'
    p['envelope_blob_sha1']=m.git_blob_sha1(enc)
    p['readme_blob_sha1']=m.git_blob_sha1(note)
    return enc,note


class RegistryTest(unittest.TestCase):
    def test_current_registry_is_valid(self):
        summary=m.validate_registry(load())
        self.assertEqual(summary['packets'],12)
        self.assertEqual(summary['candidate_features'],17)
        self.assertEqual(summary['github_reference_features'],12)
        self.assertEqual(summary['pc_restored_verified'],0)
    def test_report_does_not_claim_studio(self):
        d=m.build_report(load())
        self.assertEqual(d['pc_status'],'PARTIAL_NOT_READY')
        self.assertTrue(all(p['status']=='DEPENDENCY_HOLD_NOT_PC_READY' for p in d['queue']))
        self.assertEqual(d['remote_verification']['status'],'NOT_RUN_THIS_COMMAND')
    def test_identical_paths_different_commits_allowed(self):
        d=load()
        metrics,cosmetic=d['sealed_packets'][-2:]
        self.assertEqual(metrics['envelope_path'],cosmetic['envelope_path'])
        self.assertNotEqual(metrics['commit'],cosmetic['commit'])
        m.validate_registry(d)
    def test_same_commit_path_duplicate_rejected(self):
        d=load(); d['sealed_packets'][-1]['commit']=d['sealed_packets'][-2]['commit']
        with self.assertRaisesRegex(m.AuditError,'SAME_COMMIT_PATH_REUSED'):
            m.validate_registry(d)
    def test_duplicate_packet_rejected(self):
        d=load();d['sealed_packets'][-1]['packet_id']=d['sealed_packets'][0]['packet_id']
        with self.assertRaisesRegex(m.AuditError,'DUPLICATE_OR_BAD_PACKET_ID'):
            m.validate_registry(d)
    def test_bad_commit_rejected(self):
        d=load();d['sealed_packets'][0]['commit']='main'
        with self.assertRaisesRegex(m.AuditError,'BAD_COMMIT'):
            m.validate_registry(d)
    def test_path_traversal_rejected(self):
        for bad in ('handoffs/../../private.key','https://evil/x','handoffs/a%2fb','handoffs/../x', 'handoffs\\x'):
            with self.subTest(bad=bad):
                d=load();d['sealed_packets'][0]['envelope_path']=bad
                with self.assertRaises(m.AuditError):
                    m.validate_registry(d)
    def test_wrong_project_rejected(self):
        d=load();d['repo']='someone-else/evil'
        with self.assertRaisesRegex(m.AuditError,'BAD_PROJECT_IDENTITY'):
            m.validate_registry(d)
    def test_fake_pc_pass_rejected(self):
        d=load();d['sealed_packets'][0]['studio_qa']='PASS'
        with self.assertRaisesRegex(m.AuditError,'PC_QA_CANNOT_BE_AUTO_CLAIMED'):
            m.validate_registry(d)
        d=load();d['pc_status']='STUDIO_QA_PASS'
        with self.assertRaisesRegex(m.AuditError,'UNSUPPORTED_PC_STATUS'):
            m.validate_registry(d)
    def test_secret_field_rejected(self):
        d=load();d['sealed_packets'][0]['private_key']='password'
        with self.assertRaisesRegex(m.AuditError,'SECRET_FIELD_IN_PUBLIC_REGISTRY'):
            m.validate_registry(d)
    def test_missing_dependency_rejected(self):
        d=load();d['sealed_packets'][0]['depends_on_packets']=['NOT_EXIST']
        with self.assertRaisesRegex(m.AuditError,'MISSING_OR_SELF_DEPENDENCY'):
            m.validate_registry(d)
    def test_cycle_rejected(self):
        d=load();d['sealed_packets'][0]['depends_on_packets']=[d['sealed_packets'][1]['packet_id']]
        with self.assertRaisesRegex(m.AuditError,'DEPENDENCY_CYCLE'):
            m.validate_registry(d)
    def test_duplicate_json_field_rejected(self):
        with self.assertRaisesRegex(m.AuditError,'DUPLICATE_JSON_KEY'):
            m._strict_json('{"x":1,"x":2}')
    def test_output_exclusive(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'report.json'
            args=['--registry',str(ROOT/'docs'/'P0D_INTAKE_REGISTRY.json'),'--output',str(p)]
            self.assertEqual(m.main(args),0)
            self.assertEqual(m.main(args),2)
    def test_no_network_default(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'report.json'
            with patch.object(m,'fetch_pinned',side_effect=AssertionError('NETWORK_CALLED')):
                self.assertEqual(m.main(['--registry',str(ROOT/'docs'/'P0D_INTAKE_REGISTRY.json'), '--output',str(p)]),0)


class AuditTest(unittest.TestCase):
    def test_valid_fixture_passes_exact_blob_and_identity(self):
        p=copy.deepcopy(load()['sealed_packets'][0]); enc,note=build_fixture(p)
        self.assertTrue(m.verify_envelope_bytes(enc,p))
        self.assertTrue(m.verify_readme_bytes(note,p))
    def test_modification_detected(self):
        p=copy.deepcopy(load()['sealed_packets'][0]); enc,note=build_fixture(p)
        with self.assertRaisesRegex(m.AuditError,'ENVELOPE_BLOB_MISMATCH'):
            m.verify_envelope_bytes(enc+b'changed',p)
        with self.assertRaisesRegex(m.AuditError,'README_BLOB_MISMATCH'):
            m.verify_readme_bytes(note+b'changed',p)
    def test_wrong_packet_detected_even_with_new_blob_sha(self):
        p=copy.deepcopy(load()['sealed_packets'][0]); enc,note=build_fixture(p)
        doc=json.loads(enc);doc['packet_id']='other-packet';modified=(json.dumps(doc)+'\n').encode();p['envelope_blob_sha1']=m.git_blob_sha1(modified)
        with self.assertRaisesRegex(m.AuditError,'ENVELOPE_IDENTITY_MISMATCH'):
            m.verify_envelope_bytes(modified,p)
    def test_wrong_zip_detected(self):
        p=copy.deepcopy(load()['sealed_packets'][0]); enc,note=build_fixture(p)
        p['zip_sha256']='0'*64
        with self.assertRaisesRegex(m.AuditError,'ENVELOPE_IDENTITY_MISMATCH'):
            m.verify_envelope_bytes(enc,p)
    def test_bad_aad_detected(self):
        p=copy.deepcopy(load()['sealed_packets'][0]); enc,_=build_fixture(p)
        doc=json.loads(enc);doc['aad_b64']=base64.b64encode(b'other').decode();modified=(json.dumps(doc)+'\n').encode();p['envelope_blob_sha1']=m.git_blob_sha1(modified)
        with self.assertRaisesRegex(m.AuditError,'ENVELOPE_CIPHER_INTEGRITY_FAIL'):
            m.verify_envelope_bytes(modified,p)
    def test_duplicate_field_in_envelope_rejected(self):
        p=copy.deepcopy(load()['sealed_packets'][0]);enc,_=build_fixture(p)
        duplicate=enc[:-2]+b',"packet_id":"override"}\n'
        p['envelope_blob_sha1']=m.git_blob_sha1(duplicate)
        with self.assertRaisesRegex(m.AuditError,'DUPLICATE_JSON_KEY'):
            m.verify_envelope_bytes(duplicate,p)
    def test_audit_marks_network_failure_blocked_not_pc_pass(self):
        d=load()
        def fails(commit,path):
            raise OSError('offline')
        summary,checks=m.audit(d,fetcher=fails)
        self.assertEqual(summary['remote_file_pairs_pass'],0)
        self.assertEqual(summary['readback_status'],'BLOCKED')
        self.assertTrue(all(c['pc_restored']=='NOT_TESTED' and c['studio_qa']=='NOT_TESTED' for c in checks))
    def test_audit_one_packet_fixture(self):
        d=load();d['sealed_packets']=d['sealed_packets'][:1];p=d['sealed_packets'][0]
        enc,note=build_fixture(p)
        def fake(commit,path):
            self.assertEqual(commit,p['commit'])
            return enc if path==p['envelope_path'] else note
        s,checks=m.audit(d,fetcher=fake)
        self.assertEqual(s['readback_status'],'PASS')
        self.assertEqual(s['remote_file_pairs_pass'],1)
        self.assertEqual(s['studio_qa_from_reference_pass'],0)


if __name__ == '__main__':
    unittest.main()
