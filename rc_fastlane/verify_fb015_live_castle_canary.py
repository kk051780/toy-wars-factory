#!/usr/bin/env python3
"""Verify source-exact actual Rojo Place for #431 opt-in castle canary."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb015_live_castle_canary import (
    read, blob, TARGET, FEATURE, ATTR, expected_original
)

def verify(dist:Path,place:Path,receipt:Path):
    sources=read(dist)
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(data) for p,data in sorted(sources.items())}
    assert len(sources)==sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    meta=fl["live_castle_canary"]
    assert meta["parent_castle_blob"]==blob(expected_original())
    assert meta["new_castle_blob"]==pins[TARGET]
    assert meta["other79_byte_identical"] is True
    assert meta["nonstudio_default"]=="OFF"
    assert meta["private_workspace_attribute"]==ATTR
    assert meta["nonstudio_max_art_parts"]==36
    expected=collections.Counter(data.decode("utf8") for data in sources.values())
    actual=collections.Counter()
    byname=collections.defaultdict(list)
    for item in ET.parse(place).iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        if props is None:
            continue
        src=props.find("string[@name='Source']")
        name=props.find("string[@name='Name']")
        if src is not None:
            text=src.text or ""
            actual[text]+=1
            if name is not None:
                byname[(kind,name.text or "")].append(text)
    assert actual==expected and sum(actual.values())==80,"ROJO80_SOURCE_NOT_EXACT"
    for kind,name,p in [
        ("Script","Game","server/Game.server.luau"),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("Script","CastleDetailArt",TARGET),
    ]:
        vals=byname[(kind,name)]
        assert len(vals)==1,(name,len(vals))
        assert vals[0]==sources[p].decode("utf8"),("INSTANCE_SOURCE_DRIFT",name)
    s=sources[TARGET].decode("utf8")
    assert 'workspace:GetAttribute("'+ATTR+'") ~= true then return end' in s
    assert 'assert(made==36,"LIVE_GATE_PART_BUDGET_DRIFT")' in s
    assert 'local isStudioPreview = RunService:IsStudio()' in s
    for forbidden in ("FireServer(","OnServerEvent:Connect(","TakeDamage(",
                      "GetDataStore(","CanCollide = true","CanQuery = true"):
        assert forbidden not in s,forbidden
    result={
      "schema":"P0D_PRIVATE_LIVE_CASTLE_SOURCE_EXACT_V1",
      "source_count":80,"actual_embedded_sources_exact":80,
      "changed_existing_art_source":[TARGET],
      "other79_byte_exact":True,
      "nonstudio_opt_in_attribute":ATTR,
      "nonstudio_default":"OFF", "nonstudio_part_budget":36,
      "new_lights_in_live_branch":0,"new_physics":0,
      "real_nonstudio_runtime":"NOT_TESTED",
      "real_android_15min":"NOT_TESTED",
      "owner_accepted":False, "art_decision":"ART_NO_GO",
      "live_art_decision":"LIVE_ART_NO_GO", "official_rc_adopted":False,
      "place_bytes":place.stat().st_size,
      "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_LIVE_CASTLE_ROJO80_EXACT_PASS",result["place_bytes"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
