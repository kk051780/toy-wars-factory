-- Independent accepted cases preserved verbatim inside distinct scenario scopes.
-- Assembly provides local ROLE_CASE='lifecycle' or 'archetypes'.
assert(ROLE_CASE=='lifecycle' or ROLE_CASE=='archetypes','EXPECTED_ROLE_CASE_SELECTOR')
if ROLE_CASE=='lifecycle' then
do
local roleFailures = {}
local function check(value, message) assert(value, message) end
local function equal(value, wanted, message)
 check(type(value)=='number' and math.abs(value-wanted)<1e-6,
  message..' actual='..tostring(value)..' expected='..tostring(wanted))
end
local function pass(name, detail) print('CASE\t'..name..'\tPASS\t'..detail) end
local expectedActors={
 WARRIOR={actorType='Guardian_SHIELD_KNIGHT',hp=110,gear='Signature_SHIELD'},
 MAGE={actorType='Guardian_ICE_MAGE',hp=70,gear='Signature_STAFF'},
 NINJA={actorType='Guardian_SHADOW_SCOUT',hp=68,gear='Signature_TWIN_BLADES'},
 TRAPPER={actorType='Guardian_PSY_PUPPET',hp=86,gear='Signature_PSI_ORB'},
 BUILDER={actorType='Guardian_CLOCK_GOLEM',hp=125,gear='Signature_HAMMER'},
 BEAST={actorType='Guardian_GUARD_WOLF',hp=84,gear='Signature_CLAWS'},
 ZOMBIE={actorType='Guardian_CURSE_SOLDIER',hp=76,gear='Signature_CURSE_BANNER'},
}
local function roleResult(name, row, wanted, detail)
 local expected=expectedActors[wanted]
 local ok = row.role==wanted and row.actorType==expected.actorType and row.isModel
  and row.maxHealth==expected.hp and row.initialHealth==expected.hp and row.gear==expected.gear
 print('CASE\t'..name..'\t'..(if ok then 'PASS' else 'FAIL')..'\tactual='..tostring(row.role)..' expected='..wanted
  ..' actor='..tostring(row.actorType)..' expected_actor='..expected.actorType
  ..' maxHP='..tostring(row.maxHealth)..' expected_maxHP='..expected.hp
  ..' initialHP='..tostring(row.initialHealth)..' gear='..tostring(row.gear)..'; '..detail)
 if not ok then table.insert(roleFailures, name) end
end
local scenes=workspace:FindFirstChild('EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW')
local function trigger(actor,part,verb)
 check(part~=nil,'actual prompt part '..verb)
 local selected=nil
 for _,child in ipairs(part:GetChildren()) do
  if child:IsA('ProximityPrompt') and child.ActionText==verb then selected=child end
 end
 check(selected and selected.Enabled,'actual enabled prompt '..verb)
 actor.Character:FindFirstChild('HumanoidRootPart').CFrame=CFrame.new(part.Position+Vector3.new(0,0,1))
 ProximityPromptService.PromptTriggered:Fire(selected,actor)
 selected.Triggered:Fire(actor)
