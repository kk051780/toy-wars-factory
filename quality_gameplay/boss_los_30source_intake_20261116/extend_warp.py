#!/usr/bin/env python3
"""Read-only owner #524 Combat safeMove source selection in existing #521 original30.

Exactly one existing Combat module is generated; no new Lua authority or code.
#518 boss, #520 ridge, #523 eggs, #517 ITEM/HEAL, #512 COMBO, #514 boss
credit and every other authored module must remain byte-identical.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from intake import mapped, sha, git_blob
import xml.etree.ElementTree as ET

COMBAT = "EGGRUMBLE_SevenRoleCombat"
BOSS = "EGGRUMBLE_NeutralStoneGiant"
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
COMBAT_BLOB="66e666418b7c23d41f87faa5d61eb6e2770a463e"
AUTHOR_524_HEAD="f90875e14446ba86b1c668ba43efa37fbc74be20"
EXPECTED=30

def source_map_assertions(base:Path, receipt:Path):
    _,baseline=mapped(base)
    assert len(baseline)==EXPECTED
    assert set((COMBAT,BOSS,HOST,"EGGRUMBLE_FieldItemPickups",
                "EGGRUMBLE_BotActors","EGGRUMBLE_ScoreBalance",
                "EGGRUMBLE_RoundAttributeFence",
                "EGGRUMBLE_BossCreditPolicy")).issubset(baseline)
    r=json.loads(receipt.read_text(encoding="utf-8"))
    assert r["selected_source_count"]==EXPECTED
    assert r["source_changes_from_original30"]==[HOST]
    assert r["cumulative_changes_from_unpatched_author30"]==[HOST,BOSS]
    assert r["selected_source_sha256"]=={n:sha(p[1].read_bytes()) for n,p in baseline.items()}
    assert r["field_ridge_reversible"] is True
    assert r["same_boss_sha256"]==sha(baseline[BOSS][1].read_bytes())
    assert "CastleAccessRamp" in baseline[HOST][1].read_text(encoding="utf-8")
    assert "CentralRidgeRight" in baseline[HOST][1].read_text(encoding="utf-8")
    assert "rowZ[row+1]" in baseline[HOST][1].read_text(encoding="utf-8")
    assert "shockwaveClear" in baseline[BOSS][1].read_text(encoding="utf-8")
    original_combat=baseline[COMBAT][1]
    assert original_combat.name=="EGGRUMBLE_SevenRoleCombat.luau"
    assert git_blob(original_combat.read_bytes())==COMBAT_BLOB
    assert baseline[COMBAT][2]=="ModuleScript"
    return baseline

def prepare(base:Path,receipt:Path,author_tool:Path,outdir:Path):
    base=base.resolve(strict=True)
    receipt=receipt.resolve(strict=True)
    author_tool=author_tool.resolve(strict=True)
    outdir=outdir.resolve()
    assert outdir!=base.parent and not base.is_relative_to(outdir)
    assert author_tool.name=="patch_safe_warp.py"
    assert author_tool.parent.name=="v3_safe_warp_landing_20261116"
    source_map_assertions(base,receipt)
    data,baseline=mapped(base)
    original_combat=baseline[COMBAT][1]
    raw=original_combat.read_bytes()
    outdir.mkdir(parents=True,exist_ok=True)
    generated=outdir/"EGGRUMBLE_SevenRoleCombat.luau"
    assert generated!=original_combat.resolve()
    subprocess.run([sys.executable,str(author_tool),"--source",str(original_combat),
                    "--out",str(generated)],check=True)
    assert original_combat.read_bytes()==raw,"NEVER modify original author module"
    produced=generated.read_bytes()
    assert produced!=raw
    # Verify exact 3-hunk owner-intended behavior without reimplementing it.
    chosen=produced.decode("utf-8")
    assert chosen.count("local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean")==1
    assert chosen.count("safeMove(session,char,root,25)")==1
    assert chosen.count("safeMove(session,char,root,20)")==1
    assert chosen.count("GetPartBoundsInBox")==1
    assert chosen.count("TacticalBattlefield")>=1
    assert produced.count(b"local function safeMove(")==1
    # Source-select exactly existing Combat: Script names/classes and other 29 bytes stable.
    new=copy.deepcopy(data)
    for name,(chain,path,_) in baseline.items():
        node=new["tree"]
        for part in chain:node=node[part]
        desired=generated if name==COMBAT else path
        node["$path"]=os.path.relpath(desired,outdir).replace(os.sep,"/")
    new["name"]="EGGRUMBLE_ORIGINAL518_520_523_524_SINGLE_GAME30_PRIVATE_NOT_RC"
    project=outdir/"GQ521_ORIGINAL_518_520_523_524_PRIVATE30.project.json"
    project.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,selected=mapped(project)
    assert set(selected)==set(baseline) and len(selected)==EXPECTED
    diffs=[]
    for name,(chain,path,cls) in baseline.items():
        nchain,np,ncls=selected[name]
        assert nchain==chain and ncls==cls
        if path.read_bytes()!=np.read_bytes():diffs.append(name)
    assert diffs==[COMBAT],("unexpected shadow author source",diffs)
    assert all(sha(selected[n][1].read_bytes())==sha(baseline[n][1].read_bytes())
               for n in baseline if n!=COMBAT)
    for klass in ("Script","LocalScript","ModuleScript"):
        assert sum(z[2]==klass for z in selected.values())==sum(z[2]==klass for z in baseline.values()),"class count changed"
    evidence={
        "status":"PRIVATE_GQ521_OWNER518_520_523_PLUS_ORIGINAL524_SOURCE_SELECT_ONLY_NOT_RC",
        "owner_524_original_head":AUTHOR_524_HEAD,
        "owner_original_combat_git_blob":COMBAT_BLOB,
        "base_single30_source_count":EXPECTED,
        "selected_single30_source_count":EXPECTED,
        "source_diff_from_518_520_523_private30":[COMBAT],
        "cumulative_from_original517_private30":[HOST,BOSS,COMBAT],
        "unchanged_original517_scripts":27,
        "unchanged_518_520_523_private30_scripts":29,
        "original_518_boss_source_unchanged":True,
        "original_520_ridge_523_field_egg_host_unchanged":True,
        "source_sha256":{n:sha(x[1].read_bytes()) for n,x in selected.items()},
        "base_sha256":{n:sha(x[1].read_bytes()) for n,x in baseline.items()},
        "original_524_warp_source_sha256":sha(produced),
        "original_516_dot_combat_included":False,
        "original_516_dot_overlap":"REQUIRES_ORIGINAL_AUTHOR_516_COMBAT_RECONCILIATION_BEFORE_RC",
        "formal_rc_adopted":False,"claim_granted":False,
        "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
        "production_red":"#482 host and #512 COMBO Studio-only"}
    receipt_path=outdir/"GQ521_4_AUTHORS30_RECEIPT.json"
    receipt_path.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ521_ORIGINAL_524_WARP_ADDED_TO_518_520_523_SINGLE30_PASS 29/30 unchanged")

def verify(project:Path,place:Path):
    _,selected=mapped(project)
    assert len(selected)==EXPECTED
    receipt=project.parent/"GQ521_4_AUTHORS30_RECEIPT.json"
    r=json.loads(receipt.read_text(encoding="utf-8"))
    assert set(selected)==set(r["source_sha256"]) and r["unchanged_original517_scripts"]==27
    observed={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("ModuleScript","Script","LocalScript"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        body=props.findtext("ProtectedString[@name='Source']")
        if body is None:body=props.findtext("string[@name='Source']")
        assert name and body is not None and name not in observed
        observed[name]=(cls,body.replace("\r\n","\n"))
    assert set(observed)==set(selected)
    for name,(_,path,cls) in selected.items():
        assert observed[name]==(cls,path.read_text(encoding="utf-8").replace("\r\n","\n"))
        assert sha(path.read_bytes())==r["source_sha256"][name]
    r["private_place_bytes"]=place.stat().st_size
    r["private_place_sha256"]=sha(place.read_bytes())
    r["source_class_exact"]="30/30"
    receipt.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ521_ORIGINAL_518_520_523_524_REAL_ROJO_SOURCE_CLASS_30_OF_30_PASS",
          r["private_place_bytes"],r["private_place_sha256"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("prepare","verify"))
    for name in ("base","receipt","author-tool","outdir","project","place"):
        p.add_argument("--"+name,type=Path)
    a=p.parse_args()
    if a.mode=="prepare":
        assert all((a.base,a.receipt,a.author_tool,a.outdir))
        prepare(a.base,a.receipt,a.author_tool,a.outdir)
    else:
        assert a.project and a.place
        verify(a.project,a.place)

if __name__=="__main__":main()
