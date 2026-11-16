#!/usr/bin/env python3
"""Original-author one-hunk TEAM ForestAmbushCover_1 ↔ DASH clearance.

Private subcandidate sourced from GQ520's already verified original34+ridgetopology.
No original owner/Game/ITEM/ART/AI/Castle/Neutral/Lobby/Score/RC writes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from augment_current26 import scripts, sha_file, HOST
from patch_ridge import ORIGINAL_GIT_BLOB, git_blob, NEW as RIDGE_PATCH

OLD_FOREST='   local z=470+math.floor(n/4)*110'
NEW_FOREST='   local z=470+math.floor(n/4)*110+(if n==1 then 18 else 0)'
FOREST_LOOP='  for n=1,7 do\n'
NEW_HOST_NAME="GQ520_RIDGE_FOREST34.server.luau"
RECEIPT_NAME="GQ520_RIDGE_FOREST34_RECEIPT.json"
COUNT=34

def forest_report():
    """AABB analysis from original #482 immutable source; NOT Roblox physics."""
    trees=[(-800+(n%4)*38,470+(n//4)*110,n) for n in range(1,8)]
    before=(-760.0,1.8,470.0)
    def touch(x,z,point=before,r=1.1):
        return abs(point[0]-x)<=3.5+r and abs(point[2]-z)<=3.5+r
    embedded=[n for x,z,n in trees if touch(x,z)]
    moved=[(x,z+(18 if n==1 else 0),n) for x,z,n in trees]
    overlapping=[n for x,z,n in moved if touch(x,z)]
    return {"before_embedded_tree_ids":embedded,
            "after_embedded_tree_ids":overlapping,
            "tree_1_before":(-762,470),
            "tree_1_after":(-762,488),
            "tree_1_radius_1_1_clearance_z_studs":14.5-1.1,
            "all_trees_preserved":len(trees)==len(moved)==7,
            "other_tree_positions_preserved":trees[1:]==moved[1:],
            "roblox_studio_verified":False}

def patch_forest(existing:str, original:str, items:str)->str:
    if git_blob(original)!=ORIGINAL_GIT_BLOB:
        raise ValueError("RED: original #482 host blob changed")
    if (original.count(OLD_FOREST)!=1 or original.count(FOREST_LOOP)!=1
        or existing.count(OLD_FOREST)!=1 or existing.count(NEW_FOREST)):
        raise ValueError("RED: original TREE scope drift / already patched")
    if existing.count(RIDGE_PATCH)!=1 or "CastleDefense.start(session)" not in existing:
        raise ValueError("RED: original GQ520 ridge + #500 castle hook missing")
    if ("{x=-140,z=470,kind=\"DASH\"}" not in items
        or "xCenter=if session.mode==\"TEAM\" then -620 else 620" not in items
        or "table.insert(points,origin+Vector3.new(xCenter+site.x,1.8,site.z))" not in items):
        raise ValueError("RED: original DASH pickup site or origin drift")
    report=forest_report()
    if (report["before_embedded_tree_ids"]!=[1]
        or report["after_embedded_tree_ids"]
        or not report["all_trees_preserved"]
        or not report["other_tree_positions_preserved"]):
        raise ValueError("RED: forest geometry no longer supports one-tree repair")
    new=existing.replace(OLD_FOREST,NEW_FOREST)
    if new.replace(NEW_FOREST,OLD_FOREST)!=existing or new.count(RIDGE_PATCH)!=1:
        raise ValueError("RED: forest patch not strictly one-hunk reversible")
    return new

def prepare(base:Path, base_receipt:Path, original:Path, items:Path, out:Path):
    base=base.resolve(strict=True)
    base_receipt=base_receipt.resolve(strict=True)
    original=original.resolve(strict=True)
    items=items.resolve(strict=True)
    out=out.resolve()
    if (out.exists() or out.parent!=base.parent or out==base
        or out.parent==original.parent):
        raise ValueError("RED: output must be a fresh isolated private project")
    manifest,old=scripts(base,COUNT)
    receipt=json.loads(base_receipt.read_text(encoding="utf-8"))
    if (receipt.get("status")!="PRIVATE34_SOURCE_EXACT_NOT_OFFICIAL_RC"
        or receipt.get("source_count")!=COUNT
        or receipt.get("unchanged_owner_sources")!=33
        or receipt.get("one_private_host_hunk")!="TEAM.CentralRidge_ONE-BLOCK_SHIELD_CLEARANCE"
        or receipt.get("official_rc_adopted")!=0):
        raise ValueError("RED: original GQ520 private34 receipt mismatch")
    if set(receipt.get("source_sha256",{}))!=set(old):
        raise ValueError("RED: private34 owner inventory drift")
    for name,(_,source,_,_) in old.items():
        if sha_file(source)!=receipt["source_sha256"][name]:
            raise ValueError("RED: private34 owner bytes changed "+name)
    existing=old[HOST][1].read_text(encoding="utf-8")
    patched=patch_forest(existing,original.read_text(encoding="utf-8"),
        items.read_text(encoding="utf-8"))
    generated=out.parent/NEW_HOST_NAME
    if generated.exists():
        raise ValueError("RED: generated forest host already exists")
    generated.write_text(patched,encoding="utf-8")
    candidate=copy.deepcopy(manifest)
    candidate["name"]="GQ520_ORIGINAL34_RIDGE_PLUS_FOREST_DASH_PRIVATE_NO_RC"
    leaf=candidate["tree"]
    for k in old[HOST][0]:
        leaf=leaf[k]
    leaf["$path"]=os.path.relpath(generated,out.parent).replace(os.sep,"/")
    out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,new=scripts(out,COUNT)
    if set(new)!=set(old):
        raise ValueError("RED: changed number/type of original owner sources")
    for name,(_,source,cls,_) in old.items():
        _,target,new_cls,_=new[name]
        if new_cls!=cls or (name!=HOST and (source!=target or sha_file(source)!=sha_file(target))):
            raise ValueError("RED: modified original non-host authority "+name)
    result={
      "status":"PRIVATE34_RIDGE_FOREST_SOURCE_ONLY_NOT_RC",
      "origin":"#520 original34 one-ridge candidate exact source receipt",
      "original_host_git_blob":ORIGINAL_GIT_BLOB,
      "source_count":COUNT,"unchanged_original_owner_count":33,
      "one_previous_hunk":"TEAM.CentralRidge_SHIELD",
      "one_new_hunk":"TEAM.ForestAmbushCover_1_DASH",
      "forest_geometry":forest_report(),
      "parent_receipt_sha256":sha_file(base_receipt),
      "parent_project_sha256":sha_file(base),
      "source_sha256":{name:sha_file(v[1]) for name,v in sorted(new.items())},
      "claim":"SOFT_NOT_GRANTED",
      "official_rc_adopted":0,
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
      "rollback":"drop forest host mapping and restore GQ520 ridge-only private34 source"
    }
    (out.parent/RECEIPT_NAME).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ520_ORIGINAL34_FOREST_DASH_ONE_HUNK_33_AUTHORS_PRESERVED_PASS")
    return out

def verify(project:Path,place:Path):
    project=project.resolve(strict=True)
    place=place.resolve(strict=True)
    _,mapped=scripts(project,COUNT)
    receipt_path=project.parent/RECEIPT_NAME
    record=json.loads(receipt_path.read_text(encoding="utf-8"))
    if record.get("status")!="PRIVATE34_RIDGE_FOREST_SOURCE_ONLY_NOT_RC":
        raise ValueError("RED: wrong forest candidate receipt")
    actual={}
    for el in ET.parse(place).getroot().iter("Item"):
        cls=el.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=el.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or name in actual or source is None:
            raise ValueError("RED: duplicate/missing Rojo script "+str(name))
        actual[name]=(cls,source.replace("\r\n","\n"))
    if set(actual)!=set(mapped) or len(actual)!=COUNT:
        raise ValueError("RED: expected exactly 34 distinct Luau scripts")
    for name,(_,source,cls,_) in mapped.items():
        if (actual[name]!=(cls,source.read_text(encoding="utf-8").replace("\r\n","\n"))
            or sha_file(source)!=record["source_sha256"][name]):
            raise ValueError("RED: real Rojo source/class mismatch "+name)
    record["place_bytes"]=place.stat().st_size
    record["place_sha256"]=sha_file(place)
    receipt_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ520_RIDGE_FOREST34_REAL_ROJO_SOURCE_CLASS_34_OF_34_PASS",
          record["place_bytes"],record["place_sha256"])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="action",required=True)
    c=sub.add_parser("prepare")
    for n in ("base","base_receipt","original","items","out"):
        c.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    c=sub.add_parser("verify")
    for n in ("project","place"):
        c.add_argument("--"+n,type=Path,required=True)
    a=ap.parse_args()
    if a.action=="prepare":
        prepare(a.base,a.base_receipt,a.original,a.items,a.out)
    else:
        verify(a.project,a.place)
if __name__=="__main__":main()
