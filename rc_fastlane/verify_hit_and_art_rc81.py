#!/usr/bin/env python3
"""A-PREP cumulative 81 Luau: original hit toast + private cosmetics (source only)."""
from __future__ import annotations
import argparse,collections,hashlib,json,sys
from pathlib import Path
from defusedxml import ElementTree as ET
from apply_private_horde_hit_toast import (
    read,blob,GAME,HUD,GAME_V2_BLOB,HUD_V2_BLOB,FEATURE as TOAST_FLAG,
    GAME_INSERT,HUD_REPLACE,patch_game,patch_hud
)
from apply_fb015_live_art_client_pilot import (
    FILES,CLIENTS,SERVER,LIVE_CASTLE,CASTLE_BLOB,
    FLAG as ART_FLAG,NEW,OLD,SERVER_OLD,SERVER_NEW
)

def verify(base:Path,toast:Path,final:Path,place:Path,receipt:Path):
    original,mid,out=read(base),read(toast),read(final)
    assert len(original)==len(mid)==len(out)==81
    assert set(original)==set(mid)==set(out)
    assert {p for p in original if original[p]!=mid[p]}=={GAME,HUD},"TOAST_ONLY_GAME_HUD"
    assert {p for p in mid if mid[p]!=out[p]}==set(FILES),"ART_ONLY_THREE"
    changed={p for p in original if original[p]!=out[p]}
    assert changed=={GAME,HUD,*FILES} and len(changed)==5,("SOURCE_DRIFT",changed)
    assert sum(out[p]==original[p] for p in original)==76
    assert blob(original[GAME])==GAME_V2_BLOB
    assert blob(original[HUD])==HUD_V2_BLOB
    assert mid[GAME]==patch_game(original[GAME]) and mid[HUD]==patch_hud(original[HUD])
    assert out[GAME]==mid[GAME] and out[HUD]==mid[HUD]
    assert out["server/MusouHorde.luau"]==original["server/MusouHorde.luau"]
    assert out[LIVE_CASTLE]==original[LIVE_CASTLE] and blob(out[LIVE_CASTLE])==CASTLE_BLOB
    for name in CLIENTS:
        assert out[name].replace(NEW.encode(),OLD.encode(),1)==original[name]
    assert out[SERVER].replace(SERVER_NEW.encode(),SERVER_OLD.encode(),1)==original[SERVER]
    for stage,source in ((toast,mid),(final,out)):
        sl=json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))
        fl=json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))
        hashes={p:blob(x) for p,x in sorted(source.items())}
        assert sl["total_scripts"]==fl["total_sources"]==81
        assert sl["blobs"]==fl["source_gitblobs"]==hashes
        assert fl["feature_flags"]["P0D_PRIVATE_LIVE_HORDE_NINE_V1"]
        assert fl["feature_flags"]["P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2"]
        assert fl["feature_flags"][TOAST_FLAG]
    fl=json.loads((final/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert fl["feature_flags"][ART_FLAG]
    game=out[GAME].decode()
    hud=out[HUD].decode()
    assert game.count("horde:reset(")==game.count("horde:tick(")==1
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('game.PrivateServerId ~= ""')==4
    assert GAME_INSERT in game and HUD_REPLACE in hud
    assert 'musouActive = RunService:IsStudio() and match.phase=="ACTIVE"' in game
    for line in (
      "first90Cue.Visible=s.musouActive==true",
      "mobCue.Visible=s.musouActive==true",
      "netButton.Visible=s.musouActive==true",
      "rescueButton.Visible=s.musouActive==true"
    ):assert hud.count(line)==1,("PERSISTENT_UI_CHANGED",line)
    assert "task.delay(.42,function()" in hud
    assert game.count("musouHitFeedback = ")==1
    raw=place.read_bytes()
    assert 100000<len(raw)<10000000 and b"<!DOCTYPE" not in raw.upper()
    assert b"<!ENTITY" not in raw.upper()
    scripts=collections.Counter()
    names=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.find("string[@name='Name']")
        src=props.find("string[@name='Source']")
        assert name is not None and src is not None
        source=src.text or ""
        scripts[source]+=1
        names[(cls,name.text or "")].append(source)
    assert sum(scripts.values())==81 and scripts==collections.Counter(x.decode() for x in out.values())
    for cls,name,path in (
        ("Script","Game",GAME),
        ("LocalScript","TrapRaidersHUD",HUD),
        ("ModuleScript","MusouHorde","server/MusouHorde.luau"),
        ("Script","P0DLiveCastleArt",LIVE_CASTLE),
        ("Script","CastleDetailArt",SERVER),
        ("LocalScript","FB015GoroganVisual",CLIENTS[0]),
        ("LocalScript","P0DConfirmedCombatFX",CLIENTS[1]),
    ):
        assert names[(cls,name)]==[out[path].decode()],("REAL_INSTANCE_OR_SOURCE_WRONG",name)
    data={
      "schema":"P0D_RC81_PRIVATE_REAL_HIT_AND_VISUAL_5_SOURCE_V1",
      "official_base":"b32664b7555f040eeca50f853927a9d975249ce5",
      "source_gate":"PASS","script_count":81,
      "exact_real_rojo_luau_source_instances":81,
      "changed_sources":sorted(changed),
      "unchanged_original_sources":76,
      "official_horde_reset_attack_tick_unchanged":True,
      "official_horde_module_and_81st_castle_unchanged":True,
      "only_real_server_impact_sequence_drives_toast":True,
      "impact_toast_duration_s":0.42,
      "persistent_hud_orig_studio_only":True,
      "independent_owner_private_permissions":["P0D_PRIVATE_LIVE_HORDE_NINE","P0D_LIVE_ART_PILOT_OPTIN"],
      "public_server_source_intent":"OFF",
      "private_runtime_nine_mobs_hit_popup_visual":"NOT_TESTED",
      "pc_android_visual":"NOT_TESTED",
      "low_end_android15min":"NOT_TESTED",
      "kid_first3min_fun":"NOT_TESTED",
      "owner_accepted":False,"official_adopted":False,
      "live_horde_decision":"LIVE_HORDE_NO_GO",
      "live_art_decision":"LIVE_ART_NO_GO",
      "art_decision":"ART_NO_GO",
      "mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO",
      "place_bytes":len(raw),"place_sha256":hashlib.sha256(raw).hexdigest(),
    }
    assert not receipt.exists()
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_444_431_HIT_TOAST_AND_CLIENT_ART_REAL81_5EDIT_76EXACT_PASS",len(raw),data["place_sha256"])
    return data
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("base","toast","final","place","receipt"):p.add_argument("--"+a,required=True,type=Path)
    a=p.parse_args();verify(a.base,a.toast,a.final,a.place,a.receipt)
