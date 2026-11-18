#!/usr/bin/env python3
"""Reversible one-module overlay for ORIGINAL #764 subsea neutral melee occlusion.

Does not alter Realm station prompts (#792), HUD (#795), legacy LSS, Host,
Game, Combat, Swarm, Score, item rules or any public publisher.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

FEATURE_ID="GQ8_SUBSEA_LEVIATHAN_MELEE_LOS_20261118"
UPSTREAM_HEAD="c51de1ed4feb7a7500ada95d21282402053ef988"
UPSTREAM_BLOB="1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1"
UPSTREAM_PATH="handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleCore.server.luau"
INSERT_AT=""" local elapsed=0
 local heartbeat
"""
HELPER="""  -- Only the existing subsea Leviathan may apply its 6HP melee to players
  -- with a truly unobstructed path. Ignore attacker and target avatar only.
  local function clearSubseaMeleePath(creature,targetCharacter,targetRoot)
   if not creature or not creature.Parent or not targetCharacter
    or not targetRoot or not targetRoot.Parent then return false end
   local from=creature:GetPivot().Position
   local delta=targetRoot.Position-from
   if delta.Magnitude<.01 then return false end
   local ray=RaycastParams.new()
   ray.FilterType=Enum.RaycastFilterType.Exclude
   ray.FilterDescendantsInstances={creature,targetCharacter}
   ray.RespectCanCollide=true
   return Workspace:Raycast(from,delta,ray)==nil
  end
"""
OLD_MELEE="""     elseif root and now-data.lastHit>=2 then
      data.lastHit=now
      local h=nearest.Character:FindFirstChildOfClass("Humanoid")
      if h then h:TakeDamage(6) end -- new underwater neutral only, no KO/score
"""
NEW_MELEE="""     elseif root and now-data.lastHit>=2 then
      local h=nearest.Character:FindFirstChildOfClass("Humanoid")
      if h and clearSubseaMeleePath(creature,nearest.Character,root) then
       -- A blocked swing is not a successful attack and spends no cooldown.
       data.lastHit=now
       h:TakeDamage(6) -- subsea neutral only, never alter KO/score ownership
      end
