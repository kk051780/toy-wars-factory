#!/usr/bin/env python3
"""Validate FB019 full private RC80 Rojo Place; only HUD source is different."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb019_swing_feedback import read,blob,TARGET,FEATURE

def verify(dist:Path,place:Path,receipt:Path)->None:
    source=read(dist)
    assert len(source)==80
    pins={p:blob(raw) for p,raw in sorted(source.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb019_attack_swing_feedback"]["other_79_byte_exact"] is True
    assert fl["fb019_attack_swing_feedback"]["new_source_blob"]==pins[TARGET]
    expected=collections.Counter(x.decode("utf8") for x in source.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        pr=item.find("Properties")
        if pr is None:continue
        n=pr.find("string[@name='Name']")
        s=pr.find("string[@name='Source']")
        if n is not None:names[(item.get("class"),n.text)]+=1
        if s is not None:actual[s.text or ""]+=1
    assert actual==expected and sum(actual.values())==80, "SOURCE_EXACT_FAILED"
    assert names[("Script","Game")]==1
    assert names[("LocalScript","TrapRaidersHUD")]==1
    assert names[("LocalScript","BattleHUDGovernor")]==1
    code=source[TARGET].decode("utf8")
    assert code.count("fb019ShowSwing()")==2
    assert code.count('remote:FireServer({action = kind, role = role, seq = seq})')==1
    assert 'fb019InBattle = s.phase == "ACTIVE"' in code
    data={
        "feedback":"FB-019","stage":"PRIVATE_RC80_SOURCE_QA_ONLY",
        "source_count":80,"all_rojo_source_exact":True,"one_original_game":True,
        "original_79_sources_unchanged":True,
        "attack_input_visual_not_authoritative_hit":True,
        "server_damage":"UNCHANGED","studio":"NOT_TESTED",
        "android":"NOT_TESTED","owner_fun":"FUN_NO_GO",
        "official_rc_adopted":False,
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB019_PRIVATE_RC80_REAL_ROJO_80_80_EXACT_PASS",data["place_bytes"])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dist",required=True,type=Path)
    ap.add_argument("--place",required=True,type=Path)
    ap.add_argument("--receipt",required=True,type=Path)
    a=ap.parse_args()
    verify(a.dist,a.place,a.receipt)
