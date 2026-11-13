"""Product studio six-log bridge tests. These six logs are explicitly synthetic fixtures:
not a real Studio run, not actual phone/child evidence, not release authorization.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
bridge=load(ROOT/"bridge_studio_evidence.py","p0d_bridge_under_test")
decide=load(ROOT/"decide_next_ab.py","p0d_original_decider")

def fake_manual():
    return {
        "adoption_id":"P0D-FUN-H1-001",
        "owner_confirmation":"OWNER_MANUALLY_PLAYED_PRIVATE_STUDIO",
        "h0_place_sha256":decide.H0_SHA,
        "h1_place_sha256":decide.H1_SHA,
        "h0":{"studio_2client":True,"server_red_blue_logs":True,"fun_90s_score":2},
        "h1":{
            "studio_2client":True,"server_red_blue_logs":True,"mobile_checked":True,
            "egg_pickup":True,"egg_return":True,"sky_with_egg":True,"sea_with_egg":True,
            "guide_helpful":True,"mobile_ui_readable":True,"first_egg_feels_rewarding":True,
            "return_route_too_slow":False,"desire_rematch":True,"technical_errors":False,
            "first_action_seconds":38,"fun_90s_score":4
        }
    }

class TestStudioProductProbeBridge(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="synthetic_p0d_product_bridge_")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.paths={}
        for version in ("h0","h1"):
            for who in ("server","red","blue"):
                name=f"{version}_{who}"
                path=self.root/(name+".txt")
                extra=f"version={version} qa_synthetic=1 stream={who}\n"
                if who=="server":
                    data=f"2026-11-13 03:15:00 P0D_STUDIO_PROBE_V1 SERVER kind=MAP_CHECK phase=ACTIVE team=NONE serial=1\n{extra}"
                else:
                    team=who.upper()
                    data=(f"P0D_STUDIO_PROBE_V1 CLIENT kind=START phase=LOBBY team={team} serial=1\n"
                          f"P0D_STUDIO_PROBE_V1 CLIENT kind=PHASE phase=ACTIVE team={team} serial=1\n"
                          +extra)
                path.write_text(data,encoding="utf-8")
                self.paths[name]=path
        self.manual=fake_manual()
    def test_original_parser_is_exact_approved_blob(self):
        raw=bridge.VENDOR.read_bytes()
        self.assertEqual(bridge.gitblob(raw),bridge.VENDOR_GIT_BLOB)
        self.assertEqual(bridge.VENDOR_GIT_BLOB,"d2e4580e1ea417225d7e75a6ea83b559a4f677ac")
    def test_vendor_parser_is_original_and_never_marks_manual_pass(self):
        p=bridge.load_original_parser()
        r=p.process(self.paths["h0_server"],self.paths["h0_red"],self.paths["h0_blue"])
        self.assertEqual(r["status"],"OBSERVED_ONLY_NOT_STUDIO_PASS")
        self.assertEqual(r["manual_case_pass_count"],0)
        self.assertFalse(r["physical_two_client_certified"])
        self.assertFalse(r["real_mobile_certified"])
    def test_blank_owner_input_keeps_hold_despite_full_synthetic_probes(self):
        blank=json.loads((ROOT/"OWNER_STUDIO_H0_H1_BLANK_NOT_TESTED.json").read_text(encoding="utf-8"))
        self.assertEqual(bridge.judge_manual_and_probe(blank,self.paths)["product_decision"],
                         "HOLD_OWNER_MUST_ACK_LOG_REVIEW")
    def test_no_owner_attestation_cannot_accept_even_full_probes(self):
        m=copy.deepcopy(self.manual);m["owner_confirmation"]="CI_ONLY"
        r=bridge.judge_manual_and_probe(m,self.paths)
        self.assertEqual(r["product_decision"],"HOLD_REAL_PLAY_REQUIRED")
    def test_clean_fake_fixture_cannot_grant_release_or_human_certification(self):
        r=bridge.judge_manual_and_probe(self.manual,self.paths)
        self.assertEqual(r["product_decision"],"RECOMMEND_SOLE_RC_REVIEW")
        for field in ("real_roblox_engine_two_client_certified","real_phone_certified",
                      "manual_owner_fun_certified","official_rc_adopted","publish_authorized",
                      "paid_features_authorized"):
            self.assertFalse(r[field],field)
        self.assertEqual(len(r["h0_h1_probe_observations_only"]),2)
        self.assertEqual(r["h0_h1_probe_observations_only"]["h1"]["manual_cases_accepted"],0)
    def test_evidence_missing_one_log_refuses(self):
        paths=dict(self.paths);paths.pop("h1_blue")
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,paths)["product_decision"],
                         "HOLD_NEED_SIX_DISTINCT_LOGS")
    def test_one_log_path_reused_refuses(self):
        paths=dict(self.paths);paths["h1_blue"]=paths["h0_blue"]
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,paths)["product_decision"],
                         "HOLD_NEED_SIX_DISTINCT_LOGS")
    def test_identical_bytes_h0_h1_rejected_even_different_paths(self):
        self.paths["h1_server"].write_bytes(self.paths["h0_server"].read_bytes())
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_REUSED_SESSION_LOGS")
    def test_mixed_client_server_stream_rejected(self):
        self.paths["h1_red"].write_text("P0D_STUDIO_PROBE_V1 SERVER kind=MAP_CHECK\n",encoding="utf-8")
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_PROBE_LOG_INVALID")
    def test_missing_RED_live_phase_fails_closed(self):
        self.paths["h1_red"].write_text(
            "P0D_STUDIO_PROBE_V1 CLIENT kind=START team=RED phase=LOBBY\n"
            "P0D_STUDIO_PROBE_V1 CLIENT kind=PHASE team=RED phase=COUNTDOWN\n",encoding="utf-8")
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_INCOMPLETE_ACTIVE_MATCH")
    def test_missing_BLUE_team_phase_rejected(self):
        self.paths["h1_blue"].write_text(
            "P0D_STUDIO_PROBE_V1 CLIENT kind=START team=BLUE phase=LOBBY\n"
            "P0D_STUDIO_PROBE_V1 CLIENT kind=PHASE team=RED phase=ACTIVE\n",encoding="utf-8")
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_PROBE_LOG_INVALID")
    def test_warning_gates_before_fun(self):
        with self.paths["h0_server"].open("a",encoding="utf-8") as out:
            out.write("P0D_STUDIO_PROBE_V1 SERVER kind=WARN_MAP phase=ACTIVE reason=NO_EGG\n")
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_REVIEW_STUDIO_WARNINGS")
    def test_unrelated_user_chat_text_is_not_returned(self):
        with self.paths["h0_server"].open("a",encoding="utf-8") as out:
            out.write("secret_chat=username123 contact=email@example.com\n")
        out=bridge.judge_manual_and_probe(self.manual,self.paths)
        self.assertNotIn("username123",json.dumps(out))
        self.assertNotIn("email@example.com",json.dumps(out))
    def test_manual_missing_h1_map_rejected_not_crash(self):
        m=copy.deepcopy(self.manual);m["h1"]=None
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["product_decision"],
                         "HOLD_OWNER_MUST_ACK_LOG_REVIEW")
    def test_missing_owner_log_review_rejected(self):
        m=copy.deepcopy(self.manual);m["h0"]["server_red_blue_logs"]=False
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["product_decision"],
                         "HOLD_OWNER_MUST_ACK_LOG_REVIEW")
    def test_no_mobile_check_holds_despite_real_like_probes(self):
        m=copy.deepcopy(self.manual);m["h1"]["mobile_checked"]=False
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["product_decision"],
                         "HOLD_MOBILE_EVIDENCE")
    def test_egg_failure_selects_engine_fix_not_cosmetics(self):
        m=copy.deepcopy(self.manual);m["h1"]["egg_return"]=False
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["next_experiment"],"FIX_GAME_ENGINE")
    def test_rock_sky_route_failure_selects_physics_fix(self):
        m=copy.deepcopy(self.manual);m["h1"]["sky_with_egg"]=False
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["next_experiment"],"FIX_ROUTE_ENGINE")
    def test_egg_not_celebratory_selects_existing_266(self):
        m=copy.deepcopy(self.manual);m["h1"]["first_egg_feels_rewarding"]=False
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["next_experiment"],"FIRST_EGG_JOY")
    def test_slow_goal_finding_selects_existing_219_compass(self):
        m=copy.deepcopy(self.manual);m["h1"]["first_action_seconds"]=75
        self.assertEqual(bridge.judge_manual_and_probe(m,self.paths)["next_experiment"],"GUIDE_COMPASS")
    def test_no_bypass_from_auto_script_marking_human_pass(self):
        m=copy.deepcopy(self.manual);m["human_ux_certified"]=True
        r=bridge.judge_manual_and_probe(m,self.paths)
        self.assertFalse(r["manual_owner_fun_certified"])
        self.assertFalse(r["publish_authorized"])
    def test_oversized_input_refuses_without_allocating(self):
        p=self.paths["h1_server"]
        with p.open("wb") as w:
            w.truncate(15*1024*1024+1)
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_NEED_SIX_DISTINCT_LOGS")
    def test_empty_observation_rejected(self):
        self.paths["h0_server"].write_text("no probe lines here\n",encoding="utf-8")
        self.assertEqual(bridge.judge_manual_and_probe(self.manual,self.paths)["product_decision"],
                         "HOLD_PROBE_LOG_INVALID")
    def test_H0_H1_session_logs_not_equal(self):
        r=bridge.judge_manual_and_probe(self.manual,self.paths)
        sha=r["h0_h1_probe_observations_only"]
        self.assertNotEqual(sha["h0"]["log_sha256"]["server"],sha["h1"]["log_sha256"]["server"])
    def test_fake_3log_probe_does_not_write_user_data(self):
        before={k:v.read_bytes() for k,v in self.paths.items()}
        r=bridge.judge_manual_and_probe(self.manual,self.paths)
        self.assertFalse(r["source_content_personal_information_retained"])
        after={k:v.read_bytes() for k,v in self.paths.items()}
        self.assertEqual(before,after)
if __name__=="__main__":unittest.main()