"""

def git_blob_sha(content:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()

def apply(original:bytes)->bytes:
    if git_blob_sha(original)!=UPSTREAM_BLOB:
        raise ValueError("RED_GQ8_SUBSEA_ORIGINAL_BLOB_DRIFT")
    text=original.decode("utf-8")
    if text.count(INSERT_AT)!=1 or text.count(OLD_MELEE)!=1 or HELPER in text or NEW_MELEE in text:
        raise ValueError("RED_GQ8_SUBSEA_ORIGINAL_ANCHOR_DRIFT")
    selected=text.replace(INSERT_AT,HELPER+INSERT_AT,1).replace(OLD_MELEE,NEW_MELEE,1).encode()
    if rollback(selected)!=original:
        raise ValueError("RED_GQ8_SUBSEA_ROLLBACK_INEXACT")
    return selected

def rollback(selected:bytes)->bytes:
    text=selected.decode("utf-8")
    if text.count(HELPER)!=1 or text.count(NEW_MELEE)!=1 or OLD_MELEE in text:
        raise ValueError("RED_GQ8_SUBSEA_SELECTED_DRIFT")
    restored=text.replace(HELPER,"",1).replace(NEW_MELEE,OLD_MELEE,1).encode()
    if git_blob_sha(restored)!=UPSTREAM_BLOB:
        raise ValueError("RED_GQ8_SUBSEA_INVERSE_BLOB_DRIFT")
    return restored

def native_harness(selected:bytes)->str:
    """Execute EXACT selected helper and melee branch in Luau with mocked physics."""
    src=selected.decode()
    assert src.count(HELPER)==src.count(NEW_MELEE)==1
    # Include original helper code, not a rewritten simulation implementation.
    helper=HELPER
    # Exact original-source gameplay branch, recast from elseif to if for isolated VM.
    branch=NEW_MELEE.replace("     elseif root and now-data.lastHit>=2 then",
                               "     if root and now-data.lastHit>=2 then",1)
    harness=r'''local Enum={RaycastFilterType={Exclude="Exclude"}}
local RaycastParams={new=function() return {} end}
local blocked=nil
local calls=0
local seen=nil
local Workspace={Raycast=function(self,origin,delta,params)
  calls+=1
  seen=params
  return blocked
end}
local function vector(x,y,z)
  local v={x=x,y=y,z=z}
  local meta={}
  meta.__sub=function(a,b)
    local dx,dy,dz=a.x-b.x,a.y-b.y,a.z-b.z
    return setmetatable({x=dx,y=dy,z=dz,Magnitude=math.sqrt(dx*dx+dy*dy+dz*dz)},meta)
  end
  return setmetatable(v,meta)
end
local avatar={Parent=true}
local root={Position=vector(2,0,0),Parent=avatar}
local creature={Parent=true,GetPivot=function() return {Position=vector(0,0,0)} end}
local hits=0
local humanoid={TakeDamage=function(self,n) assert(n==6);hits+=1 end}
function avatar:FindFirstChildOfClass(kind) assert(kind=="Humanoid");return humanoid end
local nearest={Character=avatar}
local data={lastHit=0}
local now=3
'''
    harness+=helper
    harness+="local function attemptHit()\n"+branch+"      end\nend\n"
    harness+=r'''
assert(clearSubseaMeleePath(creature,avatar,root),"empty path must pass")
assert(seen.FilterType=="Exclude" and seen.RespectCanCollide==true)
assert(#seen.FilterDescendantsInstances==2)
assert(seen.FilterDescendantsInstances[1]==creature)
assert(seen.FilterDescendantsInstances[2]==avatar)
blocked={Instance={Name="SolidCoral"}}
assert(not clearSubseaMeleePath(creature,avatar,root),"solid coral must block")
blocked={Instance={Name="CastleWall"}}
assert(not clearSubseaMeleePath(creature,avatar,root),"solid castle must block")
blocked=nil
assert(not clearSubseaMeleePath({Parent=nil},avatar,root),"retired creature must be rejected")
assert(not clearSubseaMeleePath(creature,nil,root),"missing target rejected")
assert(not clearSubseaMeleePath(creature,avatar,{Parent=nil,Position=root.Position}),"missing root parent")
assert(not clearSubseaMeleePath(creature,avatar,{Parent=avatar,Position=vector(0,0,0)}),"zero vector rejected")
blocked={Instance={Name="Reef"}}
attemptHit()
assert(hits==0 and data.lastHit==0,"blocked hit must not damage or consume attack cooldown")
blocked=nil
attemptHit()
assert(hits==1 and data.lastHit==3,"clear hit must apply exactly 6hp and stamp cooldown")
now=3.5
attemptHit()
assert(hits==1 and data.lastHit==3,"2s cooldown cannot multi-hit")
now=5
blocked={Instance={Name="Stone"}}
attemptHit()
assert(hits==1 and data.lastHit==3,"blocked second swing must not stamp cooldown")
blocked=nil
attemptHit()
assert(hits==2 and data.lastHit==5,"unblocked attack after wall clears")
print("GQ8_SUBSEA_REAL_SOURCE_NATIVE_13_CASES_PASS")
'''
    return harness

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--rollback",action="store_true")
    p.add_argument("--harness",type=Path)
    a=p.parse_args()
    b=a.source.read_bytes()
    output=rollback(b) if a.rollback else apply(b)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(output)
    if a.harness and not a.rollback:
        a.harness.parent.mkdir(parents=True,exist_ok=True)
        a.harness.write_text(native_harness(output))
    print(FEATURE_ID,"ROLLBACK" if a.rollback else "ON",
          hashlib.sha256(output).hexdigest(),len(output),"source only")

if __name__=="__main__":
    main()
