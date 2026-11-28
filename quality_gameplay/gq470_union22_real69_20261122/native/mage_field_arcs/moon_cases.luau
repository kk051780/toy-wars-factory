do
local FLAG="P0D_ENABLE_PRIVATE_BEAST_MOON"
local LABEL="EGGRUMBLE_LobbyBeastMoonLoadoutName"
local function deck()
 local tools={}
 for _,folder in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(folder:GetChildren()) do
   local id=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(id)=="string" and id:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then tools[slot]=item end
  end
 end
 return tools
end
local function old(tools)
 check(tools.A.Name=="技A・獣牙撃" and tools.B.Name=="技B・巨獣餌" and tools.C.Name=="技C・分裂餌" and not tools.D,
  "original standard Beast A/B/C")
end
local function start(enabled)
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 if enabled then
  check(workspace:GetAttribute(FLAG)==nil,"normal optional deck is available on actual private default")
  trigger(player,stand,"月狼を装備")
  check(player:GetAttribute(LABEL)=="月冠神狼・月狼円陣","real current lobby Moon selection")
 end
 local s=ready("PRIVATE_BEAST_MOON","BEAST")
 local tools=deck()
 if enabled then
  check(s.beastMoonLoadouts[player.UserId] and not s.beastOrderLoadouts[player.UserId]
   and not s.beastThunderLoadouts[player.UserId],"one current owned deck")
  check(tools.A:GetAttribute("EGGRUMBLE_FixedAbilityId")=="BEAST-020"
   and tools.C:GetAttribute("EGGRUMBLE_FixedAbilityId")=="BEAST-095"
   and tools.D:GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-017"
   and tools.B.Name=="技B・巨獣餌","actual A/C/D fixed and original B unchanged")
 else old(tools) end
 return s
end
local function mark(s,suffix)
 return s.world:FindFirstChild("EGGRUMBLE_BeastMoon"..suffix)
end
local function witness(s)
 local pet=nil
 for _,model in ipairs(s.world:GetChildren()) do
  if model:GetAttribute("EGGRUMBLE_BeastCompanion")==true then
   check(not pet,"no new escort bodies");pet=model
  end
 end
 return pet
