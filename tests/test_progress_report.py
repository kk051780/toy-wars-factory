import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("progress_report", ROOT / "tools/progress_report.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ProgressTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "config/progress_milestones.json").read_text(encoding="utf-8"))
    def test_baseline(self):
        r = mod.summarize(self.data)
        self.assertEqual((r["automation"]["pct"],r["automation"]["done"],r["automation"]["total"]), (57,8,15))
        self.assertEqual((r["game"]["pct"],r["game"]["done"],r["game"]["total"]), (38,7,18))
    def test_draft_does_not_count(self):
        self.assertEqual(self.data["tracks"][1]["milestones"][7]["state"], "blocked")
        self.assertEqual(mod.summarize(self.data)["game"]["pct"], 38)
    def test_first_cycle_is_proved_but_full_recovery_is_not(self):
        progress = mod.summarize(self.data)
        self.assertEqual(progress["automation"]["pct"], 57)
        self.assertEqual(self.data["tracks"][0]["milestones"][7]["state"], "verified")
        self.assertEqual(self.data["tracks"][0]["milestones"][8]["state"], "pending")
        self.assertEqual(self.data["tracks"][0]["milestones"][12]["state"], "pending")
        self.assertEqual(self.data["tracks"][1]["milestones"][6]["state"], "verified")
        self.assertEqual(self.data["tracks"][1]["milestones"][7]["state"], "blocked")
    def test_evidence_required(self):
        self.data["tracks"][0]["milestones"][0].pop("evidence")
        with self.assertRaises(ValueError): mod.summarize(self.data)
    def test_total_weight_guard(self):
        self.data["tracks"][1]["milestones"][0]["weight"]+=1
        with self.assertRaises(ValueError): mod.summarize(self.data)
if __name__ == "__main__": unittest.main()
