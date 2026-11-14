"""False positive prevention for low-end mobile + child first-play quality."""
import copy,json,unittest
from pathlib import Path
import check_mobile_fun as gate
ROOT=Path(__file__).resolve().parent
BASE=json.loads((ROOT/"MOBILE_KID_FUN_EVIDENCE_TEMPLATE.json").read_text("utf8"))

def ready():
    d=copy.deepcopy(BASE)
    for key,limits in gate.LIMITS.items():
        x=d["devices"][key]
        x.update({"device_model":"real test hardware","session_minutes":16,
                  "crash_free":True,"oom_free":True,"p10_fps":limits["p10_fps"]})
        if "median_fps" in limits:
            x.update({"median_fps":limits["median_fps"],
                      "warm_fps_drop_fraction":0.10,
                      "peak_memory_mb":300,"join_to_control_seconds":12,
                      "touch_attack_works":True})
    d["first_play"].update({"consent_appropriate":True,"test_sessions":3,
      "move_seconds":10,"first_attack_seconds":25,"first_real_enemy_hit_seconds":50,
      "objective_understood_seconds":120,"first_three_minutes_fun_rating":4.2,
      "solo_playable":True,"can_understand_egg_theft":True,
      "attack_actual_hp_changes":True,"no_persistent_guide":True})
    d["critical_blockers"]=[]
    d["independent_reviewer"]="test reviewer"
    d["evidence_links"]=["https://example.com/review-proof"] # schema-only; not genuine evidence
    return d

class MobileKidFun(unittest.TestCase):
    def test_blank_form_is_no_go(self):
        out=gate.gate(BASE)
        self.assertEqual(out["status"],"EVIDENCE_INCOMPLETE")
        self.assertEqual(out["fun_decision"],"FUN_NO_GO")
    def test_schema_only_green_never_owner_approves(self):
        out=gate.gate(ready())
        self.assertEqual(out["status"],"REVIEW_READY_OWNER_PENDING")
        self.assertFalse(out["owner_accepted"])
        self.assertEqual(out["mobile_decision"],"MOBILE_NO_GO")
    def test_mobile_fps_drop_hard_fail(self):
        d=ready();d["devices"]["low_android"]["p10_fps"]=19
        self.assertIn("FPS_BELOW_TARGET_OR_UNKNOWN:low_android/p10_fps",gate.gate(d)["violations"])
    def test_heat_after_15min_hard_fail(self):
        d=ready();d["devices"]["mid_android"]["warm_fps_drop_fraction"]=0.3
        self.assertIn("THERMAL_DROP_UNKNOWN_OR_OVER20PCT:mid_android",gate.gate(d)["violations"])
    def test_no_actual_hp_damage_is_no_go(self):
        d=ready();d["first_play"]["attack_actual_hp_changes"]=False
        self.assertIn("GAMEPLAY_CONDITION_FAIL_OR_UNKNOWN:attack_actual_hp_changes",gate.gate(d)["violations"])
    def test_no_consent_is_no_go(self):
        d=ready();d["first_play"]["consent_appropriate"]=False
        self.assertIn("SUPERVISED_CONSENTED_TEST_NOT_CONFIRMED",gate.gate(d)["violations"])
    def test_early_fun_slow_is_no_go(self):
        d=ready();d["first_play"]["first_attack_seconds"]=150
        self.assertIn("FTUE_UNKNOWN_OR_TOO_SLOW:first_attack_seconds",gate.gate(d)["violations"])
if __name__=="__main__":unittest.main()
