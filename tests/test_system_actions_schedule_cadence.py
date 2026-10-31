"""Adversarial offline only. Passing these tests is not GitHub service attestation."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

FILE=Path(__file__).resolve().parents[1]/'tools'/'system_actions_schedule_cadence.py'
spec=importlib.util.spec_from_file_location('actions_cadence',FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
REPO='kk051780/toy-wars-factory'
H='.github/workflows/handoff-sync.yml'
W='.github/workflows/loop-watchdog.yml'
T='2026-10-24T06:00:00Z'
B='2026-10-24T08:00:00Z'
OBS='2026-10-24T08:05:00Z'

def policy():
    return {'repository':REPO,'workflows':[
        {'path':H,'minute_offsets':[13,33,53],'branch':'main'},
        {'path':W,'minute_offsets':[7,27,47],'branch':'main'}]}

def run(path, rid, at, *, conclusion='success'):
    return {'id':rid,'event':'schedule','path':path,'head_branch':'main',
            'head_sha':'a'*40,'run_attempt':1,'created_at':at,
            'status':'completed' if conclusion is not None else 'in_progress',
            'conclusion':conclusion}

def frame():
    runs=[run(H,10,'2026-10-24T06:15:00Z'),
          run(W,11,'2026-10-24T06:11:00Z'),
          run(H,12,'2026-10-24T07:54:00Z',conclusion='failure'),
          run(W,13,'2026-10-24T07:52:00Z')]
    return {'schema':1,'repository':REPO,'window_start':T,'window_end':B,
            'observed_at':OBS,'total_count':len(runs),'runs':runs}

class CadenceTests(unittest.TestCase):
    def test_two_independent_crons_and_real_gap(self):
        out=m.analyze(frame(),policy())
        self.assertEqual(out['workflows'][H]['configured_cron_slots'],6)
        self.assertEqual(out['workflows'][W]['configured_cron_slots'],6)
        self.assertEqual(out['workflows'][H]['observed_schedule_runs'],2)
        self.assertEqual(out['workflows'][H]['observed_over_nominal_slots'],.3333)
        self.assertEqual(out['workflows'][H]['longest_observed_interrun_gap_minutes'],99)
        self.assertEqual(out['workflows'][W]['longest_observed_interrun_gap_minutes'],101)
        self.assertEqual(out['workflows'][H]['outcomes']['completed_non_success'],1)
        self.assertEqual(out['workflows'][H]['status'],'FEWER_RUNS_THAN_NOMINAL_SLOTS')
    def test_never_claim_automated_coding_or_proven_github_drop_rate(self):
        out=m.analyze(frame(),policy())
        self.assertIsNone(out['drop_rate'])
        self.assertEqual(out['drop_cause'],'UNKNOWN')
        self.assertEqual(out['source_verification'],'UNTRUSTED_INPUT_ONLY')
        self.assertTrue(out['authority'])
        self.assertTrue(all(v is False for v in out['authority'].values()))
    def test_exact_half_open_count_boundary(self):
        f=frame();f['runs']=[run(H,1,'2026-10-24T06:00:00Z'),
                               run(H,2,'2026-10-24T08:00:00Z')];f['total_count']=2
        self.assertEqual(m.analyze(f,policy())['workflows'][H]['observed_schedule_runs'],1)
    def test_outside_window_allowed_but_not_counted(self):
        f=frame();f['runs'].append(run(H,99,'2026-10-24T05:54:00Z'));f['total_count']+=1
        self.assertEqual(m.analyze(f,policy())['workflows'][H]['observed_schedule_runs'],2)
    def test_data_order_does_not_matter(self):
        f=frame();f['runs'].reverse()
        self.assertEqual(m.analyze(frame(),policy()),m.analyze(f,policy()))
    def test_zero_runs_not_zero_issues_claim(self):
        f=frame();f['runs']=[];f['total_count']=0
        out=m.analyze(f,policy())
        self.assertEqual(out['workflows'][H]['observed_schedule_runs'],0)
        self.assertEqual(out['workflows'][H]['status'],'FEWER_RUNS_THAN_NOMINAL_SLOTS')
        self.assertIsNone(out['workflows'][H]['longest_observed_interrun_gap_minutes'])
    def test_insufficient_window_status(self):
        f=frame();f['window_end']='2026-10-24T07:00:00Z'
        self.assertEqual(m.analyze(f,policy())['workflows'][H]['status'],'INSUFFICIENT_WINDOW')
    def test_partial_pages_rejected(self):
        f=frame();f['runs'].pop()
        with self.assertRaisesRegex(m.CadenceError,'INCOMPLETE_RESULT_PAGES'):m.analyze(f,policy())
    def test_duplicate_run_id_rejected(self):
        f=frame();f['runs'][1]['id']=10
        with self.assertRaisesRegex(m.CadenceError,'INVALID_RUN_ID'):m.analyze(f,policy())
    def test_provider_comparison_not_authenticated_by_matching_keys(self):
        out=m.analyze(frame(),policy());self.assertFalse(out['authority']['provider_authenticated'])
    def test_reject_foreign_repository(self):
        f=frame();f['repository']='untrusted/game'
        with self.assertRaisesRegex(m.CadenceError,'WRONG_REPOSITORY'):m.analyze(f,policy())
    def test_reject_duplicate_workflow(self):
        b=policy();b['workflows'].append(deepcopy(b['workflows'][0]))
        with self.assertRaisesRegex(m.CadenceError,'INVALID_WORKFLOW'):m.analyze(frame(),b)
    def test_reject_unexpected_workflow(self):
        f=frame();f['runs'][0]['path']='.github/workflows/unknown.yml'
        with self.assertRaisesRegex(m.CadenceError,'FOREIGN_OR_INVALID_RUN'):m.analyze(f,policy())
    def test_reject_non_schedule_events(self):
        f=frame();f['runs'][0]['event']='push'
        with self.assertRaisesRegex(m.CadenceError,'FOREIGN_OR_INVALID_RUN'):m.analyze(f,policy())
    def test_reject_different_head_branch(self):
        f=frame();f['runs'][0]['head_branch']='feature/attacker'
        with self.assertRaisesRegex(m.CadenceError,'FOREIGN_OR_INVALID_RUN'):m.analyze(f,policy())
    def test_reject_nonsha(self):
        f=frame();f['runs'][0]['head_sha']='not_sha'
        with self.assertRaisesRegex(m.CadenceError,'FOREIGN_OR_INVALID_RUN'):m.analyze(f,policy())
    def test_reject_wrong_attempt(self):
        f=frame();f['runs'][0]['run_attempt']=0
        with self.assertRaisesRegex(m.CadenceError,'INVALID_ATTEMPT'):m.analyze(f,policy())
    def test_reject_inconsistent_terminal_status(self):
        f=frame();f['runs'][0]['status']='in_progress'
        with self.assertRaisesRegex(m.CadenceError,'INCONSISTENT_TERMINAL_STATE'):m.analyze(f,policy())
    def test_in_progress_not_misreported_success(self):
        f=frame();f['runs'][0]['status']='in_progress';f['runs'][0]['conclusion']=None
        self.assertEqual(m.analyze(f,policy())['workflows'][H]['outcomes']['nonterminal'],1)
    def test_reject_future_event(self):
        f=frame();f['runs'][0]['created_at']='2026-10-25T00:00:00Z'
        with self.assertRaisesRegex(m.CadenceError,'FUTURE_RUN'):m.analyze(f,policy())
    def test_reject_naive_time(self):
        f=frame();f['window_end']='2026-10-24T08:00:00'
        with self.assertRaisesRegex(m.CadenceError,'INVALID_TIME'):m.analyze(f,policy())
    def test_reject_oversize_window(self):
        f=frame();f['window_start']='2026-09-01T00:00:00Z'
        with self.assertRaisesRegex(m.CadenceError,'INVALID_WINDOW'):m.analyze(f,policy())
    def test_reject_boolean_schema_and_integer_ids(self):
        for key in ('schema','total_count'):
            f=frame();f[key]=True
            with self.subTest(key=key),self.assertRaises(m.CadenceError):m.analyze(f,policy())
        f=frame();f['runs'][0]['id']=True
        with self.assertRaisesRegex(m.CadenceError,'INVALID_RUN_ID'):m.analyze(f,policy())
    def test_invalid_minutes_rejected(self):
        for bad in ([13,13,53],[53,13],[13,60],[-1],[],[True,13]):
            b=policy();b['workflows'][0]['minute_offsets']=bad
            with self.subTest(bad=bad),self.assertRaisesRegex(m.CadenceError,'INVALID_CRON'):m.analyze(frame(),b)
    def test_malformed_binding_fails(self):
        b=policy();b.pop('repository')
        with self.assertRaisesRegex(m.CadenceError,'INVALID_BINDING'):m.analyze(frame(),b)
    def test_extra_authority_field_rejected(self):
        f=frame();f['write_allowed']=True
        with self.assertRaisesRegex(m.CadenceError,'INVALID_FRAME'):m.analyze(f,policy())
    def test_original_input_not_mutated(self):
        f=frame();b=policy();s=json.dumps([f,b],sort_keys=True)
        m.analyze(f,b)
        self.assertEqual(s,json.dumps([f,b],sort_keys=True))
    def test_json_rejects_duplicate_keys_and_nonfinite(self):
        with self.assertRaisesRegex(m.CadenceError,'DUPLICATE_JSON_KEY'):
            json.loads('{"a":1,"a":2}',object_pairs_hook=m._no_duplicates)
        with self.assertRaisesRegex(m.CadenceError,'NONFINITE_JSON'):
            json.loads('{"x":NaN}',parse_constant=m._no_nonfinite)
    def test_cli_real_files_no_network(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'f.json';b=root/'b.json'
            f.write_text(json.dumps(frame()));b.write_text(json.dumps(policy()))
            c=subprocess.run([sys.executable,str(FILE),str(f),str(b)],capture_output=True,text=True)
            self.assertEqual(c.returncode,0,c.stderr)
            self.assertEqual(json.loads(c.stdout)['workflows'][W]['observed_schedule_runs'],2)
    def test_cli_rejects_duplicate_with_no_prompt_echo(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'f.json';b=root/'b.json'
            f.write_text('{"schema":1,"schema":1,"secret":"PRIVATE_STRING"}')
            b.write_text(json.dumps(policy()))
            c=subprocess.run([sys.executable,str(FILE),str(f),str(b)],capture_output=True,text=True)
            self.assertEqual(c.returncode,2)
            self.assertEqual(json.loads(c.stdout)['code'],'DUPLICATE_JSON_KEY')
            self.assertNotIn('PRIVATE_STRING',c.stdout)
    def test_164_hour_known_nominal_slots(self):
        start=m.instant('2026-10-24T06:00:00Z');end=m.instant('2026-10-31T02:00:00Z')
        self.assertEqual(m.expected_slots(start,end,(13,33,53)),492)
        self.assertEqual(m.expected_slots(start,end,(7,27,47)),492)
if __name__=='__main__':unittest.main()