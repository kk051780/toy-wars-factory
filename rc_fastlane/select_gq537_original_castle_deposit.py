#!/usr/bin/env python3
"""RC candidate: select the existing #537 author's castle deposit refresh into one canonical Host.

No new gameplay authority. 31 mapped Luau sources, 30/31 byte-identical,
read-only original owner inputs, reversible exact callback and Rojo verification.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
ORIGINAL_482_HOST_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
AUTHOR_537_COMPOSER_BLOB="0ed4bc12b5a448fa05a12ab803a2cad52e9d2260"
AUTHOR_537_HEAD="9e77a7f78147b68ce7d347131effb7475e6b74e2"
OWNER_482_HEAD="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ANCHOR='  if c.alive and c.heldEggs>0 then pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end) end\n'
REPLACEMENT=('  if c.alive and c.heldEggs>0 then\n'
             '   local ok=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)\n'
             '   if ok then session.refresh() end\n'
             '  end\n')

def digest(raw: bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def author_fix(original_host: Path, original_composer: Path):
    hostraw=original_host.read_bytes()
    if gitblob(hostraw)!=ORIGINAL_482_HOST_BLOB:
        raise ValueError("RED_ORIGINAL_OWNER482_HOST_SOURCE_DRIFT")
    blob=original_composer.read_bytes()
    if gitblob(blob)!=AUTHOR_537_COMPOSER_BLOB:
        raise ValueError("RED_ORIGINAL_GQ537_AUTHOR_SOURCE_DRIFT")
    old, new = [], []
    tree=ast.parse(blob.decode("utf-8"))
    for entry in tree.body:
        if isinstance(entry,ast.Assign):
            for target in entry.targets:
                if isinstance(target,ast.Name) and target.id in ("ANCHOR","REPLACEMENT"):
                    value=ast.literal_eval(entry.value)
                    (old if target.id=="ANCHOR" else new).append(value)
    if old!=[ANCHOR] or new!=[REPLACEMENT]:
        raise ValueError("RED_AUTHOR_537_CALLBACK_DIFF_NOT_EXACT")
    if hostraw.decode("utf-8").count(ANCHOR)!=1:
        raise ValueError("RED_OWNER_482_ANCHOR_MISSING")
    return old[0],new[0]

def flatten(path:Path):
    path=path.resolve(strict=True)
    tree=json.loads(path.read_text(encoding="utf-8"))
    found={}
    def visit(node,prefix=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            if not isinstance(child,dict):raise ValueError("RED_BAD_PROJECT_NODE")
            key=prefix+(name,)
            if "$path" in child:
                if set(child)!={"$path"} or key in found:
                    raise ValueError("RED_DUPLICATE_SOURCE_PATH")
                found[key]=(path.parent/child["$path"]).resolve(strict=True)
            else:visit(child,key)
    visit(tree["tree"])
    if len(set(k[-1] for k in found))!=len(found):
        raise ValueError("RED_DUPLICATE_RUNTIME_SCRIPT_NAME")
    return tree,found

def patch_host(original:str,anchor:str=ANCHOR,replacement:str=REPLACEMENT)->str:
    if original.count(anchor)!=1 or replacement in original:
        raise ValueError("RED_UNIQUE_GQ537_DEPOSIT_ANCHOR_MISSING_OR_ALREADY_FIXED")
    for marker,expected in (("session.isCurrentHuman=function",1),
                            ("gqDualBudget=GQDualBudget.new(",1),
                            ("RoundReplay.leaveWaitingQueue(",2),
                            ("RoundReplay.canStartCountdown(",1)):
        if original.count(marker)!=expected:
            raise ValueError("RED_31_HOST_OWNER_CONTROL_MISSING "+marker)
    result=original.replace(anchor,replacement,1)
    if result.replace(replacement,anchor,1)!=original:
        raise ValueError("RED_NON_REVERSIBLE_DEPOSIT_CHANGE")
    return result

def select(project_path:Path, original_host:Path, author_composer:Path, out_path:Path):
    anchor,replacement=author_fix(original_host,author_composer)
    in_data,sources=flatten(project_path)
    if len(sources)!=31 or HOST not in sources:
        raise ValueError("RED_CANONICAL_V3_31_SOURCE_MISSING")
    out_path=out_path.resolve()
    if out_path.exists():raise ValueError("RED_OUTPUT_PROJECT_ALREADY_EXISTS")
    host_path=sources[HOST]
    base=host_path.read_text(encoding="utf-8")
    selected=patch_host(base,anchor,replacement)
    for marker in ("Rules.damageCastle(","Rules.takeEggs(","Rules.takeFieldEgg(",
                   "session.dropCarrierEggs","session.isCurrentHuman=function"):
        if selected.count(marker)!=base.count(marker):
            raise ValueError("RED_UNRELATED_GAMEPLAY_AUTHORITY_CHANGED "+marker)
    folder=out_path.parent
    folder.mkdir(parents=True,exist_ok=True)
    selected_host=folder/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    if selected_host.exists():raise ValueError("RED_HOST_OUTPUT_OVERWRITE")
    selected_host.write_text(selected,encoding="utf-8")
    data=copy.deepcopy(in_data)
    data["name"]="EGGRUMBLE_V3_GQ537_ONE_ORIGINAL_HOST_RC31_SOURCE_SELECTION"
    def remap(node,prefix=()):
        for key,child in node.items():
            if key.startswith("$"):continue
            route=prefix+(key,)
            if "$path" in child:
                file=selected_host if route==HOST else sources[route]
                child["$path"]=os.path.relpath(file,folder).replace(os.sep,"/")
            else:remap(child,route)
    remap(data["tree"])
    out_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=flatten(out_path)
    if set(mapped)!=set(sources) or len(mapped)!=31:
        raise ValueError("RED_NOT_ONE_31_SOURCE_PROJECT")
    for route,path in sources.items():
        expected=selected.encode("utf-8") if route==HOST else path.read_bytes()
        if mapped[route].read_bytes()!=expected:
            raise ValueError("RED_30_OTHER_ORIGINAL_SOURCES_CHANGED "+"/".join(route))
    receipt={
        "kind":"GQ537_AUTHOR_SOURCE_SELECTED_RC31_CANDIDATE",
        "source_count":31, "source_unchanged_count":30,
        "changed_runtime_script":"/".join(HOST),
        "original_482_head":OWNER_482_HEAD,
        "original_482_host_blob":ORIGINAL_482_HOST_BLOB,
        "original_537_head":AUTHOR_537_HEAD,
        "original_537_composer_blob":AUTHOR_537_COMPOSER_BLOB,
        "host_before_sha256":digest(host_path.read_bytes()),
        "host_after_sha256":digest(selected.encode("utf-8")),
        "rollback": "omit selected Host file / use input project: all 31 original bytes exact",
        "studio_android_owner_accepted":False,
    }
    (folder/"GQ537_SELECTED_31_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ537_SINGLE_AUTHOR_HOST_SELECTED_31_30_UNCHANGED_PASS")
    return receipt

def verify_place(project_path:Path, original_project:Path, place_path:Path):
    _,selected=flatten(project_path)
    _,original=flatten(original_project)
    if len(selected)!=31 or set(selected)!=set(original):
        raise ValueError("RED_V3_SOURCE_SET_COUNT")
    actual={}
    for item in ET.fromstring(place_path.read_bytes()).iter("Item"):
        kind=item.attrib.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_ROJO_ITEM_NO_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or name in actual or source is None:
            raise ValueError("RED_ROJO_DUPLICATE_SCRIPT_OR_EMPTY")
        actual[name]=(kind,source.replace("\r\n","\n"))
    if len(actual)!=31 or set(actual)!={route[-1] for route in selected}:
        raise ValueError("RED_ROJO_RUNTIME_SCRIPT_COUNT")
    for route,file in selected.items():
        kind=("Script" if file.name.endswith(".server.luau") else
              "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if actual[route[-1]]!=(kind,file.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS_MISMATCH "+route[-1])
        if route!=HOST and file.read_bytes()!=original[route].read_bytes():
            raise ValueError("RED_UNAUTHORIZED_OTHER_SOURCE_CHANGE")
    old=original[HOST].read_text(encoding="utf-8")
    new=selected[HOST].read_text(encoding="utf-8")
    if new.replace(REPLACEMENT,ANCHOR,1)!=old:
        raise ValueError("RED_HOST_ROLLBACK_NOT_EXACT")
    receipt={"rojo_source_class_exact":31,"other_original_sources_byte_exact":30,
             "place_bytes":place_path.stat().st_size,
             "place_sha256":digest(place_path.read_bytes()),"studio_tested":False}
    print("GQ537_TRUE_ROJO_SELECTED_31_SOURCE_CLASS_PASS",receipt)
    return receipt

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source-project",type=Path,required=True)
    a.add_argument("--original-project",type=Path)
    a.add_argument("--original-owner-host",type=Path)
    a.add_argument("--original-author-537",type=Path)
    a.add_argument("--out",type=Path)
    a.add_argument("--verify-place",type=Path)
    args=a.parse_args()
    if args.verify_place:
        if args.original_project is None:a.error("--original-project is required")
        print(json.dumps(verify_place(args.source_project,args.original_project,args.verify_place)))
    else:
        if None in (args.original_owner_host,args.original_author_537,args.out):
            a.error("original inputs and out required")
        print(json.dumps(select(args.source_project,args.original_owner_host,args.original_author_537,args.out)))

if __name__=="__main__":main()
