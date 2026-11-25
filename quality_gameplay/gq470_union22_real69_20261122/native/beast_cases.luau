-- Actual Host prompts -> real ZOMBIE conversion -> real BEAST Tool/loop.
-- The world/physics APIs are bounded fixtures, not Studio evidence.
local total,failed=0,0
local function expect(name,ok,detail)
 total+=1;if not ok then failed+=1 end
 print('CASE\t'..name..'\t'..(ok and 'PASS' or 'FAIL')..'\t'..(detail or ''))
end
local function pointText(v)return string.format('%.3f,%.3f,%.3f',v.X,v.Y,v.Z)end
local function trigger(actor,part,verb)
 assert(part,'prompt part '..verb)
 local prompt=nil
 for _,c in ipairs(part:GetChildren())do
  if c:IsA('ProximityPrompt')and c.ActionText==verb then prompt=c end
 end
 assert(prompt and prompt.Enabled,'enabled prompt '..verb)
 actor.Character:FindFirstChild('HumanoidRootPart').CFrame=CFrame.new(part.Position+Vector3.new(0,0,1))
 ProximityPromptService.PromptTriggered:Fire(prompt,actor);prompt.Triggered:Fire(actor)
end
local function activate(actor,slot)
 local tool=nil
 for _,container in ipairs({actor:FindFirstChildOfClass('Backpack'),actor.Character})do
  for _,item in ipairs(container:GetChildren())do
   local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
   if item:IsA('Tool')and type(id)=='string'and id:match('^EGGRUMBLE_SKILL_'..slot..'_')then
    assert(tool==nil,'one current Tool');tool=item
   end
  end
 end
 assert(tool,'actual Tool '..slot)
 tool.Parent=actor.Character;tool.Activated:Fire()
