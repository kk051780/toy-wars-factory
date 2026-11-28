do
local FLAG='P0D_ENABLE_PRIVATE_TRAPPER_RETURN'
local function deck(slot)
 for _,folder in ipairs({player:FindFirstChildOfClass('Backpack'),player.Character}) do
  if folder then
   for _,item in ipairs(folder:GetChildren()) do
    local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
    if type(id)=='string' and id:match('^EGGRUMBLE_SKILL_'..slot..'_') then return item end
   end
  end
 end
 return nil
end
local function move(at,heading)
 rootPart.CFrame=CFrame.lookAt(at,at+(heading or Vector3.new(1,0,0)))
end
local function start(distance, neutral)
 local stand=scenes:FindFirstChild('ROLE_TRAPPER')
 trigger(player,stand,'職業選択')
 trigger(player,stand,'装備する')
 local live=ready('PRIVATE_TRAPPER_RETURN','TRAPPER')
 check(live.trapperGravityLoadouts[player.UserId],'original F opt-in is frozen by real Host')
 for slot,id in pairs({B='TRAPPER-015',C='TRAPPER-036',D='COMBO-010'}) do
  check(deck(slot) and deck(slot):GetAttribute('EGGRUMBLE_FixedAbilityId')==id,'actual Tool identity '..id)
 end
 check(deck('A').Name=='技A・念動衝撃','original A preserved')
 local mob=if neutral then spawnCurrentNeutral(live) else nil
 local floor=live.world:FindFirstChild('TacticalBattlefield')
 local past=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 local current=past+Vector3.new(distance,0,0)
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 rootPart.AssemblyLinearVelocity=Vector3.zero;rootPart.AssemblyAngularVelocity=Vector3.zero
 local function park()
  for _,other in ipairs(live.world:FindFirstChild('NeutralHorde'):GetChildren()) do
   if other.PrimaryPart then
    other:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
    other:PivotTo(CFrame.new(past+Vector3.new(-45,4,26)))
   end
  end
 end
 park();move(past)
 advanceTo(now+1.14)
 park();move(current)
 advanceTo(now+.390)
 park()
 local role=live.swarm.getRoleGrowthSnapshot(player)
 check(role and role.stage==0 and role.energy==100,'real current role sample')
 local sample=live.swarm.trapperReturnSample(player,character,.8)
 check(sample and (sample.entry.position-past).Magnitude<.02,'recorded target is a real past pose')
 check(now-sample.entry.at>=.8 and now-sample.entry.at<=1.23,'exact fixed rewind age and bounded sample tolerance')
 return live,past,current,mob
end
local function get(live,name)
 return live.world:FindFirstChild(name)
end
local function sig()return player:GetAttribute('EGGRUMBLE_SkillCastSignature')end
local function energy(live)return live.swarm.getRoleGrowthSnapshot(player).energy end
local function tell(live)return get(live,'EGGRUMBLE_TrapperReturnTell')end
local function success(live)return get(live,'EGGRUMBLE_TrapperPositionReturned')end
local function wall(live,at,size)
 local part=Instance.new('Part');part.Size=size;part.CFrame=CFrame.new(at)
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=live.world
 return part
end
local function target(live,origin,mob)
 local center=assert(live.swarm.gravityCenter(player,character,origin,origin+Vector3.new(5.5,0,0)))
 local height=2*(mob.PrimaryPart.Size.Y/2.5)
 local before=center+Vector3.new(3.4,height-1.8,0)
 mob:PivotTo(CFrame.new(before))
 local hp=mob:FindFirstChildOfClass('Humanoid');hp.Health=120
 return center,before,hp
end

function growthCases.return_player_only()
 local live,past,current=start(4)
 local castle=live.rules.castles[tostring(player.UserId)]
 local originalPose=rootPart.CFrame.LookVector
 local originalVelocity=Vector3.new(2,0,1)
 rootPart.AssemblyLinearVelocity=originalVelocity
 humanoid.Health=61;castle.hp=castle.hp-31
 local castleHp=castle.hp
 local deadline=live.deadlineLease.start
 local t=now
 activate(player,'C')
 local accepted=sig()
 check(accepted and accepted:match('^TRAPPER:C:') and tell(live) and energy(live)==60,'real standalone C charges just E40')
 check(live.swarm.tryRoleGrowthCast(player,'TRAPPER',1,1,{['TRAPPER-036']=1})==nil,'same ledger deadline is armed')
 advanceTo(t+.179)
 check((rootPart.Position-current).Magnitude<.02 and not success(live),'no visual success or movement before .18 tell')
 advanceTo(t+.181)
 check((rootPart.Position-past).Magnitude<.02 and success(live) and not tell(live),'real current avatar returns to recorded position')
 check(rootPart.CFrame.LookVector:Dot(originalPose)>.999 and (rootPart.AssemblyLinearVelocity-originalVelocity).Magnitude<.001,
  'present heading and momentum preserved')
 check(humanoid.Health==61 and castle.hp==castleHp and live.deadlineLease.start==deadline and castle.heldEggs==0 and live.swarm.getTotal()==0,
  'HP, objective, match time, egg and KO state remain current')
 check(energy(live)<90 and live.swarm.tryRoleGrowthCast(player,'TRAPPER',1,1,{['TRAPPER-036']=1})==nil,
  'real charge remains after position return')
 return 'actual C warns, translates only the same live body and preserves combat and clock state'
