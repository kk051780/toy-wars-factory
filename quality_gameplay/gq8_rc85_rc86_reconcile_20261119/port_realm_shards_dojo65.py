#!/usr/bin/env python3
"""Source-locked RC85/RC86 original REALM_HUNT, STAR_SHARDS and 2-lane DOJO
ports into the ONLY existing REAL65 Realm, SocialPlaza and Combat owners.
No S1 Game/Store/Remote/HP/Score/round replacement; preserve original 65 routes.
"""
import argparse,hashlib,json
from pathlib import Path
MARK="GQ8_RC85_REALM_SHARDS_DOJO_RECONCILE_20261119"
REALM="ServerScriptService/EGGRUMBLE_RealmBattleCore"
SOCIAL="ServerScriptService/GQ8_LobbySocialPlaza"
COMBAT="ServerScriptService/EGGRUMBLE_SevenRoleCombat"

REALM_BODY=r'''
 -- GQ8_RC85_REALM_SHARDS_DOJO_RECONCILE_20261119
 -- Original RC85 REALM_HUNT_V1 four discoveries + STAR_SHARDS_V1 six safe
 -- collectibles translated to verified V3 per-match world coordinates.
 -- One existing Realm script owns the world. Cosmetic quest ONLY, no score,
 -- XP, extra Game, extra Store, remotes, saved items or client permissions.
 local legacyHunts={
  {kind="REALM",id="SKY",title="空のひみつ",location=flightPad.Position+Vector3.new(0,4,8),
   color=Color3.fromRGB(115,218,255)},
  {kind="REALM",id="SEA",title="海のひみつ",location=dive.Position+Vector3.new(0,4,8),
   color=Color3.fromRGB(66,196,239)},
  {kind="REALM",id="EMBER",title="炎のひみつ",location=Vector3.new(x-85,y+3,z+68),
   color=Color3.fromRGB(252,121,61)},
  {kind="REALM",id="STAR",title="星のひみつ",location=Vector3.new(x+85,y+3,z-68),
   color=Color3.fromRGB(198,149,255)},
  {kind="SHARD",id="1",title="星の欠片 1/6",location=Vector3.new(x-110,y+3,z+104),
   color=Color3.fromRGB(198,149,255)},
  {kind="SHARD",id="2",title="星の欠片 2/6",location=Vector3.new(x-65,y+3,z+45),
   color=Color3.fromRGB(198,149,255)},
  {kind="SHARD",id="3",title="星の欠片 3/6",location=Vector3.new(x-10,y+3,z-100),
   color=Color3.fromRGB(198,149,255)},
  {kind="SHARD",id="4",title="星の欠片 4/6",location=Vector3.new(x+40,y+3,z+100),
   color=Color3.fromRGB(198,149,255)},
  {kind="SHARD",id="5",title="星の欠片 5/6",location=Vector3.new(x+95,y+3,z-45),
   color=Color3.fromRGB(198,149,255)},
  {kind="SHARD",id="6",title="星の欠片 6/6",location=Vector3.new(x+10,y+3,z+10),
   color=Color3.fromRGB(198,149,255)},
 }
 local legacyRecords:{[Player]:any}={}
 local legacyQuestFolder=Instance.new("Folder")
 legacyQuestFolder.Name="GQ8_RC85_LegacyQuests"
 legacyQuestFolder:SetAttribute("Owner","EGGRUMBLE_RealmBattleCore")
 legacyQuestFolder:SetAttribute("CosmeticOnly",true)
 legacyQuestFolder.Parent=core
 local function questPrefix(kind:string):string
  return if kind=="REALM" then "EGGRUMBLE_RealmHunt_"..mode.."_"
   else "EGGRUMBLE_StarShards_"..mode.."_"
 end
 local function legacyDiscover(player:Player,kind:string,id:string)
  if not eligible(player,mode,world) or not state.active then return end
  local stateFor=legacyRecords[player]
  if not stateFor then
   stateFor={REALM={},SHARD={}}
   legacyRecords[player]=stateFor
   for _,quest in ipairs({"REALM","SHARD"}) do
    local prefix=questPrefix(quest)
    player:SetAttribute(prefix.."Count",0)
    player:SetAttribute(prefix.."Complete",false)
   end
  end
  local found=stateFor[kind]
  if not found or found[id] then return end
  found[id]=true
  local count=0
  for _ in pairs(found) do count+=1 end
  local total=if kind=="REALM" then 4 else 6
  local prefix=questPrefix(kind)
  player:SetAttribute(prefix..id,true)
  player:SetAttribute(prefix.."Count",count)
  player:SetAttribute(prefix.."Complete",count==total)
 end
 for _,quest in ipairs(legacyHunts) do
  -- Explicit bounds: V3 physical arena footprint, no remote teleport.
  local dx=quest.location.X-x
  local dz=quest.location.Z-z
  if math.abs(dx)<halfX-18 and math.abs(dz)<halfZ-18 then
   local node=part(legacyQuestFolder,
    "Legacy_"..quest.kind.."_"..quest.id,CFrame.new(quest.location),
    Vector3.new(2.5,2.5,2.5),quest.color,false,.08)
   node.Shape=Enum.PartType.Ball;node.Material=Enum.Material.Neon
   node.CanQuery=false;node.CanTouch=false
   -- Server validates the *living current-mode human* even after prompt fires.
   prompt(node,"発見する",quest.title,function(player:Player)
    legacyDiscover(player,quest.kind,quest.id)
   end)
   local gui=Instance.new("BillboardGui")
   gui.Name="QuestTitle";gui.Size=UDim2.fromOffset(136,40)
   gui.StudsOffsetWorldSpace=Vector3.new(0,2.8,0)
   gui.MaxDistance=34;gui.AlwaysOnTop=false;gui.Parent=node
   local title=Instance.new("TextLabel")
   title.BackgroundTransparency=1;title.TextColor3=quest.color
   title.Font=Enum.Font.GothamBold;title.TextScaled=true
   title.Size=UDim2.fromScale(1,1);title.Text=quest.title;title.Parent=gui
  end
 end
 world.Destroying:Connect(function()
  for p in pairs(legacyRecords) do
   if p.Parent==Players then
    for _,kind in ipairs({"REALM","SHARD"}) do
     local prefix=questPrefix(kind)
     p:SetAttribute(prefix.."Count",nil)
     p:SetAttribute(prefix.."Complete",nil)
     for id in pairs(legacyRecords[p][kind]) do p:SetAttribute(prefix..id,nil) end
    end
   end
   legacyRecords[p]=nil
  end
 end)
'''

