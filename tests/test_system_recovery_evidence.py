"""Recovery evidence must describe a finish after the current fenced claim."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import (acquire, initial_state, recover_finished_worker,
                            release)

RUN = "00000000-0000-0000-0000-000000000123"
CLAIM = "2026-10-25T07:00:00Z"
NOW = "2026-10-25T07:01:00Z"


class RecoveryEvidenceTests(unittest.TestCase):
    def claim(self, kind="WORKER", state=None, at=CLAIM):
        state = copy.deepcopy(state) if state is not None else initial_state()
        task = state["task_id"] if kind == "WORKER" else "registered-" + kind
        state["authorized_tasks"][kind] = task
        branch = ("main" if kind == "REVIEWER" else
                  ("auto/twf-system-review-" if kind == "META" else
                   "auto/twf-game-repair-") + RUN)
        return acquire(state, kind, RUN, at, actor_task_id=task,
                       work_branch=branch)["state"]

    def proof(self, completed_at, status="completed"):
        return {"id": RUN, "recorded_status": status,
                "started_at": CLAIM, "completed_at": completed_at}

    def test_pre_claim_completion_never_releases_any_registered_role(self):
        for kind in ("WORKER", "META", "REVIEWER"):
            for status in ("completed", "failed", "no_update"):
                with self.subTest(kind=kind, status=status):
                    state = self.claim(kind)
                    before = copy.deepcopy(state)
                    with self.assertRaises(ValueError):
                        recover_finished_worker(
                            state, self.proof("2026-10-25T06:59:59Z", status), NOW)
                    self.assertEqual(state, before)

    def test_finished_old_generation_cannot_release_reacquired_same_run(self):
        first = self.claim()
        old_proof = self.proof("2026-10-25T07:00:10Z")
        idle = release(first, "WORKER", RUN, first["epoch"],
                       "2026-10-25T07:00:11Z")
        current = self.claim(state=idle, at="2026-10-25T07:00:20Z")
        self.assertGreater(current["epoch"], first["epoch"])
        with self.assertRaises(ValueError):
            recover_finished_worker(current, old_proof, NOW)
        self.assertEqual(current["holder"]["epoch"], current["epoch"])

    def test_post_claim_completion_recovers_without_changing_input(self):
        for kind in ("WORKER", "META", "REVIEWER"):
            for status in ("completed", "failed", "no_update"):
                with self.subTest(kind=kind, status=status):
                    state = self.claim(kind)
                    before = copy.deepcopy(state)
                    recovered = recover_finished_worker(
                        state, self.proof("2026-10-25T07:00:30Z", status), NOW)
                    self.assertEqual(state, before)
                    self.assertIsNone(recovered["holder"])
                    self.assertEqual(recovered["last_completed"]["epoch"],
                                     state["epoch"])
                    self.assertTrue(recovered["last_completed"]
                                    ["recovered_from_service_evidence"])

    def test_claim_boundary_compares_instants_across_timezones(self):
        state = self.claim()
        with self.assertRaises(ValueError):
            recover_finished_worker(
                state, self.proof("2026-10-25T15:59:59.999999+09:00"), NOW)
        for timestamp in ("2026-10-25T16:00:00+09:00", CLAIM, NOW):
            with self.subTest(timestamp=timestamp):
                self.assertIsNone(recover_finished_worker(
                    state, self.proof(timestamp), NOW)["holder"])

    def test_expiry_alone_does_not_make_old_completion_valid(self):
        state = self.claim()
        with self.assertRaises(ValueError):
            recover_finished_worker(
                state, self.proof("2026-10-25T06:59:59Z"),
                "2026-10-25T07:31:00Z")

    def test_unfinished_future_or_wrong_owner_proofs_stay_rejected(self):
        state = self.claim()
        valid = self.proof("2026-10-25T07:00:30Z")
        for changes in ({"completed_at": None},
                        {"completed_at": "2026-10-25T07:01:00.000001Z"},
                        {"recorded_status": "in_progress"},
                        {"id": "00000000-0000-0000-0000-000000000456"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                recover_finished_worker(state, {**valid, **changes}, NOW)


if __name__ == "__main__":
    unittest.main()
