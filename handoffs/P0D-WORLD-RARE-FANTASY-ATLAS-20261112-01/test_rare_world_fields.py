from pathlib import Path
import json
import unittest

P = Path(__file__).with_name("WORLD_RARE_FIELDS_V2.json")
D = json.loads(P.read_text(encoding="utf-8"))

class RareFieldContract(unittest.TestCase):
    def test_catalog_shape(self):
        self.assertEqual(D["status"], "DESIGN_ONLY")
        self.assertEqual(len(D["worlds"]), 4)
        self.assertEqual(len(D["mechanics"]), 12)
        self.assertEqual(len(D["neutral_npcs"]), 8)
    def test_ids_unique(self):
        for group in ("worlds", "mechanics", "neutral_npcs"):
            ids = [v["id"] for v in D[group]]
            self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([v["id"] for v in D["mechanics"]], ["WF-%02d" % i for i in range(13,25)])
    def test_world_links(self):
        worlds = {v["id"] for v in D["worlds"]}
        self.assertEqual(worlds, {"SPACE", "CELESTIAL", "EMBER", "ECLIPSE"})
        for name in ("mechanics", "neutral_npcs"):
            self.assertTrue(all(v["world_id"] in worlds for v in D[name]))
    def test_promotional_and_tactical_contract(self):
        fields = ("child_one_action","three_second_cue","gameplay_meaning","job_item_tactic","counterplay","marketing_hook_7s","marketing_script_15s","H0","H1","rollback","perf_budget")
        for m in D["mechanics"]:
            for f in fields:
                self.assertTrue(isinstance(m.get(f), str) and len(m[f]) >= 4, (m["id"],f))
            self.assertEqual(m["phase"], "DESIGN_ONLY")
            self.assertTrue(m["requires_real_studio"])
    def test_neutral_canon_not_assumed(self):
        for n in D["neutral_npcs"]:
            self.assertEqual(n["phase"], "DESIGN_ONLY")
            self.assertEqual(n["canon_id"], "UNASSIGNED_D18_COMPAT_REVIEW_REQUIRED")
            self.assertIn("課金なし", n["fairness"])
    def test_mobility_gating(self):
        contract = "\n".join(D["principles"])
        self.assertIn("Workspace.Gravity", contract)
        self.assertIn("無料", contract)
        self.assertIn("S1リリース", contract)
    def test_no_unverified_claims(self):
        self.assertEqual(D["governance"]["real_game_adoption_count"], 0)
        self.assertEqual(D["governance"]["Studio"], "NOT_TESTED")
        self.assertFalse(D["governance"]["S1_release_blocker"])
        self.assertTrue(all(v == "UNKNOWN" for v in D["measurement"].values()))
    def test_source_provenance(self):
        self.assertGreaterEqual(len(D["sources"]), 5)
        self.assertTrue(any(s["kind"] == "PRIMARY_TECH_DOC" for s in D["sources"]))
        self.assertTrue(any(s["kind"] == "VIDEO_DESCRIPTION_NOT_WATCHED" for s in D["sources"]))

if __name__ == "__main__":
    unittest.main()
