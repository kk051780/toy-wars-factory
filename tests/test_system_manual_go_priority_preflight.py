"""Mock-only regressions, not original GitHub/Automations provider proof."""
from __future__ import annotations
import copy
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import system_manual_go_priority_preflight as g

SHA_A = 'a'*40
SHA_B = 'b'*40
REF = 'c'*40
ID1 = 'main_shutdown_sequential_save_deadline_20261028'
ID2 = 'main_expired_lease_refresh_failure_unsavable_play_20261028'


def state():
    return {'schema':1,'task_id':g.WORKER_TASK,'epoch':324,'holder':None,
            'authorized_tasks':{'WORKER':g.WORKER_TASK},
            'manual_go_context':{'mode':'FENCED_DISPATCH_EXISTING_WORKER_ONLY',
                                 'next_actor':'REGISTERED_WORKER',
                                 'source_main_sha':SHA_A,
                                 'priority_request_ids':[ID1,ID2]}}


def work(s1='OPEN', s2='OPEN'):
    return {'schema':1,'requests':[{'id':ID1,'status':s1,'assigned_role':'WORKER'},
                                   {'id':ID2,'status':s2,'assigned_role':'WORKER'}]}


def frame():
    return {'repository':g.REPO,'current_main_sha':SHA_A,
            'coordinator_ref':REF,'work_requests_ref':REF,
            'coordinator':state(),'work_requests':work()}


def eval_frame(f=None):
    return g.preflight(**(frame() if f is None else f))


