local function check(value,message)assert(value,message)end
local function equal(value,wanted,message)
 assert(type(value)=='number'and math.abs(value-wanted)<1e-6,
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
local function activate(actor,slot)
 local selected=nil
 for _,container in ipairs({actor:FindFirstChildOfClass('Backpack'),actor.Character})do
  for _,item in ipairs(container:GetChildren())do
   local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
   if item:IsA('Tool')and type(id)=='string'and id:match('^EGGRUMBLE_SKILL_'..slot..'_')then
    check(not selected,'one actual role skill');selected=item
   end
  end
 end
 check(selected~=nil,'actual equip skill '..slot)
 selected.Parent=actor.Character
 selected.Activated:Fire()
end
local function outsideField(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local away=floor.Position+Vector3.new(floor.Size.X+2000,20,floor.Size.Z+2000)
 rootPart.CFrame=CFrame.new(away)
 secondRoot.CFrame=CFrame.new(away+Vector3.new(100,0,0))
end
local function sharedRequires()
 local expected={
  {'CastleGuardianRuntime','EGGRUMBLE_InvulRuntime'},
  {'SwarmCombat','EGGRUMBLE_InvulRuntime'},
  {'SevenRoleCombat','EGGRUMBLE_InvulRuntime'},
  {'Host','EGGRUMBLE_InvulRuntime'},
  {'CastleGuardianRuntime','EGGRUMBLE_AttackGeometry'},
  {'SwarmCombat','EGGRUMBLE_AttackGeometry'},
  {'SevenRoleCombat','EGGRUMBLE_AttackGeometry'},
  {'Host','EGGRUMBLE_CastleGuardianRuntime'},
  {'Host','EGGRUMBLE_SwarmCombat'},
  {'Host','EGGRUMBLE_SevenRoleCombat'},
  {'Host','EGGRUMBLE_RoundReplay'},
 }
 for _,pair in ipairs(expected)do
  local found=false
  for _,entry in ipairs(moduleRequires)do
   if entry.caller==pair[1]and entry.name==pair[2]then
    check(entry.value==dependencies[pair[2]],'same required module instance '..pair[1]..'/'..pair[2]);found=true
   end
  end
  check(found,'actual require edge '..pair[1]..'/'..pair[2])
  print('TRACE\tREQUIRE\t'..pair[1]..'\t'..pair[2]..'\tSHARED')
 end
 for _,entry in ipairs(mobilityRequires)do
  check(entry.value==dependencies.EGGRUMBLE_BasicMobilityPolicy,'same pure mobility singleton')
 end
 check(stubCalls['Swarm.start']==nil and stubCalls['Invul.attach']==nil
  and stubCalls['Guardian.refresh']==nil,'actual modules replaced preliminary unrelated stubs before Host')
end
local function ready(label)
 local count=#capturedSessions
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 local entered=now
 advanceTo(entered+11.99);equal(#capturedSessions,count,'actual READY countdown not shortened')
 advanceTo(entered+12.01);equal(#capturedSessions,count+1,'one actual new Host session')
 local session=capturedSessions[#capturedSessions]
 check(session.rules.phase=='ACTIVE'and session.mode=='TEAM','actual active TEAM')
 check(session.isCurrentHuman(player)and session.isCurrentHuman(second),'both actual Host current humans')
 check(session.rules.castles['42'].team=='RED'and session.rules.castles['43'].team=='BLUE','actual opponents')
 check(session.guardians==guardianAttachments[#guardianAttachments].controller,'Host owns returned actual Guardian API')
 check(session.swarm==swarmAttachments[#swarmAttachments].api,'Host owns returned actual Swarm API')
 check(session.world:FindFirstChild('NeutralHorde')~=nil,'real Swarm created current Horde folder')
 check(session.fieldItemCount==9 and session.itemIntakeStatus=='READY','real Item require integration preserved')
 equal(humanoid.WalkSpeed,20,'actual baseline first human')
 equal(secondHumanoid.WalkSpeed,12,'actual baseline second human')
 check(#warnings==0,'no suppressed optional dependency error')
 outsideField(session)
 pass(label,'actual prompts and 12-second READY; actual Guardian/Swarm attach; two human membership')
 return session
end
local function guardianHit(session,label)
 local siege=session.castleSiegeStates['43']
 local castle=session.rules.castles['43']
 local door=session.castleModels['43'].door
 for _=1,10 do
  advanceTo(now+3)
  trigger(player,door,'攻城攻撃')
  outsideField(session)
 end
 equal(siege.gateHP,0,'real gate cleared through five bounded prompts')
 equal(castle.hp,700,'real core reached original Guardian threshold through five further prompts')
 local guardian=nil
 for _,model in ipairs(session.world:GetChildren())do
  if model:GetAttribute('EGGRUMBLE_GuardianOwner')=='43' then
   check(not guardian,'one first-threshold Guardian');guardian=model
  end
 end
 check(guardian~=nil,'actual Guardian runtime spawned from real siege threshold')
 check(guardian:GetAttribute('EGGRUMBLE_GuardianRole')=='WARRIOR','actual owner role selected Guardian')
 local gh=guardian:FindFirstChildOfClass('Humanoid')
 local target=guardian.PrimaryPart.Position
 equal(gh.Health,110,'actual Guardian starting HP')
 -- Aim through the actual open SiegeGate (CanCollide=false), centered at x+0.
 -- A straight x+8 approach is correctly blocked by CastleFrontRight.
 local opening=Vector3.new(door.Position.X,target.Y,door.Position.Z)
 rootPart.CFrame=CFrame.new(target-(target-opening).Unit*25,target)
 local calls=#guardianCalls
 activate(player,'A')
 if gh.Health~=80 then
  print('DEBUG_GUARDIAN',#guardianCalls-calls,player:GetAttribute('EGGRUMBLE_Role'),player:GetAttribute('EGGRUMBLE_SkillCastSignature'),humanoid.Health)
  for i=math.max(1,#queryTrace-3),#queryTrace do
   local q=queryTrace[i]
   print('DEBUG_RAY',q.source,q.line,q.hit and q.hit.Name or 'CLEAR',q.origin.X,q.origin.Y,q.origin.Z,q.delta.X,q.delta.Y,q.delta.Z)
  end
 end
 equal(gh.Health,80,'GUARDIAN_INCOMING_HIT_MISSING')
 check(#guardianCalls==calls+1,'one actual Combat -> session.guardians call')
 local call=guardianCalls[#guardianCalls]
 check(call.session==session and call.controller==session.guardians and call.player==player,
  'actual Host session Guardian receives correct player')
 check(call.root==rootPart and call.character==character and call.shape=='CRYSTAL'and call.result==1,
  'actual new API root/character/shape forwarded with real hit result')
 print('TRACE\tGUARDIAN_HIT\t'..label..'\t110\t80\tCRYSTAL\tCURRENT_ROOT_CHARACTER')
 outsideField(session)
 pass(label,'10 real siege prompts -> actual Guardian spawn -> actual MAGE Tool A -> 30 HP incoming damage')
 return guardian
end
local function spawnCurrentNeutral(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local at=floor.Position+Vector3.new(180,floor.Size.Y*.5+3,80)
 rootPart.CFrame=CFrame.new(at)
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
 check(neutral~=nil,'actual Swarm planner and spawn clearance created a live neutral')
 check(neutral:GetAttribute('EGGRUMBLE_Neutral')==true,'real original neutral identity')
 check(neutral.Parent==horde and horde.Parent==session.world,'actual neutral belongs to this Host world')
 return neutral
end
local function neutralKO(session,label)
 local neutral=spawnCurrentNeutral(session)
 local target=neutral.PrimaryPart.Position
 local before=session.swarm.getTotal()
 rootPart.CFrame=CFrame.new(target-Vector3.new(0,-1,21),target)
 activate(player,'B')
 local after=session.swarm.getTotal()
 check(after>before,'actual MAGE Tool B caused original Humanoid Died -> Swarm KO')
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),session.swarm.kills['42'],'published score equals current actual ledger')
 check(player:GetAttribute('EGGRUMBLE_NeutralKOs')>0,'actual current human received its KO')
 print('TRACE\tSWARM_KO\t'..label..'\t'..before..'\t'..after..'\tCURRENT_MEMBER')
 outsideField(session)
 advanceTo(now+.5)
 pass(label,'actual SpawnPacing/Fairness/clearance/Swarm spawn; actual Tool B -> Died -> current human KO')
 return after
end
local function parkOldSwarm(session)
 local selected={}
 for _,record in ipairs(swarmTasks)do
  if record.session==session then
   check(coroutine.status(record.thread)=='suspended','real Swarm coroutine running before park')
   selected[record.thread]=record
  end
 end
 local held={}
 for i=#pending,1,-1 do
  local entry=pending[i];local record=selected[entry.thread]
  if record then
   table.insert(held,{entry=table.remove(pending,i),record=record})
   selected[entry.thread]=nil
  end
 end
 check(next(selected)==nil,'each selected real Swarm coroutine found in engine queue')
 equal(#held,2,'exact original Swarm spawn and movement coroutines parked')
 return held
end
local function finishAndClose(session,oldHorde)
 advanceTo(session.deadlineLease.start+900.01)
 check(session.rules.phase=='FINISHED'and session.rules.winner~=nil,'actual deadline finished Rules')
 check(session.roundReplayScheduled and session.resultsDelivered,'actual Replay and Result scheduled')
 local finishAt=nil
 for _,row in ipairs(phaseWrites)do
  if row.instance==session.world and row.phase=='FINISHED'then finishAt=finishAt or row.at end
 end
 check(finishAt~=nil,'actual Host finish phase publication')
 advanceTo(finishAt+10.1)
 check(session.world.Parent==nil and oldHorde.Parent==nil,'actual Replay closeRound destroyed old world and Horde')
 check(session.neutralBudgetEpoch==nil,'Host retired old neutral epoch')
 equal(session.neutralBudget:snapshot().total,0,'old tickets released without leak')
 check(not session.isCurrentHuman(player)and not session.isCurrentHuman(second),'old Host membership retired')
 check(player:GetAttribute('EGGRUMBLE_QueuedMode')==nil and player:GetAttribute('EGGRUMBLE_Role')==nil,'actual lobby reset')
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),0,'actual Replay reset neutral score')
 equal(humanoid.WalkSpeed,20,'actual Replay baseline reset')
 check(#guardianShutdowns>=1 and guardianShutdowns[#guardianShutdowns].session==session,
  'actual Host called its real Guardian shutdown')
 pass('FINISH_AND_CLOSE','actual 900-second deadline; Replay 10-second close; Guardian shutdown; Horde/world destroy; budget retirement')
end

local ok,result=pcall(function()
 advanceTo(now)
 sharedRequires()
 pass('SHARED_MODULES','28 full actual Sources; cached Invul/Geometry/Mobility and Host module require identities')
 local first=ready('FIRST_READY')
 local firstHorde=first.world:FindFirstChild('NeutralHorde')
 local firstEpoch=first.neutralBudgetEpoch
 local firstGuardian=guardianHit(first,'FIRST_GUARDIAN_INCOMING')
 local firstScore=neutralKO(first,'FIRST_SWARM_KO')
 local held=parkOldSwarm(first)
 finishAndClose(first,firstHorde)
 check(firstGuardian.Parent==nil,'old actual Guardian removed before replay')
 local nextSession=ready('NEXT_READY')
 check(nextSession~=first and player.Character==character and second.Character==secondCharacter,'same human avatars explicitly entered next real session')
 check(nextSession.swarm~=first.swarm and nextSession.swarm.kills~=first.swarm.kills,'separate real Swarm registry per Host session')
 check(nextSession.neutralBudget==first.neutralBudget and nextSession.neutralBudgetEpoch>firstEpoch,'shared budget with fresh actual epoch')
 equal(nextSession.swarm.getTotal(),0,'fresh next-generation Swarm score')
 local freshNeutral=spawnCurrentNeutral(nextSession)
 local freshHumanoid=freshNeutral:FindFirstChildOfClass('Humanoid')
 local freshHealth=freshHumanoid.Health
 outsideField(nextSession)
 local published=#publishedWrites;local hp=#healthWrites
 local capacity=nextSession.neutralBudget:snapshot().total
 check(capacity>0,'new epoch owns actual live neutral tickets before old task delivery')
 for _,item in ipairs(held)do
  print('TRACE\tOLD_SWARM_RESUME\t'..item.record.line..'\t'..item.entry.at..'\t'..now)
  enqueue(now,item.entry.thread,item.entry.args)
 end
 advanceTo(now)
 for _,item in ipairs(held)do check(coroutine.status(item.entry.thread)=='dead','old Swarm task exited after late delivery')end
 equal(#publishedWrites,published,'old tasks cannot publish new-round KO/Musou')
 equal(#healthWrites,hp,'old tasks cannot damage new-round avatars')
 equal(nextSession.neutralBudget:snapshot().total,capacity,'old task cleanup cannot release new epoch tickets')
 equal(first.swarm.getTotal(),firstScore,'old Swarm score remains old ledger')
 equal(nextSession.swarm.getTotal(),0,'late old loops cannot initialize or credit new registry')
 local freshAt=freshNeutral.PrimaryPart.Position
 rootPart.CFrame=CFrame.new(freshAt-Vector3.new(0,-1,21),freshAt)
 local oldCall=first.swarm.damageFromPlayer(player,freshAt,21,52,'INFERNO')
 equal(oldCall,0,'old Swarm API rejects current avatar after old match end')
 equal(freshHumanoid.Health,freshHealth,'stale API cannot hit a real new-generation neutral')
 equal(first.guardians.damageFromPlayer(player,rootPart.Position,10,30,'CRYSTAL',rootPart,character),0,'old Guardian API remains closed')
 equal(#publishedWrites,published,'old API probes cannot publish current score')
 print('TRACE\tNEW_BUDGET_DURING_OLD_RESUME\t'..capacity..'\t'..nextSession.neutralBudget:snapshot().total)
 outsideField(nextSession)
 pass('OLD_GENERATION_RETIRED','two exact old Swarm jobs resumed after same-avatar READY with live new tickets, terminated without HP/KO/budget writes; stale APIs cannot hit fresh neutral')
 guardianHit(nextSession,'SECOND_GUARDIAN_INCOMING')
 local nextScore=neutralKO(nextSession,'SECOND_SWARM_KO')
 equal(first.swarm.getTotal(),firstScore,'new valid KO does not write old registry')
 equal(nextSession.swarm.getTotal(),nextScore,'new valid KO belongs to new registry')
 check(#warnings==0,'no suppressed dependency warning')
 return 'real Host Guardian and Swarm attach, real human prompts/Tools, actual cleanup, explicit same-avatar replay, late old jobs and fresh KO'
end)
print('CASE\tCOMBINED_HOST_RUNTIME\t'..(if ok then 'PASS'else 'FAIL')..'\t'..tostring(result):gsub('\n',' '))
for _,warning in ipairs(warnings)do print('WARNING\t'..warning)end
print('METRIC\tscheduler_resumes\t'..schedulerResumes)
print('METRIC\tray_queries\t'..rayQueries)
print('METRIC\toverlap_queries\t'..overlapQueries)
print('METRIC\tguardian_attachments\t'..#guardianAttachments)
print('METRIC\tswarm_attachments\t'..#swarmAttachments)
if not ok then error(result,0)end
