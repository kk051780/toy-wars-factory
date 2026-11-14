#!/usr/bin/env python3
"""FB-019 native Studio Place acceptance: existing Game+HUD patched, 80 exact sources."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb019_attack_ack import read,blob,FEATURE,GAME,HUD,OLD_GAME,OLD_HUD

def verify(dist:Path,place:Path,receipt:Path):
    src=read(dist)
    assert len(src)==80
    pins={p:blob(v) for p,v in sorted(src.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb019_attack_ack"]["other78_byte_exact"] is True
    assert pins[GAME]!=OLD_GAME and pins[HUD]!=OLD_HUD
    expected=collections.Counter(v.decode("utf8") for v in src.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        p=item.find("Properties")
        if p is None:continue
        s=p.find("string[@name='Source']")
        n=p.find("string[@name='Name']")
        if s is not None:actual[s.text or ""]+=1
        if n is not None:names[(item.get("class"),n.text)]+=1
    assert expected==actual and sum(actual.values())==80,"ROJO_80_EMBEDDED_SOURCES_DIFFER"
    assert names[("Script","Game")]==1 and names[("LocalScript","TrapRaidersHUD")]==1
    assert names[("LocalScript","BattleHUDGovernor")]==1
    g=src[GAME].decode();h=src[HUD].decode()
    assert g.count('remote:FireClient(player,{kind="ATTACK_SWING_ACK"')==1
    attack=g[g.index("local function applyAttack"):g.index("\nend\n",g.index("local function applyAttack"))]
    assert attack.index("if not Rules.canAttack")<attack.index("lastAttack[player] = now")
    assert attack.index("lastAttack[player] = now")<attack.index('remote:FireClient(player,{kind="ATTACK_SWING_ACK"')<attack.index("horde:hit(")
    assert "hum:TakeDamage(" in attack and "match.hp[enemy]" in attack
    assert h.count("attack.Activated:Connect(requestAttack)")==1
    assert h.count('if input.KeyCode == Enum.KeyCode.F then requestAttack()')==1
    assert 'attack.MouseButton1Click:Connect(function() action("ATTACK"' not in h
    assert h.count('packet.kind=="ATTACK_SWING_ACK"')==1
    assert h.count('attackPhase~="ACTIVE"')==1
    assert 'FireServer({action="ATTACK_SWING_ACK"' not in h
    assert 'DataStoreService' not in h[h.index("-- FB019:"):h.index("attack.Activated:Connect(requestAttack)")]
    report={
       "feedback":"FB-019","scripts":80,
       "stage":"SOURCE_CI_PASS_STUDIO_RETEST_REQUIRED","source_exact":True,
       "game_authority":"ONE_ORIGINAL_GAME","existing_hud_one":True,
       "server_ack_only_after_valid_swing":True,
       "touch_pc_F_input_one_path":True,
       "transient_swing_only_no_fake_hit":True,
       "owner_fun":"NOT_TESTED","studio_pc_android":"NOT_TESTED",
       "place_bytes":place.stat().st_size,
       "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()
    }
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB019_RC80_SERVER_ACK_80_SOURCE_EXACT_PASS",report["place_bytes"],report["place_sha256"])

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--dist",required=True,type=Path)
    a.add_argument("--place",required=True,type=Path)
    a.add_argument("--receipt",required=True,type=Path)
    x=a.parse_args();verify(x.dist,x.place,x.receipt)
