--!strict
-- Appended behind the pure EGGRUMBLE_CastleMatchRules.luau source
-- by tools/make_native_rules_harness.py; actual Luau VM, no Roblox engine.
-- The injected module exposes its local M as Rules in the same chunk.
local passed=0
local function pass(ok:boolean,msg:string)
 assert(ok,msg)
 passed+=1
end
local roster=Rules.makeRoster("TEAM",{"101"},16)
pass(#roster==16,"human plus 15 AI fill 16 slots")
local red=0
local blue=0
for _,p in ipairs(roster) do
 if p.team=="RED" then red+=1 else blue+=1 end
end
pass(red==8 and blue==8,"TEAM is balanced 8v8")
local battle=Rules.new("TEAM",roster,24)
local actor="101"
local enemy=roster[2].id
pass(battle.castles[actor].hp==1000,"base castle HP equal")
pass(battle.castles[enemy].vaultEggs==3,"per-castle multiple eggs")
pass(not pcall(function() Rules.decorate(battle,actor,enemy,"GOLD") end),"cannot decorate enemy castle")
pass(not pcall(function() Rules.loadDefense(battle,actor,{"HARDENED","REPAIR"}) end),"no stacking of shield and repair")
pass(Rules.loadDefense(battle,actor,{"HARDENED","TRAP","SENSOR"})==10,"free full-budget loadout")
pass(battle.castles[actor].shield==50,"max shield 5 percent")
Rules.start(battle)
pass(not pcall(function() Rules.loadDefense(battle,actor,{"REPAIR"}) end),"no mid-game defense switch")
pass(not pcall(function() Rules.damageCastle(battle,enemy,roster[4].id,99) end),"TEAM friendly fire forbidden")
pass(not pcall(function() Rules.damageCastle(battle,actor,actor,99) end),"self destruction forbidden")
pass(Rules.takeEggs(battle,actor,2,enemy)==2,"steal from enemy castle")
pass(battle.castles[enemy].vaultEggs==1,"enemy vault lost exactly two")
pass(Rules.depositEggs(battle,actor,2)==2,"return eggs to own castle")
pass(battle.castles[actor].vaultEggs==5,"returned eggs survive in vault")
pass(battle.teamSiegeTokens.RED==2,"eggs grant bounded siege supply")
pass(Rules.auditEggConservation(battle).valid,"conservation after raid and deposit")
pass(Rules.takeFieldEgg(battle,actor,"FIELD_1")==1,"physical field token redeemed once")
pass(not pcall(function() Rules.takeFieldEgg(battle,actor,"FIELD_1") end),"replayed field egg forbidden")
pass(not pcall(function() Rules.takeFieldEgg(battle,actor,"NONEXISTENT") end),"forged egg forbidden")
local dropped,ids=Rules.onCarrierEliminated(battle,actor)
pass(dropped==1 and #ids==1,"carrier drops unique physical token")
pass(Rules.auditEggConservation(battle).valid,"conservation after carrier death")
local doubleDrop,idsAgain=Rules.onCarrierEliminated(battle,actor)
pass(doubleDrop==0 and #idsAgain==0,"death hook idempotent")
pass(Rules.takeFieldEgg(battle,actor,ids[1])==1,"dropped token can be recollected")
pass(not pcall(function() Rules.takeFieldEgg(battle,actor,ids[1]) end),"dropped token cannot be duplicated")
Rules.depositEggs(battle,actor,1)
pass(Rules.auditEggConservation(battle).valid,"conservation after drop recovery")
local count=0
for _,r in ipairs(roster) do
 if r.team=="BLUE" then
  local fell=false
  for i=1,6 do
   local result=Rules.damageCastle(battle,r.id,actor,250)
   if result.fallen then
    fell=true
    pass(#result.releasedEggIds==result.releasedEggs,"every released egg has unique pickup token")
    break
   end
  end
  pass(fell,"enemy castle can fall")
  count+=1
  if count<8 then pass(battle.phase=="ACTIVE","game continues until all enemy castles fall") end
 end
end
pass(battle.phase=="FINISHED" and battle.winner=="RED","last TEAM standing wins")
pass(Rules.auditEggConservation(battle).valid,"all castle falls preserve stock")
pass(not pcall(function() Rules.takeFieldEgg(battle,actor,"FIELD_2") end),"match ended prohibits collection")
local battleRoyal=Rules.new("BATTLE_ROYALE",{
 {id="A",isAI=false},{id="B",isAI=true},{id="C",isAI=true},
},10)
Rules.start(battleRoyal)
for _,target in ipairs({"B","C"}) do
 local fell=false
 for _=1,6 do
  local r=Rules.damageCastle(battleRoyal,target,"A",250)
  if r.fallen then fell=true;break end
 end
 pass(fell,target.." eliminated in BR")
 if target=="B" then pass(battleRoyal.phase=="ACTIVE","BR needs final last castle") end
end
pass(battleRoyal.winner=="A" and battleRoyal.phase=="FINISHED","BR last castle wins")
pass(Rules.auditEggConservation(battleRoyal).valid,"BR total egg conservation")
print("[EGGRUMBLE NATIVE LUAU] PASS",passed,"functional engine-independent assertions")
