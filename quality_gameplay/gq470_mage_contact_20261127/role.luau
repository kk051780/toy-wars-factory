local function begin(role)
 trigger(player,scenes:FindFirstChild('ROLE_'..role),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 advanceTo(now+12.01)
 local session=capturedSessions[#capturedSessions]
 assert(session.rules.phase=='ACTIVE' and session.isCurrentHuman(player))
 assert(player:GetAttribute('EGGRUMBLE_Role')==role)
 outsideField(session)
 local tool
 for _,item in player:FindFirstChildOfClass('Backpack'):GetChildren() do
  if item:GetAttribute('EGGRUMBLE_InternalToolId')=='EGGRUMBLE_BASIC_ATTACK' then assert(not tool);tool=item end
 end
 assert(tool);tool.Parent=character
 return session,tool
end
local s,tool=begin(role)
local neutral=spawnCurrentNeutral(s)
local subject=neutral:FindFirstChildOfClass('Humanoid')
local id=neutral:GetAttribute('EGGRUMBLE_NeutralInstanceId')
local spec=dependencies.EGGRUMBLE_BasicMobilityPolicy.SPECS[role].basic
local origin=s.world:FindFirstChild('TacticalBattlefield').Position+Vector3.new(93,240,83)
local aim=Vector3.new(.6,0,.8)
local right=Vector3.new(-.8,0,.6)
local function place(model,f,c,y)
 model:PivotTo(CFrame.new(origin+aim*f+right*c+Vector3.new(0,y,0)))
 rootPart.CFrame=CFrame.new(origin,origin+aim)
end
local function serial() return player:GetAttribute('EGGRUMBLE_BasicCastSerial') or 0 end
local function fire(accepted)
 local before=serial();tool.Activated:Fire();assert(serial()==before+(if accepted then 1 else 0))
end
local function rest(dt) outsideField(s);advanceTo(now+dt) end
local function liveTarget()
 if subject.Health<=0 then neutral=spawnCurrentNeutral(s);subject=neutral:FindFirstChildOfClass('Humanoid') end
end
local shots={}
local function hit(label,f,c,y,want,pitch)
 liveTarget();place(neutral,f,c,y)
 if pitch then
  local direction=aim*math.cos(pitch)+Vector3.new(0,math.sin(pitch),0)
  rootPart.CFrame=CFrame.new(origin,origin+direction)
 end
 local health=subject.Health;fire(true)
 local lost=health-subject.Health
 if want==0 then assert(lost==0,label..' expected miss, lost '..lost) else assert(lost>0,label..' expected hit') end
 table.insert(shots,label..'='..lost)
 local after=subject.Health;fire(false);assert(subject.Health==after)
 rest(spec.cooldown-.001);place(neutral,f,c,y);fire(false);assert(subject.Health==after)
 rest(.002)
end
hit('front3',3,0,0,if role~='MAGE' or patched then 1 else 0)
hit('rear',-3,0,0,0)
hit('vertical',3,0,spec.radius+.1,0)
hit('beyond',spec.reach+spec.radius+.1,0,0,0)
hit('legacy',spec.reach,0,0,1)
local wall=Instance.new('Part');wall.Name='IndependentCollider';wall.Anchored=true;wall.CanCollide=true
wall.Size=Vector3.new(1,12,2);wall.CFrame=CFrame.new(origin+aim*1.5+Vector3.new(0,1,0));wall.Parent=workspace
hit('wall',3,0,0,0);wall:Destroy()
if role=='MAGE' then
 hit('under1',.98,0,0,0)
 hit('over1',1.02,0,0,if patched then 1 else 0)
 hit('fringe',6.1,1.96,0,if patched then 1 else 0)
 hit('outside_taper',3,1.55,0,0)
 hit('height_inside',3,0,4.99,if patched then 1 else 0)
 hit('pitch_up30_same_floor',3,0,0,if patched then 1 else 0,math.rad(30))
 hit('pitch_up30_high',3,0,10.4,0,math.rad(30))
 hit('pitch_down30_low',3,0,-10.4,0,math.rad(-30))
 hit('pitch_up30_above_edge',3,0,10.6,0,math.rad(30))
 hit('pitch_straight_up_legacy',-2,0,11,1,math.rad(90))
 liveTarget()
 local horde=s.world:FindFirstChild('NeutralHorde')
 local models={}
 local function collect()
  table.clear(models)
  for _,model in horde:GetChildren() do
   local h=model:FindFirstChildOfClass('Humanoid')
   if h and h.Health>0 and model.PrimaryPart then table.insert(models,model) end
  end
 end
 collect()
 for _=1,100 do
  if #models>=3 then break end
  local floor=s.world:FindFirstChild('TacticalBattlefield')
  rootPart.CFrame=CFrame.new(floor.Position+Vector3.new(180,floor.Size.Y*.5+3,80))
  advanceTo(now+.2);collect()
 end
 assert(#models>=3,'need three real swarm members')
 rest(spec.cooldown+.01)
 local points={{3,-.8},{7,1.8},{12,-2.5}}
 local before={};local ids={}
 for i=1,3 do
  place(models[i],points[i][1],points[i][2],0)
  before[i]=models[i]:FindFirstChildOfClass('Humanoid').Health
  ids[i]=models[i]:GetAttribute('EGGRUMBLE_NeutralInstanceId')
 end
 assert(ids[1]~=ids[2] and ids[1]~=ids[3] and ids[2]~=ids[3])
 fire(true)
 for i=1,3 do
  local dmg=before[i]-models[i]:FindFirstChildOfClass('Humanoid').Health
  local want=if i==1 and not patched then 0 else math.min(before[i],9)
  equal(dmg,want,'three actual IDs single cast '..i)
  table.insert(shots,'multi'..i..'='..dmg)
 end
end
print('REVIEW',role,id,table.concat(shots,','))
