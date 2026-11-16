--!strict
-- Execute against the *actual* 27th runtime observer module with native Luau.
-- Source-level simulation only: no Roblox physics, Studio or Android claim.
local Observer=require("./Observer")

local players={}
local user={
 Parent=players,
 GetAttribute=function(self,name)
  if name=="EGGRUMBLE_Role" then return self.role end
 end,
 role="NINJA",
}
function players:GetPlayerByUserId(id:number)
 if id==101 then return user end
 return nil
end
local battlefield={Parent={}}
local world={
 Parent={},
 FindFirstChild=function(self,name)
  if name=="TacticalBattlefield" then return battlefield end
  if name=="TacticalRoute_1" or name=="TacticalRoute_2" or name=="TacticalRoute_3" then
   return battlefield
  end
  return nil
 end
}
local rules={
 CASTLE_HP=1000,
 auditEggConservation=function(state)
  return {valid=state.conservationOk==true}
 end,
}
local session={
 mode="TEAM",
 roster={{id="101",isAI=false},{id="AI_1",isAI=true}},
 rules={
  phase="ACTIVE",winner=nil,ids={"101","AI_1"},conservationOk=true,
  castles={
   ["101"]={id="101",hp=1000,alive=true,heldEggs=1},
   ["AI_1"]={id="AI_1",hp=750,alive=true,heldEggs=0},
  },
 },
 world=world,swarm={kills={["101"]=4}},
 bossStatus="READY",itemIntakeStatus="READY",fieldItemCount=9,
}

local function has(list:{string},needle:string):boolean
 for _,v in ipairs(list) do
  if v==needle then return true end
 end
 return false
end
local function inspect()
 return Observer.inspect(session,rules,players)
end
local first=inspect()
assert(#first.red==0 and #first.yellow==0,"healthy session must be clear")
for domain,checked in pairs(first.checked) do
 assert(checked==true, "unobserved domain: "..domain)
end
session.rules.conservationOk=false
assert(has(inspect().red,"EGG_CONSERVATION_OR_AUDIT_FAILED"))
session.rules.conservationOk=true
session.rules.castles["101"].hp=-1
assert(has(inspect().red,"CASTLE_HP_RANGE"))
session.rules.castles["101"].hp=1000
session.rules.castles["101"].heldEggs=4
assert(has(inspect().red,"EGG_CARRY_RANGE"))
session.rules.castles["101"].heldEggs=1
session.rules.winner="RED"
assert(has(inspect().red,"ACTIVE_MATCH_HAS_WINNER"))
session.rules.winner=nil
session.swarm.kills["101"]=-3
assert(has(inspect().red,"INVALID_SERVER_KO_COUNTER"))
session.swarm.kills["101"]=4
session.itemIntakeStatus="READY";session.fieldItemCount=0
assert(has(inspect().red,"ITEM_READY_WITHOUT_SPAWNS"))
session.fieldItemCount=9
session.itemIntakeStatus="YELLOW_ITEM_OPTIONAL"
local optional=inspect()
assert(#optional.red==0 and has(optional.yellow,"OPTIONAL_ITEM_INTAKE_FAILED"))
session.itemIntakeStatus="READY"
user.role="INVALID_ROLE"
assert(has(inspect().yellow,"HUMAN_ROLE_NOT_ACKNOWLEDGED"))
user.role="NINJA"
session.bossStatus="YELLOW_BOSS_OPTIONAL"
assert(has(inspect().yellow,"OPTIONAL_BOSS_FAILED"))
session.bossStatus="READY"
session.world={Parent=nil,FindFirstChild=world.FindFirstChild}
assert(has(inspect().red,"FIELD_WORLD_MISSING"))
session.world=world
session.rules.castles["AI_1"]=nil
assert(has(inspect().red,"ROSTER_CASTLE_MISSING"))
session.rules.castles["AI_1"]={id="AI_1",hp=750,alive=true,heldEggs=0}
assert(#inspect().red==0 and #inspect().yellow==0)
-- A clean starting state must not flood logs; new failure once, then recovery.
local clean={red={},yellow={}}
local key,emit,recovered=Observer.warningDelta(nil,clean)
assert(key=="" and not emit and not recovered)
local errorReport={red={"CASTLE_HP_RANGE","EGG_CARRY_RANGE"},yellow={"OPTIONAL_BOSS_FAILED"}}
local broken,firstAlert,alreadyRecovered=Observer.warningDelta(key,errorReport)
assert(firstAlert and not alreadyRecovered)
local again,repeatAlert=Observer.warningDelta(broken,errorReport)
assert(again==broken and not repeatAlert, "unchanged error must not emit every 5 sec")
local reordered={red={"EGG_CARRY_RANGE","CASTLE_HP_RANGE","CASTLE_HP_RANGE"},yellow={"OPTIONAL_BOSS_FAILED"}}
assert(Observer.warningSignature(reordered)==broken, "warnings must be stable when table iteration order changes")
local changed,changedAlert=Observer.warningDelta(broken,{red={"CASTLE_HP_RANGE"},yellow={}})
assert(changedAlert and changed~=broken, "new diagnostics should emit on transition")
local recoveredKey,recoveredEmit,isRecovered=Observer.warningDelta(changed,clean)
assert(recoveredKey=="" and recoveredEmit and isRecovered,"one recovery notice required")
local stable,stableEmit=Observer.warningDelta(recoveredKey,clean)
assert(stable=="" and not stableEmit,"recovery must not print repeatedly")
print("GQ_OBSERVER_WARNING_DEDUP_NATIVE_PASS")
print("GQ_7DOMAIN_OBSERVER_REAL_LUAU_NATIVE_BEHAVIOR_12_CASES_PASS_SOURCE_ONLY")
