"""Exercise cross-entry races, fenced ownership and actionable approval handoffs."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import (CONTROL_PATH, acquire, approval_packet, initial_state, owns,
                            recover_finished_worker, release, render_approvals,
                            report_needed, verify_pr)

RUN = "23e9ebe9-179c-8326-8fdd-ac241ec4ef53"
OTHER = "039874ac-64a0-8323-bc57-5c35cf58ec90"
NOW = "2026-10-25T00:00:00Z"
LATER = "2026-10-25T00:31:00Z"
BRANCH = "auto/twf-game-repair-" + RUN
REPO = "kk051780/toy-wars-factory"


class CoordinationTests(unittest.TestCase):
    def worker(self, state=None, owner=RUN, now=NOW):
        return acquire(state or initial_state(), "WORKER", owner, now, work_branch=BRANCH)

    def test_manual_go_joins_in_progress_service_without_dispatch(self):
        result = acquire(initial_state(), "DISPATCH", RUN, NOW, service_status="in_progress")
        self.assertEqual(result["action"], "JOIN_EXISTING")
        self.assertFalse(result["write"])

    def test_unknown_service_state_cannot_dispatch(self):
        for state in (None, "unknown"):
            self.assertEqual(acquire(initial_state(), "DISPATCH", RUN, NOW, service_status=state)["action"], "WAIT_METADATA")

    def test_second_manual_go_cannot_queue_another_dispatch(self):
        first = acquire(initial_state(), "DISPATCH", RUN, NOW, service_status="completed")["state"]
        second = acquire(first, "DISPATCH", OTHER, NOW, service_status="completed")
        self.assertFalse(second["write"])
        self.assertEqual(second["action"], "JOIN_EXISTING")

    def test_first_worker_adopts_manual_ticket_and_fences_dispatcher(self):
        ticket = acquire(initial_state(), "DISPATCH", RUN, NOW, service_status="completed")["state"]
        work = self.worker(ticket, OTHER)["state"]
        self.assertEqual(work["holder"]["kind"], "WORKER")
        self.assertEqual(work["holder"]["origin"], "manual")
        self.assertGreater(work["epoch"], ticket["epoch"])
        with self.assertRaises(ValueError):
            release(work, "DISPATCH", RUN, ticket["epoch"], NOW)

    def test_other_worker_waits_for_existing_owner(self):
        first = self.worker()["state"]
        second = self.worker(first, OTHER)
        self.assertFalse(second["write"])
        self.assertEqual(second["action"], "JOIN_EXISTING")
        self.assertEqual(second["state"]["holder"]["owner_id"], RUN)

    def test_same_worker_can_resume_without_a_second_claim(self):
        state = self.worker()["state"]
        result = self.worker(state)
        self.assertEqual(result["action"], "RESUME")
        self.assertFalse(result["write"])

    def test_controller_blocks_manual_and_scheduled_writes(self):
        state = acquire(initial_state(), "CONTROLLER", RUN, NOW)["state"]
        self.assertEqual(self.worker(state, OTHER)["action"], "WAIT_LOCK")
        self.assertFalse(acquire(state, "DISPATCH", OTHER, NOW, service_status="completed")["write"])

    def test_expiry_does_not_steal_or_authorize_a_write(self):
        state = self.worker()["state"]
        self.assertFalse(owns(state, "WORKER", RUN, state["epoch"], LATER))
        self.assertEqual(self.worker(state, OTHER, LATER)["action"], "WAIT_RECOVERY")
        self.assertEqual(self.worker(state, RUN, LATER)["action"], "WAIT_RECOVERY")

    def test_positive_completion_proof_recovers_finished_worker(self):
        state = self.worker()["state"]
        observed = {"id": RUN, "recorded_status": "failed", "completed_at": "2026-10-25T00:02:00Z"}
        recovered = recover_finished_worker(state, observed, LATER)
        self.assertIsNone(recovered["holder"])
        self.assertTrue(recovered["last_completed"]["recovered_from_service_evidence"])

    def test_unrelated_or_active_run_cannot_recover_lease(self):
        state = self.worker()["state"]
        for observed in ({"id": OTHER, "recorded_status": "completed", "completed_at": NOW},
                         {"id": RUN, "recorded_status": "in_progress", "completed_at": None}):
            with self.assertRaises(ValueError):
                recover_finished_worker(state, observed, LATER)

    def test_only_exact_owner_and_generation_can_release(self):
        state = self.worker()["state"]
        for owner, epoch in ((OTHER, state["epoch"]), (RUN, state["epoch"] + 1)):
            with self.assertRaises(ValueError):
                release(state, "WORKER", owner, epoch, NOW)
        idle = release(state, "WORKER", RUN, state["epoch"], NOW)
        self.assertIsNone(idle["holder"])
        self.assertGreater(self.worker(idle, OTHER)["state"]["epoch"], state["epoch"])

    def test_plan_does_not_mutate_input_and_requires_canonical_identity(self):
        state = initial_state()
        before = copy.deepcopy(state)
        self.worker(state)
        self.assertEqual(state, before)
        with self.assertRaises(ValueError):
            self.worker(state, "manual-go")

    def test_meta_and_game_writers_share_the_same_fence(self):
        state = initial_state()
        state["authorized_tasks"]["META"] = "meta-test-task"
        with self.assertRaises(ValueError):
            acquire(state, "META", OTHER, NOW, actor_task_id="unregistered")
        meta = acquire(state, "META", OTHER, NOW, actor_task_id="meta-test-task",
                       work_branch="auto/twf-system-review-" + OTHER)["state"]
        self.assertFalse(self.worker(meta)["write"])
        game = self.worker(state)["state"]
        self.assertFalse(acquire(game, "META", OTHER, NOW, actor_task_id="meta-test-task")["write"])

    def test_meta_does_not_consume_a_manual_game_dispatch(self):
        state = initial_state()
        state["authorized_tasks"]["META"] = "meta-test-task"
        ticket = acquire(state, "DISPATCH", RUN, NOW, service_status="completed")["state"]
        self.assertFalse(acquire(ticket, "META", OTHER, NOW, actor_task_id="meta-test-task")["write"])


class ApprovalTests(unittest.TestCase):
    def pr(self, number=38):
        return {"number": number, "title": "floor fix", "head": "a" * 40,
                "ci_head": "a" * 40, "ci": "success", "state": "open", "merged": False,
                "repository": REPO, "url": f"https://github.com/{REPO}/pull/{number}",
                "ci_url": f"https://github.com/{REPO}/actions/runs/1",
                "summary": "床3種類の衝突設定。5検査が合格。", "changed_files": ["src/ToyWarsServer.server.lua"]}

    def packet(self, pulls=None, now=NOW):
        return approval_packet(pulls or [self.pr()], REPO, now)

    def test_packet_names_each_pr_changes_evidence_and_reply(self):
        packet = self.packet([self.pr(35), self.pr(38), self.pr(40)])
        rendered = render_approvals(packet)
        for number in (35, 38, 40):
            self.assertIn(f"[#{number}]", rendered)
        self.assertIn("床3種類", rendered)
        self.assertIn("actions/runs/1", rendered)
        self.assertIn("#35・#38・#40のmain取り込みを承認", rendered)
        self.assertFalse(packet["automatic_merge_authorized"])
        self.assertFalse(packet["roblox_publish_authorized"])

    def test_test_only_pr_is_not_presented_as_game_source_fix(self):
        pr = self.pr()
        pr["changed_files"] = ["tests/auto/regression_spec.lua"]
        self.assertEqual(self.packet([pr])["items"][0]["kind"], "回帰検査追加")

    def test_system_improvement_has_its_own_approval_category(self):
        pr = self.pr()
        pr["changed_files"] = ["tools/repair_queue.py", "tests/test_system_example.py"]
        self.assertEqual(self.packet([pr])["items"][0]["kind"], "開発体制改善")

    def test_stale_or_failed_ci_cannot_be_approval_ready(self):
        for changes in ({"ci_head": "b" * 40}, {"ci": "pending"}, {"ci": "failure"}, {"state": "closed"}, {"repository": "other/fork"}):
            pr = {**self.pr(), **changes}
            with self.assertRaises(ValueError):
                self.packet([pr])

    def test_missing_contents_or_duplicate_pr_cannot_generate_vague_request(self):
        pr = self.pr()
        pr["summary"] = ""
        with self.assertRaises(ValueError):
            self.packet([pr])
        with self.assertRaises(ValueError):
            self.packet([self.pr(), self.pr()])

    def test_observation_time_does_not_repeat_identical_scheduled_notice(self):
        state = initial_state()
        packet = self.packet()
        self.assertTrue(report_needed(state, packet))
        state["last_reported_approval_signature"] = packet["signature"]
        again = self.packet(now=LATER)
        self.assertEqual(packet["signature"], again["signature"])
        self.assertFalse(report_needed(state, again))
        self.assertTrue(report_needed(state, again, manual=True))

    def test_head_or_evidence_change_requires_a_fresh_request(self):
        state = initial_state()
        state["last_reported_approval_signature"] = self.packet()["signature"]
        pr = self.pr()
        pr["head"] = pr["ci_head"] = "b" * 40
        self.assertTrue(report_needed(state, self.packet([pr])))

    def test_empty_queue_never_invents_an_approval_request(self):
        packet = approval_packet([], REPO, NOW)
        self.assertEqual(packet["approval_text"], "")
        self.assertFalse(report_needed(initial_state(), packet, manual=True))
        rendered = render_approvals(packet)
        self.assertIn("承認待ちの項目はありません", rendered)
        self.assertNotIn("承認する場合", rendered)


class ImmutableClaimGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        old = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, old)
        self.git("init", "-q")
        self.git("config", "user.name", "Repair control test")
        self.git("config", "user.email", "qa@example.invalid")
        self.idle = initial_state()
        self.idle["authorized_tasks"]["META"] = "meta-test-task"
        self.write(CONTROL_PATH, self.idle)
        self.git("add", ".")
        self.git("commit", "-qm", "idle")
        self.base = self.git("rev-parse", "HEAD")
        self.policy = {"queue_version": 3, "branch": "auto/twf-game-repair", "task_id": "6adbf0d6a7d881918ce181dff2468867",
                       "branch_prefix": "auto/twf-game-repair-", "coordination": {"grandfathered_pr_heads": []},
                       "system_review": {"task_id": "meta-test-task", "branch_prefix": "auto/twf-system-review-"}}

    def git(self, *args):
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()

    def write(self, path, value):
        file = Path(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(value))

    def fixture(self, owner=RUN, work_branch=BRANCH, kind="WORKER", pr_branch=BRANCH):
        self.git("checkout", "-qb", "control", self.base)
        state = acquire(self.idle, kind, owner, NOW, work_branch=work_branch,
                        actor_task_id="meta-test-task" if kind == "META" else None)["state"]
        self.write(CONTROL_PATH, state)
        self.git("add", ".")
        self.git("commit", "-qm", "claim")
        claim = self.git("rev-parse", "HEAD")
        self.git("branch", "coordinator-proof", claim)
        self.git("checkout", "-qb", pr_branch, self.base)
        proof = {"branch": "twf-repair-coordinator", "claim_commit": claim,
                 "owner_run_id": owner, "epoch": state["epoch"]}
        self.write("history/C00099_control.json", {"coordination": proof})
        self.git("add", ".")
        self.git("commit", "-qm", "repair history")
        return self.git("rev-parse", "HEAD"), claim

    def test_valid_ancestor_claim_passes(self):
        head, _ = self.fixture()
        self.assertIn("1 immutable", verify_pr(self.policy, self.base, head, BRANCH, "coordinator-proof"))

    def test_registered_meta_claim_passes_on_its_own_lane(self):
        branch = "auto/twf-system-review-" + RUN
        head, _ = self.fixture(work_branch=branch, kind="META", pr_branch=branch)
        self.assertIn("verified", verify_pr(self.policy, self.base, head, branch, "coordinator-proof"))

    def test_later_service_run_can_repair_the_same_original_branch(self):
        head, _ = self.fixture(owner=OTHER)
        self.assertIn("verified", verify_pr(self.policy, self.base, head, BRANCH, "coordinator-proof"))

    def test_foreign_branch_claim_cannot_authorize_another_lane(self):
        head, _ = self.fixture(work_branch="auto/twf-game-repair-" + OTHER)
        with self.assertRaises(ValueError):
            verify_pr(self.policy, self.base, head, BRANCH, "coordinator-proof")

    def test_dangling_unpublished_claim_cannot_pass(self):
        head, _ = self.fixture()
        with self.assertRaises(subprocess.CalledProcessError):
            verify_pr(self.policy, self.base, head, BRANCH, self.base)

    def test_claim_owner_or_generation_cannot_be_forged(self):
        _, claim = self.fixture()
        proof = {"branch": "twf-repair-coordinator", "claim_commit": claim,
                 "owner_run_id": OTHER, "epoch": 1}
        self.write("history/C00099_control.json", {"coordination": proof})
        self.git("add", ".")
        self.git("commit", "-qm", "bad owner")
        with self.assertRaises(ValueError):
            verify_pr(self.policy, self.base, "HEAD", BRANCH, "coordinator-proof")

    def test_legacy_exemption_is_bound_to_exact_branch_and_head(self):
        self.policy["coordination"]["grandfathered_pr_heads"] = [{"branch": BRANCH, "head": self.base}]
        self.assertIn("grandfathered", verify_pr(self.policy, self.base, self.base, BRANCH, "unused"))
        with self.assertRaises(ValueError):
            verify_pr(self.policy, self.base, self.base, "auto/twf-game-repair-" + OTHER, "unused")


if __name__ == "__main__":
    unittest.main()
