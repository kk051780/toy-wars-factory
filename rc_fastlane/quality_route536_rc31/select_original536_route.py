#!/usr/bin/env python3
"""Compose ONE existing original #536 BotPathRouter correction into current V3 RC31.
No gameplay reimplementation; import #536's git-pinned original source patch.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from importlib.machinery import SourceFileLoader

SOURCE_AUTHOR_HEAD = "cdf4fe5f231c998532963c5c16d9525d20a69e7e"
SOURCE_AUTHOR_BLOB = "651d4c6e92bfe8595eeadb438b594797bd473e77"
ORIGINAL_ROUTER_BLOB = "d9841bb874659129cae6c930bce302ff6936ac4a"
KEY = ("ServerScriptService", "EGGRUMBLE_BotPathRouter")
COUNT = 31


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def flat(project: Path):
    data = json.loads(project.read_text(encoding="utf-8"))
    result = {}
    def walk(node, prefix=()):
        for name, body in node.items():
            if name.startswith("$"):
                continue
            key=prefix+(name,)
            if not isinstance(body,dict):
                raise ValueError("RED_INVALID_PROJECT")
            if "$path" in body:
                if set(body)!={"$path"} or key in result:
                    raise ValueError("RED_DUPLICATE_OR_INVALID_MAP")
                result[key] = (project.parent/body["$path"]).resolve(strict=True)
            else:
                walk(body,key)
    walk(data["tree"])
    if len(result)!=COUNT or len(set(k[-1] for k in result))!=COUNT or KEY not in result:
        raise ValueError("RED_NOT_CANONICAL31")
    if sum(k[-1]=="EGGRUMBLE_BotPathRouter" for k in result)!=1:
        raise ValueError("RED_SECOND_ROUTER")
    return data, result


def author_module(path: Path):
    if blob(path.read_bytes()) != SOURCE_AUTHOR_BLOB:
        raise ValueError("RED_ORIGINAL536_PATCH_AUTHOR_BLOB_DRIFT")
    module=SourceFileLoader("original536_exact_source_patch",str(path)).load_module()
    if (module.ORIGINAL_BLOB != ORIGINAL_ROUTER_BLOB
            or module.ORIGINAL_AUTHOR_HEAD != "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"):
        raise ValueError("RED_ORIGINAL536_AUTHOR_PARENT_DRIFT")
    return module


def select(base: Path, patch_author: Path, target: Path):
    base=base.resolve(strict=True)
    patch_author=patch_author.resolve(strict=True)
    if target.resolve()==base or target.parent.resolve()!=base.parent:
        raise ValueError("RED_OUTPUT_MUST_BE_SIBLING_NONDESTRUCTIVE")
    project,original=flat(base)
    old=original[KEY].read_bytes()
    if blob(old)!=ORIGINAL_ROUTER_BLOB:
        raise ValueError("RED_CURRENT_RC_ALREADY_CHANGED_ROUTER; source-select not safe")
    author=author_module(patch_author)
    new=author.overlay(old)
    if new==old or new.replace(author.AFTER.encode(),author.BEFORE.encode(),1)!=old:
        raise ValueError("RED_ORIGINAL_AUTHOR536_NOT_SINGLE_REVERSIBLE_HUNK")
    out=target.parent/"GQ536_ORIGINAL_AUTHOR_SINGLE_ROUTER.luau"
    if out.exists() and out.read_bytes()!=new:
        raise ValueError("RED_SELECTED_ROUTER_DRIFT")
    out.write_bytes(new)
    selected=copy.deepcopy(project)
    selected["tree"]["ServerScriptService"][KEY[-1]]["$path"]=out.name
    target.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,current=flat(target)
    if set(original)!=set(current):
        raise ValueError("RED_SOURCE_AUTHORITY_CHANGED")
    changed=[k for k in original if original[k].read_bytes()!=current[k].read_bytes()]
    if changed!=[KEY]:
        raise ValueError("RED_OTHER_SCRIPT_CHANGED "+repr(changed))
    receipt={
        "source_count":COUNT,
        "selected_author_head":SOURCE_AUTHOR_HEAD,
        "selected_author_patch_git_blob":SOURCE_AUTHOR_BLOB,
        "original_parent_router_git_blob":ORIGINAL_ROUTER_BLOB,
        "selected_router_git_blob":blob(new),
        "changed_source":"/".join(KEY),
        "others_byte_exact":COUNT-1,
        "old_project_sha256":digest(base.read_bytes()),
        "new_project_sha256":digest(target.read_bytes()),
        "old_router_sha256":digest(old),
        "new_router_sha256":digest(new),
        "off_project":base.name,
        "on_project":target.name,
        "rollback":"build OFF unmodified original #489 current official31 project",
        "formal_rc_adopted":False,
        "studio_android_owner":"NOT_TESTED",
    }
    (target.parent/"GQ536_ROUTE_RC31_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ536_ORIGINAL_AUTHOR_SINGLE_ROUTER_SELECTED_31",blob(old),blob(new),
          "OTHER30_BYTE_EXACT=PASS")


def verify(base: Path, selected: Path, author_patch: Path, place: Path):
    _,old=flat(base.resolve(strict=True))
    _,on=flat(selected.resolve(strict=True))
    if set(old)!=set(on) or len(on)!=COUNT:
        raise ValueError("RED_SOURCE_COUNT_DRIFT")
    author=author_module(author_patch.resolve(strict=True))
    if blob(old[KEY].read_bytes())!=ORIGINAL_ROUTER_BLOB:
        raise ValueError("RED_OFF_NOT_ORIGINAL_ROUTER")
    if on[KEY].read_bytes()!=author.overlay(old[KEY].read_bytes()):
        raise ValueError("RED_ON_NOT_ORIGINAL536_PATCH")
    if [k for k in old if old[k].read_bytes()!=on[k].read_bytes()]!=[KEY]:
        raise ValueError("RED_OTHER30_DRIFT")
    found={}
    for node in ET.parse(place).iter("Item"):
        kind=node.attrib.get("class")
        if kind not in {"Script","ModuleScript","LocalScript"}:
            continue
        props=node.find("Properties")
        if props is None:raise ValueError("RED_MISSING_SCRIPT_PROPS")
        name=props.findtext("string[@name='Name']")
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None:content=props.findtext("string[@name='Source']")
        if not name or content is None or name in found:
            raise ValueError("RED_MISSING_OR_DUPLICATE_PLACE_SOURCE")
        found[name]=(kind,content.replace("\r\n","\n"))
    if set(found)!={k[-1] for k in on}:
        raise ValueError("RED_PLACE31_SCRIPT_NAMES")
    for key,path in on.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]]!=(kind,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_SOURCE_CLASS_NOT_EXACT "+key[-1])
    receipt_path=selected.parent/"GQ536_ROUTE_RC31_RECEIPT.json"
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["others_byte_exact"]!=30 or receipt["new_project_sha256"]!=digest(selected.read_bytes()):
        raise ValueError("RED_RECEIPT_DRIFT")
    receipt.update({"real_rojo_exact_31":True,"place_bytes":place.stat().st_size,
                    "place_sha256":digest(place.read_bytes())})
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ536_CURRENT_CANONICAL31_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",
          receipt["place_bytes"],receipt["place_sha256"],"OTHER30_BYTE_EXACT")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("select","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.action=="select":
        select(args.base,args.author,args.out)
    else:
        if not args.place:p.error("verify requires --place")
        verify(args.base,args.out,args.author,args.place)


if __name__=="__main__":
    main()
