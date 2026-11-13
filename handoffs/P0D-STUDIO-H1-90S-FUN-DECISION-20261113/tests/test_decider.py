"""Pure policy tests. ALL owner observations here are intentionally SYNTHETIC fixtures,
not evidence of a real Roblox Studio human playtest.
"""
import importlib.util
import json
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("decide_next_ab",BASE/"decide_next_ab.py")
assert spec and spec.loader
logic=importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)

def fake_owner_observation():
    return {
      "adoption_id":"P0D-FUN-H1-001",
      "owner_confirmation":"OWNER_MANUALLY_PLAYED_PRIVATE_STUDIO",
      "h0_place_sha256":logic.H0_SHA,
      "h1_place_sha256":logic.H1_SHA,
      "h0":{"studio_2client":True,"server_red_blue_logs":True,"fun_90s_score":2},
      "h1":{
          "studio_2client":True,"server_red_blue_logs":True,"mobile_checked":True,
          "egg_pickup":True,"egg_return":True,
          "sky_with_egg":True,"sea_with_egg":True,
          "guide_helpful":True,"mobile_ui_readable":True,
          "first_egg_feels_rewarding":True,"return_route_too_slow":False,
          "desire_rematch":True,"technical_errors":False,
          "first_action_seconds":40,"fun_90s_score":4
      }
    }

