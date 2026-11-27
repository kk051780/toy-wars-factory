do
local FLAG='P0D_ENABLE_PRIVATE_WARRIOR_COMBO_001'
local FIRE='P0D_ENABLE_PRIVATE_WARRIOR_COMBO_002'
local function slots()
 local deck={}
 for _,item in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do
  local name=item:GetAttribute('EGGRUMBLE_InternalToolId')
  local slot=type(name)=='string' and name:match('^EGGRUMBLE_SKILL_(%u)_')
  if slot then deck[slot]=item end
 end
 return deck
end
local function start(sequence)
 local stand=scenes:FindFirstChild('ROLE_WARRIOR')
 trigger(player,stand,'職業選択')
 for _,select in ipairs(sequence) do trigger(player,stand,select) end
 return ready('PRIVATE_WARRIOR_SKY','WARRIOR'),slots()
end
local function sky()
 local live,deck=start({'天翼を装備'})
 check(live.warriorSkyLoadouts[player.UserId] and not live.warriorLoadouts[player.UserId],'real server freezes only the sky kit')
 check(deck.A and deck.A.Name=='技A・飛翔斬撃' and deck.A:GetAttribute('EGGRUMBLE_FixedAbilityId')==nil,'old A preserved')
 for slot,ability in pairs({B='WARRIOR-020',C='WARRIOR-060',D='COMBO-001'}) do
  check(deck[slot] and deck[slot]:GetAttribute('EGGRUMBLE_FixedAbilityId')==ability,'actual server fixed Tool '..ability)
 end
 return live,deck
