#!/usr/bin/env python3
"""Port RC86 FB030 *six* real world weapon pickups into the existing REAL65 ITEM author.

No legacy Game/HUD/Remote/Store or secondary item engine is included.
Only EGGRUMBLE_FieldItemPickups + the existing EGGRUMBLE_SevenRoleCombat
are altered. All other 63 source bodies and OFF63 rollback are preserved.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ITEM="ServerScriptService/EGGRUMBLE_FieldItemPickups"
COMBAT="ServerScriptService/EGGRUMBLE_SevenRoleCombat"
FEATURE="RC86_FB030_3_WEAPONS_6_PEDESTALS_SINGLE_ITEM_OWNER_20261119"
RC86_RUN=43754858996
RC86_STAGE_GITBLOB="450ba944550c3bc44ce04dc9b91da943090598d9"
RC86_STAGE_PLACE_SHA256="d67f9f68912cb67de0e184844d57649fbe50e5b70ab30cffbe3ee320e6a15cd8"

ITEM_OLD=''' session.itemStop=function()
  active=false
  if folder.Parent then folder:Destroy() end
 end'''

# Retain all nine native HEAL/DASH/SHIELD pick-ups and their fixed fair routes.
# Additional old RC86 loot uses the SAME session/guard/cooldown/Item authority.
ITEM_NEW=''' -- RC86_FB030_SIX_STAGE_WEAPONS_SINGLE_ITEM_OWNER:
 -- Six optional, world-placeable weapon buffs without a second item/remote engine.
 -- Existing nine HEAL/DASH/SHIELD sites remain byte-exact above this block.
 local stageSpecs={
  {id="SUN_BLADE",name="炎の大剣",color=Color3.fromRGB(255,131,57),damage=1.35,reach=0},
  {id="WIND_SPEAR",name="疾風の槍",color=Color3.fromRGB(77,237,190),damage=1.08,reach=3.5},
  {id="THUNDER_BOW",name="雷光の弩",color=Color3.fromRGB(177,139,255),damage=1.22,reach=1.7},
 }
 local stageBuffs:{[number]:any}={}
 local function clearStageBuff(player:Player,record:any)
  if stageBuffs[player.UserId]~=record then return end
  stageBuffs[player.UserId]=nil
  if player.Parent==Players then
   player:SetAttribute("EGGRUMBLE_StageWeaponKind",nil)
   player:SetAttribute("EGGRUMBLE_StageWeaponUntil",nil)
  end
 end
 -- Never trust client attributes to change damage. Existing authoritative Combat
 -- invokes only this server closure and limits its result to neutral M1 attacks.
 session.getStageWeaponBuff=function(player:Player):(number,number)
  local state=stageBuffs[player.UserId]
  if not state then return 1,0 end
  if not matchActive() or not canUse(player,session)
   or carryingEnemyEggs(player,session) or state.character~=player.Character
   or os.clock()>=state.expires then
   clearStageBuff(player,state)
   return 1,0
  end
  return state.damage,state.reach
 end
 if #positions>=6 then
  for index=1,6 do
   local spec=stageSpecs[(index-1)%3+1]
   local pedestal=Instance.new("Part")
   pedestal.Name="RC86_WeaponPickup_"..tostring(index).."_"..spec.id
   pedestal.Size=Vector3.new(3.4,.9,3.4)
   pedestal.Material=Enum.Material.Slate
   pedestal.Color=Color3.fromRGB(61,76,99)
   pedestal.Anchored=true;pedestal.CanCollide=false;pedestal.CanTouch=false
   pedestal.CanQuery=true
   pedestal.Position=positions[index]+Vector3.new(9,0,0)
   pedestal.Parent=folder
   local visual=Instance.new("Part")
   visual.Name="StageWeapon_"..spec.id
   visual.Size=Vector3.new(if spec.id=="WIND_SPEAR" then .65 else 2.2,2.5,.5)
   visual.Color=spec.color;visual.Material=Enum.Material.Neon
   visual.Anchored=true;visual.CanCollide=false;visual.CanTouch=false
   visual.CanQuery=false
   visual.Position=pedestal.Position+Vector3.new(0,1.5,0)
   visual.Parent=pedestal
   local prompt=Instance.new("ProximityPrompt")
   prompt.Name="RC86_StageWeaponPrompt"
   prompt.ActionText="拾う";prompt.ObjectText=spec.name.."・18秒"
   prompt.MaxActivationDistance=8;prompt.HoldDuration=.3
   prompt.RequiresLineOfSight=true;prompt.Parent=pedestal
   local visible=true
   prompt.Triggered:Connect(function(player:Player)
    if not visible or not prompt.Enabled or not matchActive()
     or not canUse(player,session) or carryingEnemyEggs(player,session) then return end
    local humanoid,root=characterState(player)
    if not root or not humanoid or humanoid.Health<=0
     or (root.Position-pedestal.Position).Magnitude>10 then return end
    -- Existing InteractionGuard is sole prompt authority (true solid-wall LOS).
    if isV3Match and not interactionGuard.allow(player,pedestal,"拾う",pedestal.Name) then return end
    visible=false;prompt.Enabled=false
    pedestal.Transparency=1;pedestal.CanQuery=false;visual.Transparency=1
    local previous=stageBuffs[player.UserId]
    if previous then clearStageBuff(player,previous) end
    local record={damage=spec.damage,reach=spec.reach,
     character=player.Character,expires=os.clock()+18,id=spec.id}
    stageBuffs[player.UserId]=record
    player:SetAttribute("EGGRUMBLE_StageWeaponKind",spec.id)
    player:SetAttribute("EGGRUMBLE_StageWeaponUntil",record.expires)
    task.delay(18,function()
     if stageBuffs[player.UserId]==record then clearStageBuff(player,record) end
    end)
    task.delay(15,function()
     if matchActive() and pedestal.Parent and not visible then
      visible=true;prompt.Enabled=true
      pedestal.Transparency=0;pedestal.CanQuery=true;visual.Transparency=0
     end
    end)
   end)
  end
 end
 session.itemStop=function()
  active=false
  for userId,record in pairs(stageBuffs) do
   local player=Players:GetPlayerByUserId(userId)
   if player then clearStageBuff(player,record) end
  end
  table.clear(stageBuffs)
  session.getStageWeaponBuff=nil
  if folder.Parent then folder:Destroy() end
 end'''

COMBAT_OLD=''' if session.swarm then count+=session.swarm.damageFromPlayer(p,at,range,damage,shape) end'''
COMBAT_NEW=''' -- RC86_FB030_SINGLE_COMBAT_NEUTRAL_M1_STAGE_BUFF:
 -- Only original Combat reads the existing ITEM author's server-local stage buff.
 local neutralAt=at
 local neutralDamage=damage
 if stageBasic==true and type(session.getStageWeaponBuff)=="function" then
  local mult,reach=session.getStageWeaponBuff(p)
  if type(mult)=="number" and mult>=1 and mult<=1.35
   and type(reach)=="number" and reach>=0 and reach<=3.5 then
   neutralDamage=damage*mult
   if reach>0 then
    local look=root.CFrame.LookVector
    local direction=Vector3.new(look.X,0,look.Z)
    if direction.Magnitude>.01 then
     local step=direction.Unit*reach
     local ray=RaycastParams.new()
     ray.FilterType=Enum.RaycastFilterType.Exclude
     ray.FilterDescendantsInstances={char}
     ray.RespectCanCollide=true
     -- The old RC86 wall/gate security fix: never project hit origin through solids.
     if workspace:Raycast(root.Position+Vector3.new(0,1.2,0),step,ray)==nil then
      neutralAt=at+step
     end
    end
   end
  end
 end
 if session.swarm then count+=session.swarm.damageFromPlayer(p,neutralAt,range,neutralDamage,shape) end'''

BASIC_OLD='''local hits=neutralAndBotHit(session,p,root,char,center,
  spec.radius,spec.damage,JOBS[role].color,spec.shape)'''
BASIC_NEW='''local hits=neutralAndBotHit(session,p,root,char,center,
  spec.radius,spec.damage,JOBS[role].color,spec.shape,true)'''

SIGNATURE_OLD='''local function neutralAndBotHit(session:any,p:Player,root:BasePart,char:Model,at:Vector3,range:number,damage:number,c:Color3,shape:string):number'''
SIGNATURE_NEW='''local function neutralAndBotHit(session:any,p:Player,root:BasePart,char:Model,at:Vector3,range:number,damage:number,c:Color3,shape:string,stageBasic:boolean?):number'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def exactly(text:str,old:str,new:str,code:str)->str:
    if text.count(old)!=1 or new in text:
        raise ValueError("RED_RC86_STAGE_SOURCE_ANCHOR_"+code)
    return text.replace(old,new,1)

def item_patch(source:str)->str:
    for needle in ("local DEFINITIONS={","local function carryingEnemyEggs(",
                   'local interactionGuard:any=if guardSource then require(guardSource) else nil',
                   'for i,pos in ipairs(positions) do'):
        if source.count(needle)!=1:
            raise ValueError("RED_RC86_ITEM_AUTHOR_DRIFT_"+needle)
    changed=exactly(source,ITEM_OLD,ITEM_NEW,"ITEM")
    if changed.replace(ITEM_NEW,ITEM_OLD,1)!=source:
        raise ValueError("RED_RC86_ITEM_UNRELATED_SOURCE_CHANGE")
    if changed.count('session.getStageWeaponBuff=function(player:Player)')!=1:
        raise ValueError("RED_RC86_ITEM_SERVER_BUFF_CALLBACK")
    return changed

def combat_patch(source:str)->str:
    if 'RC86_FB029_WIND_SINGLE_COMBAT_PORT' not in source:
        raise ValueError("RED_RC86_STAGE_MISSING_PREVIOUS_WIND_PORT")
    before=source
    source=exactly(source,SIGNATURE_OLD,SIGNATURE_NEW,"COMBAT_SIG")
    source=exactly(source,COMBAT_OLD,COMBAT_NEW,"COMBAT_HIT")
    source=exactly(source,BASIC_OLD,BASIC_NEW,"COMBAT_BASIC")
    if source.replace(BASIC_NEW,BASIC_OLD,1).replace(COMBAT_NEW,COMBAT_OLD,1).replace(SIGNATURE_NEW,SIGNATURE_OLD,1)!=before:
        raise ValueError("RED_RC86_STAGE_UNRELATED_COMBAT_CHANGE")
    for token in ("RemoteEvent","ProcessReceipt","DataStoreService",":TakeDamage("):
        if source.count(token)!=before.count(token):
            raise ValueError("RED_RC86_STAGE_NEW_GAME_DAMAGE_STORE_OWNER")
    return source

def self_test():
    item_src="\n".join(("local DEFINITIONS={","local function carryingEnemyEggs(",
           "local interactionGuard:any=if guardSource then require(guardSource) else nil",
           "for i,pos in ipairs(positions) do",ITEM_OLD))
    out=item_patch(item_src)
    assert out.replace(ITEM_NEW,ITEM_OLD,1)==item_src
    assert "SUN_BLADE" in out and "WIND_SPEAR" in out and "THUNDER_BOW" in out
    combat_src="\n".join(("RC86_FB029_WIND_SINGLE_COMBAT_PORT",SIGNATURE_OLD,COMBAT_OLD,BASIC_OLD))
    revised=combat_patch(combat_src)
    assert revised.count("RC86_FB030_SINGLE_COMBAT_NEUTRAL_M1_STAGE_BUFF")==1
    for fn,mutant in ((item_patch,out),(item_patch,item_src.replace("session.itemStop=function()","session.itemStop=function(player)")),
                      (combat_patch,revised),(combat_patch,combat_src.replace("neutralAndBotHit","otherHit",1))):
        try:fn(mutant)
        except ValueError:pass
        else:raise AssertionError("RED_RC86_STAGE_MUTANT_ACCEPTED")
    print("RC86_FB030_3_WEAPONS_6_PEDESTALS_SAFE_PORT_NEGATIVE_FIXTURES_PASS")

def apply(project_path:Path,receipt_path:Path):
    project=json.loads(project_path.read_text(encoding="utf8"))
    receipt=json.loads(receipt_path.read_text(encoding="utf8"))
    if project.get("name")!="EGGRUMBLE_REAL65_PRIVATE_STUDIO" or len(receipt.get("sources",[]))!=65:
        raise ValueError("RED_RC86_STAGE_FORMAL_REAL65_COUNT")
    wind=receipt.get("legacy_rc86_wind")
    if not wind or wind.get("new_script_count")!=0:
        raise ValueError("RED_RC86_STAGE_PRIOR_WIND_UNVERIFIED")
    if receipt.get("legacy_rc86_stage_weapons"):
        raise ValueError("RED_RC86_STAGE_DOUBLE_PORT")
    refs={r["route"]:r for r in receipt["sources"]}
    if len(refs)!=65 or refs[ITEM]["class"]!="ModuleScript" or refs[COMBAT]["class"]!="ModuleScript":
        raise ValueError("RED_RC86_STAGE_ITEM_COMBAT_AUTHORITY")
    before={}
    for route,r in refs.items():
        node=project["tree"]
        for part in route.split("/"):node=node[part]
        path=project_path.parent/node["$path"]
        if not path.is_file() or sha(path.read_bytes())!=r["sha256"] or len(path.read_bytes())!=r["bytes"]:
            raise ValueError("RED_RC86_STAGE_PARENT_SOURCE_DRIFT_"+route)
        before[route]=(path,path.read_bytes())
    for route,modify in ((ITEM,item_patch),(COMBAT,combat_patch)):
        path,original=before[route]
        updated=modify(original.decode("utf8")).encode("utf8")
        path.write_bytes(updated)
        refs[route]["sha256"]=sha(updated)
        refs[route]["bytes"]=len(updated)
    if sum(sha(path.read_bytes())!=sha(original) for path,original in before.values())!=2:
        raise ValueError("RED_RC86_STAGE_CHANGED_SOURCE_COUNT")
    receipt["legacy_rc86_stage_weapons"]={
        "feature_id":FEATURE,"original_rc86_run":RC86_RUN,
        "original_rc86_stage_gitblob":RC86_STAGE_GITBLOB,
        "original_rc86_place_sha256":RC86_STAGE_PLACE_SHA256,
        "source_profile":"REAL65","script_count":65,
        "source_changes":[ITEM,COMBAT],"unchanged_existing_sources":63,
        "types":["SUN_BLADE","WIND_SPEAR","THUNDER_BOW"],
        "six_real_pickups":True,"original_nine_base_items_unchanged":True,
        "server_los":"Existing InteractionGuard plus wall ray before projected neutral M1",
        "authorities":"one existing FieldItemPickups and one existing Combat",
        "new_remote":0,"new_store":0,"new_damage_owner":0,
        "gameplay_scope":"server-auth pickup; 18s neutral basic-attack damage/reach; no PvP buff",
        "studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO",
        "rollback":"Remove these two source deltas, preserve prior REAL65 wind and original OFF63"}
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    for route,row in refs.items():
        path=before[route][0];data=path.read_bytes()
        if sha(data)!=row["sha256"] or len(data)!=row["bytes"]:
            raise ValueError("RED_RC86_STAGE_FINAL_SELECTED_SOURCE_LOCK_"+route)
    print("RC86_FB030_SIX_USABLE_WEAPONS_CURRENT_REAL65_63_SOURCES_UNCHANGED_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--project",type=Path)
    p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    if a.self_test:self_test()
    else:
        if not a.project or not a.receipt:p.error("--project and --receipt required")
        apply(a.project,a.receipt)
