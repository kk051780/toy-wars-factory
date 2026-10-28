"""Check authored snapshots against immutable Git objects, not mutable aliases."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def git_bytes(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def blob_id(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class CharacterHistoryTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "history/C00100_character_pipeline_pilot.json").read_text())

    def check_changes(self, changes, before_ref, after_ref):
        self.assertEqual(len({x["path"] for x in changes}), len(changes))
        for entry in changes:
            with self.subTest(path=entry["path"], after=after_ref):
                before = git_bytes(before_ref, entry["path"])
                after = git_bytes(after_ref, entry["path"])
                self.assertEqual(entry["before_bytes"], len(before))
                self.assertEqual(entry["after_bytes"], len(after))
                self.assertEqual(entry["delta_bytes"], len(after) - len(before))
                self.assertEqual(entry["before_blob"], blob_id(before))
                self.assertEqual(entry["after_blob"], blob_id(after))

    def check_metrics(self, metrics, ref):
        names = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", ref, "--", "src/"], cwd=ROOT, text=True
        ).splitlines()
        raw = [git_bytes(ref, name) for name in names if name.endswith(".lua")]
        self.assertEqual(metrics, {"lua_files": len(raw), "lua_lines": sum(len(x.splitlines()) for x in raw),
                                   "lua_bytes": sum(len(x) for x in raw)})

    def test_initial_snapshot_matches_its_actual_authored_git_tree(self):
        snapshot = self.record["initial_authored_snapshot"]
        self.check_changes(snapshot["source_changes"], snapshot["main_base"], snapshot["head"])
        self.check_metrics(snapshot["source_metrics"], snapshot["head"])

    def test_current_ledger_matches_authored_base_and_current_git_sources(self):
        self.check_changes(self.record["source_changes"], self.record["main_base"], "HEAD")
        self.check_metrics(self.record["source_metrics"], "HEAD")
        self.assertEqual(self.record["source_baseline_bytes"], 25726)

    def test_each_historical_reconciliation_matches_its_immutable_source_tree(self):
        snapshots = {
            "C00101_character_ledger_review_repair.json": "04ae31b1447ec352e504f96b72dd91ea78d24db2",
            "C00102_character_current_main_reconciliation.json": "8997fdbd364ef9f0aa88ffffecfee3bfc22087bd",
        }
        for name, ref in snapshots.items():
            record = json.loads((ROOT / "history" / name).read_text())
            self.check_metrics(record["source_metrics"], ref)
            for entry in record["source_parity"]:
                raw = git_bytes(ref, entry["path"])
                self.assertEqual((entry["bytes"], entry["blob"]), (len(raw), blob_id(raw)))

    def test_reconciled_server_values_cannot_masquerade_as_initial_snapshot(self):
        snapshot = deepcopy(self.record["initial_authored_snapshot"])
        server = next(x for x in snapshot["source_changes"] if x["path"] == "src/ToyWarsServer.server.lua")
        server.update(after_bytes=37081, after_blob="cc347bf34ee1961e319e49eabf4a3b5616455fb8")
        # Use the same comparison as the positive test, with an expected failure.
        raw = git_bytes(snapshot["head"], server["path"])
        self.assertNotEqual((server["after_bytes"], server["after_blob"]), (len(raw), blob_id(raw)))


if __name__ == "__main__":
    unittest.main()
