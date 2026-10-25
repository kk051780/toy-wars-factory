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
        self.assertEqual((r["automation"]["pct"],r["automation"]["done"],r["automation"]["total"]), (49,7,15))
        self.assertEqual((r["game"]["pct"],r["game"]["done"],r["game"]["total"]), (34,6,18))
    def test_draft_does_not_count(self):
        self.assertEqual(self.data["tracks"][1]["milestones"][6]["state"], "pending")
        self.assertEqual(mod.summarize(self.data)["game"]["pct"], 34)
    def test_evidence_required(self):
        self.data["tracks"][0]["milestones"][0].pop("evidence")
        with self.assertRaises(ValueError): mod.summarize(self.data)
    def test_total_weight_guard(self):
        self.data["tracks"][1]["milestones"][0]["weight"]+=1
        with self.assertRaises(ValueError): mod.summarize(self.data)
if __name__ == "__main__": unittest.main()
