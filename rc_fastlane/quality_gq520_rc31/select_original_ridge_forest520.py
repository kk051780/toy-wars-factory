#!/usr/bin/env python3
"""GQ520: reuse immutable author's TWO FIELD/ITEM collision patches on ONE current RC31 Host.
This source selector has NO new game logic. Geometry expectations and native policy
are loaded from the original #520 author's immutable Python/Luau fixtures.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from importlib.machinery import SourceFileLoader

N=31
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
AUTHOR_SHA="b2b89d7eaed2bdeeee163eb16d05d541d002e800"
ORIGINAL_HOST_SHA="7162b209bf67b74a71553217f3f744e072a0365d"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def source_map(project:Path):
    mod=SourceFileLoader("map541_gq520","rc_fastlane/select_gq541_original_neutral_fallback.py").load_module()
    return mod.flatten(project)

def original_modules(author:Path):
    root=author.resolve(strict=True)
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    load=lambda name:SourceFileLoader("gq520_"+name,str((root/(name+".py")).resolve(strict=True))).load_module()
    return load("patch_ridge"),load("forest_dash_overlay"),load("forest_dash_native"),load("make_native_corridor")

def author_inputs(author:Path):
    original_root=author.resolve(strict=True).parents[1]/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
    return ((original_root/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8"),
            (original_root/"EGGRUMBLE_RaidItemIntake.luau").read_text(encoding="utf-8"))

def selected_host(source:str,author:Path):
    ridge,forest,native,corr=original_modules(author)
    original,item=author_inputs(author)
    if ridge.git_blob(original)!=ORIGINAL_HOST_SHA or ridge.ORIGINAL_GIT_BLOB!=ORIGINAL_HOST_SHA:
        raise ValueError("RED original author source blob mismatch")
    if source.count(ridge.OLD)!=1 or ridge.NEW in source or source.count(forest.OLD_FOREST)!=1 or forest.NEW_FOREST in source:
        raise ValueError("RED original #520 ridge/tree already patched or source drift")
    if source.count('local rowZ=if mode=="TEAM" then {338,506,610} else {338,448,676}')!=1:
        raise ValueError("RED already adopted original #523 field egg row lost")
    if "player.Character~=character" not in source:
        raise ValueError("RED official original #551 stale carrier guard lost")
    if ridge.patch_author_host(original,item).count(ridge.NEW)!=1:
        raise ValueError("RED original GQ520 ridge source generator mismatch")
    geo=forest.forest_report()
    if (geo["before_embedded_tree_ids"]!=[1] or geo["after_embedded_tree_ids"]!=[]
        or not geo["other_tree_positions_preserved"] or not geo["all_trees_preserved"]):
        raise ValueError("RED original GQ520 tree source geometry")
    a=source.replace(ridge.OLD,ridge.NEW,1)
    b=a.replace(forest.OLD_FOREST,forest.NEW_FOREST,1)
    if b.replace(forest.NEW_FOREST,forest.OLD_FOREST,1).replace(ridge.NEW,ridge.OLD,1)!=source:
        raise ValueError("RED rollback not exact two original hunk inverses")
    return b,{"ridge_shield_before_embedded":ridge.collision_report()["before_embedded_in_collidable_ridge"],
             "ridge_passage_studs":ridge.collision_report()["after_open_passage_studs"],
             "dash_tree_before":geo["before_embedded_tree_ids"],
             "dash_tree_after":geo["after_embedded_tree_ids"]}

def native_fixture(original:str,after:str,author:Path):
    ridge,forest,original_vm,corr=original_modules(author)
    _,item=author_inputs(author)
    old_tree=original_vm.extract_forest(original)
    new_tree=original_vm.extract_forest(after)
    fixed=original_vm.extract_item_list(item)
    pos=original_vm.extract_item_position_source(item)
    def section(name,body):
        return ("local function "+name+"()\n local spawned={}\n"
                " local function block(parent,name,pos,size,color)\n"
                "  return createPart(spawned,parent,name,pos,size,color)\n"
                " end\n"+body+"\n return spawned\nend\n")
    item_func=("local function itemPositions(mode)\n"
               " local session={mode=mode}\n local origin=root\n"+pos+"\n return points\nend\n")
    # All expected collision values/tests are the original #520 author's VM body.
    forest_native=(original_vm.VEC+fixed+"\n"+item_func+
      section("createOldForest",old_tree)+section("createNewForest",new_tree)+
      section("createOldRidge",ridge.OLD)+section("createNewRidge",ridge.NEW)+original_vm.TEST)
    # Additional original #520 corridor/LOS fixture, not a second game source.
    def ridge_scope(name,body):
        return ("local function "+name+"()\n local spawned={}\n"
                " local function block(world,label,pos,size,color)\n"
                "  return makeBlock(spawned,world,label,pos,size,color)\n"
                " end\n"+body+"\n return spawned\nend\n")
    corridor_native=(corr.SOURCE_HEADER+ridge_scope("oldWorld",ridge.OLD)+
                     ridge_scope("newWorld",ridge.NEW)+corr.SOURCE_FOOTER)
    return forest_native,corridor_native

def prepare(base:Path,out:Path,author:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if base==out or out.parent!=base.parent or out.exists():
        raise ValueError("RED refuse original overwrite or preexisting generated project")
    tree,src=source_map(base)
    if len(src)!=N or HOST not in src:raise ValueError("RED missing current singleton Host or 31 scripts")
    before=src[HOST].read_text(encoding="utf-8")
    after,geo=selected_host(before,author)
    target=out.parent/"GQ520_ORIGINAL_RIDGE_FOREST_HOST.server.luau"
    if target.exists():raise ValueError("RED refuse existing generated Host")
    target.write_text(after,encoding="utf-8")
    native1,native2=native_fixture(before,after,author)
    (out.parent/"GQ520_ORIGINAL_FOREST_ITEM_NATIVE.luau").write_text(native1,encoding="utf-8")
    (out.parent/"GQ520_ORIGINAL_RIDGE_CORRIDOR_NATIVE.luau").write_text(native2,encoding="utf-8")
    selected=copy.deepcopy(tree)
    selected["tree"][HOST[0]][HOST[1]]["$path"]=target.name
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,new=source_map(out)
    altered=[key for key in src if key not in new or src[key].read_bytes()!=new[key].read_bytes()]
    if len(new)!=N or set(new)!=set(src) or altered!=[HOST]:
        raise ValueError("RED changed non-Host author source")
    meta={"source_count":N,"author_sha":AUTHOR_SHA,"single_host_changed":True,
          "other_30_sources_byte_exact":True,"two_original_520_hunks_reverse_exact":True,
          "original_523_field_egg_rows_preserved":True,"terrain_geo_source_only":geo,
          "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO","formal_adoption":False,
          "old_host_sha256":sha(before.encode()),"selected_host_sha256":sha(after.encode())}
    (out.parent/"GQ520_RIDGE_FOREST_RC31_RECEIPT.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ520_SINGLE_HOST_ORIGINAL_RIDGE_FOREST_OTHER30_ROLLBACK_EXACT_PASS")

def verify(base:Path,out:Path,place:Path,author:Path):
    _,old=source_map(base)
    _,src=source_map(out)
    expected,_=selected_host(old[HOST].read_text(encoding="utf-8"),author)
    altered=[key for key in old if key not in src or old[key].read_bytes()!=src[key].read_bytes()]
    if len(src)!=N or altered!=[HOST] or src[HOST].read_text(encoding="utf-8")!=expected:
        raise ValueError("RED unexpected author hunk, or other sources changed")
    found={}
    for el in ET.parse(place).iter("Item"):
        cls=el.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=el.find("Properties")
        if props is None:raise ValueError("RED no script properties")
        name=props.findtext("string[@name='Name']")
        text=props.findtext("ProtectedString[@name='Source']")
        if text is None:text=props.findtext("string[@name='Source']")
        if not name or text is None or name in found:raise ValueError("RED duplicate/missing script source")
        found[name]=(cls,text.replace("\r\n","\n"))
    if len(found)!=N or set(found)!={key[-1] for key in src}:
        raise ValueError("RED script inventory/class missing")
    for key,p in src.items():
        cls="Script" if p.name.endswith(".server.luau") else "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript"
        if found[key[-1]]!=(cls,p.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED script Class/Source not exact: "+key[-1])
    receipt=out.parent/"GQ520_RIDGE_FOREST_RC31_RECEIPT.json"
    meta=json.loads(receipt.read_text())
    meta.update({"real_rojo_script_class_source_exact":"31/31",
                 "place_bytes":place.stat().st_size,
                 "place_sha256":sha(place.read_bytes())})
    receipt.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print("GQ520_REAL_ROJO31_SOURCE_CLASS_EXACT_PASS",meta["place_bytes"],meta["place_sha256"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["prepare","verify"])
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":prepare(a.base,a.out,a.author)
    else:
        if a.place is None:p.error("--place required for verify")
        verify(a.base,a.out,a.place,a.author)

if __name__=="__main__":main()
