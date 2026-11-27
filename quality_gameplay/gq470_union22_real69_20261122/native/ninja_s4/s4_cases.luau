do
local FLAG='P0D_ENABLE_PRIVATE_S4_HERO_FORM'
local ROLE='EGGRUMBLE_Role'
local STAGE='EGGRUMBLE_RoleAbilityStage'
local expected={
 WARRIOR={'ART_GoldShoulder-1','ART_GoldShoulder1','ART_CrestBlade'},
 MAGE={'ART_HighCollar-1','ART_HighCollar1','ART_Diadem'},
 NINJA={'ART_BackBlade-1','ART_BackBlade1'},
 TRAPPER={'ART_FloatFin-1','ART_FloatFin1','ART_BackSpine'},
 BUILDER={'ART_ReactorPack','ART_ToolArm','ART_Antenna'},
 BEAST={'ART_Antler-1','ART_Antler1','ART_HideCape'},
 ZOMBIE={'ART_TallHorn','ART_Talisman-1','ART_Talisman1'},
}
local function costume(avatar)
 local found=avatar:FindFirstChild('EGGRUMBLE_RoleVisuals')
 check(found and found:IsA('Folder'),'real original Hero art costume')
 return found
end
local function tag(avatar)
 return avatar:FindFirstChild('Head'):FindFirstChild('EGGRUMBLE_BattleGrowthTag')
end
local function snapshot(avatar)
 local f=costume(avatar)
 local result={folder=f,parts={}}
 for _,part in ipairs(f:GetChildren())do
  check(part:IsA('BasePart') and part.Massless and not part.CanCollide and not part.CanTouch and not part.CanQuery,
    'borrowed art keeps noninteractive geometry')
  local weld=part:FindFirstChildOfClass('WeldConstraint')
  check(weld and weld.Part1==part,'existing role art uses original single weld')
  result.parts[part.Name]={part=part,size=part.Size,weld=weld,frame=part.CFrame,color=part.Color,mat=part.Material,
    class=part.ClassName}
 end
 return result
end
local function equalVector(v,w)
 return math.abs(v.X-w.X)<1e-7 and math.abs(v.Y-w.Y)<1e-7 and math.abs(v.Z-w.Z)<1e-7
