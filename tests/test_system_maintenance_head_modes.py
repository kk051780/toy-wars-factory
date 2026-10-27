"""Run the actual scope CLI against immutable Git mode changes.

The checkout under test is the exact PR78 checker, with a narrow head-mode
fix. These are local process/Git tests, not authenticated Actions evidence.
"""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools/check_meta_diff.py"
MODULE = "tools/system_host_write_triage.py"
REGRESSION = "tests/test_system_new_receipt.py"
HISTORY = "history/C09999_head_mode_regression.json"
BRANCH = "auto/twf-system-review-23e9ebe9-179c-8326-8fdd-ac241ec4ef53"


class HeadModeCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Mode regression")
        self.git("config", "user.email", "qa@local.invalid")
        self.git("config", "core.filemode", "true")
        self.write(MODULE, "VALUE = 1\n")
        (self.root / MODULE).chmod(0o644)
        self.write("config/autonomous_repair.json",
                   (ROOT / "config/autonomous_repair.json").read_text())
        self.git("add", "-A")
        self.git("commit", "-qm", "trusted regular module")
        self.base = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", self.base)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args],
                                       text=True, stderr=subprocess.PIPE).strip()

    def write(self, path, content):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

    def commit_candidate(self, *, regression=True, history=True):
        if regression:
            self.write(REGRESSION, "assert True\n")
        if history:
            self.write(HISTORY, "{}\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "candidate")
        return self.git("rev-parse", "HEAD")

    def cli(self, head, *, checker=CHECKER, base=None):
        return subprocess.run(
            [sys.executable, str(checker), "--policy",
             str(self.root / "config/autonomous_repair.json"), "--base",
             self.base if base is None else base, "--head", head,
             "--branch", BRANCH], cwd=self.root, text=True,
            capture_output=True, timeout=20)

    def assert_denied(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("PASS: system review scope", result.stdout)

    def test_regular_content_edit_is_allowed_by_real_cli(self):
        self.write(MODULE, "VALUE = 2\n")
        head = self.commit_candidate()
        result = self.cli(head)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_chmod_only_git_M_is_denied_by_real_cli(self):
        (self.root / MODULE).chmod(0o755)
        head = self.commit_candidate()
        self.assertIn("M\t" + MODULE, self.git("diff", "--name-status", self.base, head))
        self.assertTrue(self.git("ls-tree", head, "--", MODULE).startswith("100755 blob"))
        self.assert_denied(self.cli(head))

    def test_chmod_and_content_edit_are_denied(self):
        self.write(MODULE, "VALUE = 2\n")
        (self.root / MODULE).chmod(0o755)
        self.assert_denied(self.cli(self.commit_candidate()))

    def test_symlink_postimage_is_denied(self):
        file = self.root / MODULE
        file.unlink()
        file.symlink_to("../config/autonomous_repair.json")
        head = self.commit_candidate()
        self.assertTrue(self.git("ls-tree", head, "--", MODULE).startswith("120000 blob"))
        self.assert_denied(self.cli(head))

    def test_deleted_module_is_denied(self):
        (self.root / MODULE).unlink()
        self.assert_denied(self.cli(self.commit_candidate()))

    def test_new_head_only_module_does_not_gain_base_authority(self):
        self.write("tools/system_untrusted.py", "VALUE = 1\n")
        untrusted = self.commit_candidate()
        self.write("tools/system_untrusted.py", "VALUE = 2\n")
        self.write("tests/test_system_second_receipt.py", "assert True\n")
        self.write("history/C09998_second_receipt.json", "{}\n")
        head = self.commit_candidate()
        self.assert_denied(self.cli(head, base=untrusted))

    def test_immutable_head_mode_wins_over_working_tree_permissions(self):
        (self.root / MODULE).chmod(0o755)
        head = self.commit_candidate()
        (self.root / MODULE).chmod(0o644)
        self.assert_denied(self.cli(head))

    def test_ordinary_commit_wins_over_uncommitted_executable_mode(self):
        self.write(MODULE, "VALUE = 2\n")
        head = self.commit_candidate()
        (self.root / MODULE).chmod(0o755)
        result = self.cli(head)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_HEAD_resolves_to_committed_mode(self):
        (self.root / MODULE).chmod(0o755)
        self.commit_candidate()
        self.assert_denied(self.cli("HEAD"))

    def test_receipts_remain_mandatory(self):
        self.write(MODULE, "VALUE = 2\n")
        self.assert_denied(self.cli(self.commit_candidate(regression=False)))

    def test_history_remains_mandatory(self):
        self.write(MODULE, "VALUE = 2\n")
        self.assert_denied(self.cli(self.commit_candidate(history=False)))

    def test_exact_unpatched_checker_reproduces_mode_bypass(self):
        # This blob belongs to the original PR78 commit, not a reimplemented
        # checker fixture. Full CI history retains it after a fix commit.
        blob = "e8567c85c5ff9895052e8b15a1ea288304b3b978"
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "cat-file", "blob", blob])
        self.assertEqual(hashlib.sha1(b"blob " + str(len(raw)).encode() +
                                    b"\0" + raw).hexdigest(), blob)
        (self.root / MODULE).chmod(0o755)
        head = self.commit_candidate()
        trusted = self.root / "trusted-negative"
        trusted.mkdir()
        original = trusted / "check_meta_diff.py"
        original.write_bytes(raw)
        for name in ("check_auto_diff.py", "repair_control.py"):
            shutil.copyfile(ROOT / "tools" / name, trusted / name)
        before = self.cli(head, checker=original)
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assert_denied(self.cli(head))


if __name__ == "__main__":
    unittest.main()
