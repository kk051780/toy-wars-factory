#!/usr/bin/env python3
"""Exact real Rojo 82-source audit for production-MapBuilder private forest pilot."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_live_forest_safe import read,blob,DEST,FEATURE,AUTHOR_BLOB,author

def verify(dist:Path,place:Path,receipt:Path):
    sources=read(dist)
    assert len(sources)==82 and DEST in sources
    author(sources[DEST])
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(d) for p,d in sorted(sources.items())}
    assert sl["total_scripts"]==fl["total_sources"]==82
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    config=fl["live_forest_private_pilot"]
    assert config["new_source_blob"]==AUTHOR_BLOB
    assert config["original_81_source_byte_exact"] is True
    raw=place.read_bytes()
    assert 0<len(raw)<10000000
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    expected=collections.Counter(s.decode("utf8") for s in sources.values())
    actual=collections.Counter()
    byname=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"): continue
        props=item.find("Properties")
        if props is None: continue
        src=props.find("string[@name='Source']")
        name=props.find("string[@name='Name']")
        if src is None: continue
        text=src.text or ""
        actual[text]+=1
        if name is not None:
            byname[(kind,name.text or "")].append(text)
    assert actual==expected and sum(actual.values())==82,"REAL_82_LUA_SOURCE_MISMATCH"
    for kind,name,p in [
        ("Script","Game","server/Game.server.luau"),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("Script","P0DLiveForestArt",DEST),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau"),
        ("ModuleScript","MapBuilder","server/MapBuilder.luau"),
    ]:
        matches=byname[(kind,name)]
        assert len(matches)==1 and matches[0]==sources[p].decode("utf8"),(
            "BAD_GAME_ORIGINAL_INSTANCE",name,len(matches))
    s=sources[DEST].decode("utf8")
    assert "game.PrivateServerId" in s
    assert 'workspace:GetAttribute("P0D_PRIVATE_LIVE_FOREST")' in s
    for token in ("CanCollide = true","CanQuery = true",
                  "FireServer(","OnServerEvent:Connect(","GetDataStore(",
                  "Terrain:FillBlock(","Instance.new(\"ScreenGui\")"):
        assert token not in s
    report={
        "schema":"P0D_PRIVATE_LIVE_FOREST_SOURCE_EXACT_V1",
        "scripts":82,"rojo_source_exact":82,"new_script":DEST,
        "original81_byte_identical":True,
        "private_nonstudio_only_opt_in":True,
        "public_default":"OFF","max_static_parts":60,
        "nonstudio_runtime":"NOT_TESTED","actual_fps":"NOT_TESTED",
        "pc_appearance":"NOT_TESTED","owner_accepted":False,
        "art_decision":"ART_NO_GO",
        "live_art_decision":"LIVE_ART_NO_GO",
        "mobile_decision":"MOBILE_NO_GO","fun_decision":"FUN_NO_GO",
        "official_rc_adopted":False,
        "place_bytes":len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest(),
    }
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_LIVE_FOREST_82_REAL_ROJO_EXACT_PASS",report["place_bytes"])
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
