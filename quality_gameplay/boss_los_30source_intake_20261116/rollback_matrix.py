#!/usr/bin/env python3
"""32-case ORIGINAL source-author rollback matrix for five independent #521 repairs.

Only PRIVATE manifests/Place evidence. It builds NO gameplay Luau logic. Every
source is selected from the original #517 baseline, the current #521 selected
31-source place, or reverted with exact ORIGINAL #520/#523/#524 author hunks.
It deliberately does not own Builder, ITEM, neutral pacing, AI or ART fixes.
"""
from __future__ import annotations
import argparse
import copy
from itertools import product
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from intake import mapped,sha,git_blob,BOSS_NAME,BOSS_BLOB
from combine_status_warp import COMBAT,HOST,FENCE,COMBAT_ORIGINAL_BLOB,STATUS_COMBAT_BLOB,STATUS_FENCE_BLOB

FIXES=("status516","boss518","ridge520","eggs523","warp524")
NAMES=30
STATUS_HELPER=FENCE

def load_owner_module(path:Path,name:str):
    path=path.resolve(strict=True)
    assert path.name in ("patch_ridge.py","patch_field_eggs.py","patch_safe_warp.py")
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    x=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(x)
    return x

def once_replace(source:str,old:str,new:str,label:str)->str:
    if source.count(old)!=1:
        raise ValueError(f"RED {label}: expected exact unique author hunk, got {source.count(old)}")
    if new and new in source:
        raise ValueError(f"RED {label}: attempted double-apply or mutated source")
    output=source.replace(old,new,1)
    assert output!=source
    return output

def author_reverts(current:dict[str,bytes],original:dict[str,bytes],
                   status_bytes:bytes,helper_bytes:bytes,ridge,egg,warp):
    """Verify the three owners' actual source hunk reversibility before any toggle."""
    base_combat=original[COMBAT].decode("utf-8")
    assert git_blob(original[COMBAT])==COMBAT_ORIGINAL_BLOB
    assert git_blob(original[BOSS_NAME])==BOSS_BLOB
    assert git_blob(status_bytes)==STATUS_COMBAT_BLOB
    assert git_blob(helper_bytes)==STATUS_FENCE_BLOB
    assert warp.patch(original[COMBAT])!=original[COMBAT]
    assert current[COMBAT]!=original[COMBAT]
    combat=current[COMBAT].decode("utf-8")
    for prev,new in reversed(tuple(zip(
         (warp.OLD,warp.OLD_NINJA,warp.OLD_ESPER),
         (warp.NEW,warp.NEW_NINJA,warp.NEW_ESPER)))):
        combat=once_replace(combat,new,prev,"#524 reverse safeMove")
    assert combat.encode("utf-8")==status_bytes,"RED: cannot isolate #516 original status"
    assert warp.patch(original[COMBAT])==warp.patch(base_combat.encode("utf-8"))
    host=current[HOST].decode("utf-8")
    egg_off=once_replace(host,egg.REPLACEMENT_LINE,egg.ORIGINAL_LINE,
                         "#523 egg Z expression")
    egg_off=once_replace(egg_off,egg.ROWS_LINE,"","#523 egg rows")
    ridge_off=once_replace(host,ridge.NEW,ridge.OLD,"#520 single CentralRidge")
    all_off=once_replace(egg_off,ridge.NEW,ridge.OLD,"#520 from egg-off")
    alt_off=once_replace(ridge_off,egg.REPLACEMENT_LINE,egg.ORIGINAL_LINE,
                         "#523 from ridge-off")
    alt_off=once_replace(alt_off,egg.ROWS_LINE,"","#523 from ridge-off")
    assert all_off==alt_off==original[HOST].decode("utf-8"),"RED original #484 host not restored"
    assert "CastleAccessRamp" in all_off,"#484 original ramp must always survive"
    assert "CentralRidgeRight" not in all_off
    assert egg.ROWS_LINE not in all_off
    assert "shockwaveClear" in current[BOSS_NAME].decode("utf-8")
    return {"host_all":host,"host_egg_off":egg_off,
            "host_ridge_off":ridge_off,"host_none":all_off,
            "combat_both":current[COMBAT],"combat_status_only":status_bytes,
            "combat_warp_only":warp.patch(original[COMBAT]),
            "combat_none":original[COMBAT]}

