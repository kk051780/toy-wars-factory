#!/usr/bin/env python3
"""Source-locked RC85 two-lane DOJO port into current SocialPlaza/Combat.
RC86 exploration Realm4+Star6 is ALREADY adopted via independent PR #877
as one and only real 66th script. NEVER create another Realm/Shard quest.
Retain all original REAL65 scripts and let formal composer select REAL66.
"""
import argparse,hashlib,json
from pathlib import Path
MARK="GQ8_RC85_DOJO_RECONCILE_20261119"
REALM="ServerScriptService/EGGRUMBLE_RealmBattleCore"
SOCIAL="ServerScriptService/GQ8_LobbySocialPlaza"
COMBAT="ServerScriptService/EGGRUMBLE_SevenRoleCombat"

SOCIAL_BODY=r'''
-- GQ8_RC85_DOJO_RECONCILE_20261119
-- Original RC85 DojoRules: BEAST/WEAPON, 180s each, levels1..5, costs
-- 10/15/20/25, +50% when *actual* friends are practicing together.
-- One existing SocialPlaza script owns physical pads and XP, no second Game,
-- no save, no Store, no Remote and no paid shortcuts. Existing Combat applies
-- only <=20% in neutral PvE, never PvP/castle/bots/summoned guardians.
local dojoPlatform=part("LegacyDojoPlatform",Vector3.new(0,-.65,-40),
 Vector3.new(54,1.2,27),Color3.fromRGB(89,111,133),Enum.Material.Slate,true)
part("LegacyDojoWalkway",Vector3.new(0,-.28,-25),
 Vector3.new(9,.8,14),stone,Enum.Material.Cobblestone,true)
local dojoPads:{[string]:BasePart}={}
local dojoSigns:{[string]:TextLabel}={}
local dojoTrainers:{[number]:any}={}
local dojoFriendCache:{[string]:any}={}
local dojoCosts={10,15,20,25}
for _,kind in ipairs({"BEAST","WEAPON"}) do
 local px=if kind=="BEAST" then -13 else 13
 local primary=if kind=="BEAST" then Color3.fromRGB(96,194,143)
  else Color3.fromRGB(232,179,104)
 local pad=part("LegacyDojoPad_"..kind,Vector3.new(px,.22,-40),
  Vector3.new(15,.5,12),primary,Enum.Material.WoodPlanks,true)
 local banner=part("LegacyDojoBanner_"..kind,Vector3.new(px,4,-47),
  Vector3.new(12,5,.35),primary,Enum.Material.Fabric,false)
 local labelText=if kind=="BEAST" then "魔獣修行" else "武器修行"
 local sign=label(banner,labelText.."\nLv1〜5・1回180秒")
 dojoPads[kind]=pad;dojoSigns[kind]=sign
 local trainingPrompt=Instance.new("ProximityPrompt")
 trainingPrompt.Name="GQ8_RC85_DojoPractice_"..kind
 trainingPrompt.ActionText="修行開始";trainingPrompt.ObjectText=labelText.."（セッション限定）"
 trainingPrompt.MaxActivationDistance=9;trainingPrompt.HoldDuration=.35
 trainingPrompt.RequiresLineOfSight=true;trainingPrompt.Parent=pad
 trainingPrompt.Triggered:Connect(function(player:Player)
  local root=aliveRoot(player)
  if player.Parent~=Players or not root or (root.Position-pad.Position).Magnitude>11
   or player:GetAttribute("EGGRUMBLE_QueuedMode")=="TEAM"
   or player:GetAttribute("EGGRUMBLE_QueuedMode")=="BATTLE_ROYALE" then return end
  local state=dojoTrainers[player.UserId]
  if not state then
   state={level={BEAST=1,WEAPON=1},xp={BEAST=0,WEAPON=0},
    trainedSeconds={BEAST=0,WEAPON=0},active="NONE"}
   dojoTrainers[player.UserId]=state
   player:SetAttribute("EGGRUMBLE_DojoServerGranted",true)
   player:SetAttribute("EGGRUMBLE_DojoBeastLevel",1)
   player:SetAttribute("EGGRUMBLE_DojoWeaponLevel",1)
  end
  state.active=kind
  player:SetAttribute("EGGRUMBLE_DojoActiveSkill",kind)
 end)
end
local function stepLegacyDojo(player:Player,root:BasePart,now:number,step:number)
 local state=dojoTrainers[player.UserId]
 if not state or not state.active or not dojoPads[state.active] then return end
 local kind=state.active
 local pad=dojoPads[kind]
 if (root.Position-pad.Position).Magnitude>8
  or player:GetAttribute("EGGRUMBLE_QueuedMode")=="TEAM"
  or player:GetAttribute("EGGRUMBLE_QueuedMode")=="BATTLE_ROYALE" then
  state.active="NONE";player:SetAttribute("EGGRUMBLE_DojoActiveSkill","NONE")
  return
 end
 local seconds=state.trainedSeconds[kind]
 if seconds>=180 then return end
 local friend=false
 for _,other in ipairs(Players:GetPlayers()) do
  if other~=player then
   local otherRoot=aliveRoot(other)
   if otherRoot and (otherRoot.Position-pad.Position).Magnitude<=8 then
    local left=math.min(player.UserId,other.UserId)
    local right=math.max(player.UserId,other.UserId)
    local pairKey=tostring(left).."_"..tostring(right)
    local cached=dojoFriendCache[pairKey]
    if not cached or (not cached.pending and now-cached.checked>60) then
     -- The friendship API may yield. Never suspend a training tick or replay
     -- old training state after a player departs, changes skill or joins a match.
     cached={checked=now,yes=false,pending=true,left=player,right=other}
     dojoFriendCache[pairKey]=cached
     local request=cached
     task.spawn(function()
      local ok,yes=pcall(function() return player:IsFriendsWith(other.UserId) end)
      if dojoFriendCache[pairKey]~=request or not plaza.Parent
       or player.Parent~=Players or other.Parent~=Players then return end
      request.checked=time()
      request.yes=ok and yes==true
      request.pending=false
     end)
    end
    if not cached.pending and cached.yes then friend=true;break end
   end
  end
 end
 local used=math.min(step,180-seconds)
 state.trainedSeconds[kind]=seconds+used
 local level=state.level[kind]
 if level<5 then
  local xp=state.xp[kind]+used*(if friend then 1.5 else 1)
  while level<5 and xp>=dojoCosts[level] do
   xp-=dojoCosts[level];level+=1
  end
  if level==5 then xp=0 end
  state.level[kind]=level;state.xp[kind]=xp
 end
 local attr=if kind=="BEAST" then "EGGRUMBLE_DojoBeastLevel"
  else "EGGRUMBLE_DojoWeaponLevel"
 player:SetAttribute(attr,state.level[kind])
 player:SetAttribute("EGGRUMBLE_DojoFriendBonus",friend)
 local name=if kind=="BEAST" then "魔獣修行" else "武器修行"
 dojoSigns[kind].Text=name.."\nLv"..state.level[kind].."/5・"..math.floor(state.trainedSeconds[kind]).."秒"
end
Players.PlayerRemoving:Connect(function(player:Player)
 dojoTrainers[player.UserId]=nil
 -- Drop completed and pending requests. A late response may only update its
 -- original entry, never recreate a departed player's pair or new session.
 for key,request in pairs(dojoFriendCache) do
  if request.left==player or request.right==player then dojoFriendCache[key]=nil end
 end
end)
'''

