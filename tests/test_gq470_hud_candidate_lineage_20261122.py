"""Current PR lineage tests; synthetic metadata is never engine evidence."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hud_lineage", ROOT / "quality_gameplay/gq470_hud_labels_real69_20261120/verify_candidate_lineage.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

LIVE = "18e4b04eb550ebf5195c3e287f97076dd9c92b6e"
HEAD = "894cad8b50db4ddfb43e83ec6e53b00297ad681a"
MERGE = "e731c9d0fe999b72ac54c90203b8b6208434c522"
OTHER = "a" * 40


def comparison(base, head):
    return {"status": "identical" if base == head else "ahead",
            "base_commit": {"sha": base}, "merge_base_commit": {"sha": base}}


def fixture():
    env = {"GITHUB_REPOSITORY": gate.REPOSITORY, "GITHUB_EVENT_NAME": "pull_request",
           "GITHUB_SHA": MERGE, "GITHUB_REF": "refs/pull/1013/merge"}
    event = {"repository": {"full_name": gate.REPOSITORY}, "number": 1013,
             "pull_request": {"number": 1013,
                              "base": {"ref": gate.CANONICAL_BRANCH, "sha": LIVE,
                                       "repo": {"full_name": gate.REPOSITORY}},
                              "head": {"sha": HEAD, "repo": {"full_name": gate.REPOSITORY}}}}
    return dict(env=env, event=event, live_head=LIVE,
                author_lineage=comparison(gate.AUTHOR_BASE, LIVE),
                head_lineage=comparison(LIVE, HEAD),
                build_commit={"sha": MERGE, "parents": [{"sha": LIVE}, {"sha": HEAD}]},
                checkout_sha=MERGE)


class LineageTests(unittest.TestCase):
    def reject(self, mutate, message):
        case = fixture()
        mutate(case)
        with self.assertRaisesRegex(gate.LineageError, message):
            gate.verify(**case)

    def test_current_descendant_pr_preserves_old_author_pin(self):
        result = gate.verify(**fixture())
        self.assertEqual(result["immutable_author_base"], gate.AUTHOR_BASE)
        self.assertEqual(result["observed_canonical_head"], LIVE)
        self.assertEqual(result["candidate_source_head"], HEAD)
        self.assertEqual(result["actual_checkout_head"], MERGE)
        self.assertFalse(result["formal_rc_adoption_proven"])
        self.assertFalse(result["prepared_output_is_current_rc_game"])

    def test_original_author_base_itself_is_valid_ancestor(self):
        x = fixture()
        x["live_head"] = gate.AUTHOR_BASE
        x["event"]["pull_request"]["base"]["sha"] = gate.AUTHOR_BASE
        x["author_lineage"] = comparison(gate.AUTHOR_BASE, gate.AUTHOR_BASE)
        x["head_lineage"] = comparison(gate.AUTHOR_BASE, HEAD)
        x["build_commit"]["parents"][0]["sha"] = gate.AUTHOR_BASE
        self.assertEqual(gate.verify(**x)["observed_canonical_head"], gate.AUTHOR_BASE)

    def test_canonical_dispatch_is_still_only_historical_prep(self):
        x = fixture()
        x["env"].update(GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_SHA=LIVE,
                         GITHUB_REF="refs/heads/" + gate.CANONICAL_BRANCH)
        x["event"] = {"repository": {"full_name": gate.REPOSITORY}}
        x["head_lineage"] = None
        x["build_commit"] = {"sha": LIVE, "parents": [{"sha": gate.AUTHOR_BASE}]}
        x["checkout_sha"] = LIVE
        result = gate.verify(**x)
        self.assertIsNone(result["pull_request"])
        self.assertFalse(result["formal_rc_adoption_proven"])

    def test_stale_pr_base_rejected(self):
        self.reject(lambda x: x["event"]["pull_request"]["base"].update(sha=OTHER), "STALE_PR_BASE")

    def test_wrong_author_lineage_rejected(self):
        self.reject(lambda x: x["author_lineage"].update(status="diverged"), "AUTHOR_NOT_DESCENDANT")

    def test_wrong_author_compare_base_rejected(self):
        self.reject(lambda x: x["author_lineage"]["base_commit"].update(sha=OTHER), "AUTHOR_WRONG_BASE")

    def test_wrong_author_merge_base_rejected(self):
        self.reject(lambda x: x["author_lineage"]["merge_base_commit"].update(sha=OTHER), "AUTHOR_DIVERGENT")

    def test_pr_head_must_descend_from_live_base(self):
        self.reject(lambda x: x["head_lineage"].update(status="diverged"), "PR_HEAD_NOT_DESCENDANT")

    def test_pr_head_compare_cannot_substitute_another_base(self):
        self.reject(lambda x: x["head_lineage"]["base_commit"].update(sha=OTHER), "PR_HEAD_WRONG_BASE")

    def test_pr_synthetic_merge_parents_must_match(self):
        self.reject(lambda x: x["build_commit"]["parents"][1].update(sha=OTHER), "SYNTHETIC_MERGE_PARENTS")

    def test_actual_checkout_must_match_build(self):
        self.reject(lambda x: x.update(checkout_sha=HEAD), "CHECKOUT_SHA_MISMATCH")

    def test_build_commit_must_match_build(self):
        self.reject(lambda x: x["build_commit"].update(sha=OTHER), "BUILD_COMMIT_MISMATCH")

    def test_wrong_pr_number_or_ref_rejected(self):
        self.reject(lambda x: x["env"].update(GITHUB_REF="refs/pull/1012/merge"), "WRONG_PR_REF")
        self.reject(lambda x: x["event"].update(number=True), "INVALID_PULL_REQUEST_NUMBER")

    def test_wrong_repository_or_fork_rejected(self):
        self.reject(lambda x: x["env"].update(GITHUB_REPOSITORY="other/repo"), "WRONG_REPOSITORY")
        self.reject(lambda x: x["event"]["pull_request"]["head"]["repo"].update(full_name="other/repo"), "WRONG_PR_REPOSITORY")

    def test_wrong_base_branch_rejected(self):
        self.reject(lambda x: x["event"]["pull_request"]["base"].update(ref="main"), "WRONG_PR_BASE_BRANCH")

    def test_malformed_sha_rejected(self):
        self.reject(lambda x: x["event"]["pull_request"]["head"].update(sha="HEAD"), "INVALID_SHA_PR_HEAD")

    def test_dispatch_outside_canonical_rejected(self):
        self.reject(lambda x: x["env"].update(GITHUB_EVENT_NAME="workflow_dispatch"), "DISPATCH_NOT_CANONICAL")

    def test_unsupported_event_rejected(self):
        self.reject(lambda x: x["env"].update(GITHUB_EVENT_NAME="push"), "UNSUPPORTED_EVENT")

    def test_live_head_movement_during_api_checks_rejected(self):
        x = fixture()
        replies = [{"object": {"sha": LIVE}}, x["author_lineage"], x["head_lineage"],
                   x["build_commit"], {"object": {"sha": OTHER}}]
        with patch.object(gate, "api", side_effect=replies), patch.object(
                gate.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, MERGE + "\n")):
            with self.assertRaisesRegex(gate.LineageError, "CANONICAL_HEAD_MOVED"):
                gate.run_live(x["env"], x["event"])

    def test_api_failure_cannot_produce_success_receipt(self):
        x = fixture()
        with patch.object(gate, "api", side_effect=subprocess.CalledProcessError(1, ["gh", "api"])):
            with self.assertRaises(subprocess.CalledProcessError):
                gate.run_live(x["env"], x["event"])

    def test_workflow_keeps_all_original_source_and_recovery_gates(self):
        text = (ROOT / ".github/workflows/gq470-hud-tool-display-real69-prep.yml").read_text()
        for fragment in ("44673605213", gate.AUTHOR_BASE, "--self-test", "--count 69",
                         "cmp /tmp/GQ470_HUD_OFF69_ROLLBACK_PRIVATE.rbxlx",
                         "assert len(families)==17", "audit_legacy48.py --base",
                         "verify_candidate_lineage.py", "HUD_CANDIDATE_LINEAGE_RECEIPT.json"):
            self.assertIn(fragment, text)
        self.assertNotIn("STALE_PARENT_NO_ADMISSION", text)


if __name__ == "__main__":
    unittest.main()
