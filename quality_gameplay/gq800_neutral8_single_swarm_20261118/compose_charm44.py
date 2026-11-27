#!/usr/bin/env python3
"""Existing verified Real43 singleton Swarm + immutable #801 curse policy -> Real44.
No extra HP, spawner, KO, remote, store, or score writer. Experimental Studio profile.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re
from pathlib import Path

FINISHER=("ServerScriptService","EGGRUMBLE_NeutralFinisherPolicy")
CHARM=("ServerScriptService","EGGRUMBLE_CurseConversionPolicy")
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
CHARM_BLOB="0bd81a807ff6a935642a660b9fe9e0fd05ef484c"

def blob(data:bytes)->str:
 return hashlib.sha1(("blob %d"%len(data)).encode()+b"\0"+data).hexdigest()

def flatten(project:Path):
 project=project.resolve(strict=True)
 doc=json.loads(project.read_text(encoding="utf8"))
 found={}
 def visit(node,path=()):
  for name,item in node.items():
   if name.startswith("$"): continue
   route=path+(name,)
   if "$path" in item:
    if route in found: raise ValueError("RED_DUPLICATE_RUNTIME_ROUTE")
    found[route]=(project.parent/item["$path"]).resolve(strict=True)
   else:visit(item,route)
 visit(doc["tree"])
 return doc,found

def patch(source:str)->str:
 def once(old:str,new:str,why:str):
  nonlocal source
  if source.count(old)!=1:raise ValueError("RED_ANCHOR_"+why+"_"+str(source.count(old)))
  source=source.replace(old,new,1)
 once('local NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))',
  'local NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))\nlocal CurseConversionPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_CurseConversionPolicy"))',
  "ORIGINAL_POLICY_REQUIRE")

 # Session-scoped state, not another neutral controller.
 once(' local hitSerial=0\n',''' local hitSerial=0
 local curseEpoch=tostring(session.world)
 local curseStates:{[string]:any}={}
 local charmedByModel:{[Model]:any}={}
 local neutralById:{[string]:Model}={}
 local lastCharmAttack:{[Model]:number}={}
 local function currentZombie(user:Player?):boolean
  if not user or user:GetAttribute("EGGRUMBLE_Role")~="ZOMBIE" then return false end
  if not session.isCurrentHuman or session.isCurrentHuman(user)~=true then return false end
  local c=session.rules.castles[tostring(user.UserId)]
  local ch=user.Character
  local h=ch and ch:FindFirstChildOfClass("Humanoid")
  return c~=nil and c.alive==true and ch~=nil and h~=nil and h.Health>0
 end
 local function releaseCharmed(model:Model)
  local rec=charmedByModel[model]
  if not rec then return end
  charmedByModel[model]=nil
  lastCharmAttack[model]=nil
  model:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",nil)
  model:SetAttribute("EGGRUMBLE_NeutralCharmUntil",nil)
  model:SetAttribute("EGGRUMBLE_NeutralSeals",nil)
  local accent=model:FindFirstChild("SpeciesAccent")
  if accent and accent:IsA("BasePart") then accent.Color=rec.originalColor end
 end
''',"SESSION_CHARM_STATE")
 # Reuse each actual spawned model's serial as a unique per-session key, never Model.Name.
 # Existing Real43 preserves the earlier KoFence-safe spawn wrapper; its
 # local model variable is not the simplistic preview 'm'. Capture actual owner.
 added=re.findall(r"(?m)^([ \t]*)live\[([A-Za-z_]\w*)\]=h[ \t]*$",source)
 if len(added)!=1:raise ValueError("RED_REAL43_LIVE_SPAWN_ANCHOR_"+str(len(added)))
 indent,actor=added[0]
 marker=indent+"live["+actor+"]=h"
 source=source.replace(marker,marker+"""
"""+indent+"local neutralId=tostring(spawnSerial)"+"""
"""+indent+actor+':SetAttribute("EGGRUMBLE_NeutralInstanceId",neutralId)'+"""
"""+indent+"neutralById[neutralId]="+actor,1)
 dead=re.findall(r"(?m)^([ \t]*)live\[([A-Za-z_]\w*)\]=nil[ \t]*$",source)
 if len(dead)!=1 or dead[0][1]!=actor:
  raise ValueError("RED_REAL43_LIVE_DEATH_ANCHOR_"+str(dead))
 dead_indent=dead[0][0]; dead_marker=dead_indent+"live["+actor+"]=nil"
 source=source.replace(dead_marker,dead_marker+"""
