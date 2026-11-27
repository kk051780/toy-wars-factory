-- GQ470_SECTION_BEGIN SERVER_ENGINE
-- Additional engine-boundary model; frozen original fixtures remain unchanged.
-- Only explicitly selected signals defer. This is NOT global Roblox emulation.
-- Source: create.roblox.com/docs/scripting/events/deferred
-- Explicit Connection:Disconnect cancels queued invocations.
-- Destroy's implicit disconnect stops future events but retains queued ones.
local deferredSignals={}
local deferredQueue={}
local deferredTrace={}
local deferredSerial=0
local function deferredEvent(kind,detail)
 table.insert(deferredTrace,{kind=kind,detail=detail})
end
signal=function()
 local callbacks={}
 local object={}
 local meta={deferred=false,callbacks=callbacks,label='UNNAMED'}
 deferredSignals[object]=meta
 object.Connect=function(self,fn)
  signalCount+=1
  local entry={fn=fn,connected=true,cancelGeneration=0}
  table.insert(callbacks,entry)
  return {Disconnect=function()
   -- Explicit disconnect also cancels callbacks queued before implicit destroy.
   entry.connected=false
   entry.cancelGeneration+=1
   deferredEvent('EXPLICIT_DISCONNECT',meta.label)
  end}
 end
 object.Fire=function(self,...)
  local args=table.pack(...)
  for _,entry in ipairs(table.clone(callbacks)) do
   if entry.connected then
    if meta.deferred then
     deferredSerial+=1
     table.insert(deferredQueue,{entry=entry,generation=entry.cancelGeneration,
      args=args,label=meta.label,serial=deferredSerial})
     deferredEvent('QUEUED',meta.label)
    else
     entry.fn(table.unpack(args,1,args.n))
    end
   end
  end
 end
 object.DisconnectAll=function(self)
  -- This fixture-only method is used by the unchanged Instance Destroy boundary.
  for _,entry in ipairs(callbacks) do entry.connected=false end
  deferredEvent('IMPLICIT_DISCONNECT',meta.label)
 end
 return object
end
local function modelDeferred(object,label)
 local meta=deferredSignals[object]
 assert(meta,'signal must originate from additive model')
 meta.deferred=true;meta.label=label
 return object
end
local function drainDeferred()
 local delivered,cancelled=0,0
 for _=1,2000 do
  if #deferredQueue==0 then
   return delivered,cancelled
  end
  local item=table.remove(deferredQueue,1)
  if item.entry.cancelGeneration==item.generation then
   delivered+=1
   deferredEvent('DELIVERED',item.label)
   item.entry.fn(table.unpack(item.args,1,item.args.n))
  else
   cancelled+=1
   deferredEvent('CANCELLED',item.label)
  end
 end
 error('bounded deferred model queue exceeded',0)
end

local beforeDeferredInstance=Instance.new
Instance.new=function(class)
 local object=beforeDeferredInstance(class)
 object._props.AncestryChanged=signal()
 return object
end
local beforeDeferredWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local previous=self._props[key]
 beforeDeferredWrite(self,key,value)
 if key=='Parent' and previous~=value then
  local own=self._props.AncestryChanged
  if own then own:Fire(self,value)end
  -- Descendant notifications share the original changed ancestor and new parent.
  for _,descendant in ipairs(self:GetDescendants())do
   local related=descendant._props.AncestryChanged
   if related then related:Fire(self,value)end
  end
 end
end
local beforeDeferredDestroy=methods.Destroy
function methods:Destroy()
 beforeDeferredDestroy(self)
 -- Existing generic fixture auto-disconnects top-level signals on Destroy.
 -- Attribute-specific signals are nested; model the same implicit disconnect.
 for _,event in pairs(self._props.attributeSignals or {})do
  if deferredSignals[event] then event:DisconnectAll()end
 end
end

-- S1A acceptance ENGINE PREPEND ONLY.
-- Append after the immutable original fixtures and before every production body.
-- This adds scheduling controls and observations, never a B publisher or getter.
local growthEngine={
 worldSerial=0,worldPrefixes={},writes={},
 watched={
  EGGRUMBLE_BattleStage=true,EGGRUMBLE_BattleXP=true,EGGRUMBLE_GrowthActive=true,
  EGGRUMBLE_NeutralKOs=true,EGGRUMBLE_BattleLevel=true,EGGRUMBLE_Combo=true,
  EGGRUMBLE_BestCombo=true,
 },
}
function growthEngine.deferWorld(world)
 local prefix=growthEngine.worldPrefixes[world]
 if prefix then return prefix end
 growthEngine.worldSerial+=1
 prefix='GROWTH_WORLD_'..growthEngine.worldSerial..'|'
 growthEngine.worldPrefixes[world]=prefix
 modelDeferred(world:GetAttributeChangedSignal('EGGRUMBLE_MatchPhase'),prefix..'PHASE')
 modelDeferred(world.Destroying,prefix..'DESTROYING')
 modelDeferred(world.AncestryChanged,prefix..'ANCESTRY')
 local horde=world:FindFirstChild('NeutralHorde')
 if horde then modelDeferred(horde.Destroying,prefix..'HORDE_DESTROYING')end
 return prefix
