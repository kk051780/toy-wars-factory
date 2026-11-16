#!/usr/bin/env python3
"""Source-selectively layer GQ520 ridge onto #504's ORIGINAL 34-source candidate.

This is NOT a second 34-source composer; run the exact pre-existing #504 original
composer first. The only authored delta here is one TEAM CentralRidge one-block
terrain replacement. Refuse source drift and all official RC writes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from augment_current26 import scripts, sha_file, HOST
from patch_ridge import OLD, NEW, ORIGINAL_GIT_BLOB, git_blob, patch_author_host

COUNT=34
BASENAME="GQ520_FIELD_ITEM_ON_AUTHOR34_NOT_RC"
RECEIPT="GQ520_PRIVATE34_RECEIPT.json"
PRIVATE_HOST="GQ520_RIDGE34_OnlyHost.server.luau"

def patch34(base_host: str, original_host: str, item: str) -> str:
    """Preserve all #504 existing host additions incl #484 ramp + #500 defense."""
    source_probe=patch_author_host(original_host,item)
    if source_probe.count(NEW)!=1 or base_host.count(OLD)!=1:
        raise ValueError("RED: original TEAM CentralRidge already patched or drifted")
    if git_blob(original_host)!=ORIGINAL_GIT_BLOB:
        raise ValueError("RED: #482 author host immutable blob mismatch")
    for token in (
        "CastleAccessRamp",
        "CastleDefense.start(session)",
        "session.castleDefenseStop()",
        "EGGRUMBLE_RaidItemIntake",
        "EGGRUMBLE_NeutralStoneGiant",
        "EGGRUMBLE_SevenRoleCombat",
    ):
        if token not in base_host:
            raise ValueError("RED: original #504 composite lost required authority "+token)
    modified=base_host.replace(OLD,NEW)
    if modified.replace(NEW,OLD)!=base_host:
        raise ValueError("RED: host change not strictly reversible")
    return modified

