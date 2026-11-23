#!/usr/bin/env python3
"""Port pinned PR797's actual storm fix to existing REAL65; fail closed on drift."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"quality_gameplay/gq8_real63_intake_20261119"))
from compose_real63 import flatten,sha
ROUTE=("ServerScriptService","EGGRUMBLE_RealmBattleCore")
HELPER_BLOB="e8665138825488256aaa0875c55b1c623d9887b8"
def blob(d):return hashlib.sha1(b"blob "+str(len(d)).encode()+b"\0"+d).hexdigest()
def check(x,k):
 if not x:raise ValueError("RED_REAL65_STORM_"+k)
def run(project,receipt_path,helper_file):
 check(blob(helper_file.read_bytes())==HELPER_BLOB,"AUTHOR797_DRIFT")
 spec=importlib.util.spec_from_file_location("original_pr797",helper_file)
 helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 check(helper.ROUTE==ROUTE and helper.SOURCE_BLOB=="1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1","ORIGINAL_PROVENANCE")
 doc,src=flatten(project)
 print("GQ8_REAL65_ACTUAL_REALM_ROUTE_CANDIDATES",[(("/".join(k)),v[0]) for k,v in src.items() if "Realm" in k[-1] or "LandSea" in k[-1] or "Weather" in k[-1] or "Storm" in k[-1]])
 check(len(src)==65 and ROUTE in src and src[ROUTE][0]=="ModuleScript","REAL65_EXPECT_INERT_MODULE")
 current=src[ROUTE][1]
 exact_author=helper.blob_sha(current)==helper.SOURCE_BLOB
 body=current.decode("utf8")
 # PR797's two original code anchors must still be present exactly once,
 # even when another author has added unrelated Realm functionality.
 if body.count(helper.PATCHED_TRANSITION)==1 and body.count(helper.PATCHED_STRIKE)==1:
  check(body.count(helper.ORIGINAL_TRANSITION)==0 and body.count(helper.ORIGINAL_STRIKE)==0,
        "MIXED_ALREADY_PATCHED_REALM")
  fixed=current
  state="ALREADY_SOURCE_PATCHED_REQUIRE_ONLY_CLASS_ACTIVATION"
 else:
  check(body.count(helper.ORIGINAL_TRANSITION)==1 and body.count(helper.ORIGINAL_STRIKE)==1,
        "REALM_ANCHORS_CHANGED")
  fixed=helper.patch_source(current,verify_blob=exact_author)
  state="EXACT_AUTHOR" if exact_author else "SOURCE_DRIFT_ANCHOR_LOCKED"
 print("GQ8_REAL65_CURRENT_REALM_PROVENANCE",{"git_blob":helper.blob_sha(current),"author_exact":exact_author,"patch_mode":state,"original_len":len(current),"patched_len":len(fixed)})
 node=doc["tree"]["ServerScriptService"]["EGGRUMBLE_RealmBattleCore"]
 check(set(node)=={"$path"},"SOURCE_ROUTE_AMBIGUOUS")
 path=(project.parent/node["$path"]).resolve(strict=True)
 check(path==project.parent.resolve()/"sources/ServerScriptService/EGGRUMBLE_RealmBattleCore.luau","ROUTE_PATH")
 active_path=path.with_name("EGGRUMBLE_RealmBattleCore.server.luau")
 check(not active_path.exists(),"ACTIVE_REALM_SCRIPT_COLLISION")
 receipt=json.loads(receipt_path.read_text(encoding="utf8"))
 check(receipt["new_selected_source_count"]==65 and receipt["original_real63_byte_unchanged"]==58 and len(receipt["sources"])==65,"PARENT_RECEIPT")
 indexed={tuple(r["route"].split("/")):r for r in receipt["sources"]}
 check(set(indexed)==set(src),"RECEIPT_ROUTES")
 for key,(cls,body) in src.items():
  r=indexed[key]
  check(r["sha256"]==sha(body) and r["bytes"]==len(body) and r["class"]==cls,"PREPATCH_DRIFT_"+"/".join(key))
 active_path.write_bytes(fixed)
 path.unlink()
 node["$path"]="sources/ServerScriptService/EGGRUMBLE_RealmBattleCore.server.luau"
 project.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 _,new=flatten(project)
 check(len(new)==65 and set(new)==set(src),"SOURCE_COUNT")
 for key in src:
  check(new[key]==(("Script",fixed) if key==ROUTE else src[key]),"SOURCE_DRIFT_"+"/".join(key))
 indexed[ROUTE]["sha256"]=sha(fixed);indexed[ROUTE]["bytes"]=len(fixed);indexed[ROUTE]["class"]="Script"
 receipt["original_real63_byte_unchanged"]=57
 receipt["patched_existing_routes"].append("/".join(ROUTE))
 receipt["realm_storm797"]={"feature_id":"GQ8_REALM_STORM_PHASE_FENCE_20261118","reused_author_pr":797,"helper_git_blob":HELPER_BLOB,"original_source_blob":helper.SOURCE_BLOB,"actual_real65_source_blob":helper.blob_sha(current),"author_source_exact":exact_author,"patch_mode":state,"only_changed_route":"/".join(ROUTE),"repaired_class":"ModuleScript -> Script (server auto-start)","other_original_real65_sources_byte_exact":64,"rollback":"prior official REAL65 source/Place, OFF63 exact","studio_2client":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO"}
 receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_REAL65_STORM797_FIXED65_WITH64_UNCHANGED_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--project",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 p.add_argument("--author-helper",type=Path,required=True)
 a=p.parse_args();run(a.project,a.receipt,a.author_helper)
