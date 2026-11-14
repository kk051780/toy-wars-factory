#!/usr/bin/env python3
"""FB019: embedded real Roblox Studio Place must contain all 80 exact Luau sources.
This proves compile/Rojo input output consistency, NOT that Studio input worked.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb019_attack_gesture import read,blob,HUD,FEATURE
def verify(dist:Path,place:Path,receipt:Path):
    src=read(dist)
    assert len(src)==80
    pins={p:blob(v) for p,v in sorted(src.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb019_attack_feedback"]["other79_byte_exact"] is True
    expected=collections.Counter(raw.decode("utf8") for raw in src.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        properties=item.find("Properties")
        if properties is None:continue
        script=properties.find("string[@name='Source']")
        if script is not None:actual[script.text or ""]+=1
        name=properties.find("string[@name='Name']")
        if name is not None:names[(item.get("class"),name.text)]+=1
    assert actual==expected and sum(actual.values())==80,"SOURCE_NOT_EXACT"
    for cls,name in [("Script","Game"),("LocalScript","TrapRaidersHUD"),
                     ("LocalScript","BattleHUDGovernor"),("ModuleScript","MusouHorde")]:
        assert names[(cls,name)]==1,(cls,name,names[(cls,name)])
    hud=src[HUD].decode("utf8")
    assert hud.count("attack.Activated:Connect(pressAttack)")==1
    assert hud.count("if input.KeyCode == Enum.KeyCode.F then pressAttack()")==1
    assert hud.count('action("ATTACK",nil)')==1
    assert "attack.MouseButton1Click:Connect(" not in hud
    assert "attackDebris:AddItem(flash,.24)" in hud
    assert "noGuidanceActive" in src["client/BattleHUDGovernor.client.luau"].decode()
    game=src["server/Game.server.luau"].decode()
    assert 'if data.action == "ATTACK" then applyAttack(player, data)' in game
    assert 'local touched,defeated = horde:hit(' in game
    assert game.count("remote.OnServerEvent:Connect(")==1
    receipt_data={
        "source_count":80,"all_source_exact":True,"sole_game":True,
        "owner_feedback":"FB-019","local_swing_on_valid_client_input":True,
        "server_damage_unmodified":True,"other79_sources_byte_exact":True,
        "pc_mouse_touch_activated":"CODE_LEVEL_VERIFIED",
        "in_engine_attack":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(receipt_data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB019_INPUT_SWING_RC80_ROJO_REAL_SOURCE_80_80_PASS",receipt_data["place_bytes"],receipt_data["place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
