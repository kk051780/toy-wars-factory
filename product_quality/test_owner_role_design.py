"""OWNER approved role spec is independently traced; none counts as engine-play verified."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from check_concept_trace import evaluate, ROLE_CAPABILITIES

ROOT=Path(__file__).resolve().parents[1]
def load():
    c=json.loads((ROOT/"rc_fastlane/FEATURE_CATALOG.json").read_text(encoding="utf-8"))
    t=json.loads((ROOT/"product_quality/DESIGN_TO_GAME_TRACE_MATRIX.json").read_text(encoding="utf-8"))
    return c,t

class OwnerRoleDesignTests(unittest.TestCase):
    def test_full_owner_role_contracts_all_eight_mapped(self):
        c,t=load()
        a=evaluate(c,t)
        self.assertEqual(a["catalog_entries"],67)
        self.assertEqual(a["design_coverage"],"67/67")
        self.assertEqual(a["verified_design_contracts"],"8/67")
        self.assertEqual(a["release_must_pass"],29)
        self.assertEqual(a["release_unresolved"],29)
        self.assertEqual(a["seven_jobs_full_engine_pass"],"0/7")
        self.assertEqual(a["real_engine_pass"],0)
        self.assertEqual(a["decision"],"DESIGN_NO_GO")
        rr={r["feature_id"]:r for r in t["rows"]}
        for fid in [f"P0D-{x:03d}" for x in range(8,16)]:
            r=rr[fid]
            self.assertEqual(r["design_contract_status"],"VERIFIED")
            self.assertEqual(r["release_scope"],"OWNER_RELEASE_REQUIRED")
            self.assertEqual(r["release_required"],True)
            self.assertIsNone(r["engine_proof"])
            self.assertTrue(r["design_revision_url"].startswith("https://github.com/"))
    def test_each_role_capability_has_separate_unproven_engine_proof(self):
        _,t=load()
        rr={r["feature_id"]:r for r in t["rows"]}
        for fid,caps in ROLE_CAPABILITIES.items():
            self.assertEqual(set(rr[fid]["capability_proofs"]),set(caps))
            self.assertTrue(all(v is None for v in rr[fid]["capability_proofs"].values()))
    def test_stripping_a_role_contract_keeps_release_no_go(self):
        c,t=load()
        t=deepcopy(t)
        next(r for r in t["rows"] if r["feature_id"]=="P0D-010")["design_contract_status"]="PENDING_ORIGINAL_REVIEW"
        a=evaluate(c,t)
        self.assertEqual(a["verified_design_contracts"],"7/67")
        self.assertIn("DESIGN_CONTRACT_UNVERIFIED:P0D-010",a["issues"])
    def test_legacy_assassin_name_denied_even_with_8_contracts(self):
        c,t=load()
        t=deepcopy(t)
        next(r for r in t["rows"] if r["feature_id"]=="P0D-011")["display_name"]="忍者"
        self.assertIn("ASSASSIN_ALIAS_INVALID",evaluate(c,t)["issues"])
    def test_unknown_future_feature_still_mapped_but_not_blocker(self):
        c,t=load()
        future=next(r for r in t["rows"] if r["release_scope"]=="DEFERRED_FUTURE_TRACK_ONLY")
        self.assertFalse(future["release_required"])
        self.assertEqual(future["design_contract_status"],"PENDING_ORIGINAL_REVIEW")
        self.assertEqual(evaluate(c,t)["release_unresolved"],29)

if __name__=="__main__":
    unittest.main()
