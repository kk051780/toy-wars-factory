-- New diagnostic setup: player42 NINJA and selected original guardian archetype; existing Host spawn path.
local function check(value,message)assert(value,message)end
local function equal(value,wanted,message)
 assert(type(value)=='number'and math.abs(value-wanted)<1e-6,
  message..' actual='..tostring(value)..' expected='..tostring(wanted))
end
local function pass(name,detail)print('CASE\t'..name..'\tPASS\t'..detail)end
local function vectorText(v)return string.format('%.9f,%.9f,%.9f',v.X,v.Y,v.Z)end
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
local function parkSwarm(session)
 local selected={}
 for _,record in ipairs(swarmTasks)do
  if record.session==session then
   check(coroutine.status(record.thread)=='suspended','real Swarm coroutine before park')
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
 check(next(selected)==nil,'original Swarm coroutines found in engine queue')
 equal(#held,2,'only original unrelated Swarm spawn and movement jobs parked')
 return held
end
local function prepareActualHost()
 advanceTo(now)
 trigger(player,scenes:FindFirstChild('ROLE_NINJA'),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_'..GUARDIAN_ROLE),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 advanceTo(now+12.01)
 equal(#capturedSessions,1,'one actual Host session')
 local session=capturedSessions[1]
 check(session.mode=='TEAM'and session.rules.phase=='ACTIVE','actual active TEAM')
 check(session.isCurrentHuman(player)and session.isCurrentHuman(second),'both actual current humans')
 check(session.rules.castles['42'].team~=session.rules.castles['43'].team,'actual opposing teams')
 check(session.guardians==guardianAttachments[1].controller,'actual Host owns actual Guardian API')
 outsideField(session)
 local held=parkSwarm(session)
 pass('HOST_READY','real two-human TEAM prompts and 12-second READY; two unrelated Swarm engine jobs parked')
 local door=session.castleModels['43'].door
 local base=session.castleLocations['43']
 for _=1,10 do
  advanceTo(now+3)
  trigger(player,door,'攻城攻撃')
  outsideField(session)
 end
 equal(session.castleSiegeStates['43'].gateHP,0,'real bounded prompts clear siege gate')
 equal(session.rules.castles['43'].hp,700,'real bounded prompts reach original Guardian threshold')
 local guardian=nil
 for _,model in ipairs(session.world:GetChildren())do
  if model:GetAttribute('EGGRUMBLE_GuardianOwner')=='43'then
   check(not guardian,'exactly one first-threshold Guardian');guardian=model
  end
 end
 check(guardian~=nil,'actual Guardian spawned from real Host damage threshold')
 check(guardian:GetAttribute('EGGRUMBLE_GuardianRole')==GUARDIAN_ROLE,'actual selected Guardian role')
 local guardianHum=guardian:FindFirstChildOfClass('Humanoid')
 equal(guardianHum.Health,GUARDIAN_EXPECT.hp,'original selected Guardian HP')
 local spawnAt=now
 local initial=guardian.PrimaryPart.Position
 print('TRACE\tSPAWN\t'..now..'\t'..vectorText(initial)..'\tBASE\t'..vectorText(base))
 print('TRACE\tGATE\t'..door.Name..'\t'..vectorText(door.Position)..'\t'..vectorText(door.Size)..'\t'..tostring(door.CanCollide)..'\t'..tostring(door.CanQuery))
 return {session=session,door=door,base=base,guardian=guardian,guardianHum=guardianHum,spawnAt=spawnAt,initial=initial,held=held}
end
