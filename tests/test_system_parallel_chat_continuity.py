"""Issue123 chat-full continuity tests. These mocks do NOT attest a live service."""
import copy
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_parallel_chat_continuity import (
    draft_checkpoint, successor_preflight, compact_handoff, verify_packet
)
from system_parallel_shadow_leases import KEY

REPO = "kk051780/toy-wars-factory"
OWNER = "da7e6d82-8b0d-4e87-a643-8c8c4e37d710"
TASK = "6adbf0d6a7d881918ce181dff2468867"
START = "2026-11-08T00:00:00Z"
OBS = "2026-11-08T00:05:00Z"
END = "2026-11-08T00:20:00Z"
LATE = "2026-11-08T00:30:00Z"
BRANCH = "controller/chat-full-continuity"


def fixture():
    holder = {"kind": "CONTROLLER", "origin": "controller", "epoch": 513,
              "owner_id": OWNER, "task_id": None, "acquired_at": START,
              "expires_at": END, "base_main_sha": "a"*40,
              "work_branch": BRANCH}
    snap = {"repository": REPO, "main_sha": "a"*40, "ref_sha": "b"*40,
            "state": {"schema": 1, "epoch": 513, "holder": holder}}
    req = {"project_id": "toy-wars-factory", "work_id": "context-p0",
           "branch": BRANCH, "source_head": "c"*40, "seq": 1,
           "stage": "DRAFT_PR", "next_action": "CHECK_CI",
           "summary": "Wait for exact-head CI", "changed_paths": ["tools/safe.py"],
           "pr_number": 202, "ci_run_id": None, "observed_at": OBS}
    return snap, req


def observe(snap, req, at=OBS):
    return {"snapshot": snap, "branch_head": req["source_head"],
            "pr_head": req["source_head"], "observed_at": at}


