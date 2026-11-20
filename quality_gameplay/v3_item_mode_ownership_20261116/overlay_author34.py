#!/usr/bin/env python3
"""Select only GQ525 host+item fixes into ORIGINAL #504 34-source composition.

This is not a second 34-source composer. First run unchanged original-author
#504 compose_neutral34.py and its preceding 26->27->28->30->32->28->34 chain.
Never write official RC, main or author repos. Fail closed on all source drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import patch_sources as own
from compose_author26 import load_heal

COUNT=34
HOST="EGGRUMBLE_LobbyCastleModesPreview"
ITEM="EGGRUMBLE_FieldItemPickups"
NEUTRAL="EGGRUMBLE_SwarmCombat"
EXPECTED_SERVER=27
EXPECTED_CLIENT=7
EXPECTED_SOURCE34_STATUS="PRIVATE_SOURCE_ONLY_NOT_AUTHENTICATED_RC"
RECEIPT_STATUS="GQ525_SOURCE_SELECTED_ORIGINAL34_NOT_OFFICIAL_RC"
REQUIRED_PRESERVE={
    "EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_BotActors",
    "EGGRUMBLE_BotPathRouter","EGGRUMBLE_RaidItemIntake",
    "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_CastleDefenseLive",
    "EGGRUMBLE_CastleDefensePolicy","EGGRUMBLE_NeutralStoneGiant",
    "EGGRUMBLE_BossSessionFence","EGGRUMBLE_NeutralSpawnPacing",
    "EGGRUMBLE_NeutralEncounterFairness","EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_HeroSilhouetteArt","EGGRUMBLE_FlagshipFieldArt",
    "EGGRUMBLE_EncounterReadabilityArt","EGGRUMBLE_RealHitAudio",
    "EGGRUMBLE_CombatFXBudget","EGGRUMBLE_CombatFXClarity",
    "EGGRUMBLE_GQ_ObjectiveCompass","EGGRUMBLE_MatchResultService",
    "EGGRUMBLE_ScoreBalance","EGGRUMBLE_ProceduralSkills",
}

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def read_sources(project:Path)->tuple[dict,dict]:
    data=json.loads(project.read_text(encoding="utf-8"))
    tree=data["tree"]
    sources={}
    def walk(obj,chain):
        if not isinstance(obj,dict):
            return
        if "$path" in obj:
            if set(obj)!={"$path"} or not chain or chain[-1] in sources:
                raise ValueError("RED: duplicate/unsafe original 34 source node")
            name=chain[-1]
            path=(project.parent/obj["$path"]).resolve(strict=True)
            cls="Script" if path.name.endswith(".server.luau") else (
                "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
            sources[name]=(chain,path,cls)
        else:
            for name,value in obj.items():
                if not name.startswith("$"):
                    walk(value,chain+(name,))
    walk(tree,())
    if len(sources)!=COUNT or not REQUIRED_PRESERVE.issubset(sources):
        raise ValueError("RED: original 34 scripts or eight domains missing")
    if len(tree["ServerScriptService"])-1!=EXPECTED_SERVER:
        raise ValueError("RED: original 34 server count drift")
    if len(tree["StarterPlayer"]["StarterPlayerScripts"])-1!=EXPECTED_CLIENT:
        raise ValueError("RED: original 34 client count drift")
    if sources[HOST][0] != ("ServerScriptService",HOST) or sources[HOST][2]!="Script":
        raise ValueError("RED: original host script identity drift")
    if sources[ITEM][0] != ("ServerScriptService",ITEM) or sources[ITEM][2]!="ModuleScript":
        raise ValueError("RED: original item script identity drift")
    return data,sources

def prepare(project:Path,receipt_file:Path,item_author:Path,heal_patch:Path,
            out:Path,out_receipt:Path)->None:
    project=project.resolve(strict=True)
    receipt_file=receipt_file.resolve(strict=True)
    item_author=item_author.resolve(strict=True)
    out=out.resolve()
    out_receipt=out_receipt.resolve()
    if (out.parent!=project.parent or out==project or out.exists()
            or out_receipt.exists()):
        raise ValueError("RED: prepare only fresh adjacent private author34 overlay")
    base,found=read_sources(project)
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    if (receipt.get("status")!=EXPECTED_SOURCE34_STATUS
            or receipt.get("total_source_count")!=COUNT
            or receipt.get("unchanged_previous_count")!=31
            or receipt.get("neutral_swarm_private_overlay") is not True
            or receipt.get("official_rc_integrated") is not False
            or set(receipt.get("source_sha256",{}))!=set(found)):
        raise ValueError("RED: not exact original #504 34 source receipt")
    for name,(_,source,_) in found.items():
        if receipt["source_sha256"][name]!=digest(source.read_bytes()):
            raise ValueError("RED: original #504 author receipt source changed "+name)
    host=found[HOST][1].read_text(encoding="utf-8")
    # Must retain exact original unique Game authority incl defense+neutral+ART.
    for token in ("CastleAccessRamp","CastleDefense.start(session)",
                  "session.castleDefenseStop()","EGGRUMBLE_RaidItemIntake",
                  "EGGRUMBLE_NeutralStoneGiant","EGGRUMBLE_SevenRoleCombat",
                  "sessions[mode]=session"):
        if token not in host:
            raise ValueError("RED: original 34 host lost required author behavior "+token)
    if "EGGRUMBLE_NeutralSpawnPacing" not in found[NEUTRAL][1].read_text(encoding="utf-8"):
        raise ValueError("RED: original #494 neutral pacing not linked")
    if "EGGRUMBLE_NeutralEncounterFairness" not in found[NEUTRAL][1].read_text(encoding="utf-8"):
        raise ValueError("RED: original #501 neutral fairness not linked")
    raw=item_author.read_bytes()
    if own.git_blob_sha(raw)!=own.ORIGINAL_ITEM_BLOB:
        raise ValueError("RED: not exact original #489 item")
    heal=load_heal(heal_patch)
    healed=heal.patch(raw.decode("utf-8"))
    new_host,new_item=own.patch_sources(host,healed)
    if (new_host.replace(own.HOST_INSERT,"",1)!=host or
            new_item.replace(own.ITEM_INSERT,"",1)!=healed or
            healed.replace(heal.HELPER,"",1).replace(heal.CALL,"",1)!=raw.decode("utf-8")):
        raise ValueError("RED: source-selective 2-site promise broken")
    overlay_dir=out.parent/"gq525_original34_source_selected"
    if overlay_dir.exists():
        raise ValueError("RED: refuse overlay directory overwrite")
    overlay_dir.mkdir()
    overlay_paths={HOST:overlay_dir/own.HOST_NAME,ITEM:overlay_dir/own.ITEM_NAME}
    overlay_paths[HOST].write_text(new_host,encoding="utf-8")
    overlay_paths[ITEM].write_text(new_item,encoding="utf-8")
    data=json.loads(project.read_text(encoding="utf-8"))
    data["name"]="EGGRUMBLE_GQ525_ORIGINAL34_PRIVATE_NOT_OFFICIAL_RC"
    for name,path in overlay_paths.items():
        data["tree"]["ServerScriptService"][name]["$path"]=os.path.relpath(
            path,out.parent).replace(os.sep,"/")
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,final=read_sources(out)
    if set(final)!=set(found):
        raise ValueError("RED: lost original 34 script identities")
    for name,(_,source,klass) in found.items():
        current=final[name]
        if current[2]!=klass:
            raise ValueError("RED: original class mutated "+name)
        if name not in overlay_paths and (current[1]!=source or
                current[1].read_bytes()!=source.read_bytes()):
            raise ValueError("RED: unowned original source changed "+name)
    record={
       "status":RECEIPT_STATUS,
       "source_count":COUNT,
       "unchanged_owner_sources":COUNT-2,
       "source_selected_overlays":[HOST,ITEM],
       "source34_receipt_sha256":digest(receipt_file.read_bytes()),
       "source34_project_sha256":digest(project.read_bytes()),
       "original_34_sha256":{name:digest(source.read_bytes())
              for name,(_,source,_) in sorted(found.items())},
       "source_sha256":{name:digest(source.read_bytes())
              for name,(_,source,_) in sorted(final.items())},
       "source_owners":{
         "34_composer":"#504@385d3242cbc8d0a3008ee818d8dc30040170fce6",
         "26_composer":"#484@6b52eaf1f2725496277998fe0c5532b7a8fcaab5",
         "game":"#482@fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
         "item":"#489@03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd",
         "heal":"#517@c8a324ad7bb40648d82a5828cbf54e217585fefd"},
       "native_compile":"NOT_YET","rojo_source_exact":"NOT_YET",
       "official_rc_adoption":0,
       "studio":"NOT_TESTED","android":"NOT_TESTED",
       "owner":"NO_GO",
       "rollback":"revert the exactly two source-selection nodes to original #504 34 receipt",
    }
    out_receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ525_ORIGINAL34_32_OWNER_SOURCES_UNCHANGED_2_PATCHED_PASS",COUNT)

def verify(project:Path,receipt_file:Path,place:Path,compiler:Path)->None:
    project=project.resolve(strict=True)
    place=place.resolve(strict=True)
    _,found=read_sources(project)
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    if (receipt.get("status")!=RECEIPT_STATUS or
            receipt.get("source_count")!=COUNT or
            receipt.get("unchanged_owner_sources")!=COUNT-2 or
            set(receipt.get("source_sha256",{}))!=set(found) or
            receipt.get("official_rc_adoption")!=0):
        raise ValueError("RED: source34 approval record drift")
    actual={}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=node.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):
            continue
        props=node.find("Properties")
        if props is None:
            continue
        name=props.findtext("string[@name='Name']")
        text=props.findtext("ProtectedString[@name='Source']")
        if text is None:
            text=props.findtext("string[@name='Source']")
        if not name or text is None or name in actual:
            raise ValueError("RED: duplicate or malformed source/class in private Place")
        actual[name]=(cls,text.replace("\r\n","\n"))
    if set(actual)!=set(found) or len(actual)!=COUNT:
        raise ValueError("RED: actual Rojo Place has missing/extra scripts")
    for name,(_,source,cls) in sorted(found.items()):
        if actual[name]!=(cls,source.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED: actual Rojo source/class bytes differ "+name)
        if digest(source.read_bytes())!=receipt["source_sha256"][name]:
            raise ValueError("RED: source hash not equal to receipt "+name)
        subprocess.run([str(compiler),str(source)],check=True,stdout=subprocess.DEVNULL)
    receipt["native_compile"]="34/34"
    receipt["rojo_source_exact"]="34/34"
    receipt["private_place_bytes"]=place.stat().st_size
    receipt["private_place_sha256"]=digest(place.read_bytes())
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ525_ORIGINAL34_NATIVE_AND_ROJO_SOURCE_EXACT_34_OF_34_PASS",
          receipt["private_place_bytes"],receipt["private_place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("prepare","verify"))
    for field in ("project","receipt_file","item_author","heal_patch","out","out_receipt","place","compiler"):
        p.add_argument("--"+field.replace("_","-"),type=Path)
    o=p.parse_args()
    if o.mode=="prepare":
        assert all((o.project,o.receipt_file,o.item_author,o.heal_patch,o.out,o.out_receipt))
        prepare(o.project,o.receipt_file,o.item_author,o.heal_patch,o.out,o.out_receipt)
    else:
        assert all((o.out,o.out_receipt,o.place,o.compiler))
        verify(o.out,o.out_receipt,o.place,o.compiler)
