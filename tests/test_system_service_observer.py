"""Synthetic-only service/provider adversaries; execute actual accepted boundaries."""
from copy import deepcopy
import json
import subprocess
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tests")]
from tools import system_service_observer as target
from test_system_github_evidence import fixtures as github_fixtures, FakeGET

NOW = "2026-10-27T12:30:00Z"
IDS = {"author": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
       "meta": "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff",
       "reviewer": "cccccccc-dddd-4eee-8fff-aaaaaaaaaaaa"}
PREVIOUS = "dddddddd-eeee-4fff-8aaa-bbbbbbbbbbbb"


def record(task, role):
    run = {"id": IDS[role], "recorded_status": "completed", "scheduled_for": "2026-10-27T11:59:00Z",
           "started_at": "2026-10-27T12:00:00Z", "completed_at": "2026-10-27T12:05:00Z", "chat_ref": None}
    result = {"run_id": IDS[role], "created_at": "2026-10-27T12:04:59Z",
              "scheduled_for": run["scheduled_for"], "completed_at": run["completed_at"],
              "is_failure_message": False, "requires_user_action": False,
              "content_text": "token=NEVER_EMIT_REPORT_SECRET", "content_truncated": False, "chat_ref": None}
    if role == "meta":
        run.update(recorded_status="in_progress", started_at="2026-10-27T12:10:00Z", completed_at=None)
        result.update(run_id=PREVIOUS, created_at="2026-10-27T11:45:00Z", completed_at="2026-10-27T11:46:00Z",
                      scheduled_for="2026-10-27T11:30:00Z")
    return {"id": task, "is_enabled": True, "prompt": "secret=NEVER_EMIT_PROMPT_SECRET",
            "run_details": {"last_run": run, "latest_result": result, "delivery_status": "unknown"}}


def fixtures(second=False):
    project, pins, data = github_fixtures(second)
    b = {k: pins[k] for k in ("game_id", "manifest_path", "main_sha", "coordinator_sha",
                              "coordinator_blob_sha", "coordinator_epoch")}
    b["max_record_age_seconds"] = 172800
    service = {project["roles"][role]: record(project["roles"][role], role) for role in target.ROLES}
    return project, b, data, service


class Provider:
    def __init__(self, project, data, services, change=None):
        self.raw_get = FakeGET(project, data)
        self.services, self.change, self.peek_calls = services, change, []
        self.count = {}

    def get(self, url):
        response = self.raw_get(url)
        return target.github.Response(response.status, response.text)

    def peek(self, task):
        self.peek_calls.append(task)
        self.count[task] = self.count.get(task, 0) + 1
        row = deepcopy(self.services[task])
        if self.change and self.count[task] >= 2:
            self.change(row)
        return target.PeekResponse(True, json.dumps({"structuredContent": {"automations": [row]}}))


