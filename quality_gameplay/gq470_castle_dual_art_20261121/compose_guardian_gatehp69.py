#!/usr/bin/env python3
"""Nonformal two-author 69-source compatibility candidate: #957 + #958.
Neither original author branch nor certified formal RC is modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF="OFF69_GUARDIAN_GATEHP"
TARGETS={
    "ServerScriptService/EGGRUMBLE_CastleGuardianRuntime":{
        "rel":"selected_sources/ServerScriptService/EGGRUMBLE_CastleGuardianRuntime.luau",
        "old":"3b8cf7e9b939213633fde964d81bb5e9508e4fe467ef932ddad0bfbe270bd96b",
        "new":"8803926d71bdc233213a8bdad7589a5c0670061a7be898028872faac8f0fb2da",
        "who":"guardian"},
    "ServerScriptService/EGGRUMBLE_CastleSiegeBridge":{
        "rel":"sources/ServerScriptService/EGGRUMBLE_CastleSiegeBridge.luau",
        "old":"14f0f291ae9e8d14d525be0c1626e964aff52398b002c2ef1051c5bd1e4f72c5",
        "new":"f3a2806ed683615dc76d84eb1856cb37948b4dce81798e5373f054cb52937541",
        "who":"gatehp"},
}
def digest(blob):
    return hashlib.sha256(blob).hexdigest()
def assert_safe(cond,code):
    if not cond: raise ValueError("RED_GQ470_DUAL_"+code)
def selected(root):
    project=json.loads((root/PROJECT).read_text())
    paths={}
    def walk(node,route=""):
        if not isinstance(node,dict):return
        if "$path" in node:
            p=(root/node["$path"]).resolve()
            assert_safe(p.is_relative_to(root.resolve()) and p.is_file(),"SOURCE_PATH")
            assert_safe(route not in paths,"DUPLICATE")
            paths[route]=p
        for k,v in node.items():
            if not k.startswith("$"):walk(v,route+"/"+k if route else k)
    walk(project["tree"])
    return paths
def compose(original,guardian,gatehp):
    paths=selected(original)
    rec=json.loads((original/RECEIPT).read_text())
    assert_safe(rec.get("official_branch")=="rc/p0d-s1-kids-rc01" and
                rec.get("build_head")==BASE and rec.get("canonical_build") is True,
                "FORMAL_BASE")
    assert_safe(rec.get("selected_source_count")==69 and len(paths)==69,"69_COUNT")
    assert_safe(set(paths)==set(rec["source_hashes"])==set(rec["source_classes"]),
                "SOURCE_SET")
    assert_safe(len(TARGETS)==2,"TWO_TARGETS")
    for route,path in paths.items():
        assert_safe(digest(path.read_bytes())==rec["source_hashes"][route],
                    "OFFICIAL_SOURCE_HASH_"+route)
    gmanifest=json.loads((guardian/"SOURCE_SELECT_MANIFEST.json").read_text())
    assert_safe(gmanifest["base_rc"]==BASE and
                gmanifest["selected_route"] in TARGETS and
                gmanifest["source_sha256_new"]==TARGETS[gmanifest["selected_route"]]["new"] and
                gmanifest["selected_changes"]==1 and gmanifest["unchanged_selected"]==68,
                "GUARDIAN_AUTHOR_PROVENANCE")
    gater=json.loads((gatehp/RECEIPT).read_text())
    assert_safe(gater.get("build_head")==BASE and
                gater.get("gq470_castle_gatehp_matte",{}).get(
                  "other_selected_sources_byte_exact")==68 and
                gater["gq470_castle_gatehp_matte"].get("authority_changed") is False,
                "GATEHP_AUTHOR_PROVENANCE")
    off=original/OFF
    assert_safe(not off.exists(),"OFF_ALREADY_EXISTS")
    off.mkdir()
    shutil.copytree(original/"sources",off/"sources")
    for name in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copyfile(original/name,off/name)
    for route,spec in TARGETS.items():
        source_root=guardian if spec["who"]=="guardian" else gatehp
        source=(source_root/spec["rel"]).read_bytes()
        assert_safe(digest(source)==spec["new"],"PINNED_A_SOURCE_"+route)
        assert_safe(rec["source_hashes"][route]==spec["old"],"BASE_SOURCE_"+route)
        assert_safe(rec["source_classes"][route]=="ModuleScript","BASE_CLASS_"+route)
        paths[route].write_bytes(source)
        rec["source_hashes"][route]=spec["new"]
    unchanged={route for route,path in paths.items() if
               path.read_bytes()!=selected(off)[route].read_bytes()}
    assert_safe(unchanged==set(TARGETS),"EXACT_TWO_SOURCE_DIFF")
    assert_safe((original/PROJECT).read_bytes()==(off/PROJECT).read_bytes(),
                "PROJECT_DIFF")
    rec["gq470_dual_candidate_957_958"]={
      "only_selected_routes_changed":sorted(TARGETS),
      "unchanged_selected_sources":67,
      "all_selected_routes_and_classes_unchanged":True,
      "original_formal_head":BASE,
      "guardian_pr":957,"guardian_a_source_sha":TARGETS[
       "ServerScriptService/EGGRUMBLE_CastleGuardianRuntime"]["new"],
      "gatehp_pr":958,"gatehp_a_source_sha":TARGETS[
       "ServerScriptService/EGGRUMBLE_CastleSiegeBridge"]["new"],
      "original_place_rollback":OFF,
      "unverified_in_studio":True,
      "android_15m":"NOT_TESTED","owner_accepted":False,
      "formal_integrated":False,"no_new_server_authority":True
    }
    (original/RECEIPT).write_text(json.dumps(rec,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ470_957_958_DUAL_SOURCE_EXACT_2_OF_69_PASS", ",".join(sorted(TARGETS)))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--guardian",type=Path,required=True)
    ap.add_argument("--gatehp",type=Path,required=True)
    args=ap.parse_args()
    compose(args.base,args.guardian,args.gatehp)
