"""Negative controls: 67-row design trace must not accept source-only metadata."""
import copy
import unittest
from check_concept_trace import evaluate, ROLE_CAPABILITIES

HEAD = "a" * 40
def fixture():
    ids = [f"P0D-{n:03d}" for n in range(1, 68)]
    catalog = {"rows": [{"id": x, "release": "S1" if i < 5 else "S2+"} for i, x in enumerate(ids)]}
    rows = [{"feature_id": x, "concept_id": x,
             "design_source_url": "https://example.org/source",
             "design_revision_url": None, "design_contract_status": "PENDING_ORIGINAL_REVIEW",
             "must_behave": x, "catalog_release": catalog["rows"][i]["release"],
             "release_required": i < 5 or x in ROLE_CAPABILITIES or x == "P0D-008",
             "real_source_paths": [], "real_source_sha256": [],
             "engine_proof": None, "gap_type": "EVIDENCE_MISSING",
             "capability_proofs": {k: None for k in ROLE_CAPABILITIES.get(x, ())},
             **({"display_name": "暗殺者", "internal_role": "NINJA"} if x == "P0D-011" else {})}
            for i, x in enumerate(ids)]
    trace = {"schema": "P0D_DESIGN_TO_GAME_TRACE_V1", "official_rc_head": HEAD,
             "rows": rows, "art_gate": "ART_NO_GO", "mobile_gate": "MOBILE_NO_GO",
             "kid_fun_gate": "FUN_NO_GO", "owner_accepted": False}
    return catalog, trace

class TestTrace(unittest.TestCase):
    def test_unverified_67_rows_never_equal_actual_coverage(self):
        c, t = fixture()
        r = evaluate(c, t)
        self.assertEqual(r["inventory_covered"], 67)
        self.assertEqual(r["design_coverage"], "67/67")
        self.assertEqual(r["verified_design_contracts"], "0/67")
        self.assertEqual(r["seven_jobs_full_engine_pass"], "0/7")
        self.assertEqual(r["decision"], "DESIGN_NO_GO")
    def test_missing_catalog_row(self):
        c, t = fixture()
        c["rows"].pop()
        self.assertIn("CATALOG_67_NOT_VERIFIED", evaluate(c, t)["issues"])
    def test_missing_feature_trace(self):
        c, t = fixture()
        t["rows"].pop()
        self.assertTrue(any(x.startswith("UNMAPPED_FEATURE_IDS:") for x in evaluate(c, t)["issues"]))
    def test_duplicate_feature_trace(self):
        c, t = fixture()
        t["rows"][1]["feature_id"] = "P0D-001"
        self.assertIn("TRACE_INVALID_OR_DUPLICATE_IDS", evaluate(c, t)["issues"])
    def test_release_override_even_when_old_s2(self):
        c, t = fixture()
        self.assertEqual(evaluate(c, t)["release_must_pass"], 13)
        t["rows"][10]["release_required"] = False
        self.assertIn("RELEASE_REQUIREMENT_MISMATCH:P0D-011", evaluate(c, t)["issues"])
    def test_assassin_player_name_and_internal_id(self):
        c, t = fixture()
        t["rows"][10]["display_name"] = "忍者"
        self.assertIn("ASSASSIN_ALIAS_INVALID", evaluate(c, t)["issues"])
    def test_source_without_engine_is_unknown(self):
        c, t = fixture()
        r = t["rows"][8]
        r["real_source_paths"] = ["server/Game.server.luau"]
        r["real_source_sha256"] = ["b" * 64]
        self.assertIn("ENGINE_UNKNOWN:P0D-009", evaluate(c, t)["issues"])
    def test_unverified_role_capabilities_not_counted(self):
        c, t = fixture()
        row = t["rows"][13]
        row["design_contract_status"] = "VERIFIED"
        row["design_revision_url"] = "https://example.org/revision"
        row["real_source_paths"] = ["server/BeastService.luau"]
        row["real_source_sha256"] = ["b" * 64]
        self.assertIn("ROLE_CAPABILITY_ENGINE_UNKNOWN:P0D-014:mount", evaluate(c, t)["issues"])
        self.assertEqual(evaluate(c, t)["seven_jobs_full_engine_pass"], "0/7")
    def test_false_owner_or_art_go_not_accepted(self):
        c, t = fixture()
        t["owner_accepted"] = "true"
        t["art_gate"] = "ART_GO"
        self.assertEqual(evaluate(c, t)["decision"], "DESIGN_NO_GO")
        self.assertIn("OWNER_NOT_ACCEPTED", evaluate(c, t)["issues"])
    def test_untrusted_proof_head_rejected(self):
        c, t = fixture()
        t["rows"][8]["capability_proofs"]["heavy_attack"] = {
            "result": "PASS", "official_rc_head": "b" * 40,
            "recording_url": "https://example.org/clip",
            "device": "Android", "reviewer": "QA",
            "observed_effect": "damage", "same_head_build_url": "https://example.org/run"}
        self.assertIn("ROLE_CAPABILITY_ENGINE_UNKNOWN:P0D-009:heavy_attack", evaluate(c, t)["issues"])

if __name__ == "__main__":
    unittest.main()
