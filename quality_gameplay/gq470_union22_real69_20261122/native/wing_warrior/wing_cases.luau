do
local flag='P0D_ENABLE_PRIVATE_MAGE_COMBO_005'
local function kit(solo)
 local stand=scenes:FindFirstChild('ROLE_MAGE')
 trigger(player,stand,'職業選択')
 trigger(player,stand,'風翼を装備')
 check(player:GetAttribute('EGGRUMBLE_LobbyMageProjectileName')=='氷槍＋風翼','actual wing option selected')
 local live=if solo then growthCases.readySoloBR() else ready('PRIVATE_WING_TEAM')
 check(live.mageProjectiles[player.UserId]=='MAGE-040','actual Host snapshots opt-in')
 local actual={}
 for _,t in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do
  if t:IsA('Tool') then actual[t.Name]=t end
 end
 for _,entry in ipairs({{'技A・氷槍','MAGE-012'},{'技C・蒼天嵐衣','MAGE-040'},{'技D・白銀嵐翼','COMBO-005'}}) do
  check(actual[entry[1]] and actual[entry[1]]:GetAttribute('EGGRUMBLE_FixedAbilityId')==entry[2],
   'actual fixed Tool minted: '..entry[2])
 end
 check(actual['技B・爆炎陣'],'existing Fire B kept in opt-in Mage deck')
 return live
end
local function pose(live,afterX,support)
 local neutral=spawnCurrentNeutral(live)
 local floor=live.world:FindFirstChild('TacticalBattlefield')
 local at=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
 rootPart.AssemblyLinearVelocity=Vector3.zero
 rootPart.AssemblyAngularVelocity=Vector3.zero
 humanoid.MoveDirection=Vector3.zero
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false
 humanoid.PlatformStand=false
 local mobs=live.world:FindFirstChild('NeutralHorde')
 for _,mob in ipairs(mobs:GetChildren()) do
  mob:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
  mob:PivotTo(CFrame.new(at+Vector3.new(-40,0,25)))
 end
 local crown=neutral:FindFirstChildOfClass('Humanoid')
 crown.Health=96
 neutral:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 neutral:SetAttribute('EGGRUMBLE_NeutralSpecies',support or 'FOREST_IMP')
 neutral:PivotTo(CFrame.new(at+Vector3.new(afterX,1,0)))
 advanceTo(now+.39)
 local self=live.swarm.getRoleGrowthSnapshot(player)
 check(self and self.energy==100 and self.stage==0,'current real Mage sample')
 return crown,at,neutral
end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function cue(live,name) return live.world:FindFirstChild(name) end
local function tag() return player:GetAttribute('EGGRUMBLE_SkillCastSignature') end
local function wall(live,at,size)
 local blocker=Instance.new('Part')
 blocker.Size=size;blocker.CFrame=CFrame.new(at);blocker.Anchored=true;blocker.CanCollide=true;blocker.CanQuery=true
 blocker.Parent=live.world
 return blocker
end

function growthCases.wing_combo()
 local live=kit()
 local health,origin,target=pose(live,10.8)
 local t=now
 activate(player,'D')
 local cast=tag()
 check(cast and cast:match('^MAGE:D:') and energy(live)==20 and rootPart.Anchored,'actual D charges E80 once and starts guarded flight')
 check(cue(live,'EGGRUMBLE_WingLandingTell') and not cue(live,'EGGRUMBLE_MAGE-012_Aim'),'landing warning precedes spear warning')
 advanceTo(t+.39)
 check(rootPart.Position.Y-origin.Y>3.75 and rootPart.Position.Y-origin.Y<=4.01 and health.Health==96,
  'real airborne avatar reaches fixed S0 altitude without damage')
 activate(player,'A')
 activate(player,'B')
 activate(player,'C')
 check(tag()==cast and health.Health==96,'other active skills cannot launch while airborne')
 advanceTo(t+.79)
 check(rootPart.Anchored and health.Health==96 and not cue(live,'EGGRUMBLE_MAGE-012_Aim'),'no attack before exact flight duration')
 advanceTo(t+.92)
 check(not rootPart.Anchored and math.abs(rootPart.Position.Y-origin.Y)<.07 and (rootPart.Position-origin).Magnitude>4.7,
  'actual verified ground landing and normal grounded mobility restored')
 check(cue(live,'EGGRUMBLE_MAGE-012_Aim') and health.Health==96,'real aligned spear warning after settled landing, no early damage')
 check(not cue(live,'EGGRUMBLE_WingLandingRing'),'compound does not add standalone ring damage')
 advanceTo(t+1.40)
 check(health.Health==66 and energy(live)>=20,'original ice spear takes exact neutral HP with no second debit')
 check(target:FindFirstChild('EGGRUMBLE_Frost')~=nil,'ordinary eligible neutral receives old authorized frost cue')
 check(live.swarm.getTotal()==0,'one real hit does not fabricate KO')
 return 'real COMBO-005 Tool pays once, flies safely, lands, warns, and only then the original ice spear hits'
end

