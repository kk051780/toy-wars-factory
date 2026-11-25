#!/usr/bin/env python3
"""FB019 V2 real Rojo Studio Place audit: ONLY server-ack confirmed neutral HIT."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb019_hit_visibility import GAME,GOV,FEATURE,GAME_NEW,GOV_NEW,blob,read
def verify(dist:Path,place:Path,receipt:Path):
    src=read(dist)
    assert len(src)==80
    pins={p:blob(v) for p,v in sorted(src.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb019_hit_visibility"]["other78_byte_exact"] is True
    expected=collections.Counter(v.decode("utf8") for v in src.values())
    actual=collections.Counter();names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:continue
        code=props.find("string[@name='Source']")
        if code is not None:actual[code.text or ""]+=1
        nm=props.find("string[@name='Name']")
        if nm is not None:names[(item.get("class"),nm.text)]+=1
    assert actual==expected and sum(actual.values())==80,"EMBEDDED_SOURCE_NOT_EXACT"
    for typ,name in [
        ("Script","Game"),("LocalScript","BattleHUDGovernor"),
        ("LocalScript","TrapRaidersHUD"),("LocalScript","P0DConfirmedCombatFX"),
        ("ModuleScript","MusouHorde"),("ModuleScript","SoloTeamBots"),
    ]:
        assert names[(typ,name)]==1,(typ,name,names[(typ,name)])
    game=src[GAME].decode("utf8")
    governor=src[GOV].decode("utf8")
    horde=src["server/MusouHorde.luau"].decode("utf8")
    swing=src["client/HUD.client.luau"].decode("utf8")
    assert GAME_NEW in game and GOV_NEW in governor
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert 'remote:FireClient(player,snapshotFor(player))' in game
    assert 'm.hp=math.max(0,beforeHp-dealt)' in horde
    assert 'm.popup.Enabled=true' in horde and 'm.popupUntil=now+.72' in horde
    assert 'attack.Activated:Connect(pressAttack)' in swing
    assert 'noGuidanceActive=true' in governor
    assert 'node.Name=="S1_CARRIED_EGG"' in governor
    assert 'node.Name=="RealDamagePopup"' in governor
    assert "PlayerGui" in governor
    data={
        "source_count":80,"all_source_exact":True,"game_unique":True,
        "fb":"FB-019-v2",
        "real_horde_hit_receipt_sent_immediately":True,
        "server_owned_damage_popup_not_suppressed":True,
        "other78_source_exact":True,
        "owner_game_damage_logic_unmodified":True,
        "in_engine_studio_attack":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB019_V2_REAL_HIT_VISIBILITY_80_SOURCE_EXACT_PASS",
          data["place_bytes"],data["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
