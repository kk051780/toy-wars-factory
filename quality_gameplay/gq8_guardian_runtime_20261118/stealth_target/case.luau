-- Read-only full-source Guardian diagnosis, not Studio. MODE is injected by the runner.
-- The real Host creates its match/guardian and the real NINJA B creates stealth.
-- Character placement is controlled by this API fixture, not natural movement.
local ok,reason=pcall(function()
 local teammate=nil
 if MODE=='same_team' then
  -- Queue two additional real human objects before the existing42/43 helper.
  -- Existing TEAM allocation alternates sides, so45 and43 become distinct allies.
  local function addHuman(id)
   local p=Instance.new('Player');p.UserId=id;p.Name='StealthTeamControl'..id;p.Parent=Players
   local gui=Instance.new('PlayerGui');gui.Parent=p
   local bag=Instance.new('Backpack');bag.Parent=p
   local ch=Instance.new('Model');ch.Name=p.Name..'Avatar';ch.Parent=workspace
   local hum=Instance.new('Humanoid');hum.WalkSpeed=16;hum.Parent=ch
   local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=ch
   ch.PrimaryPart=root;p.Character=ch
   table.insert(currentPlayers,p);Players.PlayerAdded:Fire(p)
   trigger(p,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
   trigger(p,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
   return p
  end
  addHuman(44)
  teammate=addHuman(45)
 end
 local f=prepareActualHost()
 local session=f.session
 local castle=session.rules.castles['42']
 check(player:GetAttribute('EGGRUMBLE_Role')=='NINJA','actual NINJA role selected')
 equal(castle.heldEggs,0,'initial real human inventory is empty')
 local targetPoint=f.base+Vector3.new(8,3,8)
 local sensors=session.world:FindFirstChild('EGGRUMBLE_CastleDefenseLive')
 local minimumSensorDistance=math.huge
 for _,part in ipairs(sensors:GetChildren())do
  if part.Name=='CastleDefense_SENSOR'then
   minimumSensorDistance=math.min(minimumSensorDistance,(part.Position-targetPoint).Magnitude)
  end
 end
 check(minimumSensorDistance>30,'diagnostic position is outside existing real sensor radius')
 print('TRACE\tSENSOR_SEPARATION\t'..minimumSensorDistance)
 if MODE~='visible' and MODE~='same_team' and MODE~='inactive' then
  local floor=session.world:FindFirstChild('TacticalBattlefield')
  local start=floor.Position+Vector3.new(200,floor.Size.Y*.5+3,200)
  rootPart.CFrame=CFrame.new(start,start+Vector3.new(0,0,-1))
  activate(player,'B')
  local untilTime=player:GetAttribute('EGGRUMBLE_StealthUntil')
  check(type(untilTime)=='number'and untilTime>now,'real NINJA B grants current stealth')
  print('TRACE\tNINJA_B\t'..now..'\tUNTIL\t'..untilTime..'\tHELD\t'..castle.heldEggs)
  if MODE=='carrier' then
   local vault=session.castleModels['43'].model:FindFirstChild('EggVault')
   trigger(player,vault,'敵の卵を奪取')
   equal(castle.heldEggs,1,'real Host/Rules enemy-egg steal')
   check(player:GetAttribute('EGGRUMBLE_StealthUntil')>now,'stealth timer remains after real objective pickup')
   check(session.rules.events[#session.rules.events]~=nil,'real objective event retained')
  elseif MODE=='expired' then
   outsideField(session)
   advanceTo(untilTime+.01)
   check(now>player:GetAttribute('EGGRUMBLE_StealthUntil'),'real stealth expiry reached')
   -- The live Guardian patrol moves during expiry. Pick a visible fixture
   -- position from fixed interior points, retaining real source LOS/range checks.
   local chosen=nil
   for _,offset in ipairs({Vector3.new(8,3,8),Vector3.new(10,3,-4),Vector3.new(10,3,0),Vector3.new(12,3,-5)})do
    local point=f.base+offset
    local clearSensors=true
    for _,part in ipairs(sensors:GetChildren())do
     if part.Name=='CastleDefense_SENSOR'and(part.Position-point).Magnitude<=30 then clearSensors=false end
    end
    local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
    ray.FilterDescendantsInstances={f.guardian,character}
    local origin=f.guardian.PrimaryPart.Position
    if clearSensors and(point-origin).Magnitude<17 and workspace:Raycast(origin,point-origin,ray)==nil then
     chosen=point;break
    end
   end
   check(chosen~=nil,'expired contrast has unobstructed original Guardian LOS')
   targetPoint=chosen
   print('TRACE\tEXPIRED_TARGET\t'..vectorText(targetPoint)..'\tGUARDIAN\t'..vectorText(f.guardian.PrimaryPart.Position))
  elseif MODE=='fake_carrier_attribute' then
   player:SetAttribute('EGGRUMBLE_CarryingEgg',true)
   equal(castle.heldEggs,0,'false read-only carry attribute does not create an egg')
  end
 end
 local victim=humanoid
 if MODE=='same_team' then
  check(teammate~=second and teammate.UserId==45,'distinct same-team human')
  check(session.isCurrentHuman(teammate),'actual current teammate membership')
  check(session.rules.castles['43'].team==session.rules.castles['45'].team,'actual Host assigns allied teams')
  teammate.Character:FindFirstChild('HumanoidRootPart').CFrame=CFrame.new(targetPoint,f.guardian.PrimaryPart.Position)
  victim=teammate.Character:FindFirstChildOfClass('Humanoid')
 elseif MODE=='inactive' then
  -- PlayerRemoving is fired while the avatar/object is still inspectable.
  -- Host membership, not a test-written castle/phase flag, rejects the old player.
  Players.PlayerRemoving:Fire(player)
  check(not session.isCurrentHuman(player),'real Host removed current membership')
  check(session.rules.phase=='ACTIVE','second real human keeps match active')
  rootPart.CFrame=CFrame.new(targetPoint,f.guardian.PrimaryPart.Position)
 else
  rootPart.CFrame=CFrame.new(targetPoint,f.guardian.PrimaryPart.Position)
 end
 local beforeHP=victim.Health
 local beforeCalls=#guardianDamageFilters
 local beforeRays=#queryTrace
 local began=now
 advanceTo(now+2.01)
 local calls=0
 for index=beforeCalls+1,#guardianDamageFilters do
  local row=guardianDamageFilters[index]
  if row.victim==victim then
   calls+=1
   check(row.kind=='NEUTRAL'and row.damage==GUARDIAN_EXPECT.damage,'original selected Guardian damage/filter path')
  end
 end
 local rays=0
 for index=beforeRays+1,#queryTrace do
  local row=queryTrace[index]
  if row.source=='CastleGuardianRuntime' then rays+=1 end
 end
 local lost=beforeHP-victim.Health
 local stealthUntil=player:GetAttribute('EGGRUMBLE_StealthUntil')or 0
 print('OBSERVATION\t'..GUARDIAN_ROLE..'\t'..MODE..'\tHP_BEFORE\t'..beforeHP..'\tHP_AFTER\t'..victim.Health
  ..'\tFILTER_CALLS\t'..calls..'\tTARGET_RAYS\t'..rays..'\tAT\t'..began..'\tEND\t'..now
  ..'\tSTEALTH_UNTIL\t'..stealthUntil..'\tHELD\t'..castle.heldEggs)
 if (MODE=='hidden' or MODE=='fake_carrier_attribute')and GUARDIAN_ROLE~='NINJA' then
  check(stealthUntil>now,'entire observation window is within real NINJA stealth')
  equal(castle.heldEggs,0,'real authoritative carrier state stays empty')
  equal(lost,0,'GUARDIAN_MUST_NOT_TARGET_STEALTH_NONCARRIER')
  equal(calls,0,'hidden noncarrier never enters original Guardian damage filter')
 elseif MODE=='same_team'or MODE=='inactive'then
  equal(lost,0,'original team/current-membership rejection remains effective')
  equal(calls,0,'no Guardian damage to excluded player')
 else
  equal(lost,GUARDIAN_EXPECT.damage,'visible/revealed/expired enemy or intended NINJA detection receives one original attack')
  equal(calls,1,'one original Guardian attack through real Invul filter')
 end
 return 'real Host/Rules/Combat/Guardian; API-fixture target selection only'
end)
print('CASE\tGUARDIAN_STEALTH_'..GUARDIAN_ROLE..'_'..MODE..'\t'..(if ok then 'PASS'else 'FAIL')..'\t'..tostring(reason):gsub('\n',' '))
if not ok then error(reason,0)end
