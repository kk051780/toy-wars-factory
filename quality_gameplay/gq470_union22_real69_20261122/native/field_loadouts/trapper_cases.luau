do
local FLAG='P0D_ENABLE_PRIVATE_TRAPPER_015'
local H=120
local function bySlot(who,slot)
 for _,container in ipairs({who:FindFirstChildOfClass('Backpack'),who.Character})do
  for _,tool in ipairs(container:GetChildren())do
   local id=tool:GetAttribute('EGGRUMBLE_InternalToolId')
   if tool:IsA('Tool') and type(id)=='string' and id:match('^EGGRUMBLE_SKILL_'..slot..'_') then return tool end
  end
 end
 return nil
end
local function cast()return player:GetAttribute('EGGRUMBLE_SkillCastSignature')end
local function state(s)
 local result=s.swarm.getRoleGrowthSnapshot(player)
 check(result and result.role=='TRAPPER','current actual Trapper growth state')
 return result
end
local function cue(s)return s.world:FindFirstChild('P0D_TRAPPER_GRAVITY_ORB')end
local function setup(opted)
 local stand=scenes:FindFirstChild('ROLE_TRAPPER')
 trigger(player,stand,'職業選択')
 if opted then
  trigger(player,stand,'装備する')
  check(player:GetAttribute('EGGRUMBLE_LobbyTrapperLoadoutName')=='重力球','real optional arena loadout prompt')
 end
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 advanceTo(now+12.01)
 local s=capturedSessions[#capturedSessions]
 check(s and s.isCurrentHuman(player) and s.rules.phase=='ACTIVE' and player:GetAttribute('EGGRUMBLE_Role')=='TRAPPER',
  'actual Host role membership')
 check(bySlot(player,'A').Name=='技A・念動衝撃' and bySlot(player,'C').Name=='技C・空間転移' and not bySlot(player,'D'),
  'untouched actual A/C of standard Trapper')
 if opted then
  check(s.trapperGravityLoadouts[player.UserId] and bySlot(player,'B').Name=='技B・重力球'
    and bySlot(player,'B'):GetAttribute('EGGRUMBLE_FixedAbilityId')=='TRAPPER-015','Host equips fixed optional B only')
  check(bySlot(second,'B'):GetAttribute('EGGRUMBLE_FixedAbilityId')==nil,'other role cannot receive the Tool')
 else
  check(bySlot(player,'B').Name=='技B・重力牢獄' and bySlot(player,'B'):GetAttribute('EGGRUMBLE_FixedAbilityId')==nil,
    'actual legacy Trapper B')
 end
 outsideField(s)
 return s
end
local function aim(at)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
end
local function liveNeutral(s,n)
 spawnCurrentNeutral(s)
 for _=1,48 do
  local found={}
  for _,m in ipairs(s.world:FindFirstChild('NeutralHorde'):GetChildren())do
   local h=m:FindFirstChildOfClass('Humanoid')
   if h and h.Health>0 then table.insert(found,{model=m,h=h}) end
  end
  if #found>=n then return found end
  advanceTo(now+.25)
 end
 error('existing Swarm did not spawn enough actual neutral models')
end
local function park(row,at)
 row.model:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 row.model:PivotTo(CFrame.new(at+Vector3.new(-36,10,25)))
end
local function prepare(s,count)
 local mobs=liveNeutral(s,count)
 local floor=s.world:FindFirstChild('TacticalBattlefield')
 local origin,center
 for _,offset in ipairs({{170,-115},{280,150},{-300,250},{315,-210}})do
  origin=floor.Position+Vector3.new(offset[1],floor.Size.Y*.5+3,offset[2])
  for _,row in ipairs(mobs)do park(row,origin)end
  aim(origin)
  advanceTo(now+.4)
  center=s.swarm.gravityCenter(player,character,origin,origin+Vector3.new(5.5,0,0))
  if center then break end
 end
 check(center and state(s).stage==0 and state(s).energy==100,'find actual ground/LOS in current arena')
 return mobs,origin,center
end
local function place(row,center,x,z)
 local height=2*(row.model.PrimaryPart.Size.Y/2.5)
 local at=center+Vector3.new(x,height-1.8,z)
 row.model:PivotTo(CFrame.new(at));row.h.Health=H
 return at
end
local function wall(s,at,size)
 local p=Instance.new('Part');p.Name='NativeGravityWall';p.Anchored=true;p.CanCollide=true;p.CanQuery=true
 p.Size=size;p.CFrame=CFrame.new(at);p.Parent=s.world
 return p
end
local function horizontal(a,b)return Vector3.new(a.X-b.X,0,a.Z-b.Z).Magnitude end

function growthCases.gravity_cap_and_release()
 local s=setup(true)
 local mobs,origin,center=prepare(s,5)
 local a,b,c,d,dead=mobs[1],mobs[2],mobs[3],mobs[4],mobs[5]
 local p1,p2,p3,p4=place(a,center,2.8,0),place(b,center,0,3.3),place(c,center,4.5,0),place(d,center,0,-5.7)
 local deadAt=place(dead,center,-1.8,0);dead.h.Health=0
 local opponent=origin+Vector3.new(5.5,0,-1)
 secondRoot.CFrame=CFrame.new(opponent)
 local t=now
 activate(player,'B')
 check(cast():match('^TRAPPER:B:') and state(s).energy==60 and cue(s),'real B spends E40 and warns')
 local tell=cue(s)
 local ring=tell:FindFirstChild('GravityRadiusTell')
 check(ring and ring.Size.Y==10 and not ring.CanCollide and not ring.CanTouch and not ring.CanQuery,
  'original radius tell remains inert and indicates S0 radius five')
 local seq=cast();activate(player,'B');check(cast()==seq and state(s).energy==60,'one cast and no second charge')
 advanceTo(t+.299)
 check((a.model.PrimaryPart.Position-p1).Magnitude<.001,'no move before .30 tell')
 advanceTo(t+.301)
 local pulled1,pulled2=a.model.PrimaryPart.Position,b.model.PrimaryPart.Position
 check(horizontal(pulled1,center)<horizontal(p1,center) and horizontal(pulled2,center)<horizontal(p2,center),
  'two actual enemies move toward committed center')
 check((c.model.PrimaryPart.Position-p3).Magnitude<.001 and (d.model.PrimaryPart.Position-p4).Magnitude<.001,
  'third legal neutral and outside-radius neutral untouched')
 check((dead.model.PrimaryPart.Position-deadAt).Magnitude<.001,'dead body cannot consume or move in the pull')
 advanceTo(t+.619)
 check((a.model.PrimaryPart.Position-pulled1).Magnitude<.001,'actor stays held until .32 release')
 advanceTo(t+.621)
 check(horizontal(a.model.PrimaryPart.Position,pulled1)>1.7 and horizontal(b.model.PrimaryPart.Position,pulled2)>1.7,
  'two captured neutrals physically released via existing orbit vector')
 for _,row in ipairs({a,b,c,d})do equal(row.h.Health,H,'gravity has no damage budget')end
 check((secondRoot.Position-opponent).Magnitude<.001 and s.swarm.getTotal()==0,'no player displacement or KO side effect')
 advanceTo(t+.75)
 check(not cue(s),'original artist cue expires without a leftover part')
 return 'real S0 Tool charges E40, 0.30 tell then two neutral pulls and .32 release; no HP/KO/players'
end

function growthCases.gravity_occlusion()
 local s=setup(true)
 local mobs,_,center=prepare(s,1)
 local hit=mobs[1];local before=place(hit,center,4,0)
 local t=now
 activate(player,'B')
 wall(s,center+Vector3.new(2.6,0,0),Vector3.new(.5,8,10))
 advanceTo(t+.65)
 check((hit.model.PrimaryPart.Position-before).Magnitude<.001,'new wall separates target from orb before actual pull')
 equal(hit.h.Health,H,'wall and gravity never damage neutral')
 return 'actual late wall blocks pull with clear initial placement, no body crossing'
end

function growthCases.gravity_release_wall()
 local s=setup(true)
 local mobs,_,center=prepare(s,1)
 local hit=mobs[1];local before=place(hit,center,3.4,0)
 local t=now
 activate(player,'B');advanceTo(t+.301)
 local pulled=hit.model.PrimaryPart.Position
 check(horizontal(pulled,center)<horizontal(before,center),'control: pull happens before independent late release wall')
 local width=hit.model.PrimaryPart.Size.X
 wall(s,pulled+Vector3.new(width*.5+.62,0,0),Vector3.new(.22,8,8))
 advanceTo(t+.63)
 check((hit.model.PrimaryPart.Position-pulled).Magnitude<.02,'donor full body sweep prevents unsafe release through wall')
 return 'new obstacle after committed pull blocks release independently of initial LOS'
end

function growthCases.gravity_initial_overlap()
 local s=setup(true)
 local mobs,_,center=prepare(s,1)
 local hit=mobs[1];local before=place(hit,center,3.4,0)
 local depth=hit.model.PrimaryPart.Size.Z
 wall(s,before+Vector3.new(0,0,depth*.5-.08),Vector3.new(.35,7,.24))
 local t=now;activate(player,'B')
 check(cue(s) and cast():match('^TRAPPER:B:'),'ray sees the open centerline and the Tool starts')
 advanceTo(t+.66)
 check((hit.model.PrimaryPart.Position-before).Magnitude<.001,'source overlap cannot be traversed to reach a clear target')
 return 'clear center ray cannot move a body whose starting volume already intersects a wall'
end

local function retire(kind)
 local s=setup(true)
 local mobs,_,center=prepare(s,1)
 local hit=mobs[1];local before=place(hit,center,3.4,0)
 local t=now;activate(player,'B');advanceTo(t+.301)
 local pulled=hit.model.PrimaryPart.Position
 check(horizontal(pulled,center)<horizontal(before,center),'actual hold precedes invalidation')
 if kind=='carry' then s.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=='avatar' then player.Character=Instance.new('Model')
 elseif kind=='role' then player:SetAttribute('EGGRUMBLE_Role','MAGE')
 elseif kind=='finish' then s.rules.phase='FINISHED';s.world:SetAttribute('EGGRUMBLE_MatchPhase','FINISHED')
 elseif kind=='off' then workspace:SetAttribute(FLAG,false);drainDeferred() end
 advanceTo(t+.64)
 check((hit.model.PrimaryPart.Position-pulled).Magnitude<.001,'held target may not release from a stale cast '..kind)
 equal(hit.h.Health,H,'retired control does not write HP')
 if kind=='off' then
  check(not cue(s) and bySlot(player,'B').Name=='技B・重力牢獄','actual Host reequips legacy B on fallback')
 end
 return 'real optional movement safely retires after '..kind..' without a stale release'
end
for _,kind in ipairs({'carry','avatar','role','finish','off'})do growthCases['gravity_cancel_'..kind]=function()return retire(kind)end end

function growthCases.gravity_carry_denial()
 local s=setup(true)
 local mobs,_,center=prepare(s,1)
 local at=place(mobs[1],center,3.4,0)
 local castle=s.rules.castles[tostring(player.UserId)]
 castle.heldEggs=1;activate(player,'B');advanceTo(now+.4)
 check(not cue(s) and cast()==nil and (mobs[1].model.PrimaryPart.Position-at).Magnitude<.001,
   'server objective cargo blocks action and energy charge')
 castle.heldEggs=0;advanceTo(now+.43);equal(state(s).energy,100,'no cost while carrying')
 return 'carry blocks optional Tool completely and leaves old active E100'
end

function growthCases.gravity_legacy()
 local s=setup(false)
 local mob=spawnCurrentNeutral(s)
 local floor=s.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(180,20,80)
 aim(origin);advanceTo(now+.39)
 local hum=mob:FindFirstChildOfClass('Humanoid');hum.Health=H
 mob:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 mob:PivotTo(CFrame.new(origin+Vector3.new(15,1,0)))
 activate(player,'B')
 check(cast():match('^TRAPPER:B:') and hum.Health<H and state(s).energy==100 and not cue(s),
   'base GRAVITY/slow and damage remain without activating the optional orb')
 return 'actual legacy B still reaches original combat with its own damage and no growth cost'
end

function growthCases.gravity_physical_off()
 local stand=scenes:FindFirstChild('ROLE_TRAPPER')
 for _,p in ipairs(stand:GetChildren())do
  check(not p:IsA('ProximityPrompt') or p.ActionText~='装備する','physical parent has no new Trapper kit prompt')
 end
 return growthCases.gravity_legacy()
end

local function moveUntil(s,origin,t)
 local corners={Vector3.new(0,0,0),Vector3.new(0,0,1),Vector3.new(1,0,1),Vector3.new(1,0,0)}
 local i=0
 while now+.39<t do
  i+=1
  for _,mob in ipairs(s.world:FindFirstChild('NeutralHorde'):GetChildren())do
   if mob:FindFirstChildOfClass('Humanoid') then park({model=mob},origin) end
  end
  aim(origin+corners[(i-1)%4+1]);advanceTo(now+.39)
 end
 aim(origin);advanceTo(t)
end

function growthCases.gravity_budget()
 local s=setup(true)
 local mobs,origin,center=prepare(s,1)
 place(mobs[1],center,3.4,0)
 local t=now;activate(player,'B')
 local once=cast()
 equal(state(s).energy,60,'first server E40')
 advanceTo(t+.75)
 moveUntil(s,origin,t+23.98)
 local e=state(s).energy
 check(e>=40 and not cue(s),'control has enough restored E')
 activate(player,'B')
 check(cast()==once and state(s).energy==e and not cue(s),'real B refuses before exact 24s')
 moveUntil(s,origin,t+24.02)
 e=state(s).energy
 activate(player,'B')
 check(cast()~=once and cue(s) and state(s).energy==e-40,'real B becomes available and debits once after 24s')
 return 'same server Tool enforces exact 24s cooldown and E40 once per cast'
end
end
