"""New current-record contract tests; synthetic evidence never authenticates a host."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
try:
    import system_integration_contract as target
except ModuleNotFoundError as ex:
    if ex.name != "system_integration_contract":
        raise
    target = None

MERGE = "a" * 40
MAIN = "b" * 40
HEAD = "c" * 40


def fixture(repo="owner/game-one"):
    def job(i, name, run):
        return dict(id=i, name=name, head=MERGE, run_id=run,
                    run_attempt=1, status="completed", conclusion="success")
    tail = dict(pr=137, head=HEAD, merge_sha=MERGE, main_qa=1001,
                handoff=1002, main_after_handoff=MAIN, details={"preserve": [1, 2]})
    old = dict(schema=1, repository=repo, merged_prs=[
        dict(pr=124, details={"old": True}), dict(pr=136, payload=[1, {"x": "old"}]), tail],
        latest_review=dict(pr=137, head=HEAD, merge_sha=MERGE),
        merge_sha=MERGE, main_after_merge=MERGE, main_after_handoff=MAIN,
        latest_main_sha=MAIN, main_qa=1001, handoff=1002,
        historical_snapshot={"scope": "OLD_AUDIT_ONLY", "main_qa": 99, "handoff": 98},
        compatibility_repair={"keep": ["prior"]}, old_key={"unchanged": True})
    after = copy.deepcopy(old)
    after["main_qa"] = dict(id=1001, head=MERGE, status="completed", conclusion="success",
        attempt=1, url=f"https://github.com/{repo}/actions/runs/1001",
        jobs={"offline": "success", "compile_hold": "success"},
        job_evidence=[job(201, "offline", 1001), job(202, "compile_hold", 1001)])
    after["handoff"] = dict(id=1002, head=MERGE, status="completed", conclusion="success",
        attempt=1, url=f"https://github.com/{repo}/actions/runs/1002",
        jobs=[job(203, "update", 1002)])
    comparison = dict(base_commit={"sha": MERGE}, status="ahead", ahead_by=1,
        behind_by=0, total_commits=1, commits=[{"sha": MAIN}],
        files=[{"filename": "status/CHAT_HANDOFF.md", "status": "modified"},
               {"filename": "status/LATEST_STATE.json", "status": "modified"}])
    return old, after, comparison


class IntegrationContract(unittest.TestCase):
    def setUp(self):
        self.before, self.after, self.compare = fixture()

    def check(self, repo="owner/game-one"):
        self.assertIsNotNone(target, "accepted main lacks the integration receipt contract")
        result = target.check_transition(self.before, self.after, repository=repo,
                                         comparison=self.compare)
        self.assertEqual(result["verification"], "NOT_VERIFIED")
        for flag in ("write_allowed", "start_now_allowed", "takeover_allowed",
                     "dispatch_allowed", "merge_allowed", "publish_allowed",
                     "external_spend_allowed", "github_cas_performed"):
            self.assertIs(result[flag], False)
        return result

    def blocked(self):
        self.assertEqual(self.check()["status"], "BLOCKED_LEDGER_CONTRACT")

    def test_restore_current_objects_preserves_historical_numeric_snapshot(self):
        saved = copy.deepcopy((self.before, self.after, self.compare))
        ans = self.check()
        self.assertEqual(ans["status"], "CONTRACT_PASS_UNTRUSTED_EVIDENCE")
        self.assertEqual(ans["historical_rows_preserved"], 3)
        self.assertEqual(saved, (self.before, self.after, self.compare))

    def test_numeric_main_qa_regression(self):
        self.after["main_qa"] = 1001
        self.blocked()

    def test_numeric_handoff_regression(self):
        self.after["handoff"] = 1002
        self.blocked()

    def test_jobs_must_be_dictionary(self):
        self.after["main_qa"]["jobs"] = ["offline", "compile_hold"]
        self.blocked()

    def test_missing_required_qa_job(self):
        del self.after["main_qa"]["jobs"]["compile_hold"]
        self.blocked()

    def test_failed_run(self):
        self.after["main_qa"]["conclusion"] = "failure"
        self.blocked()

    def test_pending_job(self):
        self.after["main_qa"]["job_evidence"][0]["status"] = "in_progress"
        self.blocked()

    def test_wrong_job_run_id(self):
        self.after["main_qa"]["job_evidence"][0]["run_id"] = 1002
        self.blocked()

    def test_wrong_job_attempt(self):
        self.after["handoff"]["jobs"][0]["run_attempt"] = 2
        self.blocked()

    def test_wrong_job_head(self):
        self.after["main_qa"]["job_evidence"][0]["head"] = "d" * 40
        self.blocked()

    def test_boolean_run_id(self):
        self.after["main_qa"]["id"] = True
        self.blocked()

    def test_float_attempt(self):
        self.after["handoff"]["attempt"] = 1.0
        self.blocked()

    def test_duplicate_job_ids_across_runs(self):
        self.after["handoff"]["jobs"][0]["id"] = 201
        self.blocked()

    def test_duplicate_job_names(self):
        self.after["main_qa"]["job_evidence"][1]["name"] = "offline"
        self.blocked()

    def test_historical_rewrite(self):
        self.after["merged_prs"][0]["details"]["old"] = False
        self.blocked()

    def test_historical_bool_float_alias(self):
        self.before["merged_prs"][0]["details"]["old"] = 1
        self.after["merged_prs"][0]["details"]["old"] = 1.0
        self.blocked()

    def test_history_deleted(self):
        self.after["merged_prs"].pop(0)
        self.blocked()

    def test_history_reordered(self):
        self.after["merged_prs"][:2] = reversed(self.after["merged_prs"][:2])
        self.blocked()

    def test_duplicate_pr(self):
        self.after["merged_prs"].append(copy.deepcopy(self.after["merged_prs"][-1]))
        self.blocked()

    def test_required_old_root_key_deleted(self):
        del self.after["old_key"]
        self.blocked()

    def test_historical_snapshot_must_not_be_rewritten(self):
        self.after["historical_snapshot"]["main_qa"] = 1001
        self.blocked()

    def test_stale_latest_review(self):
        self.after["latest_review"]["head"] = "d" * 40
        self.blocked()

    def test_cross_repository_url(self):
        self.after["main_qa"]["url"] = "https://github.com/other/game/actions/runs/1001"
        self.blocked()

    def test_non_status_descendant(self):
        self.compare["files"][0]["filename"] = "src/Game.lua"
        self.blocked()

    def test_wrong_compare_base(self):
        self.compare["base_commit"]["sha"] = "d" * 40
        self.blocked()

    def test_wrong_compare_latest_main(self):
        self.compare["commits"][-1]["sha"] = "d" * 40
        self.blocked()

    def test_second_game_uses_its_own_binding(self):
        self.before, self.after, self.compare = fixture("another-org/second-game")
        self.assertEqual(self.check("another-org/second-game")["status"],
                         "CONTRACT_PASS_UNTRUSTED_EVIDENCE")

    def test_one_new_detailed_adoption_is_allowed(self):
        tail = copy.deepcopy(self.after["merged_prs"][-1])
        tail["pr"] = 140
        self.after["merged_prs"].append(tail)
        self.after["latest_review"]["pr"] = 140
        self.assertEqual(self.check()["appended_rows"], 1)

    def test_two_new_adoptions_not_one_operation(self):
        for pr in (140, 141):
            tail = copy.deepcopy(self.after["merged_prs"][-1])
            tail["pr"] = pr
            self.after["merged_prs"].append(tail)
        self.after["latest_review"]["pr"] = 141
        self.blocked()

    def test_json_malformed_or_nan_never_passes(self):
        self.after["old_key"]["bad"] = float("nan")
        self.blocked()


if __name__ == "__main__":
    unittest.main()
