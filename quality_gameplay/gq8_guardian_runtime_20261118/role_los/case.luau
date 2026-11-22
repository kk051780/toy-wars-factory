-- Reuses the original #796 outgoing-LOS acceptance bodies without edits.
-- Assembly supplies local LOS_CASE='gate' or 'wall'.
assert(LOS_CASE=='gate' or LOS_CASE=='wall','EXPECTED_LOS_CASE_SELECTOR')
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
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
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
 check(guardian:GetAttribute('EGGRUMBLE_GuardianRole')=='MAGE','actual MAGE Guardian')
 local guardianHum=guardian:FindFirstChildOfClass('Humanoid')
 equal(guardianHum.Health,70,'original MAGE Guardian HP')
 local spawnAt=now
 local initial=guardian.PrimaryPart.Position
 print('TRACE\tSPAWN\t'..now..'\t'..vectorText(initial)..'\tBASE\t'..vectorText(base))
 print('TRACE\tGATE\t'..door.Name..'\t'..vectorText(door.Position)..'\t'..vectorText(door.Size)..'\t'..tostring(door.CanCollide)..'\t'..tostring(door.CanQuery))
 return {session=session,door=door,base=base,guardian=guardian,guardianHum=guardianHum,spawnAt=spawnAt,initial=initial,held=held}
end

