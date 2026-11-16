--!strict
-- Native Luau regression; appended to the EXACT modified #482 original Rules file.
-- No duplicate Game, no fake Roblox engine / product-success claims.
local Rules=M
local passed=0
local function check(ok:boolean,msg:string)
 assert(ok,msg)
 passed+=1
end
local function ending(actor:string,mode:string)
 local roster
 if mode=="TEAM" then
  roster=Rules.makeRoster("TEAM",{actor,"BLUE"},2)
 else
  roster={{id=actor,isAI=false},{id="BLUE",isAI=true},{id="GREEN",isAI=true}}
 end
 local battle=Rules.new(mode,roster,24)
 Rules.start(battle)
 check(Rules.takeEggs(battle,actor,1,"BLUE")==1,mode.." winner carries enemy egg")
 check(battle.castles[actor].heldEggs==1,mode.." carried stock is live")
 for _,target in ipairs(if mode=="TEAM" then {"BLUE"} else {"BLUE","GREEN"}) do
  local n=0
  while battle.castles[target].alive and n<8 do
   Rules.damageCastle(battle,target,actor,250)
   n+=1
  end
  check(not battle.castles[target].alive,mode.." enemy castle genuinely fell")
 end
 check(battle.phase=="FINISHED" and battle.winner==(if mode=="TEAM" then "RED" else actor),
  mode.." settled server-side")
 check(Rules.auditEggConservation(battle).valid,mode.." before late death conservation")
 local beforeHeld=battle.castles[actor].heldEggs
 local beforeField=battle.fieldEggs
 local beforeSerial=battle.eggSerial
 local beforeEvents=#battle.events
 local beforeTokens=0
 for _ in pairs(battle.fieldEggTokens) do beforeTokens+=1 end
 for _=1,2 do
  local dropped,ids=Rules.onCarrierEliminated(battle,actor)
  check(dropped==0 and #ids==0,mode.." late death produces zero eggs/tokens")
 end
 local afterTokens=0
 for _ in pairs(battle.fieldEggTokens) do afterTokens+=1 end
 check(battle.castles[actor].heldEggs==beforeHeld,mode.." carried stock frozen")
 check(battle.fieldEggs==beforeField,mode.." field stock frozen")
 check(battle.eggSerial==beforeSerial and afterTokens==beforeTokens,mode.." token ledger frozen")
 check(#battle.events==beforeEvents,mode.." result event ledger frozen")
 check(Rules.auditEggConservation(battle).valid,mode.." after late death conservation")
end
ending("HERO","TEAM")
ending("HERO","BATTLE_ROYALE")
local active=Rules.new("TEAM",Rules.makeRoster("TEAM",{"A","B"},2),24)
Rules.start(active)
Rules.takeEggs(active,"A",1,"B")
local dropped,ids=Rules.onCarrierEliminated(active,"A")
check(dropped==1 and #ids==1,"ACTIVE legitimate carrier death still releases one token")
local replay,none=Rules.onCarrierEliminated(active,"A")
check(replay==0 and #none==0,"ACTIVE double death remains idempotent")
check(Rules.auditEggConservation(active).valid,"ACTIVE conservation")
local waiting=Rules.new("TEAM",Rules.makeRoster("TEAM",{"A","B"},2),24)
local waitingSerial=waiting.eggSerial
local d,empty=Rules.onCarrierEliminated(waiting,"A")
check(d==0 and #empty==0 and waiting.eggSerial==waitingSerial,"LOBBY death creates nothing")
print("POSTWIN_EGG_DEATH_NATIVE_PASS",passed)
