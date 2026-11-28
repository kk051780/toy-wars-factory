do
local FLAG="P0D_ENABLE_PRIVATE_WARRIOR_TECH"
local direction=Vector3.new(1,0,0)
local rows={
 half={id="WARRIOR-001",kit=1,slot="A",energy=30,cd=15,tell=.28},
 split={id="WARRIOR-003",kit=1,slot="B",energy=30,cd=14,tell=.23},
 twin={id="WARRIOR-005",kit=1,slot="C",energy=40,cd=20,tell=.26},
 spin={id="WARRIOR-008",kit=2,slot="A",energy=40,cd=24,tell=.35},
 spear={id="WARRIOR-015",kit=2,slot="B",energy=40,cd=24,tell=.36},
 charge={id="WARRIOR-091",kit=2,slot="C",energy=35,cd=21,tell=.8},
 diamond={id="WARRIOR-018",kit=3,slot="A",energy=40,cd=24,pct=.08,life=1},
 parry={id="WARRIOR-021",kit=3,slot="B",energy=30,cd=18,pct=.12,life=.6},
 side={id="WARRIOR-027",kit=3,slot="C",energy=35,cd=22,pct=.08,life=1},
}
local names={"剣の三技","間合い三技","守りの三技"}
local function tools()
 local result={}
 for _,container in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,tool in ipairs(container:GetChildren()) do
   local value=tool:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(value)=="string" and value:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then check(not result[slot],"one current physical Tool per slot");result[slot]=tool end
  end
 end
 return result
end
local function standard()
 local deck=tools()
 check(deck.A.Name=="技A・飛翔斬撃" and deck.B.Name=="技B・槍陣突撃" and deck.C.Name=="技C・神憑き" and not deck.D,
  "real original Warrior A/B/C and no D")
