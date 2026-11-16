#!/usr/bin/env python3
"""Build/verify one unpublished exact-source V3 21-script Place after one terrain hunk.
Original #482 sources are read-only; generated private host is separate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from patch_ridge import AUTHOR, HOST, ITEMS, patch_author_host

ORIGINAL_PROJECT = AUTHOR / "EGGRUMBLE_V3_STUDIO.project.json"
HOST_NAME = "EGGRUMBLE_LobbyCastleModesPreview"
HOST_FILE = "EGGRUMBLE_LobbyCastleModesPreview.private.server.luau"
EXPECTED_COUNT = 21

def walk(node: dict, chain=()):
    for name, entry in node.items():
        if name.startswith("$") or not isinstance(entry, dict):
            continue
        if "$path" in entry:
            if set(entry) != {"$path"}:
                raise ValueError(("mixed path/authority", name))
            yield chain + (name,), entry
        else:
            yield from walk(entry, chain + (name,))

def sources(project: Path):
    obj = json.loads(project.read_text(encoding="utf-8"))
    out = {}
    for chain, entry in walk(obj["tree"]):
        name = chain[-1]
        if name in out:
            raise ValueError(("duplicate source name", name))
        src = (project.parent / entry["$path"]).resolve(strict=True)
        cls = "Script" if src.name.endswith(".server.luau") else (
            "LocalScript" if src.name.endswith(".client.luau") else "ModuleScript"
        )
        out[name] = (cls, src, chain)
    return out

def compose(outdir: Path) -> Path:
    outdir = outdir.resolve()
    if outdir.is_relative_to(AUTHOR.resolve()):
        raise ValueError("RED: private files must not overwrite original author")
    outdir.mkdir(parents=True, exist_ok=True)
    obj = json.loads(ORIGINAL_PROJECT.read_text(encoding="utf-8"))
    original = sources(ORIGINAL_PROJECT)
    if len(original) != EXPECTED_COUNT or HOST_NAME not in original:
        raise ValueError("RED: original V3 project no longer maps exactly 21 scripts")
    patched = patch_author_host(HOST.read_text(encoding="utf-8"), ITEMS.read_text(encoding="utf-8"))
    private_host = outdir / HOST_FILE
    private_host.write_text(patched, encoding="utf-8")
    # Preserve exact original author paths for 20/21 sources; only one host override.
    for chain, entry in walk(obj["tree"]):
        name = chain[-1]
        file = private_host if name == HOST_NAME else original[name][1]
        entry["$path"] = Path(os.path.relpath(file, outdir)).as_posix()
    project = outdir / "GQ_V3_RIDGE_PRIVATE21.project.json"
    project.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    current = sources(project)
    if set(current) != set(original):
        raise ValueError("RED: script names changed")
    for name in original:
        if name == HOST_NAME:
            if current[name][1] != private_host or current[name][0] != "Script":
                raise ValueError("RED: original host class or path changed")
        elif current[name][1] != original[name][1]:
            raise ValueError(("RED: original source path changed",name))
    print("GQ_V3_RIDGE_PRIVATE21_COMPOSE_PASS", project, "exact original20 + patch host1")
    return project

def verify(project: Path, place: Path) -> dict:
    proj = sources(project)
    actual = {}
    for item in ET.parse(place).getroot().iter("Item"):
        klass = item.attrib.get("class")
        if klass not in {"Script","LocalScript","ModuleScript"}:
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if name:
            if name in actual:
                raise ValueError(("duplicate runtime source",name))
            actual[name] = (klass, (source or "").replace("\r\n","\n"))
    if len(proj) != EXPECTED_COUNT or set(proj) != set(actual):
        raise ValueError(("RED: source count/names mismatch",len(proj),len(actual)))
    for name,(klass,path,_) in proj.items():
        content = path.read_text(encoding="utf-8").replace("\r\n","\n")
        if actual[name] != (klass,content):
            raise ValueError(("RED: Rojo source/class drift",name))
    original = sources(ORIGINAL_PROJECT)
    if len(original) != EXPECTED_COUNT:
        raise ValueError("RED: original source count changed")
    for name,(_,src,_) in original.items():
        if name == HOST_NAME:
            continue
        if src.read_bytes() != proj[name][1].read_bytes():
            raise ValueError(("RED: original author source overwritten",name))
    if proj[HOST_NAME][1].read_text(encoding="utf-8") != patch_author_host(
        HOST.read_text(encoding="utf-8"), ITEMS.read_text(encoding="utf-8")
    ):
        raise ValueError("RED: private host hunk drifted")
    report = {
        "source_exact": "21/21", "original_unchanged": 20,
        "patched_host": 1, "official_rc_adopted": False, "engine_tested": False,
        "place_bytes": place.stat().st_size,
        "place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    (project.parent/"GQ_RIDGE_SOURCE_RECEIPT.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    print("GQ_V3_RIDGE_PRIVATE21_ROJO_SOURCE_CLASS_EXACT_PASS", report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    cmd=parser.add_subparsers(dest="cmd",required=True)
    p=cmd.add_parser("compose");p.add_argument("--outdir",type=Path,required=True)
    v=cmd.add_parser("verify");v.add_argument("--project",type=Path,required=True);v.add_argument("--place",type=Path,required=True)
    args=parser.parse_args()
    if args.cmd=="compose":
        compose(args.outdir)
    else:
        verify(args.project,args.place)
if __name__=="__main__":
    main()
