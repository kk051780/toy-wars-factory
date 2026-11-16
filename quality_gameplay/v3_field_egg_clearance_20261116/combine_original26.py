#!/usr/bin/env python3
"""Source-select GQ523 field eggs AFTER original #484 26 + ORIGINAL GQ520 ridge.
Never reimplement any role/field/battle/castle/neutral/ITEM/lobby/balance game source.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from patch_field_eggs import patch, ROWS_LINE, ORIGINAL_LINE, REPLACEMENT_LINE

HOST="EGGRUMBLE_LobbyCastleModesPreview"
EXPECTED=26
OTHER_ORIGINALS=25

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def load_map(project:Path):
    project=project.resolve(strict=True)
    doc=json.loads(project.read_text(encoding="utf-8"))
    assert doc["tree"]["$className"]=="DataModel"
    found={}
    def visit(node:dict,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            assert set(node)=={"$path"}
            assert chain and chain[-1] not in found
            real=(project.parent/node["$path"]).resolve(strict=True)
            cls=("Script" if real.name.endswith(".server.luau") else
                 "LocalScript" if real.name.endswith(".client.luau") else "ModuleScript")
            found[chain[-1]]=(chain,real,cls)
        else:
            for name,child in node.items():
                if not name.startswith("$"):visit(child,chain+(name,))
    visit(doc["tree"])
    assert len(found)==EXPECTED and HOST in found
    assert found[HOST][2]=="Script"
    assert sum(n=="EGGRUMBLE_LobbyCastleModesPreview" for n in found)==1
    assert "EGGRUMBLE_ScoreBalance" in found
    assert "EGGRUMBLE_FlagshipFieldArt" in found
    assert "EGGRUMBLE_BotActors" in found and "EGGRUMBLE_SwarmCombat" in found
    return doc,found

def prepare(ridge_project:Path,outdir:Path):
    ridge_project=ridge_project.resolve(strict=True)
    outdir=outdir.resolve()
    assert outdir!=ridge_project.parent and not ridge_project.is_relative_to(outdir)
    base,inputs=load_map(ridge_project)
    r=json.loads((ridge_project.parent/"GQ520_PRIVATE26_RECEIPT.json").read_text(encoding="utf-8"))
    assert r["source_count"]==26 and r["unchanged_source_count"]==25
    assert set(r["source_sha256"])==set(inputs)
    for name,(_,p,_) in inputs.items():
        assert sha(p.read_bytes())==r["source_sha256"][name],"Ridge original source receipt drift "+name
    existing=inputs[HOST][1].read_text(encoding="utf-8")
    assert "CastleAccessRamp" in existing, "original #484 castle entrance lost"
    assert "CentralRidgeRight" in existing, "#520 ridge fix must already be selected"
    assert existing.count(ORIGINAL_LINE)==1, "field egg source drift"
    changed=patch(existing)
    assert changed.replace(ROWS_LINE,"",1).replace(REPLACEMENT_LINE,ORIGINAL_LINE,1)==existing
    assert changed.count("CentralRidgeRight")==existing.count("CentralRidgeRight")
    assert changed.count("CastleAccessRamp")==existing.count("CastleAccessRamp")
    outdir.mkdir(parents=True,exist_ok=True)
    host=outdir/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    host.write_text(changed,encoding="utf-8")
    new=copy.deepcopy(base)
    records={}
    for name,(chain,original,cls) in inputs.items():
        chosen=host if name==HOST else original
        node=new["tree"]
        for token in chain:node=node[token]
        node["$path"]=Path(os.path.relpath(chosen,outdir)).as_posix()
        records[name]={"baseline":sha(original.read_bytes()),"after":sha(chosen.read_bytes()),
                       "class":cls,"chosen":str(chosen)}
    assert [n for n,r in records.items() if r["baseline"]!=r["after"]]==[HOST]
    assert sum(r["baseline"]==r["after"] for r in records.values())==OTHER_ORIGINALS
    new["name"]="GQ523_ORIGINAL26_RIDGE520_PLUS_EGG523_PRIVATE_NO_OFFICIAL_RC"
    project=outdir/"GQ523_FIELD_EGGS_RIDGE_AUTHOR26.project.json"
    project.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=load_map(project)
    assert set(mapped)==set(inputs)
    receipt={"source_count":26,"source_exact_before":26,"original_520_ridge_source_kept":True,
             "original_484_castle_ramp_kept":True,
             "unchanged_other_authors":OTHER_ORIGINALS,"overlay_host_only":HOST,
             "owner_520_ridge_head":"f53162f4dc1d0f1832942a28bf89df7114ae4f3d",
             "original_482_head":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
             "original_484_head":"6b52eaf1f2725496277998fe0c5532b7a8fcaab5",
             "original_485_head":"e86702c906bdf9c71adcdf769ae48a206b26607b",
             "original_487_head":"438a406ccfda5563053d783d7561797ccd364361",
             "sources":records,"formal_rc_adopted":False,"android_studio_owner":"NOT_TESTED"}
    (outdir/"GQ523_PRIVATE26_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ523_ORIGINAL26_ART_AI_SCORE_PLUS_RIDGE520_AND_FIELD_EGG523_ONE_HOST_PASS",len(mapped),OTHER_ORIGINALS)

def verify(project:Path,place:Path):
    _,mapped=load_map(project)
    r=json.loads((project.parent/"GQ523_PRIVATE26_RECEIPT.json").read_text(encoding="utf-8"))
    observed={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        body=props.findtext("ProtectedString[@name='Source']")
        if body is None:body=props.findtext("string[@name='Source']")
        assert name and body is not None and name not in observed,"missing/duplicate Script Source"
        observed[name]=(cls,body.replace(chr(13)+chr(10),chr(10)).encode("utf-8"))
    assert set(observed)==set(mapped) and len(observed)==EXPECTED
    for name,(_,src,cls) in mapped.items():
        ocls,body=observed[name]
        assert cls==ocls,"Rojo class mismatch "+name
        assert sha(body)==sha(src.read_bytes())==r["sources"][name]["after"],"Source mismatch "+name
    r["private_place_bytes"]=place.stat().st_size
    r["private_place_sha256"]=sha(place.read_bytes())
    r["rojo_exact"]="26/26"
    (project.parent/"GQ523_PRIVATE26_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("GQ523_ORIGINAL26_ROJO_SOURCE_CLASS_EXACT_PASS",r["private_place_bytes"],r["private_place_sha256"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("op",choices=["prepare","verify"])
    ap.add_argument("--ridge-project",type=Path)
    ap.add_argument("--outdir",type=Path)
    ap.add_argument("--project",type=Path)
    ap.add_argument("--place",type=Path)
    a=ap.parse_args()
    if a.op=="prepare":
        assert a.ridge_project and a.outdir
        prepare(a.ridge_project,a.outdir)
    else:
        assert a.project and a.place
        verify(a.project,a.place)

if __name__=="__main__":
    main()