function growthCases.wing_only()
 local live=kit()
 local health=pose(live,7.3)
 local t=now
 activate(player,'C')
 check(tag():match('^MAGE:C:') and energy(live)==55,'fixed standalone flight E45')
 advanceTo(t+.74)
 check(health.Health==96,'no ring damage in the air')
 advanceTo(t+.94)
 check(health.Health==87 and cue(live,'EGGRUMBLE_WingLandingRing') and not cue(live,'EGGRUMBLE_MAGE-012_Aim'),
  'stance releases before the standalone one-neutral wind ring and no spear')
 advanceTo(t+1.27)
 check(not cue(live,'EGGRUMBLE_WingLandingRing') and health.Health==87,'bounded ring expires and causes one hit')
 return 'standalone flight applies a real bounded wind ring only after legal touchdown'
end

local function denied(kind)
 local live=kit()
 local health,origin=pose(live,10.8)
 local t=now
 if kind=='ceiling' then
  wall(live,origin+Vector3.new(0,4.4,0),Vector3.new(25,.25,22))
  activate(player,'D')
  check(not rootPart.Anchored and energy(live)==100 and not cue(live,'EGGRUMBLE_WingLandingTell'),
   'known high obstruction denied before debit')
 else
  activate(player,'D')
  check(rootPart.Anchored and energy(live)==20,'accepted real D prior to disruption')
  advanceTo(t+.23)
  if kind=='wall' then wall(live,origin+Vector3.new(3.8,2,0),Vector3.new(.2,15,20))
  elseif kind=='egg' then live.rules.castles[tostring(player.UserId)].heldEggs=1
  elseif kind=='avatar' then player.Character=Instance.new('Model')
  elseif kind=='air' then humanoid.FloorMaterial=Enum.Material.Air
  elseif kind=='end' then live.rules.phase='FINISHED'
  elseif kind=='off' then workspace:SetAttribute(flag,false);drainDeferred()
  end
  advanceTo(t+1.45)
  check(not rootPart.Anchored,'cancel must release own root anchor')
  check(not cue(live,'EGGRUMBLE_WingLandingTell') and not cue(live,'EGGRUMBLE_WingLeft'),
   'cancel cleans both arena and wing cues')
 end
 check(health.Health==96 and not cue(live,'EGGRUMBLE_MAGE-012_Aim'),'rejected or interrupted flight never attacks')
 return 'flight rejects or cleans up without a late spear: '..kind
end
for _,kind in ipairs({'ceiling','wall','egg','avatar','air','end','off'}) do
 growthCases['wing_negative_'..kind]=function() return denied(kind) end
end

function growthCases.wing_ice_defense()
 local live=kit()
 local health,_,target=pose(live,10.8,'BABY_GOLEM')
 local t=now
 activate(player,'D')
 advanceTo(t+1.38)
 check(health.Health==66 and not target:FindFirstChild('EGGRUMBLE_Frost'),
  'authorized spear HP still resolves, resistance blocks frost status only')
 return 'existing Rock Golem resistance suppresses real Combo frost without canceling lawful spear damage'
end

function growthCases.wing_spear_wall()
 local live=kit()
 local health,origin=pose(live,10.8)
 local t=now
 activate(player,'D')
 advanceTo(t+.91)
 check(cue(live,'EGGRUMBLE_MAGE-012_Aim'),'actual spear sweep warned after landing')
 wall(live,origin+Vector3.new(8,0,0),Vector3.new(.24,12,12))
 advanceTo(t+1.45)
 check(health.Health==96,'new wall clips original swept spear and no HP leaks')
 return 'authorized after-landing projectile keeps original dynamic cover checks'
end

function growthCases.wing_br_steering()
 local live=kit(true)
 local _,origin=pose(live,13)
 local t=now
 activate(player,'C')
 advanceTo(t+.2)
 humanoid.MoveDirection=Vector3.new(.8,0,.6)
 advanceTo(t+.96)
 local travel=rootPart.Position-origin
 check(tag():match('^MAGE:C:') and not rootPart.Anchored and math.abs(travel.Y)<.1,
  'actual BR selection flies and settles to its own physical floor')
 check(travel.Z>1.4 and travel.Magnitude<=4.82,'server-observed steering remains inside fixed mobility envelope')
 return 'BR opt-in uses its own world, bounded steering, ground and release'
end

function growthCases.wing_off_parent()
 local stand=scenes:FindFirstChild('ROLE_MAGE')
 for _,prompt in ipairs(stand:GetChildren()) do
  check(not prompt:IsA('ProximityPrompt') or prompt.ActionText~='風翼を装備','physical OFF contains no wing prompt')
 end
 local live=ready('PRIVATE_WING_PARENT_OFF')
 check(not live.mageProjectiles[player.UserId],'physical OFF keeps standard Mage selection')
 local slots={}
 for _,item in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do slots[item.Name]=true end
 check(slots['技A・氷弾'] and slots['技B・爆炎陣'] and slots['技C・雷光治癒'] and not slots['技D・白銀嵐翼'],
  'physical parent keeps original A/B/C')
 return 'exact physical parent has no wing Tool or opt-in and preserves Mage A/B/C'
end
end