def prepare(project: Path, receipt_file: Path, original_host: Path, item: Path,
            out:Path) -> Path:
    project=project.resolve(strict=True)
    receipt_file=receipt_file.resolve(strict=True)
    original_host=original_host.resolve(strict=True)
    item=item.resolve(strict=True)
    out=out.resolve()
    if (out.parent!=project.parent or out==project or out.exists()
        or out.parent==original_host.parent):
        raise ValueError("RED: can only create fresh private 34 project adjacent to original")
    manifest, mapped=scripts(project, COUNT)
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    if (receipt.get("status")!="PRIVATE_SOURCE_ONLY_NOT_AUTHENTICATED_RC"
        or receipt.get("total_source_count")!=COUNT
        or receipt.get("unchanged_previous_count")!=31
        or receipt.get("neutral_swarm_private_overlay") is not True
        or receipt.get("official_rc_integrated") is not False
        or len(receipt.get("source_sha256",{}))!=COUNT):
        raise ValueError("RED: #504 original 34 source receipt contract mismatch")
    if set(receipt["source_sha256"])!=set(mapped):
        raise ValueError("RED: original script name/receipt identity mismatch")
    for name,(_,f,_,_) in mapped.items():
        if sha_file(f)!=receipt["source_sha256"][name]:
            raise ValueError("RED: original #504 source hash mismatch "+name)
    expected_servers={
      "EGGRUMBLE_BotActors","EGGRUMBLE_BotPathRouter","EGGRUMBLE_SevenRoleCombat",
      "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_CastleDefenseLive","EGGRUMBLE_CastleDefensePolicy",
      "EGGRUMBLE_NeutralSpawnPacing","EGGRUMBLE_NeutralEncounterFairness",
      "EGGRUMBLE_SwarmCombat","EGGRUMBLE_RaidItemIntake","EGGRUMBLE_FieldItemPickups",
      "EGGRUMBLE_MatchResultService","EGGRUMBLE_ScoreBalance","EGGRUMBLE_NeutralStoneGiant",
    }
    expected_clients={
      "EGGRUMBLE_RealHitAudio","EGGRUMBLE_CombatFXClarity",
      "EGGRUMBLE_GQ_ObjectiveCompass","EGGRUMBLE_ProceduralSkills",
    }
    if (not expected_servers.issubset(manifest["tree"]["ServerScriptService"])
        or not expected_clients.issubset(manifest["tree"]["StarterPlayer"]["StarterPlayerScripts"])
        or mapped[HOST][2]!="Script"):
        raise ValueError("RED: 8-domain #504 original composition incomplete")
    before=mapped[HOST][1].read_text(encoding="utf-8")
    after=patch34(before,original_host.read_text(encoding="utf-8"),
        item.read_text(encoding="utf-8"))
    private_host=out.parent/PRIVATE_HOST
    if private_host.exists():
        raise ValueError("RED: refuse overwrite of generated private host")
    private_host.write_text(after,encoding="utf-8")
    merged=copy.deepcopy(manifest)
    hostnode=merged["tree"]
    for part in mapped[HOST][0]:
        hostnode=hostnode[part]
    hostnode["$path"]=os.path.relpath(private_host,out.parent).replace(os.sep,"/")
    merged["name"]=BASENAME
    out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,final=scripts(out,COUNT)
    for name,(_,file,cl,_) in mapped.items():
        current=final[name]
        if cl!=current[2]:
            raise ValueError("RED: changed original script class "+name)
        if name!=HOST and (file!=current[1] or sha_file(file)!=sha_file(current[1])):
            raise ValueError("RED: modified non-terrain owner source "+name)
    if len(final)!=COUNT or len(merged["tree"]["ServerScriptService"])-1!=27:
        raise ValueError("RED: extra/deleted original modules")
    digest={name:sha_file(file) for name,(_,file,_,_) in sorted(final.items())}
    record={
      "status":"PRIVATE34_SOURCE_EXACT_NOT_OFFICIAL_RC",
      "source_count":COUNT,"unchanged_owner_sources":33,
      "original_34_receipt_sha256":sha_file(receipt_file),
      "original_34_project_sha256":sha_file(project),
      "one_private_host_hunk":"TEAM.CentralRidge_ONE-BLOCK_SHIELD_CLEARANCE",
      "original_author_head":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
      "existing_original34_composer":"#504@385d3242cbc8d0a3008ee818d8dc30040170fce6",
      "original_34_host_sha256":sha_file(mapped[HOST][1]),
      "original_host_blob":ORIGINAL_GIT_BLOB,
      "source_sha256":digest,
      "official_rc_adopted":0,
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
      "rollback":"replace one generated host mapping with #504's original host mapping",
    }
    (out.parent/RECEIPT).write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ520_ORIGINAL34_REUSE_FIELD_ITEM_ONLY_33_OF_34_UNCHANGED_PASS")
    return out

def verify(project:Path, place:Path)->None:
    project=project.resolve(strict=True)
    place=place.resolve(strict=True)
    _,sources=scripts(project,COUNT)
    record_path=project.parent/RECEIPT
    record=json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("status")!="PRIVATE34_SOURCE_EXACT_NOT_OFFICIAL_RC":
        raise ValueError("RED: wrong private receipt")
    actual={}
    for node in ET.parse(place).getroot().iter("Item"):
        klass=node.attrib.get("class")
        if klass not in ("Script","ModuleScript","LocalScript"):continue
        props=node.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if name in actual or not name or source is None:
            raise ValueError("RED: missing/duplicate actual Roblox source "+str(name))
        actual[name]=(klass,source.replace("\r\n","\n"))
    if len(actual)!=COUNT or set(actual)!=set(sources):
        raise ValueError("RED: 34/34 names do not match")
    for name,(_,source,klass,_) in sources.items():
        if actual[name]!=(klass,source.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED: real Rojo source/class mismatch "+name)
        if sha_file(source)!=record["source_sha256"][name]:
            raise ValueError("RED: receipt mismatch "+name)
    record["place_bytes"]=place.stat().st_size
    record["place_sha256"]=sha_file(place)
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ520_PRIVATE34_ACTUAL_ROJO_SOURCE_AND_CLASS_34_OF_34_PASS",
          record["place_bytes"],record["place_sha256"])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="op",required=True)
    p=sub.add_parser("prepare")
    for key in ("project","receipt_file","original_host","item","out"):
        p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    p=sub.add_parser("verify")
    for key in ("project","place"):
        p.add_argument("--"+key,type=Path,required=True)
    a=ap.parse_args()
    if a.op=="prepare":
        prepare(a.project,a.receipt_file,a.original_host,a.item,a.out)
    else:verify(a.project,a.place)
if __name__=="__main__":main()
