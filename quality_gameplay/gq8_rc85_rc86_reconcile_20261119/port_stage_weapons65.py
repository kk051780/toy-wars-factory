#!/usr/bin/env python3
"""RC85->RC86 weapon-pickup functional delta ported into REAL65's sole Item/Combat.

Never copies S1 Game/Store/Remote, never starts second loot engine, exact source
receipt/class/hash for all 65 existing scripts, source-count unchanged.
RC86 original: PR479 Actions43714858562 + PR479 wall-safe Actions43754858996.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ITEM="ServerScriptService/EGGRUMBLE_FieldItemPickups"
COMBAT="ServerScriptService/EGGRUMBLE_SevenRoleCombat"
MARK="GQ8_RC86_STAGE_WEAPONS_TO_REAL65_20261119"
INSERT_API=r'''
-- GQ8_RC86_STAGE_WEAPONS_TO_REAL65_20261119: existing Item author owns all grants.
-- RC86 had three 18-second weapons; integrate with V3's existing pickup engine.
local WEAPON_SPECS={
 SUN_BLADE={label="炎の大剣",damage=1.35,color=Color3.fromRGB(255,131,57)},
 WIND_SPEAR={label="疾風の槍",damage=1.08,color=Color3.fromRGB(77,237,190)},
 THUNDER_BOW={label="雷光の弩",damage=1.22,color=Color3.fromRGB(177,139,255)},
}
local weaponBuffs:{[Player]:any}=setmetatable({},{__mode="k"})
local function clearWeaponBuff(player:Player,lease:any)
 if weaponBuffs[player]~=lease then return end
 weaponBuffs[player]=nil
 if player.Parent==Players then
  player:SetAttribute("EGGRUMBLE_FieldWeaponKind",nil)
  player:SetAttribute("EGGRUMBLE_FieldWeaponUntil",nil)
 end
end
function Items.weaponDamageMultiplier(player:Player,session:any):number
 local lease=weaponBuffs[player]
 if not lease or lease.session~=session or lease.character~=player.Character
  or not lease.character or not lease.character.Parent
  or not session or not session.world or not session.world.Parent
  or not session.rules or session.rules.phase~="ACTIVE"
  or not canUse(player,session) or carryingEnemyEggs(player,session) then return 1 end
 local hum=lease.character:FindFirstChildOfClass("Humanoid")
 if not hum or hum.Health<=0 or os.clock()>=lease.expires then return 1 end
 return lease.damage
end
'''
INSERT_STAGE=r'''
 -- One original Item engine, same TEAM/BR roster & wall-LOS guard as consumables.
 -- RC86 source's 6 world weapon pickups and 18s damage bonuses, no second Store.
 local stageSet={
  {2,40,35,"SUN_BLADE"},{5,-40,-35,"SUN_BLADE"},
  {8,40,35,"WIND_SPEAR"},{1,-40,-35,"WIND_SPEAR"},
  {4,40,35,"THUNDER_BOW"},{7,-40,-35,"THUNDER_BOW"},
 }
 local weaponId=0
 for _,point in ipairs(stageSet) do
  local source=positions[point[1]]
  if source then
   local kind=point[4]
   local def=WEAPON_SPECS[kind]
   weaponId+=1
   local id=weaponId
   local base=Instance.new("Part")
   base.Name="GQ8_RC86_Weapon_"..kind.."_"..id
   base.Size=Vector3.new(2.8,.55,2.8)
   base.Anchored=true;base.CanCollide=false;base.CanTouch=false
   base.CanQuery=true;base.Material=Enum.Material.Metal;base.Color=def.color
   base.Position=source+Vector3.new(point[2],-.45,point[3])
   base.Parent=folder
   local shaft=Instance.new("Part")
   shaft.Name="GQ8_WeaponShape_"..kind
   shaft.Size=if kind=="WIND_SPEAR" then Vector3.new(.35,3.2,.35)
    elseif kind=="SUN_BLADE" then Vector3.new(.65,2.4,.4)
    else Vector3.new(2.0,.5,.4)
   shaft.Anchored=true;shaft.CanCollide=false;shaft.CanTouch=false;shaft.CanQuery=false
   shaft.Material=Enum.Material.SmoothPlastic;shaft.Color=def.color
   shaft.Position=base.Position+Vector3.new(0,1.65,0)
   shaft.Parent=folder
   local prompt=Instance.new("ProximityPrompt")
   prompt.ActionText="拾って強化";prompt.ObjectText=def.label.."・18秒"
   prompt.MaxActivationDistance=8;prompt.RequiresLineOfSight=true;prompt.HoldDuration=.25
   prompt.Parent=base
   local available=true
   prompt.Triggered:Connect(function(player:Player)
    if not available or not matchActive() or not canUse(player,session)
     or carryingEnemyEggs(player,session) then return end
    local hum,root=characterState(player)
    if not hum or not root or hum.Health<=0 then return end
    if (root.Position-base.Position).Magnitude>10 then return end
    if isV3Match and not interactionGuard.allow(player,base,"拾う",base.Name) then return end
    local now=os.clock()
    local current=weaponBuffs[player]
    if current then clearWeaponBuff(player,current) end
    local lease={session=session,character=player.Character,expires=now+18,
     kind=kind,damage=def.damage}
    weaponBuffs[player]=lease
    player:SetAttribute("EGGRUMBLE_FieldWeaponKind",kind)
    player:SetAttribute("EGGRUMBLE_FieldWeaponUntil",lease.expires)
    available=false;prompt.Enabled=false;base.Transparency=1;shaft.Transparency=1
    task.delay(18,function() clearWeaponBuff(player,lease) end)
    task.delay(15,function()
     if not matchActive() or not base.Parent then return end
     available=true;prompt.Enabled=true;base.Transparency=0;shaft.Transparency=0
    end)
   end)
  end
 end
'''
INSERT_COMBAT=r'''
 -- RC86 temporary field weapons use this SAME existing Combat damage authority.
 -- No client-supplied multipliers, no extra HP/KO writer, no summoned minion buffs.
 if root.Parent==p.Character then
  damage*=FieldItemPickups.weaponDamageMultiplier(p,session)
 end
'''
def require(flag:bool,why:str)->None:
 if not flag: raise ValueError("RED_RC86_PORT_"+why)
def patch_project(project_path:Path,receipt_path:Path)->None:
 project=json.loads(project_path.read_text(encoding="utf8"))
 receipt=json.loads(receipt_path.read_text(encoding="utf8"))
 by_route={r["route"]:r for r in receipt["sources"]}
 require(project.get("name")=="EGGRUMBLE_REAL65_PRIVATE_STUDIO" and len(by_route)==65
         and len(receipt["sources"])==65,"REAL65_PARENT")
 require(ITEM in by_route and COMBAT in by_route,"EXISTING_OWNER_NOT_FOUND")
 def file_for(route):
  node=project["tree"]
  for part in route.split("/"):node=node[part]
  require(isinstance(node,dict) and "$path" in node,"NO_SOURCE_PATH_"+route)
  return project_path.parent/node["$path"]
 # Verify all original source/class bytes, not only the two touched files.
 for route,entry in by_route.items():
  f=file_for(route);body=f.read_bytes()
  require(hashlib.sha256(body).hexdigest()==entry["sha256"] and len(body)==entry["bytes"],
    "PARENT_SOURCE_MUTATED_"+route)
 before={}
 for route in (ITEM,COMBAT):before[route]=file_for(route).read_text(encoding="utf8")
 src=before[ITEM]
 require(src.count("local function characterState(player:Player):(Humanoid?,BasePart?)")==1
         and src.count(" session.itemStop=function()")==1
         and MARK not in src,"ITEM_ANCHOR")
 src=src.replace("local function characterState(player:Player):(Humanoid?,BasePart?)",
                 INSERT_API+"\nlocal function characterState(player:Player):(Humanoid?,BasePart?)",1)
 src=src.replace(" session.itemStop=function()",INSERT_STAGE+"\n session.itemStop=function()",1)
 # cleanup original ITEM module retains original itemStop ownership
 require(src.count("  active=false\n  if folder.Parent then folder:Destroy() end")==1,
         "ITEM_STOP_ANCHOR")
 src=src.replace("  active=false\n  if folder.Parent then folder:Destroy() end",
   '''  active=false
  for player,lease in pairs(weaponBuffs) do
   if lease.session==session then clearWeaponBuff(player,lease) end
  end
  if folder.Parent then folder:Destroy() end''',1)
 combat=before[COMBAT]
 key='local CoreAction=require(script.Parent:WaitForChild("EGGRUMBLE_BasicMobilityPolicy"))'
 hit='local function neutralAndBotHit(session:any,p:Player,root:BasePart,char:Model,at:Vector3,range:number,damage:number,c:Color3,shape:string):number\n'
 require(combat.count(key)==1 and combat.count(hit)==1 and MARK not in combat,"COMBAT_ANCHOR")
 combat=combat.replace(key,key+'\nlocal FieldItemPickups=require(script.Parent:WaitForChild("EGGRUMBLE_FieldItemPickups"))',1)
 combat=combat.replace(hit,hit+INSERT_COMBAT,1)
 require(combat.count("FieldItemPickups.weaponDamageMultiplier(p,session)")==1,
         "COMBAT_SINGLE_BONUS_CALL")
 for route,body in ((ITEM,src),(COMBAT,combat)):
  f=file_for(route);encoded=body.encode("utf8");f.write_bytes(encoded)
  by_route[route]["sha256"]=hashlib.sha256(encoded).hexdigest()
  by_route[route]["bytes"]=len(encoded)
  require(encoded!=before[route].encode("utf8"),"UNMODIFIED_"+route)
 # Keep exact rollback OFF63 and existing successful REAL65 lineage intact.
 require(Path(project_path.parent/"OFF63_EXACT_OFFICIAL.rbxlx").is_file(),
         "OFF63_NOT_RETAINED")
 receipt["patched_existing_routes"] += [ITEM] if ITEM not in receipt["patched_existing_routes"] else []
 receipt["patched_existing_routes"] += [COMBAT] if COMBAT not in receipt["patched_existing_routes"] else []
 receipt["original_real63_byte_unchanged"]=55
 receipt["rc85_rc86_stage_weapon_delta"]={
  "feature_id":MARK,
  "source":"PR479 original RC86 StagePickupLoot 6 pickups, 3 weapons, 18s bonuses",
  "original_artifact_id":14161823401,
  "wall_safe_source_artifact_id":14177514150,
  "actual_selected_sources":65,
  "changed_existing_routes":[ITEM,COMBAT],
  "added_script_owners":0,
  "single_owner_policy":"existing EGGRUMBLE_FieldItemPickups and EGGRUMBLE_SevenRoleCombat",
  "weapons":["SUN_BLADE","WIND_SPEAR","THUNDER_BOW"],
  "buff_seconds":18,"studio":"NOT_TESTED","android":"NOT_TESTED",
  "rollback":"prior REAL65 profile via branch ancestry; OFF63 exact retained"}
 receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("RC85_RC86_STAGE_WEAPONS_IN_EXISTING_REAL65_ITEM_COMBAT_65_SOURCE_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--project",required=True,type=Path)
 p.add_argument("--receipt",required=True,type=Path)
 a=p.parse_args();patch_project(a.project,a.receipt)
