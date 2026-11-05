"""Test scheduled-PR scope against real rename/delete/modify Git change types."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_auto_diff import changed_entries, violations


class CloudRepairScopeTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "config/autonomous_repair.json").read_text())

    def test_game_fix_with_new_regression_and_history_is_allowed(self):
        self.assertEqual(violations([
            ("M", "src/ToyWarsServer.server.lua"),
            ("A", "tests/auto/production_spec.lua"),
            ("A", "history/C00018_production.json"),
        ], self.policy), [])

    def test_executed_coverage_improvement_without_game_change_is_allowed(self):
        self.assertEqual(violations([
            ("A", "tests/auto/production_spec.lua"),
            ("A", "tests/test_auto_production.py"),
        ], self.policy), [])

    def test_audit_only_and_source_without_regression_are_rejected(self):
        self.assertTrue(violations([("A", "history/C00018_audit.json")], self.policy))
        self.assertTrue(violations([("M", "src/ToyWarsHUD.client.lua")], self.policy))

    def test_governance_secrets_and_existing_gates_are_rejected(self):
        for path in ("AGENTS.md", "PROJECT_STATE.json", "config/quality_policy.json",
                     "config/autonomous_repair.json", ".github/workflows/bootstrap-quality.yml",
                     "tools/gemini_patch_gate.py", "tests/server_event_spec.lua", ".env"):
            with self.subTest(path=path):
                self.assertTrue(violations([("M", path), ("A", "tests/auto/valid_spec.lua")], self.policy))

    def test_existing_accepted_regressions_and_history_cannot_be_rewritten(self):
        for path in ("tests/auto/production_spec.lua", "tests/test_auto_production.py",
                     "history/C00018_production.json"):
            with self.subTest(path=path):
                self.assertTrue(violations([("M", path), ("A", "tests/auto/valid_spec.lua")], self.policy))

    def test_deletes_renames_and_parent_traversal_are_rejected(self):
        for entry in (("D", "src/ToyWarsServer.server.lua"),
                      ("R100", "tests/auto/renamed_spec.lua"),
                      ("A", "tests/auto/../../outside_spec.lua")):
            with self.subTest(entry=entry):
                self.assertTrue(violations([entry, ("A", "tests/auto/valid_spec.lua")], self.policy))

    def test_tests_hidden_below_ci_discovery_and_nested_history_are_rejected(self):
        for path in ("tests/auto/nested/ignored_spec.lua",
                     "tests/test_auto_nested/ignored.py", "history/C00018_nested/ignored.json"):
            with self.subTest(path=path):
                self.assertTrue(violations([("A", path), ("A", "tests/auto/valid_spec.lua")], self.policy))

    def test_git_diff_reports_delete_and_add_without_hiding_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            def git(*args):
                return subprocess.check_output(["git", "-C", tmp, *args], text=True).strip()
            git("init", "-q")
            git("config", "user.name", "Scope fixture")
            git("config", "user.email", "scope@local.invalid")
            (directory / "old file.lua").write_text("return true\n")
            git("add", "old file.lua")
            git("commit", "-qm", "Base")
            base = git("rev-parse", "HEAD")
            (directory / "old file.lua").rename(directory / "new file.lua")
            git("add", "-A")
            git("commit", "-qm", "Rename")
            previous = Path.cwd()
            try:
                import os
                os.chdir(directory)
                self.assertEqual(changed_entries(base, "HEAD"), [
                    ("A", "new file.lua"), ("D", "old file.lua")])
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
