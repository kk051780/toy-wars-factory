"""End-to-end continuity checks using real temporary Git history, no API calls."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HandoffCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("src", "config", "tools", "history"):
            shutil.copytree(ROOT / directory, self.root / directory,
                            ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(ROOT / "PROJECT_STATE.json", self.root / "PROJECT_STATE.json")
        self.git("init", "-q")
        self.git("config", "user.name", "Offline regression")
        self.git("config", "user.email", "test@local.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "Initial verification fixture")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

    def build(self):
        subprocess.run(["python3", "tools/build_handoff.py"], cwd=self.root,
                       check=True, capture_output=True, text=True)
        return json.loads((self.root / "status/LATEST_STATE.json").read_text())

    def test_failed_trial_and_unmerged_pr_origin_survive_generation(self):
        result = self.build()
        state = json.loads((self.root / "PROJECT_STATE.json").read_text())
        self.assertEqual(result["resume_checkpoint"], state["resume_checkpoint"])
        self.assertEqual(result["review_queue"], state["review_queue"])
        self.assertFalse(result["resume_checkpoint"]["authorization"]["new_inference_authorized"])
        proposal = next(item for item in result["review_queue"] if item["number"] == 17)
        self.assertEqual(proposal["origin"], "CHAT_ASSISTANT_NOT_GEMINI")
        self.assertEqual(proposal["status"], "DRAFT_UNMERGED")
        text = (self.root / "status/CHAT_HANDOFF.md").read_text()
        for value in (state["resume_checkpoint"]["id"], "PR #17", "CHAT_ASSISTANT_NOT_GEMINI", "新規推論承認: False"):
            self.assertIn(value, text)
        actual = sum(file.stat().st_size for file in (self.root / "src").glob("*.lua"))
        self.assertEqual(result["source_metrics"]["bytes"], actual)
        # The baseline is still enforced on main, but a review branch may
        # contain an explicitly recorded, unmerged gameplay integration.
        baseline = state["tracked_metrics"]["lua_source_bytes"]
        self.assertEqual(baseline, 25726)
        integration_file = self.root / "history/C00011_main_based_game_integration.json"
        if integration_file.exists():
            integration = json.loads(integration_file.read_text())
            changes = [item for item in integration["source_changes"]
                       if item["path"].startswith("src/") and item["path"].endswith(".lua")]
            self.assertEqual([item["path"] for item in changes],
                             ["src/ToyWarsServer.server.lua"])
            self.assertEqual(
                (self.root / changes[0]["path"]).stat().st_size,
                changes[0]["after_bytes"],
            )
            self.assertEqual(actual, baseline + sum(item["delta_bytes"] for item in changes))
        else:
            self.assertEqual(actual, baseline)

    def test_generated_snapshot_commit_is_stable_but_new_evidence_advances_revision(self):
        before = self.build()
        snapshots = {name: (self.root / "status" / name).read_bytes()
                     for name in ("CHAT_HANDOFF.md", "LATEST_STATE.json")}
        self.git("add", "status")
        self.git("commit", "-qm", "Only generated status")
        after = self.build()
        self.assertEqual(before["source_revision"], after["source_revision"])
        for name, data in snapshots.items():
            self.assertEqual((self.root / "status" / name).read_bytes(), data)
        (self.root / "history/new_evidence.json").write_text('{"offline":true}\n')
        self.git("add", "history/new_evidence.json")
        self.git("commit", "-qm", "Substantive new evidence")
        updated = self.build()
        self.assertEqual(updated["source_revision"], self.git("rev-parse", "HEAD"))
        self.assertNotEqual(updated["source_revision"], before["source_revision"])

    def test_shallow_history_fails_before_snapshot_and_full_history_recovers(self):
        before = self.build()
        self.git("add", "status")
        self.git("commit", "-qm", "Snapshot-only commit")
        shallow = self.root / "shallow-checkout"
        subprocess.run(["git", "clone", "-q", "--depth=1", self.root.as_uri(), str(shallow)],
                       check=True, capture_output=True)
        result = subprocess.run(["python3", "tools/build_handoff.py"], cwd=shallow,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shallow Git history", result.stderr)
        subprocess.run(["git", "fetch", "-q", "--unshallow"], cwd=shallow,
                       check=True, capture_output=True)
        subprocess.run(["python3", "tools/build_handoff.py"], cwd=shallow,
                       check=True, capture_output=True)
        recovered = json.loads((shallow / "status/LATEST_STATE.json").read_text())
        self.assertEqual(recovered["source_revision"], before["source_revision"])

    def test_old_state_without_checkpoint_remains_supported(self):
        file = self.root / "PROJECT_STATE.json"
        state = json.loads(file.read_text())
        state.pop("resume_checkpoint", None)
        state.pop("review_queue", None)
        file.write_text(json.dumps(state))
        result = self.build()
        self.assertEqual(result["resume_checkpoint"], {})
        self.assertEqual(result["review_queue"], [])


if __name__ == "__main__":
    unittest.main()
