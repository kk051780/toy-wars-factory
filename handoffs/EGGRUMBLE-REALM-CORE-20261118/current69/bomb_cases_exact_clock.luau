-- Source-level acceptance tests. Geometry, signals, time and seat welding are
-- explicit Native fixtures; complete official game bodies are otherwise intact.
local MODE=TEST_MODE
local SCENARIO=TEST_SCENARIO
advanceTo(now)
local count=#capturedSessions
trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
trigger(second,scenes:FindFirstChild('ROLE_BUILDER'),'職業選択')
local portal=scenes:FindFirstChild(MODE..'_PORTAL')
trigger(player,portal,'参加する');trigger(second,portal,'参加する')
local entered=now
advanceTo(entered+11.99);equal(#capturedSessions,count,'real READY retained')
advanceTo(entered+12.01);equal(#capturedSessions,count+1,'real Host session')
local session=capturedSessions[#capturedSessions]
check(session.mode==MODE and session.rules.phase=='ACTIVE','actual requested mode')
check(session.isCurrentHuman(player)and session.isCurrentHuman(second),'current actual Host membership')
local core=session.world:FindFirstChild('EGGRUMBLE_REALM_BATTLE_CORE')
local lss=session.world:FindFirstChild('EGGRUMBLE_LAND_SEA_SKY_20261117')
check(core and lss,'actual Realm and LSS installed')
trigger(second,lss:FindFirstChild('ScientistShipyard'),'造船')
local boat=lss:FindFirstChild('BUILDER_SEA_BOAT_43')
check(boat and boat:FindFirstChild('PilotSeat').Occupant==secondHumanoid,'real LSS creation')
check(boat:GetAttribute('RealmHP')==nil,'no fixture HP initialization')
local hangar=core:FindFirstChild('PublicFighterHangar')
trigger(player,hangar,'戦闘機に搭乗')
trigger(second,hangar,'戦闘機に搭乗')
local shooter=core:FindFirstChild('GQ8_Fighter_42')
local enemy=core:FindFirstChild('GQ8_Fighter_43')
local neutral=core:FindFirstChild('SubseaLeviathan_2')
check(shooter and shooter:FindFirstChild('PilotSeat').Occupant==humanoid,'real shooter seat')
check(enemy and enemy:FindFirstChild('PilotSeat').Occupant==secondHumanoid,'real target fighter seat')
equal(shooter:GetAttribute('RealmBombs'),3,'original ammunition')
equal(enemy:GetAttribute('RealmHP'),120,'original fighter HP')
equal(neutral:GetAttribute('RealmHP'),70,'original neutral HP')

local floor=session.world:FindFirstChild('TacticalBattlefield')
local impact=floor.Position+Vector3.new(120,60,80)
local pad=Instance.new('Part');pad.Name='FixtureImpactPlatform'
pad.Size=Vector3.new(4,1,4);pad.CFrame=CFrame.new(impact-Vector3.new(0,.5,0))
pad.Anchored=true;pad.CanCollide=true;pad.CanQuery=true;pad.Parent=session.world
local wall=Instance.new('Part');wall.Name='FixtureCover'
wall.Size=Vector3.new(2,20,60);wall.CFrame=CFrame.new(impact+Vector3.new(10,6,0))
wall.Anchored=true;wall.CanCollide=SCENARIO~='NONCOLLIDING';wall.CanQuery=true
wall.Transparency=if SCENARIO=='TRANSPARENT_SOLID'or SCENARIO=='NONCOLLIDING'then 1 else 0
if SCENARIO=='SOLID'or SCENARIO=='TRANSPARENT_SOLID'or SCENARIO=='NONCOLLIDING'or SCENARIO=='TERRAIN'then wall.Parent=session.world end
neutral:PivotTo(CFrame.new(impact+Vector3.new(20,4,0)))
enemy:PivotTo(CFrame.new(impact+Vector3.new(20,6,12)))
boat:PivotTo(CFrame.new(impact+Vector3.new(20,4,-12)))
local targets={neutral,enemy,boat}
local initial={70,120,nil}
local targetNames={'NEUTRAL','FIGHTER','LSS'}
local selectedTarget=nil
if SCENARIO:match('^TARGET_')then
 for index,target in ipairs(targets)do
  if SCENARIO=='TARGET_'..targetNames[index]then
   selectedTarget=target
   target:PivotTo(CFrame.new(impact+Vector3.new(20,4,0)))
   target.PrimaryPart.CanCollide=true
  else target:PivotTo(CFrame.new(impact+Vector3.new(100+index*40,4,index*30)))end
 end
elseif SCENARIO=='BELOW_FLOOR'then
 neutral:PivotTo(CFrame.new(impact+Vector3.new(20,-4,0)))
 enemy:PivotTo(CFrame.new(impact+Vector3.new(20,-6,12)))
 boat:PivotTo(CFrame.new(impact+Vector3.new(20,-4,-12)))
elseif SCENARIO=='BOUNDARY_27'or SCENARIO=='OUTSIDE_RADIUS'then
 neutral:PivotTo(CFrame.new(impact+Vector3.new(if SCENARIO=='BOUNDARY_27'then 27 else 27.001,0,0)))
 enemy:PivotTo(CFrame.new(impact+Vector3.new(100,6,12)))
 boat:PivotTo(CFrame.new(impact+Vector3.new(100,4,-12)))
end
shooter:PivotTo(CFrame.new(impact+Vector3.new(0,60,0)))
character:PivotTo(CFrame.new(shooter:GetPivot().Position+Vector3.new(0,4,0)))
secondCharacter:PivotTo(CFrame.new(enemy:GetPivot().Position+Vector3.new(0,4,0)))

-- Terrain is a bounded solid-volume API fixture. The inherited exact AABB
-- intersection still chooses the nearest physical hit; only its returned
-- Instance class changes from the volume Part to Terrain, as Roblox does.
local terrain=nil
if SCENARIO=='TERRAIN'then
 terrain=Instance.new('Terrain');terrain.Name='FixtureTerrain';terrain.Parent=workspace
 local ordinaryRaycast=workspace.Raycast
 workspace.Raycast=function(self,from,delta,params)
  local hit=ordinaryRaycast(self,from,delta,params)
  if hit and hit.Instance==wall then hit.Instance=terrain end
  return hit
 end
end

local protected=SCENARIO=='SOLID'or SCENARIO=='TRANSPARENT_SOLID'or SCENARIO=='TERRAIN'or SCENARIO=='BELOW_FLOOR'
local beforeQuery=#queryTrace
for _,target in ipairs(targets)do
 if (target:GetPivot().Position-impact).Magnitude<=27 then
  local params=RaycastParams.new();params.FilterType=Enum.RaycastFilterType.Exclude
  params.RespectCanCollide=true
  params.FilterDescendantsInstances={shooter,character,secondCharacter,neutral,enemy,boat}
  if SCENARIO~='BELOW_FLOOR'then table.insert(params.FilterDescendantsInstances,pad)end
  local origin=impact+Vector3.new(0,.1,0)
  local hit=workspace:Raycast(origin,target:GetPivot().Position-origin,params)
  if protected then
   check(hit~=nil,'fixture cover intersects actual target segment')
   check(hit.Instance==(terrain or (SCENARIO=='BELOW_FLOOR'and pad or wall)),'fixture expected obstruction')
  else check(hit==nil,'fixture open target segment')end
 end
end
local geometryProbes=#queryTrace-beforeQuery

local observations={};local failed=0
local function expect(label,actual,wanted)
 local good=actual==wanted
 if type(actual)=='number'and type(wanted)=='number'then good=math.abs(actual-wanted)<1e-6 end
 table.insert(observations,{label=label,actual=actual,wanted=wanted,good=good})
 if not good then failed+=1 end
 print('EXPECT\t'..label..'\t'..(good and 'PASS'or 'FAIL')..'\tactual='..tostring(actual)..'\twanted='..tostring(wanted))
end
local remote=ReplicatedStorage:FindFirstChild('EGGRUMBLE_RealmBattleIntent_V1')
check(remote and remote.ClassName=='RemoteEvent','real existing Remote')
local healthA,healthB=humanoid.Health,secondHumanoid.Health
-- Use exact integer clock anchors for the 8 s boundary probe.
-- The original fractional 7.99+.01 sequence lost an ULP on the third shot.
if SCENARIO=='OUTSIDE_RADIUS'then now=math.ceil(now)end
local firstBombAt=now
local shotQueryStart=#queryTrace
remote.OnServerEvent:Fire(player,'FIRE','BOMB')
local effect=core:FindFirstChild('BombImpact')
check(effect~=nil,'real accepted BOMB')
equal((effect.Position-impact).Magnitude,0,'unshifted actual impact retained')
expect('ONE_AMMO_SPENT',shooter:GetAttribute('RealmBombs'),2)
expect('OWN_FIGHTER_SAFE',shooter:GetAttribute('RealmHP'),120)
expect('HUMAN_A_SAFE',humanoid.Health,healthA)
expect('HUMAN_B_SAFE',secondHumanoid.Health,healthB)
for index,target in ipairs(targets)do
 local radiusOK=(target:GetPivot().Position-impact).Magnitude<=27
 local authorityOK=index==1 or MODE=='BATTLE_ROYALE'
 local shouldDamage=radiusOK and authorityOK and not protected
 local wanted=if shouldDamage then (initial[index]or 100)-46 else initial[index]
 expect(targetNames[index]..'_EXPECTED_HEALTH',target:GetAttribute('RealmHP'),wanted)
end
local shotRays=#queryTrace-shotQueryStart
if selectedTarget then
 local sawSelf=false
 for index=shotQueryStart+1,#queryTrace do
  local hit=queryTrace[index].hit
  if hit and hit:IsDescendantOf(selectedTarget)then sawSelf=true end
 end
 expect('TARGET_OWN_COLLIDABLE_HIT_ACCEPTED',sawSelf,true)
end
local afterFirst={neutral:GetAttribute('RealmHP'),enemy:GetAttribute('RealmHP'),boat:GetAttribute('RealmHP')}
remote.OnServerEvent:Fire(player,'FIRE','BOMB')
expect('SAME_TIME_REPEAT_REJECTED',shooter:GetAttribute('RealmBombs'),2)
for index,target in ipairs(targets)do expect(targetNames[index]..'_NO_DUPLICATE_DAMAGE',target:GetAttribute('RealmHP'),afterFirst[index])end
expect('SAME_TIME_REPEAT_NO_QUERY',#queryTrace-shotQueryStart,shotRays)
if SCENARIO=='OUTSIDE_RADIUS'then
 now=firstBombAt+7.99;remote.OnServerEvent:Fire(player,'FIRE','BOMB')
 expect('COOLDOWN_7_99_REJECTS',shooter:GetAttribute('RealmBombs'),2)
 now=firstBombAt+8;remote.OnServerEvent:Fire(player,'FIRE','BOMB')
 expect('COOLDOWN_8_ACCEPTS',shooter:GetAttribute('RealmBombs'),1)
 now=firstBombAt+16;remote.OnServerEvent:Fire(player,'FIRE','BOMB')
 expect('THIRD_BOMB_ACCEPTS',shooter:GetAttribute('RealmBombs'),0)
 now=firstBombAt+24;local beforeFourth=#queryTrace;remote.OnServerEvent:Fire(player,'FIRE','BOMB')
 expect('FOURTH_BOMB_EMPTY',shooter:GetAttribute('RealmBombs'),0)
 expect('EMPTY_AMMO_NO_QUERY',#queryTrace,beforeFourth)
 for index,target in ipairs(targets)do expect(targetNames[index]..'_OUT_OF_RADIUS_REMAINS',target:GetAttribute('RealmHP'),initial[index])end
end
expect('WARNINGS',#warnings,0)
print('RESULT\t'..MODE..'\t'..SCENARIO..'\tobservations='..#observations..'\tfailed='..failed..'\tshot_rays='..shotRays..'\tgeometry_probes='..geometryProbes)
if failed>0 then error('SOURCE_ACCEPTANCE_RED:'..failed)end
print('CASE\tREALM_BOMB_ACCEPTANCE_'..MODE..'_'..SCENARIO..'\tPASS\tNative source evidence only')
