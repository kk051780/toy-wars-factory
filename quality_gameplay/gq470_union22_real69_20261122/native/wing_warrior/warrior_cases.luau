do
local FLAG='P0D_ENABLE_PRIVATE_WARRIOR_COMBO_002'
local H=150
local function slot(who,name)
 for _,container in ipairs({who:FindFirstChildOfClass('Backpack'),who.Character})do
  for _,item in ipairs(container:GetChildren())do
   local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
   if type(id)=='string'and id:match('^EGGRUMBLE_SKILL_'..name..'_')then return item end
  end
 end
 return nil
end
local function sig()return player:GetAttribute('EGGRUMBLE_SkillCastSignature')end
local function ember(mob)return mob:FindFirstChild('EGGRUMBLE_Ember')end
local function state(session)
 local growth=session.swarm.getRoleGrowthSnapshot(player)
 check(growth and growth.role=='WARRIOR','actual current server role-growth at '..now..' caster HP '..humanoid.Health)
 return growth
end
local function setup(equip)
 local stand=scenes:FindFirstChild('ROLE_WARRIOR')
 trigger(player,stand,'職業選択')
 if equip then
  trigger(player,stand,'装備する')
  check(player:GetAttribute('EGGRUMBLE_LobbyWarriorLoadoutName')=='炎刃・光輪刃・炎輪剣舞','actual optional lobby loadout')
 end
 trigger(second,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 advanceTo(now+12.01)
 local s=capturedSessions[#capturedSessions]
 check(s and s.rules.phase=='ACTIVE' and s.isCurrentHuman(player) and player:GetAttribute('EGGRUMBLE_Role')=='WARRIOR',
  'real Host admits existing Warrior role')
 check(slot(player,'A')~=nil,'original Warrior A is always retained')
 if equip then
  check(s.warriorLoadouts[player.UserId] and slot(player,'B'):GetAttribute('EGGRUMBLE_FixedAbilityId')=='WARRIOR-071'
   and slot(player,'C'):GetAttribute('EGGRUMBLE_FixedAbilityId')=='WARRIOR-016'
   and slot(player,'D'):GetAttribute('EGGRUMBLE_FixedAbilityId')=='COMBO-002' and not slot(second,'D'),
   'Host grants only opted-in Warrior B, C and D')
 else
  check(not slot(player,'D') and slot(player,'B'):GetAttribute('EGGRUMBLE_FixedAbilityId')==nil, 'legacy kit preserved')
 end
 outsideField(s)
 return s
end
local function pose(session,offset)
 local neutral=spawnCurrentNeutral(session)
 local h=neutral:FindFirstChildOfClass('Humanoid')
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(170,20,-115)
 local at=origin+offset+Vector3.new(0,1,0)
 neutral:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 h.Health=H
 rootPart.CFrame=CFrame.lookAt(origin,origin+Vector3.new(1,0,0))
 neutral:PivotTo(CFrame.new(at))
 advanceTo(now+.39)
 neutral:PivotTo(CFrame.new(at))
 for _,m in ipairs(session.world:FindFirstChild('NeutralHorde'):GetChildren())do
  if m~=neutral and m:FindFirstChildOfClass('Humanoid')then
   m:SetAttribute('EGGRUMBLE_NeutralSpeed',0);m:PivotTo(CFrame.new(origin+Vector3.new(-36,10,0)))
  end
 end
 local filters=RaycastParams.new();filters.FilterType=Enum.RaycastFilterType.Exclude
 filters.FilterDescendantsInstances={character,neutral};filters.RespectCanCollide=true
 check(workspace:Raycast(origin+Vector3.new(0,1,0),at-origin,filters)==nil,'expected clear original server hitscan lane')
 return neutral,h,origin,at
end
local function moveUntil(s,mob,origin,untilAt)
 local steps={Vector3.new(0,0,0),Vector3.new(0,0,1),Vector3.new(1,0,1),Vector3.new(1,0,0)}
 mob:PivotTo(CFrame.new(origin+Vector3.new(-36,10,0)))
 local i=0
 while now+.39<untilAt do
  i+=1
  local at=origin+steps[(i-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
  advanceTo(now+.39)
  for _,m in ipairs(s.world:FindFirstChild('NeutralHorde'):GetChildren())do
   if m~=mob and m:FindFirstChildOfClass('Humanoid')then
    m:SetAttribute('EGGRUMBLE_NeutralSpeed',0);m:PivotTo(CFrame.new(origin+Vector3.new(-36,10,0)))
   end
  end
 end
 rootPart.CFrame=CFrame.lookAt(origin,origin+Vector3.new(1,0,0))
 advanceTo(untilAt)
end
function growthCases.warrior_ignite()
 local s=setup(true)
 local mob,h,_,at=pose(s,Vector3.new(4,0,0))
 local t=now
 activate(player,'B')
 check(sig():match('^WARRIOR:B:') and state(s).energy==70 and s.world:FindFirstChild('EGGRUMBLE_WarriorFireTell'),
  'actual Tool B costs exactly E30 and creates a real directed tell')
 advanceTo(t+.179)
 equal(h.Health,H,'ignite cannot hurt before its tell')
 advanceTo(t+.181)
 equal(h.Health,H-36,'first hit spends only the nonreserved P0 damage')
 local cue=ember(mob)
 check(cue and cue:IsA('Highlight'),'actual Swarm owns one burned-neutral mark')
 advanceTo(t+.8)
 check(h.Health<H-36 and h.Health>=H-44 and ember(mob)==cue,'shared .38 tick draws from same original damage budget')
 advanceTo(t+1.62)
 check(ember(mob)==nil,'actual burn status expires')
 check(h.Health>=H-44 and (mob.PrimaryPart.Position-at).Magnitude<.01,'no extra DoT or displacement')
 return 'existing Warrior B emits real tell; one authorized neutral strike plus bounded shared burn, E30 and cleanup'
end
function growthCases.warrior_ring()
 local s=setup(true)
 local mob,h,origin=pose(s,Vector3.new(-2,0,0))
 local before=secondHumanoid.Health
 secondRoot.CFrame=CFrame.new(origin+Vector3.new(1,0,0))
 activate(player,'C')
 check(sig():match('^WARRIOR:C:') and state(s).energy==65,'actual standalone C spends E35')
 equal(h.Health,H-44,'true radial ring hits behind and only once')
 equal(secondHumanoid.Health,before,'enemy hero does not inherit the neutral-only radius')
 advanceTo(now+.48)
 equal(h.Health,H-44,'standalone ring has no repeated pulse')
 check(ember(mob)==nil,'ring without ignition adds no status')
 return 'actual C radial neutral hit including rear at S0, no burn, no extra hit, no hero HP change'
end
function growthCases.warrior_combo()
 local s=setup(true)
 local mob,h,origin=pose(s,Vector3.new(2,0,0))
 local t=now
 activate(player,'D')
 local first=sig()
 check(first:match('^WARRIOR:D:') and state(s).energy==20,'locked compound spends one E80 before warning')
 local tell=s.world:FindFirstChild('EGGRUMBLE_WarriorFireTell')
 check(tell and #tell:GetChildren()==8,'real ring warning marks its committed radius')
 for _,w in ipairs(tell:GetChildren())do check(not w.CanCollide and not w.CanQuery and not w.CanTouch,'warning is non-interactive')end
 activate(player,'D')
 check(sig()==first and state(s).energy==20,'duplicate input neither creates a second tell nor spends')
 advanceTo(t+.799)
 equal(h.Health,H,'actual compound cannot hit before 0.8 seconds')
 advanceTo(t+.801)
 equal(h.Health,H-36,'one immediate damage budget with reserved burn, never a sum of two standalone skills')
 local mark=ember(mob)
 check(mark and tell.Parent==nil and s.world:FindFirstChild('EGGRUMBLE_WarriorFireCut'),'real single pulse and neutral mark')
 advanceTo(t+2.2)
 check(h.Health>=H-44 and h.Health<H-36 and not ember(mob),'expiration keeps the total one hit budget')
 check((rootPart.Position-origin).Magnitude<.01,'attack never moves or empowers the caster')
 return 'actual D has one E80 payment, period .8 warning, one unified pulse and one bounded burn registration'
end
function growthCases.warrior_wall_and_resist()
 local s=setup(true)
 local mob,h,origin,at=pose(s,Vector3.new(2.7,0,0))
 local t=now
 activate(player,'B')
 local wall=Instance.new('Part');wall.Name='NativeWarriorTellWall';wall.Size=Vector3.new(.5,14,14)
 wall.CanCollide=true;wall.CanQuery=true;wall.CFrame=CFrame.new(origin+Vector3.new(1.3,1,0));wall.Parent=s.world
 advanceTo(t+.23)
 equal(h.Health,H,'wall entering during warning blocks actual outgoing neutral damage')
 check(not ember(mob),'blocked target cannot receive a status')
 wall:Destroy()
 moveUntil(s,mob,origin,t+18.01)
 mob:PivotTo(CFrame.new(at));mob:SetAttribute('EGGRUMBLE_NeutralSpecies','BABY_GOLEM')
 activate(player,'B')
 advanceTo(now+.19)
 equal(h.Health,H-44,'existing immune Golem keeps one direct budget without burn reservation')
 check(not ember(mob),'shared Mage immunity is preserved for Warrior')
 return 'actual wall by impact blocks both writes; defensive neutral shares the existing immunity and no burn'
end
function growthCases.warrior_off()
 local s=setup(true)
 local mob,h=pose(s,Vector3.new(2,0,0))
 local d=slot(player,'D')
 local t=now
 activate(player,'D')
 advanceTo(t+.23)
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 check(d.Parent==nil and not slot(player,'D') and not s.warriorLoadouts[player.UserId],
  'Host revokes the real old optional Tool and restores the old inventory')
 check(not s.world:FindFirstChild('EGGRUMBLE_WarriorFireTell'),'OFF immediately clears the pending warning')
 advanceTo(t+1.15)
 equal(h.Health,H,'retired callback cannot hurt or burn')
 check(not ember(mob),'no old status after runtime OFF')
 return 'real live feature-OFF cancels pending attack and restores ordinary Warrior A/B/C'
end
function growthCases.warrior_budget()
 local s=setup(true)
 local mob,_,origin,at=pose(s,Vector3.new(2,0,0))
 local t=now
 activate(player,'D')
 local first=sig()
 moveUntil(s,mob,origin,t+17.98);mob:PivotTo(CFrame.new(at))
 local available=state(s).energy
 check(available>=30,'fixture recharged enough for component B')
 activate(player,'B');check(sig()==first and state(s).energy==available,'B remains locked before 18s')
 moveUntil(s,mob,origin,t+18.02);mob:PivotTo(CFrame.new(at))
 available=state(s).energy
 activate(player,'B');check(sig():match('^WARRIOR:B:') and state(s).energy==available-30,'B alone unlocks at 18s')
 local next=sig()
 moveUntil(s,mob,origin,t+21.98);mob:PivotTo(CFrame.new(at))
 available=state(s).energy
 check(available>=35,'fixture recharged enough for component C')
 activate(player,'C');check(sig()==next and state(s).energy==available,'C remains locked before 22s')
 moveUntil(s,mob,origin,t+22.02);mob:PivotTo(CFrame.new(at))
 available=state(s).energy
 activate(player,'C');check(sig():match('^WARRIOR:C:') and state(s).energy==available-35,'C alone unlocks at 22s')
 moveUntil(s,mob,origin,t+39.98);local energy=state(s).energy
 check(energy>=80,'cooldown control has enough E')
 check(s.swarm.tryRoleGrowthCast(player,'WARRIOR',40,80,{['COMBO-002']=40})==nil and state(s).energy==energy,
  'same authoritative tool clock rejects D 39.98 without charges')
 moveUntil(s,mob,origin,t+40.02)
 check(s.swarm.tryRoleGrowthCast(player,'WARRIOR',40,80,{['COMBO-002']=40})~=nil,
  'same real D component deadline releases at 40.02 independently of separately reused components')
 return 'one Swarm ledger holds component B18, C22 and D40, all observed around exact charge boundaries'
end

function growthCases.warrior_growth_cap()
 local s=setup(true)
 local mob,_,origin=pose(s,Vector3.new(2,0,0))
 moveUntil(s,mob,origin,now+194)
 local growth=state(s)
 check(growth.stage==4 and growth.activeSeconds>=180,'actual Swarm produces S4; sampled '..growth.activeSeconds)
 local targets={}
 for _,neutral in ipairs(s.world:FindFirstChild('NeutralHorde'):GetChildren())do
  local hum=neutral:FindFirstChildOfClass('Humanoid')
  if hum and hum.Health>0 and #targets<6 then
   table.insert(targets,{neutral=neutral,hum=hum})
  end
 end
 equal(#targets,6,'six real eligible Swarm neutrals')
 local radii={1.5,2.4,3.7,4.6,6.9,6.99}
 for i,row in ipairs(targets)do
  local angle=i*math.pi/3
  row.neutral:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
  row.neutral:SetAttribute('EGGRUMBLE_NeutralSpecies','ACORN_IMP')
  row.hum.Health=H
  row.neutral:PivotTo(CFrame.new(origin+Vector3.new(radii[i]*math.cos(angle),1,radii[i]*math.sin(angle))))
 end
 local teammate=s.rules.castles[tostring(second.UserId)]
 teammate.team=s.rules.castles[tostring(player.UserId)].team
 secondRoot.CFrame=CFrame.new(origin+Vector3.new(-1,0,0))
 -- Hold movement/melee scheduling for this one post-growth AoE witness. The
 -- live Swarm API, original recent role snapshot and actual HP remain in use.
 parkOldSwarm(s)
 local allyBefore=secondHumanoid.Health
 local at=now
 activate(player,'D')
 check(sig():match('^WARRIOR:D:') and state(s).energy==20,'one S4 compound charge')
 advanceTo(at+.81)
 local hits,withBurn=0,0
 for _,row in ipairs(targets)do
  if row.hum.Health<H then hits+=1 end
  if ember(row.neutral) then withBurn+=1;equal(row.hum.Health,H-36,'single reserved budget') end
  check(row.hum.Health>=H-44,'no neutral receives two component hits')
 end
 equal(hits,5,'live S4 reaches exactly five of six legal neutrals')
 equal(targets[5].hum.Health,H-44,'fifth neutral at 6.9 studs lies within the S4 circle')
 equal(targets[6].hum.Health,H,'sixth neutral at 6.99 studs is outside the hit-count budget')
 equal(withBurn,1,'whole unified compound registers exactly one burn')
 equal(secondHumanoid.Health,allyBefore,'same-team hero in the ring is untouched')
 return 'actual S4 growth then radius seven to five real neutrals, one burn ledger, teammate untouched'
end

function growthCases.warrior_burn_off()
 local s=setup(true)
 local mob,h=pose(s,Vector3.new(3,0,0))
 local t=now
 activate(player,'B')
 advanceTo(t+.19)
 check(ember(mob)~=nil and h.Health==H-36,'real live elemental budget before OFF')
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 advanceTo(t+.85)
 check(not ember(mob) and h.Health==H-36,'OFF cancels remaining shared DoT without another HP write')
 return 'real current burn stops and its remaining reserve is retired on feature OFF'
end
end
