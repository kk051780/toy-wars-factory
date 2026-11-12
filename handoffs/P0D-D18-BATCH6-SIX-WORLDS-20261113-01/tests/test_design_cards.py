#!/usr/bin/env python3
import json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
cards=json.loads((ROOT/"design/six_play_cards.json").read_text(encoding="utf-8"))
class Cards(unittest.TestCase):
 def test_six_unique_pinned_source_ids(self):
  d=json.loads((ROOT/"data/six_pilot_geometry.json").read_text(encoding="utf-8"))
  self.assertEqual({c["id"] for c in cards["characters"]},set(d["characters"]))
  self.assertEqual(len(cards["characters"]),6)
  for c in cards["characters"]:
   can=d["characters"][c["id"]]
   for k in ("name","category","rarity","world"):
    self.assertEqual(c[k],can[k])
 def test_actions_have_child_ux_and_counterplay(self):
  for c in cards["characters"]:
   for k in ("recognition","player_action","profession_synergy","proposal","counterplay"):
    self.assertGreaterEqual(len(c[k]),5)
   self.assertGreaterEqual(len(c["hard_limits"]),3)
 def test_future_only_and_noncommercial(self):
  self.assertEqual(cards["status"],"DESIGN_HYPOTHESIS_ONLY_NOT_IMPLEMENTED")
  self.assertFalse(cards["gameplay_impl"])
  self.assertFalse(cards["studio_tested"])
  self.assertFalse(cards["purchase_enabled"])
 def test_review_hypotheses_not_claimed_results(self):
  self.assertEqual(len(cards["experiments"]),2)
  for x in cards["experiments"]:
   self.assertIn("H0",x);self.assertIn("H1",x);self.assertIn("metric",x)
   self.assertEqual(x["observed_result"],"UNKNOWN")
if __name__=="__main__":unittest.main()
