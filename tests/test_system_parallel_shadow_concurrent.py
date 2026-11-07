"""Real threaded contention of two logical CAS clients; fake-host only.

A pass DOES NOT prove two separate authenticated GPT writers on GitHub.
"""
import copy
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_parallel_shadow_leases import claim, release, apply_once, KEY

REPO = "kk051780/toy-wars-factory"
MAIN = "a"*40
NOW = "2026-11-08T00:00:00Z"
CURRENT = "2026-11-08T00:01:00Z"
END = "2026-11-08T00:20:00Z"
A = ("11111111-1111-4111-8111-111111111111",
     "22222222-2222-4222-8222-222222222222",
     "33333333-3333-4333-8333-333333333333")
B = ("44444444-4444-4444-8444-444444444444",
     "55555555-5555-4555-8555-555555555555",
     "66666666-6666-4666-8666-666666666666")


def snapshot():
    return {"repository": REPO, "main_sha": MAIN, "ref_sha": "b"*40,
            "state": {"schema": 1, "epoch": 20, "holder": None,
                      "unrelated_policy": "PRESERVE"}}


def intent(work, path, identity):
    return {
        "scope": {"project_id": "toy-wars-factory", "repository": REPO,
                  "work_id": work, "branch": "controller/" + work,
                  "base_sha": MAIN, "write_paths": [path], "read_paths": [],
                  "generated_paths": [], "shared_resources": [], "status": "ACTIVE"},
        "owner_id": identity[0], "run_id": identity[1],
        "nonce": identity[2], "expires_at": END,
    }


def ownership(value):
    return {"work_id": value["scope"]["work_id"],
            "owner_id": value["owner_id"], "run_id": value["run_id"],
            "nonce": value["nonce"]}


class RacingFakeHost:
    def __init__(self, initial):
        self.value = copy.deepcopy(initial)
        self.mu = threading.Lock()
        self.barrier = None
        self.calls = 0

    def read(self):
        with self.mu:
            return copy.deepcopy(self.value)

    def cas(self, expected, next_state):
        barrier = self.barrier
        if barrier:
            barrier.wait(timeout=4)
        with self.mu:
            self.calls += 1
            if self.value["ref_sha"] != expected:
                return None
            ref = hashlib.sha1(json.dumps(next_state, sort_keys=True).encode()).hexdigest()
            self.value["ref_sha"] = ref
            self.value["state"] = copy.deepcopy(next_state)
            return ref

    def attempt(self, base, proposal):
        return apply_once(base, proposal, read=self.read, cas=self.cas,
                          clock=lambda: CURRENT, requested_at=NOW)

    def race(self, base, left, right):
        self.barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.attempt, base, left),
                       pool.submit(self.attempt, base, right)]
            results = [f.result(timeout=7) for f in futures]
        self.barrier = None
        return results


class GenuineThreadInterleavingTests(unittest.TestCase):
    def setUp(self):
        self.initial = snapshot()
        self.left = intent("alpha-work", "tools/alpha.py", A)
        self.right = intent("bravo-work", "tests/bravo.py", B)

    def proposals(self, base):
        a = claim(base, self.left, NOW)
        b = claim(base, self.right, NOW)
        self.assertEqual(a["decision"], "SHADOW_CLAIM_CAS_PROPOSAL")
        self.assertEqual(b["decision"], "SHADOW_CLAIM_CAS_PROPOSAL")
        return a, b

    def test_actual_threaded_cas_interleaving_has_one_winner(self):
        host = RacingFakeHost(self.initial)
        results = host.race(self.initial, *self.proposals(self.initial))
        statuses = sorted(item["status"] for item in results)
        self.assertEqual(statuses, sorted([
            "MOCK_CAS_READBACK_ONLY_NO_AUTHORITY",
            "WAIT_CAS_CONFLICT_OR_BAD_ACK",
        ]))
        self.assertEqual(host.calls, 2)
        self.assertEqual(host.read()["state"]["epoch"], 21)
        self.assertEqual(len(host.read()["state"][KEY]["entries"]), 1)
        self.assertEqual(host.read()["state"]["unrelated_policy"], "PRESERVE")
        for result in results:
            self.assertFalse(result["may_write"])
            self.assertFalse(result["github_authenticated"])
            self.assertFalse(result["parallel_real"])

    def test_losing_writer_rereads_then_claims_second_disjoint_scope(self):
        host = RacingFakeHost(self.initial)
        results = host.race(self.initial, *self.proposals(self.initial))
        self.assertEqual(sum(item["status"] ==
                             "MOCK_CAS_READBACK_ONLY_NO_AUTHORITY"
                             for item in results), 1)
        fresh = host.read()
        present = fresh["state"][KEY]["entries"][0]["scope"]["work_id"]
        loser = self.right if present == "alpha-work" else self.left
        proposed = claim(fresh, loser, NOW)
        self.assertEqual(proposed["decision"], "SHADOW_CLAIM_CAS_PROPOSAL")
        self.assertEqual(host.attempt(fresh, proposed)["status"],
                         "MOCK_CAS_READBACK_ONLY_NO_AUTHORITY")
        final = host.read()
        self.assertEqual(final["state"]["epoch"], 22)
        self.assertEqual(len(final["state"][KEY]["entries"]), 2)
        self.assertEqual({row["scope"]["work_id"] for row in
                          final["state"][KEY]["entries"]},
                         {"alpha-work", "bravo-work"})

    def test_conflicting_second_writer_blocked_after_race(self):
        host = RacingFakeHost(self.initial)
        self.right["scope"]["write_paths"] = ["tools/alpha.py"]
        host.race(self.initial, *self.proposals(self.initial))
        final = host.read()
        self.assertEqual(len(final["state"][KEY]["entries"]), 1)
        current = final["state"][KEY]["entries"][0]["scope"]["work_id"]
        other = self.left if current == "bravo-work" else self.right
        self.assertEqual(claim(final, other, NOW)["decision"], "WAIT_WRITE_COLLISION")
        self.assertEqual(host.calls, 2)

    def test_concurrent_own_releases_preserve_unrelated_writer(self):
        host = RacingFakeHost(self.initial)
        for req in (self.left, self.right):
            fresh = host.read()
            proposal = claim(fresh, req, NOW)
            self.assertEqual(proposal["decision"], "SHADOW_CLAIM_CAS_PROPOSAL")
            self.assertEqual(host.attempt(fresh, proposal)["status"],
                             "MOCK_CAS_READBACK_ONLY_NO_AUTHORITY")
        before = host.read()
        self.assertEqual(len(before["state"][KEY]["entries"]), 2)
        a = release(before, ownership(self.left), NOW)
        b = release(before, ownership(self.right), NOW)
        self.assertEqual(a["decision"], "SHADOW_RELEASE_CAS_PROPOSAL")
        self.assertEqual(b["decision"], "SHADOW_RELEASE_CAS_PROPOSAL")
        statuses = sorted(x["status"] for x in host.race(before, a, b))
        self.assertEqual(statuses, sorted([
            "MOCK_CAS_READBACK_ONLY_NO_AUTHORITY",
            "WAIT_CAS_CONFLICT_OR_BAD_ACK",
        ]))
        after = host.read()
        self.assertEqual(len(after["state"][KEY]["entries"]), 1)
        remaining = after["state"][KEY]["entries"][0]["scope"]["work_id"]
        self.assertIn(remaining, ("alpha-work", "bravo-work"))
        self.assertEqual(after["state"]["unrelated_policy"], "PRESERVE")


if __name__ == "__main__":
    unittest.main()
