--!strict
-- SOURCE-EXACT postwin Rules regression on a FULL 1 human + 15 AI roster.
-- Native Luau only, no Roblox Studio, no fake NPC/visual performance claims.
-- Tests state conservation during real randomized rule operations and a
-- no-post-win-mutation check on 16 personal castles / 8v8 team castles.
local Rules=M
local checks=0
local actions=0
local function pass(ok:boolean,msg:string)
 assert(ok,"GQ509_16SLOT_"..msg)
 checks+=1
end
local function xorsafeRng(start:number)
 local state=start
 return function(n:number):number
  -- All 1664525 * 2^32 values are under 2^53 (exact integer in double).
  state=(state*1664525+1013904223)%4294967296
  return (state%n)+1
 end
end
local function proveAudit(battle:any,mode:string,run:number,step:number)
 local a=Rules.auditEggConservation(battle)
 pass(a.valid,mode.."_"..run.."_"..step.."_CONSERVATION")
 pass(a.tokens==a.fieldEggs,mode.."_"..run.."_"..step.."_PHYSICAL_TOKENS")
 pass(a.tokens+a.inCastles+a.carried==a.total,mode.."_"..run.."_"..step.."_TOTAL")
 pass(battle.teamSiegeTokens.RED<=2 and battle.teamSiegeTokens.BLUE<=2,
  mode.."_"..run.."_"..step.."_SIEGE_CAP")
end
local function liveFieldToken(battle:any)
 -- Choose an available token by reproducible lowest alphabetic key, rather
 -- than Lua table iteration order (not stable across native/build versions).
 local found=nil
 for key,available in pairs(battle.fieldEggTokens) do
  if available and (found==nil or key<found) then found=key end
 end
 return found
end
local function stateFingerprint(battle:any)
 local c={}
 local keys={}
 for id,_ in pairs(battle.castles) do table.insert(keys,id) end
 table.sort(keys)
 for _,id in ipairs(keys) do
  local v=battle.castles[id]
  table.insert(c,id..":"..v.vaultEggs..":"..v.heldEggs..":"..v.hp..":"..tostring(v.alive))
 end
 local field={}
 for key,v in pairs(battle.fieldEggTokens) do
  if v then table.insert(field,key) end
 end
 table.sort(field)
 return table.concat({
  tostring(battle.phase),tostring(battle.winner),battle.fieldEggs,
  battle.eggSerial,#battle.events,battle.teamDeposits.RED,battle.teamDeposits.BLUE,
  battle.teamSiegeTokens.RED,battle.teamSiegeTokens.BLUE,
  table.concat(c,"|"),table.concat(field,"|")
 },";")
