#!/usr/bin/env python3
"""GQ522 source-select 31 official V3 Luau scripts + existing Builder modules.
Source-only private Rojo candidate: one Host hook, 30 untouched originals, 2
optional modules. Never writes canonical RC branch or replaces original Game.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
HEAD = "325472fd280e0b013380f687a87fdf9be4b5f905"
SOURCE_PLACE_SHA256 = "8ae449893a1709127e96e7c061dda6926b6d8c0962627d265f8baad9b866f8cf"
SCRIPT_CLASSES = {"Script", "ModuleScript", "LocalScript"}
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
BUILDER = "EGGRUMBLE_BuilderConstruction"
POLICY = "EGGRUMBLE_BuilderPlacementPolicy"
REQUIRE = 'local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
EQUIP = 'SevenRoleCombat.equip(session,p,role)'
CLOSE = 'if session.world.Parent then session.world:Destroy() end'
STAMP = "GQ522_BUILDER_WALL_ONLY_PRIVATE_20261117"

class GateError(RuntimeError):
    pass

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def name(item: ET.Element) -> str:
    return item.findtext("Properties/string[@name='Name']") or ""

def source_node(item: ET.Element) -> ET.Element:
    props = item.find("Properties")
    if props is None:
        raise GateError("RED_NO_PROPERTIES")
    e = props.find("ProtectedString[@name='Source']")
    if e is None:
        e = props.find("string[@name='Source']")
    if e is None:
        raise GateError("RED_NO_SOURCE_" + name(item))
    return e

def walk(root: ET.Element):
    """Extract original paths + class + exact source, including nested services."""
    records = {}
    containers = {}
    def go(item: ET.Element, parents: tuple[str,...]):
        kind = item.attrib.get("class", "")
        label = name(item)
        if kind == "DataModel":
            path = parents
        else:
            if not label:
                raise GateError("RED_UNNAMED_ITEM_"+kind)
            path = parents + (label,)
        if kind in SCRIPT_CLASSES:
            if len(path) < 2 or path in records:
                raise GateError("RED_SCRIPT_PATH_COLLISION")
            records[path] = (kind, source_node(item).text or "")
        else:
            if path:
                containers[path] = kind
            for sub in item.findall("Item"):
                go(sub, path)
    for top in root.findall("Item"):
        go(top, ())
    return records, containers

def exact_replace(text: str, old: str, new: str, tag: str) -> str:
    if text.count(old) != 1 or new in text:
        raise GateError("RED_HOST_ANCHOR_"+tag)
    return text.replace(old, new, 1)

def host_select(src: str) -> str:
    if STAMP in src:
        raise GateError("RED_ALREADY_BUILDER_SELECTED")
    if "session.isCurrentHuman=function" not in src:
        raise GateError("RED_MISSING_ORIGINAL_531_LIVE_MATCH_FENCE")
    if src.count(EQUIP) != 2:
        raise GateError("RED_EXPECT_TWO_ORIGINAL_ROLE_EQUIP_PATHS")
    src = exact_replace(src, REQUIRE,
        REQUIRE + '\nlocal BuilderConstruction=require(script.Parent:WaitForChild("EGGRUMBLE_BuilderConstruction"))\n'
        + 'local BUILDER_WALL_RC_PREVIEW=true -- private source trial, not public authorization\n'
        + 'local BUILDER_BRIDGE_RC_PREVIEW=false -- real crossing not yet present\n', "REQUIRE")
    # One hook at spawn and one after same-session respawn, using the original Tool
    # transport. No second server Game, Remote or stand-in combat controller.
    hook = ('\n   if role=="BUILDER" then\n'
            '    BuilderConstruction.equip(session,p,BUILDER_WALL_RC_PREVIEW,BUILDER_BRIDGE_RC_PREVIEW)\n'
            '   end')
    src = src.replace(EQUIP, EQUIP + hook)
    src = exact_replace(src, CLOSE,
        "BuilderConstruction.clear(session)\n  " + CLOSE, "CLEANUP")
    if src.count("BuilderConstruction.equip(session,p,") != 2:
        raise GateError("RED_BUILDER_HOOK_COUNT")
    if src.count("BuilderConstruction.clear(session)") != 1:
        raise GateError("RED_BUILDER_CLEANUP_COUNT")
    return src

def new_project(records, containers, folder: Path, project: Path):
    tree = {"$className": "DataModel"}
    srcdir = folder / "source33"
    srcdir.mkdir(parents=True, exist_ok=True)
    if len({k[-1] for k in records}) != len(records):
        raise GateError("RED_SCRIPT_NAMES_NOT_UNIQUE")
    for path, (kind, raw) in records.items():
        node = tree
        for depth, step in enumerate(path[:-1], start=1):
            route = path[:depth]
            typ = containers.get(route)
            if not typ:
                raise GateError("RED_UNKNOWN_PARENT_" + "/".join(route))
            node = node.setdefault(step, {"$className": typ})
        ext = ".server.luau" if kind == "Script" else (
            ".client.luau" if kind == "LocalScript" else ".luau")
        dest = srcdir / (path[-1] + ext)
        if dest.exists():
            raise GateError("RED_SOURCE_NAME_CLASH")
        dest.write_text(raw, encoding="utf-8")
        node[path[-1]] = {"$path": str(dest.relative_to(project.parent))}
    project.write_text(json.dumps({"name": "GQ522_PRIVATE_BUILDER33_SOURCE_ONLY",
        "tree":tree}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def load_records(place: Path):
    raw = place.read_bytes()
    if digest(raw) != SOURCE_PLACE_SHA256:
        raise GateError("RED_PINNED_OFFICIAL_PLACE_SHA_MISMATCH")
    root = ET.fromstring(raw)
    rows, parents = walk(root)
    if len(rows) != 31:
        raise GateError("RED_NOT_ACTUAL_31_SCRIPTS")
    hosts = [k for k in rows if k[-1] == HOST]
    if len(hosts) != 1 or rows[hosts[0]][0] != "Script":
        raise GateError("RED_NO_UNIQUE_HOST")
    return rows, parents, hosts[0]

def select(place: Path, out: Path):
    originals, containers, key = load_records(place)
    selected = copy.deepcopy(originals)
    selected[key] = ("Script", host_select(originals[key][1]))
    parent = key[:-1]
    for component in (BUILDER, POLICY):
        k = parent + (component,)
        if k in selected:
            raise GateError("RED_DUPLICATE_BUILDER_MODULE")
        body = (HERE / (component + ".luau")).read_text(encoding="utf-8")
        if not body.startswith("--!strict\n"):
            raise GateError("RED_NONSTRICT_BUILDER_"+component)
        selected[k] = ("ModuleScript", body)
    if len(selected) != 33:
        raise GateError("RED_NOT_33_SCRIPTS")
    if {k for k in originals if selected.get(k) != originals[k]} != {key}:
        raise GateError("RED_MORE_THAN_ONE_OLD_SCRIPT_CHANGED")
    # Reverse rollback is byte-exact to the actual 31-script source.
    reversion = copy.deepcopy(selected)
    reversion[key] = originals[key]
    for component in (BUILDER, POLICY):
        del reversion[parent+(component,)]
    if reversion != originals:
        raise GateError("RED_31_SCRIPT_ROLLBACK_NOT_EXACT")
    out.mkdir(parents=True, exist_ok=True)
    project = out / "GQ522_CURRENT_RC_PRIVATE33.project.json"
    new_project(selected, containers, out, project)
    evidence = {
        "schema":"GQ522_REAL_CURRENT31_TO_PRIVATE33_V1",
        "official_base_sha":HEAD,
        "official_place_sha256":SOURCE_PLACE_SHA256,
        "private_candidate":True,
        "official_rc_adopted":False,
        "studio_android_art_fun_owner":"NOT_TESTED",
        "original_source_count":31,
        "candidate_source_count":33,
        "only_modified_existing_script":"/".join(key),
        "unchanged_existing_script_count":30,
        "original_31_rollback_exact":True,
        "original_531_live_membership_reused":True,
        "original_three_builder_skills_retained":True,
        "added_one_server_wall_tool":True,
        "bridge_ui_enabled":False,
        "builder_modules":[BUILDER,POLICY],
        "component_sha256":{k:digest(selected[parent+(k,)][1].encode("utf-8"))
                            for k in (BUILDER,POLICY)}
    }
    (out/"GQ522_REAL31_TO33_RECEIPT.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ522_CURRENT31_BUILDER33_SOURCE_SELECT_AND_OFF_ROLLBACK_PASS",
          evidence["official_base_sha"])

def verify(rojo: Path, project: Path):
    tree = json.loads(project.read_text(encoding="utf-8"))["tree"]
    expected = {}
    def scan(node, route=()):
        for key, val in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(val, dict):
                raise GateError("RED_PROJECT_INVALID")
            sub = route+(key,)
            if "$path" in val:
                file = (project.parent / val["$path"]).resolve(strict=True)
                typ = "Script" if file.name.endswith(".server.luau") else (
                    "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
                expected[sub] = (typ,file.read_text(encoding="utf-8").replace("\r\n","\n"))
            else:
                scan(val,sub)
    scan(tree)
    if len(expected)!=33:
        raise GateError("RED_PROJECT_NOT33")
    built,_ = walk(ET.fromstring(rojo.read_bytes()))
    if set(expected)!=set(built):
        raise GateError("RED_ROJO33_PATH_MISMATCH")
    for path,pair in expected.items():
        if (built[path][0],built[path][1].replace("\r\n","\n"))!=pair:
            raise GateError("RED_ROJO33_SOURCE_CLASS_MISMATCH_"+"/".join(path))
    receipt=project.parent/"GQ522_REAL31_TO33_RECEIPT.json"
    r=json.loads(receipt.read_text(encoding="utf-8"))
    r.update(private33_rojo_source_class_exact="33/33",
             private33_place_bytes=rojo.stat().st_size,
             private33_place_sha256=digest(rojo.read_bytes()))
    receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ522_ACTUAL_OFFICIAL31_TO_PRIVATE33_ROJO_SOURCE_CLASS_PASS",
          rojo.stat().st_size)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("select","verify"))
    p.add_argument("--official-place",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--rojo",type=Path)
    p.add_argument("--project",type=Path)
    args=p.parse_args()
    if args.action=="select":
        if args.official_place is None or args.out is None:
            p.error("select needs --official-place and --out")
        select(args.official_place,args.out)
    else:
        if args.rojo is None or args.project is None:
            p.error("verify needs --rojo and --project")
        verify(args.rojo,args.project)

if __name__=="__main__":
    main()
