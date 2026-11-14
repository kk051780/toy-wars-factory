#!/usr/bin/env python3
"""P0 #444 verify actual Rojo 81 source Game-only lifecycle source under official B reset."""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
from defusedxml import ElementTree as ET
from apply_private_horde_combat import (
 GAME,HORDE,FEATURE,PARENT_FEATURE,RESET_AUTH,HIT_NEW,TICK_NEW,BOT_NEW,
 PRIVATE_ATTR,HORDE_OFFICIAL_BLOB,read,blob
)

def verify(dist:Path,place:Path,receipt:Path)->dict:
    sources=read(dist)
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert len(sources)==sl["total_scripts"]==fl["total_sources"]==81
    locks={p:blob(v) for p,v in sorted(sources.items())}
    assert sl["blobs"]==fl["source_gitblobs"]==locks
    assert fl["feature_flags"][PARENT_FEATURE] is True
    assert fl["feature_flags"][FEATURE] is True
    rec=fl["live_horde_attack_tick_v2"]
    assert rec["game_after"]==locks[GAME] and rec["other80_byte_identical"] is True
    assert rec["original_reset_from_B_unchanged"]
    assert locks[HORDE]==HORDE_OFFICIAL_BLOB
    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    actual=collections.Counter()
    named=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        klass=item.get("class")
        if klass not in {"Script","LocalScript","ModuleScript"}:continue
        props=item.find("Properties")
        if props is None:continue
        name=props.find("string[@name='Name']")
        source=props.find("string[@name='Source']")
        if name is None or source is None:continue
        txt=source.text or ""
        actual[txt]+=1
        named[(klass,name.text or "")].append(txt)
    expected=collections.Counter(x.decode("utf8") for x in sources.values())
    assert actual==expected and sum(actual.values())==81
    for k,n,p in (
        ("Script","Game",GAME),
        ("ModuleScript","MusouHorde",HORDE),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau")
    ):
        val=named[(k,n)]
        assert len(val)==1 and val[0]==sources[p].decode("utf8"),("REAL_INSTANCE_DRIFT",n,len(val))
    game=sources[GAME].decode("utf8")
    assert game.count(RESET_AUTH)==1
    assert game.count(HIT_NEW)==1 and game.count(TICK_NEW)==1 and game.count(BOT_NEW)==1
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count("horde:reset(")==1
    assert game.count('game.PrivateServerId ~= ""')==3
    assert game.count('workspace:GetAttribute("'+PRIVATE_ATTR+'") == true')==3
    result={
      "schema":"P0D_HORDE_PRIVATE_LIFECYCLE81_REAL_ROJO_V2",
      "original_B_reset_unchanged":True,
      "Game_changed_only":True,"original80_other_byte_exact":True,
      "embedded81_real_luau_exact":81,"one_Game_Horde_HUD":True,
      "three_original_Horde_guards_with_private_optin":True,
      "soloBots_studio_tick_unchanged":True,
      "public_default":"OFF",
      "source_gate":"PASS",
      "private_game_engine":"NOT_TESTED",
      "neutral_mobs9_live":"NOT_TESTED",
      "real_attack_hp_popup":"NOT_TESTED",
      "mobile15min":"NOT_TESTED","child3min":"NOT_TESTED",
      "live_horde_decision":"LIVE_HORDE_NO_GO",
      "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO","owner_accepted":False,
      "official_rc_adopted":False,
      "place_bytes":len(raw),"place_sha256":hashlib.sha256(raw).hexdigest()
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_HORDE_PRIVATE_THREE_GATES_REAL81_SOURCE_EXACT_PASS",result["place_bytes"],result["place_sha256"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args();verify(a.dist,a.place,a.receipt)