if LOS_CASE=='gate' then
do
local ok,result=pcall(function()
 local f=prepareActualHost()
 local actor=f.guardian;local target=f.guardianHum
 rootPart.CFrame=CFrame.new(Vector3.new(f.door.Position.X,f.base.Y+2.5,f.door.Position.Z-1),actor.PrimaryPart.Position)
 check(f.door.CanCollide==false and f.door.CanQuery==true,'real open gate properties')
 check((rootPart.Position-actor.PrimaryPart.Position).Magnitude>17,'human initially outside original MAGE range')
 local farStart=#queryTrace
 advanceTo(now+.99)
 for i=farStart+1,#queryTrace do
  check(queryTrace[i].source~='CastleGuardianRuntime','original out-of-range guard emits no target ray')
 end
 equal(humanoid.Health,100,'original range17 still rejects far enemy')
 pass('OUT_OF_RANGE_CONTROL','actual current enemy starts beyond17; three original ticks give no target ray or damage')
 local first=nil
 local seen=#queryTrace
 for _=1,45 do
  advanceTo(now+.33)
  for i=seen+1,#queryTrace do
   local q=queryTrace[i]
   if q.source=='CastleGuardianRuntime'then first=q;break end
  end
  seen=#queryTrace
  if first then break end
 end
 check(first~=nil and first.delta.Magnitude<17,'natural Guardian movement enters original range')
 check(first.at>f.spawnAt+1.6,'unchanged original first attack cooldown elapsed')
 check(f.session.isCurrentHuman(player)and f.session.rules.castles['42'].alive,'actual alive current human')
 print('TRACE\tGATE_OUTGOING\t'..first.at..'\t'..vectorText(first.origin)..'\t'..vectorText(first.origin+first.delta)..'\t'..first.delta.Magnitude..'\t'..tostring(first.respectCanCollide)..'\t'..(first.hit and first.hit.Name or 'CLEAR')..'\tHP'..humanoid.Health)
 equal(humanoid.Health,94,'OPEN_GATE_OUTGOING_DAMAGE_MISSING')
 check(first.respectCanCollide==true and first.hit==nil,'actual candidate targetOf ignores noncolliding real gate')
 equal(#guardianDamageFilters,1,'one actual Guardian attack reaches real Invul filter')
 local filtered=guardianDamageFilters[1]
 check(filtered.victim==humanoid and filtered.kind=='NEUTRAL','actual current human receives Guardian attack')
 equal(filtered.damage,6,'unchanged MAGE base damage')
 equal(filtered.filtered,6,'original Invul accepts6')
 pass('OPEN_GATE_OUTGOING_DAMAGE','actual noncolliding gate no longer hides real enemy; original MAGE Guardian deals6, HP100 to94')
 local humanAt=rootPart.Position
 local guardianAt=actor.PrimaryPart.Position
 rootPart.CFrame=CFrame.new(humanAt,guardianAt)
 local diagnostic=RaycastParams.new();diagnostic.FilterType=Enum.RaycastFilterType.Exclude
 diagnostic.FilterDescendantsInstances={character,actor}
 local origin=humanAt+Vector3.new(0,1.5,0)
 local oldQuery=workspace:Raycast(origin,guardianAt-origin,diagnostic)
 check(oldQuery and oldQuery.Instance==f.door,'same actual incoming segment crosses real gate')
 local rayStart=#queryTrace;local calls=#guardianCalls
 activate(player,'B')
 equal(target.Health,25,'unchanged incoming repair still permits capped45 through real gate')
 equal(#guardianCalls,calls+1,'actual human Tool routes through Host Guardian API once')
 local call=guardianCalls[#guardianCalls]
 check(call.session==f.session and call.player==player and call.root==rootPart and call.character==character
  and call.shape=='INFERNO'and call.result==1,'actual existing origin/character/shape caller preserved')
 local incoming=nil
 for i=rayStart+1,#queryTrace do
  if queryTrace[i].source=='CastleGuardianRuntime'then incoming=queryTrace[i]end
 end
 check(incoming and incoming.hit==nil and incoming.respectCanCollide==true,'actual incoming LOS remains collidable-only')
 check(f.door.CanCollide==false and f.door.CanQuery==true,'no door property mutation')
 print('TRACE\tGATE_INCOMING\t'..now..'\t'..vectorText(incoming.origin)..'\t'..vectorText(incoming.origin+incoming.delta)..'\ttrue\tCLEAR\tHP70_TO25')
 pass('OPEN_GATE_INCOMING_PRESERVED','real MAGE Tool B and existing incoming repair, capped45/HP70 to25, original args and shape')
 return 'real Host open gate, original range/cooldown/Invul, reciprocal legitimate attacks'
end)
print('CASE\tGATE_OUTGOING\t'..(if ok then 'PASS'else 'FAIL')..'\t'..tostring(result):gsub('\n',' '))
if not ok then error(result,0)end

end
else
do
local ok,result=pcall(function()
 local f=prepareActualHost()
 local actor=f.guardian;local target=f.guardianHum
 local wall=f.session.castleModels['43'].model:FindFirstChild('CastleFrontRight')
 check(wall and wall.CanCollide==true and wall.CanQuery==true,'actual Host collidable front wall')
 check((wall.Position-Vector3.new(-465,12,247)).Magnitude<1e-6,'actual wall source position')
 check((wall.Size-Vector3.new(10,12,2)).Magnitude<1e-6,'actual wall source size')
 local humanAt=Vector3.new(f.door.Position.X+9,f.base.Y+2.5,f.door.Position.Z-2)
 rootPart.CFrame=CFrame.new(humanAt,actor.PrimaryPart.Position)
 print('TRACE\tREAL_WALL\t'..wall.Name..'\t'..vectorText(wall.Position)..'\t'..vectorText(wall.Size)..'\ttrue\ttrue\tHUMAN\t'..vectorText(humanAt))
 check((humanAt-actor.PrimaryPart.Position).Magnitude>17,'human initially outside original MAGE range')
 local farStart=#queryTrace
 advanceTo(now+.99)
 for i=farStart+1,#queryTrace do
  check(queryTrace[i].source~='CastleGuardianRuntime','original out-of-range guard emits no target ray')
 end
 equal(humanoid.Health,100,'original range17 still rejects far enemy')
 pass('OUT_OF_RANGE_CONTROL','actual current enemy starts beyond17; three original ticks give no target ray or damage')
 local seen=#queryTrace;local blocked={}
 for _=1,80 do
  advanceTo(now+.33)
  check(actor.Parent~=nil,'actual Guardian remains alive during wall comparison')
  for i=seen+1,#queryTrace do
   local q=queryTrace[i]
   if q.source=='CastleGuardianRuntime'then
    check(q.hit==wall,'actual collidable CastleFrontRight is outgoing obstruction')
    check(q.delta.Magnitude<17 and q.at>f.spawnAt+1.6,'original range and attack delay eligible')
    table.insert(blocked,q)
    print('TRACE\tWALL_OUTGOING\t'..q.at..'\t'..vectorText(q.origin)..'\t'..vectorText(q.origin+q.delta)..'\t'..q.delta.Magnitude..'\t'..tostring(q.respectCanCollide)..'\tCastleFrontRight')
   end
  end
  seen=#queryTrace
  if #blocked>=10 and blocked[#blocked].at-blocked[1].at>2.7 then break end
 end
 check(#blocked>=10 and blocked[#blocked].at-blocked[1].at>2.7,'actual collidable wall blocks for more than original attack period')
 equal(humanoid.Health,100,'real wall still prevents Guardian attack')
 equal(#guardianDamageFilters,0,'real wall prevents target acquisition before Invul')
 check(f.session.isCurrentHuman(player)and f.session.rules.castles['42'].alive,'actual current enemy alive')
 pass('COLLIDABLE_WALL_OUTGOING_REJECTED','10 eligible original source queries across more than2.7s hit actual CastleFrontRight; HP100, no damage filter call')
 local guardianAt=actor.PrimaryPart.Position
 rootPart.CFrame=CFrame.new(humanAt,guardianAt)
 local rayStart=#queryTrace;local calls=#guardianCalls
 activate(player,'B')
 equal(target.Health,70,'existing incoming repair keeps actual collidable wall protection')
 equal(#guardianCalls,calls+1,'actual human Tool invokes existing Guardian API')
 local call=guardianCalls[#guardianCalls]
 check(call.session==f.session and call.player==player and call.root==rootPart and call.character==character
  and call.shape=='INFERNO'and call.result==0,'actual incoming args preserved and wall rejects hit')
 local incoming=nil
 for i=rayStart+1,#queryTrace do
  if queryTrace[i].source=='CastleGuardianRuntime'then incoming=queryTrace[i]end
 end
 check(incoming and incoming.respectCanCollide==true and incoming.hit==wall,'actual incoming geometry passed and original LOS hits actual wall')
 check(wall.CanCollide==true and wall.CanQuery==true,'actual wall flags unchanged')
 print('TRACE\tWALL_INCOMING\t'..now..'\t'..vectorText(incoming.origin)..'\t'..vectorText(incoming.origin+incoming.delta)..'\ttrue\tCastleFrontRight\tHP70_UNCHANGED')
 pass('COLLIDABLE_WALL_INCOMING_PRESERVED','actual MAGE Tool B reaches original incoming LOS and is blocked by real CastleFrontRight, GuardianHP70')
 return 'real Host collidable wall, original range/cooldown, outgoing and incoming both reject'
end)
print('CASE\tWALL_OUTGOING\t'..(if ok then 'PASS'else 'FAIL')..'\t'..tostring(result):gsub('\n',' '))
if not ok then error(result,0)end

end
end
