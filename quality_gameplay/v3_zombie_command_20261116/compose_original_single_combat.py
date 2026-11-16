#!/usr/bin/env python3
"""Inline unique #582 zombie policy/runtime into ONE original SevenRoleCombat.

SOURCE_CANDIDATE ONLY. This does NOT change active RC, install 32nd Script,
or claim live Roblox acceptance. To apply to official RC use the latest
composed 31-project Combat and repeat full-31 source/class/native/Rojo gates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ORIGINAL_COMBAT_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"
HERO_ANCHOR = "local HeroCombat={}\n"
OLD_ZOMBIE = ''' elseif role=="ZOMBIE" then
  if slot=="A" then blast()
  elseif slot=="B" then
   blast()
  else
   for i=1,3 do
    local puppet=makeEffect(session.world,rootAdvance(root,5+i*3),Vector3.new(3,7,3),def.color,2.4)
    puppet.Name="CurseUndead_"..i
    task.delay(i*.22,function()
     if session.rules.phase=="ACTIVE" and owner.alive and root.Parent then blast(spec.reach+(i-2)*3) end
    end)
   end
  end
'''
# The existing one server-authoritative damage function must perform the
# real hit. It uses the original Combat's attacker/owner/session/LOS checks.
NEW_ZOMBIE = ''' elseif role=="ZOMBIE" then
  -- A: retask FOLLOW; B: retask GUARD; C: spawn 3 real Humanoid servants.
  if slot=="A" then
   ZombieCommander.order(p,"FOLLOW",nil)
   blast()
  elseif slot=="B" then
   ZombieCommander.order(p,"GUARD",nil)
   blast()
  else
   local matchToken=tostring(session)
   -- Weak per-instance keys, monotonic IDs: two NeutralHorde models can share Name.
   -- The same model keeps its ID even if a different neutral dies or reorders.
   local neutralIds=setmetatable({}, {__mode="k"})
   local nextNeutralId=0
   local function neutralTargetId(enemy:Model):string
    local id=neutralIds[enemy]
    if id then return id end
    nextNeutralId+=1
    id="N:"..tostring(p.UserId)..":"..tostring(nextNeutralId)
    neutralIds[enemy]=id
    return id
   end
   local function commanderSnapshot(_player:Player):any
    local state=session.rules.castles[tostring(p.UserId)]
    local alive=state~=nil and state.alive and p.Character==char and h.Health>0
     and session.rules.phase=="ACTIVE" and p:GetAttribute("EGGRUMBLE_Role")=="ZOMBIE"
     and (session.isCurrentHuman==nil or session.isCurrentHuman(p)==true)
    local targets={}
    if alive then
     for _,other in ipairs(game:GetService("Players"):GetPlayers()) do
      local c=session.rules.castles[tostring(other.UserId)]
      local theirChar,theirRoot,theirHum=characterOf(other)
      if other~=p and c and c.alive and theirRoot and theirHum
       and theirHum.Health>0
       and (session.isCurrentHuman==nil or session.isCurrentHuman(other)==true)
       and (session.mode~="TEAM" or c.team~=state.team) then
       table.insert(targets,{id="H:"..tostring(other.UserId),kind="ENEMY_PLAYER",
        x=theirRoot.Position.X,z=theirRoot.Position.Z,active=true,
        matchToken=matchToken,friendly=false})
      end
     end
     for id,enemy in pairs(session.botActors or {}) do
      local c=session.rules.castles[id]
      local er=enemy and enemy.PrimaryPart
      local eh=enemy and enemy:FindFirstChildOfClass("Humanoid")
      if c and c.alive and er and eh and eh.Health>0
       and (session.mode~="TEAM" or c.team~=state.team) then
       table.insert(targets,{id="B:"..id,kind="ENEMY_BOT",
        x=er.Position.X,z=er.Position.Z,active=true,
        matchToken=matchToken,friendly=false})
      end
     end
     local horde=session.world:FindFirstChild("NeutralHorde")
     if horde then
      for _,enemy in ipairs(horde:GetChildren()) do
       if enemy:IsA("Model") then
        local er=enemy.PrimaryPart
        local eh=enemy:FindFirstChildOfClass("Humanoid")
        if er and eh and eh.Health>0 then
         table.insert(targets,{id=neutralTargetId(enemy),kind="NEUTRAL",
          x=er.Position.X,z=er.Position.Z,active=true,
          matchToken=matchToken,friendly=false})
        end
       end
      end
     end
    end
    return {
     ownerId=tostring(p.UserId), ownerAlive=alive==true,
     phase=session.rules.phase, matchToken=matchToken,
     ownerPosition={x=root.Position.X,z=root.Position.Z},
     guardPoint=if session.castleLocations[tostring(p.UserId)]
       then {x=session.castleLocations[tostring(p.UserId)].X,
             z=session.castleLocations[tostring(p.UserId)].Z}
       else {x=root.Position.X,z=root.Position.Z},
     targets=targets,
     visible=function(ax:number,az:number,tx:number,tz:number):boolean
      local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
      local servants=session.world:FindFirstChild("EGGRUMBLE_ZombieServants_"..tostring(p.UserId))
      ray.FilterDescendantsInstances=if servants then {char,servants} else {char}
      ray.RespectCanCollide=true
      local origin=Vector3.new(ax,root.Position.Y+2,az)
      local endpoint=Vector3.new(tx,root.Position.Y+2,tz)
      local delta=endpoint-origin
      if delta.Magnitude<.01 then return true end
      local obstruction=workspace:Raycast(origin,delta,ray)
      return obstruction==nil or obstruction.Distance>=delta.Magnitude-2
     end,
    }
   end
   local function commanderHit(player:Player,targetId:string,damage:number,token:string,minionRoot:BasePart):()
    -- Never expose a new damage authority: one existing author Combat decides.
    if player~=p or token~=matchToken or p.Character~=char
     or not minionRoot or not minionRoot:IsDescendantOf(session.world)
     or h.Health<=0 or session.rules.phase~="ACTIVE" or not owner.alive then return end
    if p:GetAttribute("EGGRUMBLE_Role")~="ZOMBIE" then return end
    local fresh=commanderSnapshot(p)
    if fresh.ownerAlive~=true or fresh.phase~="ACTIVE" then return end
    for _,candidate in ipairs(fresh.targets) do
     if candidate.id==targetId and candidate.active and not candidate.friendly then
      local at=Vector3.new(candidate.x,root.Position.Y,candidate.z)
      -- Keep servants inside the original author's player-attack maximum.
      if (at-minionRoot.Position).Magnitude<=6
       and minionRoot.Parent and minionRoot.Parent:IsA("Model")
       and fresh.visible(minionRoot.Position.X,minionRoot.Position.Z,candidate.x,candidate.z)==true then
       -- Hit from the actual summoned body, never remotely from the caster.
       neutralAndBotHit(session,p,minionRoot,minionRoot.Parent,at,3,math.min(damage,6),def.color,spec.shape)
      end
      return
     end
    end
   end
   ZombieCommander.begin(p,{
    matchToken=matchToken,ownerId=tostring(p.UserId),world=session.world,
    snapshot=commanderSnapshot,hit=commanderHit
   })
  end
'''

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def compose(original: str, policy: str, runtime: str) -> str:
    if original.count(HERO_ANCHOR) != 1 or original.count(OLD_ZOMBIE) != 1:
        raise ValueError("RED_ORIGINAL_COMBAT_ANCHOR_DRIFT")
    if not original.rstrip().endswith("return HeroCombat"):
        raise ValueError("RED_ORIGINAL_COMBAT_AUTHORITY_DRIFT")
    if not policy.startswith("--!strict") or policy.count("return Policy") != 1:
        raise ValueError("RED_POLICY_BLOB_DRIFT")
    if runtime.count('local Policy = require(script.Parent.EGGRUMBLE_ZombieOrderPolicy)') != 1:
        raise ValueError("RED_RUNTIME_BLOB_DRIFT")
    policy_body=policy.replace("--!strict\n","",1).replace("return Policy\n","",1)
    runtime_body=runtime.replace("--!strict\n","",1)
    runtime_body=runtime_body.replace('local RunService = game:GetService("RunService")\n','',1)
    runtime_body=runtime_body.replace('local Policy = require(script.Parent.EGGRUMBLE_ZombieOrderPolicy)\n','',1)
    runtime_body=runtime_body.replace("return Runtime\n","",1)
    inline=('local ZombieCommander=(function()\n'
            + policy_body + "\n" + runtime_body
            + "\nreturn Runtime\nend)()\n")
    replaced=original.replace(HERO_ANCHOR,HERO_ANCHOR+inline,1)
    replaced=replaced.replace(OLD_ZOMBIE,NEW_ZOMBIE,1)
    # Hard OFF restore yields the exact original Combat without touching other jobs.
    assert replaced.replace(HERO_ANCHOR+inline,HERO_ANCHOR,1).replace(
        NEW_ZOMBIE,OLD_ZOMBIE,1)==original
    return replaced

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--combat",type=Path,required=True)
    parser.add_argument("--policy",type=Path,required=True)
    parser.add_argument("--runtime",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    original_bytes=args.combat.read_bytes()
    if git_blob(original_bytes)!=ORIGINAL_COMBAT_BLOB:
        raise ValueError("RED_ORIGINAL_482_COMBAT_BLOB_UNEXPECTED")
    original=original_bytes.decode("utf-8")
    result=compose(original,args.policy.read_text(),args.runtime.read_text())
    if args.out.exists(): raise ValueError("RED_OUTPUT_MUST_BE_NEW")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(result,encoding="utf-8")
    receipt={
      "source":"#482 immutable frozen original (not latest official Combat)",
      "original_combat_git_blob":ORIGINAL_COMBAT_BLOB,
      "source_count_changed":0,
      "single_combat_source_change":True,
      "other_six_roles_and_all_author_functions_byte_exact":True,
      "off_rollback_original_combat_byte_exact":True,
      "new_combat_sha256":hashlib.sha256(result.encode()).hexdigest(),
      "new_combat_bytes":len(result.encode()),
      "formal_rc_adopted":False,
      "studio_tested":False,"android_tested":False,
      "needed_next":"Integrate after latest official31 and rerun all 31 native+Rojo/CAS"
    }
    args.receipt.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("GQ_ZOMBIE_ORIGINAL_AUTHOR_SINGLE_COMBAT_INLINE_AND_OFF_ROLLBACK_PASS")
if __name__=="__main__":
    main()
