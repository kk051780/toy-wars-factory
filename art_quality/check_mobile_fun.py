#!/usr/bin/env python3
"""FB015 P0 mobile performance + kid-fun gate, real hardware evidence only.

Source CI, a human-filled form, or impressive stills do not certify fun. This
validator rejects missing/unsafe metrics and cannot approve its own release.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

LIMITS={
    "low_android":{"median_fps":30.0,"p10_fps":25.0},
    "mid_android":{"median_fps":45.0,"p10_fps":30.0},
    "pc":{"p10_fps":45.0}
}
FUN_GOALS={"move_seconds":15, "first_attack_seconds":45,
           "first_real_enemy_hit_seconds":75,
           "objective_understood_seconds":180}

def valid_number(v):
    return type(v) in (int,float) and math.isfinite(v)

def gate(data:dict|None)->dict:
    violations=[]
    if not isinstance(data,dict):
        return {"status":"EVIDENCE_MISSING","violations":["REAL_DEVICE_AND_FUN_MANIFEST_MISSING"],
                "fun_decision":"FUN_NO_GO","mobile_decision":"MOBILE_NO_GO"}
    if data.get("schema")!="P0D_MOBILE_KID_FUN_EVIDENCE_V1":
        violations.append("SCHEMA_INVALID")
    devices=data.get("devices",{})
    if not isinstance(devices,dict):devices={}
    for kind,floors in LIMITS.items():
        item=devices.get(kind,{})
        if not isinstance(item,dict): item={}
        if not item.get("device_model") or not item.get("graphics_quality"):
            violations.append("MISSING_REAL_HARDWARE:"+kind)
        minutes=item.get("session_minutes")
        if not valid_number(minutes) or minutes<15:
            violations.append("MISSING_15_MIN_REAL_SESSION:"+kind)
        for field,threshold in floors.items():
            value=item.get(field)
            if not valid_number(value) or value<threshold:
                violations.append("FPS_BELOW_TARGET_OR_UNKNOWN:"+kind+"/"+field)
        if item.get("crash_free") is not True or item.get("oom_free") is not True:
            violations.append("MOBILE_CRASH_OOM_UNKNOWN_OR_FAIL:"+kind)
        if kind!="pc":
            decline=item.get("warm_fps_drop_fraction")
            if not valid_number(decline) or not 0<=decline<=0.2:
                violations.append("THERMAL_DROP_UNKNOWN_OR_OVER20PCT:"+kind)
            if not valid_number(item.get("peak_memory_mb")) or item["peak_memory_mb"]<=0:
                violations.append("MEMORY_PEAK_NOT_MEASURED:"+kind)
            if not valid_number(item.get("join_to_control_seconds")):
                violations.append("JOIN_TO_CONTROL_UNMEASURED:"+kind)
            if item.get("touch_attack_works") is not True:
                violations.append("TOUCH_ATTACK_NOT_TESTED:"+kind)
    fun=data.get("first_play",{})
    if not isinstance(fun,dict):fun={}
    if fun.get("consent_appropriate") is not True:
        violations.append("SUPERVISED_CONSENTED_TEST_NOT_CONFIRMED")
    if not valid_number(fun.get("test_sessions")) or fun["test_sessions"]<3:
        violations.append("INSUFFICIENT_FIRST_PLAY_SESSIONS")
    for key,limit in FUN_GOALS.items():
        x=fun.get(key)
        if not valid_number(x) or not 0<=x<=limit:
            violations.append("FTUE_UNKNOWN_OR_TOO_SLOW:"+key)
    rating=fun.get("first_three_minutes_fun_rating")
    if not valid_number(rating) or rating<4 or rating>5:
        violations.append("KID_FUN_NOT_AT_LEAST_4_OF_5")
    for flag in ("solo_playable","can_understand_egg_theft",
                 "attack_actual_hp_changes","no_persistent_guide"):
        if fun.get(flag) is not True:
            violations.append("GAMEPLAY_CONDITION_FAIL_OR_UNKNOWN:"+flag)
    if data.get("critical_blockers")!=[]:
        violations.append("UNRESOLVED_CRITICAL_BLOCKERS")
    if not data.get("independent_reviewer") or not data.get("evidence_links"):
        violations.append("HUMAN_EVIDENCE_NOT_LINKED")
    clear=not violations
    return {
        "status":"REVIEW_READY_OWNER_PENDING" if clear else "EVIDENCE_INCOMPLETE",
        "violations":violations,
        "fun_decision":"FUN_NO_GO",
        "mobile_decision":"MOBILE_NO_GO",
        "owner_accepted":False,
        "note":"Numbers are P0D acceptance targets, not official platform thresholds. Authenticity and kid enjoyment require real playtesting and human OWNER acceptance."
    }

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--strict",action="store_true")
    a=p.parse_args(argv)
    try:
        data=json.loads(a.evidence.read_text("utf8")) if a.evidence else None
        result=gate(data)
    except (OSError,ValueError,TypeError) as e:
        result=gate(None)
        result["error"]=str(e)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf8")
    print("P0D_MOBILE_KID_FUN",result["status"],result["fun_decision"],result["mobile_decision"])
    return 2 if a.strict and result["status"]!="REVIEW_READY_OWNER_PENDING" else 0

if __name__=="__main__":
    sys.exit(main())
