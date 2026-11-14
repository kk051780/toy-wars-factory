#!/usr/bin/env python3
"""Verify 81 actual native Rojo sources and uniquely wired Game/HUD/Horde."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from apply_private_horde_hit_toast import GAME,HUD,FEATURE,read,blob,verify_all_real_hit_branches,verify_original_toast_epoch

def verify(dist:Path,place:Path,receipt:Path)->dict:
    before=read(dist)
    assert len(before)==81 and GAME in before and HUD in before
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={name:blob(value) for name,value in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    meta=fl["horde_private_hit_toast_v3"]
    assert meta["changed_sources"]==[GAME,HUD]
    assert meta["original_other79_byte_exact"] is True
    assert meta["official_rc_adopted"] is False
    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000 and b"<!DOCTYPE" not in raw.upper()
    assert b"<!ENTITY" not in raw.upper()
    bysource=collections.Counter()
    byname=collections.defaultdict(list)
    for it in ET.fromstring(raw).iter("Item"):
        kind=it.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=it.find("Properties")
        if props is None:continue
        name=props.find("string[@name='Name']")
        code=props.find("string[@name='Source']")
        assert name is not None and code is not None,("SCRIPT_MISSING_NAME_OR_SOURCE",kind)
        val=code.text or ""
        bysource[val]+=1
        byname[(kind,name.text)].append(val)
    expected=collections.Counter(code.decode("utf8") for code in before.values())
    assert bysource==expected and sum(bysource.values())==81,"REAL_ROJO_81_SOURCE_MISMATCH"
    for kind,name,path in (
        ("Script","Game",GAME),
        ("LocalScript","TrapRaidersHUD",HUD),
        ("ModuleScript","MusouHorde","server/MusouHorde.luau"),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau")
    ):
        actual=byname[(kind,name)]
        assert len(actual)==1 and actual[0]==before[path].decode("utf8"),(
          "INSTANCE_ROLE_OR_CONTENT_SWAPPED",name,len(actual))
    game=before[GAME].decode("utf8")
    hud=before[HUD].decode("utf8")
    verify_all_real_hit_branches(game)
    verify_original_toast_epoch(hud)
    assert 'musouActive = RunService:IsStudio() and match.phase=="ACTIVE"' in game
    assert game.count('musouHitFeedback = (RunService:IsStudio() or (game.PrivateServerId ~= ""')==1
    assert 'if s.musouActive==true or (s.musouHitFeedback==true and s.phase=="ACTIVE") then' in hud
    assert 'first90Cue.Visible=s.musouActive==true' in hud
    assert 'mobCue.Visible=s.musouActive==true' in hud
    assert 'netButton.Visible=s.musouActive==true' in hud
    assert 'rescueButton.Visible=s.musouActive==true' in hud
    assert 'impactToast.Visible=true' in hud and 'task.delay(.42,function()' in hud
    result={
      "schema":"P0D_444_PRIVATE_HIT_TRANSIENT_RECEIPT_V3_SOURCE_ONLY",
      "source_count":81,
      "real_rojo_scripts_byte_exact":81,
      "changed_sources":[GAME,HUD],
      "original_other79_source_bytes_exact":True,
      "one_original_Game":True,
      "one_original_HUD":True,
      "one_original_Horde":True,
      "no_new_event_authority":True,
      "real_Horde_reset_hit_tick_source_preserved":True,
      "server_real_hit_seq_used_not_client_invented":True,
      "transient_duration_seconds":0.42,
      "persistent_coach_in_private_nonstudio":False,
      "persistent_mob_banner_in_private_nonstudio":False,
      "owner_authorized_private_nonstudio_real_hit":"NOT_TESTED",
      "android_15min":"NOT_TESTED",
      "kid_fun_first3min":"NOT_TESTED",
      "official_rc_adopted":False,
      "owner_accepted":False,
      "live_horde_decision":"LIVE_HORDE_NO_GO",
      "art_decision":"ART_NO_GO",
      "mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO",
      "place_bytes":len(raw),
      "place_sha256":hashlib.sha256(raw).hexdigest(),
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_444_REAL_HIT_TOAST_PRIVATE81_ALL_SOURCE_QA_PASS",result["place_bytes"])
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
