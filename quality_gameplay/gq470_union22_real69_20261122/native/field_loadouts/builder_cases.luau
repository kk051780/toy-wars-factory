do
local FLAG='P0D_ENABLE_PRIVATE_BUILDER_COMBO_013'
local function checkKit(live)
 check(live.builderFlightLoadouts[player.UserId],'actual server copied Builder kit into its round')
 local names={}
 for _,item in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do names[item.Name]=item end
 check(names['技A・電磁射撃'] and names['技A・電磁射撃']:GetAttribute('EGGRUMBLE_FixedAbilityId')==nil,'untouched A remains')
 for _,row in ipairs({{'技B・連装砲','BUILDER-018'},{'技C・星環飛行艇','BUILDER-040'},{'技D・星環空砲','COMBO-013'}}) do
  check(names[row[1]] and names[row[1]]:GetAttribute('EGGRUMBLE_FixedAbilityId')==row[2],'real Tool ID '..row[2])
 end
end
local function kit()
 local stand=scenes:FindFirstChild('ROLE_BUILDER')
 trigger(player,stand,'職業選択')
 trigger(player,stand,'装備する')
 check(player:GetAttribute('EGGRUMBLE_LobbyBuilderLoadoutName')=='連装砲・星環飛行艇・星環空砲','real opt-in')
 local live=ready('PRIVATE_BUILDER_FLIGHT','BUILDER')
 checkKit(live)
 return live