end
local function geometry(before,avatar,changes)
 local after=snapshot(avatar)
 check(after.folder==before.folder,'S4 never rebuilds or adds a costume folder')
 equal(#after.folder:GetChildren(),#before.folder:GetChildren(),'role costume Part count stays fixed')
 check(#after.folder:GetChildren()<=13,'original asset Part cap')
 for name,partBefore in pairs(before.parts)do
  local partAfter=after.parts[name]
  check(partAfter and partAfter.part==partBefore.part and partAfter.weld==partBefore.weld and partAfter.frame==partBefore.frame
    and partAfter.color==partBefore.color and partAfter.mat==partBefore.mat and partAfter.class==partBefore.class,
    'retained source piece, anchor pose, weld and material: '..name)
  local shouldGrow=table.find(changes,name)~=nil
  check(equalVector(partAfter.size,partBefore.size)~=shouldGrow,'exact role-specific shape change: '..name)
  if shouldGrow then check(partAfter.size.Magnitude>partBefore.size.Magnitude,'geometry delta has visible dimensions: '..name) end
 end
 for _,name in ipairs(changes)do check(before.parts[name]~=nil,'role-specific authored asset exists: '..name)end
end
local function selected(role)
 trigger(player,scenes:FindFirstChild('ROLE_'..role),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 local lobby=snapshot(character)
 player:SetAttribute(STAGE,4)
 geometry(lobby,character,{})
 check(tag(character)==nil,'unadmitted lobby does not show match B tag')
 player:SetAttribute(STAGE,nil)
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 advanceTo(now+12.01)
 local session=capturedSessions[#capturedSessions]
 check(session and session.rules.phase=='ACTIVE' and session.isCurrentHuman(player),'actual Host active member')
 check(player:GetAttribute(ROLE)==role,'actual chosen and equipped role: '..role)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(180,20,80)
 rootPart.CFrame=CFrame.new(origin)
 advanceTo(now+.39)
 check(tag(character)~=nil,'original B tag is present on existing Head')
 return session,origin,snapshot(character)
end
for role,changes in pairs(expected)do
 growthCases['s4_role_'..role]=function()
  local _,_,plain=selected(role)
  local originalTag=tag(character)
  check(originalTag:FindFirstChild('BattleGrowthText').Text=='この試合 B1｜中立KO0','B1 and existing KO text unchanged')
  for stage=0,3 do player:SetAttribute(STAGE,stage); geometry(plain,character,{}) end
  player:SetAttribute('EGGRUMBLE_BattleStage',3)
  player:SetAttribute('EGGRUMBLE_NeutralKOs',4)
  geometry(plain,character,{})
  check(tag(character)==originalTag and originalTag:FindFirstChild('BattleGrowthText').Text=='この試合 B3｜中立KO4',
    'legacy B3 and neutral KO stay independent')
  player:SetAttribute(STAGE,4)
  geometry(plain,character,changes)
  check(tag(character)==originalTag,'existing B label is neither rebuilt nor repurposed')
  return role..' keeps original parts and gains only its defined S4 geometry; B1/B3/KO independent'
 end
end

function growthCases.s4_actual_growth()
 local session,origin,plain=selected('MAGE')
 local swarm=session.swarm
 local ticks=0
 local corners={Vector3.new(0,0,0),Vector3.new(0,0,1),Vector3.new(1,0,1),Vector3.new(1,0,0)}
 while player:GetAttribute(STAGE)~=4 and ticks<600 do
  ticks+=1
  rootPart.CFrame=CFrame.new(origin+corners[(ticks-1)%4+1])
  advanceTo(now+.39)
  for _,mob in ipairs(session.world:FindFirstChild('NeutralHorde'):GetChildren())do
   if mob:FindFirstChildOfClass('Humanoid') then
    mob:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
    mob:PivotTo(CFrame.new(origin+Vector3.new(-36,10,0)))
   end
  end
 end
 local state=swarm.getRoleGrowthSnapshot(player)
 check(state and state.stage==4 and state.activeSeconds>=180 and player:GetAttribute(STAGE)==4,
    'Swarm activity never reached S4, actual='..tostring(state and state.activeSeconds))
 equal(swarm.getTotal(),0,'role growth is separate from KO')
 geometry(plain,character,expected.MAGE)
 check(tag(character):FindFirstChild('BattleGrowthText').Text=='この試合 B1｜中立KO0','actual MAGE S4 does not replace B1')
 return string.format('Host/Swarm actual %.2f active seconds gives S4, MAGE shape changes and B1/KO0 still visible',state.activeSeconds)
end

function growthCases.s4_retirement()
 local session,origin,plain=selected('NINJA')
 player:SetAttribute(STAGE,4)
 geometry(plain,character,expected.NINJA)
 character:SetAttribute('EGGRUMBLE_Downed',true)
 geometry(plain,character,{})
 character:SetAttribute('EGGRUMBLE_Downed',nil)
 geometry(plain,character,expected.NINJA)
 rootPart.CFrame=CFrame.new(origin+Vector3.new(5000,0,0))
 geometry(plain,character,{})
 rootPart.CFrame=CFrame.new(origin)
 geometry(plain,character,expected.NINJA)
 workspace:SetAttribute(FLAG,false)
 geometry(plain,character,{})
 check(tag(character)~=nil,'art flag disables S4 independently of old B')
 workspace:SetAttribute(FLAG,true)
 geometry(plain,character,expected.NINJA)
 humanoid.Health=0
 geometry(plain,character,{})
 humanoid.Health=100
 geometry(plain,character,expected.NINJA)
 local old=character
 player.CharacterRemoving:Fire(old)
 geometry(plain,old,{})
 local replacement=Instance.new('Model');replacement.Name='S4FixtureAvatar';replacement.Parent=workspace
 local human=Instance.new('Humanoid');human.Parent=replacement
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.CFrame=CFrame.new(origin+Vector3.new(5000,0,0));root.Parent=replacement
 UIAudit.rig(replacement)
 player.Character=replacement;player.CharacterAdded:Fire(replacement)
 advanceTo(now+.02)
 local fresh=snapshot(replacement)
 check(fresh.parts['ART_BackBlade1'].size.Y==plain.parts['ART_BackBlade1'].size.Y,'stale S4 cannot grow a new avatar waiting in lobby')
 rootPart.CFrame=CFrame.new(origin)
 geometry(plain,old,{})
 root.CFrame=CFrame.new(origin)
 geometry(fresh,replacement,expected.NINJA)
 local horde=session.world:FindFirstChild('NeutralHorde')
 parkOldSwarm(session)
 outsideField(session)
 finishAndClose(session,horde)
 geometry(fresh,replacement,{})
 return 'actual NINJA source: downed/dead, outside field, OFF, old-avatar callbacks and Host finish restore original rig'
end

function growthCases.s4_physical_off()
 local _,_,plain=selected('WARRIOR')
 player:SetAttribute(STAGE,4)
 geometry(plain,character,{})
 check(tag(character)~=nil,'physical OFF retains actual previous B tag')
 return 'exact original rollback retains original Warrior silhouette even during published S4'
end
end