def prepare(original_project:Path,current_project:Path,current_receipt:Path,
            owner_status:Path,owner_helper:Path,ridge_patch:Path,egg_patch:Path,
            warp_patch:Path,outdir:Path):
    original_project=original_project.resolve(strict=True)
    current_project=current_project.resolve(strict=True)
    outdir=outdir.resolve()
    assert outdir not in (original_project.parent,current_project.parent)
    assert not original_project.is_relative_to(outdir)
    assert not current_project.is_relative_to(outdir)
    data_orig,before=mapped(original_project)
    data_cur,after=mapped(current_project)
    assert len(before)==NAMES and len(after)==NAMES+1
    assert set(after)==set(before)|{FENCE}
    assert before[HOST][2]==after[HOST][2]=="Script"
    assert before[COMBAT][2]==after[COMBAT][2]=="ModuleScript"
    assert before[BOSS_NAME][2]==after[BOSS_NAME][2]=="ModuleScript"
    assert after[FENCE][2]=="ModuleScript"
    record=json.loads(current_receipt.resolve(strict=True).read_text(encoding="utf-8"))
    assert record["selected_source_count"]==31
    assert record["source_sha256"]=={n:sha(t[1].read_bytes()) for n,t in after.items()}
    for name,(chain,p,cls) in before.items():
        assert chain==after[name][0] and cls==after[name][2],f"RED source class/location {name}"
    assert {n for n in before if before[n][1].read_bytes()!=after[n][1].read_bytes()}=={
        HOST,COMBAT,BOSS_NAME},"RED: unexpected original author source changed"
    originals={n:p.read_bytes() for n,(_,p,_) in before.items()}
    currents={n:p.read_bytes() for n,(_,p,_) in after.items()}
    status=owner_status.resolve(strict=True).read_bytes()
    helper=owner_helper.resolve(strict=True).read_bytes()
    assert helper==currents[FENCE],"original #516 policy source drift"
    ridge=load_owner_module(ridge_patch,"gq521_owner520_rollback")
    egg=load_owner_module(egg_patch,"gq521_owner523_rollback")
    warp=load_owner_module(warp_patch,"gq521_owner524_rollback")
    assert ridge.ORIGINAL_GIT_BLOB=="7162b209bf67b74a71553217f3f744e072a0365d"
    assert egg.ORIGINAL_HOST_BLOB==ridge.ORIGINAL_GIT_BLOB
    assert warp.EXPECTED_GIT_BLOB==COMBAT_ORIGINAL_BLOB
    choices=author_reverts(currents,originals,status,helper,ridge,egg,warp)
    outdir.mkdir(parents=True,exist_ok=True)
    results=[]
    receipt_files=[]
    for bits in product((False,True),repeat=len(FIXES)):
        enabled=dict(zip(FIXES,bits))
        code="".join("1" if b else "0" for b in bits)
        vdir=outdir/code
        vdir.mkdir(exist_ok=True)
        want=dict(originals)
        if enabled["boss518"]:
            want[BOSS_NAME]=currents[BOSS_NAME]
        if enabled["ridge520"] and enabled["eggs523"]:
            want[HOST]=choices["host_all"].encode("utf-8")
        elif enabled["ridge520"]:
            want[HOST]=choices["host_egg_off"].encode("utf-8")
        elif enabled["eggs523"]:
            want[HOST]=choices["host_ridge_off"].encode("utf-8")
        if enabled["status516"] and enabled["warp524"]:
            want[COMBAT]=choices["combat_both"]
        elif enabled["status516"]:
            want[COMBAT]=choices["combat_status_only"]
        elif enabled["warp524"]:
            want[COMBAT]=choices["combat_warp_only"]
        if enabled["status516"]:
            want[FENCE]=helper
        assert len(want)==NAMES+int(enabled["status516"])
        if code=="00000":
            assert all(want[n]==originals[n] for n in originals)
        if code=="11111":
            assert all(want[n]==currents[n] for n in after)
        # Restore by selecting the owner's original source, never reimplementing
        # the underlying battle/role/item/AI/ART/score modules.
        chosen=copy.deepcopy(data_orig)
        for name,(chain,p,cls) in before.items():
            node=chosen["tree"]
            for part in chain:node=node[part]
            if want[name]==originals[name]:
                use=p
            elif want[name]==currents.get(name,b""):
                use=after[name][1]
            else:
                filename=p.name
                use=vdir/filename
                use.write_bytes(want[name])
            node["$path"]=os.path.relpath(use,vdir).replace(os.sep,"/")
        if enabled["status516"]:
            node=chosen["tree"]["ServerScriptService"]
            assert FENCE not in node
            node[FENCE]={"$path":os.path.relpath(after[FENCE][1],vdir).replace(os.sep,"/")}
        chosen["name"]="GQ521_ORIGINAL_OWNER_ROLLBACK_"+code+"_PRIVATE_NO_OFFICIAL_RC"
        project=vdir/f"ROLLBACK_{code}.project.json"
        project.write_text(json.dumps(chosen,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        _,manifest=mapped(project)
        assert len(manifest)==len(want) and set(manifest)==set(want)
        for n,(_,p,cls) in manifest.items():
            assert p.read_bytes()==want[n],"RED wrong selected source "+n
            if n in before:assert cls==before[n][2] and manifest[n][0]==before[n][0]
            if n==FENCE:assert cls=="ModuleScript"
        assert sum(n==COMBAT for n in manifest)==1
        assert sum(n==HOST for n in manifest)==1
        assert sum(n==BOSS_NAME for n in manifest)==1
        expected_diff={n for n in before if want[n]!=originals[n]}
        assert expected_diff==({
            HOST} if enabled["ridge520"] or enabled["eggs523"] else set())|({
            BOSS_NAME} if enabled["boss518"] else set())|({
            COMBAT} if enabled["status516"] or enabled["warp524"] else set())
        assert all(want[n]==originals[n] for n in before if n not in (HOST,COMBAT,BOSS_NAME))
        row={"code":code,"enabled":enabled,"project":str(project),
             "source_count":len(manifest),"changed_existing":sorted(expected_diff),
             "source_sha256":{n:sha(want[n]) for n in sorted(want)},
             "original_author_script_changes":0,"official_rc_adopted":False}
        results.append(row)
    assert len(results)==32 and len({r["code"] for r in results})==32
    assert sum(r["source_count"]==31 for r in results)==16
    assert sum(r["source_count"]==30 for r in results)==16
    assert results[0]["code"]=="00000" and results[-1]["code"]=="11111"
    evidence={"scope":"GQ521_FIVE_OWNER_FIXES_32_COMBINATION_PRIVATE_ONLY",
              "fixed_order":FIXES,"private_cases":results,"total":len(results),
              "no_new_gameplay_Luau":True,"five_owner_rollbacks_fail_closed":True,
              "original_source_unchanged_count":NAMES-3,
              "official_rc_head":"d2f3ed1a47558fdaf07be0181c83c698bdb2ce34",
              "official_rc_adopted":0,"studio":"NOT_RUN","android":"NOT_RUN",
              "production_red":"original #482 Game and #512 COMBO Studio-only"}
    (outdir/"MATRIX_RECEIPT.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ521_ORIGINAL_FIVE_AUTHOR_ROLLBACK_SOURCE_MATRIX_32_OF_32_PASS 16x30+16x31")

def verify(outdir:Path):
    evidence_path=outdir/"MATRIX_RECEIPT.json"
    doc=json.loads(evidence_path.read_text(encoding="utf-8"))
    assert doc["total"]==32 and len(doc["private_cases"])==32
    metrics=[]
    for row in doc["private_cases"]:
        code=row["code"]
        project=Path(row["project"])
        _,manifest=mapped(project)
        assert len(manifest)==row["source_count"]==30+int(row["enabled"]["status516"])
        assert {n:sha(v[1].read_bytes()) for n,v in manifest.items()}==row["source_sha256"]
        place=outdir/code/f"ROLLBACK_{code}.rbxlx"
        actual={}
        for item in ET.parse(place).getroot().iter("Item"):
            cls=item.get("class")
            if cls not in ("Script","ModuleScript","LocalScript"):continue
            props=item.find("Properties")
            assert props is not None
            name=props.findtext("string[@name='Name']")
            source=props.findtext("ProtectedString[@name='Source']")
            if source is None:source=props.findtext("string[@name='Source']")
            assert name and source is not None and name not in actual
            actual[name]=(cls,source.replace("\r\n","\n"))
        assert set(actual)==set(manifest),f"Rojo script authority mismatch {code}"
        for n,(_,p,cls) in manifest.items():
            assert actual[n]==(cls,p.read_text(encoding="utf-8").replace("\r\n","\n")),("source readback drift",code,n)
        row["actual_rojo_source_class_exact"]=f"{len(manifest)}/{len(manifest)}"
        row["private_place_bytes"]=place.stat().st_size
        row["private_place_sha256"]=sha(place.read_bytes())
        metrics.append(row["private_place_bytes"])
    doc["tested_real_rojo_cases"]=len(metrics)
    doc["min_private_place_bytes"]=min(metrics)
    doc["max_private_place_bytes"]=max(metrics)
    evidence_path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ521_ORIGINAL_FIVE_AUTHOR_ROLLBACK_NATIVE_ROJO_32_PRIVATE_PLACES_SOURCE_CLASS_EXACT_PASS",
          min(metrics),max(metrics))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("prepare","verify"))
    for k in ("original-project","current-project","current-receipt","owner-status","owner-helper",
              "ridge-patch","egg-patch","warp-patch","outdir"):
        ap.add_argument("--"+k,type=Path)
    a=ap.parse_args()
    if a.mode=="prepare":
        keys=("original_project","current_project","current_receipt","owner_status",
              "owner_helper","ridge_patch","egg_patch","warp_patch","outdir")
        assert all(getattr(a,k) for k in keys)
        prepare(*(getattr(a,k) for k in keys))
    else:
        assert a.outdir
        verify(a.outdir)

if __name__=="__main__":
    main()
