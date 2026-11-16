#!/usr/bin/env python3
"""Source-select preexisting original #523 FIELD-egg layout into current real 31-source Host.
Does not author any new game logic. Other 30 scripts exact byte-for-byte.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from importlib.machinery import SourceFileLoader
from pathlib import Path
import xml.etree.ElementTree as ET

OWNER523_HEAD="54ea74aa15e387d83512566715f44216ba8587a2"
OWNER523_PATCH_GIT_BLOB="bd70e14c44341e0c827c43af1990ad8e11a4c698"
ORIGINAL482_HOST_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
COUNT=31


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def mapping(project_path: Path):
    project=json.loads(project_path.read_text(encoding="utf-8"))
    sources={}
    def walk(node,parents=()):
        for key,value in node.items():
            if key.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_BROKEN_SCRIPT_MAP")
            name=parents+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or name in sources:
                    raise ValueError("RED_DUPLICATE_SCRIPT_MAP")
                file=(project_path.parent/value["$path"]).resolve(strict=True)
                sources[name]=file
            else:walk(value,name)
    walk(project["tree"])
    if len(sources)!=COUNT or len({k[-1] for k in sources})!=COUNT or HOST not in sources:
        raise ValueError("RED_NOT_ONE_CANONICAL_HOST_IN31")
    return project,sources


def original_author(path: Path):
    if git_blob(path.read_bytes()) != OWNER523_PATCH_GIT_BLOB:
        raise ValueError("RED_PINNED_ORIGINAL523_AUTHOR_BLOB_DRIFT")
    a=SourceFileLoader("gq_original523_author",str(path)).load_module()
    if a.ORIGINAL_COMMIT!="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9" or a.ORIGINAL_HOST_BLOB!=ORIGINAL482_HOST_BLOB:
        raise ValueError("RED_PINNED_ORIGINAL523_PARENT_DRIFT")
    return a


def prepare(base: Path, author_file: Path, destination: Path):
    base=base.resolve(strict=True)
    author_file=author_file.resolve(strict=True)
    if destination.resolve()==base or destination.parent.resolve()!=base.parent:
        raise ValueError("RED_OUTPUT_MUST_BE_SIBLING_NONDESTRUCTIVE")
    original,mapped=mapping(base)
    author=original_author(author_file)
    old=mapped[HOST].read_text(encoding="utf-8")
    # Only #523's *original authored function* owns this change. Source guards
    # demand all 24 IDs unchanged, old x/row layout present exactly once.
    if ('local function nearbyBoard(' not in old or
        'session.refresh=function()' not in old or
        'coreBoard.MaxDistance=' not in old or
        'vaultBoard.MaxDistance=' not in old):
        raise ValueError("RED_PRIOR_539_537_547_HOST_INTEGRATION_MISSING")
    changed=author.patch(old)
    if changed.replace(author.ROWS_LINE,"",1).replace(author.REPLACEMENT_LINE,author.ORIGINAL_LINE,1)!=old:
        raise ValueError("RED_523_NOT_REVERSIBLE_EXACT")
    out=destination.parent/"GQ523_ORIGINAL_FIELD_EGG_HOST.server.luau"
    if out.exists() and out.read_text(encoding="utf-8")!=changed:
        raise ValueError("RED_SELECTED_HOST_DRIFT")
    out.write_text(changed,encoding="utf-8")
    data=copy.deepcopy(original)
    data["tree"]["ServerScriptService"][HOST[-1]]["$path"]=out.name
    destination.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,selected=mapping(destination)
    if set(mapped)!=set(selected):
        raise ValueError("RED_CHANGE_OF_GAME_SOURCE_AUTHORITY")
    diff=[key for key in mapped if mapped[key].read_bytes()!=selected[key].read_bytes()]
    if diff!=[HOST]:
        raise ValueError("RED_CHANGED_SOURCES_NOT_ONLY_EXISTING_HOST "+str(diff))
    receipt={
      "script_count":COUNT,"changed_source":"/".join(HOST),
      "other_30_sources_byte_exact":True,"owner523_fixed_head":OWNER523_HEAD,
      "owner523_original_patch_git_blob":OWNER523_PATCH_GIT_BLOB,
      "original482_host_git_blob":ORIGINAL482_HOST_BLOB,
      "before_host_sha256":sha(old.encode()),"after_host_sha256":sha(changed.encode()),
      "off_project":base.name,"on_project":destination.name,
      "off_rollback_source_byte_exact":True,
      "existing_original_547_castle_boards_preserved":True,
      "new_game_remote_store_authorities":False,"studio_android_owner":"NOT_TESTED",
      "formal_rc_adoption":False,
    }
    (destination.parent/"GQ523_FIELD_EGGS_31_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ523_REAL_31_AUTHOR_FIELD_EGGS_SINGLE_EXISTING_HOST_SELECTED",sha(changed.encode()),"OTHER30_BYTE_EXACT")


def verify(base: Path, author_file: Path, selected: Path, place: Path):
    author=original_author(author_file.resolve(strict=True))
    _,old=mapping(base.resolve(strict=True))
    _,new=mapping(selected.resolve(strict=True))
    if set(old)!=set(new):
        raise ValueError("RED_NAME_OR_AUTHORITY_CHANGE")
    original=old[HOST].read_text(encoding="utf-8")
    patched=new[HOST].read_text(encoding="utf-8")
    if patched!=author.patch(original):
        raise ValueError("RED_NOT_EXACT_ORIGINAL523_SOURCE_PATCH")
    if [key for key in old if old[key].read_bytes()!=new[key].read_bytes()]!=[HOST]:
        raise ValueError("RED_OTHER_SOURCE_MUTATED")
    found={}
    for item in ET.parse(place).iter("Item"):
        kind=item.attrib.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_PLACE_SCRIPT_PROPERTIES_MISSING")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in found:raise ValueError("RED_PLACE_DUPLICATE_SCRIPT")
        found[name]=(kind,src.replace("\r\n","\n"))
    if set(found)!={k[-1] for k in new}:raise ValueError("RED_PLACE_NAMES_NOT_31")
    for key,f in new.items():
        typ=("Script" if f.name.endswith(".server.luau") else
             "LocalScript" if f.name.endswith(".client.luau") else "ModuleScript")
        expected=(typ,f.read_text(encoding="utf-8").replace("\r\n","\n"))
        if found[key[-1]]!=expected:
            raise ValueError("RED_SOURCE_CLASS_NOT_EXACT "+key[-1])
    receipt_file=selected.parent/"GQ523_FIELD_EGGS_31_SOURCE_RECEIPT.json"
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    if not receipt["off_rollback_source_byte_exact"] or not receipt["other_30_sources_byte_exact"]:
        raise ValueError("RED_RECEIPT_INVALID")
    receipt.update({"real_rojo_source_class_exact":"31/31","place_size_bytes":place.stat().st_size,
                    "place_sha256":sha(place.read_bytes())})
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ523_CURRENT31_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",receipt["place_size_bytes"],receipt["place_sha256"])


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--author",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.author,args.out)
    else:
        if not args.place:p.error("verify needs --place")
        verify(args.base,args.author,args.out,args.place)


if __name__=="__main__":main()
