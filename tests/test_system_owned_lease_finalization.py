"""Same-owner finalization; callbacks are synthetic host fixtures, not authentication."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import repair_control as control

RUN = "47b45262-2f40-8329-b6cd-3a4b4643b055"
OTHER = "28e539e9-f940-832c-a678-7d91076d4c39"
TASK = "6add6aaceb4c8191b1666fe15f97cd88"
REPO = "example/game"
NOW = "2026-10-30T00:00:00Z"
BEFORE = "2026-10-29T23:59:59Z"
EXPIRED = "2026-10-30T00:30:00Z"


class Host:
    def __init__(self):
        state = control.initial_state()
        state["authorized_tasks"]["REVIEWER"] = TASK
        self.state = control.acquire(state, "REVIEWER", RUN, NOW,
            actor_task_id=TASK, work_branch="main")["state"]
        self.state["foreign_history"] = [{"pr": 124, "status": "MERGED"}]
        self.ref = "a" * 40
        self.time = NOW
        self.run = {"task_id": TASK, "last_run": {"id": RUN,
            "recorded_status": "in_progress", "started_at": NOW, "completed_at": None}}
        self.calls = []
        self.writes = []
        self.read_hook = None
        self.cas_error = None
        self.read_error = False
        self.after_write = None

    def read(self, repository, branch, path):
        self.calls.append(("read", repository, branch, path))
        if self.read_error:
            raise OSError("host private failure; must not leak")
        snapshot = {"repository": REPO, "branch": control.CONTROL_BRANCH,
                    "ref": self.ref, "state": deepcopy(self.state)}
        if self.read_hook:
            self.read_hook(snapshot)
        return snapshot

    def peek(self, task):
        self.calls.append(("peek", task))
        return deepcopy(self.run)

    def clock(self):
        return self.time

    def cas(self, repository, branch, *, expected_sha, state, force):
        self.calls.append(("cas", repository, branch, expected_sha, force))
        self.writes.append(deepcopy(state))
        assert repository == REPO and branch == control.CONTROL_BRANCH
        assert force is False and expected_sha == self.ref
        if self.cas_error:
            raise self.cas_error
        self.ref = "b" * 40
        self.state = deepcopy(state)
        if self.after_write:
            self.after_write(self)
        return self.ref


class OwnedFinalizationTests(unittest.TestCase):
    def setUp(self):
        self.host = Host()

    def session(self, **changes):
        args = dict(repository=REPO, kind="REVIEWER", owner_id=RUN, epoch=1,
                    task_id=TASK, read=self.host.read, cas=self.host.cas,
                    peek=self.host.peek, clock=self.host.clock)
        args.update(changes)
        return control.owned_lease(**args)

    def rejected(self, mutate=lambda h: None, **changes):
        before = deepcopy(self.host.state)
        mutate(self.host)
        with self.assertRaises((ValueError, RuntimeError)):
            with self.session(**changes):
                self.fail("invalid entry executed body")
        self.assertFalse(self.host.writes)
        return before

    def test_release_rejects_clock_before_acquisition(self):
        with self.assertRaises(ValueError):
            control.release(self.host.state, "REVIEWER", RUN, 1, BEFORE)

    def test_release_rejects_boolean_generation(self):
        with self.assertRaises(ValueError):
            control.release(self.host.state, "REVIEWER", RUN, True, NOW)

    def test_release_rejects_float_generation(self):
        with self.assertRaises(ValueError):
            control.release(self.host.state, "REVIEWER", RUN, 1.0, NOW)

    def test_normal_finally_release_requires_readback_and_preserves_foreign_data(self):
        previous = deepcopy(self.host.state)
        with self.session() as receipt:
            self.assertEqual(receipt["status"], "OWNED")
            self.assertFalse(self.host.writes)
        self.assertEqual(receipt["status"], "RELEASED_READBACK")
        self.assertFalse(receipt["provider_verified"])
        self.assertEqual(receipt["provider_terminal"], "NOT_ATTESTED")
        self.assertEqual(receipt["to_ref"], self.host.ref)
        self.assertIsNone(self.host.state["holder"])
        self.assertEqual(self.host.state["last_completed"]["owner_id"], RUN)
        self.assertEqual(self.host.state["last_completed"]["epoch"], 1)
        self.assertIn("release_receipt", self.host.state["last_completed"])
        for key in previous:
            if key not in ("holder", "last_completed"):
                self.assertEqual(previous[key], self.host.state[key])
        self.assertEqual(len(self.host.writes), 1)
        self.assertEqual(self.host.calls[-1][0], "read")

    def test_body_error_still_releases_and_propagates_original(self):
        with self.assertRaisesRegex(LookupError, "body failed"):
            with self.session() as receipt:
                raise LookupError("body failed")
        self.assertEqual(receipt["status"], "RELEASED_READBACK")
        self.assertIsNone(self.host.state["holder"])

    def test_keyboard_interrupt_still_attempts_own_cleanup(self):
        with self.assertRaises(KeyboardInterrupt):
            with self.session() as receipt:
                raise KeyboardInterrupt()
        self.assertEqual(receipt["status"], "RELEASED_READBACK")

    def test_foreign_owner_rejected_before_body(self):
        self.rejected(owner_id=OTHER)

    def test_foreign_role_task_rejected_before_body(self):
        self.rejected(task_id=control.TASK_ID)

    def test_wrong_epoch_rejected_before_body(self):
        self.rejected(epoch=2)

    def test_foreign_repo_rejected_before_body(self):
        self.rejected(repository="other/game")

    def test_other_service_latest_cannot_impersonate_owner(self):
        self.rejected(lambda h: h.run["last_run"].update(id=OTHER))

    def test_completed_service_is_not_live_same_owner_cleanup(self):
        self.rejected(lambda h: h.run["last_run"].update(
            recorded_status="completed", completed_at=NOW))

    def test_missing_service_evidence_does_not_use_clock_expiry(self):
        self.rejected(lambda h: setattr(h, "run", {}))

    def test_service_started_after_claim_cannot_own_older_generation(self):
        self.rejected(lambda h: h.run["last_run"].update(
            started_at="2026-10-30T00:01:00Z"))

    def test_expired_owner_is_not_automatically_recovered(self):
        self.rejected(lambda h: setattr(h, "time", EXPIRED))

    def test_clock_reversal_rejected_without_write(self):
        with self.assertRaises(RuntimeError):
            with self.session() as receipt:
                self.host.time = BEFORE
        self.assertEqual(receipt["status"], "NOT_RELEASED")
        self.assertFalse(self.host.writes)

    def test_expiry_during_body_does_not_recover_without_terminal_history(self):
        with self.assertRaises(RuntimeError):
            with self.session() as receipt:
                self.host.time = EXPIRED
        self.assertEqual(receipt["status"], "NOT_RELEASED")
        self.assertFalse(self.host.writes)

    def test_new_holder_during_body_never_gets_released(self):
        with self.assertRaises(RuntimeError):
            with self.session():
                self.host.state["holder"]["owner_id"] = OTHER
        self.assertFalse(self.host.writes)
        self.assertEqual(self.host.state["holder"]["owner_id"], OTHER)

    def test_new_epoch_same_owner_during_body_never_gets_released(self):
        with self.assertRaises(RuntimeError):
            with self.session():
                self.host.state["epoch"] = self.host.state["holder"]["epoch"] = 2
        self.assertFalse(self.host.writes)

    def test_same_tuple_changed_holder_anchor_is_rejected(self):
        with self.assertRaises(RuntimeError):
            with self.session():
                self.host.state["holder"]["expires_at"] = "2026-10-30T00:29:00Z"
        self.assertFalse(self.host.writes)

    def test_double_release_is_rejected_without_second_cas(self):
        with self.session():
            pass
        with self.assertRaises(ValueError):
            with self.session():
                self.fail("second body")
        self.assertEqual(len(self.host.writes), 1)

    def test_finally_read_failure_does_not_mask_body_with_private_host_text(self):
        with self.assertRaises(RuntimeError) as caught:
            with self.session() as receipt:
                self.host.read_error = True
                raise LookupError("original body")
        self.assertEqual(receipt["status"], "NOT_RELEASED")
        self.assertNotIn("private", str(caught.exception))
        self.assertFalse(self.host.writes)

    def test_ref_race_between_cleanup_reads_prevents_cas(self):
        counter = []
        def race(snapshot):
            counter.append(1)
            snapshot["ref"] = ("c" if len(counter) % 2 else "d") * 40
        with self.assertRaises(RuntimeError):
            with self.session():
                self.host.read_hook = race
        self.assertFalse(self.host.writes)

    def test_cas_rejection_no_retry_no_success_receipt(self):
        with self.assertRaises(RuntimeError):
            with self.session() as receipt:
                self.host.cas_error = OSError("CAS conflict")
        self.assertEqual(receipt["status"], "RELEASE_UNCONFIRMED")
        self.assertEqual(len(self.host.writes), 1)
        self.assertIsNotNone(self.host.state["holder"])

    def test_lost_ack_is_not_false_failure_or_retried_release(self):
        def lost(repository, branch, *, expected_sha, state, force):
            self.host.cas(repository, branch, expected_sha=expected_sha, state=state, force=force)
            raise OSError("ACK lost")
        with self.assertRaises(RuntimeError):
            with self.session(cas=lost) as receipt:
                pass
        self.assertIsNone(self.host.state["holder"])
        self.assertEqual(receipt["status"], "RELEASE_UNCONFIRMED")
        self.assertEqual(len(self.host.writes), 1)

    def test_false_postwrite_receipt_is_not_confirmed(self):
        self.host.after_write = lambda h: h.state.update(holder=deepcopy(Host().state["holder"]))
        with self.assertRaises(RuntimeError):
            with self.session() as receipt:
                pass
        self.assertEqual(receipt["status"], "RELEASE_UNCONFIRMED")
        self.assertEqual(len(self.host.writes), 1)

    def test_wrong_postwrite_commit_is_not_confirmed(self):
        self.host.after_write = lambda h: setattr(h, "ref", "c" * 40)
        def wrong_commit(*args, **kwargs):
            self.host.cas(*args, **kwargs)
            return "b" * 40
        with self.assertRaises(RuntimeError):
            with self.session(cas=wrong_commit) as receipt:
                pass
        self.assertEqual(receipt["status"], "RELEASE_UNCONFIRMED")

    def test_legacy_positive_exact_run_recovery_is_preserved(self):
        done = {"id": RUN, "recorded_status": "failed",
                "started_at": NOW, "completed_at": "2026-10-30T00:01:00Z"}
        idle = control.recover_finished_worker(self.host.state, done, EXPIRED)
        self.assertIsNone(idle["holder"])
        self.assertTrue(idle["last_completed"]["recovered_from_service_evidence"])


if __name__ == "__main__":
    unittest.main()
