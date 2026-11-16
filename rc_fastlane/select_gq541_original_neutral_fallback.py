#!/usr/bin/env python3
"""Source-select ONLY original #541 author's exact neutral melee fallback into the
already assembled 31-source EGGRUMBLE V3 companion. Never invent a second AI.
This script is read-only on original author sources and fails closed on drift.
"""
from __future__ import annotations
import argparse, ast, copy, hashlib, json, os, xml.etree.ElementTree as ET
from pathlib import Path

OLD_AUTHOR_COMPOSER_BLOB="032c4de1560a4f5396b06905fcdc3bcd0b764975"
NEW_AUTHOR_541_COMPOSER_BLOB="896aabf81113c02ac7a74909d579ffd20beb2b57"
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
ORIGINAL_MARK="nearest.humanoid:TakeDamage(Melee.DAMAGE)"
CURRENT_MARK="candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"
TYPES={"Script","ModuleScript","LocalScript"}

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def author_movement_section(path:Path,expected_blob:str,needle:str)->str:
    raw=path.read_bytes()
    if gitblob(raw)!=expected_blob:
        raise ValueError("RED_ORIGINAL_AUTHOR_COMPOSER_SHA "+str(path))
    tree=ast.parse(raw.decode("utf-8"))
    matches=[]
    for f in tree.body:
        if isinstance(f,ast.FunctionDef) and f.name=="patch":
            for n in ast.walk(f):
                if isinstance(n,ast.Assign) and any(
                    isinstance(t,ast.Name) and t.id=="b" for t in n.targets):
                    if isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
                        if needle in n.value.value:matches.append(n.value.value)
    if len(matches)!=1:
        raise ValueError("RED_AUTHOR_SELECTION_NOT_UNIQUE "+str(path))
    section=matches[0]
    if section.count(needle)!=1 or section.count("meleeRays+=1")!=1:
        raise ValueError("RED_AUTHOR_SOURCE_UNSAFE")
    return section

def flatten(project:Path):
    project=project.resolve(strict=True)
    tree=json.loads(project.read_text(encoding="utf-8"))
    found={}
    def walk(node,prefix=()):
        for key,value in node.items():
            if key.startswith("$"):continue
            if not isinstance(value,dict):
                raise ValueError("RED_PROJECT_INVALID")
            current=prefix+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or current in found:
                    raise ValueError("RED_MAPPING_COLLISION")
                found[current]=(project.parent/value["$path"]).resolve(strict=True)
            else:
                walk(value,current)
    walk(tree["tree"])
    if len({x[-1] for x in found})!=len(found):raise ValueError("RED_DUPLICATE_SCRIPT")
    return tree,found

