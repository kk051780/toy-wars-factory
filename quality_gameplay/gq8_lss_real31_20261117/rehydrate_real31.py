#!/usr/bin/env python3
"""Rehydrate the *current official* V3 31 Lua sources from a proven Rojo Place.

Unlike a mock31 test, every byte of the generated 31-source project originates
from the official selected31 Place on the exact official RC HEAD. No original
game sources are edited. All 31 Roblox classes and hierarchy routes are checked.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

CLASSES = {"Script": ".server.luau",
           "LocalScript": ".client.luau", "ModuleScript": ".luau"}
HOST = ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
SWARM = ("ServerScriptService", "EGGRUMBLE_SwarmCombat")
ENC = "utf-8"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_scripts(root: ET.Element) -> dict[tuple[str,...], tuple[str,str]]:
    out: dict[tuple[str,...],tuple[str,str]] = {}
    seen_referents: set[str] = set()

    def visit(item: ET.Element, parent: tuple[str,...]) -> None:
        ref = item.get("referent")
        if not ref or ref in seen_referents:
            raise ValueError("RED_DUPLICATE_OR_MISSING_ROBLOX_REFERENT")
        seen_referents.add(ref)
        props = item.find("Properties")
        name = props.findtext("string[@name='Name']") if props is not None else None
        if not name or not re.fullmatch(r"[A-Za-z0-9_]+", name):
            raise ValueError("RED_INVALID_INSTANCE_NAME")
        route = parent + (name,)
        cls = item.get("class")
        if cls in CLASSES:
            source = props.findtext("string[@name='Source']")
            if source is None:
                source = props.findtext("ProtectedString[@name='Source']")
            if source is None or route in out:
                raise ValueError("RED_MISSING_OR_DUPLICATE_SCRIPT_SOURCE")
            out[route] = (cls, source.replace("\r\n", "\n"))
        for child in item.findall("Item"):
            visit(child,route)

    for item in root.findall("Item"):
        visit(item,())
    return out


def flat_project(proj: dict) -> dict[tuple[str,...],dict]:
    if not isinstance(proj.get("tree"),dict):
        raise ValueError("RED_NO_ROJO_TREE")
    out: dict[tuple[str,...],dict] = {}

    def visit(node, prefix=()):
        for name, val in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(val,dict):
                raise ValueError("RED_BAD_ROJO_NODE")
            route=prefix+(name,)
            if "$path" in val:
                if route in out:raise ValueError("RED_DUPLICATE_ROJO_SOURCE")
                out[route]=val
            else:
                visit(val,route)
    visit(proj["tree"])
    return out


def extract(place: Path, template: Path, receipt: Path, out: Path, head: str):
    if not re.fullmatch(r"[a-f0-9]{40}",head):
        raise ValueError("RED_BAD_HEAD")
    if out.exists():
        raise ValueError("RED_REFUSE_OVERWRITE_EXTRACTION")
    info=json.loads(receipt.read_text(ENC))
    if info.get("github_commit_sha")!=head or not info.get("official_rc_commit_verified"):
        raise ValueError("RED_NOT_ACTUAL_SAMEHEAD_OFFICIAL")
    if info.get("place_sha256")!=sha(place):
        raise ValueError("RED_OFFICIAL_PLACE_SHA_MISMATCH")
    root=ET.parse(place).getroot()
    place_scripts=tree_scripts(root)
    original=json.loads(template.read_text(ENC))
    model=copy.deepcopy(original)
    routes=flat_project(model)
    if len(place_scripts)!=31 or len(routes)!=31:
        raise ValueError("RED_NOT_CANONICAL31")
    if set(routes)!=set(place_scripts):
        raise ValueError("RED_PROJECT_NOT_SAME_PLACE_HIERARCHY")
    if HOST not in place_scripts or SWARM not in place_scripts:
        raise ValueError("RED_MISSING_SINGLE_HOST_OR_SWARM")
    if len(set(r[-1] for r in place_scripts))!=31:
        raise ValueError("RED_DUPLICATE_SCRIPT_NAMES")
    if set(root.attrib.keys())!={"version"} or root.get("version")!="4":
        raise ValueError("RED_NOT_RBXLX_PLACE_V4")
    out.mkdir(parents=True)
    sources=out/"sources";sources.mkdir()
    metadata=[]
    for path, (cls,src) in sorted(place_scripts.items()):
        name=path[-1]
        target=sources/(name+CLASSES[cls])
        if target.exists():
            raise ValueError("RED_NAME_COLLISION")
        target.write_text(src,encoding=ENC,newline="\n")
        routes[path]["$path"]="sources/"+target.name
        metadata.append({
            "route":"/".join(path),"class":cls,"source_sha256":sha(target),
            "bytes":len(target.read_bytes())})
    model["name"]="EGGRUMBLE_V3_REAL31_REHYDRATED_"+head[:8]
    actual=out/"CURRENT31_REAL_SOURCE.project.json"
    actual.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",ENC)
    status={"feature":"GQ8_LSS_REAL31_SOURCE_BRIDGE_20261117",
            "official_rc_commit":head,
            "official_place_sha256":sha(place),
            "real_original31_count":len(metadata),
            "actual_source_routes_and_classes":metadata,
            "original_project_hierarchy_exact":True,
            "source_changed":False,
            "studio": "NOT_TESTED","android":"NOT_TESTED",
            "main_or_formal_rc_written":False}
    (out/"CURRENT31_REAL_SOURCE_RECEIPT.json").write_text(
        json.dumps(status,ensure_ascii=False,indent=2)+"\n",ENC)
    print("GQ8_LSS_CURRENT_REAL31_EXTRACT_SOURCE_CLASS_ROUTE_EXACT_PASS",head)
    return actual


def verify_built(project: Path, place: Path, expected_n: int):
    from collections import Counter
    source=json.loads(project.read_text(ENC))
    tree=flat_project(source)
    if len(tree)!=expected_n:
        raise ValueError("RED_WRONG_PROJECT_COUNT")
    expected={}
    for path,node in tree.items():
        f=(project.parent/node["$path"]).resolve(strict=True)
        ext=next((ext for ext in CLASSES.values() if f.name.endswith(ext)),None)
        if ext is None:raise ValueError("RED_BAD_SCRIPT_EXTENSION")
        cls=next(cls for cls,e in CLASSES.items() if e==ext)
        expected[path]=(cls,f.read_text(ENC).replace("\r\n","\n"))
    actual=tree_scripts(ET.parse(place).getroot())
    if len(actual)!=expected_n or actual!=expected:
        missing=set(expected)-set(actual)
        changed=[str(k) for k in expected.keys()&actual.keys() if expected[k]!=actual[k]]
        raise ValueError("RED_REAL_ROJO_SOURCE_OR_CLASS_MISMATCH: "+str((missing,changed)))
    print("GQ8_LSS_REAL_ROJO_SOURCE_CLASS_ROUTE_EXACT_PASS",expected_n,sha(place))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["extract","verify"])
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--template",type=Path)
    p.add_argument("--receipt",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--head")
    p.add_argument("--project",type=Path)
    p.add_argument("--count",type=int)
    a=p.parse_args()
    if a.action=="extract":
        if not all((a.template,a.receipt,a.out,a.head)):
            p.error("extract requires --template --receipt --out --head")
        extract(a.place,a.template,a.receipt,a.out,a.head)
    else:
        if a.project is None or a.count is None:
            p.error("verify requires --project --count")
        verify_built(a.project,a.place,a.count)


if __name__=="__main__":
    main()