SOCIAL_TICK=r'''
            -- Real server-measured station time; stopped when leaving the pad.
            stepLegacyDojo(player,root,now,step)
'''

COMBAT_BODY=r'''
 -- GQ8_RC85_DOJO_RECONCILE_20261119
 -- Original RC85 session-only dojo +5% per level (<=20%). Only the
 -- existing Combat neutral Swarm hit consumes this. Player/server attributes
 -- are set by the Studio-only SocialPlaza station; client changes do not
 -- replicate to the authoritative server attribute table.
 if root.Parent==p.Character and p:GetAttribute("EGGRUMBLE_DojoServerGranted")==true then
  local kind=if p:GetAttribute("EGGRUMBLE_Role")=="BEAST" then "Beast"
   elseif stageBasic==true then "Weapon" else ""
  if kind~="" then
   local level=p:GetAttribute("EGGRUMBLE_Dojo"..kind.."Level")
   if typeof(level)=="number" and level==math.floor(level)
    and level>=1 and level<=5 then
    neutralDamage*=1+(level-1)*.05
   end
  end
 end
'''

def check(test,msg):
 if not test: raise ValueError("RED_RC85_RC86_REAL65_"+msg)
def replace_once(text,old,new,msg):
 check(text.count(old)==1,"ANCHOR_"+msg)
 return text.replace(old,new,1)
