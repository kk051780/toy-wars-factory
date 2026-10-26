"""Fail-closed reconciliation of independently authored source-size ledgers.

All src/*.lua before/after chains are still checked by the original handoff
test, and total current bytes must equal the original baseline plus every
recorded source delta. Only an explicit immutable-Git-backed concurrent merge
may explain a branch-local source_metrics value differing from the *sorted*
global ledger total. Never rewrite original C records to fake merge order.
"""
import json
import subprocess
from pathlib import Path


class MergeMetricReconciliation:
    def __init__(self, origin_repo, history_dir):
        self.repo = Path(origin_repo)
        self.history_dir = Path(history_dir)
        manifest_path = self.history_dir / "MERGE_ORDER_RECONCILIATION.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest.get("schema") == 1
        exceptions = manifest.get("exceptions")
        assert isinstance(exceptions, list)
        names = [item.get("record") for item in exceptions]
        assert len(names) == len(set(names)), "duplicate reconciliation record"
        self.exceptions = {item["record"]: item for item in exceptions}
        self.used = set()

    def _git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repo, stderr=subprocess.PIPE)

    def _exists(self, sha, path):
        return subprocess.run(
            ["git", "cat-file", "-e", f"{sha}:{path}"],
            cwd=self.repo, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL).returncode == 0

    def _ancestor(self, start, end):
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", start, end],
            cwd=self.repo, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL).returncode == 0

    @staticmethod
    def adjustment(record_file, record, actual_total, prior_records, entry):
        assert isinstance(entry, dict)
        assert entry.get("record") == record_file.name
        assert entry.get("record_id") == record.get("id")
        excluded = entry.get("excluded_prior_records")
        assert isinstance(excluded, list) and excluded
        assert len(excluded) == len(set(excluded)), "duplicate excluded record"
        assert all(name in prior_records for name in excluded), "not a prior record"
        affected = {
            item["path"] for item in record["source_changes"]
            if item["path"].startswith("src/") and item["path"].endswith(".lua")
        }
        total = 0
        for name in excluded:
            earlier = prior_records[name]
            assert earlier.get("source_changes"), "excluded record lacks source change"
            for change in earlier["source_changes"]:
                assert change["path"] not in affected, "conflicting same-source changes"
                assert (change["after_bytes"] - change["before_bytes"] ==
                        change["delta_bytes"]), "invalid excluded delta"
                total += change["delta_bytes"]
        assert total > 0, "missing positive independent source delta"
        assert (actual_total - record["source_metrics"]["lua_bytes"] == total), (
            "branch authored bytes do not reconcile to ordered ledger bytes")
        assert record["main_base"] == entry.get("authored_base")
        return total

    def verify(self, record_file, record, actual_total, prior_records):
        expected = record["source_metrics"]["lua_bytes"]
        entry = self.exceptions.get(record_file.name)
        if expected == actual_total:
            assert entry is None, "unused waiver for now-consistent ledger"
            return
        assert entry is not None, (
            f"unexplained source_metrics drift in {record_file.name}: "
            f"{expected} != {actual_total}")
        assert record_file.name not in self.used
        self.adjustment(record_file, record, actual_total, prior_records, entry)
        self._audit_git_provenance(record_file, record, entry)
        self.used.add(record_file.name)

    def _audit_git_provenance(self, record_file, record, entry):
        authored = entry["authored_commit"]
        earlier = entry["earlier_main_merge"]
        later = entry["later_main_merge"]
        excluded = entry["excluded_prior_records"]
        assert self._ancestor(entry["authored_base"], authored)
        assert self._ancestor(authored, earlier)
        assert self._ancestor(earlier, later)
        assert self._ancestor(later, "HEAD")
        path = "history/" + record_file.name
        authored_record = json.loads(self._git("show", f"{authored}:{path}"))
        assert authored_record == record, "record changed after authored source commit"
        assert self._exists(earlier, path), "author record missing at earlier merge"
        assert self._exists(later, path), "author record lost by later merge"
        source_files = entry.get("source_files")
        assert source_files == [
            "src/ToyWarsBalance.lua", "src/ToyWarsServer.server.lua",
            "src/ToyWarsHUD.client.lua", "src/ToyWarsSmokeTest.server.lua"
        ], "source file list must be the four canonical Lua modules"
        authored_bytes = {
            path: len(self._git("show", f"{authored}:{path}"))
            for path in source_files
        }
        assert sum(authored_bytes.values()) == record["source_metrics"]["lua_bytes"], (
            "author-commit source bytes differ from recorded branch snapshot")
        for change in record["source_changes"]:
            assert authored_bytes[change["path"]] == change["after_bytes"], (
                "author's changed source does not match claimed after_bytes")
        for name in excluded:
            excluded_path = "history/" + name
            assert not self._exists(earlier, excluded_path), (
                "excluded source record already present at earlier merge")
            assert self._exists(later, excluded_path), (
                "excluded source record absent at later merge")

    def assert_all_consumed(self):
        assert self.used == set(self.exceptions), "stale or unused reconciliation entry"