end
local function simulate(mode:string,run:number)
 local rng=xorsafeRng((mode=="TEAM" and 21423 or 54781)+run*101)
 local roster=Rules.makeRoster(mode,{"HUMAN_1"},16)
 local red=0
 local blue=0
 for _,entry in ipairs(roster) do
  if mode=="TEAM" then
   if entry.team=="RED" then red+=1 else blue+=1 end
  end
 end
 if mode=="TEAM" then pass(red==8 and blue==8,"TEAM_8v8") end
 pass(#roster==16,"REAL_ROSTER_16")
 local battle=Rules.new(mode,roster,24)
 local hero=battle.castles.HUMAN_1
 Rules.start(battle)
 local targetIds={}
 for _,entry in ipairs(roster) do
  if entry.id~="HUMAN_1" and
   (mode=="BATTLE_ROYALE" or entry.team~=hero.team) then
   table.insert(targetIds,entry.id)
  end
 end
 pass(#targetIds==(mode=="TEAM" and 8 or 15),"ENEMY_COUNT")
 proveAudit(battle,mode,run,0)
 for step=1,96 do
  local available={}
  for _,id in ipairs(targetIds) do
   local castle=battle.castles[id]
   if castle.alive then table.insert(available,id) end
  end
  local target=if #available>0 then available[rng(#available)] else nil
  local action=rng(6)
  if action==1 and hero.heldEggs<3 then
   local token=liveFieldToken(battle)
   if token~=nil then
    local oldEggs=hero.heldEggs
    pass(Rules.takeFieldEgg(battle,"HUMAN_1",token)==oldEggs+1,
     mode.."_FIELD_INCREMENT")
    pass(not pcall(function() Rules.takeFieldEgg(battle,"HUMAN_1",token) end),
     mode.."_DOUBLE_SPEND_DENIED")
    actions+=1
   end
  elseif action==2 and target~=nil and hero.heldEggs<3
   and battle.castles[target].vaultEggs>0 then
   local oldEggs=hero.heldEggs
   pass(Rules.takeEggs(battle,"HUMAN_1",1,target)==oldEggs+1,
    mode.."_REAL_ENEMY_STEAL")
   actions+=1
  elseif action==3 and hero.heldEggs>0 then
   local before=hero.heldEggs
   local beforeVault=hero.vaultEggs
   Rules.depositEggs(battle,"HUMAN_1",1)
   pass(hero.heldEggs==before-1 and hero.vaultEggs==beforeVault+1,
    mode.."_VAULT_DEPOSIT")
   actions+=1
  elseif action==4 and hero.heldEggs>0 then
   local before=hero.heldEggs
   local dropped,ids=Rules.onCarrierEliminated(battle,"HUMAN_1")
   pass(dropped==before and #ids==before,mode.."_ACTIVE_DEATH_PHYSICAL")
   local second,again=Rules.onCarrierEliminated(battle,"HUMAN_1")
   pass(second==0 and #again==0,mode.."_IDEMPOTENT_DEATH")
   actions+=1
  elseif action==5 and target~=nil then
   -- Damage <=100 still uses real siege token, shields and castle HP.
   local old=hero.hp
   Rules.damageCastle(battle,target,"HUMAN_1",rng(100))
   pass(old==hero.hp,mode.."_NO_SELF_DAMAGE")
   actions+=1
  elseif action==6 then
   -- Hostile attempts never bypass same-team / self castle ownership.
   pass(not pcall(function()
    Rules.takeEggs(battle,"HUMAN_1",1,"HUMAN_1")
   end),mode.."_SELF_STEAL_DENIED")
  end
  proveAudit(battle,mode,run,step)
  pass(battle.phase=="ACTIVE",mode.."_PRE_FINAL_STILL_ACTIVE")
 end
 -- Guarantee winner carries live physical cargo. The post-final death hook
 -- must preserve this cargo and every live token/event/score bit.
 if hero.heldEggs==0 then
  local token=liveFieldToken(battle)
  if token~=nil then
   Rules.takeFieldEgg(battle,"HUMAN_1",token)
  else
   for _,id in ipairs(targetIds) do
    if battle.castles[id].alive and battle.castles[id].vaultEggs>0 then
     Rules.takeEggs(battle,"HUMAN_1",1,id)
     break
    end
   end
  end
 end
 pass(hero.heldEggs>0,mode.."_CARRY_BEFORE_FINAL")
 for i,id in ipairs(targetIds) do
  while battle.castles[id].alive do
   Rules.damageCastle(battle,id,"HUMAN_1",250)
   actions+=1
   proveAudit(battle,mode,run,100+i)
  end
  if i<#targetIds then
   pass(battle.phase=="ACTIVE",mode.."_MUST_WAIT_LAST_CASTLE")
  end
 end
 pass(battle.phase=="FINISHED",mode.."_FINISHED")
 pass(battle.winner==(mode=="TEAM" and "RED" or "HUMAN_1"),
  mode.."_EXPECTED_WINNER")
 local before=stateFingerprint(battle)
 for _=1,3 do
  for _,entry in ipairs(roster) do
   local dropped,ids=Rules.onCarrierEliminated(battle,entry.id)
   pass(dropped==0 and #ids==0,mode.."_LATE_DEATH_ZERO")
  end
 end
 pass(stateFingerprint(battle)==before,mode.."_TERMINAL_FULL_LEDGER_FROZEN")
 local token=liveFieldToken(battle)
 pass(token~=nil,mode.."_POSTWIN_EXISTING_FIELD_TOKEN")
 pass(not pcall(function() Rules.takeFieldEgg(battle,"HUMAN_1",token) end),
  mode.."_POSTWIN_PICKUP_DENIED")
 pass(not pcall(function() Rules.depositEggs(battle,"HUMAN_1",1) end),
  mode.."_POSTWIN_DEPOSIT_DENIED")
 pass(not pcall(function() Rules.damageCastle(battle,targetIds[1],"HUMAN_1",1) end),
  mode.."_POSTWIN_SIEGE_DENIED")
 pass(stateFingerprint(battle)==before,mode.."_POSTWIN_OPERATIONS_NO_MUTATION")
 proveAudit(battle,mode,run,200)
end
for _,mode in ipairs({"TEAM","BATTLE_ROYALE"}) do
 for case=1,6 do simulate(mode,case) end
end
pass(actions>300,"MANY_REAL_STATE_TRANSITIONS")
print("GQ509_16SLOT_FUZZ_CONSERVATION_PASS checks="..checks.." actions="..actions.." modes=2 seeds=12")
