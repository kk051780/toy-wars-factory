"""Git-backed behavior tests for the protected handoff status-writer step.

All remote operations target a temporary local bare Git repository. No GitHub
token, external service, workflow dispatch, or real main branch is used.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/handoff-sync.yml"
STEP_NAME = "      - name: Commit exact allowlisted status only, single no-retry push\n"


def actual_writer_shell():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert source.count(STEP_NAME) == 1
    part = source.split(STEP_NAME, 1)[1]
    script = part.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0]
    rows = script.splitlines()
    assert rows and all(not line.strip() or line.startswith("          ") for line in rows)
    return "\n".join(line[10:] if line else "" for line in rows) + "\n"


def command(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.PIPE).strip()


class WriterGitBoundary(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="twf-handoff-writer-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        self.summary = self.root / "summary.md"
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        mock = self.fake_bin / "gh"
        mock.write_text("#!/bin/sh\n"
                        "test \"$1\" = auth && test \"$2\" = setup-git || exit 90\n"
                        "exit 0\n", encoding="utf-8")
        mock.chmod(0o755)
        command("git", "init", "--bare", "-q", "-b", "main", str(self.remote))
        command("git", "init", "-q", "-b", "main", str(self.work))
        self.git("config", "user.name", "TWF Synthetic Test")
        self.git("config", "user.email", "synthetic@example.invalid")
        (self.work / "status").mkdir()
        (self.work / "docs").mkdir()
        (self.work / "status/CHAT_HANDOFF.md").write_text("old handoff\n")
        (self.work / "status/LATEST_STATE.json").write_text('{"old":true}\n')
        (self.work / "docs/original.md").write_text("untouched\n")
        self.git("add", "--all")
        self.git("commit", "-qm", "initial fixture")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "origin", "HEAD:refs/heads/main")
        self.source_sha = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return command("git", *args, cwd=self.work)

    def remote_sha(self):
        return command("git", "--git-dir", str(self.remote), "rev-parse", "refs/heads/main")

    def run_writer(self):
        env = os.environ.copy()
        env.update({"PATH": str(self.fake_bin) + os.pathsep + os.environ.get("PATH", ""),
                    "GH_TOKEN": "SYNTHETIC_NO_REAL_TOKEN",
                    "TWF_SOURCE_COMMIT": self.source_sha,
                    "GITHUB_STEP_SUMMARY": str(self.summary),
                    "GIT_TERMINAL_PROMPT": "0"})
        return subprocess.run(["bash", "-euo", "pipefail", "-c", actual_writer_shell()],
                              cwd=self.work, env=env, capture_output=True, text=True, timeout=20)

    def change_status(self):
        (self.work / "status/CHAT_HANDOFF.md").write_text("new handoff\n")
        source_revision = self.git("log", "-1", "--format=%H", "--",
                                       "src", "tests", "tools", "docs", "config",
                                       "PROJECT_STATE.json", "AGENTS.md", ".github", "history")
        (self.work / "status/LATEST_STATE.json").write_text(
            json.dumps({"new": True, "source_revision": source_revision}) + "\n")

    def test_status_only_update_pushes_exactly_two_paths(self):
        self.change_status()
        result = self.run_writer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(self.remote_sha(), self.source_sha)
        paths = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        self.assertEqual(paths, ["status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"])
        self.assertEqual(self.remote_sha(), self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("show", "HEAD:status/CHAT_HANDOFF.md"), "new handoff")

    def test_unchanged_status_skips_commit_and_push(self):
        (self.work / ".verified-handoff").mkdir()
        (self.work / ".verified-handoff/untracked").write_text("ignored untracked artifact\n")
        result = self.run_writer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.source_sha)
        self.assertEqual(self.remote_sha(), self.source_sha)
        self.assertIn("NO_CHANGE", self.summary.read_text())

    def test_unrelated_tracked_change_blocks_push(self):
        self.change_status()
        (self.work / "docs/original.md").write_text("should be rejected\n")
        result = self.run_writer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_sha(), self.source_sha)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.source_sha)

    def test_unrelated_staged_change_blocks_push(self):
        self.change_status()
        (self.work / "docs/original.md").write_text("staged unrelated\n")
        self.git("add", "docs/original.md")
        result = self.run_writer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_sha(), self.source_sha)

    def test_remote_main_moved_blocks_push_without_overwrite(self):
        self.change_status()
        other = self.root / "other"
        command("git", "clone", "-q", str(self.remote), str(other))
        command("git", "config", "user.name", "Independent synthetic writer", cwd=other)
        command("git", "config", "user.email", "other@example.invalid", cwd=other)
        (other / "docs/original.md").write_text("new accepted main\n")
        command("git", "add", "docs/original.md", cwd=other)
        command("git", "commit", "-qm", "competing main change", cwd=other)
        command("git", "push", "-q", "origin", "HEAD:refs/heads/main", cwd=other)
        moved = self.remote_sha()
        self.assertNotEqual(moved, self.source_sha)
        result = self.run_writer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.remote_sha(), moved)
        self.assertNotEqual(self.git("rev-parse", "HEAD"), self.source_sha)
        self.assertNotIn("SYNTHETIC_NO_REAL_TOKEN", result.stdout + result.stderr)


    def test_wrong_but_well_formed_source_revision_blocks_writer(self):
        self.change_status()
        path = self.work / "status/LATEST_STATE.json"
        record = json.loads(path.read_text())
        self.assertNotEqual(record["source_revision"], "0" * 40)
        record["source_revision"] = "0" * 40
        path.write_text(json.dumps(record) + "\n")
        result = self.run_writer()
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_sha(), self.source_sha)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.source_sha)

    def test_missing_source_revision_blocks_writer(self):
        self.change_status()
        path = self.work / "status/LATEST_STATE.json"
        path.write_text('{"new":true}\n')
        result = self.run_writer()
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_sha(), self.source_sha)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.source_sha)

    def test_source_revision_tracks_latest_substantive_not_status_commit(self):
        source_sha = self.source_sha
        (self.work / "status/CHAT_HANDOFF.md").write_text("status-only snapshot\n")
        self.git("add", "status/CHAT_HANDOFF.md")
        self.git("commit", "-qm", "synthetic status-only main commit")
        self.git("push", "-q", "origin", "HEAD:refs/heads/main")
        self.source_sha = self.git("rev-parse", "HEAD")
        self.assertNotEqual(self.source_sha, source_sha)
        self.change_status()
        record = json.loads((self.work / "status/LATEST_STATE.json").read_text())
        self.assertEqual(record["source_revision"], source_sha)
        result = self.run_writer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_sha(), self.git("rev-parse", "HEAD"))



    def test_future_snapshot_does_not_write_unprotected_main(self):
        self.change_status()
        result = self.run_writer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_sha(), self.source_sha,
                         "Unprotected main must remain unchanged by handoff job")

    def test_future_snapshot_branch_contains_exact_two_passive_files(self):
        self.change_status()
        result = self.run_writer()
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot_sha = command(
            "git", "--git-dir", str(self.remote), "rev-parse",
            "refs/heads/twf-handoff-snapshots")
        paths = command(
            "git", "--git-dir", str(self.remote), "ls-tree", "-r",
            "--name-only", snapshot_sha).splitlines()
        self.assertEqual(paths, ["status/CHAT_HANDOFF.md",
                                 "status/LATEST_STATE.json"])

    def test_future_snapshot_does_not_embed_executable_source_tree(self):
        self.change_status()
        result = self.run_writer()
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot_sha = command(
            "git", "--git-dir", str(self.remote), "rev-parse",
            "refs/heads/twf-handoff-snapshots")
        tree = command("git", "--git-dir", str(self.remote),
                       "ls-tree", "--name-only", snapshot_sha)
        self.assertEqual(tree, "status")


if __name__ == "__main__":
    unittest.main()
