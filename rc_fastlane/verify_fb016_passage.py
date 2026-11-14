#!/usr/bin/env python3
"""Verify FB-016 final physical Studio Place embeds exactly 80 authored sources.
This does NOT establish real in-engine pathing or player acceptance."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb016_passage import read,gitblob,FEATURE

def verify(dist:Path,place:Path,receipt:Path):
    data=read(dist)
    assert len(data)==80
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(v) for p,v in sorted(data.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb016_passage"]["original78_byte_exact"] is True
    expected=collections.Counter(v.decode("utf8") for v in data.values())
    actual=collections.Counter();names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        p=item.find("Properties")
        if p is None:continue
        src=p.find("string[@name='Source']")
        if src is not None:actual[src.text or ""]+=1
        nm=p.find("string[@name='Name']")
        if nm is not None:names[(item.get("class"),nm.text)]+=1
    assert expected==actual and sum(actual.values())==80,"NOT_ALL_RC80_NATIVE_SOURCE_EXACT"
    for typ,name in [
        ("Script","Game"),
        ("Script","Owner361CastleBattlefield"),
        ("Script","H1SeaGroundRepair"),
        ("Script","FoliagePassageFix"),
        ("LocalScript","FoliageCameraFade"),
        ("ModuleScript","SoloTeamBots"),
    ]:
        assert names[(typ,name)]==1,(typ,name,names[(typ,name)])
    server=data["server/FoliagePassageFix.server.luau"].decode()
    client=data["client/FoliageCameraFade.client.luau"].decode()
    for symbol in (
        'obj.CanCollide=false','obj.CanQuery=false',
        'p.CanCollide=true','oldTop-.5',
        '"SOUTH_MAINLAND"','"NORTH_HIGHLANDS"',
        '"WEST_COAST_FLANK"','"EAST_COAST_FLANK"',
        '"FOREST_TRUNK_"','"LeafMass_"',
    ):
        assert symbol in server,("MISSING_PASSAGE_GUARD",symbol)
    assert "LocalTransparencyModifier=if dist<radius+9 then .96 else 0" in client
    assert "local function decorativeFoliage" in server
    assert "server/Game.server.luau" in data
    results={
        "branch_role":"STAGING_UNTIL_CANONICAL_CAS_CONFIRMED",
        "source_count":80,
        "all_source_exact":True,
        "unique_game":True,
        "owner_feedback":"FB-016",
        "foliage_collision_policy":"SOURCE_AND_NATIVE_STATIC_TESTED",
        "shoreline_top_height":"UNCHANGED_BY_POLICY",
        "real_studio_walkthrough":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO",
        "owner_art":"ART_NO_GO",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB016_RC80_ALL_LUAU_ROJO_SOURCE_EXACT_PASS",
          results["place_bytes"],results["place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