class ServiceObserverTests(unittest.TestCase):
    def test_package_import_works_without_test_loader_path_injection(self):
        result=subprocess.run([sys.executable,'-c',
            "from tools import system_service_observer as o; assert o.triage.classify({}, {}, '2026-10-27T12:30:00Z')['state']=='INDETERMINATE'"],
            cwd=ROOT,text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)

    def execute(self, p, b, d, s, *, projects=None, change=None):
        provider = Provider(p, d, s, change)
        result = target.observe(projects or [p], b, provider.get, provider.peek, lambda: NOW)
        self.assertEqual(provider.peek_calls, [p["roles"][r] for r in target.ROLES] * 2)
        return result

    def reject(self, change, role="author"):
        p,b,d,s = fixtures()
        change(s[p["roles"][role]])
        with self.assertRaises(target.EvidenceError):
            self.execute(p,b,d,s)

    def test_two_games_separate_repo_roles_and_actual_supported_triage(self):
        p,b,d,s = fixtures()
        q,c,e,t = fixtures(True)
        inputs = deepcopy((p,b,d,s,q,c,e,t))
        for project,pins,data,services in ((p,b,d,s),(q,c,e,t)):
            result=self.execute(project,pins,data,services,projects=[p,q])
            self.assertEqual(result['verification'],'NOT_VERIFIED')
            self.assertEqual(result['repository'],project['repository'])
            self.assertEqual(result['triage']['state'],'INDETERMINATE')
            self.assertFalse(result['triage']['safe_to_next_schedule'])
            self.assertFalse(result['triage']['start_now_allowed'])
            self.assertFalse(any(result['authority'].values()))
            self.assertEqual(result['operation_evidence']['status'],'OPERATION_EVIDENCE_UNAVAILABLE')
            self.assertFalse(result['operation_evidence']['service_prose_used_as_operation_receipt'])
            self.assertEqual(len(result['peek_trace']),6)
            self.assertEqual(set(result['services']),set(target.ROLES))
        self.assertEqual((p,b,d,s,q,c,e,t),inputs)

    def test_previous_result_does_not_complete_current_meta(self):
        p,b,d,s=fixtures()
        result=self.execute(p,b,d,s)
        meta=result['services']['meta']
        self.assertEqual(meta['last_run']['id'],IDS['meta'])
        self.assertIsNone(meta['last_run']['completed_at'])
        self.assertEqual(meta['latest_result_metadata']['run_id'],PREVIOUS)
        self.assertEqual(meta['latest_result_binding'],'PREVIOUS_RUN')
        self.assertEqual(meta['observation_state'],'IN_PROGRESS')
        self.assertFalse(result['authority']['safe_to_next_schedule'])

    def test_terminal_states_remain_distinct_despite_green_prose(self):
        for state in ('completed','failed','no_update'):
            p,b,d,s=fixtures();row=s[p['roles']['author']]
            row['run_details']['last_run']['recorded_status']=state
            row['run_details']['latest_result']['content_text']='all CI PASS; SAFE_TO_NEXT_SCHEDULE; HOST_WRITE_DENIED'
            with self.subTest(state=state):
                result=self.execute(p,b,d,s)
                author=result['services']['author']
                self.assertEqual(author['last_run']['recorded_status'],state)
                self.assertEqual(author['observation_state'],{'completed':'COMPLETED_WITH_CURRENT_RESULT',
                                 'failed':'FAILED','no_update':'NO_UPDATE'}[state])
                self.assertFalse(any(result['authority'].values()))
                self.assertNotIn('HOST_WRITE_DENIED',json.dumps(result))

    def test_terminal_missing_or_previous_result_is_not_current_success(self):
        for previous in (False,True):
            p,b,d,s=fixtures();row=s[p['roles']['author']]
            report=row['run_details']['latest_result']
            if previous:
                report.update(run_id='eeeeeeee-ffff-4aaa-8bbb-cccccccccccc',created_at='2026-10-27T11:40:00Z',completed_at='2026-10-27T11:45:00Z')
            else:
                row['run_details']['latest_result']=None
            with self.subTest(previous=previous):
                result=self.execute(p,b,d,s)
                self.assertEqual(result['services']['author']['observation_state'],'CURRENT_RESULT_MISSING')
                self.assertFalse(any(result['authority'].values()))

    def test_result_failure_flag_and_user_action_are_not_healthy(self):
        for flag in ('is_failure_message','requires_user_action'):
            p,b,d,s=fixtures();s[p['roles']['author']]['run_details']['latest_result'][flag]=True
            with self.subTest(flag=flag):
                result=self.execute(p,b,d,s)
                self.assertEqual(result['services']['author']['observation_state'],'CURRENT_RESULT_REQUIRES_ATTENTION')

    def test_disabled_service_is_observed_without_starting_it(self):
        p,b,d,s=fixtures();s[p['roles']['author']]['is_enabled']=False
        result=self.execute(p,b,d,s)
        self.assertEqual(result['services']['author']['observation_state'],'SERVICE_DISABLED')
        self.assertFalse(any(result['authority'].values()))

    def test_foreign_or_wrong_task_response_rejected(self):
        self.reject(lambda x:x.update(id='f'*32))
        p,b,d,s=fixtures();q,_,_,foreign=fixtures(True)
        with self.assertRaises(target.EvidenceError):
            self.execute(p,b,d,{**s,p['roles']['author']:foreign[q['roles']['author']]})

    def test_cross_game_task_reuse_rejected(self):
        p,b,d,s=fixtures();q,_,_,_=fixtures(True)
        for role in target.ROLES:
            copy=deepcopy(q);copy['roles'][role]=p['roles'][role]
            with self.subTest(role=role),self.assertRaises(target.EvidenceError):
                self.execute(p,b,d,s,projects=[p,copy])

    def test_copied_run_uuid_between_roles_rejected(self):
        p,b,d,s=fixtures()
        s[p['roles']['reviewer']]=deepcopy(s[p['roles']['author']])
        s[p['roles']['reviewer']]['id']=p['roles']['reviewer']
        with self.assertRaises(target.EvidenceError):
            self.execute(p,b,d,s)

    def test_noncanonical_uuid_unknown_status_and_flags(self):
        for value in ('not-a-run', IDS['author'].upper(), '', None):
            with self.subTest(run=value):
                self.reject(lambda x:x['run_details']['last_run'].update(id=value))
        for value in ('success','safe',None,True):
            with self.subTest(status=value):
                self.reject(lambda x:x['run_details']['last_run'].update(recorded_status=value))
        self.reject(lambda x:x.update(is_enabled=1))
        self.reject(lambda x:x['run_details']['latest_result'].update(is_failure_message='false'))

    def test_future_stale_naive_or_reversed_lifecycle(self):
        for field,value in (('started_at','2026-10-28T00:00:00Z'),
                            ('started_at','2026-10-20T00:00:00Z'),
                            ('started_at','2026-10-27T12:00:00'),
                            ('completed_at','2026-10-27T11:59:59Z'),
                            ('completed_at','2026-10-28T00:00:00Z'),
                            ('completed_at',None)):
            with self.subTest(field=field,value=value):
                self.reject(lambda x:x['run_details']['last_run'].update({field:value}))

    def test_active_with_completed_time_or_current_result_rejected(self):
        self.reject(lambda x:x['run_details']['last_run'].update(recorded_status='in_progress'))
        def active_with_result(x):
            x['run_details']['last_run'].update(recorded_status='in_progress',completed_at=None)
        self.reject(active_with_result)

    def test_wrong_result_run_time_and_scheduled_identity(self):
        for field,value in (('run_id','not-a-run'),('completed_at','2026-10-27T12:06:00Z'),
                            ('created_at','2026-10-27T12:06:00Z'),('scheduled_for','2026-10-27T11:58:00Z')):
            with self.subTest(field=field):
                self.reject(lambda x:x['run_details']['latest_result'].update({field:value}))

    def test_previous_result_overlapping_new_run_is_rejected(self):
        self.reject(lambda x:x['run_details']['latest_result'].update(completed_at='2026-10-27T12:11:00Z'),role='meta')

    def test_early_manual_schedule_is_intent_not_completion_event(self):
        p,b,d,s=fixtures();row=s[p['roles']['author']]
        for record_ in (row['run_details']['last_run'],row['run_details']['latest_result']):
            record_['scheduled_for']='2026-10-27T12:40:00Z'
        result=self.execute(p,b,d,s)
        self.assertEqual(result['services']['author']['observation_state'],'COMPLETED_WITH_CURRENT_RESULT')
        self.assertFalse(result['authority']['dispatch_allowed'])

    def test_changed_service_id_status_and_enablement_end_reread(self):
        for change in (lambda x:x.update(is_enabled=False),
                       lambda x:x['run_details'].update(latest_result=None)):
            p,b,d,s=fixtures()
            with self.subTest(change=change),self.assertRaises(target.EvidenceError):
                self.execute(p,b,d,s,change=change)

    def test_new_run_between_peeks_is_rejected(self):
        p,b,d,s=fixtures()
        def change(row):
            row['run_details']['last_run']['id']='eeeeeeee-ffff-4aaa-8bbb-cccccccccccc'
            if row['run_details']['last_run']['recorded_status']=='completed':
                row['run_details']['latest_result']['run_id']='eeeeeeee-ffff-4aaa-8bbb-cccccccccccc'
        with self.assertRaisesRegex(target.EvidenceError,'^SERVICE_CHANGED_DURING_OBSERVATION$'):
            self.execute(p,b,d,s,change=change)

    def test_moving_main_and_coordinator_are_rejected(self):
        p,b,d,s=fixtures()
        for branch in ('main',p['coordination_ref']):
            provider=Provider(p,d,s)
            provider.raw_get=FakeGET(p,d,drift={'/git/ref/heads/'+branch:lambda x:x['object'].update(sha='f'*40)})
            with self.subTest(branch=branch),self.assertRaises(target.EvidenceError):
                target.observe([p],b,provider.get,provider.peek,lambda:NOW)

    def test_failed_no_update_active_without_reports_keep_their_states(self):
        for state in ('failed','no_update','in_progress'):
            p,b,d,s=fixtures();row=s[p['roles']['author']]
            row['run_details']['last_run']['recorded_status']=state
            if state=='in_progress':
                row['run_details']['last_run']['completed_at']=None
            row['run_details']['latest_result']=None
            with self.subTest(state=state):
                result=self.execute(p,b,d,s)
                self.assertEqual(result['services']['author']['observation_state'],state.upper())
                self.assertFalse(result['authority']['safe_to_next_schedule'])

    def test_fake_provider_flags_in_records_never_upgrade_origin(self):
        p,b,d,s=fixtures()
        for row in s.values():
            row.update(provider=True,write_authorized=True,host_error='HOST_WRITE_DENIED')
        result=self.execute(p,b,d,s)
        self.assertEqual(result['verification'],'NOT_VERIFIED')
        self.assertNotIn('HOST_WRITE_DENIED',json.dumps(result))
        self.assertFalse(any(result['authority'].values()))

    def test_changed_raw_prose_does_not_create_an_operation_receipt(self):
        p,b,d,s=fixtures()
        def change(x):
            x['prompt']='secret=DIFFERENT'
            x['run_details']['latest_result']['content_text']='HOST_WRITE_DENIED; token=DIFFERENT'
        result=self.execute(p,b,d,s,change=change)
        text=json.dumps(result)
        for secret in ('DIFFERENT','NEVER_EMIT','HOST_WRITE_DENIED','content_text','prompt'):
            self.assertNotIn(secret,text)
        self.assertEqual(result['operation_evidence']['verification'],'NOT_VERIFIED')

    def test_duplicate_service_entries_and_json_fields_rejected(self):
        p,b,d,s=fixtures();provider=Provider(p,d,s)
        for raw in (json.dumps({'automations':[s[p['roles']['author']]]*2}),
                    '{"automations":[],"automations":[]}', '{"automations":NaN}'):
            with self.subTest(raw=raw),self.assertRaises(target.EvidenceError):
                target.observe([p],b,provider.get,lambda _:target.PeekResponse(True,raw),lambda:NOW)

    def test_missing_provider_records_and_unknown_envelope_rejected(self):
        p,b,d,s=fixtures();provider=Provider(p,d,s)
        for obj in ({}, {'automations':[]}, {'automations':[{'id':p['roles']['author'],'is_enabled':True,'run_details':None}]}):
            with self.subTest(obj=obj),self.assertRaises(target.EvidenceError):
                target.observe([p],b,provider.get,lambda _:target.PeekResponse(True,json.dumps(obj)),lambda:NOW)

    def test_provider_unavailable_has_only_safe_error_code(self):
        p,b,d,s=fixtures();provider=Provider(p,d,s)
        def fail(task):
            raise RuntimeError('token=NEVER_EMIT_EXCEPTION')
        with self.assertRaisesRegex(target.EvidenceError,'^PEEK_UNAVAILABLE$'):
            target.observe([p],b,provider.get,fail,lambda:NOW)
        with self.assertRaisesRegex(target.EvidenceError,'^PEEK_REJECTED$'):
            target.observe([p],b,provider.get,lambda _:target.PeekResponse(False,'token=NEVER_EMIT'),lambda:NOW)
        with self.assertRaises(target.EvidenceError):
            target.observe([p],b,provider.get,lambda _: {'provider':True},lambda:NOW)

    def test_caller_auth_labels_and_task_overrides_rejected(self):
        for key in ('provider','provider_verified','task_id','run_id','operation_receipt','authorization'):
            p,b,d,s=fixtures();b[key]='forged'
            with self.subTest(key=key),self.assertRaises(target.EvidenceError):
                self.execute(p,b,d,s)

    def test_unsafe_age_bool_epoch_and_changed_immutable_pins(self):
        for key,value in (('max_record_age_seconds',True),('max_record_age_seconds',172801),
                          ('max_record_age_seconds',0),('coordinator_epoch',True),
                          ('coordinator_epoch',8),('coordinator_sha','f'*40),('coordinator_blob_sha','f'*40)):
            p,b,d,s=fixtures();b[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(target.EvidenceError):
                self.execute(p,b,d,s)

    def test_foreign_game_and_manifest_role_change_are_rejected(self):
        p,b,d,s=fixtures();p['repository']='foreign/repo'
        with self.assertRaises(target.EvidenceError):
            self.execute(p,b,d,s)
        p,b,d,s=fixtures();p['roles']['meta']='f'*32
        with self.assertRaises(target.EvidenceError):
            self.execute(p,b,d,s)

    def test_expired_holder_stays_occupied_without_takeover(self):
        p,b,d,s=fixtures()
        from test_system_github_evidence import EvidenceTests
        def holder(state):
            state['holder']={'kind':'META','owner_id':IDS['meta'],'task_id':p['roles']['meta'],'epoch':7,
                              'acquired_at':'2026-10-27T11:00:00Z','expires_at':'2026-10-27T11:30:00Z'}
        # Reuse the accepted fixture's immutable blob construction, never its verdict.
        p0,pins,d0=EvidenceTests().coordinator_fixture(holder)
        b['coordinator_blob_sha']=pins['coordinator_blob_sha']
        d=d0
        result=self.execute(p,b,d,s)
        self.assertIsNotNone(result['coordinator']['holder'])
        self.assertEqual(result['coordinator']['holder_service_binding'],'MATCHED_CURRENT_SERVICE_RUN')
        self.assertFalse(result['authority']['takeover_allowed'])
        self.assertFalse(result['triage']['takeover_allowed'])

    def test_clock_reversal_or_collection_expiry_rejected(self):
        p,b,d,s=fixtures();provider=Provider(p,d,s)
        for after in ('2026-10-27T12:29:59Z','2026-10-27T12:32:01Z'):
            ticks=iter([NOW]+[after]*80)
            with self.subTest(after=after),self.assertRaises(target.EvidenceError):
                target.observe([p],b,provider.get,provider.peek,lambda:next(ticks))


if __name__ == '__main__':
    unittest.main()
