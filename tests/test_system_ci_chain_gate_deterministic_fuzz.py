"""Deterministic untrusted snapshot regression for PR154; fail-closed and no authority."""
from __future__ import annotations
import copy
import json
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_ci_chain_gate import assess_with_payload

REPO = 'kk051780/toy-wars-factory'
HEAD = 'e220e85df6519ad5ec163042aba8b78564f3622f'
WORKFLOW = 394718989
RUN = {'id': 41145842751, 'run_attempt': 1, 'event': 'pull_request',
       'workflow_id': WORKFLOW, 'name': 'Toy Wars bootstrap offline QA',
       'head_sha': HEAD, 'status': 'completed', 'conclusion': 'success',
       'repository': {'full_name': REPO}}
JOBS = [{'id': 124370626245, 'run_id': RUN['id'], 'run_attempt': 1,
         'head_sha': HEAD, 'name': 'compile_hold', 'status': 'completed', 'conclusion': 'success'},
        {'id': 124370626516, 'run_id': RUN['id'], 'run_attempt': 1,
         'head_sha': HEAD, 'name': 'offline', 'status': 'completed', 'conclusion': 'success'}]

class FuzzFailClosed(unittest.TestCase):
    def test_fixed_seed_5000_one_field_mutations_never_authorize(self):
        rng = random.Random(0x154_2026)
        invalid = [None, False, True, -1, 0, 1, 1.25, 'wat', '', [], {}, [1], {'data': True}]
        run_keys = list(RUN)
        job_keys = list(JOBS[0])
        for iteration in range(5000):
            packet = {'run': copy.deepcopy(RUN), 'jobs': copy.deepcopy(JOBS)}
            if rng.random() < 0.5:
                field = rng.choice(run_keys)
                val = copy.deepcopy(rng.choice(invalid))
                packet['run'][field] = val
                changed = ('run', field, val)
            else:
                index = rng.randrange(2)
                field = rng.choice(job_keys)
                val = copy.deepcopy(rng.choice(invalid))
                packet['jobs'][index][field] = val
                changed = ('job', field, val)
            payload = json.dumps(packet)
            verdict = assess_with_payload(REPO, HEAD, WORKFLOW, payload)
            with self.subTest(case=iteration):
                self.assertIsInstance(verdict, dict)
                self.assertFalse(verdict['write_allowed'])
                self.assertFalse(verdict['dispatch_allowed'])
                self.assertFalse(verdict['merge_allowed'])
                self.assertFalse(verdict['publish_allowed'])
                self.assertFalse(verdict['provider_attested'])
                self.assertFalse(verdict['independent_review_complete'])
                benign_positive_id = (changed[2] == 1 and type(changed[2]) is int
                                      and changed[:2] in (('run', 'run_attempt'),
                                                         ('job', 'run_attempt'),
                                                         ('job', 'id')))
                if not benign_positive_id:
                    self.assertNotEqual(verdict['verdict'], 'QA_CANDIDATE_GREEN')

if __name__ == '__main__':
    unittest.main()
