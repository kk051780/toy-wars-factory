--!strict
-- OWNER QA runnable in a separate private Studio place: requires sibling
-- EGGRUMBLE_CastleMatchRules ModuleScript. No production Game/Store/Remote changes.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))
local pass=0
local function expect(condition:boolean,msg:string)
 assert(condition,msg)
 pass+=1
end

local roster=Rules.makeRoster("TEAM",{"101"},16)
expect(#roster==16,"AI must fill remaining slots")
local red=0;local blue=0;local ai=0
for _,entry in ipairs(roster) do
 if entry.team=="RED" then red+=1 else blue+=1 end
 if entry.isAI then ai+=1 end
end
expect(red==8 and blue==8,"teams must have eight castles each")
expect(ai==15,"one human means 15 AI slots")
local match=Rules.new("TEAM",roster,24)
local redPlayer=roster[1].id
local blueBot=roster[2].id
expect(match.castles[redPlayer].hp==1000,"equal default core HP")
expect(match.castles[blueBot].vaultEggs==3,"multiple eggs in every castle")
expect(not pcall(function()
 Rules.loadDefense(match,redPlayer,{"HARDENED","REPAIR"})
end),"repair and armor stacking must be rejected")
expect(not pcall(function()
 Rules.decorate(match,redPlayer,blueBot,"GOLD")
end),"cannot decorate somebody else's castle")
expect(Rules.loadDefense(match,redPlayer,{"HARDENED","TRAP","SENSOR"})==10,
 "full equal-defense budget remains ten points")
Rules.start(match)
expect(not pcall(function()
 Rules.damageCastle(match,blueBot,roster[4].id,100)
end),"friendly-fire attack must fail")
expect(Rules.takeEggs(match,redPlayer,2,blueBot)==2,"red hero steals two blue eggs")
expect(match.castles[blueBot].vaultEggs==1,"vault decremented")
Rules.depositEggs(match,redPlayer,2)
expect(match.teamDeposits.RED==2,"team bank credits returned eggs")
expect(match.teamSiegeTokens.RED>0,"egg raid provides capped siege pressure")
expect(Rules.auditEggConservation(match).valid,"egg stock is conserved after castle raids")
expect(Rules.takeFieldEgg(match,redPlayer,"FIELD_1")==1,"one physical field egg collected")
expect(not pcall(function() Rules.takeFieldEgg(match,redPlayer,"FIELD_1") end),
 "same physical field egg cannot be collected twice")
local dropped,dropIds=Rules.onCarrierEliminated(match,redPlayer)
expect(dropped==1 and #dropIds==1,"carrier death creates exactly one unique loot ID")
expect(not pcall(function() Rules.takeFieldEgg(match,redPlayer,"FIELD_1") end),
 "old consumed egg token remains spent")
expect(Rules.takeFieldEgg(match,redPlayer,dropIds[1])==1,"carrier-drop egg can be collected")
Rules.depositEggs(match,redPlayer,1)
expect(Rules.auditEggConservation(match).valid,"egg stock conserved after dropping, retrieving, depositing")
local blueOwned=0
for _,c in pairs(match.castles) do
 if c.team=="BLUE" then blueOwned+=1 end
end
expect(blueOwned==8,"blue team contains eight castles")
local eliminated=0
for _,entry in ipairs(roster) do
 if entry.team=="BLUE" then
  local result=nil
  repeat
   result=Rules.damageCastle(match,entry.id,redPlayer,250)
  until result.fallen
  eliminated+=1
  if eliminated<8 then
   expect(match.phase=="ACTIVE","team survives until all eight castles fall")
  end
 end
end
expect(match.phase=="FINISHED" and match.winner=="RED","all enemy castles destroyed -> RED wins")
expect(match.fieldEggs>24,"fallen castles release their remaining eggs")
expect(Rules.auditEggConservation(match).valid,"castle falls do not create or lose eggs")
expect(not pcall(function() Rules.takeEggs(match,redPlayer,1) end),
 "no actions after team match ends")

local bRoster={{id="A",team=nil,isAI=false},{id="B",team=nil,isAI=true},{id="C",team=nil,isAI=true}}
local br=Rules.new("BATTLE_ROYALE",bRoster,10)
Rules.start(br)
repeat
 local res=Rules.damageCastle(br,"B","A",250)
 if res.fallen then break end
until false
expect(br.phase=="ACTIVE","BR continues with two castles")
repeat
 local res=Rules.damageCastle(br,"C","A",250)
 if res.fallen then break end
until false
expect(br.phase=="FINISHED" and br.winner=="A","last personal castle wins BR")
expect(Rules.auditEggConservation(br).valid,"BR castle falls conserve all eggs")
print("[EGGRUMBLE V3 SOURCE SMOKE] PASS",pass,"assertions; Studio-only rules test")
