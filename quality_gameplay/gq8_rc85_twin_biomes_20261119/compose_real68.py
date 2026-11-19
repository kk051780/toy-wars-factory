#!/usr/bin/env python3
"""REAL67 -> REAL68: preserve all 67 original sources; one TwinBiomes scene +
one source-exact, existing Combat owner neutral-only controlled bond intake.
No separate Game/Store/Remote/score/HP/XP writer and byte-exact OFF67 backup.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil,os
from pathlib import Path

ROUTE="ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
REL="sources/ServerScriptService/EGGRUMBLE_LegacyTwinBiomes.server.luau"
COMBAT="ServerScriptService/EGGRUMBLE_SevenRoleCombat"
FEATURE="GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119"
GATE=' -- Both hit APIs are SERVER-owned; neutral KO credit only comes from Humanoid.Died.\n'
PATCH=r''' -- GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119
 -- Original TwinBondPolicy session lease 180s, Lv2=10% and Lv3=20%.
 -- V3 still owns all Swarm HP/KO. This branch only adjusts the *existing*
 -- server neutral basic-M1 value, NEVER PvP/bot/guardian/castle/summon.
 -- Exclusive session nonce and server-granted lease prevent stale sessions.
 if stageBasic==true and root.Parent==p.Character
  and p:GetAttribute("EGGRUMBLE_TwinBondServerGranted")==true
  and session and session.world and session.world.Parent
  and p:GetAttribute("EGGRUMBLE_TwinBondSession")==session.world:GetAttribute("EGGRUMBLE_TwinBondSession") then
  local lease=p:GetAttribute("EGGRUMBLE_TwinBondExpires")
  local species=p:GetAttribute("EGGRUMBLE_TwinBondSpecies")
  local level=p:GetAttribute("EGGRUMBLE_TwinBondLevel")
  if typeof(lease)=="number" and lease==lease and os.clock()<lease
   and typeof(level)=="number" and level==math.floor(level)
   and (level==2 or level==3) and
   (species=="AWARIN" or species=="SANGORU" or species=="RAIKO" or species=="KUMONON") then
   local bondMult=if level==3 then 1.2 else 1.1
   -- The already-existing BEAST/WEAPON dojo +5%/level is not multiplied
   -- by original TwinBond; use stronger of original dojo or TwinBond.
   local dojoMult=1
   if p:GetAttribute("EGGRUMBLE_DojoServerGranted")==true then
    local dojoKind=if p:GetAttribute("EGGRUMBLE_Role")=="BEAST" then "Beast" else "Weapon"
    local dojoLevel=p:GetAttribute("EGGRUMBLE_Dojo"..dojoKind.."Level")
    if typeof(dojoLevel)=="number" and dojoLevel==math.floor(dojoLevel)
     and dojoLevel>=1 and dojoLevel<=5 then
     dojoMult=1+(dojoLevel-1)*.05
    end
   end
   neutralDamage*=math.max(1,bondMult/dojoMult)
  end
 end

'''
def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def gate(ok:bool,msg:str)->None:
 if not ok:raise ValueError("RED_REAL68_"+msg)
def source_paths(root:dict)->dict[str,str]:
 ans={}
 def walk(parent,prefix):
  for name,item in parent.items():
   if name.startswith("$") or not isinstance(item,dict):continue
   route=prefix+(name,)
   if "$path" in item:ans["/".join(route)]=item["$path"]
   else:walk(item,route)
 walk(root,())
 return ans
def do(base:Path,source:Path,out:Path,head:str):
 gate(not out.exists(),"CANNOT_OVERWRITE")
 r67=json.loads((base/"REAL67_LEGACY_INTAKE_RECEIPT.json").read_text())
 p67=json.loads((base/"EGGRUMBLE_REAL67.project.json").read_text())
 selected=source_paths(p67["tree"])
 gate(r67.get("candidate_head")==head
       and r67.get("native_selected")=="PASS_67_OF_67"
       and r67.get("rojo_source_class")=="PASS_67_OF_67"
       and r67.get("off66_place_byte_exact") is True,
       "PARENT67_NOT_SAME_HEAD_NATIVE_ROJO_OFF66")
 gate(r67.get("formal_adopted") is (os.environ.get("GITHUB_REF")=="refs/heads/rc/p0d-s1-kids-rc01"),
       "PR_VS_FORMAL_PROFILE_EVENT_FENCE")
 gate(len(selected)==67 and r67["source_count"]==67,"PARENT67")
 gate(r67["parent_all66_byte_identical"] and r67["new_route"]=="ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes","CUMULATIVE_CANYON")
 gate(ROUTE not in selected and COMBAT in selected,"DUPLICATE_OR_MISSING_COMBAT")
 r65=json.loads((base/"REAL65_INTAKE_RECEIPT.json").read_text())
 gate(r65.get("rc86_starry_path") and r65.get("rc86_meteor_shortcut") and
      r65.get("rc85_dojo_lobby_training") and r65.get("legacy_rc86_wind") and
      r65.get("rc86_three_undead_command") and r65.get("rc86_trapper_pair_warp"),"LEGACY_ALREADY_ADOPTED")
 old={}
 for route,path in selected.items():
  f=base/path
  data=f.read_bytes();old[route]=(path,data)
  gate(len(data)>50,"MISSING_SOURCE_"+route)
 for row in r65["sources"]:
  route=row["route"]
  gate(route in old and digest(old[route][1])==row["sha256"] and len(old[route][1])==row["bytes"],
       "NOT_SOURCE_EXACT65_"+route)
 gate(digest(old[r67["new_route"]][1])==r67["new_sha256"],"NOT_EXACT_CANYON")
 gate((base/"EGGRUMBLE_REAL67_PRIVATE.rbxlx").exists(),"MISSING_ROLLBACK_PLACE")
 code=source.read_bytes()
 for a in (b"--!strict\n",FEATURE.encode(),b"AWARIN",b"SANGORU",b"RAIKO",b"KUMONON",
           b"TwinBondExpires",b"TwinBondSession",b"player"):
  if a==b"player":continue
  gate(a in code,"NEW_SCRIPT_MISSING_"+a.decode())
 gate(code.startswith(b"--!strict"),"STRICT_REQUIRED")
 combat_src=old[COMBAT][1].decode("utf8")
 gate(combat_src.count(GATE)==1 and FEATURE not in combat_src,"EXISTING_HIT_GATE")
 gate(combat_src.count("neutralDamage*=1+(level-1)*.05")==1,"DOJO_EXACT_PRESENT")
 gate(combat_src.count("session.swarm.damageFromPlayer(p,neutralAt,range,neutralDamage,shape)")==1,
      "SINGLE_HIT_OWNER")
 combat_new=combat_src.replace(GATE,PATCH+GATE,1).encode("utf8")
 gate(digest(combat_new)!=digest(old[COMBAT][1]),"ACTUAL_COMBAT_DELTA")
 # Source-private copy of the previous canonical 67 and OFF67 reproducibility.
 shutil.copytree(base,out)
 off=out/"off67";off.mkdir()
 (off/"EGGRUMBLE_REAL67.project.json").write_bytes((base/"EGGRUMBLE_REAL67.project.json").read_bytes())
 for route,(path,data) in old.items():
  target=off/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 (out/"OFF67_EXACT_ORIGINAL.rbxlx").write_bytes((base/"EGGRUMBLE_REAL67_PRIVATE.rbxlx").read_bytes())
 (out/old[COMBAT][0]).write_bytes(combat_new)
 fp=out/REL;fp.parent.mkdir(parents=True,exist_ok=True);fp.write_bytes(code)
 spec=copy.deepcopy(p67)
 spec["name"]="EGGRUMBLE_REAL68_RC85_RC86_REAL65_SINGLE_PRIVATE_STUDIO"
 spec["tree"]["ServerScriptService"]["EGGRUMBLE_LegacyTwinBiomes"]={"$path":REL}
 expanded=source_paths(spec["tree"])
 gate(len(expanded)==68 and set(expanded)-set(selected)=={ROUTE},"ONE_NEW_SCRIPT_ONLY")
 for route,(path,data) in old.items():
  result=(out/path).read_bytes()
  gate(path==expanded[route],"ORIGINAL_ROUTE_CLASS_"+route)
  gate(result==(combat_new if route==COMBAT else data),"NONLOSS_ORIGINAL_SOURCE_"+route)
 (out/"EGGRUMBLE_REAL68.project.json").write_text(json.dumps(spec,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 receipt={
  "schema":"GQ8_RC85_RC86_SINGLE_FORMAL_REAL68_TWIN_V1",
  "feature_id":FEATURE,"formal_branch":"rc/p0d-s1-kids-rc01",
  "candidate_head":head,"selected_source_count":68,"previous_formal67_count":67,
  "previous_formal67_source_routes_preserved":True,
  "unchanged_existing_sources":66,
  "modified_existing_routes":[COMBAT],"new_route":ROUTE,
  "new_class":"Script","new_path":REL,
  "original_rc85_artifact_id":14158848286,
  "original_rc86_artifact_id":14161823401,
  "ported_flags":["TWIN_BIOMES_4NPC_V1","TWIN_CREATURE_TRAINING_V1","TWIN_BOND_PVE_COMPANION_V1"],
  "biomes":["CORAL_REEF","THUNDER_CLOUD"],"species":["AWARIN","SANGORU","RAIKO","KUMONON"],
  "species_instances_per_arena":8,"per_species_practice_xp_cap":7,
  "training_level_thresholds":[0,3,7],"practice_cooldown_seconds":20,
  "bond_seconds":180,"bond_switch_seconds":20,
  "bond_neutral_basic_max_multiplier":1.2,
  "same_existing_combat_owner":True,"second_game_owners":0,"new_remotes":0,
  "new_store_hp_ko_score_writers":0,
  "off67_private_place_sha256":digest((base/"EGGRUMBLE_REAL67_PRIVATE.rbxlx").read_bytes()),
  "old_combat_sha256":digest(old[COMBAT][1]),
  "new_combat_sha256":digest(combat_new),
  "new_script_sha256":digest(code),
  "source_fences":{route:{"path":path,"sha256":digest(data),"bytes":len(data)}
                  for route,(path,data) in old.items()},
  "player_studio":"NOT_TESTED","android15min":"NOT_TESTED",
  "visual_art":"NO_GO","fun":"NO_GO","owner":"NOT_TESTED",
  "monetization":False,"roblox_publish":False,
  "formal_adopted":False,
  "rollback":"remove new 68th twin script and restore only Combat old SHA; included exact OFF67"
 }
 (out/"REAL68_TWIN_INTAKE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 print("GQ8_RC85_TWIN4x2_TRAIN_BOND_REAL68_67_PRIOR_SOURCES_WITH_ONE_COMBAT_DELTA_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--base",type=Path,required=True);p.add_argument("--source",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True);p.add_argument("--sha",required=True)
 a=p.parse_args();do(a.base,a.source,a.out,a.sha)