end
local function start(row)
 local stand=scenes:FindFirstChild("ROLE_WARRIOR")
 trigger(player,stand,"職業選択")
 if row then
  for index=1,row.kit do
   trigger(player,stand,"剣技を装備")
   check(player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName")==names[index],"real authorized standby selection")
   advanceTo(now+.51)
  end
 end
 local live=ready("PRIVATE_WARRIOR_TECH","WARRIOR")
 if row then
  local tool=tools()[row.slot]
  check(tool and tool:GetAttribute("EGGRUMBLE_FixedAbilityId")==row.id
   and tool.ToolTip:find("E"..row.energy,1,true) and tool.ToolTip:find(tostring(row.cd).."s",1,true),
   "exact fixed Tool with energy and cooldown description")
 else standard() end
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local origin=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(origin,origin+direction)
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.MoveDirection=Vector3.zero
 return live,floor
end
local function gather(live,base,count)
 local mobs={}
 for _=1,48 do
  table.clear(mobs)
  for _,model in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   local hp=model:FindFirstChildOfClass("Humanoid")
   if hp and hp.Health>0 and model.PrimaryPart then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(base+Vector3.new(-37,2,35)))
    table.insert(mobs,{model=model,hp=hp})
   end
  end
  if #mobs>=count then break end
  advanceTo(now+.35)
 end
 check(#mobs>=count,"real existing Spawn owns each target")
 return mobs
end
local function put(entry,at)
 local y=2*(entry.model.PrimaryPart.Size.Y/2.5)
 local where=at+Vector3.new(0,y,0)
 entry.model:PivotTo(CFrame.new(where));entry.hp.Health=150
 entry.model:SetAttribute("EGGRUMBLE_NeutralSpecies","BANNER_KNIGHT")
 return where
end
local function effect(live,row,guard)
 return live.world:FindFirstChild("EGGRUMBLE_WarriorTech_"..row.id..(if guard then "_Guard" else "_Tell"))
end
local function cast(live,row)
 local t=now
 activate(player,row.slot)
 local state=live.swarm.getRoleGrowthSnapshot(player)
 local signature=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 check(state and state.energy==100-row.energy and signature and signature:match("^WARRIOR:"..row.slot..":"),
  "true existing Growth accepted one actual cast")
 activate(player,row.slot)
 check(live.swarm.getRoleGrowthSnapshot(player).energy==100-row.energy
  and player:GetAttribute("EGGRUMBLE_SkillCastSignature")==signature,"immediate re-use retains one debit")
 return t
end
local function approx(a,b) return math.abs(a-b)<.011 end
local function wall(live,position)
 local part=Instance.new("Part")
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true
 part.Size=Vector3.new(.2,8,6);part.CFrame=CFrame.new(position);part.Parent=live.world
end

local function attack(key,row)
 local live,floor=start(row)
 local mobs=gather(live,floor,3)
 local offsets=if key=="half" then {{2.55,-.6},{4.15,1.55},{-2.4,0}}
  elseif key=="split" then {{4.6,.15},{3,1.3},{5.7,0}}
  elseif key=="twin" then {{2.25,-2},{2.35,1.95},{-2.4,0}}
  elseif key=="spin" then {{-2.2,0},{.35,1.75},{3.9,.25}}
  elseif key=="spear" then {{6.65,0},{7.7,0},{5.4,1.7}}
  else {{4.2,0},{2.9,1.75},{4.9,0}}
 local first
 for index,v in ipairs(offsets) do
  local at=put(mobs[index],floor+Vector3.new(v[1],0,v[2]))
  if index==1 then first=at end
 end
 local t=cast(live,row)
 local tell=effect(live,row)
 check(tell and #tell:GetChildren()>0,"physical noninteractive warning")
 advanceTo(t+row.tell-.001)
 check(mobs[1].hp.Health==150 and mobs[2].hp.Health==150 and mobs[3].hp.Health==150,"bounded tell leaves HP unchanged")
 if key=="twin" then
  advanceTo(t+row.tell+.001)
  check(mobs[1].hp.Health<150 and mobs[2].hp.Health==150,"first legal left beat only")
  local left=mobs[1].hp.Health
  advanceTo(t+row.tell+.302)
  check(mobs[1].hp.Health==left and mobs[2].hp.Health<150 and mobs[3].hp.Health==150,
   "second right beat shares one cast budget; no duplicate left hit")
 elseif key=="spear" then
  advanceTo(t+.43)
  check(live.world:FindFirstChild("EGGRUMBLE_WarriorSpearShadow") and mobs[1].hp.Health==150,
   "existing continuous sweep travels before confirmed contact")
  advanceTo(t+.93)
  check(mobs[1].hp.Health<150 and mobs[2].hp.Health==150 and mobs[3].hp.Health==150,
   "first actual S0 contact exhausts spear cap")
 else
  advanceTo(t+row.tell+.001)
  local two=key=="half" or key=="spin"
  check(mobs[1].hp.Health<150 and (mobs[2].hp.Health<150)==two and mobs[3].hp.Health==150,
   "shared exact current neutral authority applies only in geometry/cap")
  if key=="half" then
   check(mobs[1].model.PrimaryPart.Position.X>first.X+.4,"legal real flinch through existing neutral sweep")
  end
 end
 check(not tell.Parent and live.swarm.getTotal()==0,"warning removed; actual HP and no ghost KO")
 return row.id.." actual Tool completes its own warning, geometry and bounded neutral HP"
end
for _,key in ipairs({"half","split","twin","spin","spear","charge"}) do
 growthCases["wtech_"..key]=function() return attack(key,rows[key]) end
end

local function defense(key,row,wrong)
 local live,floor=start(row)
 local mobs=gather(live,floor,1)
 if key=="side" then humanoid.MoveDirection=Vector3.new(0,0,-1) end
 local casterHealth=humanoid.Health
 local t=cast(live,row)
 local tell=effect(live,row,true)
 check(tell and dependencies.EGGRUMBLE_InvulRuntime.currentPolicySnapshot(player).phase=="NONE","finite guard has no invulnerability state")
 local forward=if key=="side" and not wrong then Vector3.new(0,0,-3.2)
  elseif key=="diamond" and wrong then Vector3.new(-3.2,0,0) else Vector3.new(3.2,0,0)
 put(mobs[1],floor+forward)
 advanceTo(t+.39)
 check(approx(casterHealth-humanoid.Health,4*(if wrong then 1 else 1-row.pct)),
  "true ordinary Swarm melee keeps positive damage with the precise admitted multiplier")
 if key=="diamond" or wrong then check(tell.Parent==live.world,"persistent or missed guard should keep its window")
 else check(not tell.Parent,"one real hit consumes a one-shot guard") end
 put(mobs[1],floor+Vector3.new(-41,0,32))
 advanceTo(t+row.life+.002)
 check(not tell.Parent,"bounded expiry cannot leave stance in world")
 return row.id.." actual Swarm melee uses precise finite guard, original HP and direction, no immunity"
end
for _,key in ipairs({"diamond","parry","side"}) do
 growthCases["wtech_"..key]=function() return defense(key,rows[key],false) end
end
function growthCases.wtech_guard_back() return defense("diamond",rows.diamond,true) end
function growthCases.wtech_guard_wrong_side() return defense("side",rows.side,true) end

function growthCases.wtech_guard_live_pvp()
 local row=rows.diamond
 local live,floor=start(row)
 local from=floor+Vector3.new(20,3,0)
 secondRoot.CFrame=CFrame.lookAt(from,from-direction)
 local old=humanoid.Health
 cast(live,row)
 activate(second,"A")
 check(approx(old-humanoid.Health,44*.92),
  "same current verified hostile player's normal A applies one finite front multiplier")
 return "existing separate PvP hit travels through the same guard pre-hit factor"
end

function growthCases.wtech_guard_round()
 local row=rows.diamond
 local live=start(row)
 cast(live,row)
 local tell=effect(live,row,true)
 check(tell and tell.Parent==live.world,"arm the actual guard before termination")
 live.rules.phase="FINISHED"
 live.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED")
 drainDeferred()
 check(not tell.Parent,"completed round does not wait for guard timeout")
 return "actual phase end removes that active finite guard immediately"
end

function growthCases.wtech_switch_kits()
 local stand=scenes:FindFirstChild("ROLE_WARRIOR")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"剣技を装備")
 check(player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName")=="剣の三技","J selects the new technique deck")
 advanceTo(now+.51)
 trigger(player,stand,"装備する")
 check(not player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName")
  and player:GetAttribute("EGGRUMBLE_LobbyWarriorLoadoutName")== "炎刃・光輪刃・炎輪剣舞","F preserves its original Fire deck")
 advanceTo(now+.51)
 trigger(player,stand,"剣技を装備")
 check(not player:GetAttribute("EGGRUMBLE_LobbyWarriorLoadoutName")
  and player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName")=="剣の三技","J switches back without stale Fire choice")
 advanceTo(now+.51)
 trigger(player,stand,"天翼を装備")
 workspace:SetAttribute(FLAG,false);drainDeferred()
 check(not player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName")
  and player:GetAttribute("EGGRUMBLE_LobbyWarriorSkyLoadoutName")=="天界百剣・天翼武装・天翼剣雨",
  "old G choice survives independent new flag OFF")
 local live=ready("PRIVATE_WARRIOR_OLD_SKY","WARRIOR")
 local deck=tools()
 check(live.warriorSkyLoadouts[player.UserId]==true and not live.warriorTechLoadouts[player.UserId]
  and deck.D:GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-001","same official Host/Tool carries actual G kit into match")
 return "same physical stand keeps J, F and G independent and reaches real legacy G Tools"
end

local function denied(kind)
 local row=if kind=="guard_shield" or kind=="guard_off" then rows.diamond else rows.charge
 local live,floor=start(row)
 local mobs=gather(live,floor,1)
 local target=mobs[1]
 put(target,floor+Vector3.new(4.15,0,0))
 if kind=="carrier" or kind=="guard_shield" then
  if kind=="carrier" then live.rules.castles[tostring(player.UserId)].heldEggs=1
  else local shield=Instance.new("ForceField");shield.Parent=player.Character end
  activate(player,row.slot)
  live.rules.castles[tostring(player.UserId)].heldEggs=0
  check(live.swarm.getRoleGrowthSnapshot(player).energy==100 and not effect(live,row,kind=="guard_shield")
   and not player:GetAttribute("EGGRUMBLE_SkillCastSignature"),"already held egg or immunity rejects without charge")
  return "real owner denies "..kind
 end
 local t=cast(live,row)
 if kind=="wall" then wall(live,floor+Vector3.new(2,2.6,0))
 elseif kind=="avatar" then player.CharacterRemoving:Fire(player.Character);player.Character=Instance.new("Model")
 else
  local stale=tools()[row.slot]
  workspace:SetAttribute(FLAG,false)
  drainDeferred();standard()
  stale.Activated:Fire()
 end
 if kind=="guard_off" then put(target,floor+Vector3.new(3.1,0,0));advanceTo(t+.39)
  check(approx(humanoid.Health,96),"runtime OFF restores full ordinary damage without stale finite stance")
 end
 advanceTo(t+1.02)
 check(target.hp.Health==150 and not effect(live,row,kind=="guard_off"),"late failure protects original ownership")
 return "real warning, guard or damage cancels on "..kind
end
for _,kind in ipairs({"wall","avatar","off","guard_off","carrier","guard_shield"}) do
 growthCases["wtech_deny_"..kind]=function() return denied(kind) end
end

function growthCases.wtech_physical_off()
 start(nil)
 for _,prompt in ipairs(scenes:FindFirstChild("ROLE_WARRIOR"):GetChildren()) do
  check(not prompt:IsA("ProximityPrompt") or prompt.ActionText~="剣技を装備","unmodified OFF has no new offer")
 end
 return "physical parent retains real old Warrior selection and default A/B/C"
end
end
