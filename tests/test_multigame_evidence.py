"""P2 fail-closed proof: provider responses never grant dispatch or game release."""
import base64
import copy
import json
from pathlib import Path
import unittest

from studio_autopilot.core import InvalidProject, validate_project
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
            "contents/.github/workflows/bootstrap-quality.yml?ref=" + MAIN: self.workflow_file(),
            "contents/.github/workflows/bootstrap-quality.yml?ref=" + HEAD: self.workflow_file(),
            "actions/runs/11": self.run(MAIN, 101, "push"),
            "actions/runs/22": self.run(HEAD, 202, "pull_request"),
            "actions/jobs/1100": self.job(MAIN, 11, "offline", 501, 1100),
            "actions/jobs/1101": self.job(MAIN, 11, "compile_hold", 502, 1101),
            "actions/jobs/2200": self.job(HEAD, 22, "offline", 601, 2200),
            "actions/jobs/2201": self.job(HEAD, 22, "compile_hold", 602, 2201),
        }
        self.counter = {}

    @staticmethod
    def good_checks(sha):
        is_main = (sha == MAIN)
        run_id, suite_id, first_job, first_check = (11, 101, 1100, 501) if is_main else (22, 202, 2200, 601)
        rows = [
            {
                "head_sha": sha, "name": name,
                "id": first_check + i,
                "status": "completed", "conclusion": "success",
                "app": {"slug": "github-actions", "id": 15368},
                "check_suite": {"id": suite_id},
                "details_url": "https://github.com/" + REPO +
                               "/actions/runs/" + str(run_id) + "/job/" + str(first_job + i),
            }
            for i, name in enumerate(("offline", "compile_hold"))
        ]
        return {"total_count": len(rows), "check_runs": rows}

    @staticmethod
    def run(sha, suite_id, event):
        return {
            "workflow_id": 394718989,
            "path": ".github/workflows/bootstrap-quality.yml",
            "head_sha": sha, "check_suite_id": suite_id,
            "status": "completed", "conclusion": "success", "event": event,
        }

    @staticmethod
    def job(sha, run_id, name, check_id, job_id):
        return {
            "id": job_id, "run_id": run_id,
            "name": name, "head_sha": sha,
            "status": "completed", "conclusion": "success",
            "check_run_url": API_ORIGIN + "/repos/" + REPO +
                             "/check-runs/" + str(check_id),
        }

    @staticmethod
    def workflow_file():
        return {"type": "file", "path": PROJECT["ci_provenance"]["workflow_path"],
                "sha": PROJECT["ci_provenance"]["workflow_blob_sha"]}

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

    def test_fake_app_same_name_and_sha_fails_closed(self):
        self.fake.responses["commits/" + HEAD + "/check-runs?per_page=100"][
            "check_runs"][0]["app"]["id"] = 99999
        self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_spoofed_workflow_run_with_same_sha_is_rejected(self):
        self.fake.responses["actions/runs/22"]["path"] = ".github/workflows/attacker.yml"
        self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_forged_run_head_sha_or_suite_is_rejected(self):
        for field, value in (("head_sha", "f" * 40), ("check_suite_id", 1234)):
            with self.subTest(field=field):
                old = self.fake.responses["actions/runs/22"][field]
                self.fake.responses["actions/runs/22"][field] = value
                self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
                self.fake.responses["actions/runs/22"][field] = old

    def test_fake_details_url_cannot_send_token_to_unsafe_host(self):
        self.fake.responses["commits/" + HEAD + "/check-runs?per_page=100"][
            "check_runs"][0]["details_url"] = "https://evil.invalid/capture"
        self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
        self.assertTrue(all(url.startswith(self.fake.path_prefix) for url in self.fake.calls))

    def test_run_not_complete_or_wrong_event_is_rejected(self):
        for field, value in (("conclusion", "failure"), ("status", "in_progress"),
                             ("event", "workflow_dispatch")):
            with self.subTest(field=field):
                old = self.fake.responses["actions/runs/22"][field]
                self.fake.responses["actions/runs/22"][field] = value
                self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
                self.fake.responses["actions/runs/22"][field] = old

    def test_provenance_cannot_be_invented_by_unbound_template(self):
        altered = copy.deepcopy(TEMPLATE)
        altered["ci_provenance"] = {
            "workflow_path": ".github/workflows/bootstrap-quality.yml",
            "app_slug": "github-actions", "app_id": 15368,
        }
        with self.assertRaises(InvalidProject):
            validate_project(altered)

    def test_manifest_rejects_untrusted_or_missing_ci_origin(self):
        for trust in (None, {},
                      {"workflow_path": ".github/workflows/evil.yml",
                       "app_slug": "other-app", "app_id": 15368},
                      {"workflow_path": "../arbitrary.yml",
                       "app_slug": "github-actions", "app_id": 15368},
                      {"workflow_path": ".github/workflows/bootstrap-quality.yml",
                       "app_slug": "github-actions", "app_id": True}):
            with self.subTest(trust=trust):
                altered = copy.deepcopy(PROJECT)
                altered["ci_provenance"] = trust
                with self.assertRaises(InvalidProject):
                    validate_project(altered)

    def test_tokened_workflow_runs_only_from_trusted_main(self):
        wf = (ROOT / ".github/workflows/studio-autopilot-evidence.yml").read_text(encoding="utf-8")
        self.assertIn('on:\n  push:\n    branches: ["main"]', wf)
        self.assertNotIn("\n  pull_request:", wf)
        self.assertNotIn("workflow_dispatch:", wf)
        self.assertIn('ref: ${{ github.sha }}', wf)
        self.assertIn('test "$(git rev-parse HEAD)" = "${{ github.sha }}"', wf)
        self.assertIn("  actions: read", wf)

    def test_forged_job_id_cannot_pass(self):
        # Correct workflow ID, suite and SHA; job ID alone is nonexistent.
        original = self.fake.responses["commits/" + HEAD + "/check-runs?per_page=100"][
            "check_runs"][0]["details_url"]
        self.fake.responses["commits/" + HEAD + "/check-runs?per_page=100"][
            "check_runs"][0]["details_url"] = original.replace("/job/2200", "/job/999999")
        with self.assertRaises(EvidenceUnavailable):
            self.read()

    def test_wrong_real_job_name_or_run_id_cannot_pass(self):
        job = self.fake.responses["actions/jobs/2200"]
        for field, bad in (("name", "compile_hold"), ("run_id", 11)):
            old = job[field]
            job[field] = bad
            self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
            job[field] = old

    def test_foreign_check_run_url_and_job_sha_cannot_pass(self):
        job = self.fake.responses["actions/jobs/2200"]
        for field, bad in (("check_run_url", "https://api.github.com/repos/evil/repo/check-runs/601"),
                           ("head_sha", "f" * 40),
                           ("conclusion", "failure")):
            old = job[field]
            job[field] = bad
            self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
            job[field] = old

    def test_forged_trusted_workflow_id_rejected(self):
        run = self.fake.responses["actions/runs/22"]
        run["workflow_id"] = 394718990
        self.assertEqual(self.read()["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_main_qa_must_be_push_and_not_pr_success(self):
        self.fake.responses["actions/runs/11"]["event"] = "pull_request"
        report = self.read()
        self.assertEqual(report["main"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
        self.assertEqual(report["pr"]["checks"]["status"], "PASS")
        self.assertFalse(report["execution"]["merge_allowed"])

    def test_pr_qa_must_be_pr_and_not_push_success(self):
        self.fake.responses["actions/runs/22"]["event"] = "push"
        report = self.read()
        self.assertEqual(report["main"]["checks"]["status"], "PASS")
        self.assertEqual(report["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")

    def test_modified_workflow_in_pr_with_real_successful_jobs_refused(self):
        key = "contents/.github/workflows/bootstrap-quality.yml?ref=" + HEAD
        self.fake.responses[key]["sha"] = "f" * 40
        result = self.read()
        self.assertEqual(result["main"]["checks"]["status"], "PASS")
        self.assertEqual(result["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
        self.assertEqual(result["pr"]["checks"]["reason"], "TRUSTED_QA_WORKFLOW_CONTENT_CHANGED")

    def test_modified_main_workflow_cannot_prove_main_qa(self):
        key = "contents/.github/workflows/bootstrap-quality.yml?ref=" + MAIN
        self.fake.responses[key]["sha"] = "f" * 40
        result = self.read()
        self.assertEqual(result["main"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
        self.assertEqual(result["pr"]["checks"]["status"], "PASS")

    def test_missing_or_fake_trusted_workflow_blob_refused(self):
        for bad in (None, True, "x" * 40, ["bad"]):
            with self.subTest(value=bad):
                candidate = copy.deepcopy(PROJECT)
                candidate["ci_provenance"]["workflow_blob_sha"] = bad
                if bad == "x" * 40:
                    result = collect(candidate, self.fake.client(), pr_number=51)
                    self.assertEqual(result["pr"]["checks"]["status"], "HOLD_EXACT_HEAD_CHECKS")
                else:
                    with self.assertRaises(InvalidProject):
                        validate_project(candidate)

    def test_workflow_blob_is_fetched_at_exact_main_and_pr_head(self):
        self.read()
        expected = [
            self.fake.path_prefix + "contents/.github/workflows/bootstrap-quality.yml?ref=" + sha
            for sha in (MAIN, HEAD)
        ]
        for url in expected:
            self.assertIn(url, self.fake.calls)

    def test_the_reader_does_not_depend_on_planner_json_claims(self):
        payload = self.read()
        self.assertEqual(payload["main"]["sha"], MAIN)
        self.assertFalse(payload["execution"]["merge_allowed"])
        self.assertFalse(payload["execution"]["publish_allowed"])


if __name__ == "__main__":
    unittest.main()