end
function growthEngine.holdWorld(world)
 local prefix=growthEngine.worldPrefixes[world]
 assert(prefix,'mark real world Deferred before parking deliveries')
 local held={}
 for i=#deferredQueue,1,-1 do
  local item=deferredQueue[i]
  if item.label:sub(1,#prefix)==prefix then
   table.insert(held,1,table.remove(deferredQueue,i))
   deferredEvent('PARKED',item.label)
  end
 end
 return held
end
function growthEngine.extendHeld(destination,source)
 for _,item in ipairs(source)do table.insert(destination,item)end
end
function growthEngine.requeue(held)
 -- Preserve exact registered closure, event arguments and cancellation generation.
 -- This intentionally adversarial delay is not a claim of ordinary engine timing.
 for _,item in ipairs(held)do
  table.insert(deferredQueue,item)
  deferredEvent('REQUEUED',item.label)
 end
end
function growthEngine.writeCount(playerRef)
 local count=0
 for _,row in ipairs(growthEngine.writes)do
  if row.player==playerRef then count+=1 end
 end
 return count
end
function growthEngine.snapshot(playerRef)
 local result={}
 for key in pairs(growthEngine.watched)do result[key]=playerRef:GetAttribute(key)end
 return result
end
local beforeGrowthAcceptanceAttribute=methods.SetAttribute
function methods:SetAttribute(name,value)
 if self:IsA('Player') and growthEngine.watched[name] then
  local line=debug.info(2,'l')
  table.insert(growthEngine.writes,{
   player=self,userId=self.UserId,name=name,value=value,
   before=self:GetAttribute(name),at=now,line=line,source=sourceLabel(line),
  })
 end
 return beforeGrowthAcceptanceAttribute(self,name,value)
end

-- Observe actual functions registered through the engine Connect boundary.
-- Invocations always forward to the exact production closure with original args.
-- Cancellation alone is deliberately not accepted as stale-dispatch coverage.
growthEngine.callbackDispatches={}
local beforeGrowthObservedSignal=signal
signal=function()
 local object=beforeGrowthObservedSignal()
 local originalConnect=object.Connect
 object.Connect=function(self,fn)
  local connection=originalConnect(self,fn)
  local meta=deferredSignals[object]
  local entry=meta.callbacks[#meta.callbacks]
  local line=debug.info(fn,'l')
  entry.productionSource=sourceLabel(line)
  entry.productionLine=line
  entry.productionCallback=fn
  entry.actualInvocations=0
  entry.fn=function(...)
   entry.actualInvocations+=1
   table.insert(growthEngine.callbackDispatches,{
    entry=entry,callback=fn,source=entry.productionSource,line=line,
    label=meta.label,args=table.pack(...),at=now,
   })
   return fn(...)
  end
  return connection
 end
 return object
end
-- The frozen fixture creates this service signal before product loading.
-- It has no product subscribers yet. Recreate its engine boundary so optional
-- Deferred delivery also covers actual Host and actual Swarm PlayerRemoving.
Players.PlayerRemoving=signal()
function growthEngine.holdSignal(object,source)
 local meta=deferredSignals[object]
 assert(meta,'selected signal must use the observed boundary')
 local held={}
 for i=#deferredQueue,1,-1 do
  local item=deferredQueue[i]
  if item.label==meta.label and (source==nil or item.entry.productionSource==source)then
   table.insert(held,1,table.remove(deferredQueue,i))
   deferredEvent('PARKED',item.label)
  end
 end
 return held
end
function growthEngine.swarmWitness(held,wantedLabel)
 local result={}
 local seen={}
 for _,item in ipairs(held)do
  local entry=item.entry
  if entry.productionSource=='SwarmCombat'and not seen[entry]
   and (wantedLabel==nil or item.label==wantedLabel)then
   seen[entry]=true
   table.insert(result,{entry=entry,before=entry.actualInvocations,
    label=item.label,line=entry.productionLine,callback=entry.productionCallback})
  end
 end
 assert(#result>0,'MISSING_ACTUAL_REGISTERED_SWARM_CLOSURE_WITNESS')
 return result
end
function growthEngine.requireSwarmDispatch(witness,label)
 local delivered=0
 for _,row in ipairs(witness)do
  local count=row.entry.actualInvocations-row.before
  if count>0 then
   delivered+=count
   print('DISPATCH_WITNESS\t'..label..'\tSwarmCombat\t'..row.line..'\t'..row.label..'\t'..count)
  end
 end
 assert(delivered>0,'CANCELLED_ONLY_IS_NOT_STALE_SWARM_DISPATCH_COVERAGE:'..label)
 return delivered
end
-- GQ470_SECTION_END SERVER_ENGINE
-- GQ470_SECTION_BEGIN SERVER_CASES
-- S1A ACCEPTANCE CASES ONLY: append after all unchanged full production bodies
-- and the unchanged helper prefix from combined_cases_clear_los.luau.
-- No product function, KO ledger, B attribute or proposed getter is synthesized.
-- H93 is expected to stop at the actual first Host start with missing BattleStage.
local growthCases={}
function growthCases.observe(name,detail)
 print('OBSERVATION\t'..name..'\t'..detail)
end
function growthCases.describe(session,playerRef)
 return 'phase='..tostring(session.rules.phase)
  ..';currentHuman='..tostring(session.isCurrentHuman(playerRef))
  ..';ledger='..tostring(session.swarm.kills[tostring(playerRef.UserId)] or 0)
  ..';B='..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleStage'))
  ..';XP='..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleXP'))
  ..';active='..tostring(playerRef:GetAttribute('EGGRUMBLE_GrowthActive'))
  ..';KO='..tostring(playerRef:GetAttribute('EGGRUMBLE_NeutralKOs'))
  ..';legacyLevel='..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleLevel'))
end
function growthCases.expectPublic(playerRef,stage,xp,active,kos,label)
 equal(playerRef:GetAttribute('EGGRUMBLE_BattleStage'),stage,label..' stage')
 equal(playerRef:GetAttribute('EGGRUMBLE_BattleXP'),xp,label..' XP')
 check(playerRef:GetAttribute('EGGRUMBLE_GrowthActive')==active,label..' active flag')
 equal(playerRef:GetAttribute('EGGRUMBLE_NeutralKOs'),kos,label..' original KO attribute')
 local stats=playerRef:FindFirstChild('leaderstats')
 local score=stats and stats:FindFirstChild('NeutralKO')
 check(score~=nil,label..' existing KO leaderboard')
 equal(score.Value,kos,label..' existing KO leaderboard value')
end
function growthCases.expectSnapshot(session,playerRef,stage,xp,kos,label)
 check(type(session.swarm.getBattleGrowthSnapshot)=='function',
  'MISSING_PRODUCTION_GET_BATTLE_GROWTH_SNAPSHOT')
 local before=#growthEngine.writes
 local ledgerBefore=table.clone(session.swarm.kills)
 local totalBefore=session.swarm.getTotal()
 for _=1,2 do
  local value=session.swarm.getBattleGrowthSnapshot(tostring(playerRef.UserId))
  check(type(value)=='table',label..' actual snapshot object')
  equal(value.stage,stage,label..' snapshot stage')
  equal(value.xp,xp,label..' snapshot XP')
  equal(value.neutralKOs,kos,label..' snapshot KO')
 end
 equal(#growthEngine.writes,before,label..' getter must not write any watched Player attribute')
 equal(session.swarm.getTotal(),totalBefore,label..' getter preserves original total')
 for id,value in pairs(ledgerBefore)do equal(session.swarm.kills[id],value,label..' getter preserves ledger '..id)end
 for id,value in pairs(session.swarm.kills)do equal(value,ledgerBefore[id],label..' getter cannot add ledger key '..id)end
 equal(session.swarm.kills[tostring(playerRef.UserId)] or 0,kos,label..' original KO ledger retained')
end
function growthCases.expectStart(session,playerRef,label,legacyLevel)
 growthCases.observe('ACTUAL_HOST_START',label..';'..growthCases.describe(session,playerRef))
 local stage=playerRef:GetAttribute('EGGRUMBLE_BattleStage')
 if stage==nil then
  error('RED_MISSING_BATTLE_STAGE_AT_ACTUAL_HOST_START actual=nil expected=1',0)
 end
 growthCases.expectPublic(playerRef,1,0,true,0,label)
 check(playerRef:GetAttribute('EGGRUMBLE_BattleLevel')==legacyLevel,
  label..' original initial BattleLevel unchanged, actual='
   ..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleLevel'))..' expected='..tostring(legacyLevel))
 growthCases.expectSnapshot(session,playerRef,1,0,0,label)
end
function growthCases.realKO(session,duplicate)
 local neutral=spawnCurrentNeutral(session)
 local human=neutral:FindFirstChildOfClass('Humanoid')
 local target=neutral.PrimaryPart.Position
 local before=session.swarm.getTotal()
 local id=tostring(player.UserId)
 local beforePlayer=session.swarm.kills[id] or 0
 modelDeferred(human.Died,'REAL_NEUTRAL_DIED|'..session.world.Name..'|'
  ..tostring(neutral:GetAttribute('EGGRUMBLE_NeutralInstanceId')))
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 -- Trusted existing server API: real geometry/LOS/HP/attribution/Died/KoFence.
 -- No direct calls to credit, no synthetic KO or fabricated attribution receipt.
 local hits=session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE')
 equal(hits,1,'one actual neutral admitted by full Swarm geometry/LOS')
 equal(human.Health,0,'actual damage authority reached Humanoid death')
 equal(session.swarm.getTotal(),before,'Deferred Died has not run before resumption')
 local delivered=drainDeferred()
 check(delivered>0,'actual registered Died callback delivered at modeled resumption')
 equal(session.swarm.getTotal(),before+1,'one actual Died credited once')
 equal(session.swarm.kills[id],beforePlayer+1,'one original player KO ledger increment')
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),beforePlayer+1,'same original KO publisher')
 if duplicate then
  local combo=player:GetAttribute('EGGRUMBLE_Combo')
  local writes=growthEngine.writeCount(player)
  human.Died:Fire()
  drainDeferred()
  equal(session.swarm.getTotal(),before+1,'duplicate registered Died consumed once')
  equal(session.swarm.kills[id],beforePlayer+1,'duplicate Died cannot increase original ledger')
  equal(player:GetAttribute('EGGRUMBLE_Combo'),combo,'duplicate Died cannot change timed Combo')
  equal(growthEngine.writeCount(player),writes,'duplicate Died cannot republish growth/KO/legacy')
  growthCases.observe('DUPLICATE_DIED_CONSUMED',
   'explicit adversarial signal replay; genuine first damage/death; ledger='..(beforePlayer+1))
 end
 outsideField(session)
 advanceTo(now+.26)
 return neutral,human
end
function growthCases.earn(session,count)
 for _=1,count do growthCases.realKO(session,false)end
end
function growthCases.finish(session)
 advanceTo(session.deadlineLease.start+900.01)
 check(session.rules.phase=='FINISHED'and session.rules.winner~=nil,'actual 900-second deadline finished')
 check(session.roundReplayScheduled and session.resultsDelivered,'real Result and Replay executed')
 local finishAt=nil
 for _,row in ipairs(phaseWrites)do
  if row.instance==session.world and row.phase=='FINISHED'then finishAt=finishAt or row.at end
 end
 check(finishAt~=nil,'real Host FINISHED phase publication')
 check(not session.isCurrentHuman(player),'actual old membership rejects finished round')
 return finishAt
end
function growthCases.sameAttributes(playerRef,before,label)
 for name in pairs(growthEngine.watched)do
  check(playerRef:GetAttribute(name)==before[name],label..' mutated '..name)
 end
end
function growthCases.resumeOld(held)
 for _,item in ipairs(held)do enqueue(now,item.entry.thread,item.entry.args)end
 advanceTo(now)
 for _,item in ipairs(held)do
  check(coroutine.status(item.entry.thread)=='dead','exact old Swarm task terminates after late delivery')
 end
end
function growthCases.progression_and_legacy()
 local session=ready('GROWTH_ACTUAL_READY')
 growthCases.expectStart(session,player,'FIRST_START',nil)
 for count=1,25 do
  growthCases.realKO(session,count==1)
  if count==1 then
   growthCases.expectPublic(player,2,10,true,1,'KO1')
   growthCases.expectSnapshot(session,player,2,10,1,'KO1')
  elseif count==2 then
   growthCases.expectPublic(player,2,20,true,2,'KO2')
   growthCases.expectSnapshot(session,player,2,20,2,'KO2')
  elseif count==3 then
   growthCases.expectPublic(player,2,30,true,3,'KO3')
   growthCases.expectSnapshot(session,player,2,30,3,'KO3')
  elseif count==4 then
   growthCases.expectPublic(player,3,40,true,4,'KO4')
   growthCases.expectSnapshot(session,player,3,40,4,'KO4')
  elseif count==8 then
   growthCases.expectPublic(player,3,80,true,8,'KO8')
   growthCases.expectSnapshot(session,player,3,80,8,'KO8')
  elseif count==24 then
   growthCases.expectPublic(player,3,80,true,24,'KO24')
   growthCases.expectSnapshot(session,player,3,80,24,'KO24')
  elseif count==25 then
   growthCases.expectPublic(player,3,80,true,25,'KO25')
   growthCases.expectSnapshot(session,player,3,80,25,'KO25')
  end
  equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),if count<25 then 1 else 2,
   'original BattleLevel still advances only at KO25')
 end
 growthCases.observe('REAL_KO_THRESHOLDS','KO1=B2/10;KO4=B3/40;KO8=B3/80;KO25=B3/80;legacy25=2')
 return 'actual Host start; 25 genuine unique neutral deaths; duplicate receipt consumed; original BattleLevel threshold'
end
function growthCases.finished_deferred_snapshot()
 local session=ready('GROWTH_FINISH_READY')
 growthCases.expectStart(session,player,'FINISH_START',nil)
 growthCases.earn(session,4)
 growthCases.expectPublic(player,3,40,true,4,'BEFORE_FINISH')
 growthEngine.deferWorld(session.world)
 -- Prove a real hittable target first. Its genuine fatal-damage Died callback
 -- is then parked, so rejection after FINISHED cannot pass merely for no target.
 local neutral=spawnCurrentNeutral(session)
 local dying=neutral:FindFirstChildOfClass('Humanoid')
 local target=neutral.PrimaryPart.Position
 modelDeferred(dying.Died,'FINISH_PENDING_GENUINE_DIED')
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 equal(session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE'),1,'genuine pre-finish lethal hit')
 equal(dying.Health,0,'genuine pending Died originates from actual fatal damage')
 equal(session.swarm.getTotal(),4,'genuine Died queued before KO ledger credit')
 local heldDied=growthEngine.holdSignal(dying.Died)
 local diedWitness=growthEngine.swarmWitness(heldDied)
 outsideField(session)
 local heldTasks=parkOldSwarm(session)
 local oldCombo=player:GetAttribute('EGGRUMBLE_Combo')
 local oldLevel=player:GetAttribute('EGGRUMBLE_BattleLevel')
 growthCases.finish(session)
 growthCases.expectSnapshot(session,player,3,40,4,'BEFORE_DEFERRED_CLEANUP')
 -- No assertion of synchronous clearing inside Host.refresh/ResultService.
 growthCases.observe('BEFORE_FINISH_RESUMPTION',growthCases.describe(session,player))
 local heldCleanup=growthEngine.holdWorld(session.world)
 growthEngine.requeue(heldDied)
 drainDeferred()
 growthEngine.requireSwarmDispatch(diedWitness,'GENUINE_DIED_AFTER_FINISHED_BEFORE_CLEANUP')
 equal(session.swarm.getTotal(),4,'real delayed Died cannot credit after FINISHED')
 growthCases.expectPublic(player,3,40,true,4,'DIED_REJECTED_BEFORE_PHASE_DISPATCH')
 growthEngine.requeue(heldCleanup)
 local delivered,cancelled=drainDeferred()
 check(delivered>0,'independently owned phase cleanup delivered')
 growthCases.expectPublic(player,1,0,false,0,'AFTER_FINISH_RESUMPTION')
 growthCases.expectSnapshot(session,player,3,40,4,'FINAL_RESULT_SNAPSHOT')
 equal(player:GetAttribute('EGGRUMBLE_Combo'),oldCombo,'new cleanup does not reset legacy timed Combo')
 equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),oldLevel,'new cleanup does not reset old BattleLevel')
 check(#heldTasks==2,'cleanup completed with both original Swarm loops parked')
 growthCases.observe('FINISH_DEFERRED_CLEANUP',
  'delivered='..delivered..';cancelled='..cancelled..';public=B1/0/inactive/KO0;snapshot=B3/40/4')
 return 'real FINISHED; next modeled resumption cleanup; pure final snapshot from original kills; no cleanup loop'
end
function growthCases.same_player_next_round_stale()
 local first=ready('GROWTH_OLD_READY')
 growthCases.expectStart(first,player,'OLD_START',nil)
 growthCases.earn(first,4)
 growthEngine.deferWorld(first.world)
 local heldTasks=parkOldSwarm(first)
 local finishAt=growthCases.finish(first)
 local held=growthEngine.holdWorld(first.world)
 check(#held>0,'real old phase callback queued before adversarial delay')
 advanceTo(finishAt+10.1)
 check(first.world.Parent==nil,'actual Replay close destroyed old world')
 growthEngine.extendHeld(held,growthEngine.holdWorld(first.world))
 local nextSession=ready('GROWTH_NEXT_READY')
 check(nextSession~=first and player.Character==character,'same concrete Player and avatar enter real next round')
 growthCases.expectStart(nextSession,player,'NEXT_START',1)
 growthCases.realKO(nextSession,false)
 growthCases.expectPublic(player,2,10,true,1,'NEXT_KO1')
 local before=growthEngine.snapshot(player)
 local writes=growthEngine.writeCount(player)
 local capacity=nextSession.neutralBudget:snapshot().total
 local witness=growthEngine.swarmWitness(held,growthEngine.worldPrefixes[first.world]..'PHASE')
 growthEngine.requeue(held)
 local delivered,cancelled=drainDeferred()
 growthEngine.requireSwarmDispatch(witness,'SAME_PLAYER_OLD_PHASE_CLOSURE')
 growthCases.resumeOld(heldTasks)
 growthCases.sameAttributes(player,before,'old callback after same Player next round')
 equal(growthEngine.writeCount(player),writes,'old lease cannot even republish same values to newer Player lease')
 equal(nextSession.neutralBudget:snapshot().total,capacity,'old tasks do not release new neutral epoch')
 growthCases.expectPublic(player,2,10,true,1,'AFTER_OLD_DELIVERY')
 growthCases.expectSnapshot(first,player,3,40,4,'OLD_FINAL_LEDGER')
 growthCases.expectSnapshot(nextSession,player,2,10,1,'NEW_LEDGER')
 equal(first.swarm.damageFromPlayer(player,rootPart.Position,5,52,'CIRCLE'),0,'old API rejects actual new current human')
 growthCases.observe('SAME_PLAYER_LATE_CLEANUP',
  'held='..#held..';delivered='..delivered..';cancelled='..cancelled..';new=B2/10/1;writes=0')
 return 'same concrete Player real replay; exact old registered callbacks delayed and requeued; no newer-lease write'
end
function growthCases.makeReplacement()
 local oldPlayer=player
 modelDeferred(Players.PlayerRemoving,'REPLACEMENT_OLD_PLAYER_REMOVING')
 Players.PlayerRemoving:Fire(oldPlayer)
 -- Adversarially park only the actual old Swarm listener while allowing the
 -- exact Host removal callbacks to run. No membership function is substituted.
 local heldRemoving=growthEngine.holdSignal(Players.PlayerRemoving,'SwarmCombat')
 local removalWitness=growthEngine.swarmWitness(heldRemoving)
 drainDeferred()
 oldPlayer.Parent=nil
 currentPlayers={second}
 local replacement=Instance.new('Player')
 replacement.Name='GrowthReplacement42';replacement.UserId=oldPlayer.UserId;replacement.Parent=Players
 local gui=Instance.new('PlayerGui');gui.Parent=replacement
 local backpack=Instance.new('Backpack');backpack.Parent=replacement
 local avatar=Instance.new('Model');avatar.Name='GrowthReplacementAvatar';avatar.Parent=workspace
 local human=Instance.new('Humanoid');human.WalkSpeed=20;human.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=avatar
 avatar.PrimaryPart=root;replacement.Character=avatar
 currentPlayers={replacement,second}
 Players.PlayerAdded:Fire(replacement)
 player=replacement;playerGui=gui;bag=backpack
 character=avatar;humanoid=human;rootPart=root
 check(Players:GetPlayerByUserId(42)==replacement and replacement~=oldPlayer,
  'engine fixture resolves fresh concrete Player for same numeric UserId')
 return oldPlayer,heldRemoving,removalWitness
end
function growthCases.readySoloBR()
 local count=#capturedSessions
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(player,scenes:FindFirstChild('BATTLE_ROYALE_PORTAL'),'参加する')
 local entered=now
 advanceTo(entered+11.99);equal(#capturedSessions,count,'real BR READY not shortened')
 advanceTo(entered+12.01);equal(#capturedSessions,count+1,'one real BR session')
 local session=capturedSessions[#capturedSessions]
 check(session.mode=='BATTLE_ROYALE'and session.rules.phase=='ACTIVE','real replacement BR round active')
 check(session.isCurrentHuman(player)and not session.isCurrentHuman(second),'actual BR membership fence')
 check(session.swarm==swarmAttachments[#swarmAttachments].api,'actual replacement Swarm attached')
 outsideField(session)
 return session
end
function growthCases.replacement_player_same_user_id()
 local first=ready('GROWTH_REJOIN_OLD_READY')
 growthCases.expectStart(first,player,'REJOIN_OLD_START',nil)
 growthCases.earn(first,4)
 growthEngine.deferWorld(first.world)
 local heldTasks=parkOldSwarm(first)
 local oldPlayer,heldRemoving,removalWitness=growthCases.makeReplacement()
 check(first.rules.phase=='ACTIVE'and first.isCurrentHuman(second),'remaining real human keeps old TEAM active')
 growthCases.expectPublic(second,1,0,true,0,'REMAINING_OLD_HUMAN')
 check(not first.isCurrentHuman(player),'old Host rejects replacement after real removal')
 local nextSession=growthCases.readySoloBR()
 growthCases.expectStart(nextSession,player,'REPLACEMENT_START',nil)
 growthCases.realKO(nextSession,false)
 growthCases.expectPublic(player,2,10,true,1,'REPLACEMENT_KO1')
 first.closeRound(true)
 check(first.rules.phase=='ABANDONED'and first.world.Parent==nil,'actual old Host closeRound abandoned and destroyed world')
 local held=growthEngine.holdWorld(first.world)
 check(#held>0,'old independent cleanup or implicit-destroy invocation exists at engine boundary')
 -- New genuine progress is earned while old cleanup remains parked.
 growthCases.realKO(nextSession,false)
 growthCases.expectPublic(player,2,20,true,2,'REPLACEMENT_KO2')
 local before=growthEngine.snapshot(player)
 local writes=growthEngine.writeCount(player)
 local capacity=nextSession.neutralBudget:snapshot().total
 local phaseWitness=growthEngine.swarmWitness(held,growthEngine.worldPrefixes[first.world]..'PHASE')
 growthEngine.requeue(heldRemoving)
 growthEngine.requeue(held)
 local delivered,cancelled=drainDeferred()
 growthEngine.requireSwarmDispatch(removalWitness,'REPLACEMENT_OLD_PLAYER_REMOVING_CLOSURE')
 growthEngine.requireSwarmDispatch(phaseWitness,'REPLACEMENT_OLD_PHASE_CLOSURE')
 growthCases.resumeOld(heldTasks)
 growthCases.sameAttributes(player,before,'old cleanup must target concrete old Player, not UserId lookup')
 equal(growthEngine.writeCount(player),writes,'old concrete Player cleanup performs no replacement writes')
 equal(nextSession.neutralBudget:snapshot().total,capacity,'old abandoned tasks preserve replacement BR budget')
 check(oldPlayer~=player and oldPlayer.Parent==nil,'old concrete Player stays disconnected')
 check(nextSession.isCurrentHuman(player)and not first.isCurrentHuman(player),'real new membership stays current')
 growthCases.expectPublic(player,2,20,true,2,'AFTER_REPLACEMENT_STALE_DELIVERY')
 growthCases.expectSnapshot(first,oldPlayer,3,40,4,'DISCONNECTED_OLD_LEDGER')
 growthCases.expectSnapshot(nextSession,player,2,20,2,'REPLACEMENT_NEW_LEDGER')
 growthCases.observe('REPLACEMENT_PLAYER_LATE_CLEANUP',
  'sameUserId=42;differentConcretePlayer=true;held='..#held..';delivered='..delivered
   ..';cancelled='..cancelled..';new=B2/20/2;writes=0')
 return 'actual PlayerRemoving/PlayerAdded; new concrete same-UserId Player in real BR; delayed old TEAM cleanup'
end
function growthCases.same_round_death_respawn()
 local session=ready('GROWTH_RESPAWN_READY')
 growthCases.expectStart(session,player,'RESPAWN_START',nil)
 growthCases.earn(session,4)
 local oldCombo=player:GetAttribute('EGGRUMBLE_Combo')
 humanoid:TakeDamage(humanoid.Health)
 equal(humanoid.Health,0,'real fixture Humanoid death boundary')
 growthCases.expectPublic(player,3,40,true,4,'DEAD_SAME_ROUND')
 local old=character
 player.CharacterRemoving:Fire(old)
 old:Destroy()
 local avatar=Instance.new('Model');avatar.Name='GrowthRespawnAvatar';avatar.Parent=workspace
 local human=Instance.new('Humanoid');human.WalkSpeed=20;human.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=avatar
 avatar.PrimaryPart=root;player.Character=avatar
 character=avatar;humanoid=human;rootPart=root
 player.CharacterAdded:Fire(avatar)
 growthCases.expectPublic(player,3,40,true,4,'NEW_AVATAR_BEFORE_HOST_RETURN')
 advanceTo(now+.81)
 check(session.isCurrentHuman(player)and player.Character==avatar,'same real Host owns replacement avatar')
 check(player:GetAttribute('EGGRUMBLE_Role')=='MAGE','actual Host restored selected role')
 local tools=0
 for _,container in ipairs({bag,avatar})do
  for _,item in ipairs(container:GetChildren())do
   if item:IsA('Tool')and type(item:GetAttribute('EGGRUMBLE_InternalToolId'))=='string'then tools+=1 end
  end
 end
 check(tools>=3,'actual Combat.equip restored role tools after Host .8-second return')
 growthCases.expectPublic(player,3,40,true,4,'ACTUAL_HOST_RESPAWN')
 growthCases.expectSnapshot(session,player,3,40,4,'RESPAWN_LEDGER')
 equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),1,'legacy BattleLevel retained')
 equal(player:GetAttribute('EGGRUMBLE_Combo'),oldCombo,'timed Combo not relabeled or reset as death streak')
 outsideField(session)
 growthCases.observe('SAME_ROUND_REAL_HOST_RESPAWN','death->CharacterAdded->actualHost0.8s->CombatEquip;B3/40/4 retained')
 return 'same-round death and genuine Host delayed return preserve cumulative B/XP/KO'
end
function growthCases.finished_immediate_snapshot()
 local session=ready('GROWTH_IMMEDIATE_FINISH_READY')
 growthCases.expectStart(session,player,'IMMEDIATE_FINISH_START',nil)
 growthCases.earn(session,4)
 local held=parkOldSwarm(session)
 growthCases.finish(session)
 growthCases.expectPublic(player,1,0,false,0,'IMMEDIATE_FINISHED')
 growthCases.expectSnapshot(session,player,3,40,4,'IMMEDIATE_FINISHED_FINAL_SNAPSHOT')
 check(#held==2,'no growth cleanup loop')
 return 'real FINISHED under Immediate signal delivery clears public B while original final KO snapshot survives'
end
function growthCases.teardown(kind,deferred)
 local session=ready('GROWTH_TEARDOWN_READY')
 growthCases.expectStart(session,player,'TEARDOWN_START',nil)
 growthCases.realKO(session,false)
 local world=session.world
 if deferred then growthEngine.deferWorld(world)end
 -- This same actual living neutral is demonstrably hittable before detach.
 local target=spawnCurrentNeutral(session)
 local human=target:FindFirstChildOfClass('Humanoid')
 local point=target.PrimaryPart.Position
 rootPart.CFrame=clearNeutralApproach(target,point)
 equal(session.swarm.damageFromPlayer(player,point,.01,1,'CIRCLE'),1,'actual pre-teardown hittable control')
 local hp=human.Health
 local heldTasks=parkOldSwarm(session)
 local dispatchStart=#growthEngine.callbackDispatches
 local oldParent=world.Parent
 if kind=='destroy'then
  world:Destroy()
 elseif kind=='abandon'then
  session.closeRound(true)
 else
  world.Parent=nil
  equal(session.swarm.damageFromPlayer(player,point,.01,52,'CIRCLE'),0,'same hittable target rejected while exact world detached')
  equal(human.Health,hp,'detached-world API cannot damage the proven hittable neutral')
  if kind=='reattach'then world.Parent=oldParent end
 end
 if deferred then
  local queued=growthEngine.holdWorld(world)
  local label=growthEngine.worldPrefixes[world]..(
   if kind=='destroy'then 'DESTROYING'elseif kind=='abandon'then 'PHASE'else 'ANCESTRY')
  local witness=growthEngine.swarmWitness(queued,label)
  growthEngine.requeue(queued);drainDeferred()
  growthEngine.requireSwarmDispatch(witness,'TEARDOWN_'..kind)
 end
 local ownDeliveries=0
 for i=dispatchStart+1,#growthEngine.callbackDispatches do
  if growthEngine.callbackDispatches[i].source=='SwarmCombat'then ownDeliveries+=1 end
 end
 check(ownDeliveries>0,'actual candidate Swarm teardown callback executed')
 growthCases.expectPublic(player,1,0,false,0,'TEARDOWN_'..kind)
 growthCases.expectSnapshot(session,player,2,10,1,'TEARDOWN_FINAL_KO')
 if kind~='abandon'then check(session.rules.phase=='ACTIVE','external operation does not impersonate Host phase change')end
 if kind=='reattach'then
  check(world.Parent==oldParent,'captured nil-parent event still retires after reparent')
  equal(session.swarm.damageFromPlayer(player,point,.01,52,'CIRCLE'),0,'retired old world stays rejected after reparent')
  equal(human.Health,hp,'same restored target cannot be damaged through retired lease')
 end
 local writes=growthEngine.writeCount(player)
 drainDeferred()
 equal(growthEngine.writeCount(player),writes,'duplicate queued teardown does not republish')
 check(#heldTasks==2,'teardown did not need either original Swarm loop')
 growthCases.observe('ACTUAL_CANDIDATE_TEARDOWN',
  'kind='..kind..';delivery='..(if deferred then 'Deferred'else 'Immediate')
   ..';ownCallbacks='..ownDeliveries..';B1/0/inactive/KO0;final=1')
 return 'actual candidate own callback clears derived publication on '..kind
end
function growthCases.external_destroy_immediate()return growthCases.teardown('destroy',false)end
function growthCases.external_destroy_deferred()return growthCases.teardown('destroy',true)end
function growthCases.external_detach_immediate()return growthCases.teardown('detach',false)end
function growthCases.external_detach_deferred()return growthCases.teardown('detach',true)end
function growthCases.external_reattach_immediate()return growthCases.teardown('reattach',false)end
function growthCases.external_reattach_deferred()return growthCases.teardown('reattach',true)end
function growthCases.abandoned_immediate()return growthCases.teardown('abandon',false)end
function growthCases.abandoned_deferred()return growthCases.teardown('abandon',true)end
function growthCases.last_human_abandonment()
 local session=ready('GROWTH_LAST_HUMAN_READY')
 growthCases.expectStart(session,player,'LAST_HUMAN_START',nil)
 growthCases.realKO(session,false)
 growthEngine.deferWorld(session.world)
 modelDeferred(Players.PlayerRemoving,'LAST_HUMAN_REMOVING')
 Players.PlayerRemoving:Fire(player)
 player.Parent=nil;currentPlayers={second}
 drainDeferred()
 check(session.rules.phase=='ACTIVE'and session.isCurrentHuman(second),'first actual departure leaves remaining human active')
 growthCases.expectPublic(second,1,0,true,0,'REMAINING_LAST_HUMAN')
 Players.PlayerRemoving:Fire(second)
 second.Parent=nil;currentPlayers={}
 drainDeferred()
 check(session.rules.phase=='ABANDONED'and session.world.Parent==nil,'real last departure invokes Host abandonment and destroys world')
 equal(session.neutralBudget:snapshot().total,0,'real Host retired neutral epoch')
 check(not session.isCurrentHuman(player)and not session.isCurrentHuman(second),'old real memberships retired')
 growthCases.expectSnapshot(session,player,2,10,1,'ABANDONED_FINAL_KO')
 growthCases.observe('REAL_LAST_HUMAN_ABANDONMENT','actual2PlayerRemoving->HostABANDONED->worldnil;disconnected attributes are not a live UI')
 return 'actual last-human leave; disconnected concrete Player state cannot become a replacement-player publication'
end
function growthCases.false_fake_spectator_membership()
 local session=ready('GROWTH_MEMBERSHIP_READY')
 growthCases.expectStart(session,player,'MEMBERSHIP_START',nil)
 local neutral=spawnCurrentNeutral(session)
 local human=neutral:FindFirstChildOfClass('Humanoid')
 local target=neutral.PrimaryPart.Position
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 equal(session.swarm.damageFromPlayer(player,target,.01,1,'CIRCLE'),1,'same target is hittable by genuine current Player')
 local health=human.Health
 local fake=Instance.new('Player');fake.Name='AdversarialSameId';fake.UserId=player.UserId;fake.Parent=Players
 fake.Character=character
 check(fake~=player and session.isCurrentHuman(fake),'actual numeric Host membership alone accepts same-id fixture double')
 equal(session.swarm.damageFromPlayer(fake,target,.01,52,'CIRCLE'),0,'concrete-token guard rejects same-id fake')
 equal(human.Health,health,'same-id fake cannot damage known hittable neutral')
 fake.Parent=nil
 local spectator=Instance.new('Player');spectator.Name='ConnectedSpectator';spectator.UserId=99;spectator.Parent=Players
 local avatar=Instance.new('Model');avatar.Parent=workspace
 local h=Instance.new('Humanoid');h.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.CFrame=rootPart.CFrame;root.Parent=avatar
 avatar.PrimaryPart=root;spectator.Character=avatar
 table.insert(currentPlayers,spectator)
 check(not session.isCurrentHuman(spectator),'actual connected spectator never joined this Host')
 equal(session.swarm.damageFromPlayer(spectator,target,.01,52,'CIRCLE'),0,'spectator rejected at concrete current-human API boundary')
 equal(human.Health,health,'spectator cannot damage same known hittable neutral')
 growthCases.expectPublic(player,1,0,true,0,'NO_FALSE_KO_PUBLICATION')
 Players.PlayerRemoving:Fire(player)
 check(session.rules.phase=='ACTIVE'and not session.isCurrentHuman(player),'actual Host removal revokes old human while peer remains')
 equal(session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE'),0,'real departed human rejected with still-valid avatar and target')
 equal(human.Health,health,'departed human cannot damage same proven target')
 equal(session.swarm.getTotal(),0,'all three negative callers leave original total unchanged')
 growthCases.expectSnapshot(session,player,1,0,0,'NO_FALSE_LEDGER_CREDIT')
 growthCases.observe('CONCRETE_CURRENT_HUMAN_NEGATIVES',
  'realControlHit=1;sameIdFake=0;connectedSpectator=0;actualDepartedHuman=0;sameTargetHPUnchanged;ledger0')
 return 'proven hittable neutral; fake same-id Player, actual spectator and actual departed human rejected without damage or KO'
end

local ok,result=pcall(function()
 advanceTo(now)
 sharedRequires()
 check(type(growthCases[AUDIT_VARIANT])=='function','unknown S1A acceptance variant')
 local detail=growthCases[AUDIT_VARIANT]()
 check(#warnings==0,'no suppressed dependency warning')
 return detail
end)
print('CASE\tGROWTH_ACCEPTANCE_'..AUDIT_VARIANT..'\t'..(if ok then 'PASS'else 'FAIL')
 ..'\t'..tostring(result):gsub('\n',' '))
for _,warning in ipairs(warnings)do print('WARNING\t'..warning)end
print('METRIC\tscheduler_resumes\t'..schedulerResumes)
print('METRIC\tgrowth_attribute_writes\t'..#growthEngine.writes)
print('METRIC\tdeferred_trace_entries\t'..#deferredTrace)
if not ok then error(result,0)end
-- GQ470_SECTION_END SERVER_CASES
-- GQ470_SECTION_BEGIN UI_OBSERVERS
-- Extra read-only engine-boundary observations for the H93 growth baseline.
-- Frozen prior fixtures remain byte-identical. No product function is replaced.
local growthObservedWrites={}
local priorGrowthSetAttribute=methods.SetAttribute
function methods:SetAttribute(name,value)
 if (self==player or self==second) and
  (name=='EGGRUMBLE_NeutralKOs' or name=='EGGRUMBLE_BattleLevel'
   or name=='EGGRUMBLE_Combo' or name=='EGGRUMBLE_BestCombo'
   or name=='EGGRUMBLE_Role') then
  local line=debug.info(2,'l')
  table.insert(growthObservedWrites,{player=self,name=name,value=value,
   before=self:GetAttribute(name),at=now,line=line,source=sourceLabel(line)})
 end
 return priorGrowthSetAttribute(self,name,value)
end
-- GQ470_SECTION_END UI_OBSERVERS
-- GQ470_SECTION_BEGIN UI_ENGINE
-- Additive Native engine boundaries for complete H93 Hero/HUD execution.
-- This file does not calculate growth, KO credit, role choice or match phase.
-- GUI rectangles are deterministic UDim arithmetic, not Roblox rendering.
local UIAudit={created={},writes={},renderCallbacks={},realm='server',serverEpochOffset=100000}
do
 local guiClasses={Frame=true,TextLabel=true,TextButton=true,ImageLabel=true,
  ImageButton=true,ScrollingFrame=true,ViewportFrame=true}
 local previousIsA=methods.IsA
 function methods:IsA(class)
  return previousIsA(self,class) or class=='GuiObject' and guiClasses[self.ClassName]==true
   or class=='LayerCollector' and (self.ClassName=='ScreenGui' or self.ClassName=='BillboardGui')
 end
 local function addSignals(object)
  for _,name in ipairs({'ChildAdded','ChildRemoved','DescendantAdded','DescendantRemoving',
   'AncestryChanged','Destroying'}) do
   if not object._props[name] then object._props[name]=signal() end
  end
  if object:IsA('Humanoid') and not object._props.HealthChanged then object._props.HealthChanged=signal() end
 end
 addSignals(workspace)
 for _,object in ipairs(workspace:GetDescendants()) do addSignals(object) end
 for _,p in ipairs(currentPlayers) do
  addSignals(p)
  for _,object in ipairs(p:GetDescendants()) do addSignals(object) end
 end
 local beforeNew=Instance.new
 Instance.new=function(class)
  local object=beforeNew(class)
  addSignals(object)
  if guiClasses[class] then
   object._props.Size=UDim2.fromOffset(100,100)
   object._props.Position=UDim2.fromOffset(0,0)
   object._props.AnchorPoint=Vector2.new(0,0)
   object._props.ClipsDescendants=false
   object._props.Text=''
   object._props.TextSize=14
   object._props.TextScaled=false
   object._props.TextWrapped=false
   object._props.Rotation=0
   object._props.ZIndex=1
  elseif class=='RemoteEvent' then
   object._props.OnClientEvent=signal()
  elseif class=='UISizeConstraint' then
   object._props.MinSize=Vector2.new(0,0)
   object._props.MaxSize=Vector2.new(math.huge,math.huge)
  end
  local line=debug.info(2,'l')
  table.insert(UIAudit.created,{object=object,class=class,at=now,line=line,source=sourceLabel(line)})
  return object
 end
 function methods:GetPropertyChangedSignal(name)
  if not self._props.propertySignals then self._props.propertySignals={} end
  if not self._props.propertySignals[name] then self._props.propertySignals[name]=signal() end
  return self._props.propertySignals[name]
 end
 function methods:GetFullName()
  local names={self.Name};local cursor=self.Parent
  while cursor and cursor._props do table.insert(names,1,cursor.Name);cursor=cursor.Parent end
  return table.concat(names,'.')
 end
 local oldFind=methods.FindFirstChild
 function methods:FindFirstChild(name,recursive)
  local found=oldFind(self,name)
  if found or not recursive then return found end
  for _,child in ipairs(self:GetChildren()) do
   found=child:FindFirstChild(name,true)
   if found then return found end
  end
  return nil
 end
 local function ancestors(parent)
  local out={};local cursor=parent
  while cursor and cursor._props do table.insert(out,cursor);cursor=cursor.Parent end
  return out
 end
 local beforeWrite=instanceMeta.__newindex
 instanceMeta.__newindex=function(self,key,value)
  local before=self._props[key]
  local moving=key=='Parent' and before~=value
  local descendants=nil
  if moving then
   descendants={self}
   for _,child in ipairs(self:GetDescendants()) do table.insert(descendants,child) end
   for _,ancestor in ipairs(ancestors(before)) do
    if ancestor._props.DescendantRemoving then
     for _,descendant in ipairs(descendants) do ancestor.DescendantRemoving:Fire(descendant) end
    end
   end
  end
  beforeWrite(self,key,value)
  if moving then
   for _,ancestor in ipairs(ancestors(value)) do
    if ancestor._props.DescendantAdded then
     for _,descendant in ipairs(descendants) do ancestor.DescendantAdded:Fire(descendant) end
    end
   end
   if self._props.AncestryChanged then self.AncestryChanged:Fire(self,value) end
  end
  if before~=value and self._props.propertySignals and self._props.propertySignals[key] then
   self._props.propertySignals[key]:Fire()
  end
  if self:IsA('GuiObject') and (key=='Text' or key=='Visible' or key=='Size') then
   local line=debug.info(2,'l')
   table.insert(UIAudit.writes,{object=self,key=key,value=value,before=before,
    at=now,line=line,source=sourceLabel(line)})
  end
 end
 UIAudit.camera=Instance.new('Camera')
 UIAudit.camera.ViewportSize=Vector2.new(393,851)
 workspace._props.CurrentCamera=UIAudit.camera
 workspace.GetServerTimeNow=function() return now+UIAudit.serverEpochOffset end
 local beforeIndex=instanceMeta.__index
 local absoluteSize,absolutePosition
 absoluteSize=function(object)
  if object.ClassName=='PlayerGui' or object.ClassName=='ScreenGui' then
   return UIAudit.camera.ViewportSize
  end
  if not guiClasses[object.ClassName] then return Vector2.new(0,0) end
  local parent=object.Parent
  local basis=parent and parent._props and absoluteSize(parent) or Vector2.new(0,0)
  local size=object.Size
  local x=math.max(0,basis.X*size.X.Scale+size.X.Offset)
  local y=math.max(0,basis.Y*size.Y.Scale+size.Y.Offset)
  local constraint=object:FindFirstChildOfClass('UISizeConstraint')
  if constraint then
   x=math.clamp(x,constraint.MinSize.X,constraint.MaxSize.X)
   y=math.clamp(y,constraint.MinSize.Y,constraint.MaxSize.Y)
  end
  return Vector2.new(x,y)
 end
 absolutePosition=function(object)
  if not guiClasses[object.ClassName] then return Vector2.new(0,0) end
  local parent=object.Parent
  local parentSize=parent and parent._props and absoluteSize(parent) or Vector2.new(0,0)
  local parentAt=parent and parent._props and absolutePosition(parent) or Vector2.new(0,0)
  local size=absoluteSize(object);local at=object.Position;local anchor=object.AnchorPoint
  return Vector2.new(parentAt.X+parentSize.X*at.X.Scale+at.X.Offset-size.X*anchor.X,
   parentAt.Y+parentSize.Y*at.Y.Scale+at.Y.Offset-size.Y*anchor.Y)
 end
 instanceMeta.__index=function(self,key)
  if key=='AbsoluteSize' then return absoluteSize(self) end
  if key=='AbsolutePosition' then return absolutePosition(self) end
  return beforeIndex(self,key)
 end
 UIAudit.rect=function(object)
  local at=object.AbsolutePosition;local size=object.AbsoluteSize
  return {x=at.X,y=at.Y,w=size.X,h=size.Y}
 end
 UIAudit.intersects=function(a,b)
  return math.min(a.x+a.w,b.x+b.w)>math.max(a.x,b.x)
   and math.min(a.y+a.h,b.y+b.h)>math.max(a.y,b.y)
 end
 UIAudit.replication=Instance.new('ReplicatedStorage')
 local module=Instance.new('ModuleScript');module.Name='EGGRUMBLE_HudPresentationPolicy';module.Parent=UIAudit.replication
 UIAudit.mapRemote=Instance.new('RemoteEvent');UIAudit.mapRemote.Name='EGGRUMBLE_MapIntelUpdate_V1'
 UIAudit.mapRemote.Parent=UIAudit.replication
 UIAudit.input={InputBegan=signal(),InputEnded=signal(),TouchEnabled=true,KeyboardEnabled=false}
 local oldService=game.GetService
 game.GetService=function(self,name)
  if name=='ReplicatedStorage' then return UIAudit.replication end
  if name=='UserInputService' then return UIAudit.input end
  return oldService(self,name)
 end
 local oldRequire=require
 require=function(moduleRef)
  local name=if type(moduleRef)=='table' and moduleRef._props and moduleRef:IsA('ModuleScript') then moduleRef.Name else moduleRef
  return oldRequire(name)
 end
 Players.LocalPlayer=player
 RunService.RenderStepped=signal()
 local renderConnect=RunService.RenderStepped.Connect
 RunService.RenderStepped.Connect=function(self,callback)
  local line=debug.info(callback,'l')
  table.insert(UIAudit.renderCallbacks,{callback=callback,line=line,source=sourceLabel(line)})
  return renderConnect(self,callback)
 end
 RunService.IsServer=function()return UIAudit.realm=='server'end
 RunService.IsClient=function()return UIAudit.realm=='client'end
 UIAudit.client=function(callback,...)
  local old=UIAudit.realm;UIAudit.realm='client'
  local result=table.pack(pcall(callback,...))
  UIAudit.realm=old
  if not result[1] then error(result[2],0) end
  return table.unpack(result,2,result.n)
 end
 UIAudit.frame=function(dt) UIAudit.client(function()RunService.RenderStepped:Fire(dt or .17)end) end
 UIAudit.deliverMap=function(payload) UIAudit.client(function()UIAudit.mapRemote.OnClientEvent:Fire(payload)end) end
 UIAudit.viewport=function(w,h) UIAudit.camera.ViewportSize=Vector2.new(w,h);UIAudit.frame() end
 -- Realistic rig presence, supplied at the engine boundary before source load.
 -- This is not an animation/rigid-body solver; these anchors are not visual proof.
 UIAudit.rig=function(model)
  if not model:FindFirstChild('UpperTorso') then
   local torso=Instance.new('Part');torso.Name='UpperTorso';torso.CanCollide=false;torso.Parent=model
  end
  if not model:FindFirstChild('Head') then
   local head=Instance.new('Part');head.Name='Head';head.CanCollide=false;head.Parent=model
  end
 end
 UIAudit.rig(character);UIAudit.rig(secondCharacter)
end
-- GQ470_SECTION_END UI_ENGINE
-- GQ470_SECTION_BEGIN UI_ACCEPT_ENGINE
-- Additional engine-only acceptance observations. The existing UI boundary,
-- frozen fixtures and all product files remain unmodified.
-- Reference: https://create.roblox.com/docs/scripting/events/deferred
-- This is an explicitly controlled queue at selected boundaries, not a complete
-- Roblox scheduler or a claim that all engine events run in Deferred mode.
local UIAcceptanceEngine={writes={},queue={},registrations={},legacyRegions={},holdDepth=0,
 flushing=false,delivered=0,dropped=0,automaticDisconnects=0,explicitDisconnects=0}
do
 local ownedEvents=setmetatable({},{__mode='k'})
 local function legacyCallback(source,line)
  local span=fullSourceRanges[source]
  if not span then return false end
  local relative=line-span.first+1
  for _,region in ipairs(UIAcceptanceEngine.legacyRegions[source] or {})do
   if relative>=region.first and relative<=region.last then return true end
  end
  return false
 end
 local captured={EGGRUMBLE_BattleStage=true,EGGRUMBLE_BattleXP=true,EGGRUMBLE_GrowthActive=true}
 local previousAttribute=methods.SetAttribute
 function methods:SetAttribute(name,value)
  -- This is deliberately the outermost engine writer wrapper, so debug.info(2)
  -- names the production writer, not another observer's forwarding function.
  if captured[name] then
   local line=debug.info(2,'l')
   table.insert(UIAcceptanceEngine.writes,{object=self,name=name,value=value,
    before=self:GetAttribute(name),at=now,line=line,source=sourceLabel(line),realm=UIAudit.realm})
  end
  return previousAttribute(self,name,value)
 end
 local function invoke(entry,args)
  local oldRealm=UIAudit.realm;UIAudit.realm=entry.realm
  local result=table.pack(pcall(entry.callback,table.unpack(args,1,args.n or #args)))
  UIAudit.realm=oldRealm
  if not result[1] then error(result[2],0) end
 end
 local function decorateSignal(event,owner,signalName,alwaysImmediate)
  if owner then
   event._uiOwner=owner
   if not ownedEvents[owner]then ownedEvents[owner]={}end
   ownedEvents[owner][event]=true
  end
  if signalName then event._uiSignalName=signalName end
  if alwaysImmediate then event._uiAlwaysImmediate=true end
  if rawget(event,'_uiDeferredInstrumented') then
   for _,entry in ipairs(event._uiEntries)do
    entry.owner=event._uiOwner;entry.signalName=event._uiSignalName
   end
   return event
  end
  event._uiDeferredInstrumented=true
  local entries={}
  event._uiEntries=entries
  local originalConnect=event.Connect
  local originalDisconnectAll=event.DisconnectAll
  event.Connect=function(self,callback)
   local line=debug.info(callback,'l')
   local source=sourceLabel(line)
   local entry={callback=callback,line=line,source=source,realm=UIAudit.realm,
    owner=event._uiOwner,signalName=event._uiSignalName,event=event,
    legacyCallback=legacyCallback(source,line),connected=true,cancelPending=false}
   table.insert(entries,entry)
   table.insert(UIAcceptanceEngine.registrations,entry)
   local function forward(...)
    local args=table.pack(...)
    if UIAcceptanceEngine.holdDepth>0 or UIAcceptanceEngine.flushing then
     table.insert(UIAcceptanceEngine.queue,{entry=entry,args=args})
    else invoke(entry,args) end
   end
   -- Preserve the original callback identity for the existing frame observer.
   local connection=originalConnect(self,if event._uiAlwaysImmediate then callback else forward)
   return setmetatable({Disconnect=function()
    if entry.connected or not entry.cancelPending then
     UIAcceptanceEngine.explicitDisconnects+=1
    end
    entry.connected=false;entry.cancelPending=true
    connection:Disconnect()
   end},{__index=function(_,key)
    if key=='Connected' then return entry.connected end
    error('unknown fixture RBXScriptConnection member '..tostring(key))
   end})
  end
  event.DisconnectAll=function(self)
   -- Frozen Instance:Destroy invokes this internal fixture operation. Roblox
   -- automatic destruction disconnects future firing but retains queued calls.
   for _,entry in ipairs(entries)do
    if entry.connected then UIAcceptanceEngine.automaticDisconnects+=1 end
    entry.connected=false
   end
   return originalDisconnectAll(self)
  end
  event.Once=function(self,callback)
   local connection
   connection=self:Connect(function(...)
    connection:Disconnect();callback(...)
   end)
   -- The forwarding closure is fixture machinery. Attribute a Once binding to
   -- the actual supplied source callback, just as Connect is attributed.
   local entry=entries[#entries]
   entry.line=debug.info(callback,'l');entry.source=sourceLabel(entry.line)
   entry.legacyCallback=legacyCallback(entry.source,entry.line)
   return connection
  end
  return event
 end
 local originalSignal=signal
 signal=function()return decorateSignal(originalSignal())end
 local function inspectSignals(object)
  for name,value in pairs(object._props)do
   if type(value)=='table' and type(rawget(value,'Connect'))=='function'
    and type(rawget(value,'Fire'))=='function' then decorateSignal(value,object,name) end
  end
 end
 local previousAttributeSignal=methods.GetAttributeChangedSignal
 function methods:GetAttributeChangedSignal(name)
  return decorateSignal(previousAttributeSignal(self,name),self,'Attribute:'..name)
 end
 local previousPropertySignal=methods.GetPropertyChangedSignal
 function methods:GetPropertyChangedSignal(name)
  return decorateSignal(previousPropertySignal(self,name),self,'Property:'..name)
 end
 local previousDestroy=methods.Destroy
 function methods:Destroy()
  previousDestroy(self)
  -- Frozen generic Destroy already disconnects direct signals. Include the
  -- generic attribute/property signal tables owned by this same Instance;
  -- this models engine lifetime, never an application cleanup predicate.
  for event in pairs(ownedEvents[self] or {})do event:DisconnectAll()end
 end
 inspectSignals(workspace)
 for _,object in ipairs(workspace:GetDescendants())do inspectSignals(object)end
 for _,actor in ipairs(currentPlayers)do
  inspectSignals(actor)
  for _,object in ipairs(actor:GetDescendants())do inspectSignals(object)end
 end
 inspectSignals(UIAudit.replication)
 for _,object in ipairs(UIAudit.replication:GetDescendants())do inspectSignals(object)end
 inspectSignals(UIAudit.camera)
 decorateSignal(Players.PlayerAdded,Players,'PlayerAdded')
 decorateSignal(Players.PlayerRemoving,Players,'PlayerRemoving')
 decorateSignal(RunService.Heartbeat,RunService,'Heartbeat')
 decorateSignal(RunService.RenderStepped,RunService,'RenderStepped',true)
 -- RenderStepped remains the existing explicit frame/resumption boundary. Its
 -- source attribution observer is unchanged; no new frame callback is added.
 UIAcceptanceEngine.hold=function()UIAcceptanceEngine.holdDepth+=1 end
 UIAcceptanceEngine.release=function()
  assert(UIAcceptanceEngine.holdDepth>0,'deferred boundary hold required')
  UIAcceptanceEngine.holdDepth-=1
  if UIAcceptanceEngine.holdDepth>0 then return end
  UIAcceptanceEngine.flushing=true
  for _=1,20000 do
   if #UIAcceptanceEngine.queue==0 then UIAcceptanceEngine.flushing=false;return end
   local pendingEvent=table.remove(UIAcceptanceEngine.queue,1)
   if pendingEvent.entry.cancelPending then
    UIAcceptanceEngine.dropped+=1
   else
    UIAcceptanceEngine.delivered+=1
    invoke(pendingEvent.entry,pendingEvent.args)
   end
  end
  UIAcceptanceEngine.flushing=false
  error('bounded deferred fixture queue exhausted',0)
 end
 UIAcceptanceEngine.atomic=function(callback)
  UIAcceptanceEngine.hold()
  local result=table.pack(pcall(callback))
  UIAcceptanceEngine.release()
  if not result[1]then error(result[2],0)end
 end
 UIAcceptanceEngine.isUI=function(entry)
  return entry.source=='HeroSilhouetteArt' or entry.source=='HudIntelRuntime'
 end
 UIAcceptanceEngine.isOwnedBy=function(entry,object)
  local owner=entry.owner
  return owner==object or owner and owner._props~=nil and owner:IsDescendantOf(object)
 end
 UIAcceptanceEngine.captureLive=function(predicate)
  local found={}
  for _,entry in ipairs(UIAcceptanceEngine.registrations)do
   if entry.connected and predicate(entry)then table.insert(found,entry)end
  end
  return found
 end
 UIAcceptanceEngine.liveCount=function(predicate)
  return #UIAcceptanceEngine.captureLive(predicate)
 end
 -- Generic defaults used only for inspecting future production-created GUI.
 -- No instances with the accepted growth component names are created here.
 local previousNew=Instance.new
 Instance.new=function(class)
  local object=previousNew(class)
  inspectSignals(object)
  if class=='BillboardGui'then
   object._props.AlwaysOnTop=false
   object._props.MaxDistance=math.huge
   object._props.Size=UDim2.fromOffset(0,0)
   object._props.StudsOffset=Vector3.new(0,0,0)
  end
  return object
 end
 allowedNil.Adornee=true
end
-- GQ470_SECTION_END UI_ACCEPT_ENGINE
-- GQ470_SECTION_BEGIN UI_GENERIC_API
-- Generic engine boundary missing from the frozen CFrame fixture. The real
-- current arena floor is unrotated; retain the frozen approximate orientation
-- model and do not implement any arena/admission/growth predicate here.
do
 local previousFrameIndex=frameMeta.__index
 local function pointToObjectSpace(frame,point)
  assert(math.abs(frame.LookVector.Y)<1e-8 and math.abs(frame.RightVector.Y)<1e-8,
   'native PointToObjectSpace only supports the frozen planar CFrame basis')
  local delta=point-frame.Position
  return Vector3.new(delta:Dot(frame.RightVector),delta.Y,-delta:Dot(frame.LookVector))
 end
 frameMeta.__index=function(frame,key)
  if key=='PointToObjectSpace'then return pointToObjectSpace end
  if type(previousFrameIndex)=='function'then return previousFrameIndex(frame,key)end
  return previousFrameIndex and previousFrameIndex[key] or nil
 end
 local probe=CFrame.new(10,20,30):PointToObjectSpace(Vector3.new(13,25,23))
 assert(probe.X==3 and probe.Y==5 and probe.Z==-7,'generic CFrame inverse translation fixture control')
end
-- GQ470_SECTION_END UI_GENERIC_API
-- GQ470_SECTION_BEGIN UI_CASES
-- Future S1A UI acceptance against genuine full-source combat/lifecycle events.
-- The fixture never writes the three new attributes and never creates either
-- component named in this contract. Missing components are NOT_REACHED for
-- visibility checks, never vacuous PASS.
local UIContract={tag='EGGRUMBLE_BattleGrowthTag',footer='BattleGrowthFooter',
 stage='EGGRUMBLE_BattleStage',xp='EGGRUMBLE_BattleXP',active='EGGRUMBLE_GrowthActive',
 getter='getBattleGrowthSnapshot',maxTagDistance=80}
local UIExpect={red=0,notReached=0,passed=0,everTag=false,everFooter=false,
 maxLiveHero=0,maxLiveHud=0,retiredHeroLive=0}
local function expectation(name,fn,reachable)
 if reachable==false then
  UIExpect.notReached+=1
  print('EXPECTATION\t'..name..'\tNOT_REACHED\trequired production UI component was absent')
  return false
 end
 local ok,detail=pcall(fn)
 if ok then UIExpect.passed+=1 else UIExpect.red+=1 end
 print('EXPECTATION\t'..name..'\t'..(if ok then 'PASS' else 'RED')..'\t'..tostring(detail or 'requirements observed'):gsub('\n',' '))
 return ok
end
local function observeUI(name,detail)print('OBSERVATION\t'..name..'\t'..detail)end
local function clickUI(object)UIAudit.client(function()object.Activated:Fire()end)end
local function exactNumberToken(text,prefix,expected,detail)
 -- Capture the entire numeric token before comparing: KO4 must not match KO40,
 -- B3 must not match B30, and duplicate/decimal/identifier tokens are rejected.
 local count=0;local from=1
 while true do
  local first,last,digits=text:find(prefix..'(%d+)',from)
  if not first then break end
  local before=if first>1 then text:sub(first-1,first-1) else ''
  local after=text:sub(last+1,last+1)
  check(before=='' or before:find('[%w_]')==nil,detail..' has a left token boundary')
  check(after=='' or after:find('[%w_.,]')==nil,detail..' has a right integer-token boundary')
  equal(tonumber(digits),expected,detail..' exact numeric value')
  count+=1;from=last+1
 end
 equal(count,1,detail..' occurs exactly once')
end
local function heroOwned(object)
 return UIAcceptanceEngine.captureLive(function(entry)
  return entry.source=='HeroSilhouetteArt' and UIAcceptanceEngine.isOwnedBy(entry,object)
 end)
end
local function heroPlayerOwned(actor,avatar)
 return UIAcceptanceEngine.captureLive(function(entry)
  return entry.source=='HeroSilhouetteArt'
   and (entry.owner==actor or avatar and UIAcceptanceEngine.isOwnedBy(entry,avatar))
 end)
end
local function requireDisconnected(entries,detail)
 for _,entry in ipairs(entries)do
  check(not entry.connected,detail..': '..entry.source..'/'..tostring(entry.signalName)..' remains live')
 end
end
local function liveSource(source)
 return UIAcceptanceEngine.liveCount(function(entry)return entry.source==source end)
end
local function observeConnections(label)
 local hero=liveSource('HeroSilhouetteArt');local hud=liveSource('HudIntelRuntime')
 UIExpect.maxLiveHero=math.max(UIExpect.maxLiveHero,hero)
 UIExpect.maxLiveHud=math.max(UIExpect.maxLiveHud,hud)
 observeUI('CONNECTIONS_'..label,'HeroLive='..hero..';HUDLive='..hud)
 return hero,hud
end
local function requireHudConnectionContract()
 -- Exact existing H93 inventory: 13 fixed GUI actions, one map remote, one
 -- RenderStepped, and three unchanged LegacyExplore Player attributes.
 local registered=0;local legacy=0
 for _,entry in ipairs(UIAcceptanceEngine.registrations)do
  if entry.source=='HudIntelRuntime'then
   registered+=1
   check(entry.connected,'existing HUD connection remains live for its client lifetime')
   if entry.owner==player then
    check(entry.legacyCallback,'HUD adds no Player attribute/character subscriptions')
    legacy+=1
   end
  end
 end
 equal(registered,18,'HUD adds zero subscriptions to the exact existing 18')
 equal(legacy,3,'unchanged LegacyExplore block retains its existing three Player callbacks')
 UIExpect.hudRegistrations=registered
end
local function requireNoExtraFramePolling()
 local render=0;local heartbeat=0
 for _,entry in ipairs(UIAcceptanceEngine.registrations)do
  if UIAcceptanceEngine.isUI(entry) and entry.owner==RunService then
   if entry.signalName=='RenderStepped'then
    render+=1;check(entry.source=='HudIntelRuntime' and entry.connected,'existing HUD frame subscription survives')
   elseif entry.signalName=='Heartbeat'then heartbeat+=1 end
  end
 end
 equal(render,1,'exactly one historical UI RenderStepped registration, including retired registrations')
 equal(heartbeat,0,'UI adds no Heartbeat registration, including retired registrations')
 equal(#UIAudit.renderCallbacks,1,'original render observer also sees exactly one callback')
 UIExpect.uiHeartbeatRegistrations=heartbeat
end
local function fixedHPAndBuffs(gui,width)
 local status=gui:FindFirstChild('CompactStatus')
 local hp=status:FindFirstChild('HP');local buffs=status:FindFirstChild('Buffs')
 equal(humanoid.Health,117,'explicit live Humanoid health oracle')
 equal(humanoid.MaxHealth,230,'explicit live Humanoid maximum oracle')
 check(hp.Text=='HP 117/230','literal existing HP text, not candidate self-comparison')
 check(buffs.Text=='属性 FIRE 燃焼 鈍足','literal existing filtered status text')
 local sr=UIAudit.rect(status);local br=UIAudit.rect(gui:FindFirstChild('MusouCharge'))
 equal(sr.y,9,'H93 compact status top remains y9');equal(sr.h,27,'H93 status height remains 27')
 check(sr.w>=110 and sr.x>=0 and sr.x+sr.w<=width,'H93 status horizontal bounds remain')
 equal(br.y,37,'H93 Musou bar remains y37');equal(br.h,5,'H93 Musou bar remains height5')
 check(not UIAudit.intersects(sr,br),'existing status and Musou stay separate')
 equal(hp.Size.X.Scale,.45,'original HP width scale');equal(hp.Size.X.Offset,-3,'original HP width offset')
 equal(hp.Position.X.Scale,0,'original HP x scale');equal(hp.Position.X.Offset,6,'original HP x offset')
 equal(buffs.Size.X.Scale,.55,'original Buffs width scale');equal(buffs.Size.X.Offset,-5,'original Buffs width offset')
 equal(buffs.Position.X.Scale,.45,'original Buffs x scale');equal(buffs.Position.X.Offset,2,'original Buffs x offset')
 equal(hp.TextSize,12,'original HP font size');equal(buffs.TextSize,11,'original Buffs font size')
 check(not hp.TextWrapped and not buffs.TextWrapped,'original status does not add wrapped lines')
 check(hp.TextTruncate==Enum.TextTruncate.AtEnd and buffs.TextTruncate==Enum.TextTruncate.AtEnd,
  'original truncation contract remains; rendered text fit is not tested')
end
local function findTags(actor)
 local found={};local avatar=actor.Character
 if avatar then
  for _,object in ipairs(avatar:GetDescendants())do
   if object.Name==UIContract.tag then table.insert(found,object)end
  end
 end
 return found
end
local function tagVisible(tag)
 return tag and tag.Parent~=nil and tag.Enabled==true
end
local function tagText(tag)
 local text={}
 for _,object in ipairs(tag:GetDescendants())do
  if object:IsA('TextLabel')then table.insert(text,object.Text)end
 end
 return table.concat(text,' '):gsub('%s','')
end
local function requireTag(actor,stage,kos)
 local tags=findTags(actor)
 equal(#tags,1,'exactly one production growth tag under this concrete human character')
 local tag=tags[1];local head=actor.Character:FindFirstChild('Head')
 check(tag:IsA('BillboardGui') and tagVisible(tag),'active head tag is enabled BillboardGui')
 local target=if tag.Adornee~=nil then tag.Adornee else tag.Parent
 local hum=actor.Character:FindFirstChildOfClass('Humanoid')
 check(head and head:IsA('BasePart') and head.Parent==actor.Character
  and hum and hum.Health>0 and target==head,'effective Adornee is the current living concrete Head')
 check(tag.AlwaysOnTop==false,'head tag must not render through occluders')
 check(type(tag.MaxDistance)=='number' and tag.MaxDistance>0 and tag.MaxDistance<=UIContract.maxTagDistance,
  'nearby tag MaxDistance is positive and bounded at 80 studs')
 local text=tagText(tag)
 exactNumberToken(text,'この試合B',stage,'tag current-match B')
 exactNumberToken(text,'中立KO',kos,'tag genuine neutral KO')
 check(text:find('Lv',1,true)==nil,'new stage is not mislabeled as permanent Lv')
 UIExpect.everTag=true
 return tag
end
local function hiddenTag(actor)
 local tags=findTags(actor)
 check(#tags<=1,'hidden/retired state never leaves duplicate tags')
 for _,tag in ipairs(tags)do check(not tagVisible(tag),'growth tag is hidden or removed')end
end
local function footer(gui)
 local item=gui:FindFirstChild(UIContract.footer,true)
 if item then check(item:IsA('TextLabel'),'growth footer is a bounded text label')end
 return item
end
local function requireFooter(gui,stage,xp)
 local f=footer(gui)
 check(f~=nil,'production BattleGrowthFooter is missing')
 local count=0
 for _,object in ipairs(gui:GetDescendants())do if object.Name==UIContract.footer then count+=1 end end
 equal(count,1,'one footer only')
 check(f.Visible,'active footer is visible')
 check(f.Parent==gui and gui:IsA('ScreenGui') and gui.Enabled==true,
  'direct footer and its actual ScreenGui are visible')
 check(gui.Parent==playerGui and playerGui.Parent==player,'footer uses the current client GUI ancestry')
 check(f.Text==string.format('覚醒B%d XP%d/80',stage,xp),'footer uses truthful B/XP label')
 local rect=UIAudit.rect(f);local status=UIAudit.rect(gui:FindFirstChild('CompactStatus'))
 equal(rect.y,43,'footer begins at y43')
 equal(rect.h,12,'footer stays 12 high')
 check(rect.x>=status.x and rect.x+rect.w<=status.x+status.w,'footer remains within existing status width')
 check(not UIAudit.intersects(rect,status),'footer does not consume existing HP/Buffs area')
 check(not UIAudit.intersects(rect,UIAudit.rect(gui:FindFirstChild('MusouCharge'))),'footer avoids existing Musou bar')
 UIExpect.everFooter=true
 return f
end
local function freshMap(mode)
 return {version=1,kind='MAP_INTEL',mode=mode,x=0,z=0,layer='LAND',
  markers={},explored={},cell=40,statuses={'燃焼','鈍足'},defense={phase='NONE',remaining=0}}
end
local function realReady(role)
 local before=#capturedSessions
 advanceTo(now+.5)
 trigger(player,scenes:FindFirstChild('ROLE_'..role),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 advanceTo(now+12.01)
 equal(#capturedSessions,before+1,'real Host produces one session after original READY')
 local session=capturedSessions[#capturedSessions]
 check(session.rules.phase=='ACTIVE' and session.isCurrentHuman(player),'genuine human active session')
 check(player:GetAttribute('EGGRUMBLE_Role')==role,'actual Combat equipped selected role '..role)
 outsideField(session)
 UIAudit.deliverMap(freshMap('TEAM'));UIAudit.frame()
 return session
end
local function genuineKO(session)
 local neutral=spawnCurrentNeutral(session)
 local h=neutral:FindFirstChildOfClass('Humanoid')
 local before=session.swarm.kills['42'] or 0
 local curse=player:GetAttribute('EGGRUMBLE_Role')=='ZOMBIE'
 for hit=1,16 do
  local target=neutral.PrimaryPart.Position
  if curse then
   -- Current curse hits are capped at 7/11 and can convert nearby targets.
   -- A real clear 34-stud approach is inside existing Swarm reach (36), outside
   -- conversion reach (32). Repeat actual bounded damage; never fake HP/role.
   local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude
   params.FilterDescendantsInstances={character,neutral};params.RespectCanCollide=true
   local chosen=nil
   for _,offset in ipairs({Vector3.new(0,1,-34),Vector3.new(0,1,34),Vector3.new(-34,1,0),Vector3.new(34,1,0)})do
    local at=target+offset
    if workspace:Raycast(at+Vector3.new(0,1,0),target-at,params)==nil then chosen=CFrame.new(at,target);break end
   end
   check(chosen~=nil,'bounded clear source-admitted curse approach exists')
   rootPart.CFrame=chosen
  else rootPart.CFrame=clearNeutralApproach(neutral,target)end
  equal(session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE'),1,'one genuine neutral hit')
  if h.Health<=0 then break end
  check(curse,'non-curse fixture expects the original one-hit target')
  advanceTo(now+dependencies.EGGRUMBLE_CombatBalance.skill('ZOMBIE','A').cooldown+.01)
 end
 equal(h.Health,0,'full actual damage path causes actual fixture Humanoid death')
 equal(session.swarm.kills['42'],before+1,'full actual KoFence/credit produces one genuine KO')
 outsideField(session);advanceTo(now+.26);UIAudit.frame()
 return before+1
end
local function snapshotExpectation(label,session,stage,xp,ko,active)
 expectation(label..'_PUBLISHED',function()
  equal(player:GetAttribute(UIContract.stage),stage,'actual Swarm BattleStage publication')
  equal(player:GetAttribute(UIContract.xp),xp,'actual Swarm BattleXP publication')
  check(player:GetAttribute(UIContract.active)==active,'actual Swarm GrowthActive publication')
 end)
 expectation(label..'_TAG',function()requireTag(player,stage,ko)end)
 local gui=playerGui:FindFirstChild('EGGRUMBLE_CombatHudIntel')
 expectation(label..'_FOOTER',function()requireFooter(gui,stage,xp)end)
 observeUI(label,'ledger='..tostring(session.swarm.kills['42'] or 0)
  ..';BattleLevel='..tostring(player:GetAttribute('EGGRUMBLE_BattleLevel'))
  ..';B='..tostring(player:GetAttribute(UIContract.stage))..';XP='..tostring(player:GetAttribute(UIContract.xp))
  ..';GrowthActive='..tostring(player:GetAttribute(UIContract.active)))
end
local function replaceCharacter(session,label,deferred,includeHead,hadTag)
 local old=character
 local oldConnections=heroOwned(old)
 local new=Instance.new('Model');new.Name='UIAcceptanceAvatar';new.Parent=workspace
 local hum=Instance.new('Humanoid');hum.WalkSpeed=20;hum.Parent=new
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=new
 local spawn=scenes:FindFirstChild('GQ646_LOBBY_NEUTRAL_SPAWN')
 check(spawn~=nil,'actual original lobby SpawnLocation exists')
 root.CFrame=CFrame.new(spawn.Position+Vector3.new(0,3,0))
 local torso=Instance.new('Part');torso.Name='UpperTorso';torso.CanCollide=false;torso.Parent=new
 if includeHead then local head=Instance.new('Part');head.Name='Head';head.CanCollide=false;head.Parent=new end
 new.PrimaryPart=root
 local function transition()
  player.CharacterRemoving:Fire(old)
  player.Character=new;character=new;humanoid=hum;rootPart=root
  player.CharacterAdded:Fire(new)
  old:Destroy()
 end
 local started=now
 if deferred then UIAcceptanceEngine.atomic(transition) else transition()end
 local arrival=session.castleLocations['42']+Vector3.new(0,7,-45)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 for _,elapsed in ipairs({0,.36,.79})do
  advanceTo(started+elapsed);UIAudit.frame()
  check(player.Character==new and (root.Position-arrival).Magnitude>1,'new avatar has not physically returned to castle yet')
  local delta=root.Position-floor.Position
  check(math.abs(delta.X)>floor.Size.X*.5 or math.abs(delta.Z)>floor.Size.Z*.5,'new avatar is outside the current arena before Host return')
  expectation(label..'_PRE_RETURN_'..math.floor(elapsed*1000)..'MS_TAG_HIDDEN',function()hiddenTag(player)end,hadTag)
 end
 observeUI(label..'_PRE_RETURN','observed0/360/790ms;newAvatarOutsideArena=true;actualHostReturnNotYet=true;hasHead='..tostring(includeHead))
 advanceTo(started+.81);UIAudit.frame()
 check(player.Character==new and (root.Position-arrival).Magnitude<.001,'actual unmodified Host returned this avatar to its castle')
 expectation(label..'_RETIRED_CHARACTER_CONNECTIONS',function()
  requireDisconnected(oldConnections,'retired character/descendant signal')
 end,hadTag or #oldConnections>0)
 observeUI(label..'_HOST_RETURN','elapsed='..tostring(now-started)..';physicalArrivalError='..(root.Position-arrival).Magnitude)
 return old,new
end

-- These probes use the same full31 execution. Missing growth UI gates only its
-- own observation; real combat and role callbacks remain reachable on H93.
local function naturalNinjaFollowup(session,hadTag)
 local deadline,castAt,avatar,head,heroBefore,hudBefore,heroCast,hudCast
 local monitor=nil;local changes={};local attempts=0
 local castOK,castDetail=pcall(function()
  advanceTo(now+dependencies.EGGRUMBLE_CombatBalance.skill('NINJA','B').cooldown+.01)
  avatar=player.Character;head=avatar and avatar:FindFirstChild('Head')
  check(avatar and head and humanoid.Health>0 and session.isCurrentHuman(player)
   and session.rules.phase=='ACTIVE' and player:GetAttribute('EGGRUMBLE_Role')=='NINJA',
   'second real NINJA B uses the current living ACTIVE human')
  heroBefore=liveSource('HeroSilhouetteArt');hudBefore=liveSource('HudIntelRuntime')
  monitor=player:GetAttributeChangedSignal('EGGRUMBLE_StealthUntil'):Connect(function()
   table.insert(changes,{at=now,value=player:GetAttribute('EGGRUMBLE_StealthUntil')})
  end)
  local floor=session.world:FindFirstChild('TacticalBattlefield')
  for index,offset in ipairs({{0,0},{0,-80},{-120,0},{120,0}})do
   attempts=index
   if index>1 then advanceTo(now+dependencies.EGGRUMBLE_CombatBalance.skill('NINJA','B').cooldown+.01)end
   local at=floor.Position+Vector3.new(offset[1],floor.Size.Y*.5+3,offset[2])
   rootPart.CFrame=CFrame.new(at,at+Vector3.new(0,0,-1))
   castAt=now;activate(player,'B')
   deadline=player:GetAttribute('EGGRUMBLE_StealthUntil')
   if type(deadline)=='number' and deadline>now and deadline<math.huge then break end
  end
  check(type(deadline)=='number' and deadline>now and deadline<math.huge,'real second B publishes a finite deadline')
  equal(deadline-castAt,3,'original three-second stealth duration')
  equal(#changes,1,'exactly one actual B attribute publication')
  equal(changes[1].value,deadline,'actual observed second B deadline')
  heroCast=liveSource('HeroSilhouetteArt');hudCast=liveSource('HudIntelRuntime')
 end)
 expectation('UI_FOLLOWUP_NINJA_SECOND_REAL_B',function()check(castOK,tostring(castDetail))end)
 expectation('UI_FOLLOWUP_NINJA_SECOND_CAST_HIDDEN',function()hiddenTag(player)end,castOK and hadTag)
 local beforeOK,beforeDetail=false,'second B was not admitted'
 if castOK then
  beforeOK,beforeDetail=pcall(function()
   advanceTo(deadline-.001)
   check(player.Character==avatar and avatar:FindFirstChild('Head')==head
    and humanoid.Health>0 and session.isCurrentHuman(player),'same living avatar before natural deadline')
   equal(player:GetAttribute('EGGRUMBLE_StealthUntil'),deadline,'deadline unchanged before expiry')
   equal(#changes,1,'no attribute event before natural expiry')
  end)
 end
 expectation('UI_FOLLOWUP_NINJA_PRE_DEADLINE_HIDDEN',function()
  check(beforeOK,tostring(beforeDetail));hiddenTag(player)
 end,castOK and hadTag)
 local afterOK,afterDetail=false,'second B was not admitted'
 if castOK then
  afterOK,afterDetail=pcall(function()
   advanceTo(deadline+.02)
   check(player.Character==avatar and avatar:FindFirstChild('Head')==head
    and humanoid.Health>0 and session.isCurrentHuman(player),'same living avatar after natural deadline')
  end)
 end
 expectation('UI_FOLLOWUP_NINJA_NATURAL_DEADLINE_TAG',function()
  check(afterOK,tostring(afterDetail));requireTag(player,3,4)
 end,castOK and hadTag)
 expectation('UI_FOLLOWUP_NINJA_DEADLINE_VALUE_UNCHANGED',function()
  check(beforeOK,tostring(beforeDetail));check(afterOK,tostring(afterDetail))
  equal(player:GetAttribute('EGGRUMBLE_StealthUntil'),deadline,'expired numeric deadline is not rewritten')
  equal(#changes,1,'only the real B publication changed StealthUntil')
  equal(changes[1].value,deadline,'the original deadline value survives')
 end,castOK)
 if monitor then monitor:Disconnect()end
 expectation('UI_FOLLOWUP_NINJA_CONNECTIONS_BOUNDED',function()
  equal(heroCast,heroBefore,'second cast adds no live Hero connection')
  equal(hudCast,hudBefore,'second cast adds no live HUD connection')
  equal(liveSource('HeroSilhouetteArt'),heroBefore,'natural expiry adds no live Hero connection')
  equal(liveSource('HudIntelRuntime'),hudBefore,'natural expiry adds no live HUD connection')
  check(monitor and not monitor.Connected,'test-only attribute observer is disconnected')
  requireHudConnectionContract();requireNoExtraFramePolling()
 end,castOK)
 observeUI('FOLLOWUP_NINJA_NATURAL','secondRealB='..tostring(castOK)..';attempts='..attempts
  ..';deadline='..tostring(deadline)..';attributeEvents='..#changes
  ..';frameDrivesAfterCast=0;fixtureStealthWrites=0')
end

local function rolePendingFollowup()
 local audit={tasks={},errors={},origin=nil,callLines={}}
 local originalDefer,originalDelay=task.defer,task.delay
 local span=fullSourceRanges.HeroSilhouetteArt
 local auxiliary={};local live,new=nil,nil
 local liveArt,newArt,liveOwned,newOwned
 local liveErrors,newErrors={},{}
 local function remember(errors,fn)
  local ok,detail=pcall(fn);if not ok then table.insert(errors,tostring(detail))end
 end
 local function observeTask(kind,line,fn,args,beforeSerial,at,seconds,returns)
  if not audit.origin or line<span.first or line>span.last then return end
  local callbackLine=debug.info(fn,'l')
  check(callbackLine>=span.first and callbackLine<=span.last,'original callback belongs to the full Hero body')
  if audit.callLines[kind]then check(audit.callLines[kind]==line,'same actual role-task callsite across input origins')
  else audit.callLines[kind]=line end
  local appended={}
  for _,entry in ipairs(pending)do if entry.serial>beforeSerial then table.insert(appended,entry)end end
  equal(#appended,1,'pass-through leaves exactly the original scheduler entry')
  local entry=appended[1]
  equal(entry.at,at+seconds,'original due time is unchanged')
  equal(args.n,0,'original role closure takes no arguments')
  equal(entry.args.n,args.n,'original argument count is unchanged')
  for i=1,args.n do check(entry.args[i]==args[i],'original argument identity is unchanged')end
  equal(returns.n,0,'frozen original task return count is unchanged')
  table.insert(audit.tasks,{kind=kind,line=line,fn=fn,origin=audit.origin,
   thread=entry.thread,serial=entry.serial,at=entry.at,scheduledAt=at})
  observeUI('FOLLOWUP_ROLE_TASK_SCHEDULED','origin='..audit.origin..';kind='..kind
   ..';rawLine='..(line-span.first+1)..';serial='..entry.serial..';due='..entry.at
   ..';callbackWrapped=false;args=0;returns=0')
 end
 task.defer=function(fn,...)
  local line=debug.info(2,'l');local args=table.pack(...);local beforeSerial=serial;local at=now
  local returns=table.pack(originalDefer(fn,table.unpack(args,1,args.n)))
  remember(audit.errors,function()observeTask('defer',line,fn,args,beforeSerial,at,0,returns)end)
  return table.unpack(returns,1,returns.n)
 end
 task.delay=function(seconds,fn,...)
  local line=debug.info(2,'l');local args=table.pack(...);local beforeSerial=serial;local at=now
  local returns=table.pack(originalDelay(seconds,fn,table.unpack(args,1,args.n)))
  remember(audit.errors,function()observeTask('delay',line,fn,args,beforeSerial,at,seconds,returns)end)
  return table.unpack(returns,1,returns.n)
 end
 local function originInput(name,fn)
  check(audit.origin==nil,'non-nested explicit role input')
  audit.origin=name;local ok,detail=pcall(fn);audit.origin=nil
  if not ok then error(detail,0)end
 end
 local function pairFor(origin,at)
  local pair={};local count=0
  for _,entry in ipairs(audit.tasks)do if entry.origin==origin then
   check(pair[entry.kind]==nil,'one original task of each kind per origin')
   pair[entry.kind]=entry;count+=1
  end end
  equal(count,2,'two original role tasks per origin')
  equal(pair.defer.scheduledAt,at,'defer schedule instant')
  equal(pair.delay.scheduledAt,at,'delay schedule instant')
  equal(pair.defer.at,at,'original defer deadline')
  equal(pair.delay.at,at+.35,'original .35 deadline')
  check(pair.defer.fn~=pair.delay.fn,'distinct original source closures')
  return pair
 end
 local function taskState(entry,dead)
  check(coroutine.status(entry.thread)==(if dead then 'dead' else 'suspended'),'original thread delivery state')
  local found=0
  for _,row in ipairs(pending)do if row.thread==entry.thread then found+=1 end end
  equal(found,if dead then 0 else 1,'one pending entry before delivery, none after')
  if dead then entry.deadObserved=true else entry.pendingObserved=true end
 end
 local function makeActor(name,id)
  local actor=Instance.new('Player');actor.Name=name;actor.UserId=id;actor.Parent=Players
  local gui=Instance.new('PlayerGui');gui.Parent=actor
  local backpack=Instance.new('Backpack');backpack.Parent=actor
  local row={actor=actor,removed=false};table.insert(auxiliary,row)
  return row
 end
 local function makeAvatar(name,torso)
  local avatar=Instance.new('Model');avatar.Name=name;avatar.Parent=workspace
  local hum=Instance.new('Humanoid');hum.Health=100;hum.MaxHealth=100;hum.Parent=avatar
  local root=Instance.new('Part');root.Name='HumanoidRootPart';root.CFrame=CFrame.new(0,5,0);root.Parent=avatar
  local head=Instance.new('Part');head.Name='Head';head.CFrame=CFrame.new(0,7,0);head.Parent=avatar
  if torso then
   local part=Instance.new('Part');part.Name='UpperTorso';part.CFrame=CFrame.new(0,6,0);part.Parent=avatar
  end
  avatar.PrimaryPart=root;return avatar
 end
 local function addActor(row,origin)
  table.insert(currentPlayers,row.actor)
  originInput(origin,function()Players.PlayerAdded:Fire(row.actor)end)
  check(Players:GetPlayerByUserId(row.actor.UserId)==row.actor,'actual current lookup is the concrete actor')
 end
 local function choose(row,role)
  trigger(row.actor,scenes:FindFirstChild('ROLE_'..role),'職業選択')
  check(row.actor:GetAttribute('EGGRUMBLE_SelectedRole')==role,'real Host role prompt selected the role')
  check(row.actor:GetAttribute('EGGRUMBLE_Role')==nil,'lobby uses SelectedRole fallback')
 end
 local function removeActor(row,retainParent)
  Players.PlayerRemoving:Fire(row.actor);row.removed=true
  for i=#currentPlayers,1,-1 do if currentPlayers[i]==row.actor then table.remove(currentPlayers,i)end end
  if not retainParent then row.actor.Parent=nil end
 end
 local function art(row)return row.avatar:FindFirstChild('EGGRUMBLE_RoleVisuals')end
 local function inspectArt(row,role)
  local folder=art(row);check(folder and folder:IsA('Folder'),'actual source-created role Folder')
  check(folder:GetAttribute('EGGRUMBLE_VisualRole')==role,'exact source visual role')
  local anchor=row.avatar:FindFirstChild('UpperTorso') or row.avatar:FindFirstChild('Torso')
  check(anchor and folder:GetAttribute('EGGRUMBLE_VisualAnchor')==anchor.Name,'current concrete art anchor')
  local parts,welds={},{};local partCount,weldCount=0,0
  for _,object in ipairs(folder:GetDescendants())do
   if object:IsA('BasePart')then
    check(parts[object.Name]==nil,'unique cosmetic Part name');parts[object.Name]=object;partCount+=1
    check(object.Parent==folder and object.Anchored==false and object.Massless==true,'live Part attachment flags')
    check(object.CanCollide==false and object.CanQuery==false and object.CanTouch==false,'cosmetic collision flags')
   elseif object:IsA('WeldConstraint')then
    check(object.Parent and object.Parent:IsA('BasePart'),'Weld parent is the cosmetic Part')
    check(object.Part0==anchor and object.Part1==object.Parent,'live Weld connects the concrete Torso and Part')
    check(welds[object.Parent.Name]==nil,'one Weld per Part');welds[object.Parent.Name]=object;weldCount+=1
   else error('unexpected role decoration descendant '..object.ClassName,0)end
  end
  equal(partCount,8,'bounded MAGE/WARRIOR eight-part silhouette')
  equal(weldCount,8,'one live Weld per Part');check(partCount<=13,'original 13-part cap')
  return {folder=folder,parts=parts,welds=welds,anchor=anchor}
 end
 local function unchanged(row,role,before,owned)
  local after=inspectArt(row,role)
  check(after.folder==before.folder and after.anchor==before.anchor,'Folder and anchor identities survive')
  for name,object in pairs(before.parts)do check(after.parts[name]==object,'Part identity survives '..name)end
  for name,object in pairs(before.welds)do check(after.welds[name]==object,'Weld identity survives '..name)end
  local current=heroPlayerOwned(row.actor,row.avatar)
  equal(#current,#owned,'live actor connection count is unchanged')
  local currentSet={};for _,entry in ipairs(current)do currentSet[entry]=true end
  for _,entry in ipairs(owned)do check(entry.connected and currentSet[entry],'same concrete live connection survives')end
 end
 local function clearOld(row,label)
  local folder=art(row)
  if folder then folder:Destroy()end
  check(art(row)==nil,'explicit test-only clear isolates the next reserved task')
  observeUI('FOLLOWUP_TEST_ONLY_OLD_VISUAL_CLEAR','boundary='..label..';productCleanupClaim=false')
 end
 local function checkLive()
  if liveArt then remember(liveErrors,function()unchanged(live,'MAGE',liveArt,liveOwned)end)end
 end
 local liveOK,liveDetail=pcall(function()
  local at=now
  live=makeActor('UIFollowupLiveLateTorso',7317);addActor(live,'LIVE_NO_AVATAR')
  live.avatar=makeAvatar('UIFollowupLiveAvatar',false);live.actor.Character=live.avatar
  originInput('LIVE_CHARACTER_ADDED',function()live.actor.CharacterAdded:Fire(live.avatar)end)
  choose(live,'MAGE')
  check(art(live)==nil,'no Torso means no inline art')
  local pair=pairFor('LIVE_CHARACTER_ADDED',at)
  taskState(pair.defer,false);taskState(pair.delay,false)
  advanceTo(at);taskState(pair.defer,true);taskState(pair.delay,false)
  check(art(live)==nil,'original defer before Torso creates no art')
  advanceTo(at+.20)
  local torso=Instance.new('Part');torso.Name='UpperTorso';torso.CFrame=CFrame.new(0,6,0);torso.Parent=live.avatar
  check(art(live)==nil,'Torso insertion alone does not decorate')
  advanceTo(at+.349);taskState(pair.delay,false)
  check(art(live)==nil,'reserved .35 callback is not delivered early')
  advanceTo(pair.delay.at);taskState(pair.delay,true)
  liveArt=inspectArt(live,'MAGE');liveOwned=heroPlayerOwned(live.actor,live.avatar)
 end)
 expectation('UI_FOLLOWUP_LIVE_LATE_TORSO',function()check(liveOK,tostring(liveDetail))end)

 local nilActor,nilPair,nilOwned,nilAt,nilImmediately,nilAfterDefer,nilAfterDelay
 local nilOK,nilDetail=pcall(function()
  nilAt=now;nilActor=makeActor('UIFollowupRetiredNil',7326);addActor(nilActor,'NIL_NO_AVATAR')
  nilActor.avatar=makeAvatar('UIFollowupRetiredNilAvatar',true);nilActor.actor.Character=nilActor.avatar
  originInput('NIL_CHARACTER_ADDED',function()nilActor.actor.CharacterAdded:Fire(nilActor.avatar)end)
  choose(nilActor,'WARRIOR');inspectArt(nilActor,'WARRIOR')
  nilPair=pairFor('NIL_CHARACTER_ADDED',nilAt)
  taskState(nilPair.defer,false);taskState(nilPair.delay,false)
  nilOwned=heroPlayerOwned(nilActor.actor,nilActor.avatar)
  removeActor(nilActor,false);nilImmediately=#heroPlayerOwned(nilActor.actor,nilActor.avatar)
  clearOld(nilActor,'nil_before_defer')
 end)
 local nilDeferOK,nilDeferDetail=false,'nil actor setup failed'
 if nilOK then
  nilDeferOK,nilDeferDetail=pcall(function()
   advanceTo(nilAt);taskState(nilPair.defer,true);taskState(nilPair.delay,false)
   nilAfterDefer=#heroPlayerOwned(nilActor.actor,nilActor.avatar)
  end)
 end
 expectation('UI_FOLLOWUP_RETIRED_NIL_DEFER',function()
  check(nilOK,tostring(nilDetail));check(nilDeferOK,tostring(nilDeferDetail))
  check(nilActor.actor.Parent==nil and art(nilActor)==nil,'retired Parent-nil defer cannot redraw old art')
 end)
 local nilDelayOK,nilDelayDetail=false,'nil actor setup failed'
 if nilOK then
  nilDelayOK,nilDelayDetail=pcall(function()
   clearOld(nilActor,'nil_between_defer_and_delay')
   advanceTo(nilPair.delay.at-.001);taskState(nilPair.delay,false)
   check(art(nilActor)==nil,'nil old avatar remains clear before original .35')
   advanceTo(nilPair.delay.at);taskState(nilPair.delay,true)
   nilAfterDelay=#heroPlayerOwned(nilActor.actor,nilActor.avatar)
  end)
 end
 expectation('UI_FOLLOWUP_RETIRED_NIL_DELAY',function()
  check(nilDelayOK,tostring(nilDelayDetail))
  check(nilActor.actor.Parent==nil and art(nilActor)==nil,'retired Parent-nil .35 cannot redraw old art')
 end,nilOK)
 expectation('UI_FOLLOWUP_RETIRED_NIL_OWNERS_ZERO',function()
  equal(nilImmediately,0,'nil retired ownership is zero immediately after Removing')
  equal(nilAfterDefer,0,'nil retired ownership stays zero after defer')
  equal(nilAfterDelay,0,'nil retired ownership stays zero after .35')
  requireDisconnected(nilOwned,'nil retired original Hero subscriptions')
 end,nilOK)
 checkLive()

 local retired,pair,newPair,retiredAt,retiredOwned,retiredImmediately,retiredAfterDefer,retiredAfterDelay
 local retainedOK,retainedDetail=pcall(function()
  retiredAt=now;retired=makeActor('UIFollowupRetiredRetained',7327)
  retired.avatar=makeAvatar('UIFollowupRetiredRetainedAvatar',true);retired.actor.Character=retired.avatar
  addActor(retired,'RETAINED_EXISTING_AVATAR');choose(retired,'WARRIOR');inspectArt(retired,'WARRIOR')
  pair=pairFor('RETAINED_EXISTING_AVATAR',retiredAt)
  taskState(pair.defer,false);taskState(pair.delay,false)
  retiredOwned=heroPlayerOwned(retired.actor,retired.avatar)
  removeActor(retired,true);retiredImmediately=#heroPlayerOwned(retired.actor,retired.avatar)
  clearOld(retired,'retained_before_defer')
  new=makeActor('UIFollowupNewSameUIDMage',7327)
  new.avatar=makeAvatar('UIFollowupNewSameUIDMageAvatar',true);new.actor.Character=new.avatar
  check(retired.actor~=new.actor and retired.avatar~=new.avatar,'sameUID has distinct concrete Players and avatars')
  addActor(new,'NEW_EXISTING_AVATAR');choose(new,'MAGE')
  newPair=pairFor('NEW_EXISTING_AVATAR',retiredAt)
  taskState(newPair.defer,false);taskState(newPair.delay,false)
  newArt=inspectArt(new,'MAGE');newOwned=heroPlayerOwned(new.actor,new.avatar)
  check(retired.actor.Parent==Players and retired.actor.Character==retired.avatar
   and retired.avatar.Parent==workspace,'explicit retired old Parent/Character retention')
 end)
 local function preserveNew()
  if newArt then remember(newErrors,function()
   check(retired.actor~=new.actor and retired.avatar~=new.avatar,'old/new identities remain distinct')
   check(Players:GetPlayerByUserId(7327)==new.actor,'actual lookup stays on the new sameUID Player')
   unchanged(new,'MAGE',newArt,newOwned)
  end)end
  checkLive()
 end
 local retainedDeferOK,retainedDeferDetail=false,'retained actor setup failed'
 if retainedOK then
  retainedDeferOK,retainedDeferDetail=pcall(function()
   advanceTo(retiredAt);taskState(pair.defer,true);taskState(newPair.defer,true)
   taskState(pair.delay,false);taskState(newPair.delay,false)
   retiredAfterDefer=#heroPlayerOwned(retired.actor,retired.avatar)
  end)
  preserveNew()
 end
 expectation('UI_FOLLOWUP_RETIRED_RETAINED_DEFER',function()
  check(retainedOK,tostring(retainedDetail));check(retainedDeferOK,tostring(retainedDeferDetail))
  check(retired.actor.Parent==Players and retired.actor.Character==retired.avatar
   and art(retired)==nil,'retired retained-Parent defer cannot redraw its old avatar')
 end)
 local retainedDelayOK,retainedDelayDetail=false,'retained actor setup failed'
 if retainedOK then
  retainedDelayOK,retainedDelayDetail=pcall(function()
   clearOld(retired,'retained_between_defer_and_delay')
   advanceTo(pair.delay.at-.001);taskState(pair.delay,false);taskState(newPair.delay,false)
   check(art(retired)==nil,'retained old avatar remains clear before original .35')
   preserveNew()
   advanceTo(pair.delay.at);taskState(pair.delay,true);taskState(newPair.delay,true)
   retiredAfterDelay=#heroPlayerOwned(retired.actor,retired.avatar)
  end)
  preserveNew()
 end
 expectation('UI_FOLLOWUP_RETIRED_RETAINED_DELAY',function()
  check(retainedDelayOK,tostring(retainedDelayDetail))
  check(retired.actor.Parent==Players and retired.actor.Character==retired.avatar
   and art(retired)==nil,'retired retained-Parent .35 cannot redraw its old avatar')
 end,retainedOK)
 expectation('UI_FOLLOWUP_RETIRED_RETAINED_OWNERS_ZERO',function()
  equal(retiredImmediately,0,'retained retired ownership is zero immediately after Removing')
  equal(retiredAfterDefer,0,'retained retired ownership stays zero after defer')
  equal(retiredAfterDelay,0,'retained retired ownership stays zero after .35')
  requireDisconnected(retiredOwned,'retained retired original Hero subscriptions')
 end,retainedOK)
 expectation('UI_FOLLOWUP_SAME_UID_NEW_MAGE_IDENTITIES',function()
  equal(#newErrors,0,'new MAGE art/connections must survive every old/new delivery: '..table.concat(newErrors,' | '))
  check(retainedDeferOK and retainedDelayOK,'both old and new original task pairs were delivered')
  check(Players:GetPlayerByUserId(7327)==new.actor,'lookup still names the new concrete Player')
  unchanged(new,'MAGE',newArt,newOwned)
 end,retainedOK)
 expectation('UI_FOLLOWUP_LIVE_CURRENT_IDENTITIES',function()
  equal(#liveErrors,0,'live late-Torso MAGE survives both retired inputs: '..table.concat(liveErrors,' | '))
  check(nilDeferOK and nilDelayOK and retainedDeferOK and retainedDelayOK,'both retired task pairs were delivered')
  check(Players:GetPlayerByUserId(7317)==live.actor,'live current lookup is preserved')
  unchanged(live,'MAGE',liveArt,liveOwned)
 end,liveOK)
 task.defer,task.delay=originalDefer,originalDelay
 expectation('UI_FOLLOWUP_ROLE_TASK_DELIVERY_BOUNDARY',function()
  check(task.defer==originalDefer and task.delay==originalDelay,'task APIs are restored')
  equal(#audit.errors,0,'pass-through observations succeeded: '..table.concat(audit.errors,' | '))
  equal(#audit.tasks,8,'exactly four origins times the original defer/.35 pair')
  local threads,serials={},{}
  for _,entry in ipairs(audit.tasks)do
   check(not threads[entry.thread] and not serials[entry.serial],'all original threads/serials are distinct')
   threads[entry.thread]=true;serials[entry.serial]=true
   check(entry.pendingObserved and entry.deadObserved,'each original thread was pending and then genuinely delivered')
   taskState(entry,true)
  end
  requireNoExtraFramePolling()
 end)
 local cleanupOK,cleanupDetail=pcall(function()
  for _,row in ipairs(auxiliary)do
   if not row.removed then removeActor(row,false)else row.actor.Parent=nil end
  end
 end)
 expectation('UI_FOLLOWUP_AUXILIARY_HERO_CLEANUP',function()
  check(cleanupOK,tostring(cleanupDetail))
  for _,row in ipairs(auxiliary)do
   equal(#heroPlayerOwned(row.actor,row.avatar),0,'every auxiliary Hero-owned connection retires without destroying the Player')
  end
  check(audit.origin==nil and task.defer==originalDefer and task.delay==originalDelay,'no task observer remains')
  check(UIAcceptanceEngine.holdDepth==0 and #UIAcceptanceEngine.queue==0,'no deferred hold/queue remains')
 end)
end


local ok,result=pcall(function()
 advanceTo(now);sharedRequires()
 equal(#UIAudit.renderCallbacks,1,'one existing HUD frame callback before acceptance run')
 local gui=playerGui:FindFirstChild('EGGRUMBLE_CombatHudIntel')
 local status=gui:FindFirstChild('CompactStatus');local hp=status:FindFirstChild('HP');local buffs=status:FindFirstChild('Buffs')
 local map=gui:FindFirstChild('FilteredMinimap');local drawer=gui:FindFirstChild('ChoiceDrawer')
 local toast=gui:FindFirstChild('LegacyExploreDiscoveryToast')
 UIAudit.frame();check(not gui.Enabled,'original lobby gating works')
 check(hp.Text=='HP 100/100' and buffs.Text=='属性 -- ','literal H93 lobby HP/status oracle')
 requireHudConnectionContract();requireNoExtraFramePolling();observeConnections('LOBBY')

 exactNumberToken('この試合B3 中立KO4','中立KO',4,'token fixture positive control')
 for _,row in ipairs({{'中立KO40','中立KO',4},{'B30','B',3},{'KO4.5','KO',4},
  {'KO4 KO4','KO',4},{'wrongB3','B',3}})do
  local accepted=pcall(function()exactNumberToken(row[1],row[2],row[3],'negative token control')end)
  check(not accepted,'numeric-token oracle must reject '..row[1])
 end
 pass('UI_INTEGER_TOKEN_CONTROL','whole integer tokens reject KO40 for KO4, B30 for B3, decimals, duplicates and embedded identifiers')

 -- Sanity checks for the explicitly documented engine queue model only.
 local probe=Instance.new('Folder');local delivered=0
 local c=probe:GetAttributeChangedSignal('UIAuditProbe'):Connect(function()delivered+=1 end)
 UIAcceptanceEngine.hold();probe:SetAttribute('UIAuditProbe',1);c:Disconnect();UIAcceptanceEngine.release()
 equal(delivered,0,'explicit Disconnect drops queued signal callback in fixture')
 probe.Destroying:Connect(function()check(probe.Parent==nil,'destroyed object observed at deferred resumption');delivered+=1 end)
 UIAcceptanceEngine.hold();probe:Destroy();UIAcceptanceEngine.release()
 equal(delivered,1,'automatic destruction retains queued Destroying callback in fixture')
 pass('UI_DEFERRED_BOUNDARY_CONTROL','selected FIFO queue model checked; complete Roblox scheduler remains NOT_TESTED')

 local roles={{'WARRIOR','武神'},{'MAGE','魔法使い'},{'NINJA','暗殺者'},
  {'TRAPPER','超能力者'},{'BUILDER','マッドサイエンティスト'},{'BEAST','魔獣使い'},{'ZOMBIE','呪術師'}}
 local expectedActiveHero=nil
 for roleIndex,row in ipairs(roles)do
  local role=row[1]
  check(dependencies.EGGRUMBLE_SevenRoleCombat.info(role).name==row[2],'real selected role display name')
  local session=realReady(role)
  local art=character:FindFirstChild('EGGRUMBLE_RoleVisuals')
  check(art and art:GetAttribute('EGGRUMBLE_VisualRole')==role,'actual role art follows actual equipped role')
  snapshotExpectation(role..'_START',session,1,0,0,true)
  local koCount=0
  for _=1,(if roleIndex==1 then 8 else 4)do
   koCount=genuineKO(session)
   if koCount==1 then snapshotExpectation(role..'_KO1',session,2,10,1,true)end
   if koCount==4 then snapshotExpectation(role..'_KO4',session,3,40,4,true)end
  end
  local xp=if roleIndex==1 then 80 else 40
  if roleIndex==1 then snapshotExpectation(role..'_KO8',session,3,80,8,true)end
  equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),1,'existing 25-KO level is preserved, not repurposed as B')
  check(character:FindFirstChild('EGGRUMBLE_RoleVisuals')==art,'KO updates preserve original body art instance')
  local hadTag=#findTags(player)>0
  local hadFooter=footer(gui)~=nil
  local activeHero=observeConnections(role..'_ACTIVE')
  if expectedActiveHero==nil then expectedActiveHero=activeHero end
  expectation(role..'_ACTIVE_HERO_CONNECTIONS_STABLE',function()
   equal(activeHero,expectedActiveHero,'same complete current avatar does not accumulate live Hero subscriptions between rounds')
  end,hadTag)
  requireHudConnectionContract();requireNoExtraFramePolling()
  local held=parkOldSwarm(session)

   if roleIndex==1 then
    expectation('UI_FOLLOWUP_TAG_EFFECTIVE_ADORNEE',function()requireTag(player,3,8)end,hadTag)
    expectation('UI_FOLLOWUP_FOOTER_VISIBLE_ANCESTRY',function()requireFooter(gui,3,80)end,hadFooter)
    -- An explicit existing-attribute ordering input models Role disappearing
   -- while the current match's growth publication has not yet changed. The
   -- role was genuinely selected/equipped above; no new B attribute is forged.
   player:SetAttribute('EGGRUMBLE_Role',nil)
   expectation('NO_ACTUAL_ROLE_TAG_HIDDEN',function()hiddenTag(player)end,hadTag)
   player:SetAttribute('EGGRUMBLE_Role',role)
   expectation('ACTUAL_ROLE_RESTORES_TAG',function()requireTag(player,3,8)end,hadTag)
   -- A non-player visual subject is an explicit engine model input. Original
   -- Hero bot decoration may run, but no human B tag may be created for it.
   local nonhuman=Instance.new('Model');nonhuman.Name='AI_Actor_UIAcceptance'
   nonhuman:SetAttribute('EGGRUMBLE_BotId','UI_ACCEPTANCE_NONPLAYER')
   nonhuman.Parent=workspace
   local nonhumanRoot=Instance.new('Part');nonhumanRoot.Name='HumanoidRootPart'
   nonhumanRoot.Color=Color3.fromRGB(120,60,60);nonhumanRoot.CanCollide=false;nonhumanRoot.Parent=nonhuman
   UIAudit.rig(nonhuman);advanceTo(now)
   expectation('NONHUMAN_NEVER_GROWTH_TAG',function()
    check(nonhuman:FindFirstChild(UIContract.tag,true)==nil,'non-player model must never acquire growth tag')
    for _,object in ipairs(workspace:GetDescendants())do
     if object.Name==UIContract.tag and object:IsA('BillboardGui') and tagVisible(object)then
      local owner=nil
      for _,actor in ipairs(currentPlayers)do
       if actor.Parent==Players and actor.Character and object:IsDescendantOf(actor.Character)then owner=actor;break end
      end
      check(owner~=nil and type(owner:GetAttribute('EGGRUMBLE_Role'))=='string','every visible growth tag belongs to an equipped human')
     end
    end
   end,hadTag)
   nonhuman:Destroy()
   player:SetAttribute('EGGRUMBLE_Attribute','FIRE')
   local originalHealth,originalMax=humanoid.Health,humanoid.MaxHealth
   humanoid.MaxHealth=230;humanoid.Health=117;UIAudit.frame()
   fixedHPAndBuffs(gui,UIAudit.camera.ViewportSize.X)
   observeUI('FIXED_HP_STATUS_ORACLE','actualHumanoid=117/230;expectedText=HP 117/230;expectedBuffs=属性 FIRE 燃焼 鈍足')
   local shapes={{320,260},{393,851},{375,667},{600,300},{851,393},{1280,720},{1024,768}}
   for _,shape in ipairs(shapes)do for _,hand in ipairs({'RIGHT','LEFT'})do
    player:SetAttribute('EGGRUMBLE_LeftHanded',hand=='LEFT');UIAudit.viewport(shape[1],shape[2])
    local label=shape[1]..'x'..shape[2]..'_'..hand
    expectation('FOOTER_RECT_'..label,function()requireFooter(gui,3,80)end,hadFooter)
    fixedHPAndBuffs(gui,shape[1])
    check(not UIAudit.intersects(UIAudit.rect(status),UIAudit.rect(map)),'original collapsed map/status separation')
    clickUI(map:FindFirstChild('ToggleMap'));UIAudit.frame()
    check(map:FindFirstChild('MapLayer').Visible,'actual existing expanded-map state reached')
    expectation('EXPANDED_MAP_FOOTER_'..label,function()check(not footer(gui).Visible,'only new footer hides during expanded map')end,hadFooter)
    check(gui.Enabled and map.Visible and status.Visible,'expanded map preserves existing chrome')
    fixedHPAndBuffs(gui,shape[1])
    clickUI(map:FindFirstChild('ToggleMap'));UIAudit.frame()
    expectation('COLLAPSED_RESTORE_'..label,function()requireFooter(gui,3,80)end,hadFooter)
   end end
   pass('UI_14_VIEWPORT_PRESERVATION','actual source controls reached in 14 hand/viewport conditions; fonts and renderer remain unverified')
   UIAudit.viewport(393,851);player:SetAttribute('EGGRUMBLE_LeftHanded',false);UIAudit.frame()
   player:SetAttribute('EGGRUMBLE_LegacyExplore_Mode','TEAM')
   player:SetAttribute('EGGRUMBLE_LegacyExplore_Realms',1)
   player:SetAttribute('EGGRUMBLE_LegacyExplore_Shards',0)
   check(toast.Visible,'actual existing exploration toast is visible from server-publication engine input')
   UIAudit.frame()
   expectation('EXPLORE_TOAST_FOOTER_HIDDEN',function()check(not footer(gui).Visible,'new footer hides while existing toast is visible')end,hadFooter)
   fixedHPAndBuffs(gui,393)
   advanceTo(now+3.81);UIAudit.frame();check(not toast.Visible,'actual existing toast timer expires')
   expectation('EXPLORE_TOAST_FOOTER_RESTORED',function()requireFooter(gui,3,80)end,hadFooter)
   -- NaturalRegen is genuine source and may have advanced during the toast.
   -- Reapply only the explicit Humanoid property input for the fixed UI oracle.
   humanoid.MaxHealth=230;humanoid.Health=117;UIAudit.frame()
   clickUI(gui:FindFirstChild('SKILL'));check(drawer.Visible,'existing actual skill drawer opens')
   local realm=Instance.new('ScreenGui');realm.Name='GQ8_RealmBattleControls';realm.Parent=playerGui
   local panel=Instance.new('Frame');panel.Name='Controls';panel.Parent=realm
   UIAudit.frame()
   check(gui.Enabled and map.Visible and status.Visible and not drawer.Visible,'original mounted544 preserves status/map and closes drawer')
   for _,name in ipairs({'ATTACK','JUMP','DODGE','INVUL','MUSOU','ITEM','SKILL','SelectedSkillUse'})do
    check(not gui:FindFirstChild(name).Visible,'original mounted544 hides '..name)
   end
   expectation('MOUNTED_FOOTER_REMAINS',function()requireFooter(gui,3,80)end,hadFooter)
   fixedHPAndBuffs(gui,393);requireHudConnectionContract();requireNoExtraFramePolling()
   panel.Visible=false;UIAudit.frame();realm:Destroy()
   pass('UI_MOUNTED544_PRESERVATION','actual unchanged branch exercised; Realm gameplay remains explicit engine-input limitation')

   humanoid.MaxHealth=originalMax;humanoid.Health=originalHealth;UIAudit.frame()
   humanoid:TakeDamage(humanoid.Health);UIAudit.frame()
   check(not gui.Enabled,'existing dead-avatar HUD gating remains')
   expectation('DEAD_TAG_HIDDEN',function()hiddenTag(player)end,hadTag)
   expectation('DEATH_B_RETAINED',function()
    equal(player:GetAttribute(UIContract.stage),3,'death retains B stage');equal(player:GetAttribute(UIContract.xp),80,'death retains XP')
   end)
   local old,new=replaceCharacter(session,'HEAD_LATE_RESPAWN',false,false,hadTag)
   check(session.isCurrentHuman(player) and player:GetAttribute('EGGRUMBLE_Role')==role,'real Host restores same-round selected role')
   expectation('HEAD_ABSENT_NO_TAG',function()hiddenTag(player)end,hadTag)
   advanceTo(now+.6) -- beyond the existing .35-second art recheck, with Head still absent
   local head=Instance.new('Part');head.Name='Head';head.CanCollide=false;head.Parent=new
   advanceTo(now);UIAudit.frame()
   expectation('HEAD_LATE_TAG',function()requireTag(player,3,8)end,hadTag)
   local completeHeroCount=liveSource('HeroSilhouetteArt')
   player.CharacterAdded:Fire(character);advanceTo(now+.36)
   expectation('SAME_CHARACTER_SINGLE_TAG',function()requireTag(player,3,8)end,hadTag)
   expectation('SAME_CHARACTER_CONNECTIONS_STABLE',function()
    equal(liveSource('HeroSilhouetteArt'),completeHeroCount,'duplicate CharacterAdded does not accumulate live Hero subscriptions')
   end,hadTag)
   -- Adversarial duplicate CharacterAdded is an explicit signal input; live
   -- engine reachability is not asserted. Genuine source callbacks execute.
   local replacedHead=head
   local replacedHeadConnections=heroOwned(replacedHead)
   UIAcceptanceEngine.atomic(function()
    replacedHead:Destroy()
    local fresh=Instance.new('Part');fresh.Name='Head';fresh.CanCollide=false;fresh.Parent=character
   end)
   advanceTo(now)
   expectation('DEFERRED_HEAD_REPLACEMENT',function()
    local tag=requireTag(player,3,8);check(tag.Adornee~=replacedHead,'retired Head is never reused')
   end,hadTag)
   expectation('DEFERRED_HEAD_CONNECTIONS_CLEANUP',function()
    requireDisconnected(replacedHeadConnections,'retired Head subscription')
    equal(liveSource('HeroSilhouetteArt'),completeHeroCount,'Head replacement does not accumulate live Hero subscriptions')
   end,hadTag)
   local retired,fresh=replaceCharacter(session,'DEFERRED_FULL_RESPAWN',true,true,hadTag)
   expectation('DEFERRED_CHARACTER_REPLACEMENT',function()
    requireTag(player,3,8)
    for _,object in ipairs(retired:GetDescendants())do check(object.Name~=UIContract.tag,'retired avatar has no growth tag')end
   end,hadTag)
   expectation('DEFERRED_CHARACTER_CONNECTIONS_STABLE',function()
    equal(liveSource('HeroSilhouetteArt'),completeHeroCount,'whole character replacement preserves one current binding set')
   end,hadTag)
   observeConnections('RESPAWN_REPLACEMENTS_COMPLETE');requireHudConnectionContract();requireNoExtraFramePolling()
   outsideField(session)
   observeUI('CHARACTER_BOUNDARIES','HeadLate=true;HeadExchangeDeferred=true;CharacterRemovingDeferred=true;duplicateCharacterAdded=ADVERSARIAL_ENGINE_INPUT')
  end

  if role=='NINJA'then
   local floor=session.world:FindFirstChild('TacticalBattlefield')
   -- Pick from four bounded real arena inputs. The actual skill/safeMove still
   -- decides collision/ground admission; no product predicate is replaced.
   local untilAt=nil
   for index,offset in ipairs({{0,0},{0,-80},{-120,0},{120,0}})do
    if index>1 then advanceTo(now+dependencies.EGGRUMBLE_CombatBalance.skill('NINJA','B').cooldown+.01)end
    local at=floor.Position+Vector3.new(offset[1],floor.Size.Y*.5+3,offset[2])
    rootPart.CFrame=CFrame.new(at,at+Vector3.new(0,0,-1))
    activate(player,'B')
    untilAt=player:GetAttribute('EGGRUMBLE_StealthUntil')
    if type(untilAt)=='number' and untilAt>now then
     observeUI('NINJA_REAL_APPROACH','boundedInput='..index..';actualSourceAccepted=true');break
    end
   end
   if type(untilAt)~='number' or untilAt<=now then
    observeUI('NINJA_CAST_DIAGNOSTIC','role='..tostring(player:GetAttribute('EGGRUMBLE_Role'))
     ..';HP='..humanoid.Health..';held='..tostring(session.rules.castles['42'].heldEggs)
     ..';signature='..tostring(player:GetAttribute('EGGRUMBLE_SkillCastSignature')))
    for i=math.max(1,#queryTrace-12),#queryTrace do
     local q=queryTrace[i]
     print('NINJA_QUERY',q.source,q.line,q.hit and q.hit.Name or 'CLEAR',
      q.origin.X,q.origin.Y,q.origin.Z,q.delta.X,q.delta.Y,q.delta.Z)
    end
   end
   check(type(untilAt)=='number' and untilAt>now,'real NINJA B produced genuine server-clock stealth')
   expectation('NINJA_STEALTH_HIDDEN_WITHOUT_FRAME',function()hiddenTag(player)end,hadTag)
   -- Existing non-growth attribute input models a genuine sensor/clear event.
   -- No B/XP/GrowthActive attribute is written by this fixture.
   player:SetAttribute('EGGRUMBLE_StealthUntil',now)
   expectation('NINJA_EARLY_CLEAR_REVEALS',function()requireTag(player,3,4)end,hadTag)
   local oldHead=character:FindFirstChild('Head')
   local oldHeadConnections=heroOwned(oldHead)
   local ninjaHeroCount=liveSource('HeroSilhouetteArt')
   UIAcceptanceEngine.atomic(function()
    oldHead:Destroy()
    local nextHead=Instance.new('Part');nextHead.Name='Head';nextHead.CanCollide=false;nextHead.Parent=character
   end)
   advanceTo(untilAt+.05)
   expectation('OLD_STEALTH_TIMER_CANNOT_HIDE_REPLACEMENT',function()requireTag(player,3,4)end,hadTag)
   expectation('NINJA_HEAD_CONNECTIONS_CLEANUP',function()
    requireDisconnected(oldHeadConnections,'stealth-era retired Head subscription')
    equal(liveSource('HeroSilhouetteArt'),ninjaHeroCount,'early clear and old timer do not accumulate live Hero subscriptions')
    end,hadTag)
    naturalNinjaFollowup(session,hadTag)
    outsideField(session)
    observeUI('STEALTH_CLOCK','actualNinjaB=true;osClock='..now..';serverEpoch='..workspace:GetServerTimeNow()
    ..';earlyClear=EXPLICIT_EXISTING_ATTRIBUTE_INPUT;oldDeadlineDelivered=true')
  end

  if role=='ZOMBIE'then
   local leavingAvatar=character
   local leavingConnections=heroPlayerOwned(player,leavingAvatar)
   local legacyHud=UIAcceptanceEngine.captureLive(function(entry)
    return entry.source=='HudIntelRuntime' and entry.owner==player and entry.legacyCallback
   end)
   observeUI('PLAYER_LEAVE_CONNECTIONS_BEFORE','HeroOwned='..#leavingConnections..';unchangedLegacyHUD='..#legacyHud)
   UIAcceptanceEngine.atomic(function()
    Players.PlayerRemoving:Fire(player);player.Parent=nil
   end)
   expectation('PLAYER_LEAVE_HERO_OWNED_CONNECTIONS_ZERO',function()
    requireDisconnected(leavingConnections,'Hero Player/avatar/Head subscription after PlayerRemoving')
    equal(#heroPlayerOwned(player,leavingAvatar),0,'all old and new Hero owned subscriptions retire on leave')
   end)
   expectation('PLAYER_LEAVE_TAG_CLEANUP',function()hiddenTag(player)end,hadTag)
   player:GetAttributeChangedSignal('EGGRUMBLE_Role'):Fire()
   player.CharacterAdded:Fire(character);advanceTo(now+.36)
   expectation('RETIRED_PLAYER_LATE_CALLBACKS',function()hiddenTag(player)end,hadTag)
   expectation('RETIRED_PLAYER_CONNECTIONS_REMAIN_ZERO',function()
    equal(#heroPlayerOwned(player,leavingAvatar),0,'late signals cannot recreate retired Hero subscriptions')
   end)
   UIExpect.retiredHeroLive=#heroPlayerOwned(player,leavingAvatar)
   equal(#legacyHud,3,'H93 LegacyExplore owns three direct Player subscriptions')
   for _,entry in ipairs(legacyHud)do check(entry.connected,'unchanged client-lifetime LegacyExplore subscription survives fixture PlayerRemoving')end
   requireHudConnectionContract();requireNoExtraFramePolling()
   observeUI('PLAYER_LEAVE_CONNECTIONS_AFTER','HeroOwned='..UIExpect.retiredHeroLive..';legacyHUDPreserved=3;clientTeardown=NOT_MODELED')
  end

  local function finish()advanceTo(session.deadlineLease.start+900.01)end
  if role=='TRAPPER'then UIAcceptanceEngine.atomic(finish)else finish()end
  check(session.rules.phase=='FINISHED','real Host deadline finishes current round')
  UIAudit.frame();check(not gui.Enabled,'original HUD hides on genuine FINISHED phase')
  expectation(role..'_FINISH_TAG_HIDDEN',function()hiddenTag(player)end,hadTag)
  expectation(role..'_FINISH_FOOTER_HIDDEN',function()check(not footer(gui).Visible,'finished footer is explicitly hidden')end,hadFooter)
  if player.Parent==Players then
   expectation(role..'_PUBLIC_FINISH_RESET',function()
    equal(player:GetAttribute(UIContract.stage),1,'public B resets after finish')
    equal(player:GetAttribute(UIContract.xp),0,'public XP resets after finish')
    check(player:GetAttribute(UIContract.active)==false,'public growth no longer active')
   end)
   local resultGui=playerGui:FindFirstChild('EGGRUMBLE_MatchResult')
   local compact=resultGui and resultGui:FindFirstChild('CompactResult')
   local stats=compact and compact:FindFirstChild('VerifiedPersonalStats')
   check(stats~=nil,'actual full ResultService produced stats')
   equal(compact.Size.Y.Offset,94,'existing result panel height preserved')
   equal(stats.Size.Y.Offset,41,'existing result two-line area preserved')
   expectation(role..'_RESULT_NEUTRAL_KO_SNAPSHOT',function()
    exactNumberToken(stats.Text,'KO',koCount,'finished result genuine neutral KO')
   end)
   expectation(role..'_RESULT_B_SNAPSHOT',function()
    exactNumberToken(stats.Text,'B',3,'finished result B snapshot after public reset')
   end)
   observeUI(role..'_RESULT_SNAPSHOT','expectedNeutralKO='..koCount..';expectedB=3;actualText='..stats.Text:gsub('\n',' / '))
  end
  local finishAt=nil
  for _,entry in ipairs(phaseWrites)do
   if entry.instance==session.world and entry.phase=='FINISHED'then finishAt=finishAt or entry.at end
  end
  check(finishAt~=nil,'genuine finish publication observed')
  advanceTo(finishAt+10.1);UIAudit.frame()
  check(session.world.Parent==nil,'actual Replay destroys finished arena')
  expectation(role..'_LOBBY_TAG_HIDDEN',function()hiddenTag(player)end,hadTag)
  expectation(role..'_LOBBY_FOOTER_HIDDEN',function()check(not footer(gui).Visible,'lobby footer remains hidden')end,hadFooter)
  for _,entry in ipairs(held)do enqueue(now,entry.entry.thread,entry.entry.args)end
  advanceTo(now)
  pass('REAL_ROLE_'..role,'real prompt/equip; genuine neutral KOs; real finish/Replay; current role name='..row[2])
 end

  rolePendingFollowup()

  expectation('NEW_ATTRIBUTE_WRITER_ORIGIN',function()
  check(#UIAcceptanceEngine.writes>0,'H93 has no new B/XP/GrowthActive writer')
  for _,entry in ipairs(UIAcceptanceEngine.writes)do
   check(entry.source=='SwarmCombat','new attributes are written only by actual Swarm source, saw '..entry.source)
  end
 end)
 for _,entry in ipairs(UIAcceptanceEngine.writes)do
  print('BWRITE\t'..entry.source..'\t'..entry.name..'\t'..tostring(entry.value)..'\t'..entry.at..'\tline='..entry.line)
 end
 requireHudConnectionContract();requireNoExtraFramePolling();observeConnections('FINAL')
 check(#warnings==0,'no dependency warning hidden')
 check(UIAcceptanceEngine.holdDepth==0 and #UIAcceptanceEngine.queue==0,'no deferred fixture work left behind')
 if UI_ACCEPTANCE_EXPECT=='baseline-red'then
  check(UIExpect.red>0 and not UIExpect.everTag and not UIExpect.everFooter,'unchanged H93 must demonstrate missing feature')
  equal(#UIAcceptanceEngine.writes,0,'fixture did not synthesize any future B attribute')
 else
  check(UIExpect.red==0 and UIExpect.notReached==0,'candidate must satisfy every reachable UI requirement')
 end
 return '31 exact complete bodies; actual selected roles and genuine KO; engine-only deferred/GUI inputs; no product edits'
end)
print('CASE\tUI_ACCEPTANCE_EXECUTION_COMPLETE\t'..(if ok then 'PASS' else 'FAIL')..'\t'..tostring(result):gsub('\n',' '))
print('METRIC\tui_expectation_red\t'..UIExpect.red)
print('METRIC\tui_expectation_not_reached\t'..UIExpect.notReached)
print('METRIC\tui_expectation_pass\t'..UIExpect.passed)
print('METRIC\tnew_attribute_writes\t'..#UIAcceptanceEngine.writes)
print('METRIC\tdeferred_delivered\t'..UIAcceptanceEngine.delivered)
print('METRIC\tdeferred_explicit_drops\t'..UIAcceptanceEngine.dropped)
print('METRIC\trender_step_callbacks\t'..#UIAudit.renderCallbacks)
print('METRIC\tui_heartbeat_registrations\t'..tostring(UIExpect.uiHeartbeatRegistrations))
print('METRIC\thud_total_registrations\t'..tostring(UIExpect.hudRegistrations))
print('METRIC\tmax_live_hero_connections\t'..UIExpect.maxLiveHero)
print('METRIC\tmax_live_hud_connections\t'..UIExpect.maxLiveHud)
print('METRIC\tretired_player_hero_connections\t'..UIExpect.retiredHeroLive)
if not ok then error(result,0)end
-- GQ470_SECTION_END UI_CASES
-- GQ470_SECTION_BEGIN AI_ENGINE
-- Fixed seed 11 preserves the known original -Z LOS failure; no passing-seed selection.
math.randomseed(11)
-- Supplementary declared 30-body suite only; not part of frozen server28/UI31.
-- Real BotActors/Router load. Pathfinding engine availability is explicitly absent.
local growthAi={jobs={},hits={}}
local aiBeforeService=game.GetService
game.GetService=function(self,name)
 if name=='PathfindingService'then
  return {CreatePath=function()error('NATIVE_PATHFINDING_ENGINE_UNAVAILABLE',0)end}
 end
 return aiBeforeService(self,name)
end
local aiBeforeSpawn=task.spawn
task.spawn=function(fn,...)
 if type(fn)=='function'and sourceLabel(debug.info(fn,'l'))=='BotActors'then
  local thread=coroutine.create(fn)
  table.insert(growthAi.jobs,{thread=thread,args=table.pack(...),line=debug.info(fn,'l')})
  return thread
 end
 return aiBeforeSpawn(fn,...)
end
function growthAi.tick(job)
 enqueue(now,job.thread,job.args)
 advanceTo(now)
 assert(coroutine.status(job.thread)=='suspended','actual BotActors tick yields at original .18s wait')
 local parked=false
 for i=#pending,1,-1 do
  if pending[i].thread==job.thread then table.remove(pending,i);parked=true;break end
 end
 assert(parked,'park next exact actual bot loop resume at engine scheduler boundary')
end
function growthAi.observeApi(session)
 local actual=session.swarm.damageFromBot
 session.swarm.damageFromBot=function(id,at)
  local caller=sourceLabel(debug.info(2,'l'))
  local result=actual(id,at)
  table.insert(growthAi.hits,{session=session,id=id,caller=caller,hits=result})
  return result
 end
end
-- GQ470_SECTION_END AI_ENGINE
-- GQ470_SECTION_BEGIN AI_CASES
-- Real full BotActors/Router supplement. All source bodies remain exact inputs.
local function aiRow(session,id,kills)
 for _,row in ipairs(dependencies.EGGRUMBLE_ScoreBalance.build(session.rules,kills).rows)do
  if row.id==id then return row end
 end
 error('actual score row absent '..id,0)
end
local function botNeutralApproach(actor,target,position)
 -- This positive KO case requires a clear, three-stud attack approach.
 -- Use the same collision query as the unchanged Swarm source; a blocked
 -- ray remains blocked, and all four blocked directions fail the fixture.
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={actor,target}
 params.RespectCanCollide=true
 for index,offset in ipairs({
  Vector3.new(0,0,-3),Vector3.new(0,0,3),
  Vector3.new(-3,0,0),Vector3.new(3,0,0),
 })do
  local at=position+offset
  local origin=at+Vector3.new(0,1,0)
  local delta=(position+Vector3.new(0,1,0))-origin
  if workspace:Raycast(origin,delta,params)==nil then
   print('TRACE\tBOT_NEUTRAL_APPROACH\t'..index)
   return CFrame.lookAt(at,position)
  end
 end
 error('NO_CLEAR_BOT_NEUTRAL_APPROACH',0)
end
local function botOneKO(session,id,job)
 local target=spawnCurrentNeutral(session)
 local human=target:FindFirstChildOfClass('Humanoid')
 local position=target.PrimaryPart.Position
 local actor=session.botActors[id]
 check(actor and actor:GetAttribute('EGGRUMBLE_BotId')==id,'actual original BotActors model and identity')
 check(session.rules.castles[id].isAI==true,'real Rules entry is AI')
 local before=table.clone(session.swarm.kills)
 local previous=before[id]or 0
 local total=session.swarm.getTotal()
 local aliveBefore={}
 for _,model in ipairs(session.world:FindFirstChild('NeutralHorde'):GetChildren())do
  local h=model:FindFirstChildOfClass('Humanoid')
  if h and h.Health>0 then aliveBefore[h]=true end
 end
 -- Geometry-only engine input: keep other real actors out of this target's
 -- attack radius, so attribution does not depend on table iteration order.
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local serial=0
 for otherId,other in pairs(session.botActors)do
  if otherId~=id then
   serial+=1
   other:PivotTo(CFrame.new(floor.Position+Vector3.new(floor.Size.X+2000+serial*10,20,floor.Size.Z+2000)))
  end
 end
 actor:PivotTo(botNeutralApproach(actor,target,position))
 growthAi.tick(job)
 equal(human.Health,0,'actual BotActors loop -> full Swarm damage -> real neutral death')
 local genuineVictims=0
 for h in pairs(aliveBefore)do
  if h.Health<=0 and h:GetAttribute('LastAttackerId')==id then genuineVictims+=1 end
 end
 check(genuineVictims>=1,'at least one originally living neutral actually died under this AI attribution')
 equal(session.swarm.kills[id],previous+genuineVictims,'every actual AI victim counted exactly once in original ledger')
 check(session.swarm.getTotal()>=total+genuineVictims,'original total includes all actual AI victims')
 local forwarded=false
 for _,row in ipairs(growthAi.hits)do
  if row.session==session and row.id==id and row.caller=='BotActors'and row.hits>0 then forwarded=true end
 end
 check(forwarded,'actual BotActors call forwarded to unchanged real damageFromBot body')
 local actualScore=aiRow(session,id,session.swarm.kills)
 local priorKOScore=aiRow(session,id,before)
 equal(actualScore.ko,previous+genuineVictims,'actual score retains exact AI victim count')
 check(previous+genuineVictims<=100,'within original six-point KO score tier')
 equal(actualScore.score-priorKOScore.score,6*genuineVictims,'original six-point score contribution for every genuine AI victim')
 outsideField(session)
 advanceTo(now+.26)
 return previous+genuineVictims,genuineVictims
end
local ok,result=pcall(function()
 advanceTo(now)
 sharedRequires()
 local first=ready('REAL_AI_HOST_READY')
 check(stubCalls['BotActors.start']==nil,'real BotActors replaced original unrelated stub')
 check(type(first.takeover)=='function'and #growthAi.jobs==1,'actual BotActors.start installed takeover and registered real loop')
 local id=nil
 for key in pairs(first.botActors)do if id==nil or key<id then id=key end end
 check(id~=nil,'actual initial AI roster created models')
 growthAi.observeApi(first)
 botOneKO(first,id,growthAi.jobs[1])
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),0,'initial bot KO never published as human KO')
 equal(player:GetAttribute('EGGRUMBLE_BattleStage'),1,'initial bot KO does not change human B')
 local old=player
 Players.PlayerRemoving:Fire(old)
 check(first.rules.castles['42'].isAI==true and first.botActors['42']~=nil,
  'actual Host PlayerRemoving invoked full BotActors.takeover')
 old.Parent=nil;currentPlayers={second}
 local fresh=Instance.new('Player');fresh.Name='RealAiReplacement42';fresh.UserId=42;fresh.Parent=Players
 local gui=Instance.new('PlayerGui');gui.Parent=fresh
 local backpack=Instance.new('Backpack');backpack.Parent=fresh
 local avatar=Instance.new('Model');avatar.Parent=workspace
 local human=Instance.new('Humanoid');human.WalkSpeed=20;human.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=avatar
 avatar.PrimaryPart=root;fresh.Character=avatar
 currentPlayers={fresh,second};Players.PlayerAdded:Fire(fresh)
 player=fresh;character=avatar;humanoid=human;rootPart=root;playerGui=gui;bag=backpack
 local count=#capturedSessions
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(player,scenes:FindFirstChild('BATTLE_ROYALE_PORTAL'),'参加する')
 local start=now
 advanceTo(start+11.99);equal(#capturedSessions,count,'real replacement READY not shortened')
 advanceTo(start+12.01);equal(#capturedSessions,count+1,'real replacement BR created')
 local current=capturedSessions[#capturedSessions]
 check(current.mode=='BATTLE_ROYALE'and current.isCurrentHuman(fresh)and not first.isCurrentHuman(fresh),
  'real replacement belongs only to new BR')
 local neutral=spawnCurrentNeutral(current)
 local point=neutral.PrimaryPart.Position
 rootPart.CFrame=clearNeutralApproach(neutral,point)
 equal(current.swarm.damageFromPlayer(fresh,point,.01,52,'CIRCLE'),1,'genuine replacement neutral KO')
 equal(current.swarm.kills['42'],1,'new real ledger established')
 outsideField(current);advanceTo(now+.26)
 equal(fresh:GetAttribute('EGGRUMBLE_BattleStage'),2,'replacement earned actual B2')
 equal(fresh:GetAttribute('EGGRUMBLE_BattleXP'),10,'replacement earned actual XP10')
 local before=growthEngine.snapshot(fresh)
 local writes=growthEngine.writeCount(fresh)
 -- The old TEAM 42 is now a true actual AI; new BR 42 is a different Player.
 local takeoverKOs,takeoverVictims=botOneKO(first,'42',growthAi.jobs[1])
 for name in pairs(growthEngine.watched)do
  check(fresh:GetAttribute(name)==before[name],'AI takeover must not publish '..name..' to replacement')
 end
 equal(growthEngine.writeCount(fresh),writes,'same numeric AI id causes zero replacement publication writes')
 equal(current.swarm.kills['42'],1,'old takeover KO never changes new BR ledger')
 equal(first.swarm.kills['42'],takeoverKOs,'old takeover ledger retains legitimate AI KO')
 print('OBSERVATION\tREAL_AI_TAKEOVER_POSITIVE\tfullBotActors/start/takeover/loop->fullSwarmDied;oldKO'..takeoverKOs..';genuineVictims'..takeoverVictims..';ScoreDelta'..(6*takeoverVictims)..';newB2/10/KO1;newPlayerWrites0')
 check(#warnings==0,'no swallowed actual bot neutral exception')
 return '30 full bodies; actual initial AI and disconnected-human takeover both earn genuine neutral KO with original score; replacement Player untouched'
end)
print('CASE\tREAL_AI_TAKEOVER_SUPPLEMENT\t'..(if ok then 'PASS'else 'FAIL')..'\t'..tostring(result):gsub('\n',' '))
if not ok then error(result,0)end
-- GQ470_SECTION_END AI_CASES