class TestP0DProductEvidenceDecider(unittest.TestCase):
    def go(self,x):
        r=logic.evaluate(x)
        self.assertIs(r["publish_authorized"],False)
        self.assertIs(r["official_rc_adopted"],False)
        self.assertIs(r["paid_features_authorized"],False)
        self.assertIs(r["studio_2client_actually_run_by_this_tool"],False)
        self.assertIs(r["human_acceptance_granted_by_this_tool"],False)
        return r
    def test_actual_template_is_unperformed_and_holds(self):
        p=json.loads((BASE/"OWNER_STUDIO_H0_H1_BLANK_NOT_TESTED.json").read_text())
        self.assertEqual(p["evidence_status"],"NOT_TESTED")
        self.assertEqual(self.go(p)["product_decision"],"HOLD_REAL_PLAY_REQUIRED")
    def test_invalid_non_object_holds(self):
        self.assertEqual(self.go(None)["product_decision"],"HOLD_INVALID_INPUT")
    def test_other_adoption_holds(self):
        a=fake_owner_observation();a["adoption_id"]="P0D-S2"
        self.assertEqual(self.go(a)["product_decision"],"HOLD_WRONG_ADOPTION")
    def test_different_H0_binary_blocks_unmatched_test(self):
        a=fake_owner_observation();a["h0_place_sha256"]="0"*64
        self.assertEqual(self.go(a)["product_decision"],"HOLD_BINARY_PROVENANCE")
    def test_different_H1_binary_blocks_unmatched_test(self):
        a=fake_owner_observation();a["h1_place_sha256"]="0"*64
        self.assertEqual(self.go(a)["product_decision"],"HOLD_BINARY_PROVENANCE")
    def test_self_proclaimed_qa_success_not_owner_confirmation(self):
        a=fake_owner_observation();a["owner_confirmation"]="CI_PASS"
        self.assertEqual(self.go(a)["product_decision"],"HOLD_REAL_PLAY_REQUIRED")
    def test_H1_2client_unverified_holds(self):
        a=fake_owner_observation();a["h1"]["studio_2client"]=False
        self.assertEqual(self.go(a)["product_decision"],"HOLD_REAL_PLAY_REQUIRED")
    def test_H0_2client_unverified_holds(self):
        a=fake_owner_observation();a["h0"]["studio_2client"]=False
        self.assertEqual(self.go(a)["product_decision"],"HOLD_REAL_PLAY_REQUIRED")
    def test_red_blue_server_logs_missing_holds(self):
        a=fake_owner_observation();a["h1"]["server_red_blue_logs"]=False
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MISSING_EVIDENCE")
    def test_mobile_not_tested_holds(self):
        a=fake_owner_observation();a["h1"]["mobile_checked"]=False
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MOBILE_EVIDENCE")
    def test_missing_fun_score_holds(self):
        a=fake_owner_observation();a["h0"]["fun_90s_score"]=None
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MISSING_EVIDENCE")
    def test_negative_fun_score_holds(self):
        a=fake_owner_observation();a["h1"]["fun_90s_score"]=-1
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MISSING_EVIDENCE")
    def test_string_time_is_not_accepted(self):
        a=fake_owner_observation();a["h1"]["first_action_seconds"]="15"
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MISSING_EVIDENCE")
    def test_boolean_disguised_as_fun_score_not_accepted(self):
        a=fake_owner_observation();a["h0"]["fun_90s_score"]=True
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MISSING_EVIDENCE")
    def test_missing_objective_observation_holds(self):
        a=fake_owner_observation();a["h1"]["sky_with_egg"]=None
        self.assertEqual(self.go(a)["product_decision"],"HOLD_MISSING_EVIDENCE")
    def test_actual_technical_error_blocks_cosmetics(self):
        a=fake_owner_observation();a["h1"]["technical_errors"]=True
        r=self.go(a);self.assertEqual(r["product_decision"],"STOP_FIX_TECHNICAL")
        self.assertEqual(r["next_experiment"],"FIX_GAME_ENGINE")
    def test_egg_return_failure_first_priority(self):
        a=fake_owner_observation();a["h1"]["egg_return"]=False
        self.assertEqual(self.go(a)["next_experiment"],"FIX_GAME_ENGINE")
    def test_unwalkable_sky_route_blocks_other_experiments(self):
        a=fake_owner_observation();a["h1"]["sky_with_egg"]=False
        r=self.go(a);self.assertEqual(r["next_experiment"],"FIX_ROUTE_ENGINE")
    def test_unwalkable_sea_route_blocks_other_experiments(self):
        a=fake_owner_observation();a["h1"]["sea_with_egg"]=False
        r=self.go(a);self.assertEqual(r["next_experiment"],"FIX_ROUTE_ENGINE")
    def test_bad_phone_hud_selects_existing_260_only(self):
        a=fake_owner_observation();a["h1"]["mobile_ui_readable"]=False
        self.assertEqual(self.go(a)["next_experiment"],"CHILD_HUD")
    def test_late_first_action_selects_existing_compass(self):
        a=fake_owner_observation();a["h1"]["first_action_seconds"]=75
        self.assertEqual(self.go(a)["next_experiment"],"GUIDE_COMPASS")
    def test_not_helpful_guide_selects_compass(self):
        a=fake_owner_observation();a["h1"]["guide_helpful"]=False
        self.assertEqual(self.go(a)["next_experiment"],"GUIDE_COMPASS")
    def test_only_after_passable_routes_short_route(self):
        a=fake_owner_observation();a["h1"]["return_route_too_slow"]=True
        self.assertEqual(self.go(a)["next_experiment"],"SHORT_ROUTE")
    def test_weak_egg_joy_selects_266(self):
        a=fake_owner_observation();a["h1"]["first_egg_feels_rewarding"]=False
        self.assertEqual(self.go(a)["next_experiment"],"FIRST_EGG_JOY")
    def test_H1_duller_than_H0_selects_one_joy_variant(self):
        a=fake_owner_observation();a["h1"]["fun_90s_score"]=1
        self.assertEqual(self.go(a)["next_experiment"],"FIRST_EGG_JOY")
    def test_boring_rematch_defers_S2_mechanics(self):
        a=fake_owner_observation();a["h1"]["desire_rematch"]=False
        self.assertEqual(self.go(a)["product_decision"],"DEFER_NEW_S1_CONTENT")
    def test_success_is_only_review_not_release(self):
        a=fake_owner_observation()
        r=self.go(a)
        self.assertEqual(r["product_decision"],"RECOMMEND_SOLE_RC_REVIEW")
        self.assertIs(r["next_experiment"],None)
        self.assertIs(r["evidence_complete"],True)
    def test_early_action_at_60_seconds_is_eligible(self):
        a=fake_owner_observation();a["h1"]["first_action_seconds"]=60
        self.assertEqual(self.go(a)["product_decision"],"RECOMMEND_SOLE_RC_REVIEW")
if __name__=="__main__":unittest.main()