def main(project_path,receipt_path):
 folder=project_path.parent
 project=json.loads(project_path.read_text(encoding="utf8"))
 receipt=json.loads(receipt_path.read_text(encoding="utf8"))
 check(len(receipt.get("sources",[]))==65,"SOURCE_65_REQUIRED")
 check(receipt.get("legacy_rc86_wind") and receipt.get("stage_weapon_reach_balance")
       and receipt.get("pickup_prompt_alias") and receipt.get("late_host_world_watch"),"LATEST_PARENTS")
 check(MARK not in receipt,"ALREADY_INTEGRATED")
 rows={r["route"]:r for r in receipt["sources"]}
 check(len(rows)==65 and all(route in rows for route in (SOCIAL,COMBAT)),"REQUIRED_OWNER")
 def original(route):
  node=project["tree"]
  for part in route.split("/"): node=node[part]
  check("$path" in node,"ROUTE_CLASS_"+route)
  path=folder/node["$path"];raw=path.read_bytes()
  check(hashlib.sha256(raw).hexdigest()==rows[route]["sha256"] and len(raw)==rows[route]["bytes"],
        "SHA_AND_BYTES_"+route)
  return path,raw.decode("utf8")
 # First verify all 65 original receipt rows before making changes.
 for route in rows:original(route)
 socialPath,social=original(SOCIAL)
 combatPath,combat=original(COMBAT)
 check(MARK not in social and MARK not in combat,"DUPLICATE_PATCH")
 social=replace_once(social,"local t=0\nlocal hb:RBXScriptConnection?",SOCIAL_BODY+"\nlocal t=0\nlocal hb:RBXScriptConnection?","SOCIAL_PAD_AND_OWNER")
 social=replace_once(social,
  "    t+=dt;if t<1 then return end;t=0\n",
  "    t+=dt;if t<1 then return end\n    local step=math.min(1.5,t);t=0\n",
  "SOCIAL_MONOTONIC_TIME")
 social=replace_once(social,
  "        if root then\n            for i,m in ipairs(meeting) do",
  "        if root then\n"+SOCIAL_TICK+"            for i,m in ipairs(meeting) do",
  "SOCIAL_PER_PLAYER_TICK")
 combat=replace_once(combat,
  " -- Both hit APIs are SERVER-owned; neutral KO credit only comes from Humanoid.Died.\n",
  COMBAT_BODY+"\n -- Both hit APIs are SERVER-owned; neutral KO credit only comes from Humanoid.Died.\n",
  "COMBAT_NEUTRAL_ONLY_HIT")
 check(social.count("stepLegacyDojo(player,root,now,step)")==1 and
       social.count('player:SetAttribute("EGGRUMBLE_DojoServerGranted",true)')==1,"REAL_DOJO")
 check(combat.count('neutralDamage*=1+(level-1)*.05')==1,"COMBAT_SINGLE_BUFF")
 for route,path,body in [(SOCIAL,socialPath,social),(COMBAT,combatPath,combat)]:
  raw=body.encode("utf8");path.write_bytes(raw)
  rows[route]["sha256"]=hashlib.sha256(raw).hexdigest()
  rows[route]["bytes"]=len(raw)
 for route in rows:original(route)
 check(len(set(r["route"] for r in receipt["sources"]))==65,"SCRIPT_COUNT")
 # No new original route was modified; all 3 already in prior patched list.
 check(set((SOCIAL,COMBAT)).issubset(set(receipt["patched_existing_routes"])),"PRIOR_PATCH_ROUTE")
 receipt["rc85_dojo_lobby_training"]={
  "feature_id":MARK,"original_rc85_source_artifact_id":14158848286,
  "original_rc86_source_artifact_id":14161823401,
  "ported_policy_flags":["FB007_LOBBY_DOJO_PHYSICAL_V1"],
  "original_dojo_rules":{"skills":["BEAST","WEAPON"],"max_level":5,
     "costs":[10,15,20,25],"seconds_per_skill":180,
     "actual_friend_training_multiplier":1.5,"neutral_pve_per_level":0.05},
  "quest_locations":0,"shard_locations":0,
  "new_script_count":0,"new_game_owners":0,"new_remote_count":0,
  "new_store_count":0,"new_damage_writers":0,
  "changed_existing_routes":[SOCIAL,COMBAT],
  "unchanged_selected_routes":63,
  "original_real63_byte_unchanged":receipt["original_real63_byte_unchanged"],
  "legacy_exploration_formal_source":"PR #877 canonical REAL66 already selected",
  "do_not_select_second_realm_or_shard":"#868 source is now selected once via REAL66 only",
  "studio_2client":"NOT_TESTED","android":"NOT_TESTED",
  "feature_parity":"PORT_LOGIC_SOURCE_ONLY_ENGINE_NOT_TESTED",
  "rollback":"prior formal REAL65 composer HEAD; OFF63 byte exact"}
 receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_RC85_DOJO2_LEVEL5_SAME_REAL66_PROVENANCE_NATIVE65_READY")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--project",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 a=p.parse_args();main(a.project,a.receipt)