def select(input_project:Path,old_author:Path,new_author:Path,output:Path)->dict:
    input_project=input_project.resolve(strict=True)
    output=output.resolve()
    if output.exists():raise ValueError("RED_NO_OVERWRITE")
    tree,sources=flatten(input_project)
    if len(sources)!=31 or SWARM not in sources:
        raise ValueError("RED_NOT_CANONICAL_31")
    old=author_movement_section(old_author,OLD_AUTHOR_COMPOSER_BLOB,ORIGINAL_MARK)
    new=author_movement_section(new_author,NEW_AUTHOR_541_COMPOSER_BLOB,CURRENT_MARK)
    old_bytes=sources[SWARM].read_bytes()
    swarm=old_bytes.decode("utf-8")
    if swarm.count(old)!=1 or swarm.count(CURRENT_MARK)!=0:
        raise ValueError("RED_31_SWARM_ALREADY_CHANGED_OR_NOT_ORIGINAL")
    repaired=swarm.replace(old,new,1)
    if repaired.count(CURRENT_MARK)!=1 or repaired.count(ORIGINAL_MARK)!=0:
        raise ValueError("RED_WRONG_SINGLE_SWARM_AUTHORITY")
    if repaired.replace(new,old,1)!=swarm:
        raise ValueError("RED_REVERSE_NOT_EXACT")
    for marker in ("SpawnPacing.step(","EncounterFair.chooseIndex(",
                   "session.neutralBudget:acquire(","session.isCurrentHuman(p)"):
        if repaired.count(marker)!=swarm.count(marker) or repaired.count(marker)==0:
            raise ValueError("RED_NEUTRAL_OWNER_LOST "+marker)
    if repaired.count("Melee.commit(")!=1 or repaired.count("Melee.MAX_RAYS_PER_TICK")<1:
        raise ValueError("RED_HIT_OR_GLOBAL_BUDGET_DRIFT")
    outdir=output.parent
    outdir.mkdir(parents=True,exist_ok=True)
    repaired_file=outdir/"EGGRUMBLE_SwarmCombat_541.luau"
    if repaired_file.exists():raise ValueError("RED_SWARM_OVERWRITE")
    repaired_file.write_text(repaired,encoding="utf-8")
    project=copy.deepcopy(tree)
    project["name"]="EGGRUMBLE_V3_GQ541_SOURCE_SELECTED_31_PRIVATE_OR_RC_PROPOSAL"
    def map_paths(node,prefix=()):
        for name,value in node.items():
            if name.startswith("$"):continue
            route=prefix+(name,)
            if "$path" in value:
                selected=repaired_file if route==SWARM else sources[route]
                value["$path"]=os.path.relpath(selected,outdir).replace(os.sep,"/")
            else: map_paths(value,route)
    map_paths(project["tree"])
    output.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=flatten(output)
    if len(mapped)!=31 or set(mapped)!=set(sources):raise ValueError("RED_SOURCE_COUNT")
    for key,orig in sources.items():
        expected=repaired.encode("utf-8") if key==SWARM else orig.read_bytes()
        if mapped[key].read_bytes()!=expected:
            raise ValueError("RED_OTHER_AUTHOR_CHANGED "+"/".join(key))
    receipt={
        "feature":"GQ_V3_NEUTRAL_MELEE_NEAREST_ELIGIBLE_FALLBACK_541",
        "official_source_selection":True,
        "source_base":"Original official author31 generated ON before #541",
        "source_count":31,
        "original_other_source_bytes_exact":30,
        "changed_script":"ServerScriptService/EGGRUMBLE_SwarmCombat",
        "old_swarm_sha256":digest(old_bytes),
        "selected_swarm_sha256":digest(repaired.encode("utf-8")),
        "original_author_head_541":"6fc0261d21a3aa260fa7bcf19b1b177d4994570a",
        "original_author_blob_sha":NEW_AUTHOR_541_COMPOSER_BLOB,
        "source_only_before_true_rojo":True,
        "engine_verified":False,
        "owner_accepted":False,
    }
    (outdir/"GQ541_SELECTED_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def verify_place(project:Path,place:Path,original_project:Path)->dict:
    _,expected=flatten(project)
    _,base=flatten(original_project)
    if len(expected)!=31 or set(expected)!=set(base):
        raise ValueError("RED_PLACE_MAP_MISMATCH")
    xml=ET.fromstring(place.read_bytes())
    found={}
    for node in xml.iter("Item"):
        kind=node.attrib.get("class")
        if kind not in TYPES:continue
        props=node.find("Properties")
        if props is None:raise ValueError("RED_XML_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or name in found or source is None:raise ValueError("RED_XML_DUPLICATE")
        found[name]=(kind,source.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={x[-1] for x in expected}:
        raise ValueError("RED_XML_MISSING_SCRIPT")
    for route,p in expected.items():
        kind=("Script" if p.name.endswith(".server.luau") else
              "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(kind,p.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_OR_CLASS "+route[-1])
        if route!=SWARM and p.read_bytes()!=base[route].read_bytes():
            raise ValueError("RED_NONOWNER_BYTES "+route[-1])
    if expected[SWARM].read_bytes()==base[SWARM].read_bytes():
        raise ValueError("RED_NO_SWARM_CHANGE")
    return {"script_count":31,"rojo_exact_scripts":31,
            "other_sources_byte_exact":30,
            "place_bytes":place.stat().st_size,
            "place_sha256":digest(place.read_bytes()),
            "formal_rc_write":False,"studio_android_verified":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-project",type=Path)
    p.add_argument("--original-author",type=Path)
    p.add_argument("--new-author",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--verify-place",type=Path)
    p.add_argument("--original-project",type=Path)
    args=p.parse_args()
    if args.verify_place:
        if not args.source_project or not args.original_project:p.error("verify requires both project paths")
        print(json.dumps(verify_place(args.source_project,args.verify_place,args.original_project),indent=2))
    else:
        if not args.source_project or not args.original_author or not args.new_author or not args.out:p.error("select requires source and author paths")
        print(json.dumps(select(args.source_project,args.original_author,args.new_author,args.out),indent=2))