end
local scenes=workspace:FindFirstChild('EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW')
trigger(player,scenes:FindFirstChild('ROLE_BEAST'),'職業選択')
trigger(second,scenes:FindFirstChild('ROLE_NINJA'),'職業選択')
trigger(third,scenes:FindFirstChild('ROLE_ZOMBIE'),'職業選択')
trigger(fourth,scenes:FindFirstChild('ROLE_ZOMBIE'),'職業選択')
trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
trigger(third,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
trigger(fourth,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
advanceTo(now+12.01)
assert(#capturedSessions==1,'one actual Host session')
local session=capturedSessions[1]
assert(session.rules.phase=='ACTIVE','real READY -> ACTIVE')
assert(session.rules.castles['42'].team==session.rules.castles['44'].team,'real BEAST/ZOMBIE teammates')
assert(session.rules.castles['43'].team~=session.rules.castles['42'].team,'real NINJA opponent')
assert(session.rules.castles['45'].team~=session.rules.castles['42'].team,'real ZOMBIE opponent')
local floor=session.world:FindFirstChild('TacticalBattlefield')
local at=nil
local zoneParams=OverlapParams.new();zoneParams.FilterType=Enum.RaycastFilterType.Exclude
zoneParams.FilterDescendantsInstances={character,secondCharacter,thirdCharacter,fourthCharacter}
zoneParams.RespectCanCollide=true
for _,x in ipairs({0,100,-100,200,-200,300,-300})do
 for _,z in ipairs({0,100,-100,200,-200})do
  local candidate=floor.Position+Vector3.new(x,floor.Size.Y*.5+4,z)
  local overlaps=workspace:GetPartBoundsInBox(CFrame.new(candidate),Vector3.new(40,5,70),zoneParams)
  if x==0 and z==0 then
   for _,part in ipairs(overlaps)do print('TRACE\tSETUP_OBSTACLE\t'..part.Name..'\t'..pointText(part.Position)..'\t'..pointText(part.Size))end
   print('TRACE\tFLOOR\t'..pointText(floor.Position)..'\t'..pointText(floor.Size))
  end
  if #overlaps==0 then
   at=candidate;break
  end
 end
 if at then break end
end
assert(at,'fixture setup requires physically clear arena section')
print('TRACE\tCLEAR_SETUP_ZONE\t'..pointText(at))
local far=at+Vector3.new(1200,30,1200)
rootPart.CFrame=CFrame.new(far)
secondRoot.CFrame=CFrame.new(far+Vector3.new(100,0,0))
thirdRoot.CFrame=CFrame.new(at)
fourthRoot.CFrame=CFrame.new(far+Vector3.new(150,0,0))
local horde=session.world:FindFirstChild('NeutralHorde')
local chosen,opponent,visible=nil,nil,nil
for _=1,20 do
 advanceTo(now+.2)
 for _,m in ipairs(horde:GetChildren())do
  local h=m:FindFirstChildOfClass('Humanoid')
  if h and h.Health>0 and m:GetAttribute('EGGRUMBLE_NeutralSpecies')~='BABY_GOLEM' then
   if not chosen then chosen=m elseif m~=chosen and not opponent then opponent=m elseif m~=chosen and m~=opponent then visible=m end
  end
 end
 if chosen and opponent and visible then break end
end
assert(chosen and opponent and visible,'three actual Swarm-spawned neutrals')
-- Control position inputs, without patching game functions or neutral HP.
for _,m in ipairs(horde:GetChildren())do
 if m.PrimaryPart then m:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))end
end
chosen:PivotTo(CFrame.new(at+Vector3.new(0,0,-14)))
thirdRoot.CFrame=CFrame.new(at,chosen.PrimaryPart.Position)
local ch=chosen:FindFirstChildOfClass('Humanoid')
local healthBefore=ch.Health
activate(third,'A')
print('TRACE\tCURSE_FIRST\t'..healthBefore..'\t'..ch.Health..'\t'..tostring(chosen:GetAttribute('EGGRUMBLE_NeutralSeals')))
print('TRACE\tCASTER\t'..tostring(third:GetAttribute('EGGRUMBLE_Role'))..'\t'..tostring(third:GetAttribute('EGGRUMBLE_SkillCastSignature'))..'\t'..tostring(session.isCurrentHuman(third))..'\t'..thirdHumanoid.Health..'\t'..pointText(thirdRoot.Position)..'\t'..pointText(chosen.PrimaryPart.Position))
for i=math.max(1,#queryTrace-6),#queryTrace do
 local q=queryTrace[i];print('TRACE\tLAST_RAY\t'..q.source..'\t'..q.line..'\t'..(q.hit and q.hit.Name or 'CLEAR')..'\t'..pointText(q.origin)..'\t'..pointText(q.delta))
end
advanceTo(now+.92)
-- The movement API fixtures may move the original neutral between casts.
thirdRoot.CFrame=CFrame.new(chosen.PrimaryPart.Position+Vector3.new(0,0,14),chosen.PrimaryPart.Position)
activate(third,'A')
assert(chosen:GetAttribute('EGGRUMBLE_NeutralFriendlyOwnerId')=='44','real two-hit Swarm/Curse conversion')
expect('REAL_TEAM_CHARM_CREATED',ch.Health>0 and ch.Health<healthBefore,'same actual neutral; owner44; HP '..ch.Health)
thirdRoot.CFrame=CFrame.new(far+Vector3.new(50,0,50))
chosen:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))
opponent:PivotTo(CFrame.new(at+Vector3.new(0,0,-14)))
fourthRoot.CFrame=CFrame.new(at,opponent.PrimaryPart.Position)
local oh=opponent:FindFirstChildOfClass('Humanoid')
local opponentHealthBefore=oh.Health
activate(fourth,'A')
advanceTo(now+.92)
fourthRoot.CFrame=CFrame.new(opponent.PrimaryPart.Position+Vector3.new(0,0,14),opponent.PrimaryPart.Position)
activate(fourth,'A')
assert(opponent:GetAttribute('EGGRUMBLE_NeutralFriendlyOwnerId')=='45','real opponent two-hit conversion')
expect('REAL_OPPONENT_CHARM_CREATED',oh.Health>0 and oh.Health<opponentHealthBefore,'same actual neutral; owner45; HP '..oh.Health)
fourthRoot.CFrame=CFrame.new(far+Vector3.new(150,0,0))
rootPart.CFrame=CFrame.new(at,at+Vector3.new(0,0,-1))
for _,m in ipairs(horde:GetChildren())do
 if m.PrimaryPart then m:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))end
