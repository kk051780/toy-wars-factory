#!/usr/bin/env python3
"""Source-select existing 952 centered reticle + 949 matte impact into ONE REAL69.

Integration-only A candidate; inputs immutable; author branches and formal RC untouched.
A native/Rojo source success is not Studio/FPS/ART/FUN or owner acceptance.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,pathlib,shutil

FORMAL="e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel"
OLD="d378d6a356b9462c99deddc19b4393d79bf113225047a057658d1782e1e8a32e"
RETICLE="ae43ff66055698dd72ccf6beb2aa3fcc61080e49343055b3d8cd3594831c0b1c"
IMPACT="860a8d60e7e577b7e5f01ca08b901290ec0a040beec63a46c66993ab71187dd3"
COMBINED="b37194cb97357cf7290fc6eb3f94396720265b15915ad588d2bd05b9b870e833"
MARK_RETICLE="GQ470_FB015_CONFIRMED_HIT_CENTERED_MATTE_RETICLE_REAL69_20261121"
MARK_IMPACT="GQ470_FB015_CONFIRMED_HIT_MATTE_STREAK_REAL69_20261121"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def need(ok,code):
    if not ok:raise ValueError("RED_COMBATFEEL_COMPOSITE_"+code)
def selected(root:pathlib.Path)->dict:
    data=json.loads((root/PROJECT).read_text())
    result={}
    def visit(node,route=""):
        if not isinstance(node,dict):return
        if "$path" in node:
            p=(root/node["$path"]).resolve()
            need(p.is_relative_to(root.resolve()) and p.is_file(),"PATH")
            need(route not in result,"DUPLICATE")
            result[route]=p
        for name,value in node.items():
            if not name.startswith("$"):visit(value,route+"/"+name if route else name)
    visit(data["tree"])
    need(len(result)==69 and TARGET in result and result[TARGET].name.endswith(".client.luau"),"SELECTED_69")
    return result

def apply(official:pathlib.Path,reticle:pathlib.Path,patch:pathlib.Path,out:pathlib.Path)->dict:
    need(official.is_dir() and reticle.is_dir() and patch.is_file() and not out.exists(),"INPUTS")
    base=selected(official);on=selected(reticle)
    need(set(base)==set(on),"SOURCE_ROUTES")
    r0=json.loads((official/RECEIPT).read_text())
    r1=json.loads((reticle/RECEIPT).read_text())
    need(r0.get("build_head")==FORMAL and r0.get("canonical_build") is True,"FORMAL_BASE")
    need(r1.get("build_head")==FORMAL and r1.get("canonical_build") is True,"RETICLE_BASE")
    need(len(r0.get("source_hashes",{}))==len(r1.get("source_hashes",{}))==69,"RECEIPT")
    for key in base:
        b=base[key].read_bytes();c=on[key].read_bytes()
        need(sha(b)==r0["source_hashes"].get(key),"ORIGINAL_HASH")
        need(sha(c)==r1["source_hashes"].get(key),"RETICLE_HASH")
        if key!=TARGET:need(b==c,"SIBLING_SOURCE_DRIFT")
    need(sha(base[TARGET].read_bytes())==OLD,"ORIGINAL_TARGET")
    need(sha(on[TARGET].read_bytes())==RETICLE,"SIBLING_TARGET")
    need(sha((official/PROJECT).read_bytes())==sha((reticle/PROJECT).read_bytes()),"PROJECT_DRIFT")
    need((official/"EGGRUMBLE_REAL69_PRIVATE.rbxlx").stat().st_size==798390,"OFFICIAL_PLACE_BYTES")
    need((reticle/"EGGRUMBLE_REAL69_PRIVATE.rbxlx").stat().st_size==798847,"RETICLE_PLACE_BYTES")
    spec=importlib.util.spec_from_file_location("p949",patch)
    need(spec and spec.loader,"PATCH_LOAD")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    need(m.OLD_SHA==OLD and m.FEATURE==MARK_IMPACT and m.TARGET==TARGET,"AUTHOR_SCOPE")
    m.self_test()
    text=on[TARGET].read_text(encoding="utf-8")
    need(text.count(MARK_RETICLE)==1 and MARK_IMPACT not in text,"RETICLE_MARKER")
    candidate=m.transform(text)
    raw=candidate.encode("utf-8")
    need(sha(raw)==COMBINED and len(raw)==28097,"COMBINED_SOURCE_HASH")
    need(candidate.count(MARK_RETICLE)==candidate.count(MARK_IMPACT)==1,"BOTH_MARKERS")
    need("local IMPACT_WINDOW=.115" in candidate and "local RECENT_CD=.12" in candidate,"HIT_GUARDS")
    need("if reduced() or player:GetAttribute(\"EGGRUMBLE_Eliminated\")==true" in candidate,"ELIM_FENCE")
    shutil.copytree(reticle,out)
    route_map=selected(out)
    route_map[TARGET].write_bytes(raw)
    diff={k for k in base if base[k].read_bytes()!=route_map[k].read_bytes()}
    need(diff=={TARGET},"ONE_SOURCE_ONLY")
    receipt=json.loads((out/RECEIPT).read_text())
    receipt["source_hashes"][TARGET]=COMBINED
    receipt["gq470_hit_composite_949_952"]={
       "source_profile":"REAL69","formal_head":FORMAL,"author952_source_sha256":RETICLE,
       "author949_impact_source_sha256":IMPACT,
       "combined_sha256":COMBINED,"selected_modified":1,"other_selected_exact":68,
       "added_client_frames":2,"new_world_parts":0,"new_remotes":0,
       "owner_accepted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
       "human_art":"NOT_TESTED"}
    (out/RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    q=receipt["gq470_hit_composite_949_952"]
    (out/"GQ470_COMBATFEEL_COMPOSITE_A_QA.json").write_text(json.dumps(q,ensure_ascii=False,indent=2)+"\n")
    return q

def self_test():
    require=[len(FORMAL)==40,len(OLD)==64,len(RETICLE)==64,len(IMPACT)==64,len(COMBINED)==64,RETICLE!=COMBINED]
    need(all(require),"CONSTANTS")
    print("GQ470_COMPOSITE_CONSTANT_SCOPE_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--official",type=pathlib.Path)
    p.add_argument("--reticle",type=pathlib.Path)
    p.add_argument("--patch949",type=pathlib.Path)
    p.add_argument("--out",type=pathlib.Path)
    args=p.parse_args()
    if args.self_test:self_test()
    else:
        need(args.official and args.reticle and args.patch949 and args.out,"ARGS")
        print(json.dumps(apply(args.official,args.reticle,args.patch949,args.out),ensure_ascii=False,indent=2))
