do
local WATER_FLAG='P0D_ENABLE_PRIVATE_MAGE_WATER_CHAIN'
local H=96
local function equip(index)
 local stand=scenes:FindFirstChild('ROLE_MAGE')
 trigger(player,stand,'職業選択')
 for _=1,index do
  advanceTo(now+1.01)
  trigger(player,stand,'装備する')
 end
end
local function tool(actor,slot)
 for _,container in ipairs({actor:FindFirstChildOfClass('Backpack'),actor.Character})do
  for _,item in ipairs(container:GetChildren())do
   local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
   if type(id)=='string'and id:match('^EGGRUMBLE_SKILL_'..slot..'_') then return item end
  end
 end
 return nil
end
local function sessionOn()
 equip(4)
 check(player:GetAttribute('EGGRUMBLE_LobbyMageProjectileName')=='水弾＋連鎖雷','actual lobby cycle reaches water/lightning')
 local session=ready('PRIVATE_WATER_CHAIN_TEAM')
 check(session.mageProjectiles[player.UserId]=='MAGE-041','actual Host freezes water choice in TEAM snapshot')
 check(tool(player,'A').Name=='技A・水弾' and tool(player,'C').Name=='技C・連鎖雷'
  and tool(player,'D').Name=='技D・雷潮連環','four actual server-authorized role Tools with exact A/C/D names')
 check(tool(player,'B').Name=='技B・爆炎陣','unchanged middle Tool')
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'装備する')
 check(session.mageProjectiles[player.UserId]=='MAGE-041','lobby cannot replace a deployed water selection')
 return session
end
local function growth(session)
 local state=session.swarm.getRoleGrowthSnapshot(player)
 check(state and state.stage==0 and state.role=='MAGE','current authoritative S0/E is present')
 return state.energy
end
local function park(session,except,origin)
 for _,mob in ipairs(session.world:FindFirstChild('NeutralHorde'):GetChildren())do
  if mob~=except and mob:FindFirstChildOfClass('Humanoid') then
   mob:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
   mob:PivotTo(CFrame.new(origin+Vector3.new(-30,0,25)))
  end
 end
end
local function aim(root,at)
 root.CFrame=CFrame.new(at,at+Vector3.new(1,0,0))
end
local function pose(session)
 local neutral=spawnCurrentNeutral(session)
 local hum=neutral:FindFirstChildOfClass('Humanoid')
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(180,20,80)
 local aligned=origin+Vector3.new(5,1,0)
 neutral:SetAttribute('EGGRUMBLE_NeutralSpeed',0)
 neutral:PivotTo(CFrame.new(aligned))
 hum.Health=H
 aim(rootPart,origin)
 advanceTo(now+.39)
 park(session,neutral,origin)
 neutral:PivotTo(CFrame.new(aligned))
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={character,second.Character,session.world:FindFirstChild('NeutralHorde')}
 for _,bot in pairs(session.botActors or {}) do table.insert(params.FilterDescendantsInstances,bot) end
 params.RespectCanCollide=true
 check(workspace:Raycast(origin+Vector3.new(0,1,0),Vector3.new(8,0,0),params)==nil,'fixture starts in unobstructed lane')
 return neutral,hum,origin,aligned,growth(session)
end
local function waterMark(neutral)
 return neutral.PrimaryPart:FindFirstChild('WaterMarkStatus')
end
local function into(session,target,neutral,origin)
 local right=false
 while now+.24<target do
  right=not right
  aim(rootPart,origin+Vector3.new(0,0,if right then .7 else 0))
  advanceTo(now+.24)
  park(session,neutral,origin)
 end
 aim(rootPart,origin)
 advanceTo(target)
 park(session,neutral,origin)
end
local function sig()return player:GetAttribute('EGGRUMBLE_SkillCastSignature')end

