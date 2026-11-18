#!/usr/bin/env python3
"""REAL65: keep actual official REAL63 and add independently proven REAL64 viral/counter.
Preserve unique Host, Combat, Swarm and trade. Fail closed on any original drift.
This is source composition only; never treat it as Roblox engine/quality acceptance.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gq8_real63_intake_20261119"))
from compose_real63 import (
    from_xml, flatten, put_project, check_diff, receipt_verify, sha
)

OFFICIAL63="ad602cebafc1a9d8caed078ab86c7a58b0fbbbef"
FORMAL62="b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff"
CANDIDATE64="7822dae126934eac8df0b482cfa264d452c5b653"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
INVUL=("ServerScriptService","EGGRUMBLE_InvulRuntime")
HUD=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime")
BASIC=("ServerScriptService","EGGRUMBLE_BasicMobilityPolicy")
VIRAL=("StarterPlayer","StarterPlayerScripts","GQ8_ViralCapture")
COUNTER=("ServerScriptService","EGGRUMBLE_InvulCounterNeutral")
PVP='enemyHum:TakeDamage(InvulRuntime.filterDamage(enemyHum,damage*duel*mark*musou,"PLAYER",p.UserId))'

def merge_combat(original:bytes, basic:bytes, counter:bytes)->bytes:
    old=original.decode("utf8")
    newbasic=basic.decode("utf8")
    newcounter=counter.decode("utf8")
    if old.count(PVP)!=1 or newbasic.count(PVP)!=1 or newcounter.count(PVP):
        raise ValueError("RED_PVP_SINGLE_SOURCE_ANCHOR")
    if "EGGRUMBLE_BASIC_ATTACK" not in newbasic or "EGGRUMBLE_DODGE_STEP" not in newbasic:
        raise ValueError("RED_REAL63_BASIC_DODGE_LOST")
    if "claimPvPCounter(" not in newcounter or "EGGRUMBLE_VisibleCounterTell" not in newcounter:
        raise ValueError("RED_COUNTER_AUTHOR_NOT_REAL")
    # PR841 changes only the existing PvP hit block. Require the entire
    # rest of the original Combat to remain EXACT before transplanting.
    shared_prefix=0
    boundary=min(len(old),len(newcounter))
    while shared_prefix<boundary and old[shared_prefix]==newcounter[shared_prefix]:
        shared_prefix+=1
    shared_suffix=0
    maxsuffix=min(len(old),len(newcounter))-shared_prefix
    while shared_suffix<maxsuffix and old[-shared_suffix-1]==newcounter[-shared_suffix-1]:
        shared_suffix+=1
    left=old[shared_prefix:len(old)-shared_suffix if shared_suffix else len(old)]
    right=newcounter[shared_prefix:len(newcounter)-shared_suffix if shared_suffix else len(newcounter)]
    if not left or not right or newbasic.count(left)!=1:
        raise ValueError("RED_COUNTER_SCOPED_REPLACEMENT_NOT_UNIQUE")
    if left not in PVP and PVP not in left:
        raise ValueError("RED_COUNTER_CHANGED_OUTSIDE_PVP_BLOCK")
    merged=newbasic.replace(left,right,1)
    if not ("EGGRUMBLE_BASIC_ATTACK" in merged and
            "EGGRUMBLE_DODGE_STEP" in merged and
            "EGGRUMBLE_VisibleCounterTell" in merged and
            "claimPvPCounter(" in merged):
        raise ValueError("RED_EITHER_COMBAT_LANE_LOST")
    if merged.replace(right,left,1)!=newbasic:
        raise ValueError("RED_COUNTER_ROLLBACK_NOT_EXACT_REAL63")
    if merged.count("EGGRUMBLE_BasicMobilityPolicy")!=1:
        raise ValueError("RED_BASIC_POLICY_LOAD_COUNT")
    return merged.encode("utf8")

def run(a):
    raw62=a.formal62.read_bytes()
    raw63=a.formal63.read_bytes()
    r62=json.loads(a.receipt62.read_text(encoding="utf8"))
    r63=json.loads(a.receipt63.read_text(encoding="utf8"))
    r64=json.loads(a.receipt64.read_text(encoding="utf8"))
    if (r62.get("tested_head")!=FORMAL62 or
        r62.get("official_rc_adopted") is not True or
        r62.get("combined_count")!=62 or
        r62.get("host_class")!="Script"):
        raise ValueError("RED_FORMAL62_ORIGIN")
    if (r63.get("candidate_git_head")!=OFFICIAL63 or
        r63.get("official_rc_adopted") is not True or
        r63.get("parent_original_sources")!=62 or
        r63.get("candidate_sources")!=63 or
        r63.get("place_sha256")!=sha(raw63)):
        raise ValueError("RED_FORMAL63_NOT_SAME_HEAD")
    if (r64.get("candidate_head")!=CANDIDATE64 or
        r64.get("selected_real_sources")!=64 or
        r64.get("formal_rc_adopted") is not False or
        r64.get("source_native")!="PASS" or
        r64.get("rojo_source_class")!="PASS" or
        r64.get("off62_bytes")!="BYTE_IDENTICAL"):
        raise ValueError("RED_PROVEN_CANDIDATE64_MISSING")
    base62=from_xml(a.formal62)
    official63=from_xml(a.formal63)
    doc64,real64=flatten(a.project64)
    if [len(x) for x in (base62,official63,real64)] != [62,63,64]:
        raise ValueError("RED_SOURCE_COUNTS")
    receipt_verify(base62,r62["on_sources"],"REAL62")
    receipt_verify(official63,r63["on_sources"],"REAL63")
    receipt_verify(real64,r64["sources"],"REAL64")
    check_diff(base62,official63,{COMBAT,HUD},{BASIC},"REAL63")
    check_diff(base62,real64,{HOST,COMBAT,INVUL},{VIRAL,COUNTER},"REAL64")
    if not ({HOST,COMBAT,INVUL,HUD,BASIC}.issubset(official63)
            and {VIRAL,COUNTER}.issubset(real64)):
        raise ValueError("RED_ORIGINAL_SINGLETON_MISSING")
    if official63[HOST][0]!="Script" or real64[HOST][0]!="Script":
        raise ValueError("RED_HOST_INERT")
    chosen=dict(official63)
    for key in (HOST,INVUL,VIRAL,COUNTER):
        chosen[key]=real64[key]
    chosen[COMBAT]=(official63[COMBAT][0],merge_combat(
        base62[COMBAT][1],official63[COMBAT][1],real64[COMBAT][1]))
    if len(chosen)!=65:
        raise ValueError("RED_65_COUNT_OR_DUPLICATE")
    if set(chosen)-set(official63)!={VIRAL,COUNTER}:
        raise ValueError("RED_NONADDITIVE_NEW_SOURCE")
    changed={k for k in official63 if chosen[k]!=official63[k]}
    if changed!={HOST,COMBAT,INVUL}:
        raise ValueError("RED_UNAUTHORIZED_CHANGED_ORIGINAL")
    if (any(chosen[k]!=official63[k] for k in set(official63)-changed)
        or chosen[HUD]!=official63[HUD] or chosen[BASIC]!=official63[BASIC]):
        raise ValueError("RED_REAL63_HUD_DODGE_OR_TRADE_LOST")
    for key in (("ServerScriptService","GQ8_TradeJournalContract"),
                ("ServerScriptService","GQ8_TradeEscrowReducer"),
                ("StarterPlayer","StarterPlayerScripts","GQ8_TradeReview")):
        if chosen[key]!=base62[key]:
            raise ValueError("RED_TRADE_CHANGED")
    for kind in ("EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat",
                 "EGGRUMBLE_SwarmCombat","EGGRUMBLE_InvulRuntime"):
        if sum(route[-1]==kind for route in chosen)!=1:
            raise ValueError("RED_DUPLICATE_SINGLETON_"+kind)
    if not ("EGGRUMBLE_VisibleCounterTell" in chosen[COMBAT][1].decode("utf8")
            and "session.swarm.musouActive" in chosen[INVUL][1].decode("utf8")):
        raise ValueError("RED_COUNTER_OR_MUSOU_RUNTIME_LOST")
    if a.out.exists():
        raise ValueError("RED_OUTPUT_EXISTS")
    a.out.mkdir(parents=True)
    on=put_project(doc64,chosen,a.out)
    on.rename(a.out/"EGGRUMBLE_REAL65.project.json")
    off=a.out/"off63"
    off.mkdir()
    offproject=put_project(doc64,official63,off)
    offproject.rename(off/"EGGRUMBLE_OFF63.project.json")
    (a.out/"FORMAL_REAL63_EXACT.rbxlx").write_bytes(raw63)
    report={
      "schema":"GQ8_REAL65_63_PLUS_VIRAL_COUNTER_V1",
      "base_official_head":OFFICIAL63,
      "base_official62_head":FORMAL62,
      "original64_author_head":CANDIDATE64,
      "source_count":65,
      "base63_original_source_count":63,
      "unchanged63_sources":60,
      "modified_singletons":["/".join(k) for k in (HOST,COMBAT,INVUL)],
      "added_sources":["/".join(k) for k in (VIRAL,COUNTER)],
      "formal_rc_adopted":False,
      "same_head_ci":"PENDING",
      "studio_2client":"NOT_TESTED",
      "android_15min":"NOT_TESTED",
      "art_fun":"NO_GO",
      "publish":False,"paid_trade":False,
      "rollback":"EXACT_REAL63_ORIGINAL_PLACE_AND_ALL_63_SCRIPT_CLASSES",
      "formal63_place_sha256":sha(raw63),
      "selected_sources":[{"route":"/".join(k),"class":v[0],"bytes":len(v[1]),
                            "sha256":sha(v[1])} for k,v in sorted(chosen.items())],
      "off63_sources":[{"route":"/".join(k),"class":v[0],"bytes":len(v[1]),
                       "sha256":sha(v[1])} for k,v in sorted(official63.items())]
    }
    (a.out/"REAL65_RECEIPT.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    _,test=flatten(a.out/"EGGRUMBLE_REAL65.project.json")
    if test!=chosen:
        raise ValueError("RED_PROJECT_ROUNDTRIP")
    print("GQ8_REAL65_CURRENT_REAL63_PLUS_VIRAL_COUNTER_60_UNCHANGED_3_PATCHED_2_ADDED")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for key in ("formal62","receipt62","formal63","receipt63",
                "project64","receipt64","out"):
        parser.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    run(parser.parse_args())
