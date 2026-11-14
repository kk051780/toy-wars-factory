#!/usr/bin/env python3
"""Real Rojo81 Game/solo/Horde source exact for #444 private one-human trial."""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
from defusedxml import ElementTree as ET
from apply_private_onehuman_horde_post_art import (
  read,blob,GAME,SOLO,HORDE,GAME_PIN,SOLO_PIN,HORDE_PIN,
  FEATURE,OWNER_ATTR,NEW_DECL,NEW_LATCH,NEW_START,NEW_EMPTY
)

def verify(dist:Path,place:Path,receipt:Path)->dict:
    scripts=read(dist)
    lock=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    flags=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    expected={p:blob(v) for p,v in sorted(scripts.items())}
    assert len(scripts)==lock["total_scripts"]==flags["total_sources"]==81
    assert lock["blobs"]==flags["source_gitblobs"]==expected
    assert flags["feature_flags"][FEATURE] is True
    meta=flags["private_one_human_trial"]
    assert meta["only_modified_existing_source"]==[GAME]
    assert meta["parent_Game_blob"]==GAME_PIN
    assert meta["new_Game_blob"]==expected[GAME]
    assert meta["other80_byte_identical"]
    assert expected[SOLO]==SOLO_PIN and expected[HORDE]==HORDE_PIN
    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    count=collections.Counter()
    instances=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        klass=item.get("class")
        if klass not in {"Script","LocalScript","ModuleScript"}:continue
        properties=item.find("Properties")
        if properties is None:continue
        n=properties.find("string[@name='Name']")
        s=properties.find("string[@name='Source']")
        if n is None or s is None:continue
        t=s.text or ""
        count[t]+=1
        instances[(klass,n.text or "")].append(t)
    assert count==collections.Counter(s.decode("utf8") for s in scripts.values())
    assert sum(count.values())==81
    for k,n,p in (
        ("Script","Game",GAME),
        ("ModuleScript","StudioSoloPreviewRules",SOLO),
        ("ModuleScript","MusouHorde",HORDE),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau")
    ):
        found=instances[(k,n)]
        assert len(found)==1 and found[0]==scripts[p].decode("utf8"),(
            "CRITICAL_REAL_ROJO_INSTANCE_DRIFT",k,n,len(found))
    g=scripts[GAME].decode("utf8")
    assert g.count(NEW_DECL)==1
    assert g.count(NEW_LATCH)==1 and g.count(NEW_START)==2
    assert g.count(NEW_EMPTY)==1
    assert g.count('game.PrivateServerId ~= ""')==5
    assert g.count('workspace:GetAttribute("'+OWNER_ATTR+'") == true')==5
    assert 'if everybodyReady() and StudioSolo.canStart(' in g
    assert g.count("musouHitFeedback = ")==1, "PREVIOUS_HIT_TOAST_LOST"
    assert "impactDisplayEpoch" in scripts["client/HUD.client.luau"].decode("utf8")
    assert 'if not everybodyReady() then' in g
    assert 'if RunService:IsStudio() and studioSoloRoundStarted' in g
    assert g.count("remote.OnServerEvent:Connect(")==1
    assert g.count("horde:reset(")==1 and g.count("horde:tick(")==1
    assert 'workspace:SetAttribute("'+OWNER_ATTR+'"' not in g
    result={
      "schema":"P0D_PRIVATE_ONE_HUMAN_HORDE_REAL_ROJO81_SOURCE_V1",
      "actual_embedded_luau_sources":81,"source_lock_matches":True,
      "only_existing_Game_modified":True,"other80_byte_exact":True,
      "original_StudioSolo_Horde_HUD_unchanged":True,
      "single_authoritative_Game_Remote_Horde":True,
      "public_match_min_players":2,
      "private_one_human_requires_owner_flag_and_READY":True,
      "private_runtime_nonstudio":"NOT_TESTED",
      "actual9_mobs":"NOT_TESTED","real_damage_hp_popup":"NOT_TESTED",
      "android_15min":"NOT_TESTED","child_first3min":"NOT_TESTED",
      "source_gate":"PASS","live_horde_decision":"LIVE_HORDE_NO_GO",
      "live_art_decision":"LIVE_ART_NO_GO","art_decision":"ART_NO_GO",
      "mobile_decision":"MOBILE_NO_GO","fun_decision":"FUN_NO_GO",
      "owner_accepted":False,"official_rc_adopted":False,
      "place_bytes":len(raw),"place_sha256":hashlib.sha256(raw).hexdigest()
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_ONE_HUMAN_HORDE_REAL_ROJO81_PASS",result["place_bytes"],result["place_sha256"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args();verify(a.dist,a.place,a.receipt)
