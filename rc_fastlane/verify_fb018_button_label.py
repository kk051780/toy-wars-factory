#!/usr/bin/env python3
"""FB018 QA: Luau source exact in built RC80 Studio Place, no duplicated Game."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb018_button_label import read,blob,TARGET,FEATURE,LABEL_NEW,POWER_NEW
def verify(dist:Path,place:Path,receipt:Path):
    source=read(dist)
    assert len(source)==80
    pins={p:blob(v) for p,v in sorted(source.items())}
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb018_button_label"]["other79_byte_exact"] is True
    expected=collections.Counter(v.decode("utf8") for v in source.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        pr=item.find("Properties")
        if pr is None:continue
        code=pr.find("string[@name='Source']")
        if code is not None:actual[code.text or ""]+=1
        name=pr.find("string[@name='Name']")
        if name is not None:names[(item.get("class"),name.text)]+=1
    assert expected==actual and sum(actual.values())==80,"ROJO_SOURCE_MISMATCH"
    assert names[("Script","Game")]==1 and names[("LocalScript","TrapRaidersHUD")]==1
    assert names[("LocalScript","BattleHUDGovernor")]==1
    hud=source[TARGET].decode("utf8")
    assert hud.count(LABEL_NEW)==1
    assert hud.count(POWER_NEW)==1
    assert hud.index("    b.Text = text")<hud.index("    b.Parent = parent")
    assert hud.count("local function button(parent: Instance")==1
    data={
        "source_count":80,"all_source_exact":True,
        "original79_unchanged":True,"unique_game":True,
        "fb":"FB-018","button_text_initialized":True,
        "locked_awakening_hidden":True,
        "engine_studio":"NOT_TESTED","owner_fun":"FUN_NO_GO",
        "owner_art":"ART_NO_GO",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB018_BUTTON_TEXT_REAL_PLACE_ALL80_SOURCE_EXACT_PASS",
          data["place_bytes"],data["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
