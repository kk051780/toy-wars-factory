"""P2 fail-closed proof: provider responses never grant dispatch or game release."""
import base64
import copy
import json
from pathlib import Path
import unittest

from studio_autopilot.github_evidence import (
    API_ORIGIN, EvidenceUnavailable, GitHubReadOnlyClient, _NoRedirect,
    collect,
)

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "studio_autopilot/projects/toy_wars.json").read_text(encoding="utf-8"))
TEMPLATE = json.loads((ROOT / "studio_autopilot/projects/skyline_parkour_template.json").read_text(encoding="utf-8"))
REPO = PROJECT["repository"]
MAIN = "a" * 40
COORD = "b" * 40
HEAD = "c" * 40
TOKEN = "test-only-token-must-never-appear"


class FakeGitHub:
    def __init__(self):
        self.calls = []
        self.path_prefix = API_ORIGIN + "/repos/" + REPO + "/"
        coord = {
            "epoch": 25,
            "holder": None,
            "authorized_tasks": {
                "WORKER": PROJECT["roles"]["author"],
                "REVIEWER": PROJECT["roles"]["reviewer"],
                "META": PROJECT["roles"]["meta"],
            },
        }
        self.responses = {
            "git/ref/heads/main": {"ref": "refs/heads/main", "object": {"sha": MAIN}},
            "git/ref/heads/twf-repair-coordinator": {
                "ref": "refs/heads/twf-repair-coordinator", "object": {"sha": COORD}},
            "commits/" + MAIN + "/check-runs?per_page=100": self.good_checks(MAIN),
            "commits/" + HEAD + "/check-runs?per_page=100": self.good_checks(HEAD),
            "contents/ops/REPAIR_COORDINATOR.json?ref=" + COORD: self.encode(coord),
            "pulls/51": self.pr(),
        }
        self.counter = {}

    @staticmethod
    def good_checks(sha):
        rows = [{"head_sha": sha, "name": name,
                 "status": "completed", "conclusion": "success"}
                for name in ("offline", "compile_hold")]
        return {"total_count": len(rows), "check_runs": rows}

    @staticmethod
    def encode(doc):
        return {"encoding": "base64", "content": base64.b64encode(
            json.dumps(doc).encode("utf-8")).decode("ascii")}

    @staticmethod
    def pr():
        return {
            "number": 51, "state": "open", "draft": True,
            "head": {"sha": HEAD, "repo": {"full_name": REPO}},
            "base": {"sha": MAIN, "ref": "main", "repo": {"full_name": REPO}},
        }

    def fetch(self, url, token):
        self.calls.append(url)
        if token != TOKEN or not url.startswith(self.path_prefix):
            raise EvidenceUnavailable("test cross-repo URL or token mismatch")
        path = url[len(self.path_prefix):]
        self.counter[path] = self.counter.get(path, 0) + 1
        if path not in self.responses:
            raise EvidenceUnavailable("unexpected requested path")
        return copy.deepcopy(self.responses[path])

    def client(self):
        return GitHubReadOnlyClient(REPO, TOKEN, http_fetch=self.fetch)


class EvidenceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeGitHub()

    def read(self, number=51):
        return collect(PROJECT, self.fake.client(), pr_number=number)

    def test_real_shape_success_remains_advisory(self):
        report = self.read()
        self.assertEqual(report["repository"], REPO)
        self.assertEqual(report["main"]["sha"], MAIN)
        self.assertEqual(report["main"]["checks"]["status"], "PASS")
        self.assertEqual(report["pr"]["checks"]["status"], "PASS")
        self.assertTrue(report["coordinator"]["task_identities_match"])
        self.assertEqual(report["source"], "AUTHENTICATED_GITHUB_API_READ_ONLY")
        self.assertEqual(report["scope"], "LIVE_REPOSITORY_METADATA_ONLY_NO_ENGINE_OR_PLAYTEST")
        self.assertEqual(report["coordinator"]["lease_observation"], "IDLE_AT_READ")
        self.assertTrue(all(value is False for value in report["execution"].values()))
        self.assertNotIn(TOKEN, json.dumps(report))

    def test_every_network_call_gets_exact_one_repo_only(self):
        self.read()
        self.assertTrue(self.fake.calls)
        self.assertTrue(all(path.startswith(self.fake.path_prefix) for path in self.fake.calls))
        self.assertEqual(self.fake.counter["git/ref/heads/main"], 2)
        self.assertEqual(self.fake.counter["git/ref/heads/twf-repair-coordinator"], 2)
        self.assertEqual(self.fake.counter["pulls/51"], 2)

    def test_read_only_without_a_pr(self):
        report = self.read(number=None)
        self.assertIsNone(report["pr"])
        self.assertNotIn("pulls/51", self.fake.counter)

    def test_unbound_template_cannot_query(self):
        with self.assertRaises(EvidenceUnavailable):
            collect(TEMPLATE, self.fake.client())

    def test_foreign_repo_client_rejected(self):
        other = GitHubReadOnlyClient("example/not-the-game", TOKEN, http_fetch=self.fake.fetch)
        with self.assertRaises(EvidenceUnavailable):
            collect(PROJECT, other)

    def test_missing_token_refused(self):
        with self.assertRaises(EvidenceUnavailable):
            GitHubReadOnlyClient(REPO, "")
        with self.assertRaises(EvidenceUnavailable):
            GitHubReadOnlyClient(REPO, None)

    def test_wrong_branch_identity_rejected(self):
        self.fake.responses["git/ref/heads/main"]["ref"] = "refs/heads/foreign"
        with self.assertRaises(EvidenceUnavailable):
            self.read()

    def test_main_ref_moving_mid_read_rejected(self):
        source = self.fake.fetch
        def moving(url, token):
            result = source(url, token)
            if url.endswith("/git/ref/heads/main") and self.fake.counter["git/ref/heads/main"] == 2:
                result["object"]["sha"] = "e" * 40
            return result
        with self.assertRaisesRegex(EvidenceUnavailable, "moved"):
            collect(PROJECT, GitHubReadOnlyClient(REPO, TOKEN, http_fetch=moving), pr_number=51)

    def test_coord_ref_moving_mid_read_rejected(self):
        source = self.fake.fetch
        def moving(url, token):
            result = source(url, token)
            path = "git/ref/heads/twf-repair-coordinator"
            if url.endswith(path) and self.fake.counter[path] == 2:
                result["object"]["sha"] = "e" * 40
            return result
        with self.assertRaisesRegex(EvidenceUnavailable, "moved"):
            collect(PROJECT, GitHubReadOnlyClient(REPO, TOKEN, http_fetch=moving))

    def test_pr_moving_mid_read_rejected(self):
        source = self.fake.fetch
        def moving(url, token):
            result = source(url, token)
            if url.endswith("/pulls/51") and self.fake.counter["pulls/51"] == 2:
                result["head"]["sha"] = "e" * 40
            return result
        with self.assertRaisesRegex(EvidenceUnavailable, "PR head/base moved"):
            collect(PROJECT, GitHubReadOnlyClient(REPO, TOKEN, http_fetch=moving), pr_number=51)

    def test_foreign_pr_head_denied(self):
        self.fake.responses["pulls/51"]["head"]["repo"]["full_name"] = "attacker/evil"
        with self.assertRaisesRegex(EvidenceUnavailable, "cross-repo"):
            self.read()

    def test_foreign_pr_base_denied(self):
        self.fake.responses["pulls/51"]["base"]["repo"]["full_name"] = "other/repo"
        with self.assertRaisesRegex(EvidenceUnavailable, "cross-repo"):
            self.read()

    def test_stale_base_is_reported_not_marked_current(self):
        self.fake.responses["pulls/51"]["base"]["sha"] = "d" * 40
        report = self.read()
        self.assertIs(report["pr"]["base_matches_main"], False)
        self.assertFalse(report["execution"]["merge_allowed"])

    def test_stale_pr_check_sha_rejected(self):
        check = self.fake.responses["commits/" + HEAD + "/check-runs?per_page=100"]
        check["check_runs"][0]["head_sha"] = "d" * 40
        with self.assertRaisesRegex(EvidenceUnavailable, "stale check-run"):
            self.read()

    def test_incomplete_pagination_cannot_mark_qa_pass(self):
        checks = self.fake.responses["commits/" + MAIN + "/check-runs?per_page=100"]
        checks["total_count"] = 3
        with self.assertRaises(EvidenceUnavailable):
            self.read()

    def test_missing_required_check_fails_closed(self):
        checks = self.fake.responses["commits/" + MAIN + "/check-runs?per_page=100"]
        checks["check_runs"] = checks["check_runs"][:1]
        checks["total_count"] = 1
        self.assertEqual(self.read()["main"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_failed_check_cannot_pass(self):
        self.fake.responses["commits/" + MAIN + "/check-runs?per_page=100"][
            "check_runs"][0]["conclusion"] = "failure"
        self.assertEqual(self.read()["main"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_pending_check_cannot_pass(self):
        self.fake.responses["commits/" + MAIN + "/check-runs?per_page=100"][
            "check_runs"][0]["status"] = "in_progress"
        self.assertEqual(self.read()["main"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_duplicated_check_cannot_pass(self):
        checks = self.fake.responses["commits/" + MAIN + "/check-runs?per_page=100"]
        checks["check_runs"].append(copy.deepcopy(checks["check_runs"][0]))
        checks["total_count"] += 1
        self.assertEqual(self.read()["main"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_cross_game_coord_task_mismatch_rejected(self):
        key = "contents/ops/REPAIR_COORDINATOR.json?ref=" + COORD
        self.fake.responses[key] = self.fake.encode({
            "epoch": 25, "holder": None, "authorized_tasks": {
                "WORKER": PROJECT["roles"]["author"],
                "META": PROJECT["roles"]["meta"],
                "REVIEWER": "0" * 32,
            }})
        with self.assertRaisesRegex(EvidenceUnavailable, "task identities mismatch"):
            self.read()

    def test_coordinator_no_holder_field_denied(self):
        key = "contents/ops/REPAIR_COORDINATOR.json?ref=" + COORD
        self.fake.responses[key] = self.fake.encode({
            "epoch": 25, "authorized_tasks": {
                "WORKER": PROJECT["roles"]["author"],
                "META": PROJECT["roles"]["meta"],
                "REVIEWER": PROJECT["roles"]["reviewer"],
            }})
        with self.assertRaises(EvidenceUnavailable):
            self.read()

    def test_occupied_lease_never_authorizes_parallel_work(self):
        key = "contents/ops/REPAIR_COORDINATOR.json?ref=" + COORD
        self.fake.responses[key] = self.fake.encode({
            "epoch": 25, "holder": {"kind": "REVIEWER", "owner_id": "another-run"},
            "authorized_tasks": {
                "WORKER": PROJECT["roles"]["author"],
                "META": PROJECT["roles"]["meta"],
                "REVIEWER": PROJECT["roles"]["reviewer"],
            }})
        report = self.read()
        self.assertEqual(report["coordinator"]["lease_observation"], "OCCUPIED_AT_READ")
        self.assertFalse(report["execution"]["dispatch_allowed"])

    def test_malformed_lease_json_refused(self):
        key = "contents/ops/REPAIR_COORDINATOR.json?ref=" + COORD
        self.fake.responses[key] = {"encoding": "base64", "content": "%%%"}
        with self.assertRaises(EvidenceUnavailable):
            self.read()

    def test_path_cannot_cross_repository_or_use_redirect(self):
        client = self.fake.client()
        for path in ("../other", "/repos/sneak", "http://evil.test/x", "git\\evil",
                     "git/ref/heads/main\nx"):
            with self.subTest(path=path):
                with self.assertRaises(EvidenceUnavailable):
                    client.get(path)
        with self.assertRaises(EvidenceUnavailable):
            _NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test")

    def test_invalid_pr_number_refused(self):
        for n in (True, -1, 0, "51", 10000001):
            with self.subTest(n=n):
                with self.assertRaises(EvidenceUnavailable):
                    self.read(n)

    def test_the_reader_does_not_depend_on_planner_json_claims(self):
        payload = self.read()
        self.assertEqual(payload["main"]["sha"], MAIN)
        self.assertFalse(payload["execution"]["merge_allowed"])
        self.assertFalse(payload["execution"]["publish_allowed"])


if __name__ == "__main__":
    unittest.main()