end
local function moveHere(at)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
end
local function prepare(live,count)
 local floor=live.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 moveHere(origin)
 rootPart.AssemblyLinearVelocity=Vector3.zero
 rootPart.AssemblyAngularVelocity=Vector3.zero
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false
 humanoid.PlatformStand=false
 humanoid.MoveDirection=Vector3.zero
 local horde=live.world:FindFirstChild('NeutralHorde')
 local mobs={}
 for _=1,42 do
  table.clear(mobs)
  for _,model in ipairs(horde:GetChildren()) do
   local hp=model:FindFirstChildOfClass('Humanoid')
   if hp and hp.Health>0 then
    model:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
    model:PivotTo(CFrame.new(origin+Vector3.new(-40,0,25)))
    table.insert(mobs,{hp=hp,model=model})
   end
  end
  if #mobs>=count then break end
  advanceTo(now+.35)
 end
 check(#mobs>=count,'real planner spawns requested neutral models')
 advanceTo(now+.39)
 local snapshot=live.swarm.getRoleGrowthSnapshot(player)
 check(snapshot and snapshot.role=='BUILDER' and snapshot.stage==0 and snapshot.energy==100,'current server role state')
 return origin,mobs
end
local function target(mob,position,hp)
 mob.hp.Health=hp or 96
 mob.model:PivotTo(CFrame.new(position))
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function sig() return player:GetAttribute('EGGRUMBLE_SkillCastSignature') end
local function turret(live) return live.world:FindFirstChild('EGGRUMBLE_BuilderTwinCannon') end
local function createWall(live,point,size)
 local wall=Instance.new('Part')
 wall.CFrame=CFrame.new(point);wall.Size=size;wall.Anchored=true;wall.CanCollide=true;wall.CanQuery=true
 wall.Parent=live.world
 return wall
end

function growthCases.builder_combo()
 local live=kit()
 local origin,mobs=prepare(live,3)
 local first,secondTarget,extra=mobs[1],mobs[2],mobs[3]
 local muzzle=origin+Vector3.new(13.8,.65,0)
 target(first,muzzle+Vector3.new(4,0,0))
 target(secondTarget,muzzle+Vector3.new(6,0,1.6))
 target(extra,muzzle+Vector3.new(7,0,2))
 local castle=live.rules.castles[tostring(second.UserId)]
 local castleHP=castle.hp
 local opposingHP=secondHumanoid.Health
 local t=now
 activate(player,'D')
 local cast=sig()
 check(cast and cast:match('^BUILDER:D:') and energy(live)==20 and rootPart.Anchored,'real D begins paid E80 flight')
 for ability,delay in pairs({['COMBO-013']=40,['BUILDER-018']=24,['BUILDER-040']=32}) do
  check(live.swarm.tryRoleGrowthCast(player,'BUILDER',delay,1,{[ability]=delay})==nil,'same state guards '..ability)
 end
 advanceTo(t+.39)
 check(rootPart.Position.Y-origin.Y>3.75 and rootPart.Position.Y-origin.Y<=4.01,
  'actual avatar in its fixed S0 flight envelope')
 activate(player,'A');activate(player,'B');activate(player,'C')
 check(sig()==cast and not turret(live) and first.hp.Health==96,'no active attacks or cannon during flight')
 advanceTo(t+.79)
 check(rootPart.Anchored and not turret(live),'no early attack before flight time')
 advanceTo(t+.93)
 local rig=turret(live)
 check(rig and not rootPart.Anchored and math.abs(rootPart.Position.Y-origin.Y)<.07,'same real flight solver lands before placement')
 local beams=0
 for _,child in ipairs(rig:GetChildren()) do if child:IsA('Beam') then beams+=1 end end
 check(beams==2 and first.hp.Health==96 and secondTarget.hp.Health==96,'real two warnings before shots')
 advanceTo(t+1.46)
 check(first.hp.Health==96,'full .7 seconds after landing before first hit')
 advanceTo(t+1.62)
 check(first.hp.Health==82 and secondTarget.hp.Health==96 and extra.hp.Health==96,'first real neutral shot exactly -14')
 advanceTo(t+2.4)
 check(first.hp.Health==82 and secondTarget.hp.Health==82 and extra.hp.Health==96,'second shot uses distinct neutral and same S0 cap')
 check(castle.hp==castleHP and secondHumanoid.Health==opposingHP and live.swarm.getTotal()==0,
  'cast does not write enemy player, castle damage or false kills')
 advanceTo(t+5)
 check(not turret(live),'donor four-second placement lifetime ends')
 return 'real air-to-ground D charges once and uses two bounded original-author timed neutral HP shots'
end

function growthCases.builder_cannon_ko()
 local live=kit()
 local origin,mobs=prepare(live,1)
 local mob=mobs[1]
 target(mob,origin+Vector3.new(14,.65,-1.1),12)
 local t=now
 activate(player,'B')
 check(sig():match('^BUILDER:B:') and energy(live)==60 and turret(live) and not rootPart.Anchored,'standalone B E40 legal ground deployment')
 advanceTo(t+.69)
 check(mob.hp.Health==12,'tell protects neutral before first pulse')
 advanceTo(t+.76)
 check(mob.hp.Health==0 and live.swarm.getTotal()==1,'actual neutral Humanoid death credited once by existing Swarm')
 advanceTo(t+1.55)
 check(live.swarm.getTotal()==1,'subsequent shot cannot recredit same target')
 return 'standalone B cannon damages and credits exactly one actual Swarm KO'
end

function growthCases.builder_flight_only()
 local live=kit()
 local origin,mobs=prepare(live,1)
 target(mobs[1],origin+Vector3.new(16,.65,-1.1))
 local t=now
 activate(player,'C')
 check(sig():match('^BUILDER:C:') and energy(live)==55 and rootPart.Anchored,'standalone C E45 starts true controlled flight')
 advanceTo(t+.21)
 humanoid.MoveDirection=Vector3.new(.8,0,.6)
 advanceTo(t+1.56)
 local traveled=rootPart.Position-origin
 check(traveled.Z>1.4 and traveled.Magnitude<=4.82 and not rootPart.Anchored,'native server-observed diagonal steering then grounded release')
 check(not turret(live) and mobs[1].hp.Health==96,'standalone flight has no combat effect')
 return 'standalone flight reuses guarded steering and releases without damage'
end

local function coverage(kind)
 local live=kit()
 local origin,mobs=prepare(live,1)
 local mob=mobs[1]
 target(mob,origin+Vector3.new(15,.65,-3))
 local t=now
 activate(player,'B')
 check(turret(live) and energy(live)==60,'ground lead-in already valid')
 advanceTo(t+.26)
 if kind=='caster' then
  createWall(live,origin+Vector3.new(4,0,-.8),Vector3.new(.16,10,.32))
 else
  moveHere(origin+Vector3.new(0,0,7))
  createWall(live,origin+Vector3.new(12,0,-1.5),Vector3.new(.16,10,.44))
 end
 advanceTo(t+.82)
 check(mob.hp.Health==96 and turret(live),'separate cover rejects target without cancelling a geometrically legal emplacement')
 return 'existing live neutral remains unharmed behind '..kind..' sight cover'
end
function growthCases.builder_cover_caster() return coverage('caster') end
function growthCases.builder_cover_muzzle() return coverage('muzzle') end

local function negative(kind)
 local live=kit()
 local origin,mobs=prepare(live,1)
 target(mobs[1],origin+Vector3.new(19,.65,-1.1))
 local t=now
 local id=tostring(player.UserId)
 if kind=='carry_start' then
  live.rules.castles[id].heldEggs=1
  activate(player,'D');activate(player,'B');activate(player,'C')
  live.rules.castles[id].heldEggs=0
  check(not rootPart.Anchored and not turret(live) and energy(live)==100,'carry denied without a debit')
 else
  activate(player,'D')
  check(rootPart.Anchored and energy(live)==20,'real D legal before disruption')
  advanceTo(t+(if kind=='round' then .93 else .25))
  if kind=='wall' then createWall(live,origin+Vector3.new(3.8,2,0),Vector3.new(.2,15,20))
  elseif kind=='carry' then live.rules.castles[id].heldEggs=1
  elseif kind=='off' then workspace:SetAttribute(FLAG,false);drainDeferred()
  elseif kind=='round' then
   check(turret(live),'test cancels live placement before the first shot')
   live.rules.phase='FINISHED'
   live.world:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED');drainDeferred()
  end
  advanceTo(t+2.44)
 end
 check(not rootPart.Anchored and not turret(live) and not live.world:FindFirstChild('EGGRUMBLE_BuilderThrusterLeft'),
  'invalidated cast releases all owned motion and placement')
 check(mobs[1].hp.Health==96,'cancel does not allow a late hit')
 return 'actual flight or warned ground shots stop on '..kind
end
for _,kind in ipairs({'carry_start','carry','wall','off','round'}) do
 growthCases['builder_negative_'..kind]=function() return negative(kind) end
end

function growthCases.builder_off_parent()
 local stand=scenes:FindFirstChild('ROLE_BUILDER')
 for _,prompt in ipairs(stand:GetChildren()) do
  check(not prompt:IsA('ProximityPrompt') or prompt.ActionText~='装備する','physical parent omits Builder kit prompt')
 end
 ready('PRIVATE_BUILDER_PARENT_OFF','BUILDER')
 local current={}
 for _,item in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do current[item.Name]=true end
 check(current['技A・電磁射撃'] and current['技B・多弾ロケット'] and current['技C・自動砲塔'] and not current['技D・星環空砲'],
  'physical rollback preserves original Builder A/B/C')
 return 'exact physical parent keeps old Builder Tools and no D'
end
end
