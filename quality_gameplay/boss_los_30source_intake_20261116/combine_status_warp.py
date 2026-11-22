#!/usr/bin/env python3
"""Fail-closed cross-owner ORIGINAL #516 DOT + #524 safeMove Combat source selector.

Input is already source-exact #521's 30-script 518+520+523+524 candidate.
This tool does not reimplement either gameplay mechanic: it takes the immutable
original #516 Combat overlay and transplants EXACT original #524 OLD->NEW hunk
constants, preserving #516 author's status callbacks byte-exact outside #524's
three movement hunks, plus adds #516's existing pure StatusTickFence module.
"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from intake import mapped, sha, git_blob

COMBAT="EGGRUMBLE_SevenRoleCombat"
FENCE="EGGRUMBLE_StatusTickFence"
BOSS="EGGRUMBLE_NeutralStoneGiant"
HOST="EGGRUMBLE_LobbyCastleModesPreview"
COMBAT_ORIGINAL_BLOB="66e666418b7c23d41f87faa5d61eb6e2770a463e"
STATUS_COMBAT_BLOB="34e6ec6e314eb36de657bd89a48bc1d07d74dcca"
STATUS_FENCE_BLOB="40bb3bc47c07fe27f82a28c97f82529d10788a8a"
AUTHOR_516_SHA="8f0275692c54874f823d66748d470fb849607df5"
AUTHOR_524_SHA="f90875e14446ba86b1c668ba43efa37fbc74be20"

def author_warp(path:Path):
    path=path.resolve(strict=True)
    assert path.name=="patch_safe_warp.py"
    spec=importlib.util.spec_from_file_location("gq521_actual_original524_patch",path)
    assert spec is not None and spec.loader is not None
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.EXPECTED_GIT_BLOB==COMBAT_ORIGINAL_BLOB
    return mod

def select(status:bytes,warp_module):
    # Verify source identity *before* applying the authors' unchanged patch.
    assert git_blob(status)==STATUS_COMBAT_BLOB,"#516 original authored Combat changed"
    value=status.decode("utf-8")
    originals=(warp_module.OLD,warp_module.OLD_NINJA,warp_module.OLD_ESPER)
    replacements=(warp_module.NEW,warp_module.NEW_NINJA,warp_module.NEW_ESPER)
    for old,new in zip(originals,replacements):
        assert value.count(old)==1,("original #524 anchor not unique inside #516",old[:50])
        assert value.count(new)==0,"#524 already applied or author overlap"
    assert value.count("StatusTickFence.canTick(")==1
    assert value.count('require(script.Parent:WaitForChild("EGGRUMBLE_StatusTickFence"))')==1
    applied=value
    for old,new in zip(originals,replacements):
        applied=applied.replace(old,new,1)
    assert applied.count("StatusTickFence.canTick(")==1
    assert applied.count("local function safeMove(")==1
    assert applied.count("GetPartBoundsInBox")==1
    assert applied.count("safeMove(session,char,root,25)")==1
    assert applied.count("safeMove(session,char,root,20)")==1
    assert applied.count("h:TakeDamage(tick)")==1
    # Prove #516 author code is unchanged except three original #524 hunks.
    reverted=applied
    for old,new in zip(reversed(originals),reversed(replacements)):
        assert reverted.count(new)==1
        reverted=reverted.replace(new,old,1)
    assert reverted==value,"status/collision source reconstruction not reversible"
    return applied.encode("utf-8")

def prepare(base:Path,prior_receipt:Path,original_combat:Path,author_status:Path,
            author_fence:Path,warp_tool:Path,outdir:Path):
    base=base.resolve(strict=True)
    outdir=outdir.resolve()
    assert outdir!=base.parent and not base.is_relative_to(outdir)
    prior=json.loads(prior_receipt.resolve(strict=True).read_text(encoding="utf-8"))
    data,old=mapped(base)
    assert len(old)==30 and FENCE not in old
    assert prior["selected_single30_source_count"]==30
    assert prior["source_diff_from_518_520_523_private30"]==[COMBAT]
    assert prior["source_sha256"]=={k:sha(v[1].read_bytes()) for k,v in old.items()}
    assert old[COMBAT][2]=="ModuleScript"
    assert old[BOSS][2]=="ModuleScript" and old[HOST][2]=="Script"
    assert "shockwaveClear" in old[BOSS][1].read_text(encoding="utf-8")
    assert "CentralRidgeRight" in old[HOST][1].read_text(encoding="utf-8")
    assert "rowZ[row+1]" in old[HOST][1].read_text(encoding="utf-8")
    original=original_combat.resolve(strict=True).read_bytes()
    status=author_status.resolve(strict=True).read_bytes()
    fence=author_fence.resolve(strict=True).read_bytes()
    assert git_blob(original)==COMBAT_ORIGINAL_BLOB,"original #482 Combat drift"
    assert git_blob(status)==STATUS_COMBAT_BLOB,"original #516 source drift"
    assert git_blob(fence)==STATUS_FENCE_BLOB,"original #516 policy drift"
    warp=author_warp(warp_tool)
    assert warp.patch(original)==old[COMBAT][1].read_bytes(),"#524 author Combat source differs"
    merged=select(status,warp)
    assert merged!=old[COMBAT][1].read_bytes()
    outdir.mkdir(parents=True,exist_ok=True)
    combat=outdir/"EGGRUMBLE_SevenRoleCombat.luau"
    combat.write_bytes(merged)
    generated=copy.deepcopy(data)
    assert generated["tree"]["ServerScriptService"].get("$className")=="ServerScriptService"
    generated["tree"]["ServerScriptService"][FENCE]={
        "$path":os.path.relpath(author_fence.resolve(strict=True),outdir).replace(os.sep,"/")}
    for name,(chain,p,_) in old.items():
        node=generated["tree"]
        for part in chain:node=node[part]
        chosen=combat if name==COMBAT else p
        node["$path"]=os.path.relpath(chosen,outdir).replace(os.sep,"/")
    generated["name"]="EGGRUMBLE_GQ521_AUTHOR516_STATUS_524_WARP_AND_518_520_523_PRIVATE31"
    project=outdir/"GQ521_ORIGINAL_516_518_520_523_524_PRIVATE31.project.json"
    project.write_text(json.dumps(generated,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,selected=mapped(project)
    assert len(selected)==31 and set(selected)==set(old)|{FENCE}
    assert selected[FENCE][2]=="ModuleScript"
    assert selected[FENCE][1].read_bytes()==fence
    for name,(chain,source,cls) in old.items():
        nchain,nsource,ncls=selected[name]
        assert nchain==chain and ncls==cls
        if name!=COMBAT:
            assert nsource.read_bytes()==source.read_bytes(),"unrelated author source modified: "+name
    assert len([n for n in old if selected[n][1].read_bytes()!=old[n][1].read_bytes()])==1
    evidence={
        "status":"PRIVATE_31_ONLY_NOT_FORMAL_RC",
        "owners_fixed":{"status_516":AUTHOR_516_SHA,"warp_524":AUTHOR_524_SHA},
        "underlying_original30":["#482","#484","#485","#487","#489","#512","#514","#517","#518","#520","#523"],
        "original_516_status_combat_blob":STATUS_COMBAT_BLOB,
        "original_516_policy_blob":STATUS_FENCE_BLOB,
        "original_524_patch_original_git_blob":COMBAT_ORIGINAL_BLOB,
        "single_combined_combat_module":COMBAT,
        "added_pure_author_policy_only":FENCE,
        "base_source_count":30,"selected_source_count":31,
        "other_29_original_scripts_identical":True,
        "status_author_516_hunks_unchanged_except_warp":True,
        "warp_author_524_three_hunks_reversible":True,
        "source_sha256":{name:sha(v[1].read_bytes()) for name,v in selected.items()},
        "base30_sha256":{name:sha(v[1].read_bytes()) for name,v in old.items()},
        "boss_original_518_kept":True,
        "ridge_original_520_kept":True,
        "field_egg_original_523_kept":True,
        "item_original_517_heal_kept":True,
        "official_rc_adopted":False,"claim_granted":False,
        "studio":"NOT_RUN","android":"NOT_RUN","owner":"NO_GO",
        "production_red":"#482 V3 Game and #512 Combo observer Studio-only"}
    (outdir/"GQ521_516_524_COMBINED31_RECEIPT.json").write_text(
        json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ521_ORIGINAL_516_DOT_AND_524_WARP_SAME_COMBAT_31_SELECTED_PASS 29/30 other preserved")

def verify(project:Path,place:Path):
    _,selected=mapped(project)
    assert len(selected)==31
    receipt=project.parent/"GQ521_516_524_COMBINED31_RECEIPT.json"
    r=json.loads(receipt.read_text(encoding="utf-8"))
    assert r["selected_source_count"]==31
    assert r["source_sha256"]=={k:sha(v[1].read_bytes()) for k,v in selected.items()}
    observed={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("ModuleScript","LocalScript","Script"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        assert name and source is not None and name not in observed
        observed[name]=(cls,source.replace("\r\n","\n"))
    assert set(observed)==set(selected)
    for name,(_,path,cls) in selected.items():
        assert observed[name]==(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")),("embedded author source/class drift",name)
    r["rojo_source_class_exact"]="31/31"
    r["private_place_bytes"]=place.stat().st_size
    r["private_place_sha256"]=sha(place.read_bytes())
    receipt.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ521_516_524_AND_518_520_523_PRIVATE31_TRUE_ROJO_EXACT_PASS",
        r["private_place_bytes"],r["private_place_sha256"])

def main():
    a=argparse.ArgumentParser()
    a.add_argument("mode",choices=("prepare","verify"))
    for arg in ("base","prior-receipt","original-combat","author-status","author-fence",
                "warp-tool","outdir","project","place"):
        a.add_argument("--"+arg,type=Path)
    o=a.parse_args()
    if o.mode=="prepare":
        args=(o.base,o.prior_receipt,o.original_combat,o.author_status,
              o.author_fence,o.warp_tool,o.outdir)
        assert all(args)
        prepare(*args)
    else:
        assert o.project and o.place
        verify(o.project,o.place)

if __name__=="__main__":
    main()
