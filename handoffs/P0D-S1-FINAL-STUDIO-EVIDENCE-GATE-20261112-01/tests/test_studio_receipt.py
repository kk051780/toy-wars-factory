import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import validate_studio_receipt as gate

class GateTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.root=Path(self.d.name)
        file=self.root/'logs'/'studio-native.txt'
        file.parent.mkdir()
        file.write_text('TEST FIXTURE ONLY; NOT REAL STUDIO EVIDENCE\n')
        self.file={'path':'logs/studio-native.txt','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'size':len(file.read_bytes())}
        self.receipt={
            'schema':gate.SCHEMA,'game_id':gate.GAME,'work_id':gate.WORK,'release_id':gate.RELEASE,
            'rc_commit':gate.RC_SHA,'rc_manifest_sha256':gate.RC_MANIFEST_SHA256,
            'source_tree_sha':gate.SOURCE_TREE_SHA,'rbxlx_sha256':gate.ROJO_RBXLX_SHA256,
            'evidence_kind':'ACTUAL_ROBLOX_STUDIO','game_published':False,'owner_release_approved':False,
            'pc_backup':{'original_place_sha256':'a'*64,'checkpoint_sha256':'b'*64,'preserved_separately':True},
            'studio_session':{'client_session_ids':['clientA','clientB'],'normal_exit':True,'studio_pid_gone':True,'saved_place_reopened':True,'measured_min_fps':31,'mobile_device_or_emulator':'TEST FIXTURE'},
            'boss_mode':'ON','boss_defer_owner_approved':False,
            'scenarios':[{'id':id,'status':'PASS','evidence':[self.file]} for id in gate.REQUIRED+gate.BOSS],
        }
    def run_gate(self,r=None):return gate.validate(r or self.receipt,self.root)
    def assert_blocked(self,r,code):
        out=self.run_gate(r)
        self.assertEqual(out['status'],'BLOCKED')
        self.assertTrue(any(code in x for x in out['errors']),out['errors'])
    def test_fixture_validates_local_hash_and_shape_only(self):
        # Passing synthetic fixture never attests genuine Roblox engine identity.
        out=self.run_gate()
        self.assertEqual(out['status'],'STUDIO_EVIDENCE_GATE_PASS')
        self.assertFalse(out['roblox_publishing_permitted'])
        self.assertIn('NOT_AN_ENGINE_ATTESTATION',out['scope'])
        self.assertEqual(out['passed_scenarios'],len(gate.REQUIRED)+len(gate.BOSS))
    def test_off_boss_requires_explicit_owner_defer(self):
        r=copy.deepcopy(self.receipt);r['boss_mode']='OFF';r['scenarios']=[x for x in r['scenarios'] if x['id'] not in gate.BOSS]
        self.assert_blocked(r,'BOSS_DEFER_OWNER_CONSENT_REQUIRED')
    def test_off_boss_consented_schema_still_requires_independent_human_review(self):
        r=copy.deepcopy(self.receipt);r['boss_mode']='OFF';r['scenarios']=[x for x in r['scenarios'] if x['id'] not in gate.BOSS]
        r['boss_defer_owner_approved']=True;r['boss_defer_owner_issue_url']='https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-999999'
        out=self.run_gate(r);self.assertEqual(out['status'],'BLOCKED')
        self.assertIn('BOSS_DISABLED_ENGINE_GATE_UNRESOLVED_HUMAN_REVIEW_REQUIRED',out['errors'])
        self.assertEqual(out['required_scenarios'],len(gate.REQUIRED))
    def test_does_not_authenticate_fake_owner_link(self):
        # The pattern is a prompt for a separate human review of decision.
        r=copy.deepcopy(self.receipt);r['boss_mode']='OFF';r['scenarios']=[x for x in r['scenarios'] if x['id'] not in gate.BOSS]
        r['boss_defer_owner_approved']=True;r['boss_defer_owner_issue_url']='https://github.com/example/other/issues/220#issuecomment-1'
        self.assert_blocked(r,'BOSS_DEFER_OWNER_DECISION_LINK_REQUIRED')
    def test_wrong_rc_sha_fails(self):
        r=copy.deepcopy(self.receipt);r['rc_commit']='f'*40;self.assert_blocked(r,'PIN_MISMATCH_RC_COMMIT')
    def test_wrong_build_pin_fails(self):
        r=copy.deepcopy(self.receipt);r['rbxlx_sha256']='a'*64;self.assert_blocked(r,'PIN_MISMATCH_RBXLX_SHA256')
    def test_mock_engine_claim_fails(self):
        r=copy.deepcopy(self.receipt);r['evidence_kind']='MOCK_LUAU';self.assert_blocked(r,'NOT_REAL_STUDIO')
    def test_one_client_fails(self):
        r=copy.deepcopy(self.receipt);r['studio_session']['client_session_ids']=['onlyA'];self.assert_blocked(r,'TWO_DISTINCT')
    def test_duplicate_client_fails(self):
        r=copy.deepcopy(self.receipt);r['studio_session']['client_session_ids']=['same','same'];self.assert_blocked(r,'TWO_DISTINCT')
    def test_missing_persistent_pc_backup_fails(self):
        r=copy.deepcopy(self.receipt);r['pc_backup']['preserved_separately']=False;self.assert_blocked(r,'PC_BACKUP_NOT_PRESERVED')
    def test_studio_process_not_exited_fails(self):
        r=copy.deepcopy(self.receipt);r['studio_session']['studio_pid_gone']=False;self.assert_blocked(r,'STUDIO_PID_EXIT_UNCONFIRMED')
    def test_mobile_measure_missing_fails(self):
        r=copy.deepcopy(self.receipt);r['studio_session']['measured_min_fps']=None;self.assert_blocked(r,'MEASURED_FPS_REQUIRED')
    def test_missing_case_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios']=r['scenarios'][:-1];self.assert_blocked(r,'NOT_TESTED_D07_CLEANUP')
    def test_not_tested_case_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][4]['status']='NOT_TESTED';self.assert_blocked(r,'NOT_TESTED_')
    def test_fail_case_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][4]['status']='FAIL';self.assert_blocked(r,'FAIL_')
    def test_duplicate_scenario_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'].append(copy.deepcopy(r['scenarios'][0]));self.assert_blocked(r,'SCENARIO_DUPLICATE')
    def test_unrecognized_scenario_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'].append({'id':'EXPLOIT_BONUS','status':'PASS','evidence':[self.file]});self.assert_blocked(r,'UNRECOGNIZED')
    def test_empty_evidence_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence']=[];self.assert_blocked(r,'EVIDENCE_MISSING')
    def test_wrong_evidence_digest_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence'][0]['sha256']='0'*64;self.assert_blocked(r,'EVIDENCE_HASH_OR_SIZE_MISMATCH')
    def test_wrong_evidence_size_fails(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence'][0]['size']=999;self.assert_blocked(r,'EVIDENCE_HASH_OR_SIZE_MISMATCH')
    def test_nonempty_evidence_hash_rejected_if_file_missing(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence'][0]['path']='logs/missing.txt';self.assert_blocked(r,'EVIDENCE_FILE_MISSING')
    def test_evidence_traversal_rejected(self):
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence'][0]['path']='../private.txt';self.assert_blocked(r,'EVIDENCE_PATH_TRAVERSAL')
    def test_symlink_rejected(self):
        try:(self.root/'logs'/'symlink').symlink_to(self.root/'logs'/'studio-native.txt')
        except (OSError,NotImplementedError):self.skipTest('symlink unsupported')
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence'][0]['path']='logs/symlink';self.assert_blocked(r,'EVIDENCE_FILE_MISSING_OR_SYMLINK')
    def test_symlink_directory_rejected(self):
        try:(self.root/'alias').symlink_to(self.root/'logs',target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('symlink unsupported')
        r=copy.deepcopy(self.receipt);r['scenarios'][0]['evidence'][0]['path']='alias/studio-native.txt'
        self.assert_blocked(r,'EVIDENCE_FILE_MISSING_OR_SYMLINK')
    def test_no_accidental_publish(self):
        r=copy.deepcopy(self.receipt);r['game_published']=True;self.assert_blocked(r,'PUBLISH_MUST_REMAIN_FALSE')
    def test_cannot_self_approve_release(self):
        r=copy.deepcopy(self.receipt);r['owner_release_approved']=True;self.assert_blocked(r,'RELEASE_APPROVAL_CANNOT_BE_INFERRED')
    def test_source_manifest_altered(self):
        r=copy.deepcopy(self.receipt);r['rc_manifest_sha256']='f'*64;self.assert_blocked(r,'PIN_MISMATCH_RC_MANIFEST_SHA256')
    def test_unknown_receipt_shape_blocked(self):
        r=self.run_gate('bad');self.assertEqual(r['status'],'BLOCKED')
    def test_off_boss_cannot_fake_boss_pass(self):
        r=copy.deepcopy(self.receipt);r['boss_mode']='OFF';r['boss_defer_owner_approved']=True;r['boss_defer_owner_issue_url']='https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-1'
        self.assert_blocked(r,'BOSS_OFF_CANNOT_HAVE_PASS')
if __name__=='__main__':unittest.main()
