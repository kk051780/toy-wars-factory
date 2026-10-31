"""Adversarial offline regression suite; no ChatGPT/GitHub credentials or calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'tools/system_prompt_drift_audit.py'
spec = importlib.util.spec_from_file_location('system_prompt_drift_audit', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

OBS = '2026-10-31T02:25:00Z'
START = '2026-10-31T02:15:00Z'
DONE = '2026-10-31T02:16:00Z'
RUN_ID = '12345678-1234-1234-1234-123456789abc'
ANCHORS = ' '.join([mod.REPO,mod.COORDINATOR,'PEEK','CAS','REVIEWER','independent','CI','Gemini','Roblox','spend','publish'])


def long_prompt(n):
    return ANCHORS + ('x' * max(0,n-len(ANCHORS)))


def row(role):
    c=mod.ROLES[role]
    return {'role': role, 'task_id': c['task_id'], 'schedule': c['schedule'],
            'is_enabled':True, 'prompt':long_prompt(c['compacted_utf16_chars']),
            'last_run':{'id':RUN_ID,'recorded_status':'completed', 'started_at':START,
                        'completed_at':DONE,'chat_ref':None}}


def fixture():
    return {'schema':1,'repository':mod.REPO,'observed_at':OBS,
            'snapshots':[row(role) for role in mod.ROLES]}


class PromptDriftAuditTests(unittest.TestCase):
    def test_baseline_three_roles_unverified(self):
        result=mod.audit(fixture())
        self.assertEqual(result['status'],'BASELINE_WITHIN_THRESHOLD_UNVERIFIED')
        self.assertEqual(result['total_baseline_chars'],21361)
        self.assertEqual(result['total_observed_chars'],21361)
        self.assertTrue(all(x['regrowth_chars']==0 for x in result['roles']))
        self.assertEqual(result['verification'],'NOT_VERIFIED')

    def test_actual_observed_regrowth_flags_meta_and_reviewer_only(self):
        data=fixture()
        for row_,n in zip(data['snapshots'],[7503,8069,8125]):row_['prompt']=long_prompt(n)
        result=mod.audit(data)
        self.assertEqual(result['total_observed_chars'],23697)
        self.assertEqual(result['total_regrowth_chars'],2336)
        self.assertEqual(result['status'],'REVIEW_REQUIRED')
        self.assertNotIn('PROMPT_REGROWTH_REVIEW',result['roles'][0]['warnings'])
        for row_ in result['roles'][1:]:
            self.assertIn('PROMPT_REGROWTH_REVIEW',row_['warnings'])

    def test_small_change_does_not_overflag(self):
        x=fixture();x['snapshots'][0]['prompt']=long_prompt(7347)
        self.assertEqual(mod.audit(x)['status'],'BASELINE_WITHIN_THRESHOLD_UNVERIFIED')

    def test_missing_anchors_report_only_not_policy_compliance(self):
        x=fixture();x['snapshots'][0]['prompt']=' ' * 7400
        r=mod.audit(x)
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
        self.assertIn('TEXTUAL_SAFETY_ANCHORS_MISSING_REVIEW',r['roles'][0]['warnings'])
        self.assertIn('fenced_write',r['roles'][0]['missing_text_anchors'])

    def test_text_anchor_is_heuristic_and_never_authorization(self):
        x=fixture();x['snapshots'][0]['prompt']=long_prompt(7346)
        self.assertFalse(any(mod.audit(x)['authority'].values()))

    def test_disabled_task_detected(self):
        x=fixture();x['snapshots'][1]['is_enabled']=False
        self.assertIn('TASK_DISABLED',mod.audit(x)['roles'][1]['warnings'])

    def test_schedule_drift_detected(self):
        x=fixture();x['snapshots'][1]['schedule']=x['snapshots'][1]['schedule'].replace('HOURLY','DAILY')
        self.assertIn('SCHEDULE_CHANGED_FROM_COMPACTED_BASELINE',mod.audit(x)['roles'][1]['warnings'])

    def test_short_prompt_requires_review(self):
        x=fixture();x['snapshots'][0]['prompt']='PEEK CAS Gemini Roblox publish CI '+mod.REPO+' '+mod.COORDINATOR
        self.assertIn('UNUSUALLY_SHORT_PROMPT_REVIEW',mod.audit(x)['roles'][0]['warnings'])

    def test_no_update_is_not_caused_by_prompt(self):
        x=fixture();x['snapshots'][1]['last_run']['recorded_status']='no_update'
        self.assertIn('LAST_RUN_NO_UPDATE_CAUSE_UNKNOWN',mod.audit(x)['roles'][1]['warnings'])
        self.assertNotIn('PROMPT_REGROWTH_REVIEW',mod.audit(x)['roles'][1]['warnings'])

    def test_inprogress_blocks_mutation(self):
        x=fixture();x['snapshots'][2]['last_run']['recorded_status']='in_progress'
        x['snapshots'][2]['last_run']['completed_at']=None
        self.assertIn('RUN_IN_PROGRESS_NO_PROMPT_MUTATION',mod.audit(x)['roles'][2]['warnings'])
        self.assertFalse(mod.audit(x)['authority']['prompt_edit_allowed'])

    def test_failed_run_note(self):
        x=fixture();x['snapshots'][1]['last_run']['recorded_status']='failed'
        self.assertIn('LAST_RUN_FAILED_CAUSE_UNKNOWN',mod.audit(x)['roles'][1]['warnings'])

    def test_missing_run_is_unknown(self):
        x=fixture();x['snapshots'][0]['last_run']=None
        self.assertIn('MISSING_LAST_RUN',mod.audit(x)['roles'][0]['warnings'])

    def test_hash_is_not_plaintext_prompt(self):
        x=fixture();x['snapshots'][0]['prompt']+=' PRIVATE_SECRET_123'
        out=mod.audit(x)
        self.assertNotIn('PRIVATE_SECRET_123',json.dumps(out))
        self.assertEqual(len(out['roles'][0]['prompt_sha256']),64)

    def test_utf16_units_handle_nonbmp(self):
        self.assertEqual(mod.utf16_units('A🥷B'),4)
        x=fixture();x['snapshots'][0]['prompt']+='🥷'
        self.assertEqual(mod.audit(x)['roles'][0]['regrowth_chars'],2)

    def test_never_mutates_inputs(self):
        x=fixture();before=copy.deepcopy(x)
        mod.audit(x)
        self.assertEqual(x,before)

    def test_every_result_no_grants(self):
        for inp in [fixture(), {}, None, {'write_allowed':True}]:
            with self.subTest(inp=type(inp).__name__):
                out=mod.audit(inp)
                self.assertTrue(all(v is False for v in out['authority'].values()))
                self.assertIs(out['changes_applied'],False)
                self.assertEqual(out['verification'],'NOT_VERIFIED')

    def test_wrong_repository_fails_closed(self):
        x=fixture();x['repository']='other/game'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_wrong_or_swapped_task_id_fails_closed(self):
        x=fixture();x['snapshots'][1]['task_id']=mod.ROLES['WORKER']['task_id']
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_duplicate_role_fails_closed(self):
        x=fixture();x['snapshots'][1]=copy.deepcopy(x['snapshots'][0])
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_missing_role_fails_closed(self):
        x=fixture();x['snapshots'].pop()
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_unknown_role_fails_closed(self):
        x=fixture();x['snapshots'][1]['role']='CONTROLLER'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_injected_permission_fails_closed(self):
        x=fixture();x['snapshots'][0]['write_allowed']=True
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_boolean_schema_rejected(self):
        x=fixture();x['schema']=True
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_boolean_enabled_must_be_actual_bool(self):
        x=fixture();x['snapshots'][0]['is_enabled']='true'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_empty_and_oversize_prompt_fails_closed(self):
        for value in ('', 'x'*65537, None):
            with self.subTest(length=len(value) if value is not None else None):
                x=fixture();x['snapshots'][0]['prompt']=value
                self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_malformed_schedule_fails_closed(self):
        x=fixture();x['snapshots'][0]['schedule']=42
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_naive_timestamp_fails_closed(self):
        x=fixture();x['observed_at']='2026-10-31T02:25:00'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_future_run_start_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['started_at']='2026-11-01T02:25:00Z'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_completion_before_start_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['completed_at']='2026-10-31T02:14:00Z'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_inconsistent_run_status_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['completed_at']=None
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_invalid_run_uuid_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['id']='not-a-real-run'
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_extra_run_claim_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['provider_verified']=True
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_invalid_chat_ref_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['chat_ref']={'type':'chatgpt','id':None}
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_invalid_run_status_type_rejected(self):
        x=fixture();x['snapshots'][0]['last_run']['recorded_status']={}
        self.assertEqual(mod.audit(x)['status'],'INVALID_INPUT')

    def test_no_implicit_automatic_actions_on_apparent_pass(self):
        x=fixture();r=mod.audit(x)
        self.assertEqual(r['status'],'BASELINE_WITHIN_THRESHOLD_UNVERIFIED')
        self.assertFalse(r['authority']['start_now_allowed'])
        self.assertFalse(r['authority']['merge_allowed'])
        self.assertFalse(r['authority']['external_spend_allowed'])

    def test_cli_reject_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.json';p.write_text('{"schema":1,"schema":1}',encoding='utf-8')
            r=subprocess.run([sys.executable,str(SOURCE),str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
            self.assertEqual(json.loads(r.stdout)['status'],'INVALID_INPUT')

    def test_cli_reject_nonfinite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.json';p.write_text('{"schema":NaN}',encoding='utf-8')
            r=subprocess.run([sys.executable,str(SOURCE),str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
            self.assertEqual(json.loads(r.stdout)['status'],'INVALID_INPUT')

    def test_cli_valid_result(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.json';p.write_text(json.dumps(fixture()),encoding='utf-8')
            r=subprocess.run([sys.executable,str(SOURCE),str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0)
            self.assertEqual(json.loads(r.stdout)['total_observed_chars'],21361)


if __name__=='__main__':
    unittest.main()