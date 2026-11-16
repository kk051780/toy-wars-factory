-- Actual authored KoFence module is prepended verbatim by build_native_harness.py.
local F = Fence
local checks = 0
local function eq(name, got, want)
  checks += 1
  assert(got == want, name .. " expected " .. tostring(want) .. " got " .. tostring(got))
end
local world = {Parent = {}}
local horde = {Parent = world}
local model = {owner = horde, neutral = true}
function model:IsDescendantOf(other)
  return self.owner == other
end
function model:GetAttribute(name)
  if name == "EGGRUMBLE_Neutral" then return self.neutral end
end
local session = {
  rules = {phase="ACTIVE",winner=nil,castles={["100"]={alive=true}, ["AI_1"]={alive=true}}},
  world=world, swarm={}
}
local function check(name,expected,id)
  eq(name,F.mayCredit(session,id or "100",model,horde),expected)
end
check("one server-confirmed current-horde human death",true)
check("one server-confirmed current-horde bot death",true,"AI_1")
session.rules.phase="FINISHED";check("finished round",false)
session.rules.phase="ABANDONED";check("abandoned round",false)
session.rules.phase="DRAW";check("draw round",false)
session.rules.phase="ACTIVE"
session.rules.winner="BLUE";check("winner already chosen",false)
session.rules.winner=nil
session.rules.castles["100"].alive=false;check("castle eliminated",false)
session.rules.castles["100"].alive=true
model.owner = {};check("foreign horde",false)
model.owner = horde
model.neutral=false;check("not actual neutral",false)
model.neutral=true
horde.Parent={};check("different Arena parent",false)
horde.Parent=world
world.Parent=nil;check("world destroyed",false)
world.Parent={}
session.swarm=nil;check("swarm was retired",false)
session.swarm={}
eq("unregistered actor",F.mayCredit(session,"999",model,horde),false)
eq("nil attacker",F.mayCredit(session,nil,model,horde),false)
eq("number attacker",F.mayCredit(session,100,model,horde),false)
eq("empty attacker",F.mayCredit(session,"",model,horde),false)
eq("missing session",F.mayCredit(nil,"100",model,horde),false)
eq("missing model",F.mayCredit(session,"100",nil,horde),false)
eq("missing horde",F.mayCredit(session,"100",model,nil),false)
eq("expired owner must not be credited",F.decide("ACTIVE",nil,false,true,true),false)
eq("old round after winner",F.decide("ACTIVE","RED",true,true,true),false)
eq("good current round",F.decide("ACTIVE",nil,true,true,true),true)
print("EGGRUMBLE_KO_DEATH_FENCE_NATIVE_PASS checks="..tostring(checks))
