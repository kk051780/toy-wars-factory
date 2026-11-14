#!/usr/bin/env python3
"""Verifies five reversible RC80 overlays as one real Studio Place (private only).
No human art rating, Android FPS claim or OWNER approval is generated here.
"""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
from defusedxml import ElementTree as ET

CHANGED={
    "server/Game.server.luau",
    "client/HUD.client.luau",
    "client/FoliageCameraFade.client.luau",
    "server/FantasyWorldArt.server.luau",
    "client/FB015CharacterArt.client.luau",
    "server/CastleDetailArt.server.luau",
}
FLAGS=(
    "FB019_ATTACK_RESPONSE_V1",
    "FB016_ART_CAMERA_SIGHTLINE_V2",
    "FB015_FOREST_BIOMES_MONUMENTS_V2",
    "FB015_GOROGAN_MOBILE_LOD_V1",
    "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
)
def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def read(root:Path)->dict[str,bytes]:
    assert root.is_dir()
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
       for p in sorted((root/"src").rglob("*.luau"))}
def verify(base:Path,dist:Path,place:Path,receipt:Path):
    before=read(base);after=read(dist)
    assert len(before)==len(after)==80 and set(before)==set(after),"80_SOURCE_SET_DRIFT"
    changed={p for p in before if before[p]!=after[p]}
    assert changed==CHANGED,("SIX_SOURCE_DIFF_UNEXPECTED",sorted(changed^CHANGED))
    oldpins={p:blob(s) for p,s in sorted(before.items())}
    pins={p:blob(s) for p,s in sorted(after.items())}
    for root,lockpins in [(base,oldpins),(dist,pins)]:
        sl=json.loads((root/"SOURCE_LOCK.json").read_text())
        fl=json.loads((root/"RC_FEATURE_LOCK.json").read_text())
        assert sl["total_scripts"]==fl["total_sources"]==80
        assert sl["blobs"]==fl["source_gitblobs"]==lockpins,"PIN_DRIFT"
    flags=json.loads((dist/"RC_FEATURE_LOCK.json").read_text())["feature_flags"]
    assert all(flags.get(x) is True for x in FLAGS),"OVERLAY_MISSING"
    assert len({x for x in FLAGS if flags.get(x)})==len(FLAGS),"DUPLICATE_FLAG"
    expected=collections.Counter(raw.decode("utf8") for raw in after.values())
    actual=collections.Counter();names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        assert props is not None,"SOURCELESS_SCRIPT"
        code=props.find("string[@name='Source']")
        name=props.find("string[@name='Name']")
        assert code is not None and name is not None,"SCRIPT_NAME_OR_SOURCE_MISSING"
        actual[code.text or ""]+=1
        names[(cls,name.text or "")]+=1
    assert actual==expected and sum(actual.values())==80,"PLACE_SOURCE_MISMATCH"
    assert names[("Script","Game")]==1,"SINGLE_GAME_REQUIRED"
    assert names[("LocalScript","TrapRaidersHUD")]==1,"SINGLE_HUD_REQUIRED"
    assert names[("Script","CastleDetailArt")]==1
    assert names[("Script","FantasyWorldArt")]==1
    assert names[("LocalScript","FoliageCameraFade")]==1
    assert names[("LocalScript","FB015CharacterArt")]==1
    data={
       "stage":"PRIVATE_SOURCE_ONLY_UNACCEPTED",
       "official_rc_integrated":False,
       "script_count":80,
       "changed_sources":sorted(changed),
       "other_74_byte_identical":True,
       "exact_source_place":True,
       "overlay_feature_ids":list(FLAGS),
       "place_bytes":place.stat().st_size,
       "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
       "pc_visual":"NOT_TESTED",
       "android_15min":"NOT_TESTED",
       "kid_fun_3min":"NOT_TESTED",
       "owner_accepted":False,
       "art_decision":"ART_NO_GO",
       "mobile_decision":"MOBILE_NO_GO",
       "fun_decision":"FUN_NO_GO",
    }
    assert not receipt.exists()
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("P0D_MULTI5_FULL80_SIX_CHANGED_SOURCE_EXACT_PASS",data["place_bytes"],data["place_sha256"])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for p in ("base","dist","place","receipt"):ap.add_argument("--"+p,required=True,type=Path)
    x=ap.parse_args()
    verify(x.base,x.dist,x.place,x.receipt)
