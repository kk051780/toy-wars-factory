do
local FLAG='P0D_ENABLE_PRIVATE_NINJA_COMBO_008'
local LABEL='EGGRUMBLE_LobbyNinjaLoadoutName'
local function stand() return scenes:FindFirstChild('ROLE_NINJA') end
local function selectKit()
 trigger(player,stand(),'職業選択')
 trigger(player,stand(),'装備する')
 check(player:GetAttribute(LABEL)=='瞬歩・煙玉・霞瞬歩','actual optional Ninja lobby selection')
end
local function tool(actor,slot)
 for _,container in ipairs({actor:FindFirstChildOfClass('Backpack'),actor.Character}) do
  for _,item in ipairs(container:GetChildren()) do
   local identity=item:GetAttribute('EGGRUMBLE_InternalToolId')
   if type(identity)=='string' and identity:match('^EGGRUMBLE_SKILL_'..slot..'_') then return item end
  end
 end
 return nil
end
local function slot(actor,code,name,id)
 local instance=assert(tool(actor,code),'actual server Tool exists at '..code)
 check(instance.Name=='技'..code..'・'..name,'exact physical display slot '..code)
 check(instance:GetAttribute('EGGRUMBLE_FixedAbilityId')==id,'server minted fixed ability identity '..code)
 return instance
end
local function expectKit(session)
 check(session.ninjaLoadouts[player.UserId], 'actual Host froze opted-in Ninja for match')
 slot(player,'A','瞬影斬',nil)
 slot(player,'B','瞬歩','NINJA-031')
 slot(player,'C','煙玉','NINJA-061')
 slot(player,'D','霞瞬歩','COMBO-008')
 check(not tool(second,'D'),'peer receives no Ninja ability without Ninja opt-in')
end
local function expectStandard(session)
 check(not session.ninjaLoadouts[player.UserId] and not tool(player,'D'),'actual standard deck has A/B/C and no D')
 slot(player,'A','瞬影斬',nil)
 slot(player,'B','風走り',nil)
 slot(player,'C','千刃旋風',nil)
