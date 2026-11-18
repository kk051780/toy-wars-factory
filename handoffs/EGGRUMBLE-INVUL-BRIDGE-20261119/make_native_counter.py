#!/usr/bin/env python3
"""Execute authentic policy+counter module via pinned Native Luau.
Only mock Roblox engine objects, never duplicate the counter implementation.
"""
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
COUNTER=ROOT/"EGGRUMBLE_InvulCounterNeutral.luau"
BODY=r'''
local POS={}
POS.__index=function(v,k)
 if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 return POS[k]
end
POS.__sub=function(a,b) return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},POS) end
POS.__add=function(a,b) return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},POS) end
local Vector3={new=function(x,y,z)return setmetatable({X=x,Y=y,Z=z},POS) end}
local Enum={RaycastFilterType={Exclude="Exclude"}}
local RaycastParams={new=function()return {} end}
local workspace={Raycast=function(self,a,b,params) return nil end}
local Players={}
function Players:GetPlayers()return self.list or {} end
function Players:GetPlayerByUserId(id)
 for _,p in ipairs(self:GetPlayers()) do if p.UserId==id then return p end end
 return nil
end
local game={GetService=function(self,name)
 assert(name=="Players")
 return Players
end}
__POLICY__
local Policy=M
__COUNTER__
local function makePlayer(id,role,x)
 local hum={Health=200,MaxHealth=200}
 local root={Position=Vector3.new(x,2,0),IsA=function(self,kind)return kind=="BasePart" end}
 local c={First=hum,root=root}
 function c:FindFirstChildOfClass(kind)
  if kind=="Humanoid" then return hum end
  return nil
 end
 function c:FindFirstChild(n)
  if n=="HumanoidRootPart" then return root end
  return nil
 end
 local p={UserId=id,Parent=Players,Character=c,
  attrs={EGGRUMBLE_QueuedMode="TEAM",EGGRUMBLE_Role=role}}
 function p:GetAttribute(name)return self.attrs[name] end
 function p:SetAttribute(name,value)self.attrs[name]=value end
 return p
end
local neutralHum={Health=100,MaxHealth=100}
local neutralPos=Vector3.new(5,2,0)
local neutral={PrimaryPart={Position=neutralPos},attrs={
 EGGRUMBLE_Neutral=true,EGGRUMBLE_NeutralInstanceId="N001"}}
function neutral:IsA(kind)return kind=="Model" end
function neutral:GetAttribute(k)return self.attrs[k] end
function neutral:FindFirstChildOfClass(k)if k=="Humanoid" then return neutralHum end end
local folder={GetChildren=function()return {neutral} end}
local world={Parent={},FindFirstChild=function(self,name)
 if name=="NeutralHorde" then return folder end
end}
local count=0
local swarm={damageFromPlayer=function(self,p,at,radius,damage,shape)
 assert(shape=="CIRCLE" and radius<=14 and damage>0)
 count+=1
 neutralHum.Health=math.max(0,neutralHum.Health-damage)
 return 1
end}
local function run(role)
 neutralHum.Health=100
 count=0
 local p=makePlayer(4,role,0)
 local ally=makePlayer(5,"WARRIOR",5)
 Players.list={p,ally}
 local session={world=world,mode="TEAM",
  rules={phase="ACTIVE",castles={
   ["4"]={alive=true,team="RED",heldEggs=0},
   ["5"]={alive=true,team="RED",heldEggs=0}}},
  swarm=swarm}
 local s=Policy.newRound(session)
 local c={epoch=session,playerId=p.UserId,avatarEpoch="v1",role=role,
  phase="ACTIVE",mode="TEAM",now=100,
  serverCurrent=true,characterAlive=true,roleVerified=true,
  castleAlive=true,downed=false,eliminated=false,carryingEgg=false,
  shieldActive=false}
 assert(Policy.arm(s,c,"SKILL"),"RED_ROLE_CANNOT_ARM")
 c.now=101
 local hits=Policy.ROLES[role].hits
 for n=1,hits do
  c.now=101+n*.1
  local verdict=Policy.onIncomingDamage(s,c,{
   serverVerified=true,hostile=true,damage=20,kind="NEUTRAL",
   attackerId="SWARM_MELEE",attackId="hit"..n})
  assert(verdict.blocked,"RED_NO_BLOCK_"..role)
  local decision=Counter.react(session,p,role,Policy,s,c,"SWARM_MELEE")
  if n<hits then
   assert(decision==nil,"RED_COUNTER_TOO_EARLY_"..role)
  else
   assert(decision~=nil,"RED_COUNTER_NOT_TRIGGERED_"..role)
  end
 end
 if role=="BUILDER" then
  assert(count==0,"RED_SCIENTIST_MINTS_NEUTRAL_DAMAGE")
  assert(Counter.allyMultiplier(session,ally,c.now)==.5,"RED_ALLY_BARRIER_MISSING")
  assert(Counter.allyMultiplier(session,p,c.now)==1,"RED_SELF_SHIELD_DOUBLE")
  c.now+=4
  assert(Counter.allyMultiplier(session,ally,c.now)==1,"RED_PERMANENT_ALLY_BARRIER")
 else
  assert(count==1,"RED_NEUTRAL_SINGLETON_NOT_USED_ONCE")
  assert(neutralHum.Health<100,"RED_COUNTER_NO_REAL_NEUTRAL_HP_LOSS")
  assert(s.entries["4"].chainUsed,"RED_NO_CONFIRMED_NEUTRAL_CHAIN")
  assert(Counter.react(session,p,role,Policy,s,c,"SWARM_MELEE")==nil,
   "RED_INFINITE_NEUTRAL_COUNTER")
 end
end
for _,role in ipairs({"MAGE","TRAPPER","BUILDER","BEAST","ZOMBIE"}) do run(role) end
-- Exact-first-attacker roles MUST NOT automatically strike unrelated neutral.
local role="WARRIOR"
neutralHum.Health=100
count=0
local p=makePlayer(4,role,0)
Players.list={p}
local session={world=world,mode="TEAM",swarm=swarm,
 rules={phase="ACTIVE",castles={["4"]={alive=true,team="RED",heldEggs=0}}}}
local s=Policy.newRound(session)
local c={epoch=session,playerId=4,avatarEpoch="v1",role=role,phase="ACTIVE",mode="TEAM",now=100,
 serverCurrent=true,characterAlive=true,roleVerified=true,castleAlive=true,
 downed=false,eliminated=false,carryingEgg=false,shieldActive=false}
assert(Policy.arm(s,c,"SKILL"),"RED_WARRIOR_ARM")
c.now=101
assert(Policy.onIncomingDamage(s,c,{serverVerified=true,hostile=true,damage=12,
 kind="PLAYER",attackerId="enemyNotANeutral",attackId="warrior1"}).blocked)
assert(Counter.react(session,p,role,Policy,s,c,"enemyNotANeutral")==nil)
assert(count==0 and neutralHum.Health==100,"RED_PVP_COUNTER_KILLED_UNRELATED_NEUTRAL")
print("GQ822_REAL_COUNTER_NATIVE_MAGE_TRAPPER_BUILDER_BEAST_ZOMBIE_SINGLE_SWARM_PASS")
'''
def gen(policy_path,out):
 policy=Path(policy_path).read_text()
 counter=COUNTER.read_text()
 assert policy.rstrip().endswith("return M") and counter.rstrip().endswith("return Counter")
 p=policy.rstrip()[:-len("return M")]
 q=counter.rstrip()[:-len("return Counter")]
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 good=BODY.replace("__POLICY__",p).replace("__COUNTER__",q)
 (out/"good.luau").write_text(good)
 mutation=q.replace("if e then", "if e then") # never edit actual source by mistake
 mutant=good.replace("return .5\nend\nreturn Counter", "return 1\nend\nreturn Counter")
 # Body strips module return; mutate the actual final original Counter method.
 mutant=good.replace(" return .5\nend\nlocal function makePlayer",
                     " return 1\nend\nlocal function makePlayer")
 if mutant==good: raise ValueError("RED_COUNTER_MUTATION_FAILED")
 (out/"barrier_mutant.luau").write_text(mutant)
 print("GQ822_NATIVE_ACTUAL_COUNTER_MODULE_VM_BUILT")
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--policy",required=True,type=Path)
 a.add_argument("--out",required=True,type=Path)
 x=a.parse_args()
 gen(x.policy,x.out)
