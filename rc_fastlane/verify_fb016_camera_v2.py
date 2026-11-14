#!/usr/bin/env python3
"""Validate actual private80 Rojo Place embeds all pinned script sources."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb016_camera_v2 import read,gitblob,TARGET,NEW_BLOB,FEATURE

def verify(dist:Path,place:Path,receipt:Path)->None:
    source=read(dist)
    assert len(source)==80
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(raw) for p,raw in sorted(source.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert pins[TARGET]==NEW_BLOB
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb016_camera_v2"]["other_79_source_bytes_unchanged"] is True
    expected=collections.Counter(raw.decode("utf8") for raw in source.values())
    actual=collections.Counter()
    names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        if props is None:continue
        n=props.find("string[@name='Name']")
        code=props.find("string[@name='Source']")
        if n is not None:names[(item.get("class"),n.text)]+=1
        if code is not None:actual[code.text or ""]+=1
    assert expected==actual and sum(actual.values())==80,"ROJO_SOURCE_NOT_EXACT"
    assert names[("Script","Game")]==1
    assert names[("LocalScript","FoliageCameraFade")]==1
    data={
        "stage":"PRIVATE_SOURCE_QA_STUDIO_RETEST_PENDING",
        "feedback":["FB-016","FB-015"],"source_count":80,
        "rojo_80_80_exact":True,"single_game":True,
        "other79_byte_exact":True,"official_rc_updated":False,
        "engine_studio":"NOT_TESTED","android":"NOT_TESTED",
        "owner_art":"ART_NO_GO","owner_fun":"FUN_NO_GO",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB016_ART_SIGHTLINE_V2_PRIVATE80_ROJO_EXACT_PASS",data["place_bytes"])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dist",type=Path,required=True)
    ap.add_argument("--place",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    verify(a.dist,a.place,a.receipt)