SOCIAL_BODY=r'''
-- GQ8_RC85_REALM_SHARDS_DOJO_RECONCILE_20261119
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
    if not cached or now-cached.checked>60 then
     local ok,yes=pcall(function() return player:IsFriendsWith(other.UserId) end)
     cached={checked=now,yes=ok and yes==true}
     dojoFriendCache[pairKey]=cached
    end
    if cached.yes then friend=true;break end
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
end)
'''

SOCIAL_TICK=r'''
            -- Real server-measured station time; stopped when leaving the pad.
            stepLegacyDojo(player,root,now,step)
'''

COMBAT_BODY=r'''
 -- GQ8_RC85_REALM_SHARDS_DOJO_RECONCILE_20261119
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
 check(len(rows)==65 and all(route in rows for route in (REALM,SOCIAL,COMBAT)),"REQUIRED_OWNER")
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
 realmPath,realm=original(REALM)
 socialPath,social=original(SOCIAL)
 combatPath,combat=original(COMBAT)
 check(MARK not in realm and MARK not in social and MARK not in combat,"DUPLICATE_PATCH")
 realm=replace_once(realm," local function clearDive(player)\n",REALM_BODY+"\n local function clearDive(player)\n","REALM_AFTER_REAL_WORLD_STATIONS")
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
 check(realm.count("legacyDiscover(player,quest.kind,quest.id)")==1,"REALM_REAL_PROMPT")
 check(social.count("stepLegacyDojo(player,root,now,step)")==1 and
       social.count('player:SetAttribute("EGGRUMBLE_DojoServerGranted",true)')==1,"REAL_DOJO")
 check(combat.count('neutralDamage*=1+(level-1)*.05')==1,"COMBAT_SINGLE_BUFF")
 for route,path,body in [(REALM,realmPath,realm),(SOCIAL,socialPath,social),(COMBAT,combatPath,combat)]:
  raw=body.encode("utf8");path.write_bytes(raw)
  rows[route]["sha256"]=hashlib.sha256(raw).hexdigest()
  rows[route]["bytes"]=len(raw)
 for route in rows:original(route)
 check(len(set(r["route"] for r in receipt["sources"]))==65,"SCRIPT_COUNT")
 # No new original route was modified; all 3 already in prior patched list.
 check(set((REALM,SOCIAL,COMBAT)).issubset(set(receipt["patched_existing_routes"])),"PRIOR_PATCH_ROUTE")
 receipt["rc85_rc86_realm_shards_dojo"]={
  "feature_id":MARK,"original_rc85_source_artifact_id":14158848286,
  "original_rc86_source_artifact_id":14161823401,
  "ported_policy_flags":["REALM_HUNT_V1","STAR_SHARDS_V1","FB007_LOBBY_DOJO_PHYSICAL_V1"],
  "original_dojo_rules":{"skills":["BEAST","WEAPON"],"max_level":5,
     "costs":[10,15,20,25],"seconds_per_skill":180,
     "actual_friend_training_multiplier":1.5,"neutral_pve_per_level":0.05},
  "quest_locations":4,"shard_locations":6,
  "new_script_count":0,"new_game_owners":0,"new_remote_count":0,
  "new_store_count":0,"new_damage_writers":0,
  "changed_existing_routes":[REALM,SOCIAL,COMBAT],
  "unchanged_selected_routes":62,
  "original_real63_byte_unchanged":receipt["original_real63_byte_unchanged"],
  "studio_2client":"NOT_TESTED","android":"NOT_TESTED",
  "feature_parity":"PORT_LOGIC_SOURCE_ONLY_ENGINE_NOT_TESTED",
  "rollback":"prior formal REAL65 composer HEAD; OFF63 byte exact"}
 receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_RC85_REALM4_SHARDS6_DOJO2_LEVEL5_NATIVE65_READY")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--project",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 a=p.parse_args();main(a.project,a.receipt)
