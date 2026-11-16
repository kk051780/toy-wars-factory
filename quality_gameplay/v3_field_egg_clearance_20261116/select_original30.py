#!/usr/bin/env python3
"""GQ523 unique intake: re-use #521's REAL 30-source private Place, then original #520 ridge
and current #523 FIELD egg grid two disjoint host hunks. No other source rewritten.
This is a private package, not the sole #220 official RC writer.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from patch_field_eggs import ORIGINAL_LINE, REPLACEMENT_LINE, ROWS_LINE, patch as patch_eggs

PARENT_PLACE_SHA="583d4c2c266f0f12f52d47789310598ad51315e060238668a431b4cdf889116b"
PARENT_PR_HEAD="272964b0ad11fccf1cda49e7da70fbcd091d4315"
UPSTREAM_BOSS_HEAD="f31081d5cb2bea86d01c76c53bb60cd2f9a8355d"
UPSTREAM_RIDGE_HEAD="f53162f4dc1d0f1832942a28bf89df7114ae4f3d"
HOST="EGGRUMBLE_LobbyCastleModesPreview"
BOSS="EGGRUMBLE_NeutralStoneGiant"
EXPECTED=30
NEEDED={
 "EGGRUMBLE_SevenRoleCombat",HOST,"EGGRUMBLE_CastleMatchRules",
 "EGGRUMBLE_AttackGeometry","EGGRUMBLE_SwarmCombat",BOSS,
 "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_RaidItemIntake",
 "EGGRUMBLE_RoundReplay","EGGRUMBLE_BotActors",
 "EGGRUMBLE_CombatBalance","EGGRUMBLE_ScoreBalance",
 "EGGRUMBLE_RoundAttributeFence","EGGRUMBLE_BossCreditPolicy",
 "EGGRUMBLE_FlagshipFieldArt",
}

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def source_map(place:Path)->dict:
    result={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        assert name and source is not None and name not in result,"missing/duplicate Script Source"
        assert re.fullmatch(r"EGGRUMBLE_[A-Za-z0-9_]+",name),name
        result[name]=(cls,source.replace(chr(13)+chr(10),chr(10)))
    assert len(result)==EXPECTED and NEEDED.issubset(result),("name/source drift",len(result))
    return result

def load_tool(path:Path):
    assert path.name=="patch_ridge.py" and path.is_file()
    spec=importlib.util.spec_from_file_location("original_gq520_ridge",path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert "CentralRidgeRight" in module.NEW and "CentralRidgeRight" not in module.OLD
    return module

def apply_two(existing:str, old:str, new:str)->str:
    assert existing.count(old)==1,"original #520 ridge anchor already changed"
    assert new not in existing,"ridge already patched: double source selection"
    assert existing.count(ORIGINAL_LINE)==1,"original #482 field egg grid drift"
    assert "CastleAccessRamp" in existing,"original #484 castle access lost"
    assert 'for i=1,24 do' in existing and 'local eggId="FIELD_"..i' in existing
    patched_ridge=existing.replace(old,new,1)
    patched=patch_eggs(patched_ridge)
    assert patched.replace(ROWS_LINE,"",1).replace(REPLACEMENT_LINE,ORIGINAL_LINE,1).replace(new,old,1)==existing
    assert patched.count("CastleAccessRamp")==existing.count("CastleAccessRamp")
    assert patched.count("Rules.takeFieldEgg(")==existing.count("Rules.takeFieldEgg(")
    assert patched.count("CentralRidgeRight")==1
    return patched

def rebase_project(data:dict,source_by_name:dict,outdir:Path)->dict:
    obj=copy.deepcopy(data)
    used=[]
    def walk(node,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            assert set(node)=={"$path"}
            name=chain[-1]
            assert name in source_by_name and name not in used,name
            cls=source_by_name[name][0]
            suffix=(".server.luau" if cls=="Script" else
                    ".client.luau" if cls=="LocalScript" else ".luau")
            node["$path"]="scripts/"+name+suffix
            used.append(name)
        else:
            for k,v in node.items():
                if not k.startswith("$"):walk(v,chain+(k,))
    walk(obj["tree"])
    assert len(used)==EXPECTED and set(used)==set(source_by_name)
    obj["name"]="GQ523_FIELD_EGG_AND_RIDGE_IN_ORIGINAL_GQ521_30_PRIVATE_NOT_RC"
    return obj

def prepare(parent_place:Path,parent_project:Path,parent_receipt:Path,
            ridge_tool:Path,outdir:Path):
    parent_place=parent_place.resolve(strict=True)
    parent_project=parent_project.resolve(strict=True)
    parent_receipt=parent_receipt.resolve(strict=True)
    outdir=outdir.resolve()
    for p in (parent_place,parent_project,parent_receipt,ridge_tool):
        assert outdir!=p and not p.is_relative_to(outdir),"never write to upstream source"
    assert sha(parent_place.read_bytes())==PARENT_PLACE_SHA, "wrong parent original30 artifact"
    parent=json.loads(parent_receipt.read_text(encoding="utf-8"))
    assert parent.get("rojo_exact_source_class")=="30/30","original #521 did not prove 30 class/source"
    assert parent.get("original_boss_blob")=="2670618cba320c51936c750a10e43c194cada0f0"
    assert parent.get("fixed_original_author_refs",{}).get("boss_los")==UPSTREAM_BOSS_HEAD
    assert len(parent["source_exact_sha256"])==EXPECTED
    before=source_map(parent_place)
    assert set(before)==set(parent["source_exact_sha256"])
    for name,(cls,source) in before.items():
        assert sha(source.encode("utf-8"))==parent["source_exact_sha256"][name],("parent source drift",name)
    # Reuse and do not modify upstream #518 boss LOS, #517 item heal and 512/514 counters.
    boss=before[BOSS][1]
    assert "RespectCanCollide=true" in boss and "h:TakeDamage(28)" in boss
    assert "GQ518" in str(parent.get("feature","")) or "518" in str(parent.get("feature",""))
    assert before["EGGRUMBLE_FieldItemPickups"][1].count("HEAL")>0
    assert "CastleAccessRamp" in before[HOST][1]
    assert "{x=0,z=470,kind=\"SHIELD\"}" in before["EGGRUMBLE_RaidItemIntake"][1]
    ridge=load_tool(ridge_tool)
    changed=apply_two(before[HOST][1],ridge.OLD,ridge.NEW)
    after=dict(before)
    after[HOST]=(before[HOST][0],changed)
    modified=[name for name in before if before[name]!=after[name]]
    assert modified==[HOST] and len(after)==EXPECTED
    assert sum(after[name]==before[name] for name in before)==29
    assert before[BOSS]==after[BOSS] and before["EGGRUMBLE_FieldItemPickups"]==after["EGGRUMBLE_FieldItemPickups"]
    original_project=json.loads(parent_project.read_text(encoding="utf-8"))
    outdir.mkdir(parents=True,exist_ok=True)
    scripts=outdir/"scripts"
    scripts.mkdir(exist_ok=True)
    manifest=rebase_project(original_project,after,outdir)
    for name,(cls,source) in after.items():
        suffix=(".server.luau" if cls=="Script" else
                ".client.luau" if cls=="LocalScript" else ".luau")
        (scripts/(name+suffix)).write_text(source,encoding="utf-8")
    project=outdir/"GQ523_ORIGINAL30_RIDGE_FIELD.project.json"
    project.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt={
       "status":"PRIVATE30_SOURCE_ONLY_NOT_OFFICIAL_RC",
       "source_count":30,"original_parent_sources_byte_exact":29,
       "changed_only":[HOST],"parent_original_521_head":PARENT_PR_HEAD,
       "parent_private_place_sha256":PARENT_PLACE_SHA,
       "original_518_boss_head":UPSTREAM_BOSS_HEAD,
       "original_520_ridge_head":UPSTREAM_RIDGE_HEAD,
       "source_sha256_before":parent["source_exact_sha256"],
       "source_sha256_after":{k:sha(v[1].encode("utf-8")) for k,v in sorted(after.items())},
       "one_game":True,"one_original_boss_518":True,
       "original_item_heal_517":True,"original_combo_512":True,
       "original_boss_credit_514":True,
       "original_field_route_ridge_520":True,"new_egg_clearance_523":True,
       "original_484_castle_ramp":True,"all_eight_domains":True,
       "formal_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
       "art_fun_owner":"NO_GO",
    }
    (outdir/"GQ523_ORIGINAL30_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ523_PLUS_520_IN_CANONICAL_518_517_ORIGINAL30_PREP_PASS 29_OF_30_UNCHANGED")

def verify(project:Path,place:Path):
    project=project.resolve(strict=True)
    outdir=project.parent
    manifest=json.loads(project.read_text(encoding="utf-8"))
    after=source_map(place)
    receipt=json.loads((outdir/"GQ523_ORIGINAL30_RECEIPT.json").read_text())
    assert set(after)==set(receipt["source_sha256_after"]) and len(after)==30
    observed={}
    def scan(node,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            name=chain[-1]
            p=(outdir/node["$path"]).resolve(strict=True)
            assert p.is_relative_to(outdir)
            cls,src=after[name]
            suffix=(".server.luau" if cls=="Script" else
                    ".client.luau" if cls=="LocalScript" else ".luau")
            assert p.name==name+suffix
            assert sha(src.encode("utf-8"))==sha(p.read_bytes())==receipt["source_sha256_after"][name]
            assert name not in observed
            observed[name]=cls
        else:
            for k,v in node.items():
                if not k.startswith("$"):scan(v,chain+(k,))
    scan(manifest["tree"])
    assert set(observed)==set(after)
    assert receipt["source_sha256_before"][BOSS]==receipt["source_sha256_after"][BOSS]
    assert receipt["source_sha256_before"]["EGGRUMBLE_FieldItemPickups"]==receipt["source_sha256_after"]["EGGRUMBLE_FieldItemPickups"]
    receipt["private_place_bytes"]=place.stat().st_size
    receipt["private_place_sha256"]=sha(place.read_bytes())
    receipt["real_rojo_source_class_exact"]="30/30"
    (outdir/"GQ523_ORIGINAL30_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ523_ORIGINAL30_RIDGE_EGGS_BOSS_HEAL_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",
          receipt["private_place_bytes"],receipt["private_place_sha256"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["prepare","verify"])
    ap.add_argument("--parent-place",type=Path)
    ap.add_argument("--parent-project",type=Path)
    ap.add_argument("--parent-receipt",type=Path)
    ap.add_argument("--ridge-tool",type=Path)
    ap.add_argument("--outdir",type=Path)
    ap.add_argument("--project",type=Path)
    ap.add_argument("--place",type=Path)
    a=ap.parse_args()
    if a.mode=="prepare":
        assert all((a.parent_place,a.parent_project,a.parent_receipt,a.ridge_tool,a.outdir))
        prepare(a.parent_place,a.parent_project,a.parent_receipt,a.ridge_tool,a.outdir)
    else:
        assert a.project and a.place
        verify(a.project,a.place)

if __name__=="__main__":
    main()
