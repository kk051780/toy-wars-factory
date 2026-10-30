"""Adversarial read-only throughput metric tests; not a provider attestation."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'tools/system_throughput_metrics.py'
m = None
if MODULE.is_file():
    spec = importlib.util.spec_from_file_location('throughput', MODULE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

W, M, R = ('1'*32,
           '2'*32,
           '3'*32)
w, meta = ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
           'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')

def fixture():
    result = {'schema':1, 'project_id':'toy_wars', 'repository':'sample/one',
            'main_sha':'a'*40, 'observed_at':'2026-10-30T00:15:00Z',
            'roles':{'WORKER':W,'META':M,'REVIEWER':R},
            'runs':[
                {'role':'META','task_id':M,'run_id':meta,
                 'scheduled_for':'2026-10-29T23:45:00Z',
                 'started_at':'2026-10-29T23:43:30Z',
                 'completed_at':'2026-10-30T00:06:00Z',
                 'recorded_status':'completed','current_result_run_id':meta},
                {'role':'WORKER','task_id':W,'run_id':w,
                 'scheduled_for':'2026-10-30T00:05:00Z',
                 'started_at':'2026-10-30T00:03:50Z',
                 'completed_at':'2026-10-30T00:05:20Z',
                 'recorded_status':'completed','current_result_run_id':meta}
            ],
            'coordinator':[{'role':'META','owner_run_id':meta,
                            'acquired_at':'2026-10-29T23:51:00Z',
                            'released_at':'2026-10-30T00:04:52Z'}]}

    for row in result['runs']:
        row['current_result_created_at'] = '2026-10-30T00:05:19Z'
    for row in result['coordinator']:
        row.update(epoch=1, claim_ref='c'*40, release_ref='d'*40)
    return result

def binding():
    return {key:copy.deepcopy(fixture()[key]) for key in ('project_id','repository','main_sha','roles')}

def build(frame, trusted=None):
    return m.build(frame, binding=binding() if trusted is None else trusted)

class ThroughputTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, "accepted main has no throughput module")

    def test_calculation_without_source_proof(self):
        v = build(fixture())
        self.assertEqual(v['roles']['META']['elapsed_seconds_sum'],1350)
        self.assertIsNone(v['roles']['META']['schedule_offset_p50_seconds'])
        self.assertEqual(v['runs'][0]['schedule_jitter_seconds'],-90)
        self.assertEqual(v['roles']['META']['lease_seconds_reported'],832)
        self.assertEqual(v['roles']['WORKER']['fresh_result_runs'],0)
        self.assertEqual(v['roles']['WORKER']['elapsed_seconds_sum'],90)
        self.assertEqual(v['roles']['WORKER']['productive_source_changes'],'NOT_VERIFIED')
        self.assertTrue(all(flag is False for flag in v['authority'].values()))
    def test_two_repositories_are_independent(self):
        f = fixture(); f['repository']='sample/two'; f['project_id']='other_game'; f['main_sha']='b'*40
        f['roles']={'WORKER':'4'*32,'META':'5'*32,'REVIEWER':'6'*32}
        for row in f['runs']: row['task_id']=f['roles'][row['role']]
        trusted={key:copy.deepcopy(f[key]) for key in ('project_id','repository','main_sha','roles')}
        self.assertEqual(build(f,trusted)['repository'],'sample/two')
    def test_stale_latest_result_does_not_count(self):
        self.assertEqual(build(fixture())['roles']['WORKER']['fresh_result_runs'],0)
    def test_same_run_report_counts_only_when_terminal(self):
        f=fixture(); f['runs'][1]['current_result_run_id']=w
        self.assertEqual(build(f)['roles']['WORKER']['fresh_result_runs'],1)
        f['runs'][1]['recorded_status']='in_progress'; f['runs'][1]['completed_at']=None
        self.assertEqual(build(f)['roles']['WORKER']['fresh_result_runs'],0)
    def test_32_hex_real_task_ids(self):
        f=fixture(); f['roles']['WORKER']='6adbf0d6a7d881918ce181dff2468867'
        f['runs'][1]['task_id']=f['roles']['WORKER']
        trusted=binding(); trusted['roles']['WORKER']=f['roles']['WORKER']
        self.assertEqual(build(f,trusted)['roles']['WORKER']['observed_runs'], 1)
    def test_foreign_lease_overlaps_worker_by_62_seconds(self):
        v = build(fixture())['roles']
        self.assertEqual(v['WORKER']['foreign_lease_overlap_seconds_reported'], 62)
        self.assertEqual(v['WORKER']['foreign_lease_overlap_terminal_runs'], 1)
        self.assertEqual(v['WORKER']['wait_reason'], 'NOT_VERIFIED')
        self.assertEqual(v['META']['foreign_lease_overlap_seconds_reported'], 0)

    def test_missing_release_never_implies_zero_foreign_lease_risk(self):
        f = fixture()
        f['coordinator'][0]['released_at'] = None
        f['coordinator'][0]['release_ref'] = None
        v = build(f)['roles']['WORKER']
        self.assertEqual(v['foreign_lease_overlap_seconds_reported'], 0)
        self.assertEqual(v['foreign_lease_incomplete_terminal_runs'], 1)
        self.assertEqual(v['wait_reason'], 'NOT_VERIFIED')

    def test_foreign_lease_after_finished_run_not_counted(self):
        f = fixture()
        f['runs'][1]['started_at'] = '2026-10-30T00:05:00Z'
        f['runs'][1]['completed_at'] = '2026-10-30T00:06:00Z'
        v = build(f)['roles']['WORKER']
        self.assertEqual(v['foreign_lease_overlap_seconds_reported'], 0)
        self.assertEqual(v['foreign_lease_overlap_terminal_runs'], 0)

    def test_in_progress_run_does_not_claim_completed_overlap(self):
        f = fixture()
        f['runs'][1]['recorded_status'] = 'in_progress'
        f['runs'][1]['completed_at'] = None
        v = build(f)['roles']['WORKER']
        self.assertEqual(v['foreign_lease_overlap_terminal_runs'], 0)
        self.assertEqual(v['foreign_lease_overlap_seconds_reported'], 0)
        self.assertEqual(v['in_progress'], 1)

    def test_interval_union_never_double_counts(self):
        start = m.instant('2026-10-30T00:00:00Z')
        end = m.instant('2026-10-30T00:01:00Z')
        intervals = [(m.instant('2026-10-30T00:00:05Z'), m.instant('2026-10-30T00:00:40Z')),
                     (m.instant('2026-10-30T00:00:20Z'), m.instant('2026-10-30T00:00:50Z'))]
        self.assertEqual(m.overlap_union_seconds(start, end, intervals), 45)

    def test_lease_acquired_after_owner_terminal_rejected(self):
        f=fixture()
        f['coordinator'][0]['acquired_at']='2026-10-30T00:07:00Z'
        f['coordinator'][0]['released_at']='2026-10-30T00:07:30Z'
        with self.assertRaises(m.MetricsError): build(f)

    def test_lease_released_after_owner_terminal_rejected(self):
        f=fixture()
        f['coordinator'][0]['released_at']='2026-10-30T00:07:30Z'
        with self.assertRaises(m.MetricsError): build(f)

    def test_two_foreign_owners_cannot_hold_single_lock_at_once(self):
        f=fixture()
        f['coordinator'].append({'role':'WORKER','owner_run_id':w,
            'acquired_at':'2026-10-30T00:03:55Z',
            'released_at':'2026-10-30T00:04:10Z','epoch':2,'claim_ref':'e'*40,'release_ref':'f'*40})
        with self.assertRaises(m.MetricsError): build(f)

    def test_no_update_cannot_claim_fresh_success_result(self):
        f=fixture()
        f['runs'][1]['recorded_status']='no_update'
        f['runs'][1]['current_result_run_id']=w
        self.assertEqual(build(f)['roles']['WORKER']['fresh_result_runs'],0)

    def test_actual_epoch262_pre_start_claim_rejected_even_with_matching_run(self):
        f = fixture()
        f['observed_at'] = '2026-10-30T01:10:00Z'
        f['roles']['META'] = '6add445e4138819197d9cf2b1a02534d'
        f['runs'] = [{
            'role': 'META', 'task_id': f['roles']['META'],
            'run_id': '6c5df803-672c-8328-b0c9-07b9b96ee6bf',
            'scheduled_for': '2026-10-30T00:45:00Z',
            'started_at': '2026-10-30T01:00:29.636938Z',
            'completed_at': '2026-10-30T01:05:12.021943Z',
            'recorded_status': 'completed',
            'current_result_run_id': '6c5df803-672c-8328-b0c9-07b9b96ee6bf',
            'current_result_created_at':'2026-10-30T01:05:11Z'}]
        f['coordinator'] = [{
            'role': 'META', 'owner_run_id': f['runs'][0]['run_id'],
            'acquired_at': '2026-10-30T00:49:24Z',
            'released_at': None,'epoch':262,'claim_ref':'c'*40,'release_ref':None}]
        # Genuine provider and GitHub observations disagree on claim chronology.
        # The parser must not infer an authentic legal lock from matching IDs.
        with self.assertRaises(m.MetricsError): build(f, {key:copy.deepcopy(f[key]) for key in ('project_id','repository','main_sha','roles')})

    def test_wrong_task_role(self):
        f=fixture(); f['runs'][0]['task_id']=W
        with self.assertRaises(m.MetricsError): build(f)
    def test_duplicate_run(self):
        f=fixture(); f['runs'].append(copy.deepcopy(f['runs'][0]))
        with self.assertRaises(m.MetricsError): build(f)
    def test_wrong_epoch_not_in_schema(self):
        f=fixture(); f['coordinator'][0]['epoch']=True
        with self.assertRaises(m.MetricsError): build(f)
    def test_orphan_lease(self):
        f=fixture(); f['coordinator'][0]['owner_run_id']=w
        with self.assertRaises(m.MetricsError): build(f)
    def test_duplicate_lease(self):
        f=fixture(); f['coordinator'].append(copy.deepcopy(f['coordinator'][0]))
        with self.assertRaises(m.MetricsError): build(f)
    def test_unreleased_not_inferred(self):
        f=fixture(); f['coordinator'][0]['released_at']=None; f['coordinator'][0]['release_ref']=None
        g=build(f)['roles']['META']
        self.assertEqual(g['lease_unreleased_unknown_count'],1)
        self.assertEqual(g['lease_seconds_reported'],0)
    def test_invalid_terminal_clock(self):
        f=fixture(); f['runs'][0]['completed_at']='2026-10-29T23:42:00Z'
        with self.assertRaises(m.MetricsError): build(f)
    def test_wrong_timezone(self):
        f=fixture(); f['runs'][0]['started_at']='2026-10-29T23:43:30'
        with self.assertRaises(m.MetricsError): build(f)
    def test_future_run(self):
        f=fixture(); f['runs'][0]['scheduled_for']='2026-10-30T00:30:00Z'
        with self.assertRaises(m.MetricsError): build(f)
    def test_running_with_completion_forbidden(self):
        f=fixture(); f['runs'][0]['recorded_status']='in_progress'
        with self.assertRaises(m.MetricsError): build(f)
    def test_noncanonical_uuid(self):
        f=fixture(); f['runs'][0]['run_id']=meta.upper()
        with self.assertRaises(m.MetricsError): build(f)
    def test_empty_runs(self):
        f=fixture(); f['runs']=[]; f['coordinator']=[]
        self.assertEqual(build(f)['roles']['META']['observed_runs'],0)
        self.assertIsNone(build(f)['roles']['META']['elapsed_p90_seconds'])
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(m.MetricsError):
            import json
            json.loads('{"schema": 1, "schema": 2}', object_pairs_hook=m.unique_pairs)
    def test_nonfinite_json_rejected(self):
        import json
        with self.assertRaises(m.MetricsError):
            json.loads('{"schema": NaN}', parse_constant=m.reject_constant)
    def test_wrong_frame_unknown_protected(self):
        f=fixture(); f['schedules']={}
        with self.assertRaises(m.MetricsError): build(f)

    def test_foreign_project_binding_rejected(self):
        f=fixture(); f['project_id']='foreign_game'
        with self.assertRaises(m.MetricsError): build(f)
    def test_foreign_repository_binding_rejected(self):
        f=fixture(); f['repository']='foreign/repository'
        with self.assertRaises(m.MetricsError): build(f)
    def test_foreign_main_binding_rejected(self):
        f=fixture(); f['main_sha']='b'*40
        with self.assertRaises(m.MetricsError): build(f)
    def test_task_uuid_is_not_registered_task_hex(self):
        f=fixture(); f['roles']['META']=meta; f['runs'][0]['task_id']=meta
        with self.assertRaises(m.MetricsError): build(f, {key:copy.deepcopy(f[key]) for key in ('project_id','repository','main_sha','roles')})
    def test_same_uuid_in_different_roles_is_duplicate(self):
        f=fixture(); f['runs'][1]['run_id']=meta
        with self.assertRaises(m.MetricsError): build(f)
    def test_same_uuid_old_attempt_result_is_stale(self):
        f=fixture(); f['runs'][1]['current_result_run_id']=w
        f['runs'][1]['current_result_created_at']='2026-10-30T00:03:00Z'
        result=build(f)
        self.assertEqual(result['roles']['WORKER']['fresh_result_runs'],0)
        self.assertEqual(result['runs'][1]['latest_result_binding'],'STALE_SAME_RUN_RESULT')
    def test_missing_release_explicitly_unknown_not_zero(self):
        f=fixture(); f['coordinator'][0]['released_at']=None; f['coordinator'][0]['release_ref']=None
        self.assertEqual(build(f)['roles']['WORKER']['foreign_lease_overlap_seconds'],'UNKNOWN')
    def test_in_progress_terminal_elapsed_unknown(self):
        f=fixture(); f['runs'][1]['recorded_status']='in_progress'; f['runs'][1]['completed_at']=None
        self.assertEqual(build(f)['runs'][1]['terminal_elapsed_seconds'],'UNKNOWN')
    def test_percentiles_never_claim_unforced_proof(self):
        role=build(fixture())['roles']['META']
        self.assertIsNone(role['elapsed_p50_seconds']); self.assertIsNone(role['elapsed_p90_seconds'])
    def test_strict_epoch_types_and_release_anchor(self):
        for epoch in [True,1.0,0,-1]:
            f=fixture(); f['coordinator'][0]['epoch']=epoch
            with self.assertRaises(m.MetricsError): build(f)
        f=fixture(); f['coordinator'][0]['release_ref']=None
        with self.assertRaises(m.MetricsError): build(f)
    def test_frame_not_mutated_and_no_auth_upgrade(self):
        f=fixture(); before=copy.deepcopy(f); v=build(f)
        self.assertEqual(f,before); self.assertEqual(v['verification'],'NOT_VERIFIED')
        self.assertEqual(set(v['authority']),{'write_allowed','start_now_allowed','takeover_allowed','dispatch_allowed','merge_allowed','publish_allowed','external_spend_allowed'})
        self.assertTrue(all(x is False for x in v['authority'].values()))
    def test_non_string_task_rejected_with_safe_error(self):
        f=fixture(); f['roles']['META']=[]
        with self.assertRaises(m.MetricsError): build(f)

if __name__=='__main__': unittest.main()