end
chosen:PivotTo(CFrame.new(at+Vector3.new(0,0,14)))
visible:PivotTo(CFrame.new(at+Vector3.new(0,0,24)))
local originalVisibleHp=visible:FindFirstChildOfClass('Humanoid').Health
activate(player,'B')
advanceTo(now)
local pet=session.world:FindFirstChild('EGGRUMBLE_BeastEscort_42')
assert(pet and pet.PrimaryPart,'real BEAST Skill B created companion')
assert(#beastMoves>0,'actual Beast task called Humanoid.MoveTo')
local command=beastMoves[#beastMoves]
expect('CHARMED_ALLY_DOES_NOT_STARVE_HOSTILE_TARGET',
 (command.target-visible.PrimaryPart.Position).Magnitude<.001,
 'MoveTo='..pointText(command.target)..'; charm='..pointText(chosen.PrimaryPart.Position)..'; hostile='..pointText(visible.PrimaryPart.Position))
expect('INITIAL_BLAST_DID_NOT_CONFOUND_BACKWARD_TARGET',visible:FindFirstChildOfClass('Humanoid').Health==originalVisibleHp,'original BEAST blast faces away')

-- Opponent-owned converted neutrals are also excluded by the existing Swarm
-- damage authority, so they must not consume the companion's target choice.
chosen:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))
opponent:PivotTo(CFrame.new(at+Vector3.new(0,0,14)))
visible:PivotTo(CFrame.new(at+Vector3.new(0,0,24)))
local before=#beastMoves
advanceTo(now+.351)
command=beastMoves[#beastMoves]
expect('OPPONENT_CHARM_DOES_NOT_STARVE_HOSTILE_TARGET',#beastMoves>before and (command.target-visible.PrimaryPart.Position).Magnitude<.001,
 'MoveTo='..pointText(command.target)..'; opponent charm='..pointText(opponent.PrimaryPart.Position)..'; hostile='..pointText(visible.PrimaryPart.Position))

-- Keep the existing pet. Generate real NINJA stealth through its existing Tool.
chosen:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))
opponent:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))
secondRoot.CFrame=CFrame.new(at+Vector3.new(15,0,20),at+Vector3.new(15,0,-10))
activate(second,'B')
assert((second:GetAttribute('EGGRUMBLE_StealthUntil')or 0)>now,'actual Ninja B produced stealth')
secondRoot.CFrame=CFrame.new(at+Vector3.new(0,0,14))
visible:PivotTo(CFrame.new(at+Vector3.new(0,0,24)))
before=#beastMoves
advanceTo(now+.351)
assert(#beastMoves>before,'second actual Beast loop')
command=beastMoves[#beastMoves]
expect('STEALTH_ENEMY_DOES_NOT_REVEAL_OR_STARVE_VISIBLE_TARGET',
 (command.target-visible.PrimaryPart.Position).Magnitude<.001,
 'MoveTo='..pointText(command.target)..'; hidden='..pointText(secondRoot.Position)..'; visible='..pointText(visible.PrimaryPart.Position)..'; original stealthUntil='..second:GetAttribute('EGGRUMBLE_StealthUntil'))

-- The original server Rules transfers a real enemy egg. Carrier reveal remains.
dependencies.EGGRUMBLE_CastleMatchRules.takeEggs(session.rules,'43',1,'42')
assert(session.rules.castles['43'].heldEggs==1,'real Rules cargo')
visible:PivotTo(CFrame.new(far+Vector3.new(250,0,250)))
before=#beastMoves
advanceTo(now+.351)
assert(#beastMoves>before,'carrier loop')
command=beastMoves[#beastMoves]
expect('STEALTH_CARRIER_REMAINS_TARGET',(command.target-secondRoot.Position).Magnitude<.001,'actual heldEggs=1')

-- A closer ordinary teammate must still be excluded by existing team rules.
-- Isolate this control from unrelated neutrals spawned during earlier steps.
for _,m in ipairs(horde:GetChildren())do
 if m.PrimaryPart then m:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))end
end
thirdRoot.CFrame=CFrame.new(at+Vector3.new(0,0,11))
secondRoot.CFrame=CFrame.new(at+Vector3.new(0,0,12))
before=#beastMoves
advanceTo(now+.351)
command=beastMoves[#beastMoves]
expect('ORDINARY_TEAMMATE_REMAINS_EXCLUDED',#beastMoves>before and (command.target-secondRoot.Position).Magnitude<.001,'MoveTo='..pointText(command.target)..'; RED ally44='..pointText(thirdRoot.Position)..'; BLUE enemy43='..pointText(secondRoot.Position))

-- Real owner death retires Curse state. The same former ally becomes a normal
-- neutral target again without changing its tag or policy tables in the test.
thirdHumanoid:TakeDamage(thirdHumanoid.Health)
thirdRoot.CFrame=CFrame.new(far+Vector3.new(50,0,50))
secondRoot.CFrame=CFrame.new(far+Vector3.new(100,0,0))
for _,m in ipairs(horde:GetChildren())do
 if m.PrimaryPart then m:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))end
end
chosen:PivotTo(CFrame.new(at+Vector3.new(0,0,12)))
visible:PivotTo(CFrame.new(at+Vector3.new(0,0,24)))
before=#beastMoves
advanceTo(now+.8)
command=beastMoves[#beastMoves]
expect('REAL_CHARM_RELEASE_RESTORES_NEUTRAL_TARGET',chosen:GetAttribute('EGGRUMBLE_NeutralFriendlyOwnerId')==nil and ch.Health>0 and #beastMoves>before and (command.target-chosen.PrimaryPart.Position).Magnitude<.001,
 'MoveTo='..pointText(command.target)..'; released='..pointText(chosen.PrimaryPart.Position)..'; charm owner='..tostring(chosen:GetAttribute('EGGRUMBLE_NeutralFriendlyOwnerId')))

-- Retain a disconnected Player in this API fixture's enumeration to prove the
-- actual Host membership fence rejects stale instances even with a live avatar.
for _,m in ipairs(horde:GetChildren())do
 if m.PrimaryPart then m:PivotTo(CFrame.new(far+Vector3.new(200,0,200)))end
end
visible:PivotTo(CFrame.new(at+Vector3.new(0,0,16)))
fourthRoot.CFrame=CFrame.new(at+Vector3.new(0,0,12))
Players.PlayerRemoving:Fire(fourth);fourth.Parent=nil
assert(not session.isCurrentHuman(fourth),'actual Host revoked member')
assert(session.rules.phase=='ACTIVE','no lifecycle or phase bypass')
before=#beastMoves
advanceTo(now+.351)
command=beastMoves[#beastMoves]
expect('STALE_HUMAN_MEMBER_REMAINS_EXCLUDED',#beastMoves>before and (command.target-visible.PrimaryPart.Position).Magnitude<.001,
 'MoveTo='..pointText(command.target)..'; stale='..pointText(fourthRoot.Position)..'; visible='..pointText(visible.PrimaryPart.Position))

-- Existing caster validity must still stop the real pet on owner death.
humanoid:TakeDamage(humanoid.Health)
before=#beastMoves
advanceTo(now+.351)
expect('DEAD_CASTER_RETIRES_COMPANION',pet.Parent==nil and #beastMoves==before,'actual Humanoid death; original Beast validity loop')
expect('NO_GAME_WARNINGS',#warnings==0,table.concat(warnings,';'))
print('RESULT|'..total..'|'..(total-failed)..'|'..failed)
assert(failed==0,'RED_BEAST_FULL_SOURCE_TARGET_SELECTION')
