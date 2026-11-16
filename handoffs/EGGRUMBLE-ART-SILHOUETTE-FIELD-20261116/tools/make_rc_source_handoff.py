#!/usr/bin/env python3
"""Emit reproducible A01 source-only RC handoff evidence for the five private Places.

This is NOT an official RC writer or a Studio/Android test. It hashes the actual
Rojo outputs and every mapped source while recording exact source ownership.
Never writes source branches, main, Roblox Place, or the real RC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

MODES=("v3","boss","castle","lobby","item")
ART_DIR=Path(__file__).resolve().parents[1]


def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(65536),b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(dir:Path)->str:
    return subprocess.check_output(["git","-C",str(dir),"rev-parse","HEAD"],text=True).strip()


def sources_under(tree:dict[str,Any], project_dir:Path, prefix:str="")->list[dict[str,str]]:
    entries=[]
    for name, value in tree.items():
        if name=="$path":
            filename=(project_dir/value).resolve(strict=True)
            if not filename.is_file():
                raise ValueError("Mapped source not a file: "+str(filename))
            entries.append({
                "node":prefix,
                "name":filename.name,
                "source_sha256":sha256(filename),
                "path":str(filename),
            })
        elif isinstance(value,dict):
            entries.extend(sources_under(value,project_dir,prefix+"/"+name))
    return entries


def generate(author_checkout:Path,project_dir:Path,private_dir:Path,
             output:Path,art_head:str="")->dict[str,Any]:
    author_checkout=author_checkout.resolve(strict=True)
    project_dir=project_dir.resolve(strict=True)
    private_dir=private_dir.resolve(strict=True)
    art_path=ART_DIR.resolve(strict=True)
    manifest={
        "schema":"EGGRUMBLE_ART_A01_SOURCE_HANDOFF_V1",
        "art_branch_requested_head":art_head or "UNKNOWN",
        "author_read_only_checkout_head":git_head(author_checkout),
        "rc_adopted":False,
        "studio_play": "NOT_RUN",
        "android_15min": "NOT_RUN",
        "owner_acceptance":"NOT_GRANTED",
        "art_quality_gate":"NO_GO",
        "official_rc_writer":"#220_ONLY",
        "private_modes":{},
    }
    unique_art_paths=set()
    for mode in MODES:
        project=(project_dir/("EGGRUMBLE_V3_CURRENT_ART_STUDIO.project.json"
                             if mode=="v3" else mode+".project.json")).resolve(strict=True)
        place=(private_dir/("EGGRUMBLE_A01_PRIVATE_"+mode+".rbxlx")).resolve(strict=True)
        if not place.is_file() or place.stat().st_size<1000:
            raise ValueError("Missing or empty real private Studio Place for "+mode)
        doc=json.loads(project.read_text(encoding="utf-8"))
        entries=sources_under(doc["tree"],project.parent)
        if not entries:
            raise ValueError("No source scripts for "+mode)
        for entry in entries:
            candidate=Path(entry["path"])
            if candidate.is_relative_to(art_path):
                unique_art_paths.add(entry["path"])
                entry["owner"]="A01_ART_ONLY"
            elif candidate.is_relative_to(author_checkout):
                entry["owner"]="ORIGINAL_GAME_AUTHOR_READ_ONLY"
            else:
                raise ValueError("Unexpected source outside isolated ownership: "+str(candidate))
            # Preserve the reproducible hash and relative source checkout path,
            # never leak runner-specific temporary checkout filesystem paths.
            entry["path"]=str(candidate.relative_to(art_path if entry["owner"]=="A01_ART_ONLY"
                                        else author_checkout))
        names=[entry["node"] for entry in entries]
        if len(names)!=len(set(names)):
            raise ValueError("Duplicated Rojo source node path")
        lod=[x for x in entries if x["name"]=="EGGRUMBLE_ArtDistanceLOD.client.luau"]
        if len(lod)!=1 or not lod[0]["node"].endswith("/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD"):
            raise ValueError("Art LOD must appear exactly once as a client StarterPlayerScript")
        if mode=="v3":
            if not any(x["name"]=="EGGRUMBLE_CombatFeel.client.luau" for x in entries):
                raise ValueError("Lost original author's client combat feedback")
            if sum(x["owner"]=="A01_ART_ONLY" for x in entries)!=4:
                raise ValueError("V3 must contain exactly 3 A01 server art + 1 client LOD")
        manifest["private_modes"][mode]={
            "rojo_build":"SOURCE_EXACT_PRIVATE_SUCCESS",
            "place_bytes":place.stat().st_size,
            "place_sha256":sha256(place),
            "project_sha256":sha256(project),
            "source_count":len(entries),
            "sources":entries,
        }
    if len(unique_art_paths)!=4:
        raise ValueError("Expected four and only four unique A01 art scripts across the private Places")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--author-checkout",type=Path,required=True)
    p.add_argument("--project-dir",type=Path,required=True)
    p.add_argument("--private-dir",type=Path,required=True)
    p.add_argument("--art-head",default="")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    m=generate(a.author_checkout,a.project_dir,a.private_dir,a.out,a.art_head)
    print("A01_SOURCE_ONLY_RC_HANDOFF=PASS")
    print("AUTHOR_SOURCE_HEAD="+m["author_read_only_checkout_head"])
    print("ART_SOURCE_HEAD="+m["art_branch_requested_head"])
    for mode,entry in m["private_modes"].items():
        print("PRIVATE_STUDIO_PLACE="+mode+" SOURCES="+str(entry["source_count"])+
              " SHA256="+entry["place_sha256"])
    print("OFFICIAL_RC_CAS_ADOPTED=0 STUDIO_ANDROID_OWNER=NOT_VERIFIED")


if __name__=="__main__":
    main()