end
local function prepare(live,amount)
 local floor=live.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(origin,origin+Vector3.new(1,0,0))
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 rootPart.AssemblyLinearVelocity=Vector3.zero;rootPart.AssemblyAngularVelocity=Vector3.zero
 humanoid.MoveDirection=Vector3.zero
 local models={}
 local horde=live.world:FindFirstChild('NeutralHorde')
 for _=1,42 do
  table.clear(models)
  for _,mob in ipairs(horde:GetChildren()) do
   local h=mob:FindFirstChildOfClass('Humanoid')
   if h and h.Health>0 then
    mob:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
    mob:PivotTo(CFrame.new(origin+Vector3.new(-33,1,45)))
    table.insert(models,{model=mob,hp=h})
   end
  end
  if #models>=amount then break end
  advanceTo(now+.35)
 end
 advanceTo(now+.39)
 check(#models>=amount,'real existing planner spawned enough neutrals')
 check(live.swarm.getRoleGrowthSnapshot(player).energy==100,'real energy baseline')
 return origin,models
end
local function aim(mob,at)
 mob.hp.Health=150
 mob.model:PivotTo(CFrame.new(at))
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function sig() return player:GetAttribute('EGGRUMBLE_SkillCastSignature') end
local function tell(live) return live.world:FindFirstChild('EGGRUMBLE_WarriorSkyFanTell') end
local function wing(live) return live.world:FindFirstChild('EGGRUMBLE_WarriorWingLeft') end
local function wall(live,at,size)
 local part=Instance.new('Part');part.Size=size;part.CFrame=CFrame.new(at)
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=live.world
 return part
end
local function old(live)
 local deck=slots()
 check(not (live.warriorSkyLoadouts and live.warriorSkyLoadouts[player.UserId]) and not deck.D,
  'standard Warrior has no optional D')
 check(deck.A.Name=='技A・飛翔斬撃' and deck.B.Name=='技B・槍陣突撃' and deck.C.Name=='技C・神憑き',
  'same exact legacy A/B/C')
end

function growthCases.sky_combo()
 local live=sky()
 local origin,mobs=prepare(live,4)
 local land=origin+Vector3.new(4.8,1,0)
 aim(mobs[1],land+Vector3.new(2.5,0,-1.7))
 aim(mobs[2],land+Vector3.new(4.4,0,2.85))
 aim(mobs[3],land+Vector3.new(6.2,0,0))
 aim(mobs[4],land+Vector3.new(0,0,3))
 local enemy=live.rules.castles[tostring(second.UserId)]
 local enemyHP,humanHP=enemy.hp,secondHumanoid.Health
 local t=now
 activate(player,'D')
 local accepted=sig()
 check(accepted:match('^WARRIOR:D:') and energy(live)==20 and rootPart.Anchored and wing(live),'actual Tool D starts E80 flight')
 for _,id in ipairs({'COMBO-001','WARRIOR-020','WARRIOR-060'}) do
  check(live.swarm.tryRoleGrowthCast(player,'WARRIOR',1,1,{[id]=1})==nil,'one existing authority owns deadline '..id)
 end
 advanceTo(t+.38)
 check(rootPart.Position.Y-origin.Y>3.75 and rootPart.Position.Y-origin.Y<=4.01 and not tell(live),'physical S0 ascent and no airborne warning or strike')
 activate(player,'A');activate(player,'B');activate(player,'C')
 check(sig()==accepted and mobs[1].hp.Health==150,'other role Tools cannot sneak in an airborne strike')
 advanceTo(t+.79)
 check(rootPart.Anchored and not tell(live),'no rain warning until exact duration completes')
 while not tell(live) and now<t+.92 do advanceTo(now+.001) end
 local observedWarn=now
 check(tell(live) and not rootPart.Anchored and math.abs(rootPart.Position.Y-origin.Y)<.1,'legal settled ground starts fan warning')
 check(#tell(live):GetChildren()==3,'S0 three visual blades independent of actual hit count')
 for index=1,3 do
  local params=RaycastParams.new()
  params.FilterType=Enum.RaycastFilterType.Exclude
  params.FilterDescendantsInstances={character,mobs[index].model};params.RespectCanCollide=true
  local from=rootPart.Position+Vector3.new(0,1,0)
  local target=mobs[index].model.PrimaryPart.Position+Vector3.new(0,1,0)
  check(not workspace:Raycast(from,target-from,params),'all three in-fan neutral pose lanes are open before testing S0 cap')
 end
 advanceTo(observedWarn+.998)
 check(tell(live) and mobs[1].hp.Health==150 and mobs[2].hp.Health==150,'one full second of post-landing warning')
 local intended={[mobs[1].model]=true,[mobs[2].model]=true,[mobs[3].model]=true,[mobs[4].model]=true}
 for _,spawned in ipairs(live.world:FindFirstChild('NeutralHorde'):GetChildren()) do
  if spawned.PrimaryPart and not intended[spawned] then
   spawned:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
   spawned:PivotTo(CFrame.new(origin+Vector3.new(-33,1,45)))
  end
 end
 advanceTo(observedWarn+1.003)
 check(not tell(live) and mobs[1].hp.Health==106 and mobs[2].hp.Health==106
  and mobs[3].hp.Health==150 and mobs[4].hp.Health==150,
  'two actual warned in-fan hits: '..mobs[1].hp.Health..','..mobs[2].hp.Health..','..mobs[3].hp.Health..','..mobs[4].hp.Health
   ..' still warned='..tostring(tell(live)~=nil))
 check(enemy.hp==enemyHP and secondHumanoid.Health==humanHP and live.swarm.getTotal()==0,'no new castle/human damage or phantom KO')
 return 'real D moves then grounds, gives one second fan preview, and hits at most two S0 neutrals'
end

function growthCases.sky_rain_cover()
 local live=sky()
 local origin,mobs=prepare(live,4)
 local launch=origin+Vector3.new(0,1,0)
 aim(mobs[1],launch+Vector3.new(2,0,0))
 aim(mobs[2],launch+Vector3.new(4,0,3))
 aim(mobs[3],launch+Vector3.new(5,0,-3))
 aim(mobs[4],launch+Vector3.new(7.2,0,0))
 local t=now
 activate(player,'B')
 check(sig():match('^WARRIOR:B:') and energy(live)==50 and tell(live) and not rootPart.Anchored,'standalone B keeps ground E50 contract')
 advanceTo(t+.3)
 wall(live,origin+Vector3.new(1.2,0,0),Vector3.new(.18,9,.35))
 aim(mobs[3],launch+Vector3.new(1,0,-4))
 advanceTo(t+.999)
 check(mobs[2].hp.Health==150,'standalone rain cannot release early')
 advanceTo(t+1.01)
 check(mobs[1].hp.Health==150 and mobs[2].hp.Health==106 and mobs[3].hp.Health==150 and mobs[4].hp.Health==150,
  'late wall, sidestep out of exact fan and 7.2 stud target each remain safe')
 return 'actual grounded standalone B uses fixed reach, late LOS and current target pose'
end

function growthCases.sky_flight_only()
 local live=sky()
 local origin,mobs=prepare(live,1)
 aim(mobs[1],origin+Vector3.new(8,1,0))
 local t=now
 activate(player,'C')
 check(sig():match('^WARRIOR:C:') and energy(live)==55 and rootPart.Anchored,'standalone flight begins E45')
 advanceTo(t+.79)
 check(mobs[1].hp.Health==150 and not tell(live),'standalone neutral wave cannot fire mid-air')
 advanceTo(t+.9)
 check(not rootPart.Anchored and mobs[1].hp.Health==138 and not tell(live),'one actual light sword wave at legal landing, no rain')
 return 'standalone C uses checked flight then its existing-role neutral landing wave'
end

local function interrupt(kind)
 local live=sky()
 local origin,mobs=prepare(live,1)
 aim(mobs[1],origin+Vector3.new(8,1,0))
 local t=now
 if kind=='carry_start' then
  live.rules.castles[tostring(player.UserId)].heldEggs=1
  activate(player,'D')
  live.rules.castles[tostring(player.UserId)].heldEggs=0
  check(not wing(live) and energy(live)==100,'carry start rejected before debit')
 else
  activate(player,'D')
  check(energy(live)==20,'real D paid before interruption')
  local inFlight=kind=='wall' or kind=='egg'
  advanceTo(t+(if inFlight then .25 else .95))
  if kind=='wall' then wall(live,origin+Vector3.new(3.8,2,0),Vector3.new(.2,15,20))
  elseif kind=='egg' then live.rules.castles[tostring(player.UserId)].heldEggs=1
  elseif kind=='off' then workspace:SetAttribute(FLAG,false);drainDeferred();old(live)
  elseif kind=='avatar' then player.CharacterRemoving:Fire(character);player.Character=Instance.new('Model')
  elseif kind=='round' then
   live.rules.phase='FINISHED';live.world:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED');drainDeferred()
  end
 end
 advanceTo(t+2.0)
 check(not wing(live) and not tell(live) and not rootPart.Anchored and mobs[1].hp.Health==150,
  'reject or interrupt leaves no late damage/anchor/cue: '..kind)
 return 'real sky cast cannot release after '..kind
end
for _,kind in ipairs({'carry_start','egg','wall','off','avatar','round'}) do
 growthCases['sky_negative_'..kind]=function() return interrupt(kind) end
end

function growthCases.sky_flag_independent()
 workspace:SetAttribute(FIRE,false);drainDeferred()
 local live=sky()
 check(player:GetAttribute('EGGRUMBLE_LobbyWarriorSkyLoadoutName')~=nil and not live.warriorLoadouts[player.UserId],
  'G works when F is disabled, through its own still-guarded prompt')
 return 'separate canonical prompt authorizes sky while the fire feature is off'
end

function growthCases.sky_to_fire()
 local live,deck=start({'天翼を装備','装備する'})
 check(live.warriorLoadouts[player.UserId] and not live.warriorSkyLoadouts[player.UserId]
  and deck.D:GetAttribute('EGGRUMBLE_FixedAbilityId')=='COMBO-002','legacy F selects its own kit after G')
 return 'real existing F remains reachable with original metadata after new G selection'
end

function growthCases.sky_physical_parent_off()
 local live=start({})
 old(live)
 return 'exact previous source retains unselected physical Warrior A/B/C'
end
end
