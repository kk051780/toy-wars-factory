"""PR144 child: require exact protected GitHub workflow path, including @refs/heads/main.

These are synthetic API fixtures: passing cases do NOT authenticate GitHub.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from github_artifact_admission import (
    REPO, WORKFLOW, ARTIFACT, AdmissionError, Expected, verify_metadata,
)

SHA = "a" * 40
RUN = 123456789
ART = 987654321

def fixture(path=None):
    if path is None:
        path = WORKFLOW + "@refs/heads/main"
    run = {
        "id": RUN, "head_sha": SHA, "head_branch": "main",
        "event": "workflow_dispatch", "status": "completed",
        "conclusion": "success", "run_attempt": 1,
        "repository": {"full_name": REPO}, "path": path,
    }
    jobs = {"total_count": 1, "jobs": [
        {"id": 4321, "name": "rojo-build-only", "run_id": RUN,
         "run_attempt": 1, "head_sha": SHA, "status": "completed",
         "conclusion": "success"},
    ]}
    artifacts = {"total_count": 1, "artifacts": [{
        "id": ART, "name": ARTIFACT, "expired": False,
        "size_in_bytes": 1234, "digest": "sha256:" + "f" * 64,
        "workflow_run": {"id": RUN, "head_sha": SHA, "head_branch": "main"},
    }]}
    return run, jobs, artifacts

class ExactWorkflowRefTests(unittest.TestCase):
    def verify(self, path):
        return verify_metadata(Expected(SHA, RUN, ART), *fixture(path))

    def rejected(self, path):
        with self.assertRaises(AdmissionError):
            self.verify(path)

    def test_protected_main_workflow_still_admitted_as_untrusted(self):
        result = self.verify(WORKFLOW + "@refs/heads/main")
        self.assertEqual(result["source_sha"], SHA)
        self.assertFalse(result["provider_authenticated"])

    def test_wrong_branch_suffix_rejected(self):
        self.rejected(WORKFLOW + "@refs/heads/unreviewed")

    def test_wrong_tag_suffix_rejected(self):
        self.rejected(WORKFLOW + "@refs/tags/v1")

    def test_pull_request_suffix_rejected(self):
        self.rejected(WORKFLOW + "@refs/pull/17/merge")

    def test_bare_workflow_path_matches_observed_github_rest_shape(self):
        # Connected Actions REST exposes bare path for actual workflow runs.
        # head_branch=main, event=workflow_dispatch, and exact SHA are verified separately.
        result = self.verify(WORKFLOW)
        self.assertFalse(result["provider_authenticated"])

    def test_empty_ref_suffix_rejected(self):
        self.rejected(WORKFLOW + "@")

    def test_main_prefix_extra_segment_rejected(self):
        self.rejected(WORKFLOW + "@refs/heads/main/unreviewed")

    def test_main_prefix_extra_at_rejected(self):
        self.rejected(WORKFLOW + "@refs/heads/main@refs/heads/unreviewed")

    def test_bogus_url_encoded_main_rejected(self):
        self.rejected(WORKFLOW + "@refs%2Fheads%2Fmain")

    def test_wrong_workflow_with_main_rejected(self):
        self.rejected(".github/workflows/unreviewed.yml@refs/heads/main")

    def test_wrong_case_main_rejected(self):
        self.rejected(WORKFLOW + "@refs/heads/Main")

if __name__ == "__main__":
    unittest.main()