function growthCases.water_a()
 local session=sessionOn()
 local neutral,hum,origin,aligned,before=pose(session)
 local t=now
 activate(player,'A')
 equal(hum.Health,H-16,'actual Tool A primary neutral HP once')
 equal(growth(session),before-30,'Tool A spends 30')
 check(type(sig())=='string'and sig():match('^MAGE:A:'),'server A receipt')
 local cue=waterMark(neutral)
 check(cue and cue:FindFirstChild('Status').Text:find('1.0秒',1,true),'S0 WaterMarkStatus text and initial lifetime')
 advanceTo(t+.55)
 check(waterMark(neutral)==cue and cue:FindFirstChild('Status').Text:find('0.5秒',1,true),'same water cue counts down')
 advanceTo(t+1.02)
 check(waterMark(neutral)==nil,'one-second water cue expires')
 into(session,t+11.99,neutral,origin)
 local signature=sig()
 activate(player,'A')
 check(sig()==signature,'standalone A rejects before exact 12-second deadline')
 into(session,t+12.02,neutral,origin)
 neutral:PivotTo(CFrame.new(aligned))
 local prior=hum.Health
 activate(player,'A')
 equal(hum.Health,prior-16,'standalone A releases after exact 12-second deadline')
 return 'Host equip then actual Tool A HP −16/E30, S0 cue 1.0→0.5→absent and 12s CD'
end

function growthCases.lightning_c()
 local session=sessionOn()
 local neutral,hum,origin,aligned,before=pose(session)
 local t=now
 activate(player,'C')
 equal(hum.Health,H,'Tool C no immediate HP write')
 check(session.world:FindFirstChild('P0D_MAGE_CHAIN_TELL')~=nil,'actual lightning warning Part')
 equal(growth(session),before-40,'Tool C E40 once')
 advanceTo(t+.239)
 equal(hum.Health,H,'Tool C has full .24s warning')
 advanceTo(t+.241)
 equal(hum.Health,H-16,'Tool C exactly one S0 hit at .24')
 check(session.world:FindFirstChild('P0D_MAGE_CHAIN_HIT')~=nil,'actual approved hit arc')
 advanceTo(t+1)
 equal(hum.Health,H-16,'no duplicate delayed C hit')
 into(session,t+20.02,neutral,origin)
 neutral:PivotTo(CFrame.new(aligned))
 local wall=Instance.new('Part')
 wall.Name='Native_Selected_Chain_Wall';wall.Size=Vector3.new(1,12,12)
 wall.CFrame=CFrame.new(origin+Vector3.new(2,1,0));wall.CanCollide=true;wall.CanQuery=true
 local cast=now
 activate(player,'C')
 wall.Parent=session.world
 advanceTo(cast+.28)
 equal(hum.Health,H-16,'new obstruction after real tell rejects fixed first target')
 return 'actual C E40 and visible .24s tell; actual solid between tell/impact prevents damage'
end

function growthCases.combo_d()
 local session=sessionOn()
 local neutral,hum,_,_,before=pose(session)
 local t=now
 activate(player,'D')
 local signature=sig()
 check(signature and signature:match('^MAGE:D:'),'real D receipt')
 equal(growth(session),before-80,'Tool D debits E80 once')
 equal(hum.Health,H,'D opener marks and does not damage')
 check(waterMark(neutral)~=nil and session.world:FindFirstChild('P0D_MAGE_CHAIN_TELL')~=nil,'D water mark and tell visible')
 activate(player,'D')
 check(sig()==signature,'repeated Tool D not accepted')
 equal(growth(session),before-80,'repeat cannot debit')
 advanceTo(t+.239)
 equal(hum.Health,H,'D full .24s tell protects neutral')
 advanceTo(t+.241)
 equal(hum.Health,H-16,'D one S0 lightning reaction after water')
 check(session.world:FindFirstChild('P0D_MAGE_CHAIN_HIT')~=nil,'real combo approved impact arc')
 advanceTo(t+.35)
 check(waterMark(neutral)==nil,'direct mark consumed without waiting natural expiry')
 advanceTo(t+1.1)
 equal(hum.Health,H-16,'D delayed effects do not repeat damage')
 equal(session.swarm.getTotal(),0,'fixed hit does not fabricate KO')
 return 'actual D only one E80, one after-tell hit, one direct water mark consumed'
end

