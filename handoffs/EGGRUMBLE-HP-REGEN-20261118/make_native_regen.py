#!/usr/bin/env python3
"""Real Luau VM test: inline actual Regen module source with mock Roblox signals.
Good source must pass; regen-too-fast mutant must fail with expected marker.
"""
from pathlib import Path
import argparse

HERE=Path(__file__).resolve().parent
MODULE=HERE/"EGGRUMBLE_NaturalRegen.luau"
POLICY_SOURCE=HERE/"EGGRUMBLE_PassiveRegenPolicy.luau"
UPSTREAM_RATE="M.REGEN_FRACTION_PER_SECOND = 0.007"
HARNESS=r'''
local clock=100
local os={clock=function() return clock end}
local function makeSignal()
 local signal={listeners={}}
 function signal:Connect(fn)
  local holder={fn=fn,enabled=true}
  table.insert(self.listeners,holder)
  return {Disconnect=function() holder.enabled=false end}
 end
 function signal:Fire(...)
  for _,listener in ipairs(self.listeners) do
   if listener.enabled then listener.fn(...) end
  end
 end
 return signal
end
local players={}
local heartbeat=makeSignal()
local game={GetService=function(self,name)
 if name=="Players" then return players end
 if name=="RunService" then return {Heartbeat=heartbeat} end
 error("UNKNOWN_SERVICE")
end}
local Policy=(function()
__POLICY_SOURCE__
end)()
local script={Parent={WaitForChild=function(self,name)
 assert(name=="EGGRUMBLE_PassiveRegenPolicy","RED_UNKNOWN_POLICY")
 return name
end}}
local require=function(name)
 assert(name=="EGGRUMBLE_PassiveRegenPolicy","RED_BAD_REQUIRE")
 return Policy
end
__ACTUAL_SOURCE__
assert(Regen.maxHP("WARRIOR")==250,"RED_WARRIOR_HP")
assert(Regen.maxHP("MAGE")==195,"RED_MAGE_HP")
assert(Regen.maxHP("NINJA")==185,"RED_ASSASSIN_HP")
assert(Regen.maxHP("TRAPPER")==205,"RED_TRAPPER_HP")
assert(Regen.maxHP("BUILDER")==225,"RED_BUILDER_HP")
assert(Regen.maxHP("BEAST")==220,"RED_BEAST_HP")
assert(Regen.maxHP("ZOMBIE")==230,"RED_ZOMBIE_HP")
assert(Regen.maxHP("UNKNOWN")==nil,"RED_UNKNOWN_HP_FALLBACK")
assert(Policy.regenDelta(60,250,106.99,100,.25,true,true,false,false)==0,"RED_EARLY_REGEN")
assert(Policy.regenDelta(60,250,107,100,.25,true,true,false,false)>0,"RED_SEVEN_SECOND_REGEN")
assert(Policy.regenDelta(60,250,140,100,.25,true,true,true,false)==0,"RED_BURNING_REGEN")
assert(Policy.regenDelta(0,250,140,100,.25,true,true,false,false)==0,"RED_DEATH_REGEN")
assert(Policy.regenDelta(250,250,140,100,.25,true,true,false,false)==0,"RED_OVERHEAL")
assert(math.abs(Policy.regenDelta(60,250,108,100,.25,true,true,false,false)-.4375)<.0001,
 "RED_REGEN_AMOUNT")
local h={Health=100,MaxHealth=100,HealthChanged=makeSignal(),Died=makeSignal(),attrs={}}
function h:GetAttribute(n) return self.attrs[n] end
local ch={FindFirstChildOfClass=function(self,c) return h end}
h.Parent=ch
local p={Parent=players,Character=ch,UserId=42,
 CharacterRemoving=makeSignal(),
 attrs={EGGRUMBLE_QueuedMode="TEAM",EGGRUMBLE_Role="WARRIOR"}}
function p:GetAttribute(n) return self.attrs[n] end
local world={Parent={},Destroying=makeSignal()}
local session={mode="TEAM",world=world,rules={phase="ACTIVE",
 castles={["42"]={alive=true}}}}
Regen.attach(session,p,"WARRIOR")
assert(h.MaxHealth==250 and h.Health==250,"RED_HP_BASELINE_NOT_INSTALLED")
clock=101
h.Health=100
h.HealthChanged:Fire(100)
clock=107.9
heartbeat:Fire(.25)
assert(h.Health==100,"RED_REGEN_BEFORE_SEVEN_SECONDS")
clock=108
heartbeat:Fire(.25)
assert(math.abs(h.Health-100.4375)<.0001,"RED_SEVEN_SECOND_HEAL_TICK")
h.attrs.EGGRUMBLE_BurnUntil=130
clock=109
h.Health=80
h.HealthChanged:Fire(80)
clock=120
heartbeat:Fire(.25)
assert(h.Health==80,"RED_REGEN_DURING_BURN")
h.attrs.EGGRUMBLE_BurnUntil=0
clock=121
heartbeat:Fire(.25)
assert(h.Health>80,"RED_REGEN_AFTER_BURN_END")
session.rules.phase="RESULTS"
clock=130
local snapshot=h.Health
heartbeat:Fire(.25)
clock=140
heartbeat:Fire(.25)
assert(h.Health==snapshot,"RED_OLD_ROUND_REGEN")
-- Late old signals must not re-open a stopped character.
h.HealthChanged:Fire(20)
assert(h.Health==snapshot,"RED_STOPPED_LISTENER_REVIVED")
print("GQ8_REGEN_ACTUAL_VM_7ROLE_LIFECYCLE_HIT_BURN_ROUND_PASS")
'''

def generate(path:Path):
 src=MODULE.read_text(encoding="utf-8")
 pure=POLICY_SOURCE.read_text(encoding="utf-8")
 if not src.rstrip().endswith("return Regen") or pure.count(UPSTREAM_RATE)!=1:
  raise ValueError("RED_REGEN_SOURCE_SIGNATURE")
 head=src.rstrip()[:-len("return Regen")]
 path.mkdir(parents=True,exist_ok=True)
 def emit(upstream):
  return HARNESS.replace("__ACTUAL_SOURCE__",head).replace("__POLICY_SOURCE__",upstream)
 (path/"good.luau").write_text(emit(pure))
 (path/"mutant.luau").write_text(emit(pure.replace(UPSTREAM_RATE,"M.REGEN_FRACTION_PER_SECOND = 0.07")))
 print("GQ8_REGEN_REAL_SOURCE_NATIVE_HARNESS_GENERATED")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 generate(a.out)
