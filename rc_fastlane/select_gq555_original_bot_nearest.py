#!/usr/bin/env python3
"""RC31 source-select ONE original BotActors, reusing verified #555 author patch.

Private pre-merge and authenticated RC build only. Changes no other source;
no independent AI/Game/Combat, no main or Publish operation.
"""
import argparse, copy, hashlib, importlib.util, json, os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_GQ555_HEAD="cd7d2cd6b39c7d5531a2b2d2437a523a6d09e32d"
AUTHOR_PATCH_BLOB="b176a76833d88b8ac4231965e47e8950d38776e4"
BOT_KEY=("ServerScriptService","EGGRUMBLE_BotActors")
REQUIRED={"EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_BotActors",
          "EGGRUMBLE_SwarmCombat","EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_MatchResultService"}

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def scan(project:Path):
    data=json.loads(project.read_text(encoding="utf-8"))
    found={}
    def traverse(node,prefix=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            if not isinstance(child,dict):raise ValueError("RED nonobject source manifest")
            key=prefix+(name,)
            if "$path" in child:
                if set(child)!={"$path"}:raise ValueError("RED nonunique source path")
                file=(project.parent/child["$path"]).resolve(strict=True)
                if key in found:raise ValueError("RED duplicate script path")
                found[key]=file
            else:traverse(child,key)
    traverse(data["tree"])
    if len(found)!=31 or len({route[-1] for route in found})!=31:
        raise ValueError("RED wrong real RC31 mapped source count")
    if not REQUIRED.issubset({route[-1] for route in found}):
        raise ValueError("RED original game/AI/neutral/score authority lost")
    if BOT_KEY not in found or sum(k[-1]=="EGGRUMBLE_BotActors" for k in found)!=1:
        raise ValueError("RED missing/duplicated actual original AI")
    return data,found

def author_patch(file:Path):
    raw=file.read_bytes()
    if git_blob(raw)!=AUTHOR_PATCH_BLOB:raise ValueError("RED GQ555 original patch source drift")
    spec=importlib.util.spec_from_file_location("gq555_original_patch",file)
    if spec is None or spec.loader is None:raise ValueError("RED missing author module")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def replace_project(base:Path,mapped:dict,bot_file:Path,out:Path):
    original,_=scan(base)
    project=copy.deepcopy(original)
    def visit(node,prefix=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            key=prefix+(name,)
            if "$path" in child:
                path=(bot_file if key==BOT_KEY else mapped[key])
                child["$path"]=os.path.relpath(path,out.parent).replace(os.sep,"/")
            else:visit(child,key)
    visit(project["tree"])
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(project,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,selected=scan(out)
    if len(selected)!=31:raise ValueError("RED selected source count")
    for key,path in mapped.items():
        if key!=BOT_KEY and path.read_bytes()!=selected[key].read_bytes():
            raise ValueError("RED other-author source changed "+"/".join(key))
    assert selected[BOT_KEY].read_bytes()==bot_file.read_bytes()

def actual_sources(place:Path):
    result={}
    for item in ET.parse(place).iter("Item"):
        kind=item.attrib.get("class")
        if kind not in {"Script","LocalScript","ModuleScript"}:continue
        p=item.find("Properties")
        if p is None:raise ValueError("RED real Place script property absent")
        name=p.findtext("string[@name='Name']")
        txt=p.findtext("ProtectedString[@name='Source']")
        if txt is None:txt=p.findtext("string[@name='Source']")
        if not name or txt is None or name in result:raise ValueError("RED Place duplicate/empty source")
        result[name]=(kind,txt.replace("\r\n","\n"))
    if len(result)!=31:raise ValueError("RED real Place not 31-source exact")
    return result

def compare(project:Path,place:Path):
    _,routes=scan(project)
    actual=actual_sources(place)
    if set(actual)!={key[-1] for key in routes}:raise ValueError("RED name map differs")
    for key,path in routes.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript"))
        expected=path.read_text().replace("\r\n","\n")
        if actual[key[-1]]!=(kind,expected):
            raise ValueError("RED source/class mismatch "+"/".join(key))
    return actual

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base31",required=True,type=Path)
    p.add_argument("--author",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--verify-place",type=Path)
    p.add_argument("--verify-off-place",type=Path)
    a=p.parse_args()
    owner=author_patch(a.author)
    _,orig=scan(a.base31)
    on,off=owner.apply(orig[BOT_KEY].read_bytes())
    if off!=orig[BOT_KEY].read_bytes():raise ValueError("RED bot OFF source drift")
    a.out.mkdir(parents=True,exist_ok=True)
    on_file=a.out/"EGGRUMBLE_BotActors_GQ555_ON.luau"
    off_file=a.out/"EGGRUMBLE_BotActors_GQ555_OFF.luau"
    on_file.write_bytes(on);off_file.write_bytes(off)
    on_project=a.out/"GQ555_ON.project.json"
    off_project=a.out/"GQ555_OFF.project.json"
    replace_project(a.base31,orig,on_file,on_project)
    replace_project(a.base31,orig,off_file,off_project)
    if a.verify_place or a.verify_off_place:
        if not a.verify_place or not a.verify_off_place:
            raise ValueError("RED ON and OFF real Rojo must both be checked")
        on_sources=compare(on_project,a.verify_place)
        off_sources=compare(off_project,a.verify_off_place)
        delta={n for n in on_sources if on_sources[n]!=off_sources[n]}
        if delta!={"EGGRUMBLE_BotActors"}:
            raise ValueError("RED more than one author source changed")
        receipt={"candidate":"GQ555_ORIGINAL_BOT_NEAREST_SINGLE_AUTHORITY",
            "original_patch_head":AUTHOR_GQ555_HEAD,
            "base31_project":str(a.base31),
            "script_count":31,"on_source_class_exact":31,"off_source_class_exact":31,
            "unchanged_original_author_sources":30,"source_diff":{"EGGRUMBLE_BotActors":"ON_ONLY"},
            "original_off_recovered":True,
            "on_place_bytes":a.verify_place.stat().st_size,
            "on_place_sha256":hashlib.sha256(a.verify_place.read_bytes()).hexdigest(),
            "off_place_bytes":a.verify_off_place.stat().st_size,
            "off_place_sha256":hashlib.sha256(a.verify_off_place.read_bytes()).hexdigest(),
            "studio_android_fun_owner":"NO_GO",
            "publication_authorized":False}
        (a.out/"GQ555_RC31_SOURCE_SELECTION_RECEIPT.json").write_text(
            json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        print(json.dumps(receipt,ensure_ascii=False))
    else:
        print("GQ555_RC31_ONLY_BOT_ACTORS_SOURCE_SELECTED_30_OF_31_PRESERVED")

if __name__=="__main__":
    main()
