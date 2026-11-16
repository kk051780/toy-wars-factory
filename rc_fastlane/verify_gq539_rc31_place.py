#!/usr/bin/env python3
"""Canonical GQ539 RC31 readback: only existing Host changes, Rojo Source/Class exact.

No network, writer, merge, release or paid actions. Genuine engine FUN still NO_GO.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HOST = "EGGRUMBLE_LobbyCastleModesPreview"
TYPES = {"Script", "ModuleScript", "LocalScript"}


def flatten(project: Path) -> dict[tuple[str, ...], Path]:
    data = json.loads(project.read_text(encoding="utf-8"))
    found: dict[tuple[str, ...], Path] = {}
    def visit(node: dict, prefix: tuple[str, ...]=()):
        for key, value in node.items():
            if not isinstance(value, dict):
                continue
            route = prefix + (key,)
            if "$path" in value:
                if set(value) != {"$path"} or route in found:
                    raise ValueError("RED competing or duplicate source route")
                path = (project.parent / value["$path"]).resolve()
                if not path.is_file():
                    raise ValueError("RED missing file " + str(path))
                found[route] = path
            else:
                visit(value, route)
    visit(data["tree"])
    if len(found) != 31 or len({p[-1] for p in found}) != 31:
        raise ValueError("RED duplicate/missing 31 scripts")
    if len([p for p in found if p[-1]==HOST]) != 1:
        raise ValueError("RED expected exactly one existing Host")
    return found


def verify(base: Path, chosen: Path, place: Path) -> dict:
    old, new = flatten(base), flatten(chosen)
    if set(old) != set(new):
        raise ValueError("RED source routes changed")
    changed=[]
    for route, oldfile in old.items():
        if oldfile.read_bytes() != new[route].read_bytes():
            changed.append(route)
    if len(changed) != 1 or changed[0][-1] != HOST:
        raise ValueError("RED must change only one existing Host")
    # Original source and this selector are input pinned in the upstream official workflow.
    import importlib.util
    script = Path("_gq539_lobby/quality_gameplay/v3_lobby_nearby_20261116/select_original_host.py")
    spec = importlib.util.spec_from_file_location("original539", script)
    if spec is None or spec.loader is None:
        raise ValueError("RED missing original GQ539 selector")
    selector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(selector)
    route=changed[0]
    original_text=old[route].read_text(encoding="utf-8")
    selected_text=new[route].read_text(encoding="utf-8")
    if selector.undo(selected_text) != original_text:
        raise ValueError("RED rollback differs from true source")
    root=ET.fromstring(place.read_bytes())
    actual: dict[str,tuple[str,str]]={}
    for item in root.iter("Item"):
        kind=item.attrib.get("class")
        if kind not in TYPES:
            continue
        props=item.find("Properties")
        if props is None:
            raise ValueError("RED XML missing Script properties")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source=props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:
            raise ValueError("RED duplicate/missing Script Source")
        actual[name]=(kind,source.replace("\r\n","\n"))
    if len(actual)!=31 or set(actual)!={key[-1] for key in new}:
        raise ValueError("RED Rojo Script count/names changed")
    for route, file in new.items():
        kind=("Script" if file.name.endswith(".server.luau") else
              "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        text=file.read_text(encoding="utf-8").replace("\r\n","\n")
        if actual[route[-1]]!=(kind,text):
            raise ValueError("RED Rojo Source/Class mismatch " + route[-1])
    return {
      "status":"SAME_HEAD_RC_PR_SOURCE_31_EXACT_PENDING_FORMAL_RC_ADOPTION",
      "script_count":31,"rojo_exact_scripts":31,
      "selected_one_existing_host":True,"other_sources_byte_exact":30,
      "rollback_byte_exact":True,
      "castle_egg_owned_by":"PR547",
      "original_swarm_fallback_owned_by":"PR541",
      "place_bytes":place.stat().st_size,
      "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
      "studio_2client":"NOT_TESTED","android":"NOT_TESTED","owner_fun":"NO_GO"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--selected",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(verify(args.base,args.selected,args.place),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