class ChatFullContinuityTests(unittest.TestCase):
    def setUp(self):
        self.snap, self.req = fixture()
        self.packet = draft_checkpoint(self.snap, self.req)["packet"]

    def result(self, snap=None, at=OBS, packet=None, terminal=None):
        return successor_preflight(
            self.packet if packet is None else packet,
            observe(self.snap if snap is None else snap, self.req, at),
            terminal=terminal)

    def test_valid_checkpoint_draft(self):
        out = draft_checkpoint(self.snap, self.req)
        self.assertEqual(out["status"], "CHECKPOINT_DRAFT_UNTRUSTED")
        self.assertFalse(out["may_write"])
        self.assertFalse(out["persisted_to_github"])
        self.assertEqual(len(out["packet"]["digest"]), 64)
        self.assertEqual(out["packet"]["owner_id"], OWNER)

    def test_packet_self_check(self):
        self.assertEqual(verify_packet(self.packet)["work_id"], "context-p0")

    def test_compact_restart_handoff(self):
        text = compact_handoff(self.packet)
        self.assertIn("Issues 123/182", text)
        self.assertIn(self.packet["digest"], text)
        self.assertIn("Never inherit", text)

    def test_live_owner_must_be_joined_read_only(self):
        out = self.result()
        self.assertEqual(out["status"], "JOIN_ACTIVE_OWNER_READ_ONLY")
        self.assertFalse(out["may_write"])
        self.assertFalse(out["may_release"])

    def test_chat_context_full_is_not_terminal_proof(self):
        self.assertEqual(self.result(at=LATE)["status"],
                         "WAIT_MANUAL_EXACT_EPOCH_OWNER_REVOCATION")

    def test_other_active_holder_not_overwritten(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"]["owner_id"] = "11111111-1111-4111-8111-111111111111"
        self.assertEqual(self.result(s)["status"], "WAIT_OTHER_OWNER_OR_EPOCH")

    def test_reacquired_new_epoch_not_old_owner(self):
        s = copy.deepcopy(self.snap)
        s["state"]["epoch"] = 514
        s["state"]["holder"]["epoch"] = 514
        self.assertEqual(self.result(s)["status"], "WAIT_OTHER_OWNER_OR_EPOCH")

    def test_branch_head_drift(self):
        obs = observe(self.snap, self.req)
        obs["branch_head"] = "d"*40
        self.assertEqual(successor_preflight(self.packet, obs)["status"],
                         "WAIT_EXACT_HEAD_DRIFT")

    def test_pr_head_drift(self):
        obs = observe(self.snap, self.req)
        obs["pr_head"] = "e"*40
        self.assertEqual(successor_preflight(self.packet, obs)["status"],
                         "WAIT_EXACT_HEAD_DRIFT")

    def test_main_drift(self):
        s = copy.deepcopy(self.snap)
        s["main_sha"] = "f"*40
        self.assertEqual(self.result(s)["status"], "WAIT_UNTRUSTED_EVIDENCE")

    def test_packet_tampering(self):
        p = copy.deepcopy(self.packet)
        p["next_action"] = "EDIT"
        self.assertEqual(self.result(packet=p)["status"], "WAIT_UNTRUSTED_EVIDENCE")

    def test_packet_unknown_field(self):
        p = copy.deepcopy(self.packet)
        p["service_proven"] = True
        self.assertEqual(self.result(packet=p)["status"], "WAIT_UNTRUSTED_EVIDENCE")

    def test_sequence_replay(self):
        same = dict(self.req, observed_at="2026-11-08T00:06:00Z")
        self.assertEqual(draft_checkpoint(self.snap, same, self.packet)["status"],
                         "WAIT_INVALID_CHECKPOINT")
        same["seq"] = 2
        self.assertEqual(draft_checkpoint(self.snap, same, self.packet)["status"],
                         "CHECKPOINT_DRAFT_UNTRUSTED")

    def test_sequence_owner_drift(self):
        changed = copy.deepcopy(self.snap)
        changed["state"]["holder"]["owner_id"] = "11111111-1111-4111-8111-111111111111"
        same = dict(self.req, seq=2, observed_at="2026-11-08T00:06:00Z")
        self.assertEqual(draft_checkpoint(changed, same, self.packet)["status"],
                         "WAIT_INVALID_CHECKPOINT")

    def test_timestamp_outside_lease(self):
        req = dict(self.req, observed_at=LATE)
        self.assertEqual(draft_checkpoint(self.snap, req)["status"],
                         "WAIT_INVALID_CHECKPOINT")

    def test_wrong_branch_scope(self):
        req = dict(self.req, branch="controller/foreign-work")
        self.assertEqual(draft_checkpoint(self.snap, req)["status"],
                         "WAIT_INVALID_CHECKPOINT")

    def test_secret_like_summary_rejected(self):
        req = dict(self.req, summary="password is private")
        self.assertEqual(draft_checkpoint(self.snap, req)["status"],
                         "WAIT_INVALID_CHECKPOINT")

    def test_control_character_summary_rejected(self):
        req = dict(self.req, summary="bad\ninjection")
        self.assertEqual(draft_checkpoint(self.snap, req)["status"],
                         "WAIT_INVALID_CHECKPOINT")

    def test_path_case_alias_rejected(self):
        req = dict(self.req, changed_paths=["tools/A.py", "TOOLS/a.py"])
        self.assertEqual(draft_checkpoint(self.snap, req)["status"],
                         "WAIT_INVALID_CHECKPOINT")

    def test_unsigned_empty_released_state_blocks(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"] = None
        self.assertEqual(self.result(s)["status"], "WAIT_ORIGINAL_RELEASE_PROOF")

    def test_exact_owner_release_proposes_fresh_lease_only(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"] = None
        s["ref_sha"] = "d"*40
        s["state"]["last_completed"] = {
            "owner_id": OWNER, "epoch": 513,
            "released_at": "2026-11-08T00:11:00Z"}
        out = self.result(s, "2026-11-08T00:12:00Z")
        self.assertEqual(out["status"], "HANDOFF_READY_ONLY_AFTER_FRESH_LEASE")
        for flag in ("may_write", "may_recover", "may_release", "provider_authenticated"):
            self.assertFalse(out[flag])

    def test_other_epoch_release_proof_rejected(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"] = None
        s["ref_sha"] = "d"*40
        s["state"]["last_completed"] = {
            "owner_id": OWNER, "epoch": 512,
            "released_at": "2026-11-08T00:11:00Z"}
        self.assertEqual(self.result(s)["status"], "WAIT_ORIGINAL_RELEASE_PROOF")

    def test_same_coordinator_ref_not_release(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"] = None
        s["state"]["last_completed"] = {
            "owner_id": OWNER, "epoch": 513,
            "released_at": "2026-11-08T00:11:00Z"}
        self.assertEqual(self.result(s)["status"], "WAIT_ORIGINAL_RELEASE_PROOF")

    def test_registered_run_needs_real_service_terminal(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"]["kind"] = "WORKER"
        s["state"]["holder"]["task_id"] = TASK
        pkt = draft_checkpoint(s, self.req)["packet"]
        self.assertEqual(pkt["origin"], "REGISTERED")
        self.assertEqual(successor_preflight(pkt, observe(s, self.req, LATE))["status"],
                         "WAIT_AUTHENTIC_SERVICE_TERMINAL")

    def test_registered_terminal_candidate_never_auto_releases(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"]["kind"] = "WORKER"
        s["state"]["holder"]["task_id"] = TASK
        pkt = draft_checkpoint(s, self.req)["packet"]
        terminal = {"task_id":TASK, "run_id":OWNER,
                    "started_at":"2026-11-07T23:59:00Z",
                    "completed_at":"2026-11-08T00:25:00Z",
                    "recorded_status":"completed"}
        out = successor_preflight(pkt, observe(s, self.req, LATE), terminal)
        self.assertEqual(out["status"],
                         "TERMINAL_CANDIDATE_REQUIRES_ORIGINAL_PROVIDER_PROOF")
        self.assertFalse(out["may_recover"])

    def test_foreign_registered_run_not_terminal_proof(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"]["kind"] = "WORKER"
        s["state"]["holder"]["task_id"] = TASK
        pkt = draft_checkpoint(s, self.req)["packet"]
        terminal = {"task_id":TASK,
                    "run_id":"11111111-1111-4111-8111-111111111111",
                    "started_at":START, "completed_at":"2026-11-08T00:25:00Z",
                    "recorded_status":"completed"}
        self.assertEqual(successor_preflight(pkt, observe(s, self.req, LATE),
                                             terminal)["status"], "WAIT_UNTRUSTED_EVIDENCE")

    def test_inprogress_is_not_terminal_proof(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"]["kind"] = "WORKER"
        s["state"]["holder"]["task_id"] = TASK
        pkt = draft_checkpoint(s, self.req)["packet"]
        terminal = {"task_id":TASK,"run_id":OWNER,"started_at":START,
                    "completed_at":None,"recorded_status":"in_progress"}
        self.assertEqual(successor_preflight(pkt, observe(s,self.req,LATE),
                                             terminal)["status"], "WAIT_UNTRUSTED_EVIDENCE")

    def test_shadow_scope_packet_not_a_grant(self):
        s = copy.deepcopy(self.snap)
        s["state"]["holder"] = None
        s["state"][KEY] = {"schema":1, "entries":[{
            "scope":{"project_id":"toy-wars-factory","repository":REPO,
                     "work_id":"context-p0","branch":BRANCH,
                     "base_sha":"a"*40,"write_paths":["tools/safe.py"],
                     "read_paths":[],"generated_paths":[],"shared_resources":[],
                     "status":"ACTIVE"},
            "owner_id":OWNER,"run_id":TASK,
            "nonce":"11111111-1111-4111-8111-111111111111",
            "lease_epoch":513,"acquired_at":START,"expires_at":END}]}
        out = draft_checkpoint(s, self.req)
        self.assertEqual(out["status"],"CHECKPOINT_DRAFT_UNTRUSTED")
        self.assertFalse(out["may_write"])
        self.assertFalse(out["persisted_to_github"])

if __name__=="__main__":
    unittest.main()
