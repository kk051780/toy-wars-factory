#!/usr/bin/env python3
"""Reuse #520 actual original34 private Place (with original #504/#500/#501 authors),
select ONLY GQ523 source-pinned FIELD egg row modification onto the already-ridge-fixed host.
No source modification under original author paths. No formal #220 RC writer actions.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from patch_field_eggs import patch, ROWS_LINE, ORIGINAL_LINE, REPLACEMENT_LINE

PARENT_SHA="2005312ed2185758848bf07c770c821275ca2bcc565c5f2b681184ee3f57bc42"
AUTHOR_520_HEAD="ce3781f7bca359ba898fe326997c416b6e981aff"
HOST="EGGRUMBLE_LobbyCastleModesPreview"
COUNT=34
NEEDED={
 HOST,"EGGRUMBLE_CastleMatchRules","EGGRUMBLE_SevenRoleCombat",
 "EGGRUMBLE_NeutralStoneGiant","EGGRUMBLE_SwarmCombat",
 "EGGRUMBLE_CastleDefenseLive","EGGRUMBLE_CastleDefensePolicy",
 "EGGRUMBLE_NeutralSpawnPacing","EGGRUMBLE_NeutralEncounterFairness",
 "EGGRUMBLE_BotActors","EGGRUMBLE_RaidItemIntake",
 "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_ScoreBalance",
 "EGGRUMBLE_RealHitAudio","EGGRUMBLE_CombatFXClarity",
 "EGGRUMBLE_GQ_ObjectiveCompass"
}
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def read_place(place:Path)->dict:
    r={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        assert name and src is not None and name not in r
        assert re.fullmatch(r"EGGRUMBLE_[A-Za-z0-9_]+",name),name
        r[name]=(cls,src.replace(chr(13)+chr(10),chr(10)))
    assert len(r)==COUNT and NEEDED.issubset(r),(len(r),sorted(NEEDED-set(r)))
    return r

def expected_project(original:dict,sources:dict)->dict:
    project=copy.deepcopy(original)
    seen=set()
    def walk(node,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            assert set(node)=={"$path"}
            name=chain[-1]
            assert name in sources and name not in seen,name
            kind=sources[name][0]
            ext=(".server.luau" if kind=="Script" else
                 ".client.luau" if kind=="LocalScript" else ".luau")
            node["$path"]="scripts/"+name+ext
            seen.add(name)
        else:
            for k,v in node.items():
                if not k.startswith("$"):walk(v,chain+(k,))
    walk(project["tree"])
    assert seen==set(sources) and len(seen)==COUNT
    project["name"]="GQ523_FIELD_EGGS_IN_REAL_GQ520_ORIGINAL34_UNPUBLISHED_NO_RC"
    return project

def change_only_eggs(host:str)->str:
    assert host.count("CentralRidgeRight")==1, "original #520 ridge must already be present"
    assert "CastleAccessRamp" in host, "original #484 ramp missing"
    assert "CastleDefense.start(session)" in host and "session.castleDefenseStop()" in host,"original #500 live defense lost"
    assert host.count(ORIGINAL_LINE)==1, "original #482 field rows missing"
    changed=patch(host)
    assert changed.replace(ROWS_LINE,"",1).replace(REPLACEMENT_LINE,ORIGINAL_LINE,1)==host
    for marker in ("CentralRidgeRight","CastleAccessRamp","CastleDefense.start(session)",
                   "session.castleDefenseStop()","EGGRUMBLE_RaidItemIntake","EGGRUMBLE_NeutralStoneGiant"):
        assert changed.count(marker)==host.count(marker),(marker,"changed original author function")
    return changed

def prepare(original_place:Path,original_project:Path,original_receipt:Path,out:Path):
    original_place=original_place.resolve(strict=True)
    original_project=original_project.resolve(strict=True)
    original_receipt=original_receipt.resolve(strict=True)
    out=out.resolve()
    for p in (original_place,original_project,original_receipt):
        assert not p.is_relative_to(out) and p!=out
    assert sha(original_place.read_bytes())==PARENT_SHA,"#520 source exact 34 private Place drift"
    before=read_place(original_place)
    record=json.loads(original_receipt.read_text(encoding="utf-8"))
    assert record["status"]=="PRIVATE34_SOURCE_EXACT_NOT_OFFICIAL_RC"
    assert record["source_count"]==COUNT and record["unchanged_owner_sources"]==33
    assert len(record["source_sha256"])==COUNT and set(record["source_sha256"])==set(before)
    for name,(_,code) in before.items():
        assert sha(code.encode("utf-8"))==record["source_sha256"][name],("parent receipt mismatch",name)
    assert record["original_host_blob"]=="7162b209bf67b74a71553217f3f744e072a0365d"
    assert '{x=0,z=470,kind="SHIELD"}' in before["EGGRUMBLE_RaidItemIntake"][1]
    new_code=change_only_eggs(before[HOST][1])
    after=dict(before);after[HOST]=(before[HOST][0],new_code)
    modified=[name for name in before if before[name]!=after[name]]
    assert modified==[HOST] and sum(before[k]==after[k] for k in before)==33
    assert before["EGGRUMBLE_NeutralStoneGiant"]==after["EGGRUMBLE_NeutralStoneGiant"]
    assert before["EGGRUMBLE_FieldItemPickups"]==after["EGGRUMBLE_FieldItemPickups"]
    assert before["EGGRUMBLE_SwarmCombat"]==after["EGGRUMBLE_SwarmCombat"]
    out.mkdir(parents=True,exist_ok=True)
    scripts=out/"scripts";scripts.mkdir(exist_ok=True)
    manifest=expected_project(json.loads(original_project.read_text(encoding="utf-8")),after)
    for name,(cls,code) in after.items():
        ext=(".server.luau" if cls=="Script" else
             ".client.luau" if cls=="LocalScript" else ".luau")
        (scripts/(name+ext)).write_text(code,encoding="utf-8")
    project=out/"GQ523_FIELD_EGGS_ORIGINAL34.project.json"
    project.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt={
        "status":"PRIVATE34_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "source_count":34,"unchanged_parent_source_count":33,
        "changed_existing_source_only":[HOST],
        "original_520_parent_head":AUTHOR_520_HEAD,"original_520_parent_place_sha256":PARENT_SHA,
        "original_504_castle_neutral_audio_fx_source_kept":True,
        "original_500_castle_defense_source_kept":True,
        "original_494_501_neutral_pacing_fairness_source_kept":True,
        "original_485_art_and_487_score_source_kept":True,
        "original_496_objective_and_503_fx_source_kept":True,
        "original_482_7roles_field_castle_item_lobby_source_kept":True,
        "source_sha256_before":record["source_sha256"],
        "source_sha256_after":{name:sha(code.encode("utf-8")) for name,(_,code) in sorted(after.items())},
        "old_source_AABB_collisions":{"TEAM":8,"BATTLE_ROYALE":4},
        "new_source_AABB_collisions":{"TEAM":0,"BATTLE_ROYALE":0},
        "formal_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
        "rollback":"source-select original #520 host from private34; do not remove its ridge or #500 castle additions"
    }
    (out/"GQ523_FIELD_EGGS_ORIGINAL34_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("GQ523_IN_ORIGINAL_520_AUTHOR34_SINGLE_EGG_HUNK_33_OF_34_UNCHANGED_PASS")

def verify(project:Path,place:Path):
    project=project.resolve(strict=True);place=place.resolve(strict=True)
    receipt_file=project.parent/"GQ523_FIELD_EGGS_ORIGINAL34_RECEIPT.json"
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    observed=read_place(place)
    assert len(observed)==COUNT and set(observed)==set(receipt["source_sha256_after"])
    original=json.loads(project.read_text(encoding="utf-8"))
    mapping=set()
    def visit(node,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            name=chain[-1]
            assert name in observed and name not in mapping
            file=(project.parent/node["$path"]).resolve(strict=True)
            assert file.is_relative_to(project.parent)
            cls,code=observed[name]
            ext=(".server.luau" if cls=="Script" else
                 ".client.luau" if cls=="LocalScript" else ".luau")
            assert file.name==name+ext
            assert sha(code.encode("utf-8"))==sha(file.read_bytes())==receipt["source_sha256_after"][name],name
            mapping.add(name)
        else:
            for k,v in node.items():
                if not k.startswith("$"):visit(v,chain+(k,))
    visit(original["tree"])
    assert mapping==set(observed)
    for name in mapping-{HOST}:
        assert receipt["source_sha256_before"][name]==receipt["source_sha256_after"][name],name
    receipt["private_place_bytes"]=place.stat().st_size
    receipt["private_place_sha256"]=sha(place.read_bytes())
    receipt["native_source_exact"]="34/34"
    receipt["rojo_source_class_exact"]="34/34"
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("GQ523_FIELD_EGGS_IN_GQ520_ORIGINAL34_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",
          receipt["private_place_bytes"],receipt["private_place_sha256"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["prepare","verify"])
    ap.add_argument("--original-place",type=Path)
    ap.add_argument("--original-project",type=Path)
    ap.add_argument("--original-receipt",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--project",type=Path)
    ap.add_argument("--place",type=Path)
    a=ap.parse_args()
    if a.mode=="prepare":
        assert all((a.original_place,a.original_project,a.original_receipt,a.out))
        prepare(a.original_place,a.original_project,a.original_receipt,a.out)
    else:
        assert a.project and a.place
        verify(a.project,a.place)
if __name__=="__main__":
    main()