"""+dead_indent+"neutralById[neutralId]=nil"+"""
"""+dead_indent+"releaseCharmed("+actor+")",1)
 once('if m.Parent and h.Health>0 and m.PrimaryPart then',
  'if m.Parent and h.Health>0 and m.PrimaryPart and not charmedByModel[m] then',
  "NO_FRIENDLY_DAMAGE_TARGET")
 # Existing singleton remains the ONE damage authority. For Curse we preserve an
 # actual wounded neutral for 2 seals (4 on baby golem) instead of one-hit killing it.
 once('    h:TakeDamage(damage) -- Existing singleton HP writer; exactly once',
  '''    local directUser=Players:GetPlayerByUserId(tonumber(id) or -1)
    local isCurseAttack=currentZombie(directUser) and directUser.Character==attacker
    local effectiveDamage=damage
    if isCurseAttack and h.Health>0 then
     local cap=if model:GetAttribute("EGGRUMBLE_NeutralSpecies")=="BABY_GOLEM" then 7 else 11
     effectiveDamage=math.min(math.max(0,damage),cap)
    end
    h:TakeDamage(effectiveDamage) -- ONE existing Humanoid damage authority''',
  "CURSE_NONLETHAL_HIT")
 # All seals are based on a real HP delta, already verified by the pre-existing fence.
 once('    ImpactFeedback.hit(model,user and (user:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR")',
  '''    if isCurseAttack and user and h.Health>0 and h.MaxHealth>0 and model.PrimaryPart then
     local ownerId=tostring(user.UserId)
     local state=curseStates[ownerId]
     if not state or not state.active then
      -- Dead avatar, role switch, or epoch change retires the previous policy state.
      -- A verified living ZOMBIE re-entry starts with a clean seal ledger.
      state=CurseConversionPolicy.new(curseEpoch,ownerId)
      curseStates[ownerId]=state
     end
     local targetId=model:GetAttribute("EGGRUMBLE_NeutralInstanceId")
     local actualDistance=(model.PrimaryPart.Position-origin).Magnitude
     local numSummoned=tonumber(user:GetAttribute("EGGRUMBLE_ZombieSummonedCount"))
     -- No connected summon receipt: reserve three slots rather than risk overfill.
     if type(targetId)=="string" and actualDistance<=32 then
      local decision=CurseConversionPolicy.seal(state,os.clock(),{
       serverConfirmedHit=true,role="ZOMBIE",epoch=curseEpoch,ownerId=ownerId,
       phase=session.rules.phase,ownerAlive=true,avatarCurrent=true,
       targetKind="NEUTRAL",targetAlive=true,targetFriendly=false,
       isBoss=false,isPlayer=false,sameTeam=false,inLineOfSight=true,
       distance=actualDistance,targetId=targetId,
       species=model:GetAttribute("EGGRUMBLE_NeutralSpecies"),
       hpFraction=h.Health/h.MaxHealth,uniqueHitId=ownerId..":"..tostring(hitSerial),
       existingSummoned=if numSummoned then math.clamp(math.floor(numSummoned),0,3) else 3,
      })
      if decision and decision.kind=="CHARM" then
       -- Exactly the pre-existing actual neutral Model changes allegiance.
       local accent=model:FindFirstChild("SpeciesAccent")
       charmedByModel[model]={ownerId=ownerId,neutralId=targetId,
        originalColor=if accent and accent:IsA("BasePart") then accent.Color else Color3.new(1,1,1),
        guardPoint=model.PrimaryPart.Position}
       model:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",ownerId)
       model:SetAttribute("EGGRUMBLE_NeutralCharmUntil",decision.expires)
       h:SetAttribute("LastAttackerId",nil) -- no stale false KO on allegiance flip
       if accent and accent:IsA("BasePart") then accent.Color=Color3.fromRGB(110,232,165) end
      elseif decision and decision.kind=="SEAL" then
       model:SetAttribute("EGGRUMBLE_NeutralSeals",decision.stacks)
      end
     end
    end
    ImpactFeedback.hit(model,user and (user:GetAttribute("EGGRUMBLE_Role") or "WARRIOR") or "WARRIOR")''',
  "SERVER_HIT_SEAL")
 # Existing, server-owned API can be wired to established Zombie controls later;
 # it does not create any new RemoteEvent or client authority.
 once('  getAliveCount=function():number',
  '''  orderCharmed=function(user:Player,order:string,focusId:string?):boolean
   if not currentZombie(user) then return false end
   local state=curseStates[tostring(user.UserId)]
   if not state then return false end
   if order=="FOCUS" and (not focusId or not neutralById[focusId]
     or charmedByModel[neutralById[focusId]]) then return false end
   return CurseConversionPolicy.order(state,order,focusId)
  end,
  getAliveCount=function():number''',"SECURE_ZOMBIE_ORDERS")
 # Normal enemy pursuit excludes friendlies. Bounded session-owned companion loop
 # uses existing strike() for actual neutral-on-neutral damage/KO rather than new HP logic.
 once('     if m.Parent and m.PrimaryPart and h.Health>0 then',
  '     if m.Parent and m.PrimaryPart and h.Health>0 and not charmedByModel[m] then',
  "NO_FRIENDLY_AI_PURSUIT")
 once('   task.wait(.38)\n  end\n end)\n print("[EGGRUMBLE_SWARM]',
  '''   local now=os.clock()
   local snapNeutrals={}
   for m,rec in pairs(charmedByModel) do
    local h=live[m]
    snapNeutrals[rec.neutralId]={
     alive=m.Parent~=nil and h~=nil and h.Health>0,
     friendlyOwnerId=rec.ownerId,epoch=curseEpoch,
    }
   end
   for ownerId,state in pairs(curseStates) do
    local user=Players:GetPlayerByUserId(tonumber(ownerId) or -1)
    local current=currentZombie(user)
    local actions=CurseConversionPolicy.step(state,now,{
     epoch=curseEpoch,ownerId=ownerId,phase=session.rules.phase,
     ownerAlive=current,avatarCurrent=current,neutrals=snapNeutrals,
    })
    for _,action in ipairs(actions) do
     local model=neutralById[action.targetId]
     if action.kind=="RELEASE" and model then
      releaseCharmed(model)
     elseif action.kind=="ORDER" and model and charmedByModel[model] then
      local rec=charmedByModel[model]
      local root=model.PrimaryPart
      local ownerRoot=user and user.Character and user.Character:FindFirstChild("HumanoidRootPart")
      if root and ownerRoot and ownerRoot:IsA("BasePart") then
       local goal:Vector3=ownerRoot.Position
       if action.order=="GUARD" then goal=rec.guardPoint end
       if action.order=="FOCUS" and action.focusId then
        local focus=neutralById[action.focusId]
        if focus and focus.PrimaryPart and not charmedByModel[focus] then
         goal=focus.PrimaryPart.Position
        end
       end
       local delta=Vector3.new(goal.X-root.Position.X,0,goal.Z-root.Position.Z)
       if delta.Magnitude>4 then
        local step=delta.Unit*math.min(3.3,delta.Magnitude-4)
        local ray=RaycastParams.new()
        ray.FilterType=Enum.RaycastFilterType.Exclude
        ray.FilterDescendantsInstances={all}
        ray.RespectCanCollide=true
        if not workspace:Raycast(root.Position+Vector3.new(0,1,0),step,ray) then
         local next=root.Position+step
         -- Same #819 ground safety as unconverted neutrals; never ghost/float across void.
         local scale=(root.Size.Y/2.5)
         local ground=workspace:Raycast(next+Vector3.new(0,3,0),Vector3.new(0,-8,0),ray)
         if ground and ground.Normal.Y>=.72 then
          local desiredY=ground.Position.Y+2*scale
          if math.abs(desiredY-root.Position.Y)<=1.4 then
           local grounded=Vector3.new(next.X,desiredY,next.Z)
           model:PivotTo(CFrame.lookAt(grounded,grounded+delta.Unit))
          end
         end
        end
       end
       if now-(lastCharmAttack[model] or -100)>=1.2 then
        -- Same Swarm strike, same 24-target and ray caps, no extra writer.
        local dealt=strike(ownerId,root.Position,5,7,
         root.Position+Vector3.new(0,1,0),model,"CIRCLE")
        -- Charge cadence for every authorized attempt, including an empty swing.
        -- Otherwise up to 3 allies raycast every .38s on low-end Android.
        lastCharmAttack[model]=now
       end
      end
     end
    end
   end
   task.wait(.38)
  end
  for model in pairs(charmedByModel) do releaseCharmed(model) end
  for _,state in pairs(curseStates) do CurseConversionPolicy.retire(state) end
 end)
 print("[EGGRUMBLE_SWARM]''',"LIVE_CHARM_AI_AND_CLEANUP")
 # Ensure no extra instances of these two single authorities were added.
 if source.count('function Swarm.start(session:any)')!=1 or source.count('local function strike(')!=1:
  raise ValueError("RED_SECOND_GAMEPLAY_AUTHORITY")
 if source.count('h:TakeDamage(effectiveDamage)')!=1 or source.count('CurseConversionPolicy.seal(')!=1:
  raise ValueError("RED_NO_ACTUAL_CURSE_SEAL")
 for keep in ("KoFence.mayCredit(session,id,m,all)","neutralBudget:acquire","SpawnPacing.step","EncounterFair"):
  if keep not in source:raise ValueError("RED_LOST_EXISTING_SWARM_"+keep)
 if any(x in source for x in ("RemoteEvent","DataStoreService","MarketplaceService")):
  raise ValueError("RED_NEW_REMOTE_STORE")
 return source

def compose(original43:Path,curse:Path,out:Path):
 original43=original43.resolve(strict=True);curse=curse.resolve(strict=True);out=out.resolve()
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 doc,original=flatten(original43)
 if len(original)!=43 or not {SWARM,FINISHER}.issubset(original) or CHARM in original:
  raise ValueError("RED_NOT_ORIGINAL43_SINGLE_AUTHORITY")
 if blob(curse.read_bytes())!=CHARM_BLOB:
  raise ValueError("RED_CURSE_POLICY_ORIGINAL_AUTHOR_SHA_MISMATCH")
 baseline=original[SWARM].read_text(encoding="utf8")
 selected=patch(baseline)
 out.parent.mkdir(parents=True,exist_ok=True)
 path=out.parent/"EGGRUMBLE_SwarmCombat_Real44.luau"
 path.write_text(selected,encoding="utf8",newline="\n")
 target=copy.deepcopy(doc)
 def relink(node,base=()):
  for key,val in node.items():
   if key.startswith("$"):continue
   route=base+(key,)
   if "$path" in val:
    chosen=path if route==SWARM else original[route]
    val["$path"]=os.path.relpath(chosen,out.parent).replace(os.sep,"/")
   else:relink(val,route)
 relink(target["tree"])
 target["tree"]["ServerScriptService"][CHARM[-1]]={
  "$path":os.path.relpath(curse,out.parent).replace(os.sep,"/")}
 target["name"]="GQ800_REAL44_CURSE_NEUTRAL_STUDIO_PREP_NOT_OFFICIAL"
 out.write_text(json.dumps(target,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 _,selected_paths=flatten(out)
 if len(selected_paths)!=44 or set(selected_paths)!=(set(original)|{CHARM}):
  raise ValueError("RED_NOT_REAL44_SINGLE_SWARM")
 for route,path_before in original.items():
  if route!=SWARM and selected_paths[route].read_bytes()!=path_before.read_bytes():
   raise ValueError("RED_OTHER_GAMEPLAY_SOURCE_MUTATED_"+"/".join(route))
 if selected_paths[CHARM].read_bytes()!=curse.read_bytes():
  raise ValueError("RED_CURSE_SOURCE_SELECTION_CHANGED")
 receipt={"feature_id":"GQ800_LIVE_CURSE_NEUTRAL_ADAPTER_20261119",
          "baseline_script_count":43,"candidate_script_count":44,
          "single_swarm":True,"only_original_source_modified":"ServerScriptService/EGGRUMBLE_SwarmCombat",
          "upstream_original_curse_blob":CHARM_BLOB,
          "remaining_unchanged_original":42,
          "source_only":True,"official_rc_adopted":False,
          "studio_2client":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO"}
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ800_CHARM_REAL44_SELECTED_SINGLETON_SOURCE_PASS")
 return receipt

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--original43",required=True,type=Path)
 p.add_argument("--curse",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args()
 compose(a.original43,a.curse,a.out)
