"""Source and negative gates using the actual extracted author31 candidate.
Invoked after compose.py in PR CI; no fake Studio behavior claims.
"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path("artifacts/gq538_rc32")
MOD=Path("_original_result538/quality_gameplay/v3_result_transient_gui_20261116/compose_result.py")
spec=importlib.util.spec_from_file_location("gq538",MOD)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project=json.loads((ROOT/"GQ538_RC32_CANDIDATE.project.json").read_text())
        cls.receipt=json.loads((ROOT/"GQ538_RC32_RECEIPT.json").read_text())
        cls.original=Path("_official_rc31/EGGRUMBLE_V3_RC31_CANONICAL_STUDIO.rbxlx")
        import sys
        sys.path.insert(0,"rc_fastlane/quality_result538_rc32")
        import compose
        cls.source=compose.extraction(cls.original)

    def test_true_original_result_blob(self):
        self.assertEqual(mod.git_blob(self.source["EGGRUMBLE_MatchResultService"][1].encode()),mod.AUTHOR_BLOB)

    def test_negative_original_drift_rejected(self):
        original=self.source["EGGRUMBLE_MatchResultService"][1].encode()
        with self.assertRaises(ValueError):
            mod.patch(original+b"\n-- mutated",True)

    def test_exact_author_off(self):
        original=self.source["EGGRUMBLE_MatchResultService"][1].encode()
        self.assertEqual(mod.patch(original,False),original)

    def test_one_original_result(self):
        service=(ROOT/"EGGRUMBLE_MatchResultService.luau").read_text()
        self.assertEqual(service.count("ResultRetry.deliver("),1)
        self.assertEqual(service.count("local ResultRetry=require("),1)
        self.assertEqual(service.count("ScoreBalance.build("),1)
        self.assertEqual(service.count("session.resultsDelivered=true"),1)

    def test_original_30_sources_identical(self):
        for name,(cls,src) in self.source.items():
            if name=="EGGRUMBLE_MatchResultService":continue
            ext=(".server.luau" if cls=="Script" else ".client.luau" if cls=="LocalScript" else ".luau")
            self.assertEqual((ROOT/(name+ext)).read_bytes(),src.encode(),name)

    def test_single_pure_retry_added(self):
        scripts=self.project["tree"]["ServerScriptService"]
        self.assertIn("EGGRUMBLE_ResultRetry",scripts)
        self.assertEqual(self.receipt["candidate_script_count"],32)
        self.assertEqual(self.receipt["unchanged_original_script_count"],30)
        self.assertFalse(self.receipt["official_rc_integration"])

    def test_result_retry_lifecycle(self):
        t=(ROOT/"EGGRUMBLE_ResultRetry.luau").read_text()
        self.assertIn("MAX_RETRIES = 8",t)
        self.assertIn("INTERVAL_SECONDS = 0.25",t)
        self.assertIn("pcall(isCurrent)",t)
        self.assertIn("pcall(renderOnce)",t)
        self.assertNotIn("DataStoreService",t)
        self.assertNotIn("RemoteEvent.new",t)

if __name__=="__main__": unittest.main()
