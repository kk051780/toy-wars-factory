#!/usr/bin/env python3
"""Verify the actual candidate Studio Place's 80 embedded Luau scripts."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb015_gorogan_mobile_lod import read,blob,TARGET,FEATURE,BASE_BLOB

def verify(dist:Path,place:Path,receipt:Path):
    scripts=read(dist)
    source_lock=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    flags=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    exact={name:blob(src) for name,src in sorted(scripts.items())}
    assert len(scripts)==80==source_lock["total_scripts"]==flags["total_sources"]
    assert source_lock["blobs"]==flags["source_gitblobs"]==exact
    assert flags["feature_flags"][FEATURE] is True
    info=flags["fb015_beast_mobile_lod"]
    assert info["old_git_blob"]==BASE_BLOB
    assert info["new_git_blob"]==exact[TARGET]
    assert info["other79_byte_exact"] is True
    assert info["changed_source"]==[TARGET]
    expected=collections.Counter(src.decode("utf8") for src in scripts.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        ps=item.find("Properties")
        if ps is None:continue
        code=ps.find("string[@name='Source']")
        name=ps.find("string[@name='Name']")
        if code is not None:actual[code.text or ""]+=1
        if name is not None:names[(kind,name.text)]+=1
    assert actual==expected and sum(actual.values())==80, "NOT_80_EXACT_ROJO_SOURCES"
    for kind,name in (("Script","Game"),("LocalScript","TrapRaidersHUD"),
                      ("LocalScript","BattleHUDGovernor"),
                      ("LocalScript","FB015GoroganVisual")):
        assert names[(kind,name)]==1,("NOT_SINGLE_AUTHOR",name)
    art=scripts[TARGET].decode("utf8")
    for clause in ("LocalTransparencyModifier","LOW_END_TOUCH",
                   "MobileDetailRadiusStuds","RunService.Heartbeat:Connect",
                   "MAX_DECOR_PARTS = 64","partCount += 1"):
        assert clause in art,clause
    for forbidden in ("TakeDamage(","FireServer(","GetDataStore(",
                      "CanCollide = true","CanQuery = true"):
        assert forbidden not in art,forbidden
    receipt_out={
        "kind":"P0D_FB015_GOROGAN_MOBILE_LOD_PRIVATE",
        "source_count":80,"embedded_source_exact":80,
        "source_changed":[TARGET],"other79_source_byte_exact":True,
        "one_original_game":True,"one_original_hud":True,
        "mobile_lod_static_policy":True,
        "mobile_phone_art": "STUDIO_NOT_TESTED",
        "fps_on_low_end_android": "NOT_TESTED",
        "visual_score": "NOT_TESTED",
        "owner_accepted":False,
        "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
        "official_rc_adopted":False,
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()
    }
    receipt.write_text(json.dumps(receipt_out,ensure_ascii=False,indent=2)+"\n","utf8")
    print("GOROGAN_MOBILE_LOD_PRIVATE80_ROJO_SOURCE_EXACT_PASS",receipt_out["place_bytes"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
