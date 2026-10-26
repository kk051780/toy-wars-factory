"""Delegation removes human waits; it does not remove independent review/CI/leases."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import acquire, approval_packet, initial_state, render_approvals
from repair_integration import decide, REVIEW_CHECKS
from check_auto_diff import violations as game_violations
from check_meta_diff import safe_module_extension, violations as meta_violations

REVIEW_RUN = "00000000-0000-0000-0000-00000000a101"
AUTHOR_RUN = "039874ac-64a0-8323-bc57-5c35cf58ec90"
NOW = "2026-10-25T01:00:00Z"


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "config/autonomous_repair.json").read_text())
        task = self.policy["integration"]["task_id"]
        state = initial_state();state["authorized_tasks"]["REVIEWER"] = task
        self.lease = acquire(state, "REVIEWER", REVIEW_RUN, NOW, actor_task_id=task, work_branch="main")["state"]
        self.main = {"sha": "c" * 40, "qa_head": "c" * 40, "qa_conclusion": "success", "qa_url": "main-ci"}
        self.pr = {"number": 57, "repository": self.policy["repository"], "branch": self.policy["branch_prefix"] + AUTHOR_RUN,
                   "state": "open", "head": "b" * 40, "mergeable": True,
                   "author_task_id": self.policy["task_id"], "author_run_id": AUTHOR_RUN,
                   "ci": {"head": "b" * 40, "conclusion": "success", "required_jobs_passed": True, "scope_and_claim_gate": "PASS"}}
        self.review = {"reviewer_task_id": task, "reviewer_run_id": REVIEW_RUN, "lease_epoch": self.lease["epoch"],
                       "head": self.pr["head"], "base_main_sha": self.main["sha"], "reviewed_at": NOW,
                       "verdict": "APPROVE", "blockers": [], "checks": {name: True for name in REVIEW_CHECKS}}

    def decision(self, now=NOW):
        result = decide(self.policy, self.main, self.pr, self.review, self.lease, now)
        self.assertFalse(result["requires_owner_reply"])
        return result


    def enable_manual_candidate(self):
        branch = "feature/twf-hud-quickstart-20261026"
        owner = "a4b3ef83-814c-431c-97c9-d14e25c9c86f"
        claim = "d" * 40
        self.pr.update(number=58, branch=branch, author_task_id=None,
                       author_run_id=owner, changed_entries=[
                           ["A", "history/C00035_hud_quickstart.json"],
                           ["M", "src/ToyWarsHUD.client.lua"],
                           ["A", "tests/auto/hud_quickstart_spec.lua"]])
        self.lease["manual_review_requests"] = [{
            "number": 58, "repository": self.policy["repository"],
            "branch": branch, "head": self.pr["head"],
            "base_main_sha": self.main["sha"],
            "reviewer_task_id": self.policy["integration"]["task_id"],
            "kind": "CONTROLLER", "owner_id": owner,
            "epoch": 47, "claim_commit": claim}]
        self.pr["ci"]["scope_and_claim_gate"] = "MANUAL_CONTROLLER_ATTESTED"
        self.review["manual_provenance"] = {
            "claim_commit": claim, "epoch": 47, "owner_id": owner,
            "head": self.pr["head"], "base_main_sha": self.main["sha"],
            "branch": branch, "changed_entries": self.pr["changed_entries"],
            "claim_state": {"epoch": 47, "holder": {
                "kind": "CONTROLLER", "owner_id": owner, "epoch": 47,
                "base_main_sha": self.main["sha"], "work_branch": branch,
                "acquired_at": "2026-10-25T00:00:00Z",
                "expires_at": "2026-10-25T01:00:00Z"}},
            "claim_commit_verified": True, "main_ancestry_verified": True,
            "github_diff_verified": True, "ledger_verified": True,
            "ci_jobs_verified": True}
        return self.lease["manual_review_requests"][0]

    def test_manual_candidate_requires_exact_independent_evidence(self):
        self.enable_manual_candidate()
        self.assertEqual(self.decision()["action"], "MERGE")

    def test_manual_candidate_without_queue_request_is_rejected(self):
        self.enable_manual_candidate()
        self.lease.pop("manual_review_requests")
        self.assertEqual(self.decision()["action"], "WAIT_MANUAL_REQUEST")

    def test_manual_candidate_disallows_duplicate_or_forged_requests(self):
        request = self.enable_manual_candidate()
        self.lease["manual_review_requests"].append(copy.deepcopy(request))
        self.assertEqual(self.decision()["action"], "WAIT_MANUAL_REQUEST")
        self.lease["manual_review_requests"].pop()
        for key,value in (("claim_commit","bad"),("owner_id",REVIEW_RUN),
                          ("epoch",0),("head","a"*40),("base_main_sha","a"*40),
                          ("reviewer_task_id","untrusted")):
            replacement=copy.deepcopy(request)
            replacement[key]=value
            self.lease["manual_review_requests"][0]=replacement
            expected = "WAIT_AUTHOR_ID" if key == "owner_id" else "WAIT_MANUAL_REQUEST"
            self.assertEqual(self.decision()["action"], expected, key)
        self.lease["manual_review_requests"][0]=request

    def test_manual_candidate_requires_genuine_workflow_scope(self):
        self.enable_manual_candidate()
        for gate in ("PASS", "GRANDFATHERED_EXACT_HEAD", "SKIPPED", None):
            self.pr["ci"]["scope_and_claim_gate"] = gate
            self.assertEqual(self.decision()["action"], "WAIT_CI")
        self.pr["ci"]["scope_and_claim_gate"] = "MANUAL_CONTROLLER_ATTESTED"
        self.assertEqual(self.decision()["action"], "MERGE")

    def test_manual_candidate_scope_rejects_secret_policy_or_no_new_test(self):
        self.enable_manual_candidate()
        accepted=self.pr["changed_entries"]
        for entries in (accepted+[["M","config/autonomous_repair.json"]],
                        [["M","src/ToyWarsHUD.client.lua"]],
                        [["A","history/C00035_hud_quickstart.json"]],
                        [["M","src/ToyWarsHUD.client.lua"],["A","tests/auto/evil.lua"]],
                        [["M","src/ToyWarsHUD.client.lua"],["A","tests/auto/../secret_spec.lua"]]):
            self.pr["changed_entries"]=entries
            self.assertEqual(self.decision()["action"], "WAIT_MANUAL_SCOPE")
        self.pr["changed_entries"]=accepted

    def test_manual_candidate_needs_real_reviewer_provenance_fields(self):
        self.enable_manual_candidate()
        proof=self.review["manual_provenance"]
        for field in ("claim_commit_verified","main_ancestry_verified",
                      "github_diff_verified","ledger_verified","ci_jobs_verified"):
            proof[field]=False
            self.assertEqual(self.decision()["action"], "WAIT_MANUAL_PROOF",field)
            proof[field]=True
        for field in ("claim_commit","epoch","head","base_main_sha","branch","owner_id"):
            prior=proof[field];proof[field]=None
            self.assertEqual(self.decision()["action"],"WAIT_MANUAL_PROOF",field)
            proof[field]=prior
        proof["changed_entries"]=[]
        self.assertEqual(self.decision()["action"], "WAIT_MANUAL_PROOF")

    def test_manual_claim_snapshot_never_accepts_alias_wrong_owner_or_epoch(self):
        self.enable_manual_candidate()
        snapshot=self.review["manual_provenance"]["claim_state"]
        self.assertEqual(self.decision()["action"], "MERGE")
        for field,value in (("work_branch", "feature/twf-hud-quickstart"),
                            ("owner_id", REVIEW_RUN), ("epoch", 46),
                            ("kind","WORKER"), ("base_main_sha","a"*40),
                            ("expires_at","2026-10-25T00:00:00Z")):
            holder=snapshot["holder"]
            old=holder[field]
            holder[field]=value
            self.assertEqual(self.decision()["action"], "WAIT_MANUAL_PROOF",field)
            holder[field]=old
        snapshot["epoch"]=46
        self.assertEqual(self.decision()["action"], "WAIT_MANUAL_PROOF")
        snapshot["epoch"]=47
        del self.review["manual_provenance"]["claim_state"]
        self.assertEqual(self.decision()["action"], "WAIT_MANUAL_PROOF")

    def test_manual_candidate_stale_head_or_base_never_merges(self):
        self.enable_manual_candidate()
        self.pr["head"]="a"*40
        self.assertEqual(self.decision()["action"], "WAIT_MANUAL_REQUEST")
        self.pr["head"]="b"*40
        self.main["sha"]="a"*40
        # An incompatible tested-main identity must stop earlier than claim matching.
        self.assertEqual(self.decision()["action"], "WAIT_MAIN_CI")

    def test_manual_candidate_wrong_author_or_same_run_never_merges(self):
        self.enable_manual_candidate()
        self.pr["author_run_id"]=REVIEW_RUN
        self.assertEqual(self.decision()["action"], "WAIT_AUTHOR_ID")
        self.pr["author_run_id"]=self.lease["manual_review_requests"][0]["owner_id"]
        self.review["reviewer_run_id"]=self.pr["author_run_id"]
        self.assertEqual(self.decision()["action"], "WAIT_LOCK")

    def test_manual_candidate_legacy_worker_paths_still_reject_untrusted(self):
        self.enable_manual_candidate()
        self.pr["branch"]="feature/evil"
        self.assertEqual(self.decision()["action"], "SKIP_UNRELATED")

    def test_good_independent_review_merges_without_owner_reply(self):
        result = self.decision()
        self.assertEqual(result["action"], "MERGE")
        self.assertEqual(result["expected_head_sha"], self.pr["head"])
        self.assertTrue(result["post_merge_qa_required"])
        self.assertFalse(result["roblox_publish_authorized"])

    def test_missing_standing_authority_disables_integration(self):
        self.policy["approval_authority"]["owner_reply_required"] = True
        self.assertEqual(self.decision()["action"], "DISABLED")

    def test_author_run_cannot_approve_its_own_head(self):
        self.pr["author_run_id"] = REVIEW_RUN
        self.assertEqual(self.decision()["action"], "WAIT_INDEPENDENT_REVIEW")

    def test_missing_or_noncanonical_author_run_cannot_merge(self):
        self.pr.pop("author_run_id")
        self.assertEqual(self.decision()["action"], "WAIT_AUTHOR_ID")
        for value in ("not-a-run-uuid", AUTHOR_RUN.upper()):
            self.pr["author_run_id"] = value
            self.assertEqual(self.decision()["action"], "WAIT_AUTHOR_ID")

    def test_shared_registration_holder_and_policy_must_name_the_same_task(self):
        self.lease["authorized_tasks"]["REVIEWER"] = "different-task"
        self.lease["holder"]["task_id"] = "different-task"
        self.assertEqual(self.decision()["action"], "WAIT_LOCK")

    def test_unregistered_reviewer_or_wrong_generation_cannot_merge(self):
        self.review["lease_epoch"] += 1
        self.assertEqual(self.decision()["action"], "WAIT_LOCK")
        self.review["lease_epoch"] -= 1;self.review["reviewer_task_id"] = self.policy["task_id"]
        self.assertEqual(self.decision()["action"], "WAIT_LOCK")

    def test_expired_lease_never_merges(self):
        self.assertEqual(self.decision("2026-10-25T01:31:00Z")["action"], "WAIT_LOCK")

    def test_main_failure_or_pending_blocks_other_integrations(self):
        self.main["qa_conclusion"] = "failure"
        self.assertEqual(self.decision()["action"], "REPAIR_MAIN")
        self.main["qa_conclusion"] = None
        self.assertEqual(self.decision()["action"], "WAIT_MAIN_CI")

    def test_missing_or_malformed_main_identity_cannot_merge(self):
        for key in ("sha", "qa_head"):
            good = self.main[key]
            for value in (None, "not-a-sha"):
                self.main[key] = value
                self.review["base_main_sha"] = self.main["sha"]
                self.assertEqual(self.decision()["action"], "WAIT_MAIN_CI")
            self.main[key] = good
        self.review["base_main_sha"] = self.main["sha"]

    def test_verified_generated_status_descendant_can_reuse_main_qa(self):
        self.main["qa_head"] = "a" * 40
        self.main["comparison_since_qa"] = {"verified": True, "status": "ahead", "paths": ["status/LATEST_STATE.json"]}
        self.assertEqual(self.decision()["action"], "MERGE")
        self.main["comparison_since_qa"]["paths"].append("src/ToyWarsServer.server.lua")
        self.assertEqual(self.decision()["action"], "WAIT_MAIN_CI")

    def test_old_head_ci_and_missing_required_jobs_do_not_pass(self):
        self.pr["ci"]["head"] = "a" * 40
        self.assertEqual(self.decision()["action"], "WAIT_CI")
        self.pr["ci"]["head"] = self.pr["head"];self.pr["ci"]["required_jobs_passed"] = False
        self.assertEqual(self.decision()["action"], "WAIT_CI")

    def test_failed_pr_ci_is_sent_back_to_author(self):
        self.pr["ci"]["conclusion"] = "failure"
        self.assertEqual(self.decision()["action"], "REPAIR_CI")

    def test_claim_gate_cannot_be_skipped_for_a_new_head(self):
        self.pr["ci"]["scope_and_claim_gate"] = "SKIPPED"
        self.assertEqual(self.decision()["action"], "WAIT_CI")

    def test_review_of_old_head_or_main_is_not_reused(self):
        self.review["head"] = "a" * 40
        self.assertEqual(self.decision()["action"], "WAIT_REVIEW")
        self.review["head"] = self.pr["head"];self.review["base_main_sha"] = "a" * 40
        self.assertEqual(self.decision()["action"], "WAIT_REVIEW")

    def test_blockers_or_missing_review_dimensions_stop_merge(self):
        self.review["blockers"] = ["regression missing"]
        self.assertEqual(self.decision()["action"], "REQUEST_CHANGES")
        self.review["blockers"] = [];self.review["checks"]["regression"] = False
        self.assertEqual(self.decision()["action"], "WAIT_REVIEW")

    def test_unrelated_or_foreign_pr_and_unknown_mergeability_wait(self):
        self.pr["mergeable"] = None
        self.assertEqual(self.decision()["action"], "WAIT_METADATA")
        self.pr["mergeable"] = True;self.pr["repository"] = "foreign/fork"
        self.assertEqual(self.decision()["action"], "SKIP_UNRELATED")

    def test_delegated_packet_does_not_ask_owner_for_approval(self):
        item = {"number": 57, "title": "small fix", "repository": self.policy["repository"], "state": "open", "merged": False,
                "head": self.pr["head"], "ci_head": self.pr["head"], "ci": "success",
                "url": "https://github.com/" + self.policy["repository"] + "/pull/57",
                "ci_url": "https://github.com/" + self.policy["repository"] + "/actions/runs/1",
                "summary": "small verified repair", "changed_files": ["src/ToyWarsServer.server.lua"]}
        packet = approval_packet([item], self.policy["repository"], NOW, delegated=True)
        self.assertEqual(packet["approval_text"], "")
        rendered = render_approvals(packet)
        self.assertIn("所有者への承認返信は不要", rendered)
        self.assertNotIn("承認する場合の返信", rendered)

    def test_module_extension_preserves_policy_and_requires_installer_and_new_test(self):
        after = copy.deepcopy(self.policy);after["additional_source_paths"] = ["src/ToyWarsWave.lua"]
        entries = [("M", "config/autonomous_repair.json"), ("M", "tools/build_installer.py"), ("A", "tests/test_system_installer_module.py")]
        self.assertTrue(safe_module_extension(self.policy, after))
        self.assertEqual(meta_violations(entries, self.policy, module_extension=(self.policy, after)), [])
        self.assertTrue(meta_violations(entries[:1] + entries[2:], self.policy, module_extension=(self.policy, after)))
        after["automatic_merge_authorized"] = False
        self.assertFalse(safe_module_extension(self.policy, after))

    def test_only_explicit_additional_source_paths_can_be_added(self):
        entries = [("A", "src/ToyWarsWave.lua"), ("A", "tests/auto/wave_module_spec.lua")]
        self.assertTrue(game_violations(entries, self.policy))
        self.policy["additional_source_paths"] = ["src/ToyWarsWave.lua"]
        self.assertEqual(game_violations(entries, self.policy), [])
        self.assertTrue(game_violations(entries[:1], self.policy))


if __name__ == "__main__":
    unittest.main()
