#!/usr/bin/env python3
"""Source-select existing #517 author HEAL no-waste hunk ON TOP OF current official #489 ITEM.

Only one pre-existing Item Script changes. Original 31-source project and all
other 30 source bytes remain intact, with strict original-author Git blobs.
This is an RC adoption candidate, NOT Roblox engine acceptance or publication.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR517_HEAD = "c8a324ad7bb40648d82a5828cbf54e217585fefd"
AUTHOR517_PATCH_BLOB = "114e888b26af42b6738f38c28526628015531e98"
AUTHOR489_ITEM_BLOB = "107046cb0bf81fed9e3cba1699ada31571e44a22"
ITEM = ("ServerScriptService", "EGGRUMBLE_FieldItemPickups")
ANCHOR = "if not healUseful(kind,hum.Health,hum.MaxHealth) then return end"

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def collect(project_path: Path):
    obj = json.loads(project_path.read_text(encoding="utf-8"))
    files = {}
    def visit(node, prefix=()):
        for name, value in node.items():
            if name.startswith("$"):
                continue
            route = prefix+(name,)
            if not isinstance(value,dict):
                raise ValueError("RED_INVALID_PROJECT_NODE")
            if "$path" in value:
                if set(value) != {"$path"} or route in files:
                    raise ValueError("RED_DUPLICATE_OR_METADATA")
                files[route] = (project_path.parent / value["$path"]).resolve(strict=True)
            else:
                visit(value,route)
    visit(obj["tree"])
    if len(files) != 31 or len({k[-1] for k in files}) != 31 or ITEM not in files:
        raise ValueError("RED_CANONICAL31_NOT_UNIQUE")
    for singular in ("EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SevenRoleCombat",
                     "EGGRUMBLE_SwarmCombat", "EGGRUMBLE_BotActors"):
        if sum(k[-1]==singular for k in files)!=1:
            raise ValueError("RED_DUPLICATE_AUTHORITY "+singular)
    return obj,files

def get_author_patch(path: Path):
    raw=path.read_bytes()
    if blob(raw)!=AUTHOR517_PATCH_BLOB:
        raise ValueError("RED_ORIGINAL_AUTHOR517_SOURCE_LOCK")
    spec=importlib.util.spec_from_file_location("original517",path)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    if module.ORIGINAL_ITEM_GIT_BLOB!=AUTHOR489_ITEM_BLOB:
        raise ValueError("RED_ORIGINAL517_WRONG_ITEM_PARENT")
    return module

def prepare(base:Path, author517:Path, out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.parent!=base.parent or out==base or out.exists():
        raise ValueError("RED_OUTPUT_MUST_BE_NEW_SIBLING")
    project, paths=collect(base)
    before=paths[ITEM].read_bytes()
    if blob(before)!=AUTHOR489_ITEM_BLOB:
        raise ValueError("RED_ITEM489_IS_NOT_LATEST_SELECTED_AUTHOR")
    author=get_author_patch(author517)
    candidate=author.patch(before.decode("utf-8"))
    if candidate.count(ANCHOR)!=1 or candidate.count(author.HELPER)!=1 or candidate.count(author.CALL)!=1:
        raise ValueError("RED_DUPLICATE_HEAL_GUARD")
    if candidate.replace(author.HELPER,"",1).replace(author.CALL,"",1)!=before.decode("utf-8"):
        raise ValueError("RED_ROLLBACK_NOT_BYTE_EXACT")
    # The HEAL gate must happen before cooldown/consumption, and never weaken #489
    for later in ("local key=tostring(player.UserId)", "consumed[id]=true;lastUse[key]=now",
                  'interactionGuard.allow(player,part,"拾う",part.Name)'):
        if candidate.index(ANCHOR)>=candidate.index(later):
            raise ValueError("RED_HEAL_CHECK_AFTER_CONSUMPTION")
    for must in (
       'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end',
       "if not matchActive() or player.Character~=buffCharacter then return end",
       "local RESPAWN_SECONDS=35",
       "return Items",
    ):
        if must not in candidate:
            raise ValueError("RED_ITEM489_AUTHOR_SAFETY_LOST "+must)
    selected_path=out.parent/"GQ_ITEM489_HEAL517_SINGLE.luau"
    if selected_path.exists() and selected_path.read_bytes()!=candidate.encode("utf-8"):
        raise ValueError("RED_SELECTED_SOURCE_ALREADY_CONFLICTING")
    selected_path.write_bytes(candidate.encode("utf-8"))
    selected=copy.deepcopy(project)
    selected["tree"][ITEM[0]][ITEM[1]]["$path"]=selected_path.name
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,current=collect(out)
    if set(current)!=set(paths) or any(current[k].read_bytes()!=paths[k].read_bytes() for k in paths if k!=ITEM):
        raise ValueError("RED_OTHER_30_SOURCE_BYTES_CHANGED")
    if current[ITEM].read_bytes()!=candidate.encode("utf-8"):
        raise ValueError("RED_ITEM_PATCH_NOT_SELECTED")
    receipt={
      "feature_id":"GQ-V3-HEAL-NO-WASTE-517",
      "original_author517_head":AUTHOR517_HEAD,
      "original_author517_patch_blob":AUTHOR517_PATCH_BLOB,
      "parent_original_item489_blob":AUTHOR489_ITEM_BLOB,
      "changed_script":"ServerScriptService/EGGRUMBLE_FieldItemPickups",
      "original_other_source_bytes_exact":30,"script_count":31,
      "off_item_sha256":sha(before),"on_item_sha256":sha(candidate.encode()),
      "off_project":base.name,"on_project":out.name,
      "rollback":"Reselect original #489 item in official 31-source companion",
      "engine_tested":False,"android_tested":False,"owner_accepted":False,
      "source_author_revision":"EXACT_PINNED"
    }
    (out.parent/"GQ517_HEAL_RC31_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ517_HEAL_SOURCE_SELECTED_EXACT_ONE_ITEM_31_30_OTHER_AUTHOR_BYTES_PASS")
    return receipt

def verify(base:Path,selected:Path,place:Path):
    _,a=collect(base)
    _,b=collect(selected)
    if set(a)!=set(b):
        raise ValueError("RED_SELECTED_PROJECT_MAP_DRIFT")
    changed=[k for k in a if a[k].read_bytes()!=b[k].read_bytes()]
    if changed!=[ITEM] or blob(a[ITEM].read_bytes())!=AUTHOR489_ITEM_BLOB:
        raise ValueError("RED_NOT_SINGLE_ITEM_ON_TOP_OF_489")
    if b[ITEM].read_text(encoding="utf-8").count(ANCHOR)!=1:
        raise ValueError("RED_NO_HEAL_GUARD")
    found={}
    for node in ET.parse(place).iter("Item"):
        kind=node.attrib.get("class")
        if kind not in {"Script","LocalScript","ModuleScript"}:continue
        props=node.find("Properties")
        if props is None:raise ValueError("RED_XML_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        txt=props.findtext("ProtectedString[@name='Source']")
        if txt is None:txt=props.findtext("string[@name='Source']")
        if not name or txt is None or name in found:raise ValueError("RED_DUPLICATE_XML_SCRIPT")
        found[name]=(kind,txt.replace("\\r\\n","\n"))
    if set(found)!={k[-1] for k in b}:raise ValueError("RED_WRONG_SCRIPT_COUNT_OR_NAMES")
    for route,path in b.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(kind,path.read_text(encoding="utf-8").replace("\\r\\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS_MISMATCH "+route[-1])
    receipt=json.loads((selected.parent/"GQ517_HEAL_RC31_RECEIPT.json").read_text())
    receipt.update({"source_class_exact":31,"actual_place_bytes":place.stat().st_size,
                    "actual_place_sha256":sha(place.read_bytes())})
    (selected.parent/"GQ517_HEAL_RC31_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ517_SELECTED_31_ROJO_CLASS_SOURCE_EXACT_PASS",place.stat().st_size,receipt["actual_place_sha256"])
    return receipt

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["prepare","verify"])
    parser.add_argument("--base",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--author517",type=Path)
    parser.add_argument("--place",type=Path)
    args=parser.parse_args()
    if args.action=="prepare":
        if not args.author517:parser.error("--author517 required")
        prepare(args.base,args.author517,args.out)
    else:
        if not args.place:parser.error("--place required")
        verify(args.base,args.out,args.place)