class PriorityPreflightTest(unittest.TestCase):
    def assert_no_authority(self, f):
        x=eval_frame(f)
        self.assertTrue(x['authority'])
        self.assertTrue(all(v is False for v in x['authority'].values()))
        self.assertFalse(x['allow_worker_run_now'])
        self.assertFalse(x['allow_dispatch_cas'])
        self.assertEqual(x['source_verification'],'UNTRUSTED_CALLER_INPUT')
        self.assertFalse(x['control_ref_authenticated'])
        return x

    def test_fresh_two_ids_still_not_dispatch_authorized(self):
        x=self.assert_no_authority(frame())
        self.assertEqual(x['status'],'SNAPSHOT_CONSISTENT_FURTHER_HOST_CHECKS_REQUIRED')
        self.assertEqual(x['selected_request_count'],2)

    def test_current_real_world_resolved_both_and_stale_main(self):
        f=frame();f['current_main_sha']=SHA_B
        f['work_requests']=work('RESOLVED_MERGED_MAIN_QA_AND_HANDOFF_PASSED',
                                'RESOLVED_MERGED_MAIN_QA_AND_HANDOFF_PASSED')
        x=self.assert_no_authority(f)
        self.assertEqual(x['status'],'WAIT_RESELECT_CURRENT_WORK')
        self.assertEqual(x['resolved_ids'],[ID2,ID1] if ID2<ID1 else [ID1,ID2])
        self.assertEqual(x['non_open_worker_ids'],sorted([ID1,ID2]))
        self.assertTrue(x['stale_main'])

    def test_resolved_without_main_change(self):
        f=frame();f['work_requests']=work('RESOLVED_MERGED_MAIN_QA_AND_HANDOFF_PASSED')
        self.assertEqual(self.assert_no_authority(f)['status'],'WAIT_RESELECT_CURRENT_WORK')

    def test_stale_main_with_open_ids(self):
        f=frame();f['current_main_sha']=SHA_B
        x=self.assert_no_authority(f)
        self.assertEqual(x['status'],'WAIT_RESELECT_CURRENT_WORK')
        self.assertEqual(x['resolved_ids'],[])
        self.assertTrue(x['stale_main'])

    def test_missing_pinned_request(self):
        f=frame();f['work_requests']['requests'].pop()
        x=self.assert_no_authority(f)
        self.assertEqual(x['status'],'WAIT_RESELECT_CURRENT_WORK')
        self.assertEqual(x['missing_ids'],[ID2])

    def test_wrong_role_stops(self):
        f=frame();f['work_requests']['requests'][0]['assigned_role']='META'
        self.assertEqual(self.assert_no_authority(f)['status'],'WAIT_RESELECT_CURRENT_WORK')

    def test_changed_status_stops(self):
        for status in ('IMPLEMENTED_IN_NEW_PR_HEAD_AWAIT_INDEPENDENT_REVIEW','SUPERSEDED_BY_AUTHOR_REHANDOFF_AND_REVIEW',
                       'CLOSED_QUARANTINED_NOT_MERGED','REQUEST_CHANGES_DUPLICATE_ADOPTION_RECEIPT'):
            with self.subTest(status=status):
                f=frame();f['work_requests']['requests'][0]['status']=status
                self.assertEqual(self.assert_no_authority(f)['status'],'WAIT_RESELECT_CURRENT_WORK')

    def test_duplicate_priority_ids_rejected(self):
        f=frame();f['coordinator']['manual_go_context']['priority_request_ids'].append(ID1)
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_INVALID_PRIORITY_IDS')

    def test_duplicate_ledger_id_rejected(self):
        f=frame();f['work_requests']['requests'].append(copy.deepcopy(f['work_requests']['requests'][0]))
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_INVALID_OR_DUPLICATE_REQUESTS')

    def test_mixed_control_refs_rejected(self):
        f=frame();f['work_requests_ref']=SHA_A
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_MIXED_COORDINATOR_SNAPSHOTS')

    def test_wrong_repo_rejected(self):
        f=frame();f['repository']='attacker/repo'
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_REPOSITORY_BINDING')

    def test_bad_main_or_ref_rejected(self):
        for key in ('current_main_sha','coordinator_ref','work_requests_ref'):
            for value in ('broken',True,None):
                with self.subTest(key=key,value=value):
                    f=frame();f[key]=value
                    self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_UNVERIFIED_REF_SHAPE')

    def test_other_holder_waits_even_on_fresh_priority(self):
        f=frame();f['coordinator']['holder']={'kind':'CONTROLLER','owner_id':'other'}
        self.assertEqual(self.assert_no_authority(f)['status'],'WAIT_SHARED_LOCK')

    def test_no_priority_waits_for_new_work(self):
        f=frame();f['coordinator']['manual_go_context']['priority_request_ids']=[]
        x=self.assert_no_authority(f)
        self.assertEqual(x['status'],'WAIT_SELECT_NEW_WORK')
        self.assertEqual(x['open_worker_request_count'],2)

    def test_missing_routing_context(self):
        f=frame();f['coordinator'].pop('manual_go_context')
        self.assertEqual(self.assert_no_authority(f)['status'],'WAIT_FRESH_ROUTING_CONTEXT')

    def test_unknown_routing_mode_waits(self):
        f=frame();f['coordinator']['manual_go_context']['mode']='UNKNOWN'
        self.assertEqual(self.assert_no_authority(f)['status'],'WAIT_FRESH_ROUTING_CONTEXT')

    def test_invalid_routing_main(self):
        f=frame();f['coordinator']['manual_go_context']['source_main_sha']='abc'
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_INVALID_ROUTING_MAIN')

    def test_unregistered_worker_denied(self):
        f=frame();f['coordinator']['authorized_tasks']['WORKER']='bad'
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_UNREGISTERED_WORKER')

    def test_invalid_coordinator_epoch_denied(self):
        f=frame();f['coordinator']['epoch']=True
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_INVALID_COORDINATOR')

    def test_invalid_work_requests_list_denied(self):
        f=frame();f['work_requests']['requests']='bad'
        self.assertEqual(self.assert_no_authority(f)['status'],'BLOCK_INVALID_REQUESTS')

    def test_input_no_mutation(self):
        f=frame();before=copy.deepcopy(f)
        eval_frame(f);self.assertEqual(f,before)

    def test_unknown_rows_do_not_grant_authority(self):
        f=frame();f['work_requests']['requests'].append({'id':'new_issue_meta','assigned_role':'META','status':'OPEN'})
        self.assertEqual(self.assert_no_authority(f)['status'],'SNAPSHOT_CONSISTENT_FURTHER_HOST_CHECKS_REQUIRED')

    def test_cli_stale_exits_nonzero_with_safe_status(self):
        f=frame();f['current_main_sha']=SHA_B
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'frame.json';path.write_text(json.dumps(f))
            p=subprocess.run([sys.executable,str(ROOT/'tools/system_manual_go_priority_preflight.py'),
                              '--frame',str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2,p.stderr)
            out=json.loads(p.stdout);self.assertEqual(out['status'],'WAIT_RESELECT_CURRENT_WORK')
            self.assertFalse(out['allow_worker_run_now'])

    def test_cli_fresh_returns_zero_but_not_authority(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'frame.json';path.write_text(json.dumps(frame()))
            p=subprocess.run([sys.executable,str(ROOT/'tools/system_manual_go_priority_preflight.py'),
                              '--frame',str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertFalse(json.loads(p.stdout)['authority']['may_dispatch'])

    def test_cli_duplicate_json_field_denied(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'frame.json';path.write_text('{"repository":"x","repository":"y","PRIVATE":"secret"}')
            p=subprocess.run([sys.executable,str(ROOT/'tools/system_manual_go_priority_preflight.py'),
                              '--frame',str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertEqual(json.loads(p.stdout)['reason'],'DUPLICATE_JSON_FIELD')
            self.assertNotIn('secret',p.stdout)

    def test_cli_nonfinite_denied(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'frame.json';path.write_text('{"x":NaN}')
            p=subprocess.run([sys.executable,str(ROOT/'tools/system_manual_go_priority_preflight.py'),
                              '--frame',str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertEqual(json.loads(p.stdout)['reason'],'NONFINITE_JSON')

    def test_no_host_actions_or_network_apis(self):
        source=(ROOT/'tools/system_manual_go_priority_preflight.py').read_text()
        for forbidden in (r'(?<![A-Za-z0-9_])requests\.get\(', r'(?<![A-Za-z0-9_])urlopen\(',
                          r'(?<![A-Za-z0-9_])update_ref\(', r'(?<![A-Za-z0-9_])run_now\(',
                          r'(?<![A-Za-z0-9_])merge_pull_request\('):
            self.assertIsNone(re.search(forbidden,source))


if __name__=='__main__':unittest.main()
