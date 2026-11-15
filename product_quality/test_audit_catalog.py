import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit_catalog", ROOT / "audit_catalog.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CatalogAuditTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT.parent / "rc_fastlane/FEATURE_CATALOG.json").read_text(encoding="utf-8"))

    def test_real_catalog_has_67_unique_ids_and_no_false_engine_pass(self):
        r = module.audit(self.catalog)
        self.assertEqual(67, r["row_count"])
        self.assertEqual(67, r["ids_examined"])
        self.assertIsNone(r["gameplay_engine_pass_count"])
        self.assertIn("CATALOG_RUNTIME_BEHAVIOR_NOT_FULLY_VERIFIED", r["issues"])

    def test_owner_assassin_rename_detected(self):
        c = copy.deepcopy(self.catalog)
        a = next(x for x in c["rows"] if x["id"] == "P0D-011")
        a["name"] = "忍者・透明"
        self.assertIn("STALE_ASSASSIN_DISPLAY_NAME:P0D-011", module.audit(c)["issues"])
        a["name"] = "暗殺者・透明"
        self.assertNotIn("STALE_ASSASSIN_DISPLAY_NAME:P0D-011", module.audit(c)["issues"])

    def test_duplicate_id_blocks_metadata_pass(self):
        c = copy.deepcopy(self.catalog)
        c["rows"][0]["id"] = c["rows"][1]["id"]
        self.assertIn("INVALID_OR_DUPLICATE_FEATURE_ID", module.audit(c)["issues"])

    def test_unknown_stage_and_missing_role_blocks_metadata_pass(self):
        c = copy.deepcopy(self.catalog)
        c["rows"] = [x for x in c["rows"] if x["id"] != "P0D-014"]
        c["rows"][0]["stage"] = "ENGINE_PASS_UNVERIFIED"
        r = module.audit(c)
        self.assertIn("UNRECOGNIZED_FEATURE_STAGE", r["issues"])
        self.assertTrue(any(x.startswith("MISSING_ROLE_FEATURES:P0D-014") for x in r["issues"]))

    def test_malformed_catalog_no_fake_pass(self):
        self.assertEqual("CATALOG_REVIEW_REQUIRED", module.audit(None)["decision"])
        self.assertEqual("CATALOG_REVIEW_REQUIRED", module.audit({"rows":"fake"})["decision"])

if __name__ == "__main__":
    unittest.main()
