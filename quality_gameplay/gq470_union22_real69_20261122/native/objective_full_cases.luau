-- Whole Host boots normally. This test drives its real prompts and real Tools.
-- It never directly invokes Policy.arm, onIncomingDamage or Runtime.filterDamage.
local function check(value,message)assert(value,message)end
local function equal(value,wanted,message)
 check(type(value)=='number' and math.abs(value-wanted)<1e-6,
  message..' actual='..tostring(value)..' expected='..tostring(wanted))
end
local function pass(name,detail)print('CASE\t'..name..'\tPASS\t'..detail)end
local scenes=workspace:FindFirstChild('EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW')
local function trigger(actor,part,verb)
 check(part~=nil,'actual prompt part '..verb)
 local selected=nil
 for _,child in ipairs(part:GetChildren())do
  if child:IsA('ProximityPrompt')and child.ActionText==verb then selected=child end
 end
 check(selected and selected.Enabled,'actual enabled prompt '..verb)
 actor.Character:FindFirstChild('HumanoidRootPart').CFrame=CFrame.new(part.Position+Vector3.new(0,0,1))
 ProximityPromptService.PromptTriggered:Fire(selected,actor)
 selected.Triggered:Fire(actor)
end
local function outsideField(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local away=floor.Position+Vector3.new(floor.Size.X+2000,20,floor.Size.Z+2000)
 rootPart.CFrame=CFrame.new(away)
 secondRoot.CFrame=CFrame.new(away+Vector3.new(100,0,0))
end
local function ready()
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 local entered=now
 advanceTo(entered+11.99);equal(#capturedSessions,0,'real 12 second READY retained')
 advanceTo(entered+12.01);equal(#capturedSessions,1,'one real Host session')
 local session=capturedSessions[1]
 check(session.rules.phase=='ACTIVE' and session.mode=='TEAM','real ACTIVE TEAM')
 check(session.isCurrentHuman(player) and session.isCurrentHuman(second),'real Host membership')
 check(session.guardians==guardianAttachments[1].controller,'real Guardian controller')
 check(session.swarm==swarmAttachments[1].api,'real Swarm controller')
 check(stubCalls['Swarm.start']==nil and stubCalls['Invul.attach']==nil
  and stubCalls['Guardian.refresh']==nil,'no preliminary policy stubs execute')
 equal(humanoid.WalkSpeed,20,'MAGE baseline speed')
 outsideField(session)
 pass('WHOLE_HOST_READY','28 actual complete modules, original 12 second READY and two current humans')
 return session
end
local function actualAwaken(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 rootPart.CFrame=CFrame.new(floor.Position+Vector3.new(180,floor.Size.Y*.5+3,80))
 local horde=session.world:FindFirstChild('NeutralHorde')
 local neutral=nil
 for _=1,6 do
  advanceTo(now+.2)
  for _,model in ipairs(horde:GetChildren())do
   local h=model:FindFirstChildOfClass('Humanoid')
   if h and h.Health>0 then neutral=model;break end
  end
  if neutral then break end
 end
 check(neutral and neutral:GetAttribute('EGGRUMBLE_Neutral')==true,'actual Swarm spawned hostile neutral')
 local tool=player:FindFirstChildOfClass('Backpack'):FindFirstChild('迎撃覚醒')
 check(tool and tool:IsA('Tool'),'actual Host-attached awakening Tool')
 tool.Parent=character
 tool.Activated:Fire()
 check(dependencies.EGGRUMBLE_InvulRuntime.currentPolicySnapshot(player).phase=='ARMED','actual Tool arms original policy')
 local beforeHealth=humanoid.Health
 local beforeWrites=#healthWrites
 local beforeRays=rayQueries
 local target=neutral.PrimaryPart.Position
 rootPart.CFrame=CFrame.new(target+Vector3.new(2,0,0),target)
 for _=1,15 do
  advanceTo(now+.1)
  if dependencies.EGGRUMBLE_InvulRuntime.currentPolicySnapshot(player).phase=='AWAKENED'then break end
 end
 local snapshot=dependencies.EGGRUMBLE_InvulRuntime.currentPolicySnapshot(player)
 check(snapshot.phase=='AWAKENED','actual Swarm melee must awaken through its real damage branch')
 equal(humanoid.Health,beforeHealth,'incoming real Swarm melee blocked by current policy')
 check(rayQueries>beforeRays,'actual melee queries executed')
 local observedSwarmRay=false
 for i=beforeRays+1,#queryTrace do
  if queryTrace[i].source=='SwarmCombat'then observedSwarmRay=true end
 end
 check(observedSwarmRay,'real full-source Swarm executed query')
 print('TRACE\tACTUAL_SWARM_AWAKEN\t'..beforeHealth..'\t'..humanoid.Health..'\t'..tostring(snapshot.phase)..'\tHP_WRITES='..(#healthWrites-beforeWrites))
 outsideField(session)
 pass('REAL_TOOL_REAL_SWARM_AWAKEN','real Tool arm and actual hostile Swarm melee, no direct Runtime or Policy test invocation')
 return player:GetAttribute('EGGRUMBLE_InvulUntil')
end
local ok,result=pcall(function()
 advanceTo(now)
 local session=ready()
 local untilTime=actualAwaken(session)
 check(type(untilTime)=='number' and untilTime>now,'actual current awakening deadline')
 local own=session.rules.castles['42']
 local enemy=session.rules.castles['43']
 local siege=session.castleSiegeStates['43']
 local enemyModel=session.castleModels['43'].model
 local gateHP=siege.gateHP
 local coreHP=enemy.hp
 trigger(player,session.castleModels['43'].door,'攻城攻撃')
 print('TRACE\tAWAKE_SIEGE\t'..gateHP..'\t'..siege.gateHP..'\t'..coreHP..'\t'..enemy.hp)
 equal(siege.gateHP,gateHP,'AWAKENED_GATE_DAMAGE_ALLOWED')
 equal(enemy.hp,coreHP,'AWAKENED_CORE_DAMAGE_ALLOWED')
 pass('AWAKENED_SIEGE_DENIED','actual Host door prompt preserves gate and core HP')
 local enemyEggs=enemy.vaultEggs
 check(type(enemyEggs)=='number','actual enemy vaultEggs ledger exists')
 local carried=own.heldEggs
 trigger(player,enemyModel:FindFirstChild('EggVault'),'敵の卵を奪取')
 equal(own.heldEggs,carried,'AWAKENED_VAULT_PICKUP_ALLOWED')
 equal(enemy.vaultEggs,enemyEggs,'enemy vaultEggs inventory preserved')
 pass('AWAKENED_VAULT_DENIED','actual Host vault prompt preserves actual carried egg ledger')
 local egg=session.world:FindFirstChild('FieldEgg_1')
 check(egg~=nil,'real field egg exists')
 trigger(player,egg,'卵を拾う')
 print('TRACE\tAWAKE_FIELD\t'..carried..'\t'..own.heldEggs..'\t'..tostring(egg.Parent==session.world))
 equal(own.heldEggs,carried,'AWAKENED_FIELD_PICKUP_ALLOWED')
 check(egg.Parent==session.world,'AWAKENED_FIELD_EGG_DESTROYED')
 check(dependencies.EGGRUMBLE_InvulRuntime.currentPolicySnapshot(player).phase=='AWAKENED','denied prompt does not consume defense')
 pass('AWAKENED_FIELD_DENIED','actual Host field prompt preserves physical egg and inventory while real policy remains awake')
 outsideField(session)
 advanceTo(untilTime+.01)
 check(dependencies.EGGRUMBLE_InvulRuntime.currentPolicySnapshot(player).phase=='NONE','actual awakening expires')
 trigger(player,egg,'卵を拾う')
 equal(own.heldEggs,carried+1,'ordinary field pickup resumes after real expiry')
 check(egg.Parent==nil,'actual accepted physical field egg consumed once')
 local deposited=own.depositedEggs or 0
 advanceTo(now+.6)
 trigger(player,session.castleModels['42'].model:FindFirstChild('OwnEggDeposit'),'卵を納入')
 equal(own.heldEggs,0,'actual deposit consumes carried ledger')
 equal(own.depositedEggs,deposited+1,'actual deposit credits one real egg')
 pass('EXPIRY_PICKUP_DEPOSIT_RESTORED','real expiry restores Host field pickup, physical consumption and server ledger deposit')
 check(#warnings==0,'no hidden dependency warning')
 return 'whole Host connects real Tool -> real Swarm damage -> actual defense -> real objective denial -> expiry -> pickup/deposit'
end)
print('CASE\tWHOLE_HOST_OBJECTIVE_CROSS\t'..(if ok then 'PASS'else 'FAIL')..'\t'..tostring(result):gsub('\n',' '))
for _,warning in ipairs(warnings)do print('WARNING\t'..warning)end
print('METRIC\tscheduler_resumes\t'..schedulerResumes)
print('METRIC\tray_queries\t'..rayQueries)
print('METRIC\toverlap_queries\t'..overlapQueries)
if not ok then error(result,0)end
