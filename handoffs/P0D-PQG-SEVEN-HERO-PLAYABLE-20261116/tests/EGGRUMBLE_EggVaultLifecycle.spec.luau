--!strict
-- SOURCE-WIP pure Luau behavioral regression for EGGRUMBLE V3.
-- Invoke after loading the actual EGGRUMBLE_CastleMatchRules ModuleScript:
-- local run = require(path.to.EGGRUMBLE_EggVaultLifecycle)
-- run(require(path.to.EGGRUMBLE_CastleMatchRules))
-- This test is NOT Roblox Studio/Android evidence unless executed and recorded there.

return function(Rules:any)
 local function equal(a:any,b:any,label:string)
  assert(a==b, label..": expected "..tostring(b)..", got "..tostring(a))
 end
 local function stock(m:any):number
  local count=m.fieldEggs
  for _,c in pairs(m.castles) do
   count+=c.vaultEggs+c.heldEggs
  end
  return count
 end
 local function rosterTeam()
  return {{id="red",team="RED",isAI=false},{id="blue",team="BLUE",isAI=true}}
 end
 -- An egg brought home stays in the victor's castle vault, still stealable;
 -- it must be released when that castle falls rather than disappear on deposit.
 local m=Rules.new(Rules.MODE_TEAM,rosterTeam(),24)
 equal(stock(m),30,"initial total egg stock")
 Rules.start(m)
 Rules.takeEggs(m,"red",1,"blue")
 equal(m.castles.blue.vaultEggs,2,"theft debits enemy vault")
 equal(m.castles.red.heldEggs,1,"egg carried in hand")
 equal(stock(m),30,"stock after theft")
 Rules.depositEggs(m,"red",1)
 equal(m.castles.red.heldEggs,0,"hand empty after deposit")
 equal(m.castles.red.vaultEggs,4,"deposited egg stored in own vault")
 equal(m.castles.red.depositedEggs,1,"cumulative player egg delivery")
 equal(m.teamDeposits.RED,1,"team delivery statistics")
 equal(stock(m),30,"stock after deposit")
 local fall
 for _=1,4 do
  fall=Rules.damageCastle(m,"red","blue",250)
 end
 assert(fall.fallen,"red castle must collapse")
 equal(fall.releasedEggs,4,"deposited egg included in fallen castle release")
 equal(m.fieldEggs,28,"all four eggs released into field")
 equal(m.winner,"BLUE","TEAM winner requires final opposing castle collapse")
 equal(stock(m),30,"stock conserved across castle collapse")
 local afterWin=pcall(function() Rules.takeEggs(m,"blue",1) end)
 assert(not afterWin,"no pickups permitted after winner is decided")

 -- Vault deposits are reversible: enemy may steal back a stored egg.
 local m2=Rules.new(Rules.MODE_TEAM,rosterTeam(),24)
 Rules.start(m2)
 Rules.takeEggs(m2,"red",1,"blue")
 Rules.depositEggs(m2,"red",1)
 Rules.takeEggs(m2,"blue",1,"red")
 equal(m2.castles.red.vaultEggs,3,"previously deposited egg can be stolen back")
 Rules.depositEggs(m2,"blue",1)
 equal(m2.castles.blue.vaultEggs,3,"recaptured egg is stored at home")
 equal(stock(m2),30,"stock after reciprocal steal-and-deposit")
 assert(not pcall(function() Rules.takeEggs(m2,"red",1,"red") end),
  "owner must not steal from their own castle")

 -- Death drops a carried egg exactly once. The preview connects this operation
 -- to a visible physical pickup; this pure rule test proves count conservation.
 local dead=Rules.new(Rules.MODE_TEAM,rosterTeam(),24)
 Rules.start(dead)
 Rules.takeEggs(dead,"red",1,"blue")
 equal(Rules.onCarrierEliminated(dead,"red"),1,"first death drops one egg")
 equal(dead.castles.red.heldEggs,0,"dead carrier has no hidden carried stock")
 equal(Rules.onCarrierEliminated(dead,"red"),0,"duplicate death cannot duplicate an egg")
 equal(dead.fieldEggs,25,"death moves the carried egg to field stock")
 equal(stock(dead),30,"death drop conserves total egg stock")

 -- Royale must not finish when the first of three personal castles falls.
 local br=Rules.new(Rules.MODE_ROYALE,{{id="A"},{id="B"},{id="C"}},24)
 Rules.start(br)
 for _=1,4 do Rules.damageCastle(br,"A","B",250) end
 equal(br.phase,"ACTIVE","BR continues after first personal elimination")
 equal(br.winner,nil,"BR cannot crown a winner with two castles alive")
 for _=1,4 do Rules.damageCastle(br,"C","B",250) end
 equal(br.winner,"B","BR winner is the last standing individual castle")
 equal(stock(br),33,"BR egg stock preserved after two castles fall")
 return true
end
