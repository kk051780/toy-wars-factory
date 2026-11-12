#!/usr/bin/env python3
"""Offline schema and anti-counterfeit QA for D18 Batch4 planning-only cards."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/six_action_cards.json").read_text(encoding="utf-8"))

class IdeaCardsTest(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(DATA["game_id"], "TRAP_RAIDERS")
        self.assertEqual(DATA["schema"], "P0D_PRODUCT_STUDIO_ACTION_CARDS_V1")
        self.assertEqual(DATA["stage"], "PRELAUNCH")
        self.assertTrue(DATA["planning_only"])

    def test_canonical_six(self):
        cards = DATA["six_idea_cards"]
        self.assertEqual(len(cards), 6)
        self.assertEqual({x["id"] for x in cards}, {
            "TRCA-BE-036","TRCA-SP-009","TRCA-VE-009",
            "TRCA-WE-009","TRCA-ZO-018","TRCA-TR-027"})
        self.assertEqual({x["category"] for x in cards},
            {"BE","SP","VE","WE","ZO","TR"})
        for item in cards:
            self.assertRegex(item["id"], r"^TRCA-(BE|SP|VE|WE|ZO|TR)-[0-9]{3}$")
            self.assertEqual(item["rarity"], "ミシック")
            self.assertEqual(len(item["shape"]), 3)
            for key in ("world","name","child_action","job_synergy","effect_candidate",
                        "counter","abuse_guard","child_cue"):
                self.assertTrue(item[key], (item["id"], key))

    def test_not_fake_3d_game_progress(self):
        self.assertEqual(DATA["source_3d_before"], 30)
        self.assertEqual(DATA["source_3d_after"], 30)
        self.assertEqual(DATA["not_started_3d_count"], 42)
        self.assertNotIn("REAL_STUDIO_PASS", json.dumps(DATA))

    def test_falsifiable_experiments_and_market(self):
        self.assertEqual(len(DATA["experiments"]), 2)
        for item in DATA["experiments"]:
            for key in ("H0","H1","primary_metric","decision_gate","rollback"):
                self.assertTrue(item[key])
        self.assertEqual(len(DATA["market_sources"]), 2)
        for s in DATA["market_sources"]:
            self.assertTrue(s["url"].startswith("https://"))
            self.assertTrue(s["observation"] and s["interpretation"])

    def test_originality_and_child_safety_gates(self):
        s = " ".join(DATA["rules"])
        self.assertIn("No direct egg teleport", s)
        self.assertIn("no purchase-only gameplay advantage", s)
        self.assertIn("Children", s)

if __name__ == "__main__":
    unittest.main()
