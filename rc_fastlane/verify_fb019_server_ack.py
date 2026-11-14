#!/usr/bin/env python3
"""Real Studio XML Rojo source-exact and singleton-authority receipt, FB-019."""
from __future__ import annotations
import argparse,collections,hashlib,json
from defusedxml import ElementTree as ET
from pathlib import Path
from apply_fb019_server_ack import read,blob,GAME,HUD,KEY,PIN_GAME,PIN_HUD

def verify(dist:Path,place:Path,receipt:Path):
    src=read(dist)
    assert len(src)==80 and GAME in src and HUD in src
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(src.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][KEY] is True
    assert fl["fb019_attack"]==sl["fb019_attack"]
    info=sl["fb019_attack"]
    assert info["other78_byte_exact"] is True
    assert info["original_blob"]=={GAME:PIN_GAME,HUD:PIN_HUD}
    assert info["new_blob"]=={GAME:pins[GAME],HUD:pins[HUD]}
    assert info["changed_sources"]==[GAME,HUD] and info["source_count"]==80
    s=src[GAME].decode("utf8");h=src[HUD].decode("utf8")
    assert s.count("local function applyAttack(player: Player, data)")==1
    assert s.count("remote.OnServerEvent:Connect(")==1
    assert s.count('kind="P0D_ATTACK_RESULT"')==1
    assert s.count('attackResponse("HIT"')==5
    assert s.count('attackResponse("MISS"')==6
    assert "if hum.Health<beforeHp then" in s
    assert 'remote:FireClient(player,snapshotFor(player))' in s
    assert fl["feature_flags"]["FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2"] is True
    assert "if victim.hum.Health<beforeHp then" in s
    assert "if match.hp[enemy]<priorCastleHp then" in s
    assert "if ok and hum and hum.Health>0 then" in s
    for x in ('Rules.validSeq(data.seq','Rules.canAttack(now, lastAttack',
              'horde:hit(', 'SoloTeamBots.tryHumanHit(',
              'match.hp[enemy] = math.max(0',
              'target=target,serial=match.serial,seq=data.seq'):
        assert x in s,x
    assert h.count("attack.Activated:Connect(")==1
    assert "attack.MouseButton1Click:Connect" not in h
    assert h.count("remote.OnClientEvent:Connect(")==2
    assert "lastAttackFeedbackSeq" in h
    assert h.count("FireServer({action = kind")==3
    assert h.count("showLocalSwing()")==2
    assert h.count("attack.Activated:Connect(pressAttack)")==1
    assert "flashConfirmedAttack(\"⚔ 命中!\"" in h
    assert "flashConfirmedAttack(\"⚔ 空振り\"" in h
    assert "attackFeedbackVersion==version" in h
    assert 'packet.serial~=lastSerial' in h
    assert h.count('Instance.new("ScreenGui")')==1 # original GUI only
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.attrib.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        prop=item.find("Properties")
        if prop is None:continue
        node=prop.find("string[@name='Source']")
        name=prop.find("string[@name='Name']")
        if node is not None:actual[node.text or ""]+=1
        if name is not None:names[(item.attrib["class"],name.text)]+=1
    expected=collections.Counter(v.decode("utf8") for v in src.values())
    assert actual==expected and sum(actual.values())==80, "ROJO_NOT_ALL80_SOURCE_EXACT"
    assert names[("Script","Game")]==1
    assert names[("LocalScript","TrapRaidersHUD")]==1
    assert names[("ModuleScript","SoloTeamBots")]==1
    result={
        "kind":"P0D_FB019_SOURCE_CANDIDATE",
        "source_count":80,"source_exact":True,"single_game":True,
        "single_remote_existing":True,
        "new_gui":0,"new_game_authorities":0,"other78_byte_exact":True,
        "owner_feedback":"FB-019","official_adopted":False,
        "studio_real":"NOT_TESTED","android":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB019_FOLLOWON_ACK_REAL80_SOURCE_EXACT_PASS",result["place_bytes"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