end

function growthCases.return_combo()
 local live,past,current,mob=start(4,true)
 local center,before,h=target(live,current,mob)
 local t=now
 activate(player,'D')
 check(sig():match('^TRAPPER:D:') and energy(live)==20 and get(live,'P0D_TRAPPER_GRAVITY_ORB'),'real D shares one E80 payment')
 for _,id in ipairs({'TRAPPER-015','TRAPPER-036','COMBO-010'}) do
  check(live.swarm.tryRoleGrowthCast(player,'TRAPPER',1,1,{[id]=1})==nil,'shared clock armed: '..id)
 end
 advanceTo(t+.301)
 local pulled=mob.PrimaryPart.Position
 check((pulled-center).Magnitude<(before-center).Magnitude and not tell(live),'real neutral is pulled before return')
 advanceTo(t+.619)
 check(not tell(live) and (rootPart.Position-current).Magnitude<.02,'must wait for safe neutral release')
 advanceTo(t+.623)
 check((mob.PrimaryPart.Position-pulled).Magnitude>1 and h.Health==120 and tell(live),'real neutral released before history warning')
 advanceTo(t+.798)
 check((rootPart.Position-current).Magnitude<.02 and not success(live),'return warning duration remains independent')
 advanceTo(t+.804)
 check((rootPart.Position-past).Magnitude<.02 and success(live) and h.Health==120 and live.swarm.getTotal()==0,
  'actual self return only after genuine neutral control and safe release')
 return 'real D uses confirmed pull/release before one shared-cost, real self-position return'
end

local function fail(kind)
 local live,_,current,mob=start(if kind=='range' then 7.2 else 4,kind=='release_wall' or kind=='carry')
 if kind=='range' then
  activate(player,'C');activate(player,'D')
  check(not tell(live) and not success(live) and energy(live)==100,'fixed S0 range rejects before debit')
  return 'outside fixed six-stud range cannot return'
 end
 if kind=='empty' then
  local t=now;activate(player,'D');advanceTo(t+.82)
  check(not success(live) and not tell(live) and energy(live)<45 and (rootPart.Position-current).Magnitude<.02,
   'no fake control receipt when no actual nearby neutral moves')
  return 'empty or failed pull never emits return success'
 end
 if kind=='release_wall' then
  local center=target(live,current,mob)
  local t=now;activate(player,'D');advanceTo(t+.301)
  local capture=mob.PrimaryPart.Position
  check((capture-center).Magnitude<3.4,'actual pull precedes obstacle')
  wall(live,capture+Vector3.new(mob.PrimaryPart.Size.X*.5+.62,0,0),Vector3.new(.22,8,8))
  advanceTo(t+.81)
  check(not tell(live) and not success(live) and (rootPart.Position-current).Magnitude<.02,
   'fully obstructed real neutral release never unlocks the return')
  return 'late solid release fails compound without a return cue or success'
 end
 if kind=='carry' then
  local owner=live.rules.castles[tostring(player.UserId)]
  owner.heldEggs=1;activate(player,'C');activate(player,'D');owner.heldEggs=0
  check(not success(live) and not tell(live) and energy(live)==100,'carrying denies both before debit')
  return 'carrying egg never authorizes either self return'
 end
 local t=now
 activate(player,'C');check(tell(live) and energy(live)==60,'valid return accepted before interference')
 advanceTo(t+.08)
 if kind=='wall' then wall(live,current-Vector3.new(2,0,0),Vector3.new(.18,10,12))
 elseif kind=='avatar' then player.CharacterRemoving:Fire(character);player.Character=Instance.new('Model')
 elseif kind=='off' then
  workspace:SetAttribute(FLAG,false);drainDeferred()
  check(deck('B'):GetAttribute('EGGRUMBLE_FixedAbilityId')=='TRAPPER-015'
   and deck('C').Name=='技C・空間転移' and not deck('D'),'specific rollback restores C/D while real B remains')
 elseif kind=='floor' then
  wall(live,current-Vector3.new(4,2.0,0),Vector3.new(2,.6,2))
 elseif kind=='round' then
  live.rules.phase='FINISHED';live.world:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED');drainDeferred()
 end
 advanceTo(t+.25)
 check(not tell(live) and not success(live) and (rootPart.Position-current).Magnitude<.02,
  'late invalidation removes warning and does not move old avatar: '..kind)
 return 'safe return rechecks current identity, support and sweep: '..kind
end
for _,kind in ipairs({'range','empty','release_wall','carry','wall','floor','avatar','off','round'}) do
 growthCases['return_negative_'..kind]=function()return fail(kind)end
end

local previousGravity=growthCases.gravity_cap_and_release
function growthCases.return_preserves_b()
 workspace:SetAttribute(FLAG,false);drainDeferred()
 return previousGravity()
end
function growthCases.return_physical_parent_off()
 return previousGravity()
end
end