end
local function pose(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(origin,origin+Vector3.new(1,0,0))
 rootPart.AssemblyLinearVelocity=Vector3.zero
 rootPart.AssemblyAngularVelocity=Vector3.zero
 humanoid.PlatformStand=false
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false
 advanceTo(now+.39)
 local profile=session.swarm.getRoleGrowthSnapshot(player)
 check(profile and profile.role=='NINJA' and profile.stage==0 and profile.energy==100,'actual current Ninja S0/E100')
 return origin
end
local function energy(session) return session.swarm.getRoleGrowthSnapshot(player).energy end
local function signature() return player:GetAttribute('EGGRUMBLE_SkillCastSignature') end
local function effect(session,name) return session.world:FindFirstChild('P0D_NINJA_COMBO_'..name) end

function growthCases.ninja_hud_transition()
 selectKit()
 local first=ready('PRIVATE_NINJA_HUD_FIRST','NINJA')
 expectKit(first)
 local origin=pose(first)
 local actions,choices,skillUse,render=growthCases.existingHudInventory()
 actions.SKILL.Activated:Fire()
 check(choices[4].Visible and choices[4].Text=='技D・霞瞬歩','actual original HUD draws Ninja D as owned fourth choice')
 choices[4].Activated:Fire()
 check(render() and skillUse.Visible and skillUse.Text=='技D','HUD arms real fourth choice')
 local t=now
 skillUse.Activated:Fire()
 check(signature():match('^NINJA:D:') and energy(first)==20,'HUD invokes actual server Ninja D and exactly one E80 charge')
 advanceTo(t+.179)
 check((rootPart.Position-origin).Magnitude<.01 and effect(first,'BLINK_TELL'),'server direction warning precedes real move')
 advanceTo(t+.181)
 check(math.abs((rootPart.Position-origin).Magnitude-5)<.02 and effect(first,'SMOKE_TELL'),'actual moved avatar then placement warning')
 advanceTo(t+.29)
 local smoke=effect(first,'LOW_SMOKE')
 check(smoke and math.abs((smoke.Position-rootPart.Position).X)<.02 and smoke.Size.X==6,'actual local smoke at the authoritative landing')
 check(player:GetAttribute('EGGRUMBLE_StealthUntil')==nil,'new kit does not inherit old wind stealth')
 local old=first.world:FindFirstChild('NeutralHorde')
 parkOldSwarm(first)
 outsideField(first)
 finishAndClose(first,old)
 check(smoke.Parent==nil,'old effect cannot survive physical round close')
 trigger(player,stand(),'職業選択')
 trigger(player,stand(),'装備する')
 check(player:GetAttribute(LABEL)==nil,'explicit opt-out restores standard selection')
 local nextMatch=ready('PRIVATE_NINJA_HUD_STANDARD','NINJA')
 expectStandard(nextMatch)
 check(render() and skillUse.Visible and skillUse.Text=='技B','same HUD automatically falls back from removed D to legacy B')
 local oldOrigin=pose(nextMatch)
 skillUse.Activated:Fire()
 check(signature():match('^NINJA:B:') and energy(nextMatch)==100,'same button reaches original B without a role-growth charge')
 check((rootPart.Position-oldOrigin).Magnitude>24 and player:GetAttribute('EGGRUMBLE_StealthUntil')>now,
  'actual legacy SafeMove and original stealth remain usable')
 return 'real Ninja lobby opt-in and HUD D performs move then smoke; next match same HUD falls back to traditional B'
end

function growthCases.ninja_components()
 selectKit()
 local live=ready('PRIVATE_NINJA_COMPONENTS','NINJA')
 expectKit(live)
 local neutral=spawnCurrentNeutral(live)
 local origin=pose(live)
 local health=neutral:FindFirstChildOfClass('Humanoid')
 health.Health=96
 neutral:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 neutral:PivotTo(CFrame.new(origin+Vector3.new(8,1,0)))
 activate(player,'A')
 check(signature():match('^NINJA:A:') and health.Health<96 and energy(live)==100,
  'actual original A still damages a current neutral without a new energy cost')
 neutral:PivotTo(CFrame.new(origin+Vector3.new(-30,0,25)))
 local before=now
 activate(player,'B')
 check(signature():match('^NINJA:B:') and energy(live)==70,'actual B Tool charges E30')
 advanceTo(before+.181)
 check(math.abs((rootPart.Position-origin).Magnitude-5)<.02 and not effect(live,'SMOKE_TELL'),
  'actual B moves by 5 without creating smoke')
 local landed=rootPart.Position
 before=now
 local available=energy(live)
 activate(player,'C')
 check(signature():match('^NINJA:C:') and math.abs(energy(live)-(available-35))<.0001,
  'actual C Tool charges E35 independently, including any ordinary growth regeneration')
 advanceTo(before+.101)
 local smoke=effect(live,'LOW_SMOKE')
 check(smoke and smoke.Size.X==6 and (rootPart.Position-landed).Magnitude<.02,'actual C creates low smoke without moving')
 local previous=signature()
 available=energy(live)
 activate(player,'D')
 check(signature()==previous and energy(live)==available,'blocked compound cannot change signature or re-spend')
 return 'original A damages its neutral, real B moves, and C places smoke with separate Swarm clocks'
end

function growthCases.ninja_off_live()
 selectKit()
 local live=ready('PRIVATE_NINJA_ROLLBACK','NINJA')
 local origin=pose(live)
 local oldD=slot(player,'D','霞瞬歩','COMBO-008')
 local t=now
 activate(player,'D')
 local accepted=signature()
 check(energy(live)==20 and effect(live,'BLINK_TELL'),'current real D pending before flag change')
 advanceTo(t+.06)
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 expectStandard(live)
 check(oldD.Parent==nil and player:GetAttribute(LABEL)==nil,'actual OFF revokes old kit and clears UI choice')
 advanceTo(t+.31)
 check(signature()==accepted and energy(live)==20 and (rootPart.Position-origin).Magnitude<.02,
  'OFF cancels pending authoritative move with no invalid refund')
 check(not effect(live,'BLINK_TELL') and not effect(live,'SMOKE_TELL') and not effect(live,'LOW_SMOKE'),
  'actual OFF removes every effect')
 activate(player,'B')
 check(signature():match('^NINJA:B:') and player:GetAttribute('EGGRUMBLE_StealthUntil')>now,
  'fresh original B remains real after rollback in same match')
 return 'OFF retires pending D and grants only original A/B/C to the current live opted-in Ninja'
end

function growthCases.ninja_prompt_gates()
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(player,stand(),'装備する')
 check(player:GetAttribute(LABEL)==nil,'other selected role cannot enroll in Ninja kit')
 trigger(player,stand(),'職業選択')
 local first=ready('PRIVATE_NINJA_DEFAULT','NINJA',function()
  trigger(player,stand(),'装備する')
  check(player:GetAttribute(LABEL)==nil,'queued avatar cannot mutate pending kit')
 end)
 expectStandard(first)
 return 'actual proximity prompt restricts enrollment to the Ninja lobby before READY'
end

function growthCases.ninja_br()
 selectKit()
 local live=growthCases.readySoloBR('NINJA')
 expectKit(live)
 local origin=pose(live)
 local t=now
 activate(player,'D')
 advanceTo(t+.29)
 check(signature():match('^NINJA:D:') and energy(live)==20,'actual BR Tool D accepted for current BR player')
 check(math.abs((rootPart.Position-origin).Magnitude-5)<.02 and effect(live,'LOW_SMOKE'),
  'BR physical current world receives the actual ordered effects')
 return 'same selected Tool and physical arena constraints execute in actual BR host'
end

function growthCases.ninja_off_boot()
 local checked=false
 for _,prompt in ipairs(stand():GetChildren()) do
  if prompt:IsA('ProximityPrompt') and prompt.ActionText=='装備する' then
   check(not prompt.Enabled,'Ninja optional equip starts disabled when feature is OFF')
   checked=true
  end
 end
 check(checked,'actual OFF hides the existing option prompt')
 local live=ready('PRIVATE_NINJA_OFF_BOOT','NINJA')
 expectStandard(live)
 return 'initial flag OFF disables the lobby option and grants physical original Ninja A/B/C'
end
end
