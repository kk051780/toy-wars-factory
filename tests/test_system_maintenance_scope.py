"""Issue72 trusted-base maintenance admission, deny-first adversarial fixtures.

The checker is a trusted *main-base* boundary. These tests do not authorize a
merge or a provider action; the registered META claim and independent REVIEWER
are separate required gates.
"""
import copy
import json
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_meta_diff import violations, trusted_base_system_modules

VALID_MODULE = "tools/system_host_write_triage.py"
VALID_TEST = ("A", "tests/test_system_maintenance_regression.py")
VALID_HISTORY = ("A", "history/C00046_system_maintenance_scope.json")
EDIT = ("M", VALID_MODULE)


class TrustedMaintenanceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "config/autonomous_repair.json").read_text())

    def allowed(self, entries, known=None):
        return violations(entries, self.policy,
                          trusted_base_modules=set(known if known is not None else [VALID_MODULE]))

    def test_allowed_only_with_trusted_existing_file_and_two_new_receipts(self):
        self.assertEqual(self.allowed([EDIT, VALID_TEST, VALID_HISTORY]), [])
        self.assertTrue(self.allowed([EDIT, VALID_TEST, VALID_HISTORY], known=set()))
        self.assertTrue(self.allowed([EDIT, VALID_TEST], known={VALID_MODULE}))
        self.assertTrue(self.allowed([EDIT, VALID_HISTORY], known={VALID_MODULE}))
        self.assertTrue(self.allowed([EDIT], known={VALID_MODULE}))

    def test_over_100_adversarial_path_status_pairs(self):
        paths = [
            "tools/system_.py", "tools/system_../evil.py",
            "tools/system_../../evil.py", "tools/system_foo.py/../secret",
            "tools/system_foo.py/evil", "tools/system_foo.py\\evil",
            "tools/System_host_write_triage.py", "tools/system-foo.py",
            "tools/system_foo.pyo", "tools/system_foo.py~",
            "tools/system_foo.py.exe", "tools/system_foo.py/.",
            "tools/system_foo.py/.git", "tools/system_foo.py.old",
            "tools/system_foo.py%00", "tools/system_foo.py:secret",
            "tools/system_foo.py;rm", "tools/system_foo.py\n",
            "tools/system_foo.py\t", "tools/evil.py",
            "tools/check_meta_diff.py", "tools/repair_integration.py",
            "config/autonomous_repair.json", ".github/workflows/bootstrap-quality.yml",
            "src/ToyWarsServer.server.lua", "tests/test_system_legacy.py",
            "history/C00043_review_repair_queue.json", ".env",
            "tools/system_foo/../host_write_triage.py",
            "tools/system_foo.py/../../config/secrets",
        ]
        statuses = ["M", "A", "D", "R100", "C100", "T", "U", "X"]
        counter = 0
        for path in paths:
            for status in statuses:
                with self.subTest(path=path, status=status):
                    result = self.allowed([(status, path), VALID_TEST, VALID_HISTORY],
                                          known={VALID_MODULE})
                    self.assertTrue(result, (status, path))
                    counter += 1
        self.assertGreaterEqual(counter, 200)

    def test_valid_path_wrong_status_or_unregistered_module_rejected(self):
        for status in ("A", "D", "R100", "T", "C100", "U"):
            with self.subTest(status=status):
                self.assertTrue(self.allowed([(status, VALID_MODULE),
                                              VALID_TEST, VALID_HISTORY]))
        self.assertTrue(self.allowed([("M", "tools/system_unknown.py"),
                                      VALID_TEST, VALID_HISTORY]))
        self.assertTrue(self.allowed([EDIT, EDIT, VALID_TEST, VALID_HISTORY]))

    def test_cannot_modify_trusted_policy_workflow_accepted_test_or_gate(self):
        for path in [
            "tools/check_meta_diff.py", "tools/check_auto_diff.py",
            "tests/test_system_review_scope.py", "tests/test_system_host_write_triage.py",
            "config/autonomous_repair.json", "AGENTS.md",
            ".github/workflows/bootstrap-quality.yml",
            "ops/REPAIR_COORDINATOR.json",
        ]:
            with self.subTest(path=path):
                self.assertTrue(self.allowed([EDIT, VALID_TEST, VALID_HISTORY,
                                              ("M", path)]))

    def test_new_test_history_require_exact_patterns_and_add_status(self):
        invalid_tests = [
            ("M", VALID_TEST[1]), ("D", VALID_TEST[1]),
            ("A", "tests/test_system_../unsafe.py"),
            ("A", "tests/test_system_foo.py.tmp"),
            ("A", "tests/nested/test_system_new.py")
        ]
        for item in invalid_tests:
            with self.subTest(test=item):
                self.assertTrue(self.allowed([EDIT, item, VALID_HISTORY]))
        invalid_histories = [
            ("M", VALID_HISTORY[1]), ("D", VALID_HISTORY[1]),
            ("A", "history/Cx0046_patch.json"),
            ("A", "history/C00046_patch.json.bak"),
            ("A", "history/nested/C00046_patch.json"),
        ]
        for item in invalid_histories:
            with self.subTest(history=item):
                self.assertTrue(self.allowed([EDIT, VALID_TEST, item]))

    def test_trusted_base_git_tree_rejects_symlinks_and_untrusted_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            def git(*args):
                return subprocess.check_output(["git", "-C", temp, *args],
                                               text=True).strip()
            git("init", "-q")
            git("config", "user.email", "scope@local.invalid")
            git("config", "user.name", "Scope")
            tools = Path(temp) / "tools"
            tools.mkdir()
            (tools / "system_host_write_triage.py").write_text("pass\n")
            (tools / "system_other.py").symlink_to("system_host_write_triage.py")
            (tools / "repair_control.py").write_text("pass\n")
            git("add", "-A")
            git("commit", "-qm", "trusted-main")
            sha = git("rev-parse", "HEAD")
            git("update-ref", "refs/remotes/origin/main", sha)
            cwd = Path.cwd()
            try:
                os.chdir(temp)
                self.assertEqual(trusted_base_system_modules(sha),
                                 {"tools/system_host_write_triage.py"})
                self.assertEqual(trusted_base_system_modules("bad-ref"), set())
                self.assertEqual(trusted_base_system_modules("f"*40), set())
                git("checkout", "-qb", "attacker")
                (tools / "system_evil.py").write_text("pass\n")
                git("add", "-A")
                git("commit", "-qm", "attacker")
                attacker = git("rev-parse", "HEAD")
                self.assertEqual(trusted_base_system_modules(attacker), set())
            finally:
                os.chdir(cwd)

    def test_reading_from_head_or_untrusted_claim_fails_closed(self):
        # Data supplied by the author is never a trusted-base Git tree.
        candidate = "tools/system_rogue.py"
        self.assertTrue(self.allowed([("M", candidate), VALID_TEST, VALID_HISTORY],
                                     known=set()))
        self.assertTrue(self.allowed([EDIT, VALID_TEST, VALID_HISTORY],
                                     known=[]))


if __name__ == "__main__":
    unittest.main()
