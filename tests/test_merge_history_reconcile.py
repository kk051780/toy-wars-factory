import unittest
from pathlib import Path
from tools.merge_history_reconcile import MergeMetricReconciliation as Reconcile


def rec(name, path, before, after, total):
    return {"id": name, "main_base": "base", "source_changes": [
        {"path": path, "before_bytes": before, "after_bytes": after, "delta_bytes": after-before}],
        "source_metrics": {"lua_bytes": total}}


class SourceHistoryOrderTests(unittest.TestCase):
    def setUp(self):
        self.hud = rec("C40", "src/ToyWarsHUD.client.lua", 4286, 6610, 29876)
        self.server = rec("C44", "src/ToyWarsServer.server.lua", 18946, 19100, 27706)

    def check_gap(self, record_name, current, prior_name, prior, total):
        return Reconcile.adjustment(Path(record_name), current, total,
            {prior_name: prior}, {"record": record_name, "record_id": current["id"],
            "authored_base": "base", "excluded_prior_records": [prior_name]})

    def test_hud_record_sorts_before_server_merge(self):
        self.assertEqual(self.check_gap("C44.json", self.server, "C40.json", self.hud, 30030), 2324)

    def test_server_merges_before_hud_record(self):
        self.assertEqual(self.check_gap("C40.json", self.hud, "C44.json", self.server, 30030), 154)

    def test_wrong_totals_fail(self):
        with self.assertRaises(AssertionError):
            self.check_gap("C44.json", self.server, "C40.json", self.hud, 30031)

    def test_conflicting_source_file_fails(self):
        colliding = rec("C40", "src/ToyWarsServer.server.lua", 16622, 18946, 29876)
        with self.assertRaises(AssertionError):
            self.check_gap("C44.json", self.server, "C40.json", colliding, 30030)

    def test_missing_prior_record_fails(self):
        with self.assertRaises(AssertionError):
            Reconcile.adjustment(Path("C44.json"), self.server, 30030, {},
                {"record": "C44.json", "record_id": "C44",
                 "authored_base": "base", "excluded_prior_records": ["C40.json"]})


if __name__ == "__main__":
    unittest.main()
