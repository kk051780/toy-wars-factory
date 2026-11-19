#!/usr/bin/env python3
"""Build REAL67 from already composed same-head REAL66 without losing ANY script.

Read exact runtime REAL66 artifact, add ONE Studio-only environmental Script from
real original RC85/86 proven feature flags WCS_F01_C01 only; existing STARRY_PATH_V1 via #879 Realm and
METEOR_FOURTH_V1 via #884 Realm are preserved without duplication. The single official RC branch remains rc/p0d-s1-kids-rc01.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil
from pathlib import Path

ROUTE="ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes"
REL="sources/ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes.server.luau"
FEATURE="GQ8_RC85_WCS_REUSE_STAR_METEOR_REAL67_20261119"
def h(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def ensure(ok:bool,tag:str):
 if not ok:raise ValueError("RED_GQ8_SINGLE_RC_67_"+tag)
def selected(tree:dict)->dict[str,str]:
 out={}
 def walk(node,path):
  for name,item in node.items():
   if name.startswith("$") or not isinstance(item,dict):continue
   route=path+(name,)
   if "$path" in item:
    out["/".join(route)]=item["$path"]
   else:walk(item,route)
 walk(tree,())
 return out
def compose(parent:Path,source:Path,out:Path,sha:str)->None:
 ensure(not out.exists(),"NO_OVERWRITE")
 project=json.loads((parent/"EGGRUMBLE_REAL66.project.json").read_text())
 receipt=json.loads((parent/"REAL66_LEGACY_INTAKE_RECEIPT.json").read_text())
 previous65=json.loads((parent/"REAL65_INTAKE_RECEIPT.json").read_text())
 ensure(previous65.get("rc86_starry_path",{}).get("original_timed_steps")==10,
        "REQUIRE_ALREADY_ADOPTED_STAR_FROM_879")
 ensure(previous65.get("rc86_meteor_shortcut",{}).get("original_timed_segments")==12,
        "REQUIRE_ALREADY_ADOPTED_METEOR_FROM_884")
 prior=selected(project["tree"])
 ensure(len(prior)==66 and receipt["candidate_selected_count"]==66,"PARENT_66")
 ensure(ROUTE not in prior,"NO_DOUBLE_ROUTES")
 ensure(receipt["added_script_count"]==1,"EXPLORATION_ALREADY_SELECTED")
 ensure(receipt["new_route"]=="ServerScriptService/EGGRUMBLE_LegacyExplorationBridge",
        "EXPLORATION_NOT_SELECTED")
 ensure(receipt.get("candidate_head")==sha,"SAME_HEAD_RECEIPT")
 ensure((parent/"EGGRUMBLE_REAL66_PRIVATE.rbxlx").is_file(),"REAL66_PLACE_MISSING")
 parent65={row["route"]:row["sha256"] for row in receipt["original65"]}
 ensure(len(parent65)==65 and len(set(parent65))==65,"NO_LOST_PARENT65")
 for route,loc in prior.items():
  data=(parent/loc).read_bytes()
  if route in parent65:ensure(h(data)==parent65[route],"PARENT65_BYTES_"+route)
  elif route==receipt["new_route"]:
   ensure(h(data)==receipt["new_sha256"] and len(data)==receipt["new_bytes"],"OLD_EXPLORE")
  else:raise ValueError("RED_GQ8_UNKNOWN_PREV_ROUTE_"+route)
 code=source.read_bytes()
 ensure(code.startswith(b"--!strict\n") and FEATURE.encode() in code,"SOURCE_LOCK_FEATURE")
 ensure(b'if not RunService:IsStudio() then return end' in code,"STUDIO_ONLY")
 for key in (b"WCS_F01_C01",b"GQ8_RC86_StarfallPath",b"GQ8_RC86_MeteorShortcut",
             b"AlwaysOpenSafeRoute",b"ExistingStarStepsReused",b"ExistingMeteorSegmentsReused",
             b"not occupied(",b"Workspace.ChildAdded:Connect"):
  ensure(key in code,"OLD_SOURCE_PARITY_"+key.decode())
 shutil.copytree(parent,out)
 location=out/REL
 location.parent.mkdir(parents=True,exist_ok=True)
 location.write_bytes(code)
 new_project=copy.deepcopy(project)
 new_project["name"]="EGGRUMBLE_REAL67_RC85_RC86_REAL65_SINGLE_PRIVATE_STUDIO"
 new_project["tree"]["ServerScriptService"]["EGGRUMBLE_LegacyCanyonRoutes"]={"$path":REL}
 new_sel=selected(new_project["tree"])
 ensure(len(new_sel)==67 and set(new_sel)-set(prior)=={ROUTE},"NO_DUP_GAME_OR_LOSS")
 for route,loc in prior.items():
  ensure(new_sel[route]==loc and (out/loc).read_bytes()==(parent/loc).read_bytes(),
         "SOURCE66_PRESERVE_"+route)
 (out/"EGGRUMBLE_REAL67.project.json").write_text(
  json.dumps(new_project,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 receipt67={
  "schema":"GQ8_SINGLE_CANONICAL_REAL67_WCS_STAR_METEOR_V1",
  "feature_id":FEATURE,
  "formal_branch":"rc/p0d-s1-kids-rc01",
  "candidate_head":sha,
  "source_profile":"EGGRUMBLE_REAL67",
  "source_count":67,
  "parent_formal_source_count":66,
  "parent_all66_byte_identical":True,
  "original65_byte_identical":True,
  "other_existing_source_count_modified":0,
  "new_route":ROUTE,"new_class":"Script",
  "new_file_path":REL,"new_bytes":len(code),"new_sha256":h(code),
  "no_duplicate_game_owners":True,
  "no_damage_score_store_remote":True,
  "original_rc85_artifact_id":14158848286,
  "original_rc86_artifact_id":14161823401,
  "original_source_sha256":{
    "WCS_CrystalCanyon":"17ee851bda13076effdd81de68346f83b8d82366ec7b09de4f7cd938a1b78198",
    "StarfallPath":"f88ec4005a5cb611a2f5acfd7eb67309f2de3799a2f51ebe6208bc2ee3670b35",
    "MeteorFourth":"d4894535eec6f1bb40c1e17a9626e1bcd98a00307ad0db858c4073e6b92b4bd2"
  },
  "ported_policy_flags":["WCS_F01_C01"],
  "preserved_existing_star_path_flag":"STARRY_PATH_V1",
  "preserved_existing_meteor_flag":"METEOR_FOURTH_V1",
  "preserved_existing_star_author":"PR #879 existing EGGRUMBLE_RealmBattleCore",
  "preserved_existing_meteor_author":"PR #884 existing EGGRUMBLE_RealmBattleCore",
  "requires_existing_realm_10star_path":True,
  "requires_existing_realm_meteor_12segments":True,
  "new_star_steps_generated":0,
  "new_meteor_segments_generated":0,
  "original_semantics":{
   "canyon_always_safe_route":True,"moguron_open_seconds":14,"gate_cooldown_seconds":4,
   "already_selected_star_steps":10,"already_selected_star_open_seconds":16,"already_selected_star_cooldown_seconds":7,
   "existing_meteor_quiet_seconds":55,"existing_meteor_warning_seconds":5,
   "existing_meteor_open_seconds":22,"dont_close_under_player":True,
   "two_symmetric_prompt_sides":True,
   "two_game_modes":["TEAM","BATTLE_ROYALE"]
  },
  "parent_real66_place_sha256":h((parent/"EGGRUMBLE_REAL66_PRIVATE.rbxlx").read_bytes()),
  "studio_2client":"NOT_TESTED","android":"NOT_TESTED",
  "visual_art":"NO_GO","fun":"NO_GO","owner":"NOT_TESTED",
  "roblox_publish":False,"paid_trade":False,
  "rollback":"remove ONLY EGGRUMBLE_LegacyCanyonRoutes; keep byte exact OFF66 from official artifact",
  "formal_adopted":False
 }
 (out/"REAL67_LEGACY_INTAKE_RECEIPT.json").write_text(
  json.dumps(receipt67,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 print("GQ8_RC85_RC86_REAL67_SINGLE_GAME_PARENT66_BYTE_IDENTICAL_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--base",required=True,type=Path)
 p.add_argument("--source",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--sha",required=True)
 a=p.parse_args();compose(a.base,a.source,a.out,a.sha)
