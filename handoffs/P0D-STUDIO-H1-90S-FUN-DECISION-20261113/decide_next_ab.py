#!/usr/bin/env python3
"""TRAP RAIDERS H1 product-office A/B decision aid. NOT a game or release controller.

Manual observations ONLY, NEVER platform analytics or autonomous Studio evidence.
This tool proposes *one* next experiment; it has no ability to merge/publish/pay.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

H0_SHA = "f0d45aae5469cdb862e3642b65fdc5c4c7da8ada924b3a0d48291cabca89344b"
H1_SHA = "f290c6fccfa8796220fa4f13000a53ed8f8ec7c7a269951280938aff3240ee7e"
# Exact SHA256 of ORIGINAL QA-only H0 23 and H1 30 script Roblox Studio Places, not UI variants.
# SHA is a safety pointer, not a game acceptance condition in itself.
MARKET_ASOF = "2026-11-13"
ADOPTION_ID = "P0D-FUN-H1-001"

# Ordered highest-safety-to-lowest decisions. No automatic public release.
VARIANT = {
    "FIX_GAME_ENGINE": {"source": "#255/#220 existing H1 owner", "reason": "Real Studio errors or broken game victory/egg path"},
    "FIX_ROUTE_ENGINE": {"source": "#255/#253 route author; #262 only for distance A/B once physics fixed",
                         "reason": "Real 3D sea/sky egg carry route failed"},
    "CHILD_HUD": {"source": "#260 full H1 kid UI", "reason": "Existing HUD/touch button unclear"},
    "GUIDE_COMPASS": {"source": "#219 D18 objective compass", "reason": "First egg action too slow or goal direction confusing"},
    "SHORT_ROUTE": {"source": "#262 short sea/sky routes", "reason": "Egg return is physically possible but too slow"},
    "FIRST_EGG_JOY": {"source": "#266 first real egg success local joy", "reason": "Child understands objective but first win lacks payoff"},
    "H2_REPLAY_TACTICS": {"source": "#267 optional Star Jump or neutral creature future S2",
                          "reason": "Base H1 was fun initially but players did not want rematch"}
}
SCHEMA_KEYS_BOOL=("studio_2client","server_red_blue_logs","mobile_checked",
                  "egg_pickup","egg_return","sky_with_egg","sea_with_egg",
                  "guide_helpful","mobile_ui_readable","first_egg_feels_rewarding",
                  "return_route_too_slow","desire_rematch","technical_errors")
SCHEMA_KEYS_NUMBER=("first_action_seconds","fun_90s_score")

def _numeric(value: object, minimum: float, maximum: float) -> bool:
    return isinstance(value,(float,int)) and not isinstance(value,bool) and minimum<=value<=maximum

def _result(status: str, next_step: str | None, reason: str, complete: bool=False) -> dict:
    return {
        "adoption_id":ADOPTION_ID,
        "product_decision":status, "next_experiment":next_step,
        "reason":reason,"evidence_complete":complete,
        "official_rc_adopted":False,
        "publish_authorized":False,
        "paid_features_authorized":False,
        "studio_2client_actually_run_by_this_tool":False,
        "human_acceptance_granted_by_this_tool":False
    }

def evaluate(obs: object) -> dict:
    if not isinstance(obs,dict):
        return _result("HOLD_INVALID_INPUT",None,"Input must be one JSON object.")
    if obs.get("adoption_id")!=ADOPTION_ID:
        return _result("HOLD_WRONG_ADOPTION",None,"Only existing H1 adoption id allowed.")
    if obs.get("h0_place_sha256")!=H0_SHA or obs.get("h1_place_sha256")!=H1_SHA:
        return _result("HOLD_BINARY_PROVENANCE",None,"Compare exact H0/H1 QA-only binaries first; do not mix different builds.")
    if obs.get("owner_confirmation")!="OWNER_MANUALLY_PLAYED_PRIVATE_STUDIO":
        return _result("HOLD_REAL_PLAY_REQUIRED",None,"No OWNER real Studio session has been attested; no synthetic result.")
    h0,h1=obs.get("h0"),obs.get("h1")
    if not isinstance(h0,dict) or not isinstance(h1,dict):
        return _result("HOLD_MISSING_EVIDENCE",None,"Need both manually observed H0 and H1 results.")
    if h0.get("studio_2client") is not True or h1.get("studio_2client") is not True:
        return _result("HOLD_REAL_PLAY_REQUIRED",None,"Two real clients for EACH version required.")
    if h1.get("server_red_blue_logs") is not True or h0.get("server_red_blue_logs") is not True:
        return _result("HOLD_MISSING_EVIDENCE",None,"Keep SERVER, RED and BLUE logs for both versions.")
    if h1.get("mobile_checked") is not True:
        return _result("HOLD_MOBILE_EVIDENCE",None,"Actual phone/representative phone QA still required.")
    if not _numeric(h0.get("fun_90s_score"),0,5):
        return _result("HOLD_MISSING_EVIDENCE",None,"H0 first90s human fun score 0-5 required.")
    for key in SCHEMA_KEYS_NUMBER:
        if not _numeric(h1.get(key),0,3600 if key.endswith("seconds") else 5):
            return _result("HOLD_MISSING_EVIDENCE",None,f"H1 measured {key} required.")
    for key in SCHEMA_KEYS_BOOL:
        if key in ("studio_2client","server_red_blue_logs","mobile_checked"):continue
        if type(h1.get(key)) is not bool:
            return _result("HOLD_MISSING_EVIDENCE",None,f"H1 manually observed {key} True/False required.")
    if h1["technical_errors"]:
        return _result("STOP_FIX_TECHNICAL", "FIX_GAME_ENGINE",
                       "Observed Studio errors; resolve engine issue before comparing creative features.",True)
    if not h1["egg_pickup"] or not h1["egg_return"]:
        return _result("STOP_FIX_CORE_LOOP","FIX_GAME_ENGINE",
                       "Real egg pickup and return is the core fun; no cosmetic variant can mask failure.",True)
    if not h1["sky_with_egg"] or not h1["sea_with_egg"]:
        return _result("STOP_FIX_TRAVERSABILITY","FIX_ROUTE_ENGINE",
                       "Actual egg carrier couldn't traverse both tactical alt routes; source geometry alone is inadequate.",True)
    if not h1["mobile_ui_readable"]:
        return _result("REVISE_ONE_AB_ONLY","CHILD_HUD",
                       "Choose ONE UI source variant to A/B; no new server authority.",True)
    if h1["first_action_seconds"]>60 or not h1["guide_helpful"]:
        return _result("REVISE_ONE_AB_ONLY","GUIDE_COMPASS",
                       "Current goal-finding friction; compare existing D18 compass to current original guide.",True)
    if h1["return_route_too_slow"]:
        return _result("REVISE_ONE_AB_ONLY","SHORT_ROUTE",
                       "Only after real route is passable, compare #262 shorter physical paths.",True)
    if not h1["first_egg_feels_rewarding"] or h1["fun_90s_score"]<=h0["fun_90s_score"]:
        return _result("REVISE_ONE_AB_ONLY","FIRST_EGG_JOY",
                       "Core works, but first moment isn't more exciting than H0; compare #266 egg joy.",True)
    if not h1["desire_rematch"]:
        return _result("DEFER_NEW_S1_CONTENT","H2_REPLAY_TACTICS",
                       "Core H1 visually improved but users did not choose rematch; H2 only after official H1 gate.",True)
    return _result("RECOMMEND_SOLE_RC_REVIEW",None,
                   "H1 beat H0 in manually supplied first90s fun, early action, core, route, mobile and replay checks; sole #220 + OWNER still decide Studio acceptance and release.",True)

def main() -> None:
    p=argparse.ArgumentParser(description="Evidence is manually entered; no Roblox API or actual Studio connection.")
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    data=json.loads(a.input.read_text(encoding="utf-8"))
    ans=evaluate(data)
    out=json.dumps(ans,ensure_ascii=False,indent=2)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(out,encoding="utf-8")
    else:
        print(out,end="")
if __name__=="__main__":main()
