#!/usr/bin/env python3
"""Execute the ACTUAL selected motionProfile/rotate Luau in a mock CFrame-only harness.

This is a native Luau logic contract, NOT a Roblox Studio engine or animation test.
"""
from __future__ import annotations
import argparse,hashlib,re
from pathlib import Path
from gate import selected,ROUTE,NEW

STUB=r'''--!strict
-- Exact selected Luau functions run against a minimal additive rotation algebra.
-- This mock has NO Roblox engine, avatar skeleton, rendering, or network.
local FRAME_MT={}
FRAME_MT.__index=FRAME_MT
FRAME_MT.__mul=function(a,b)
 return setmetatable({p=a.p+b.p,y=a.y+b.y,r=a.r+b.r},FRAME_MT)
end
local CFrame={}
function CFrame.new()
 return setmetatable({p=0,y=0,r=0},FRAME_MT)
end
function CFrame.Angles(p,y,r)
 return setmetatable({p=p,y=y,r=r},FRAME_MT)
end
'''
CHECKS=r'''
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local slots={"A","B","C"}
local function magnitude(cf)
 return math.abs(cf.p)+math.abs(cf.y)+math.abs(cf.r)
end
local function distance(a,b)
 return math.abs(a.p-b.p)+math.abs(a.y-b.y)+math.abs(a.r-b.r)
end
local function finite(x)
 assert(x==x and x<1e6 and x>-1e6, "NUMERIC_NAN_INF")
end
local function sample(role,slot,t)
 local a,b,c=rotate(role,slot,t)
 for _,cf in ipairs({a,b,c}) do
  for _,n in ipairs({cf.p,cf.y,cf.r}) do finite(n) end
 end
 return a,b,c
end
local cases=0
for _,role in ipairs(roles) do
 for _,slot in ipairs(slots) do
  local a0,b0,c0=sample(role,slot,0)
  local a1,b1,c1=sample(role,slot,1)
  assert(magnitude(a0)+magnitude(b0)+magnitude(c0)<1e-9,"START_POSE_NON_NEUTRAL")
  assert(magnitude(a1)+magnitude(b1)+magnitude(c1)<1e-9,"END_POSE_NON_NEUTRAL")
  local amid,bmid,cmid=sample(role,slot,.42)
  assert(magnitude(amid)+magnitude(bmid)+magnitude(cmid)>.25,"NO_VISIBLE_STRIKE")
  local aanti,banti,canti=sample(role,slot,.18)
  assert(magnitude(aanti)+magnitude(banti)+magnitude(canti)>.02,"NO_ANTICIPATION")
  local edges=(slot=="A") and {.18,.36,.62} or {.18,.42,.54}
  for _,edge in ipairs(edges) do
   local la,lb,lc=sample(role,slot,edge-.00001)
   local ra,rb,rc=sample(role,slot,edge+.00001)
   assert(distance(la,ra)+distance(lb,rb)+distance(lc,rc)<.01,"MOTION_PHASE_DISCONTINUITY")
  end
  for i=0,100 do sample(role,slot,i/100) end
  cases+=1
 end
 local aA,bA,cA=sample(role,"A",.42)
 local aB,bB,cB=sample(role,"B",.42)
 local aC,bC,cC=sample(role,"C",.42)
 assert(distance(aA,aB)+distance(bA,bB)+distance(cA,cB)>.01,"SLOT_B_SAME_AS_A")
 assert(distance(aA,aC)+distance(bA,bC)+distance(cA,cC)>.01,"SLOT_C_SAME_AS_A")
end
assert(cases==21,"ROLE_SLOT_21")
local anticipation,preflash=motionProfile(.18,"A")
local strike,flash=motionProfile(.36,"A")
local recovery,last=motionProfile(1,"A")
local bhit,bflash=motionProfile(.42,"B")
local chit,cflash=motionProfile(.42,"C")
local aminHoldSeconds=.26*(.62-.36)
assert(anticipation<0 and preflash==0 and strike==1 and flash==1
 and recovery==0 and last==0 and bhit==1 and bflash==1
 and chit==1 and cflash==1,"PHASE_CONTRACT")
-- On p10 25fps (40ms/frame), 67.6ms display hold spans >1 refresh period.
-- This numeric source test does NOT prove real render or visual perceived quality.
assert(aminHoldSeconds>.06 and aminHoldSeconds<.08,"A_25FPS_HIT_HOLD_TOO_SHORT")
print("GQ470_ROLE_MOTION_LUAU_RUNTIME21_7ROLES_3SLOTS_100SAMPLES_PHASE_PASS_NOT_STUDIO")
'''

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 scripts=selected(a.root)
 code=scripts[ROUTE].read_text()
 assert hashlib.sha256(code.encode()).hexdigest()==NEW,"WRONG_REAL_SELECTED_LUA_SOURCE"
 start=code.index("local function smoothstep(t:number)")
 stop=code.index("local function nearby(character:Model)")
 piece=code[start:stop]
 assert piece.count("local function motionProfile(")==1
 assert piece.count("local function rotate(")==1
 assert piece.count("return right,left,waist")==1
 assert "EGGRUMBLE_SkillCastSignature" in code
 assert "if not RunService:IsStudio() then return end" in code
 a.out.write_text(STUB+"\n"+piece+"\n"+CHECKS)
 print("GQ470_MOTION_NATIVE_HARNESS_EXTRACTED_FROM_REAL_SELECTED_LUA_SOURCE")
if __name__=="__main__":main()
