"""Untrusted callbacks are mocks; this does not authenticate real GitHub CAS."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_owner_intake_dedup import calculate_work_id, classify
from system_owner_work_registration import (
    CONTROL_BRANCH, CONTROL_PATH, Rejected, apply_once, plan, intake_projection, MAX_ROWS,
)

REPO = "kk051780/toy-wars-factory"
OWNER = "5b2ba016-a1a7-47ea-8cf6-8ba0e6f43ac9"
OTHER = "727de839-519d-49cd-82fb-d4cf7fd9a017"
MAIN = "a" * 40
REF = "b" * 40
BRANCH = "controller/owner-work-reservation-5b2ba016"
ACQUIRED = "2026-10-31T09:22:00Z"
EXPIRES = "2026-10-31T09:47:00Z"
NOW = "2026-10-31T09:24:00Z"


def fixture():
    state = {"schema": 1, "epoch": 441, "holder": {
        "kind": "CONTROLLER", "origin": "controller", "owner_id": OWNER,
        "task_id": None, "epoch": 441, "base_main_sha": MAIN,
        "work_branch": BRANCH, "acquired_at": ACQUIRED, "expires_at": EXPIRES,
    }, "other_field": {"do_not_touch": [42, False]}}
    snap = {"repository": REPO, "coordination_branch": CONTROL_BRANCH,
            "ref_sha": REF, "main_sha": MAIN, "state": state}
    req = {"project_id": "toy-wars-factory", "repository": REPO,
           "kind": "gameplay", "idea_id": "owner:oct31:repair", "owner_id": OWNER,
           "objective": "Add a new toy repair character", "epoch": 441,
           "base_main_sha": MAIN, "work_branch": BRANCH, "observed_at": NOW}
    return snap, req


class FakeRefHost:
    def __init__(self, snap):
        self.mu = threading.Lock()
        self.snap = copy.deepcopy(snap)
        self.calls = 0

    def cas(self, repo, branch, path, expected_sha, state):
        assert (repo, branch, path) == (REPO, CONTROL_BRANCH, CONTROL_PATH)
        with self.mu:
            self.calls += 1
            if self.snap["ref_sha"] != expected_sha:
                return None
            # Simulate original Git immutable commit/ref update and one winner.
            encoded = json.dumps(state, sort_keys=True, ensure_ascii=False).encode("utf-8")
            new = hashlib.sha1(b"commit " + str(len(encoded)).encode() + b"\x00" + encoded).hexdigest()
            self.snap["state"] = copy.deepcopy(state)
            self.snap["ref_sha"] = new
            return new

    def readback(self, repo, branch, path):
        assert (repo, branch, path) == (REPO, CONTROL_BRANCH, CONTROL_PATH)
        with self.mu:
            return copy.deepcopy(self.snap)


def new_entry(snap, req, *, override=None):
    row = copy.deepcopy(plan(snap, req)["proposed_state"]["work_registrations"]["entries"][0])
    row.update(override or {})
    return row


class WorkClaimCASTests(unittest.TestCase):
    def test_unknown_coordinator_schema_rejected_before_proposal(self):
        for invalid in (0, 2, 999):
            with self.subTest(schema=invalid):
                snap, req = fixture()
                snap["state"]["schema"] = invalid
                with self.assertRaisesRegex(Rejected, "malformed coordinator state"):
                    plan(snap, req)

    def test_unknown_coordinator_schema_never_attempts_cas(self):
        for invalid in (0, 2, 999):
            with self.subTest(schema=invalid):
                snap, req = fixture()
                snap["state"]["schema"] = invalid
                host = FakeRefHost(snap)
                with self.assertRaisesRegex(Rejected, "malformed coordinator state"):
                    apply_once(snap, req, cas=host.cas, readback=host.readback,
                               read_main_ref=lambda repo: MAIN)
                self.assertEqual(host.calls, 0)

    def test_expired_holder_must_fail_closed(self):
        snap, req = fixture()
        req["observed_at"] = "2026-10-31T09:48:00Z"
        with self.assertRaisesRegex(Rejected, "unexpired exclusive lease"):
            plan(snap, req)

    def test_exact_expiration_boundary_rejects(self):
        snap, req = fixture()
        req["observed_at"] = EXPIRES
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_now_before_acquisition_rejects(self):
        snap, req = fixture()
        req["observed_at"] = "2026-10-31T09:21:59Z"
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_extended_lease_over_half_hour_rejects(self):
        snap, req = fixture()
        snap["state"]["holder"]["expires_at"] = "2026-10-31T11:00:00Z"
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_non_utc_or_naive_timestamp_rejected(self):
        for now in ("2026-10-31T09:24:00", "2026-10-31T18:24:00+09:00", "yesterday"):
            with self.subTest(now=now):
                snap, req = fixture()
                req["observed_at"] = now
                with self.assertRaises(Rejected):
                    plan(snap, req)

    def test_forged_or_bad_holder_timestamp_rejected(self):
        for value in ("", "2026-10-31T09:00:00", "not-a-time"):
            with self.subTest(value=value):
                snap, req = fixture()
                snap["state"]["holder"]["acquired_at"] = value
                with self.assertRaises(Rejected):
                    plan(snap, req)

    def test_intake_projection_is_compatible_with_v2_classifier(self):
        snap, req = fixture()
        host = FakeRefHost(snap)
        result = apply_once(snap, req, cas=host.cas, readback=host.readback, read_main_ref=lambda repo: MAIN)
        self.assertEqual(result["status"], "CALLBACK_CAS_CONFIRMED_NOT_GITHUB_AUTHENTICATED")
        current = host.readback(REPO, CONTROL_BRANCH, CONTROL_PATH)
        rows = intake_projection(current)
        self.assertEqual(len(rows), 1)
        v2 = {"schema": 2, "project_id": req["project_id"], "repository": REPO,
              "main_sha": MAIN, "collection_complete": True,
              "incoming": {key: req[key] for key in ("idea_id", "kind", "objective")},
              "records": rows}
        advisory = classify(v2)
        self.assertEqual(advisory["decision"], "JOIN_EXISTING_ADVISORY")
        self.assertFalse(advisory["may_claim"])

    def test_intake_projection_does_not_mutate_registry(self):
        snap, req = fixture()
        snap["state"]["work_registrations"] = {"schema": 1,
            "entries": [new_entry(fixture()[0], req)]}
        prior = copy.deepcopy(snap)
        output = intake_projection(snap)
        self.assertEqual(snap, prior)
        self.assertEqual(set(output[0]), {
            "project_id", "repository", "idea_id", "kind", "objective", "work_id", "status"
        })

    def test_main_changes_before_cas_no_write_attempt(self):
        snap, req = fixture()
        called = []
        def cas(*args):
            called.append(1)
            return "c" * 40
        out = apply_once(snap, req, cas=cas, readback=lambda *a: {},
                         read_main_ref=lambda repo: "d" * 40)
        self.assertEqual(out["status"], "WAIT_MAIN_DRIFT_UNCONFIRMED")
        self.assertFalse(out["cas_attempted"])
        self.assertEqual(called, [])

    def test_main_changes_after_cas_refuses_confirmed(self):
        snap, req = fixture()
        host = FakeRefHost(snap)
        observations = iter([MAIN, "d" * 40])
        out = apply_once(snap, req, cas=host.cas, readback=host.readback,
                         read_main_ref=lambda repo: next(observations))
        self.assertEqual(out["status"], "WAIT_CAS_UNCONFIRMED")
        self.assertTrue(out["cas_attempted"])
        self.assertFalse(out["may_dispatch"])

    def test_main_ref_provider_error_prevents_any_cas(self):
        snap, req = fixture()
        def broken(*args):
            raise OSError("provider offline")
        out = apply_once(snap, req,
                         cas=lambda *a: self.fail("should not call CAS"),
                         readback=lambda *a: self.fail("should not read"),
                         read_main_ref=broken)
        self.assertEqual(out["status"], "WAIT_MAIN_DRIFT_UNCONFIRMED")

    def test_second_coordinator_readback_drift_blocks_ack(self):
        snap, req = fixture()
        host = FakeRefHost(snap)
        calls = []
        def drift(*args):
            v = host.readback(*args)
            calls.append(1)
            if len(calls) == 2:
                v["ref_sha"] = "e" * 40
            return v
        out = apply_once(snap, req, cas=host.cas, readback=drift,
                         read_main_ref=lambda repo: MAIN)
        self.assertEqual(out["status"], "WAIT_CAS_UNCONFIRMED")
        self.assertEqual(len(calls), 2)

    def test_new_work_makes_only_a_plan_not_a_dispatch(self):
        snap, req = fixture()
        result = plan(snap, req)
        self.assertEqual(result["decision"], "CAS_PROPOSAL_NOT_AUTHORIZED")
        self.assertFalse(result["may_dispatch"])
        self.assertFalse(result["github_authenticated"])
        self.assertEqual(result["expected_sha"], REF)

    def test_plan_leaves_original_state_exact(self):
        snap, req = fixture()
        before = copy.deepcopy(snap)
        result = plan(snap, req)
        self.assertEqual(snap, before)
        self.assertEqual(result["proposed_state"]["other_field"],
                         snap["state"]["other_field"])
        self.assertNotIn("work_registrations", snap["state"])

    def test_claim_record_hash_is_scoped_and_reserved(self):
        snap, req = fixture()
        row = plan(snap, req)["proposed_state"]["work_registrations"]["entries"][0]
        self.assertEqual(row["work_id"], calculate_work_id(
            req["project_id"], REPO, req["kind"], req["objective"]))
        self.assertEqual(row["status"], "OPEN")
        self.assertEqual(row["created_from_main_sha"], MAIN)

    def test_two_simultaneous_chat_submissions_can_only_win_one_cas(self):
        snap, req = fixture()
        other_req = dict(req, idea_id="chat:two")
        host = FakeRefHost(snap)
        barrier = threading.Barrier(2)

        def task(input_req):
            barrier.wait(timeout=5)
            return apply_once(copy.deepcopy(snap), input_req,
                              cas=host.cas, readback=host.readback, read_main_ref=lambda repo: MAIN)

        with ThreadPoolExecutor(max_workers=2) as executor:
            a = executor.submit(task, req)
            b = executor.submit(task, other_req)
            results = [a.result(timeout=7), b.result(timeout=7)]
        self.assertEqual(host.calls, 2)
        self.assertEqual(sum(v["status"] == "CALLBACK_CAS_CONFIRMED_NOT_GITHUB_AUTHENTICATED"
                             for v in results), 1)
        self.assertEqual(sum(v["status"] == "WAIT_CAS_CONFLICT_OR_INVALID_ACK"
                             for v in results), 1)
        self.assertEqual(len(host.snap["state"]["work_registrations"]["entries"]), 1)
        self.assertFalse(any(v["may_dispatch"] or v["github_authenticated"] for v in results))
        # Loser must explicitly re-read the host, join instead of retrying a CAS.
        joined = plan(host.readback(REPO, CONTROL_BRANCH, CONTROL_PATH), other_req)
        self.assertEqual(joined["decision"], "JOIN_EXISTING_UNVERIFIED")

    def test_sequential_same_id_joins_without_second_cas(self):
        snap, req = fixture()
        host = FakeRefHost(snap)
        first = apply_once(snap, req, cas=host.cas, readback=host.readback, read_main_ref=lambda repo: MAIN)
        req2 = dict(req, idea_id="another-chat")
        second = apply_once(host.readback(REPO, CONTROL_BRANCH, CONTROL_PATH), req2,
                            cas=host.cas, readback=host.readback, read_main_ref=lambda repo: MAIN)
        self.assertEqual(first["status"], "CALLBACK_CAS_CONFIRMED_NOT_GITHUB_AUTHENTICATED")
        self.assertEqual(second["status"], "JOIN_EXISTING_UNVERIFIED")
        self.assertEqual(host.calls, 1)
        self.assertFalse(second["cas_attempted"])

    def test_completed_and_cancelled_do_not_reopen(self):
        for status in ("DONE", "CANCELLED", "BLOCKED", "IN_PROGRESS"):
            with self.subTest(status=status):
                snap, req = fixture()
                row = new_entry(snap, req, override={"status": status})
                snap["state"]["work_registrations"] = {"schema": 1, "entries": [row]}
                a = plan(snap, req)
                self.assertEqual(a["decision"], "JOIN_EXISTING_UNVERIFIED")
                self.assertEqual(a["existing_status"], status)
                self.assertIsNone(a["proposed_state"])

    def test_owner_idea_drift_is_rejected(self):
        snap, req = fixture()
        row = new_entry(snap, req)
        snap["state"]["work_registrations"] = {"schema": 1, "entries": [row]}
        request = dict(req, objective="Build a bigger workshop")
        with self.assertRaisesRegex(Rejected, "changed objective"):
            plan(snap, request)

    def test_lease_foreign_holder_rejects(self):
        snap, req = fixture()
        snap["state"]["holder"]["owner_id"] = OTHER
        with self.assertRaisesRegex(Rejected, "foreign"):
            plan(snap, req)

    def test_lease_reviewer_kind_rejects(self):
        snap, req = fixture()
        snap["state"]["holder"]["kind"] = "REVIEWER"
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_holder_null_rejects_new(self):
        snap, req = fixture()
        snap["state"]["holder"] = None
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_lease_epoch_renewal_rejects_old_request(self):
        snap, req = fixture()
        snap["state"]["epoch"] = 442
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_request_main_drift_rejects(self):
        snap, req = fixture()
        snap["main_sha"] = "c" * 40
        with self.assertRaisesRegex(Rejected, "stale"):
            plan(snap, req)

    def test_holder_main_drift_rejects(self):
        snap, req = fixture()
        snap["state"]["holder"]["base_main_sha"] = "c" * 40
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_request_branch_not_exact_rejects(self):
        snap, req = fixture()
        req["work_branch"] = BRANCH + "-elsewhere"
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_legacy_v1_envelope_malformed_rejects(self):
        snap, req = fixture()
        snap["state"]["schema"] = "1"
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_wrong_branch_and_invalid_ref_rejects(self):
        for field, value in (("coordination_branch", "main"),
                             ("ref_sha", "not-a-sha"), ("main_sha", "zz")):
            with self.subTest(field=field):
                snap, req = fixture()
                snap[field] = value
                with self.assertRaises(Rejected):
                    plan(snap, req)

    def test_duplicate_work_rows_rejected(self):
        snap, req = fixture()
        row = new_entry(snap, req)
        snap["state"]["work_registrations"] = {"schema": 1, "entries": [row, row]}
        with self.assertRaisesRegex(Rejected, "duplicate"):
            plan(snap, req)

    def test_reused_owner_idea_across_distinct_work_ids_rejected(self):
        snap, req = fixture()
        row = new_entry(snap, req)
        other = dict(req, objective="Build a new conveyor")
        row2 = new_entry(snap, other)
        snap["state"]["work_registrations"] = {"schema": 1, "entries": [row, row2]}
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_foreign_project_row_stays_separate(self):
        snap, req = fixture()
        row = new_entry(snap, req)
        row["project_id"] = "other-game"
        row["work_id"] = calculate_work_id(row["project_id"], row["repository"],
                                            row["kind"], row["objective"])
        snap["state"]["work_registrations"] = {"schema": 1, "entries": [row]}
        candidate = plan(snap, req)
        self.assertEqual(candidate["decision"], "CAS_PROPOSAL_NOT_AUTHORIZED")
        self.assertEqual(len(candidate["proposed_state"]["work_registrations"]["entries"]), 2)

    def test_bad_registry_id_rejected(self):
        snap, req = fixture()
        row = new_entry(snap, req)
        row["work_id"] = "work-fake"
        snap["state"]["work_registrations"] = {"schema": 1, "entries": [row]}
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_unknown_registry_fields_rejected(self):
        snap, req = fixture()
        row = new_entry(snap, req)
        row["can_write"] = True
        snap["state"]["work_registrations"] = {"schema": 1, "entries": [row]}
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_malformed_registry_payload_rejected(self):
        for registry in ([], {}, {"schema": True, "entries": []},
                         {"schema": 1, "entries": {}}):
            with self.subTest(registry=str(registry)):
                snap, req = fixture()
                snap["state"]["work_registrations"] = registry
                with self.assertRaises(Rejected):
                    plan(snap, req)

    def test_bad_objective_unicode_rejected(self):
        snap, req = fixture()
        req["objective"] += "\u202e"
        with self.assertRaises(ValueError):
            plan(snap, req)

    def test_wrong_origin_or_task_identity_rejected(self):
        for field, value in (("origin", "worker"), ("task_id", "fake-run")):
            with self.subTest(field=field):
                snap, req = fixture()
                snap["state"]["holder"][field] = value
                with self.assertRaises(Rejected):
                    plan(snap, req)

    def test_callback_cas_denial_does_not_retry(self):
        snap, req = fixture()
        called = []
        def reject(*args):
            called.append(args)
            return None
        result = apply_once(snap, req, cas=reject,
                            readback=lambda *args: self.fail("unexpected readback"),
                            read_main_ref=lambda repo: MAIN)
        self.assertEqual(result["status"], "WAIT_CAS_CONFLICT_OR_INVALID_ACK")
        self.assertEqual(len(called), 1)

    def test_callback_ack_lost_does_not_retry(self):
        snap, req = fixture()
        called = []
        def loses_ack(*args):
            called.append(1)
            raise TimeoutError("postwrite loss")
        result = apply_once(snap, req, cas=loses_ack,
                            readback=lambda *args: self.fail("unexpected readback"),
                            read_main_ref=lambda repo: MAIN)
        self.assertEqual(result["status"], "WAIT_CAS_UNCONFIRMED")
        self.assertEqual(len(called), 1)

    def test_callback_fake_success_wrong_readback_is_unconfirmed(self):
        snap, req = fixture()
        result = apply_once(snap, req, cas=lambda *args: "c" * 40,
                            readback=lambda *args: snap, read_main_ref=lambda repo: MAIN)
        self.assertEqual(result["status"], "WAIT_CAS_UNCONFIRMED")
        self.assertFalse(result["may_dispatch"])

    def test_callback_bogus_sha_is_not_success(self):
        snap, req = fixture()
        r = apply_once(snap, req, cas=lambda *args: "not-a-git-sha",
                       readback=lambda *args: self.fail("unexpected readback"),
                            read_main_ref=lambda repo: MAIN)
        self.assertEqual(r["status"], "WAIT_CAS_CONFLICT_OR_INVALID_ACK")

    def test_host_failure_to_return_complete_snapshot_is_unconfirmed(self):
        snap, req = fixture()
        out = apply_once(snap, req, cas=lambda *args: "c" * 40,
                         readback=lambda *args: {"ref_sha": "c" * 40},
                         read_main_ref=lambda repo: MAIN)
        self.assertEqual(out["status"], "WAIT_CAS_UNCONFIRMED")

    def test_after_new_registry_other_fields_are_intact(self):
        snap, req = fixture()
        p = plan(snap, req)
        self.assertEqual(p["proposed_state"]["other_field"],
                         {"do_not_touch": [42, False]})
        self.assertEqual(p["proposed_state"]["holder"], snap["state"]["holder"])

    def test_invalid_request_extra_permissions_field_fails(self):
        snap, req = fixture()
        req["may_dispatch"] = True
        with self.assertRaises(Rejected):
            plan(snap, req)

    def test_nonlinear_unicode_objective_hash_is_stable(self):
        snap, req = fixture()
        req2 = dict(req, objective="Ａｄｄ a new toy repair character")
        self.assertEqual(plan(snap, req)["work_id"], plan(snap, req2)["work_id"])


if __name__ == "__main__":
    unittest.main()