end
local function pose(s,needed)
 local one=spawnCurrentNeutral(s)
 check(one,"actual neutral spawn")
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local center=floor.Position+Vector3.new(170,floor.Size.Y*.5,-115)
 rootPart.CFrame=CFrame.lookAt(center+Vector3.new(-5,3,0),center+Vector3.new(0,3,0))
 secondRoot.CFrame=CFrame.new(center+Vector3.new(-42,3,0))
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 local rows={}
 for _=1,38 do
  table.clear(rows)
  for _,model in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   local h=model:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(center+Vector3.new(-55,3,29)))
    table.insert(rows,{model=model,h=h})
   end
  end
  if #rows>=needed then break end
  advanceTo(now+.30)
 end
 advanceTo(now+.39)
 check(#rows>=needed and s.swarm.getRoleGrowthSnapshot(player).energy==100,"real S0 membership and spawned targets")
 return center,rows
end
local function summon(s,center)
 activate(player,"B")
 local pet=witness(s)
 check(pet and pet:GetAttribute("EGGRUMBLE_OwnerId")==player.UserId,"unchanged physical B created one original owned pet")
 local h=pet:FindFirstChildOfClass("Humanoid")
 h.FloorMaterial=Enum.Material.Grass
 local at=center+Vector3.new(0,1.55,0)
 pet:PivotTo(CFrame.lookAt(at,at+Vector3.new(1,0,0)))
 return pet,h,at
end
local function move(row,at,hp)
 row.model:PivotTo(CFrame.new(at))
 row.h.Health=hp or 96
end
local function stamina(s)
 local state=s.swarm.getRoleGrowthSnapshot(player)
 return state and state.energy
end
local function tag()
 return player:GetAttribute("EGGRUMBLE_SkillCastSignature")
end
local function barrier(s,at)
 local fixture=Instance.new("Part")
 fixture.Name="NativeMoonWall"
 fixture.Size=Vector3.new(.5,8,9);fixture.CFrame=CFrame.new(at)
 fixture.Anchored=true;fixture.CanCollide=true;fixture.CanQuery=true;fixture.Parent=s.world
 return fixture
end

function growthCases.moon020_charge()
 local s=start(true)
 local center,rows=pose(s,2)
 local pet,h,at=summon(s,center)
 local koBefore=s.swarm.getTotal()
 move(rows[1],center+Vector3.new(3.7,2.2,0))
 move(rows[2],center+Vector3.new(5.1,2.2,0))
 secondRoot.CFrame=CFrame.new(center+Vector3.new(6,2,2.9))
 local hp,castle=secondHumanoid.Health,s.rules.castles[tostring(second.UserId)].hp
 local t=now
 activate(player,"A")
 check(mark(s,"ChargeTell") and stamina(s)==55 and tag():match("^BEAST:A:"),"actual A E45 and real lane warning")
 advanceTo(t+.399)
 check((pet.PrimaryPart.Position-at).Magnitude<.01 and rows[1].h.Health==96,"full warning before movement and HP")
 advanceTo(t+.58)
 check(pet.PrimaryPart.Position.X>at.X+2 and pet.PrimaryPart.Position.X<at.X+5 and pet.PrimaryPart.Anchored,
  "same authority physically moved the original pet")
 advanceTo(t+.79)
 check((pet.PrimaryPart.Position-(at+Vector3.new(6,0,0))).Magnitude<.03 and not pet.PrimaryPart.Anchored
  and not mark(s,"Formation") and not mark(s,"ChargeTell") and witness(s)==pet,"six-stud physical stop and no bonus guard on standalone")
 check(rows[1].h.Health==90 and rows[2].h.Health==96 and s.swarm.getTotal()==koBefore,
  ("S0 one actual neutral takes old contact 6 HP, actual %s/%s KO%s"):format(rows[1].h.Health,rows[2].h.Health,s.swarm.getTotal()))
 check(secondHumanoid.Health==hp-4 and s.rules.castles[tostring(second.UserId)].hp==castle and h.Health==60,
  ("nearby foe receives only the original 4HP Swarm melee, got %s of %s, pet %s"):format(secondHumanoid.Health,hp,h.Health))
 return "existing one escort moves six actual studs after warning and makes one admitted neutral-only hit"
end

function growthCases.moon095_guard()
 local s=start(true)
 local center,rows=pose(s,2)
 local pet,h,at=summon(s,center)
 move(rows[1],center+Vector3.new(3,2.15,0))
 move(rows[2],center+Vector3.new(4.5,2.15,0))
 local t=now
 activate(player,"C")
 local guard=mark(s,"Formation")
 check(guard and guard.Size.Y==8 and not guard.CanCollide and stamina(s)==65 and tag():match("^BEAST:C:"),
  "actual C deploys S0 radius4 at same escort")
 check(h._nativeMoveGoal==at,"original Humanoid stays in its ordered formation point")
 advanceTo(t+.43)
 check(rows[1].h.Health==90 and rows[2].h.Health==96,"the existing contact damage picks only a valid nearby neutral")
 advanceTo(t+1.02)
 check(rows[1].h.Health==90,"same contact cadence prevents continuous damage")
 advanceTo(t+2.01)
 check(not mark(s,"Formation") and witness(s)==pet,"exact short guard expiry preserves the same model")
 return "actual C holds one radius-four circle with old contact cadence and timed return to normal behavior"
end

function growthCases.moon017_combo()
 local s=start(true)
 local center,rows=pose(s,2)
 local pet,h,at=summon(s,center)
 local koBefore=s.swarm.getTotal()
 move(rows[1],center+Vector3.new(3.8,2.15,0),4)
 move(rows[2],center+Vector3.new(5.5,2.15,0),96)
 local t=now
 activate(player,"D")
 local accepted=tag()
 check(stamina(s)==20 and accepted:match("^BEAST:D:") and mark(s,"ChargeTell") and not mark(s,"Formation"),
  "one accepted E80 and no early guard")
 activate(player,"D")
 check(tag()==accepted and stamina(s)==20,"same D cannot double debit")
 advanceTo(t+.59)
 check(not mark(s,"Formation") and pet.PrimaryPart.Anchored and pet.PrimaryPart.Position.X>at.X+2,
  "no formation during physically observed charge")
 advanceTo(t+.83)
 local settled=mark(s,"Formation")
 check(witness(s)==pet and not pet.PrimaryPart.Anchored and settled and (pet.PrimaryPart.Position-at).Magnitude>=5.98
  and settled.Size.Y==8 and h._nativeMoveGoal==pet.PrimaryPart.Position,"same settled actual pet proves the formation")
 check(rows[1].h.Health==0 and rows[2].h.Health==96 and s.swarm.getTotal()==koBefore+1,
  ("one actual neutral death, got %s/%s KO%s"):format(rows[1].h.Health,rows[2].h.Health,s.swarm.getTotal()))
 for _,id in ipairs({"BEAST-020","BEAST-095","COMBO-017"}) do
  check(s.swarm.tryRoleGrowthCast(player,"BEAST",1,1,{[id]=1})==nil,"exact current combo/component deadlines")
 end
 advanceTo(t+2.93)
 check(not mark(s,"Formation") and witness(s)==pet,"guard retires while underlying escort remains")
 return "D pays E80 once, actual charge and stop then one ordered circle, one original KO and all deadlines"
end

function growthCases.moon_late_wall()
 local s=start(true)
 local center,rows=pose(s,1)
 local pet,_,at=summon(s,center)
 local koBefore=s.swarm.getTotal()
 move(rows[1],center+Vector3.new(5.5,2.15,0))
 local t=now
 activate(player,"D")
 advanceTo(t+.505)
 check(pet.PrimaryPart.Anchored and pet.PrimaryPart.Position.X>at.X+.7,"real motion before late cover")
 barrier(s,center+Vector3.new(4.1,2,0))
 advanceTo(t+.86)
 check(not pet.PrimaryPart.Anchored and pet.PrimaryPart.Position.X<at.X+3.2 and not mark(s,"Formation")
  and rows[1].h.Health==96 and s.swarm.getTotal()==koBefore,
  ("late wall actual X movement=%s anchored=%s guard=%s HP=%s"):format(pet.PrimaryPart.Position.X-at.X,
   tostring(pet.PrimaryPart.Anchored),tostring(mark(s,"Formation")),rows[1].h.Health))
 return "a new solid wall stops the original pet before contact, and cannot produce a step or guard"
end

function growthCases.moon_denials()
 local s=start(true)
 local center,rows=pose(s,1)
 activate(player,"A");activate(player,"C");activate(player,"D")
 check(not witness(s) and stamina(s)==100,"without real owner pet all commands reject")
 local pet=summon(s,center)
 move(rows[1],center+Vector3.new(5.5,2.15,0))
 rows[1].model:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",tostring(second.UserId))
 activate(player,"A");activate(player,"D")
 check(not mark(s,"ChargeTell") and stamina(s)==100,"friendly neutral never qualifies")
 rows[1].model:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",nil)
 local cover=barrier(s,center+Vector3.new(3,2,0))
 activate(player,"A");activate(player,"D")
 check(not mark(s,"ChargeTell") and stamina(s)==100,"known blocked lane never charges")
 cover:Destroy()
 s.rules.castles[tostring(player.UserId)].heldEggs=1
 activate(player,"A");activate(player,"C");activate(player,"D")
 s.rules.castles[tostring(player.UserId)].heldEggs=0;advanceTo(now+.42)
 check(stamina(s)==100 and witness(s)==pet and not mark(s,"Formation"),"existing carrying authority denies all")
 return "missing owned beast, allied neutral, pre-commit cover, and carrying fail closed"
end

local function cancel(kind)
 local s=start(true)
 local center,rows=pose(s,1)
 local pet=summon(s,center)
 move(rows[1],center+Vector3.new(5.5,2.15,0))
 local t=now
 activate(player,"D")
 advanceTo(t+.50)
 check(pet.PrimaryPart.Anchored,"actual compound before interruption")
 if kind=="off" then
  local stale=deck().D
  workspace:SetAttribute(FLAG,false);drainDeferred()
  old(deck())
  check(not stale.Parent and witness(s)==pet,"rollback preserves the original existing pet")
  stale.Activated:Fire()
 elseif kind=="avatar" then
  local char=Instance.new("Model")
  local root=Instance.new("Part");root.Name="HumanoidRootPart";root.CFrame=rootPart.CFrame;root.Parent=char
  local h=Instance.new("Humanoid");h.Parent=char;char.PrimaryPart=root;char.Parent=workspace
  player.Character=char
 elseif kind=="round" then
  s.rules.phase="FINISHED";s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED")
 end
 -- Put the target outside the stationary original escort range, but where a
 -- wrongly continued charge would still reach this same actual candidate.
 move(rows[1],center+Vector3.new(6.6,2.15,0))
 advanceTo(t+.91)
 check(not pet.PrimaryPart.Anchored and not mark(s,"Formation") and not mark(s,"ChargeTell") and rows[1].h.Health==96,
  ("owned work cleanup (%s) actual anchored=%s HP=%s guard=%s tell=%s"):format(kind,tostring(pet.PrimaryPart.Anchored),
   rows[1].h.Health,tostring(mark(s,"Formation")),tostring(mark(s,"ChargeTell"))))
 return "the already moving COMBO-017 cannot finish on "..kind
end
for _,kind in ipairs({"off","avatar","round"}) do
 growthCases["moon_cancel_"..kind]=function() return cancel(kind) end
end

function growthCases.moon_switch()
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"月狼を装備")
 check(player:GetAttribute(LABEL)~=nil,"moon choice")
 trigger(player,stand,"指令笛を装備")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute("EGGRUMBLE_LobbyBeastOrdersLoadoutName")~=nil,"old order deck")
 advanceTo(now+.51)
 trigger(player,stand,"月狼を装備")
 trigger(player,stand,"装備する")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute("EGGRUMBLE_LobbyBeastLoadoutName")=="雷角竜","old Thunder deck")
 advanceTo(now+.51)
 trigger(player,stand,"月狼を装備")
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_BEAST_ORDERS",false);drainDeferred()
 check(player:GetAttribute(LABEL)~=nil,"independent order flag does not clear Moon")
 advanceTo(now+.51)
 trigger(player,stand,"月狼を装備")
 check(player:GetAttribute(LABEL)==nil,"current feature can choose standard again")
 start(false)
 return "actual Moon, orders, Thunder and standard lobby selection remain distinct and reversible"
end
function growthCases.moon_physical_off()
 local s=start(false)
 check(not s.beastMoonLoadouts,"the physical parent contains neither Moon source nor mounted Tools")
 local center=pose(s,1)
 local pet=summon(s,center)
 check(witness(s)==pet and not mark(s,"Formation") and not mark(s,"ChargeTell"),"old B retains its exact real owner")
 return "the exact physical predecessor keeps the standard original real companion"
end
end