end
local function away(actor, session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 actor.Character:FindFirstChild('HumanoidRootPart').CFrame=CFrame.new(floor.Position+Vector3.new(floor.Size.X+2500,20,floor.Size.Z+2500))
end
local function births(session,owner)
 local result={}
 for _,row in ipairs(guardianBirths) do
  if row.owner==owner and (row.model.Parent==session.world or row.world==session.world) then
   row.world=session.world;table.insert(result,row)
  end
 end
 return result
end
local function attack(actor,session,owner,times)
 for _=1,times do
  advanceTo(now+3)
  RunService.Heartbeat:Fire(.25)
  trigger(actor,session.castleModels[owner].door,'攻城攻撃')
  births(session,owner)
  away(actor,session)
 end
end
local function leave(actor)
 Players.PlayerRemoving:Fire(actor)
 for i=#currentPlayers,1,-1 do if currentPlayers[i]==actor then table.remove(currentPlayers,i) end end
 actor.Parent=nil
 if actor.Character then actor.Character:Destroy() end
 RunService.Heartbeat:Fire(.25)
end
local function freshPlayer(id,name)
 local actor=Instance.new('Player');actor.Name=name;actor.UserId=id;actor.Parent=Players
 local gui=Instance.new('PlayerGui');gui.Parent=actor
 local bag=Instance.new('Backpack');bag.Parent=actor
 local character=Instance.new('Model');character.Name=name..'Avatar';character.Parent=workspace
 local hum=Instance.new('Humanoid');hum.WalkSpeed=16;hum.Parent=character
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=character
 character.PrimaryPart=root;actor.Character=character
 table.insert(currentPlayers,actor)
 Players.PlayerAdded:Fire(actor)
 return actor
end

local ok,err=pcall(function()
 advanceTo(now)
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 local entered=now
 advanceTo(entered+11.99);equal(#capturedSessions,0,'original READY before12s')
 advanceTo(entered+12.01);equal(#capturedSessions,1,'one real TEAM session')
 local old=capturedSessions[1]
 check(old.mode=='TEAM' and old.rules.phase=='ACTIVE','real TEAM active')
 check(old.isCurrentHuman(player) and old.isCurrentHuman(second),'old exact humans')
 equal(humanoid.MaxHealth,195,'real MAGE regen attach')
 equal(secondHumanoid.MaxHealth,250,'real WARRIOR regen attach')
 check(stubCalls['BotActors.start']==nil and stubCalls['Regen.attach']==nil
  and stubCalls['Guardian.refresh']==nil,'real owners replaced preliminary stubs')
 away(player,old);away(second,old)
 pass('TEAM_READY_MAGE','real Host prompts/12s READY; real BotActors and NaturalRegen attached')

 attack(second,old,'42',10)
 local first=births(old,'42')
 equal(#first,1,'first real threshold spawn count')
 equal(old.rules.castles['42'].hp,700,'original first threshold700')
 roleResult('FIRST_OLD_CASTLE_ROLE',first[1],'MAGE','before leave; original owner chose MAGE')
 local firstAt=first[1].at

 leave(player)
 check(old.rules.phase=='ACTIVE' and old.world.Parent~=nil,'remaining human keeps TEAM alive')
 check(old.rules.castles['42'].isAI==true,'actual Host PlayerRemoving invokes actual BotActors takeover')
 check(old.botActors['42'] and old.botActors['42'].Parent,'actual replacement bot exists')
 check(not old.isCurrentHuman(player),'departed object rejected')
 pass('LEAVE_TAKEOVER','old MAGE player exits; actual same castle changes to AI without closing TEAM')

 advanceTo(firstAt+40.01)
 attack(second,old,'42',5)
 local secondWave=births(old,'42')
 equal(#secondWave,2,'second actual threshold spawn count')
 equal(old.rules.castles['42'].hp,400,'original second threshold400')
 roleResult('OLD_CASTLE_ROLE_AFTER_LEAVE',secondWave[2],'MAGE','old session must retain its role after lobby selection map entry is cleared')

 local rejoined=freshPlayer(42,'RejoinedSameUser')
 local peer=freshPlayer(44,'NewBRPeer')
 check(rejoined~=player and rejoined.UserId==player.UserId,'new identity with same UserId')
 trigger(rejoined,scenes:FindFirstChild('ROLE_NINJA'),'職業選択')
 trigger(peer,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(rejoined,scenes:FindFirstChild('BATTLE_ROYALE_PORTAL'),'参加する')
 trigger(peer,scenes:FindFirstChild('BATTLE_ROYALE_PORTAL'),'参加する')
 local brEntered=now
 advanceTo(brEntered+12.01);equal(#capturedSessions,2,'second real session')
 local fresh=capturedSessions[2]
 check(fresh.mode=='BATTLE_ROYALE' and fresh.rules.phase=='ACTIVE','new BR active')
 check(fresh.isCurrentHuman(rejoined) and not old.isCurrentHuman(rejoined),'Host membership separates old AI/new human')
 equal(rejoined.Character:FindFirstChildOfClass('Humanoid').MaxHealth,185,'new NINJA regen attach')
 away(rejoined,fresh);away(peer,fresh)
 pass('REJOIN_NEW_BR_NINJA','same UserId new Player selects NINJA in independently active BR; exact Host membership stays separate')

 attack(peer,fresh,'42',10)
 local newBirths=births(fresh,'42')
 equal(#newBirths,1,'first new BR guardian')
 roleResult('NEW_BR_CASTLE_ROLE',newBirths[1],'NINJA','new session owns its NINJA selection')
 local freshHum=rejoined.Character:FindFirstChildOfClass('Humanoid')
 freshHum:TakeDamage(10)
 local damaged=freshHum.Health
 advanceTo(now+8)
 RunService.Heartbeat:Fire(.25)
 check(freshHum.Health>damaged,'actual later natural regen heartbeat is executed')
 pass('POST_REJOIN_REGEN_TICK','real new-session NaturalRegen advances after real HealthChanged quiet period')

 check(now-secondWave[2].at>=40,'original guardian cooldown elapsed')
 attack(second,old,'42',4)
 local third=births(old,'42')
 equal(#third,3,'third original threshold spawn count')
 equal(old.rules.castles['42'].hp,160,'third original threshold below200')
 roleResult('OLD_CASTLE_ROLE_AFTER_REJOIN',third[3],'MAGE','new BR NINJA choice must not change old TEAM MAGE castle guardian')
 equal(old.castleSiegeStates['42'].guardianTotal,3,'same original max-total budget')
 equal(fresh.castleSiegeStates['42'].guardianTotal,1,'new session budget separate')
 for _,row in ipairs(third) do
  print('TRACE\tOLD_GUARDIAN\t'..row.owner..'\t'..row.role..'\t'..row.actorType..'\t'..row.maxHealth..'\t'..row.gear..'\t'..row.at)
 end
 for _,row in ipairs(newBirths) do print('TRACE\tNEW_GUARDIAN\t'..row.owner..'\t'..row.role..'\t'..row.actorType..'\t'..row.maxHealth..'\t'..row.gear..'\t'..row.at) end

 leave(second)
 check(old.rules.phase=='ABANDONED' and old.world.Parent==nil,'old TEAM ends with its last human')
 check(fresh.rules.phase=='ACTIVE' and fresh.world.Parent~=nil,'old cleanup preserves new BR')
 leave(peer);leave(rejoined)
 check(fresh.rules.phase=='ABANDONED' and fresh.world.Parent==nil,'new BR ends independently')
 advanceTo(now+50)
 RunService.Heartbeat:Fire(.25)
 equal(#pending,0,'all runnable late tasks drain after both sessions close')
 equal(#warnings,0,'no suppressed optional dependency warnings')
 pass('BOTH_SESSION_CLEANUP','actual leave/closeRound shuts down all guardians; late tasks drain; isolated parked Bot/Swarm jobs never ran')
 print('METRIC\tparked_unrelated_jobs\t'..#diagnosticParked)
 print('METRIC\tscheduler_resumes\t'..schedulerResumes)
 if #roleFailures>0 then error('GUARDIAN_ROLE_LIFECYCLE_LEAK: '..table.concat(roleFailures,','),0) end
end)
print('CASE\tWHOLE_HOST_GUARDIAN_ROLE_LIFECYCLE\t'..(if ok then 'PASS' else 'FAIL')..'\t'..tostring(err or 'all role lifetime checks passed'):gsub('\n',' '))
for _,message in ipairs(warnings) do print('WARNING\t'..message) end
if not ok then error(err,0) end


end
else
do
-- Separately labeled direct attach/refresh source diagnostic, not a Host prompt run.
-- Actual Rules, SiegeBridge and Guardian bodies perform all policy decisions.
-- Stationary fixture bot supplies the bridge's legal non-human siege actor.
local expectedActors={
 WARRIOR={actorType='Guardian_SHIELD_KNIGHT',hp=110,gear='Signature_SHIELD'},
 MAGE={actorType='Guardian_ICE_MAGE',hp=70,gear='Signature_STAFF'},
 NINJA={actorType='Guardian_SHADOW_SCOUT',hp=68,gear='Signature_TWIN_BLADES'},
 TRAPPER={actorType='Guardian_PSY_PUPPET',hp=86,gear='Signature_PSI_ORB'},
 BUILDER={actorType='Guardian_CLOCK_GOLEM',hp=125,gear='Signature_HAMMER'},
 BEAST={actorType='Guardian_GUARD_WOLF',hp=84,gear='Signature_CLAWS'},
 ZOMBIE={actorType='Guardian_CURSE_SOLDIER',hp=76,gear='Signature_CURSE_BANNER'},
}
local allCases={}
for _,role in ipairs({'WARRIOR','MAGE','NINJA','TRAPPER','BUILDER','BEAST','ZOMBIE'}) do
 table.insert(allCases,{name=role,initial=role,wanted=role})
end
table.insert(allCases,{name='MISSING_SELECTION',wanted='WARRIOR'})
table.insert(allCases,{name='INVALID_SELECTION',initial='UNRECOGNIZED_ROLE',wanted='WARRIOR'})
table.insert(allCases,{name='NIL_MAP',noMap=true,wanted='WARRIOR'})
table.insert(allCases,{name='NONTABLE_MAP',stringMap=true,wanted='WARRIOR'})
table.insert(allCases,{name='AI_NONNUMERIC_OWNER',ai=true,initial='MAGE',wanted='WARRIOR'})
local failures={}
local Rules=dependencies.EGGRUMBLE_CastleMatchRules
local Bridge=dependencies.EGGRUMBLE_CastleSiegeBridge
local Guardian=dependencies.EGGRUMBLE_CastleGuardianRuntime
local function assertion(name,condition,detail)
 print('CASE\t'..name..'\t'..(if condition then 'PASS' else 'FAIL')..'\t'..detail)
 if not condition then table.insert(failures,name) end
end
local function roleAssertion(name,row,wanted)
 local expected=expectedActors[wanted]
 assertion(name,row.role==wanted and row.actorType==expected.actorType and row.isModel
  and row.maxHealth==expected.hp and row.initialHealth==expected.hp and row.gear==expected.gear,
  'role='..tostring(row.role)..' expected='..wanted..' actor='..tostring(row.actorType)
  ..' expected_actor='..expected.actorType..' maxHP='..tostring(row.maxHealth)
  ..' expected_maxHP='..expected.hp..' initialHP='..tostring(row.initialHealth)..' gear='..tostring(row.gear))
end
advanceTo(now)
local ok,err=pcall(function()
 for index,case in ipairs(allCases) do
  local owner=if case.ai then 'AI_ROLE_TEST' else tostring(100+index)
  local foe='1999'
  local state=Rules.new('BATTLE_ROYALE',{{id=owner,isAI=case.ai==true},{id=foe,isAI=true}},0)
  Rules.start(state)
  local world=Instance.new('Folder');world.Name='RoleArchetype_'..case.name;world.Parent=workspace
  local bot=Instance.new('Model');bot.Name='StationaryLegalSiegeActor';bot.Parent=world
  local hum=Instance.new('Humanoid');hum.Parent=bot
  local root=Instance.new('Part');root.Name='HumanoidRootPart'
  root.Position=Vector3.new(100000,0,100000);root.Parent=bot;bot.PrimaryPart=root
  local session={mode='BATTLE_ROYALE',rules=state,world=world,humans={},
   castleModels={},castleLocations={[owner]=Vector3.new(index*1000,0,0),[foe]=root.Position},
   botActors={[foe]=bot}}
  local siege=Bridge.attach(session,Rules)
  local uid=tonumber(owner)
  local selections={}
  if case.ai then selections[owner]=case.initial
  elseif case.initial then selections[uid]=case.initial end
  local roleInput=if case.noMap then nil elseif case.stringMap then 'MAGE' else selections
  local controller=Guardian.attach(session,roleInput)
  local observed={}
  local function collect()
   for _,row in ipairs(guardianBirths) do
    if row.owner==owner and row.model.Parent==world and not row.seenInArchetypes then
     row.seenInArchetypes=true;table.insert(observed,row)
    end
   end
  end
  local function siegeUntil(hp)
   local calls=0
   while state.castles[owner].hp>hp do
    calls+=1;assert(calls<60,'bounded bridge attacks')
    advanceTo(now+3)
    siege(owner,foe,26,false)
    controller.refresh();collect()
   end
  end
  siegeUntil(700)
  assert(#observed==1,'one initial actual policy threshold spawn '..case.name)
  roleAssertion('ARCHETYPE_'..case.name..'_INITIAL',observed[1],case.wanted)
  if uid then selections[uid]=nil else selections[owner]=nil end
  advanceTo(math.max(now,observed[1].at+40.01))
  siegeUntil(400)
  assert(#observed==2,'one second actual policy threshold spawn '..case.name)
  roleAssertion('ARCHETYPE_'..case.name..'_AFTER_CLEAR',observed[2],case.wanted)
  local other=if case.wanted=='MAGE' then 'NINJA' else 'MAGE'
  if uid then selections[uid]=other else selections[owner]=other end
  advanceTo(math.max(now,observed[2].at+40.01))
  siegeUntil(200)
  assert(#observed==3,'one third actual policy threshold spawn '..case.name)
  roleAssertion('ARCHETYPE_'..case.name..'_AFTER_RESELECT',observed[3],case.wanted)
  assert(session.castleSiegeStates[owner].guardianTotal==3,'original max-total budget')
  state.phase='ABANDONED';controller.shutdown();world:Destroy()
  advanceTo(now+50)
  local active=0
  for _ in pairs(session.castleSiegeStates[owner].guardianActive) do active+=1 end
  assertion('ARCHETYPE_'..case.name..'_CLEANUP',active==0 and #pending==0,
   'active='..active..' pending='..#pending..'; actual shutdown releases all original policy slots')
 end
 assert(#warnings==0,'no optional dependency warnings')
 print('METRIC\trole_archetypes\t7')
 print('METRIC\tfallback_inputs\t5')
 print('METRIC\tscheduler_resumes\t'..schedulerResumes)
 if #failures>0 then error('ROLE_SNAPSHOT_MATRIX_FAILURES: '..table.concat(failures,','),0) end
end)
print('CASE\tDIRECT_ATTACH_ARCHETYPE_MATRIX\t'..(if ok then 'PASS' else 'FAIL')..'\t'..tostring(err or 'all actor identities and lifecycle selections retained'):gsub('\n',' '))
if not ok then error(err,0) end

end
end
