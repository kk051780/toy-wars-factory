#!/usr/bin/env python3
"""#444 + #431 true 81-source cumulative private studio QA, no live GO."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path
from defusedxml import ElementTree as ET
from apply_private_horde_combat import read, blob, GAME, HORDE, RESET_AUTH, HIT_NEW, TICK_NEW, BOT_NEW, HORDE_OFFICIAL_BLOB, GAME_OFFICIAL_BLOB, patch
from apply_fb015_live_art_client_pilot import FILES, CLIENTS, SERVER, LIVE_CASTLE, CASTLE_BLOB, OLD, NEW, SERVER_OLD, SERVER_NEW, FLAG as ART_FEATURE
SRC_GAME="server/Game.server.luau"
SRC_HUD="client/HUD.client.luau"

def verify(base:Path,horde:Path,final:Path,place:Path,out:Path)->dict:
    before,mid,after=read(base),read(horde),read(final)
    assert len(before)==len(mid)==len(after)==81
    assert set(before)==set(mid)==set(after)
    assert {p for p in before if before[p]!=mid[p]}=={GAME},"HORDE_ONE_GAME_ONLY"
    assert {p for p in mid if mid[p]!=after[p]}==set(FILES),"ART_THREE_ONLY"
    assert {p for p in before if before[p]!=after[p]}=={GAME,*FILES},"NO_EXTRA_MODIFICATION"
    assert sum(before[p]==after[p] for p in before)==77,"77_ORIGINAL_SOURCES_IDENTICAL"
    assert blob(before[GAME])==GAME_OFFICIAL_BLOB and mid[GAME]==patch(before[GAME])
    assert mid[GAME]==after[GAME] and after[GAME].decode().count(RESET_AUTH)==1
    assert all(after[GAME].decode().count(x)==1 for x in (HIT_NEW,TICK_NEW,BOT_NEW))
    assert after[HORDE]==before[HORDE] and blob(after[HORDE])==HORDE_OFFICIAL_BLOB
    assert after[LIVE_CASTLE]==before[LIVE_CASTLE] and blob(after[LIVE_CASTLE])==CASTLE_BLOB
    for path in CLIENTS:assert after[path].replace(NEW.encode(),OLD.encode(),1)==before[path]
    assert after[SERVER].replace(SERVER_NEW.encode(),SERVER_OLD.encode(),1)==before[SERVER]
    assert after[SRC_HUD]==before[SRC_HUD]
    assert after[GAME].count(b"remote.OnServerEvent:Connect(")==1
    assert after[GAME].count(b"horde:reset(")==after[GAME].count(b"horde:tick(")==1
    locks={p:blob(s) for p,s in sorted(after.items())}
    source_lock=json.loads((final/"SOURCE_LOCK.json").read_text("utf8"))
    feature_lock=json.loads((final/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert source_lock["total_scripts"]==feature_lock["total_sources"]==81
    assert source_lock["blobs"]==feature_lock["source_gitblobs"]==locks
    assert feature_lock["feature_flags"]["P0D_PRIVATE_LIVE_HORDE_NINE_V1"]
    assert feature_lock["feature_flags"]["P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2"]
    assert feature_lock["feature_flags"][ART_FEATURE]
    raw=place.read_bytes()
    assert 100000<len(raw)<10_000_000
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    names=collections.defaultdict(list); seen=collections.Counter()
    for item in ET.fromstring(raw).iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.find("string[@name='Name']")
        content=props.find("string[@name='Source']")
        assert name is not None and content is not None
        txt=content.text or ""
        seen[txt]+=1
        names[(klass,name.text or "")].append(txt)
    assert seen==collections.Counter(s.decode() for s in after.values()) and sum(seen.values())==81
    for kind,name,path in (
        ("Script","Game",GAME),("ModuleScript","MusouHorde",HORDE),
        ("LocalScript","TrapRaidersHUD",SRC_HUD),
        ("Script","P0DLiveCastleArt",LIVE_CASTLE),
        ("Script","CastleDetailArt",SERVER),
        ("LocalScript","FB015GoroganVisual",CLIENTS[0]),
        ("LocalScript","P0DConfirmedCombatFX",CLIENTS[1])):
        assert names[(kind,name)]==[after[path].decode()],("WRONG_INSTANCE_OR_SOURCE",name)
    assert len(names[("Script","Game")])==len(names[("LocalScript","TrapRaidersHUD")])==1
    data={
        "schema":"P0D_RC81_PRIVATE_HORDE_ART_COMPOSITE_20261115_V1",
        "baseline_official_sha":"0287c696bd2467177236c46a1b2b39646d5aa2b9",
        "all_real_embedded_sources":81,
        "changed_sources":sorted({GAME,*FILES}),
        "other_sources_original_byte_exact":77,
        "one_Game_HUD_and_Horde":True,
        "real_original_B_private_reset_unchanged":True,
        "real_Horde_nine_source_unchanged":True,
        "real_life_attack_tick_source_guarded":True,
        "studio_only_bots_preserved":True,
        "castle_81st_source_original_byte_exact":True,
        "two_private_client_cosmetics_conditional":True,
        "public_nonstudio_default":"OFF_BY_SOURCE_DESIGN_NOT_RUNTIME_TESTED",
        "real_studio":"NOT_TESTED",
        "real_private_server":"NOT_TESTED",
        "real_neutral_mobs":"NOT_TESTED",
        "real_hp_popup_vfx":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "kid_fun_3min":"NOT_TESTED",
        "pc_before_after_32":"NOT_TESTED",
        "source_gate":"PASS","owner_accepted":False,
        "live_horde_decision":"LIVE_HORDE_NO_GO",
        "live_art_decision":"LIVE_ART_NO_GO",
        "art_decision":"ART_NO_GO",
        "mobile_decision":"MOBILE_NO_GO",
        "fun_decision":"FUN_NO_GO",
        "official_rc_adopted":False,
        "place_bytes":len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest()
    }
    assert not out.exists()
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_RC81_444_HORDE_PLUS_CLIENT_ART_4MOD_77EXACT_PASS",data["place_bytes"],data["place_sha256"])
    return data
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for a in ("base","horde","final","place","out"):p.add_argument("--"+a,required=True,type=Path)
    a=p.parse_args();verify(a.base,a.horde,a.final,a.place,a.out)
