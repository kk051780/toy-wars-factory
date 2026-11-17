#!/usr/bin/env python3
"""Always choose the 31-source project whose actual Sources/Classes EXACTLY match
the current canonical RC31 Studio Place, not a stale version-named source project.
Only selector QA; does not write gameplay/author source or change publication.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

class RedGate(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise RedGate("RED_GQ470_CURRENT31_"+reason)

def canonical_scripts(place:Path):
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        require(props is not None,"MISSING_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source=props.findtext("string[@name='Source']")
        require(bool(name) and source is not None,"MISSING_NAME_OR_SOURCE")
        require(name not in found,"DUPLICATE_CANONICAL_NAME")
        found[name]=(cls,source.replace("\r\n","\n"))
    require(len(found)==31,"CANONICAL_NOT_31_SCRIPTS")
    return found

def candidate_scripts(project:Path, source_map):
    try:
        obj=json.loads(project.read_text(encoding="utf-8"))
        source=source_map(obj,project)
        if len(source)!=31:
            return None
        return {name:(cls,p.read_text(encoding="utf-8").replace("\r\n","\n"))
                for name,(p,cls) in source.items()}
    except (OSError,ValueError,KeyError,UnicodeError,TypeError):
        return None

def resolve(place:Path, directory:Path, source_map):
    canonical=canonical_scripts(place)
    require(directory.is_dir(),"PROJECT_ROOT_MISSING")
    matches=[]
    for project in sorted(directory.rglob("*.project.json")):
        if candidate_scripts(project,source_map)==canonical:
            matches.append(project)
    require(bool(matches),"NO_FINAL_CANONICAL_SOURCE_MATCH")
    # Every match has the EXACT same complete31 Source/Class as this actual Place.
    # The last deterministic path is safe; none can carry an old gameplay Source.
    return matches[-1],canonical,matches

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--selector",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location("original_gq634_selector",a.selector.resolve(strict=True))
    require(spec is not None and spec.loader is not None,"SELECTOR_IMPORT")
    lib=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    place=a.place.resolve(strict=True)
    chosen,canonical,matches=resolve(place,a.directory.resolve(strict=True),lib.source_map)
    receipt={
        "schema":"GQ470_CANONICAL31_ACTUAL_PLACE_MATCH_V1",
        "selected_project":str(chosen),"matching_project_count":len(matches),
        "current_canonical_place":str(place),
        "current_canonical_place_bytes":place.stat().st_size,
        "current_canonical_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
        "actual_script_source_class_exact":31,
        "current_project_source_count":len(canonical),
        "original_selector_reused":True,
        "studio_engine":"NOT_TESTED","publish_authorized":False
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(str(chosen.resolve()),flush=True)
if __name__=="__main__":
    main()