local function component(slot,seconds,energy)
 local session=sessionOn()
 local neutral,hum,origin,aligned,before=pose(session)
 local t=now
 activate(player,'D')
 equal(growth(session),before-80,'D must be accepted first')
 local signature=sig()
 into(session,t+seconds-.02,neutral,origin)
 neutral:PivotTo(CFrame.new(aligned))
 local available=growth(session)
 check(available>=energy,'recharged above ability cost before its deadline; have '..available..' need '..energy)
 activate(player,slot)
 check(sig()==signature,'D locks slot '..slot..' at '..seconds..'s−.02')
 equal(growth(session),available,'blocked component costs no energy')
 into(session,t+seconds+.02,neutral,origin)
 neutral:PivotTo(CFrame.new(aligned))
 available=growth(session)
 activate(player,slot)
 check(sig()~=signature and sig():match('^MAGE:'..slot..':'),'D atomically releases each component at exact source deadline')
 equal(growth(session),available-energy,'newly accepted component debits exact source cost')
 return 'actual D separately arms slot '..slot..' for '..seconds..'s; sufficient E before and after edge'
end
function growthCases.component_a()return component('A',12,30)end
function growthCases.component_c()return component('C',20,40)end
function growthCases.component_d()return component('D',40,80)end
function growthCases.component_guard()
 local session=sessionOn()
 local neutral,hum,origin,aligned=pose(session)
 local started=now
 activate(player,'A')
 local signature=sig()
 into(session,started+5,neutral,origin)
 neutral:PivotTo(CFrame.new(aligned))
 local energy=growth(session)
 check(energy>=80,'recovered at least E80 while A remains locked')
 activate(player,'D')
 check(sig()==signature and session.world:FindFirstChild('P0D_MAGE_CHAIN_TELL')==nil,
  'one unavailable component rejects D before telegraph/receipt')
 equal(growth(session),energy,'atomic rejection does not spend E80')
 activate(player,'C')
 check(sig()~=signature and sig():match('^MAGE:C:'),'failed D leaves C usable')
 equal(growth(session),energy-40,'unblocked C takes only its own E40')
 advanceTo(now+.26)
 equal(hum.Health,H-32,'A and independent C both actually damage one neutral')
 return 'live A lock rejects D atomically with E80 available; C retains its own acceptance and damage'
end

local function negative(kind)
 local session=sessionOn()
 local neutral,hum,_,_,before=pose(session)
 local t=now
 activate(player,'D')
 equal(growth(session),before-80,'one lawful combo start before invalidation')
 check(waterMark(neutral)~=nil,'water mark before authority loss')
 advanceTo(t+.1)
 if kind=='avatar' then player.Character=Instance.new('Model')
 elseif kind=='exit' then
  Players.PlayerRemoving:Fire(player)
  drainDeferred()
  check(not session.isCurrentHuman(player) and session.isCurrentHuman(second),'actual Host removing only the owner')
 elseif kind=='egg' then
  session.rules.castles[tostring(player.UserId)].heldEggs=1
  check(session.swarm.getRoleGrowthSnapshot(player)==nil,'actual egg carry invalidates caster')
 elseif kind=='off' then workspace:SetAttribute(WATER_FLAG,false)
 end
 advanceTo(t+.48)
 equal(hum.Health,H,'stale D impact must not damage after '..kind)
 check(session.world:FindFirstChild('P0D_MAGE_CHAIN_HIT')==nil and waterMark(neutral)==nil,'cue/mark cleared and no hit after '..kind)
 return 'actual warned D cancels and cue clears on '..kind
end
function growthCases.negative_avatar()return negative('avatar')end
function growthCases.negative_exit()return negative('exit')end
function growthCases.negative_egg()return negative('egg')end
function growthCases.negative_off()return negative('off')end

local function legacy(physicalOff)
 if physicalOff then workspace:SetAttribute(WATER_FLAG,false) end
 equip(0)
 local session=ready('PRIVATE_LEGACY_STANDARD')
 check(not session.mageProjectiles[player.UserId] and tool(player,'D')==nil,'old Mage receives no compound slot')
 check(tool(player,'A').Name=='技A・氷弾' and tool(player,'B').Name=='技B・爆炎陣' and tool(player,'C').Name=='技C・雷光治癒',
  'old Mage gets existing Ice/Fire/Heal actions')
 local neutral,hum,origin,_,before=pose(session)
 for _,item in ipairs({{'A',25,30},{'B',21,52},{'C',14,42}})do
  hum.Health=H
  neutral:PivotTo(CFrame.new(origin+Vector3.new(item[2],1,0)))
  if item[1]=='C' then humanoid.Health=50 end
  activate(player,item[1])
  equal(hum.Health,H-item[3],'actual legacy neutral damage for '..item[1])
  equal(growth(session),before,'old cooldown, no growth charge for '..item[1])
  if item[1]=='C' then check(humanoid.Health>50,'actual legacy C still heals') end
 end
 return 'actual no-D standard A/B/C tools, neutral damage and legacy healing preserved'
