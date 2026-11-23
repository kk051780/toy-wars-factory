#!/usr/bin/env python3
"""Source-locked original RC86 FB015GoroganVisual legacy runestone geometry
adapted to the ONE existing V3 EncounterReadabilityArt boss decorator.
No second art service, boss, script, HP/AI/attack/Remote/Store or product access.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
FEATURE="GQ8_RC86_FB015_GOROGAN_RUNESTONE_ART_SINGLE_EXISTING_OWNER_20261119"
ROUTE="ServerScriptService/EGGRUMBLE_EncounterReadabilityArt"
SOURCE_ORIGINAL="8699dd37fea2c78a11ac5d8081931a08189581f4ada7694eec735317009d2e60"
ADDITION=r'''
 -- GQ8_RC86_FB015_GOROGAN_RUNESTONE_ART_SINGLE_EXISTING_OWNER_20261119
 -- Exact RC86 FB015GoroganVisual motifs adapted to original V3 static boss.
 -- Do not instantiate old Gorogan_ServerRig, Humanoid, server AI or art script.
 -- Existing weakpoint/ProximityPrompt/HP telegraph and 5 preexisting ornaments stay intact.
 art:SetAttribute("RC86VisualMotif","GOROGAN_RUNESTONE_TITAN")
 art:SetAttribute("RC86OriginalSourceSHA256","8699dd37fea2c78a11ac5d8081931a08189581f4ada7694eec735317009d2e60")
 art:SetAttribute("GameAuthorityUnchanged",true)
 art:SetAttribute("MaxDecorParts",17)
 local basalt=Color3.fromRGB(64,73,83)
 local basaltLight=Color3.fromRGB(103,119,128)
 local rune=Color3.fromRGB(110,236,221)
 local eyeAmber=Color3.fromRGB(255,176,112)
 for _,side in ipairs({-1,1}) do
  -- Two distinctive asymmetric stone horns, the original RC86 silhouette.
  add(head,"GoroganCrownHorn"..side,"Wedge",Vector3.new(1.5,3.9,1.5),
   CFrame.new(side*1.8,3.1,.4)*CFrame.Angles(0,0,side*.28),
   basalt,Enum.Material.Slate)
  add(head,"GoroganRuneEye"..side,"Ball",Vector3.new(.75,.6,.26),
   CFrame.new(side*.93,.62,-head.Size.Z*.5-.18),
   eyeAmber,Enum.Material.Neon)
  add(torso,"GoroganShoulderSigil"..side,"Ball",Vector3.new(.85,.85,.22),
   CFrame.new(side*5.0,3.3,-torso.Size.Z*.5-.18),
   rune,Enum.Material.Neon)
  add(torso,"GoroganFlankArmor"..side,"Wedge",Vector3.new(1.3,3.2,3.0),
   CFrame.new(side*4,-2.0,0)*CFrame.Angles(0,0,side*.12),
   basaltLight,Enum.Material.Slate)
 end
 -- Original five-spine motif condensed to four within mobile art budget.
 for i=1,4 do
  add(torso,"GoroganBackSpine"..i,"Wedge",
   Vector3.new(1.1,2.8-(i-1)*.35,1.25),
   CFrame.new(0,3.8-(i-1)*1.45,torso.Size.Z*.5+.8)
    *CFrame.Angles(.5,0,0),basaltLight,Enum.Material.Slate)
 end
 -- Only the preexisting V3 ArtDistanceLOD can fade this folder at distance.
 -- Extra visual objects are weld-only, no collision/query, no independent loop.
'''
def require(ok,what):
 if not ok:raise ValueError("RED_RC86_GOROGAN_"+what)
def replace_exact(s,old,new,label):
 require(s.count(old)==1,"ANCHOR_"+label+"_"+str(s.count(old)))
 return s.replace(old,new,1)
def patch(s):
 require(FEATURE not in s,"ALREADY_APPLIED")
 require("local MAX_BOSS_ORNAMENT_PARTS=5" in s,"EXPECTED_CAP")
 require('art.Name="EGGRUMBLE_StoneGiantVisual_VisualOnly"' in s,"SINGLE_ART_OWNER")
 require('if instance:IsA("Model") and instance.Name=="NEUTRAL_BOSS_STONE_GIANT"' in s,"EXISTING_BOSS_SCOPE")
 require('art.Name="EGGRUMBLE_InteriorHeraldry_VisualOnly"' in s,"PRESERVE_CASTLE_DECOR")
 require("local function decorateNeutral(neutral:Model)" in s,"PRESERVE_NEUTRAL_ART")
 require("if not RunService:IsStudio() then return end" in s,"STUDIO_ONLY")
 s=replace_exact(s,"local MAX_BOSS_ORNAMENT_PARTS=5","local MAX_BOSS_ORNAMENT_PARTS=17","BOSS_CAP")
 s=replace_exact(s,' if bezel then\n  -- Red phase is read from real server-owned weak-point health color only.',
    ADDITION+'\n if bezel then\n  -- Red phase is read from real server-owned weak-point health color only.',"BEFORE_ORIGINAL_WEAKPOINT")
 require(s.count("GoroganCrownHorn")==1 and s.count("GoroganRuneEye")==1 and
         s.count("GoroganBackSpine")==1 and s.count(FEATURE)==1,"GEOMETRY_AND_NO_DUP")
 require(s.count("local MAX_BOSS_ORNAMENT_PARTS=17")==1 and
         s.count('art.Name="EGGRUMBLE_StoneGiantVisual_VisualOnly"')==1,"SINGLE_OWNER")
 # No gameplay trust, no new script/loop: only original A01 existing visual add() helper.
 for bad in ["Instance.new(\"RemoteEvent\")","DataStoreService","MarketplaceService","Humanoid:TakeDamage"]:
  require(bad not in ADDITION,"NO_NEW_AUTHORITY_"+bad)
 return s
def main(project_file,receipt_file):
 root=project_file.parent
 project=json.loads(project_file.read_text())
 receipt=json.loads(receipt_file.read_text())
 sources=receipt.get("sources")
 require(isinstance(sources,list) and len(sources)==65,"EXACT_SOURCE_COUNT_65")
 rows={x["route"]:x for x in sources}
 require(len(rows)==65 and ROUTE in rows,"ORIGINAL_ART_OWNER_EXISTS")
 require(receipt.get("rc86_meteor_shortcut") and receipt.get("rc86_three_undead_command")
         and receipt.get("rc86_trapper_pair_warp") and receipt.get("rc86_fb016_foliage_sightline")
         and receipt.get("rc85_dojo_lobby_training"),"CURRENT_LATEST_PARENT")
 require("rc86_gorogan_art_v2" not in receipt,"NO_DOUBLE_ART_PATCH")
 def raw_for(row):
  node=project["tree"]
  for segment in row["route"].split("/"):node=node[segment]
  require(node.get("$className") in (None,row["class"]),"CLASS_"+row["route"])
  raw=(root/node["$path"]).read_bytes()
  require(len(raw)==row["bytes"] and hashlib.sha256(raw).hexdigest()==row["sha256"],
          "PREPOST_SHA_"+row["route"])
  return root/node["$path"],raw
 for row in sources:raw_for(row)
 path,original=raw_for(rows[ROUTE])
 revised=patch(original.decode()).encode()
 path.write_bytes(revised)
 rows[ROUTE]["bytes"]=len(revised)
 rows[ROUTE]["sha256"]=hashlib.sha256(revised).hexdigest()
 for row in sources:raw_for(row)
 receipt["rc86_gorogan_art_v2"]={
  "feature":FEATURE,"old_original_script":"FB015GoroganVisual",
  "old_artifact_id":14161823401,"old_source_sha256":SOURCE_ORIGINAL,
  "existing_v3_decorator":ROUTE,"original_v3_art_ornaments_preserved":5,
  "added_noncolliding_visual_parts_per_boss":12,"total_max_per_boss":17,
  "non_studio_runtime":"DISABLED_BY_EXISTING_ART_OWNER",
  "only_changed_existing_source":ROUTE,"other_selected_sources_byte_identical":64,
  "script_count_delta":0,"new_remote_game_damage_store_owner":0,
  "art_quality":"ENGINE_NOT_TESTED","android_15min":"NOT_TESTED",
  "original_old_moving_rig_path_ai":"NOT_PORTED_DO_NOT_CLAIM"
 }
 receipt_file.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
 print("GQ8_RC86_ORIGINAL_GOROGAN_VISUAL17_V3_EXISTING_ART_OWNER_EXACT65_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--project",required=True,type=Path)
 p.add_argument("--receipt",required=True,type=Path)
 a=p.parse_args();main(a.project,a.receipt)
