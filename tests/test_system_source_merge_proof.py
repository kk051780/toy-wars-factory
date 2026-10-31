"""Immutable Git source-ledger reconciliation regressions; all local, no Roblox."""
import copy
import subprocess
import tempfile
from pathlib import Path
import unittest

from tools.system_source_merge_proof import (
    SOURCES, SourceLedgerRejected, author_ledger_from_git, plan_source_merge)


class MergeOrderProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        for name in SOURCES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("return {value=1}\n", encoding="utf-8")
        self.git("add", ".")
        self.commit("base")
        self.base = self.head()
        self.git("switch", "-q", "-c", "hud")
        self.change("src/ToyWarsHUD.client.lua", "return {value=12345}\n")
        self.commit("hud")
        self.hud = self.head()
        self.git("switch", "-q", "main")
        self.git("switch", "-q", "-c", "server")
        self.change("src/ToyWarsServer.server.lua", "return {value=999999999}\n")
        self.commit("server")
        self.server = self.head()
        self.git("switch", "-q", "main")

    def git(self, *args):
        cmd = ["git", "-c", "user.name=QA", "-c", "user.email=qa@example.invalid", *args]
        r = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0, (args, r.stderr))
        return r.stdout.strip()

    def head(self):
        return self.git("rev-parse", "HEAD")

    def change(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")

    def commit(self, label):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", label)

    def merged_one(self, first):
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "merge first", first)
        return self.head()

    def plan(self, second, main, ledger=None, base=None):
        h = self.hud if second == "hud" else self.server
        if ledger is None:
            ledger = author_ledger_from_git(self.root, self.base, h)
        return plan_source_merge(self.root, base or self.base, h, main, ledger)

    def test_two_merge_orders_have_the_same_real_source_total(self):
        results = []
        for first, second in (("hud", "server"), ("server", "hud")):
            with self.subTest(first=first):
                # Undo main to the exact authored base; the feature branches remain.
                self.git("switch", "-q", "main")
                self.git("reset", "-q", "--hard", self.base)
                one = self.merged_one(first)
                forecast = self.plan(second, one)
                self.assertTrue(forecast["source_only_commutativity"])
                self.assertEqual(forecast["observed_main_sha"], one)
                self.assertEqual(forecast["verification"], "LOCAL_GIT_OBJECT_CONSISTENCY_ONLY")
                self.assertFalse(forecast["authority"]["merge_allowed"])
                self.assertFalse(forecast["qa_verified"])
                self.assertFalse(forecast["provider_origin_verified"])
                self.git("merge", "-q", "--no-ff", "-m", "merge second", second)
                actual = sum((self.root / p).stat().st_size for p in SOURCES)
                self.assertEqual(forecast["candidate_post_merge_bytes"], actual)
                self.assertEqual(forecast["delta_bytes"], actual - forecast["observed_main_bytes"])
                results.append(actual)
        self.assertEqual(results[0], results[1])

    def test_stale_previous_main_ref_rejected(self):
        self.merged_one("hud")
        with self.assertRaisesRegex(SourceLedgerRejected, "STALE_MAIN_REF"):
            self.plan("server", self.base)

    def test_modified_authored_metrics_rejected(self):
        now = self.merged_one("hud")
        ledger = author_ledger_from_git(self.root, self.base, self.server)
        ledger["source_metrics_lua_bytes"] += 1
        with self.assertRaisesRegex(SourceLedgerRejected, "AUTHOR_BLOB_OR_METRIC_MISMATCH"):
            self.plan("server", now, ledger)

    def test_forged_author_after_blob_rejected(self):
        now = self.merged_one("server")
        ledger = author_ledger_from_git(self.root, self.base, self.hud)
        ledger["changes"][0]["after_sha"] = "f" * 40
        with self.assertRaisesRegex(SourceLedgerRejected, "AUTHOR_BLOB_OR_METRIC_MISMATCH"):
            self.plan("hud", now, ledger)

    def test_duplicate_ledger_change_rejected(self):
        now = self.merged_one("server")
        ledger = author_ledger_from_git(self.root, self.base, self.hud)
        ledger["changes"].append(copy.deepcopy(ledger["changes"][0]))
        with self.assertRaisesRegex(SourceLedgerRejected, "AUTHOR_BLOB_OR_METRIC_MISMATCH"):
            self.plan("hud", now, ledger)

    def test_same_file_concurrent_edit_rejected(self):
        self.change("src/ToyWarsServer.server.lua", "return {value=8888}\n")
        self.commit("same path on main")
        with self.assertRaisesRegex(SourceLedgerRejected, "SAME_SOURCE_FILE_CHANGED"):
            self.plan("server", self.head())

    def test_foreign_authored_base_rejected(self):
        now = self.merged_one("hud")
        with self.assertRaisesRegex(SourceLedgerRejected, "WRONG_AUTHOR_ANCESTRY"):
            self.plan("server", now, base=now)

    def test_new_source_module_cannot_escape_source_metrics(self):
        self.git("switch", "-q", "-c", "extra", self.base)
        self.change("src/Unreviewed.lua", "return {bad=true}\n") if (self.root / "src/Unreviewed.lua").exists() else (
            self.root / "src/Unreviewed.lua").write_text("return {bad=true}\n")
        self.commit("add unreviewed Lua")
        with self.assertRaisesRegex(SourceLedgerRejected, "UNEXPECTED_SOURCE_OR_MODE"):
            author_ledger_from_git(self.root, self.base, self.head())

    def test_chmod_executable_lua_is_rejected(self):
        self.git("switch", "-q", "-c", "mode", self.base)
        self.git("update-index", "--chmod=+x", "src/ToyWarsHUD.client.lua")
        self.git("commit", "-q", "-m", "unexpected executable mode")
        with self.assertRaisesRegex(SourceLedgerRejected, "UNEXPECTED_SOURCE_OR_MODE"):
            author_ledger_from_git(self.root, self.base, self.head())

    def test_noop_game_source_candidate_rejected(self):
        self.git("switch", "-q", "-c", "docs-only", self.base)
        (self.root / "README.md").write_text("docs change\n", encoding="utf-8")
        self.commit("documentation only")
        with self.assertRaisesRegex(SourceLedgerRejected, "NO_SOURCE_CHANGE"):
            author_ledger_from_git(self.root, self.base, self.head())

    def test_already_integrated_author_cannot_be_proposed_again(self):
        merged = self.merged_one("server")
        with self.assertRaisesRegex(SourceLedgerRejected, "AUTHOR_ALREADY_IN_MAIN"):
            self.plan("server", merged)

    def test_source_deletion_rejected(self):
        self.git("switch", "-q", "-c", "deleted", self.base)
        (self.root / "src/ToyWarsBalance.lua").unlink()
        self.commit("delete a source")
        with self.assertRaisesRegex(SourceLedgerRejected, "CANONICAL_SOURCE_SET_CHANGED"):
            author_ledger_from_git(self.root, self.base, self.head())


if __name__ == "__main__":
    unittest.main()