end
function growthCases.old_standard()return legacy(false)end
function growthCases.off()
 workspace:SetAttribute(WATER_FLAG,false)
 equip(4)
 check(player:GetAttribute('EGGRUMBLE_LobbyMageProjectileName')=='氷弾','physical OFF leaves previous four-step cycle')
 return legacy(true)
end
function growthCases.old_projectile()
 equip(1)
 local session=ready('PRIVATE_LEGACY_WIND')
 check(session.mageProjectiles[player.UserId]=='MAGE-033' and tool(player,'D')==nil,'old Wind selection untouched')
 local _,hum,_,_,before=pose(session)
 local t=now
 activate(player,'A')
 equal(hum.Health,H,'old moving Wind is not instant water')
 equal(growth(session),before-30,'old Wind keeps own E30')
 advanceTo(t+.28)
 check(hum.Health<H,'old actual flight applies damage')
 return 'previous Wind option still uses genuine old flight and unaffected Tool inventory'
end

local function hudOnActualInventory()
 local actions={SKILL={Activated=signal()},ITEM={Activated=signal()},ATTACK={},DODGE={}}
 local mapSnapshot={mode='TEAM'}
 local playerGui={FindFirstChild=function()return nil end}
 local gui={}
 local function button()return {Activated=signal()}end
 local function frame()return {}end
 __HUD_DRAWER__
 __HUD_SELECTED_USE__
 local function render()
 local char=player.Character
 local h=char and char:FindFirstChildOfClass('Humanoid')
 __HUD_SELECTED_RENDER__
 return inMatch
 end
 return actions,choices,skillUse,render
end

function growthCases.hud_loadout_transition()
 local first=sessionOn()
 local actions,choices,skillUse,render=hudOnActualInventory()
 actions.SKILL.Activated:Fire()
 check(choices[4].Visible and choices[4].Text=='技D・雷潮連環','actual HUD exposes owned D at the 4th row')
 choices[4].Activated:Fire()
 check(render() and skillUse.Visible and skillUse.Text=='技D','actual in-match HUD selects owned D')
 local _,firstHealth=pose(first)
 local cast=now
 skillUse.Activated:Fire()
 check(sig():match('^MAGE:D:'),'actual HUD selected skill reaches original Tool.Activated event')
 advanceTo(cast+.25)
 equal(firstHealth.Health,H-16,'the HUD D button reaches an actual after-tell neutral hit')
 local old=first.world:FindFirstChild('NeutralHorde')
 parkOldSwarm(first)
 outsideField(first)
 finishAndClose(first,old)
 equip(1) -- The prior choice persists at lobby; the next equip-prompt step is standard Ice.
 check(player:GetAttribute('EGGRUMBLE_LobbyMageProjectileName')=='氷弾','real lobby offer changes water option to Ice')
 local nextRound=ready('PRIVATE_HUD_NEXT_STANDARD')
 check(nextRound.mageProjectiles[player.UserId]~='MAGE-041' and tool(player,'B')~=nil and tool(player,'D')==nil,
  'actual next session grants legacy B and omits D')
 check(render() and skillUse.Visible and skillUse.Text=='技B',
  'STALE_D_SELECTED_BUTTON_MISSING: Visible='..tostring(skillUse.Visible)..';text='..tostring(skillUse.Text))
 local neutral,secondHealth,origin=pose(nextRound)
 neutral:PivotTo(CFrame.new(origin+Vector3.new(21,1,0)))
 skillUse.Activated:Fire()
 check(sig():match('^MAGE:B:'),'same HUD now reaches the original B Tool.Activated')
 equal(secondHealth.Health,H-52,'fallback B keeps real legacy damage')
 return 'same HUD casts actual D in first Host match, then falls back and casts actual legacy B in the next'
end
end
