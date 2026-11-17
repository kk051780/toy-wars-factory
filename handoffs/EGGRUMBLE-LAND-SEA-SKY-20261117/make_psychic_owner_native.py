#!/usr/bin/env python3
"""Extract the exact psychic trap Touched callback from the real LSS source.

The simulated Luau state deliberately tests a former caster, dead caster,
replaced avatar, valid BR victim and invalid/long-distance targets. A mutant
that removes the caster guard must fail its negative cases.
"""
from __future__ import annotations
import argparse
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"EGGRUMBLE_LandSeaSkyTraversal.server.luau"
BEGIN="   t.Touched:Connect(function(other)\n"
END="\n   end)\n   Debris:AddItem"
OWNER_CHECK='''    if not matchHuman(owner,mode,world,"TRAPPER")
     or casterHumanoid.Health<=0 or owner.Character~=casterCharacter then
     t:Destroy()
     return
    end
'''
HEAD=r'''
local function vec(x)
 return setmetatable({X=x},{
  __sub=function(a,b)
   return {Magnitude=math.abs(a.X-b.X)}
  end,
  __add=function(a,b)
   return vec(a.X+b.X)
  end
 })
end
local Vector3={new=function(x,y,z) return vec(x) end}
local function simulate(case)
 local owner={Character={},Parent=true}
 local casterCharacter=owner.Character
 local casterHumanoid={Health=100}
 local guest={Parent=true}
 local guestCurrent=true
 local ownerCurrent=true
 if case=="old_owner" then ownerCurrent=false end
 if case=="dead_owner" then casterHumanoid.Health=0 end
 if case=="different_avatar" then owner.Character={} end
 if case=="old_guest" then guestCurrent=false end
 local touchedByOwner=case=="owner_touched"
 local rootX=if case=="far_guest" then 30 else 0
 local ch={}
 guest.Character=ch
 if case=="old_guest_avatar" then guest.Character={} end
 function ch:FindFirstChildOfClass(name)
  if name=="Humanoid" then
   return {Health=if case=="dead_guest" then 0 else 100}
  end
  return nil
 end
 function ch:FindFirstChild(name)
  if name=="HumanoidRootPart" then return {Position=vec(rootX)} end
  return nil
 end
 local other={}
 function other:FindFirstAncestorOfClass(name)
  if name=="Model" then return ch end
  return nil
 end
 local Players={}
 function Players:GetPlayerFromCharacter(_model)
  return if touchedByOwner then owner else guest
 end
 local mode="BATTLE_ROYALE"
 local world={}
 local function matchHuman(p,_,_,role)
  if p==owner then return ownerCurrent and role=="TRAPPER" end
  if p==guest then return guestCurrent and role==nil end
  return false
 end
 local teleports=0
 local function safeMove(p,at,m,w)
  assert(p==guest and m==mode and w==world)
  if case=="move_rejected" then return false end
  teleports+=1
  return true
 end
 local seaRaft={Position=vec(15)}
 local t={Parent=true,Position=vec(0)}
 local destroys=0
 function t:Destroy() self.Parent=nil;destroys+=1 end
 local fired=false
 local active=true
 local function touched(other)
'''
FOOT=r'''
 end
 touched(other)
 return teleports,destroys,t.Parent
end

local tele,dead=simulate("valid")
assert(tele==1 and dead==1,"VALID_BR_TARGET_NOT_TELEPORTED")
for _,case in ipairs({"old_owner","dead_owner","different_avatar"}) do
 local n,k=simulate(case)
 assert(n==0 and k==1,"RED_CASTER_LEFT_ACTIVE_TRAP_"..case)
end
for _,case in ipairs({"old_guest","old_guest_avatar","dead_guest",
                     "far_guest","owner_touched","move_rejected"}) do
 local n,k,parent=simulate(case)
 assert(n==0 and k==0 and parent,"RED_ILLEGAL_VICTIM_"..case)
end
print("LSS_ACTUAL_PSYCHIC_OWNER_LUAU_10_CASES_PASS")
'''

def extract(text: str) -> str:
    if text.count(BEGIN)!=1 or text.count(END)!=1:
        raise ValueError("RED_PSYCHIC_CALLBACK_DRIFT")
    body=text.split(BEGIN,1)[1].split(END,1)[0]
    if body.count(OWNER_CHECK)!=1:
        raise ValueError("RED_MISSING_CASTER_GUARD")
    if "safeMove(guest," not in body or "matchHuman(guest,mode,world,nil)" not in body:
        raise ValueError("RED_TRAP_TARGET_AUTHORITY_DRIFT")
    return body

def write(out:Path, mutant:Path)->None:
    body=extract(SOURCE.read_text(encoding="utf-8"))
    out.write_text(HEAD+body+"\n"+FOOT,encoding="utf-8")
    mutant.write_text(HEAD+body.replace(OWNER_CHECK,"",1)+"\n"+FOOT,encoding="utf-8")
    print("LSS_ACTUAL_PSYCHIC_CALLBACK_NATIVE_EXTRACTION_OK")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mutant",type=Path,required=True)
    a=p.parse_args();write(a.out,a.mutant)

if __name__=="__main__":main()
