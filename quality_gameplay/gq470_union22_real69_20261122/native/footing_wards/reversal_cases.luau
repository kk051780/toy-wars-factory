do
local FLAG="P0D_ENABLE_PRIVATE_TRAPPER_REVERSAL"
local LABEL="EGGRUMBLE_LobbyTrapperReversalLoadoutName"
local X=Vector3.new(1,0,0)
local function tools()
 local result={}
 for _,container in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(container:GetChildren()) do
   local internal=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(internal)=="string" and internal:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then result[slot]=item end
  end
 end
 return result
end
local function standard()
 local t=tools()
 check(t.A.Name=="技A・念動衝撃" and t.B.Name=="技B・重力牢獄" and t.C.Name=="技C・空間転移" and not t.D,
  "original exact TRAPPER A/B/C: "..t.A.Name.." / "..t.B.Name.." / "..t.C.Name)
end
local function place(row,origin,x,z,speed)
 local current=row.h.Parent
 local at=origin+Vector3.new(x,2*(current.PrimaryPart.Size.Y/2.5)-3,z or 0)
 current:PivotTo(CFrame.new(at))
 current:SetAttribute("EGGRUMBLE_NeutralSpeed",speed or 0)
 row.h.MaxHealth=100;row.h.Health=96
 return at
end
local function setUp(count,wear)
 local stand=scenes:FindFirstChild("ROLE_TRAPPER")
 trigger(player,stand,"職業選択")
 if wear~=false then
  check(workspace:GetAttribute(FLAG)==nil,"actual default flag with one optional loadout")
  trigger(player,stand,"刻環を装備")
  check(player:GetAttribute(LABEL)=="刻界反転・無重力冠","current owner chose specialized offer")
 end
 local s=ready("PRIVATE_TRAPPER_REVERSAL","TRAPPER")
 if wear~=false then
  local t=tools()
  check(s.trapperReversalLoadouts[player.UserId] and not s.trapperSwapHoverLoadouts[player.UserId]
   and not s.trapperGravityLoadouts[player.UserId],"freeze exactly one loadout")
  for slot,id in pairs({B="TRAPPER-040",C="TRAPPER-060",D="COMBO-012"}) do
   check(t[slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"current server Tool "..id)
  end
  check(t.A.Name=="技A・念動衝撃","legacy A retained")
 else standard() end
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local origin=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 local horde=s.world:FindFirstChild("NeutralHorde")
 local rows,chosen={},{}
 local function park(unit)
  if unit.PrimaryPart then
   unit:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   unit:PivotTo(CFrame.new(origin+Vector3.new(-55,8,27)))
  end
 end
 if count>0 then check(spawnCurrentNeutral(s),"actual swarm spawn") end
 rootPart.CFrame=CFrame.lookAt(origin,origin+X)
 secondRoot.CFrame=CFrame.new(origin+Vector3.new(-50,0,0))
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.MoveDirection=Vector3.zero
 rootPart.AssemblyLinearVelocity=Vector3.zero;rootPart.AssemblyAngularVelocity=Vector3.zero
 for _=1,58 do
  table.clear(rows)
  for _,unit in ipairs(horde:GetChildren()) do
   local h=unit:FindFirstChildOfClass("Humanoid")
   if unit.PrimaryPart and h and h.Health>0 then
    park(unit)
    if #rows<count then table.insert(rows,{model=unit,h=h});chosen[unit]=true end
   end
  end
  if #rows>=count then break end
  advanceTo(now+.21)
 end
 advanceTo(now+.4)
 check(#rows==count and s.swarm.getRoleGrowthSnapshot(player).stage==0,"actual Swarm and stage0 start")
 local deadline=now+3.8
 task.spawn(function()
  while now<deadline do
   for _,unit in ipairs(horde:GetChildren()) do
    if not chosen[unit] and unit.PrimaryPart and (unit.PrimaryPart.Position-origin).Magnitude<30 then park(unit) end
   end
   task.wait(.025)
  end
 end)
 return s,origin,rows,stand
end
local function snapshot(s) return s.swarm.getRoleGrowthSnapshot(player) end
local function tell(s) return s.world:FindFirstChild("EGGRUMBLE_TrapperReversalTell") end
local function landing(s) return s.world:FindFirstChild("EGGRUMBLE_WingLandingRing") end
local function x(row) return row.model.PrimaryPart.Position.X end
local function wall(s,at,size)
 local block=Instance.new("Part")
 block.Anchored=true;block.CanCollide=true;block.CanQuery=true
 block.CFrame=CFrame.new(at);block.Size=size;block.Parent=s.world
 return block
end

function growthCases.reversal040()
 local s,origin,rows=setUp(4)
 local moving={}
 for index,row in ipairs(rows) do moving[index]=place(row,origin,7.8+(index-1)*.12,(index-2.5)*.48,2.5).X end
 local clock=s.rules.endAt
 local growth=snapshot(s).activeSeconds
 local t=now
 activate(player,"B")
 local cue=tell(s)
 check(cue and cue.Size.Y==6 and not cue.CanTouch and not cue.CanQuery and snapshot(s).energy==55,"live stage-0 fixed tell and one E45")
 advanceTo(t+.999)
 local before={}
 for i,row in ipairs(rows) do
  before[i]=x(row);check(before[i]<moving[i]-.6,"real chase moved forward during warning")
 end
 check(tell(s)==cue and not rootPart.Anchored,"full 1s tell before reversal")
 advanceTo(t+1.205)
 local reversed=0
 for i,row in ipairs(rows) do
  if x(row)>before[i]+.12 then reversed+=1 end
  check(row.h.Health==96,"no independent neutral damage")
 end
 check(reversed==3 and not tell(s) and s.rules.endAt==clock and snapshot(s).activeSeconds==growth,
  "exactly three actual checked traces, unchanged match/growth clocks: "..tostring(reversed))
 advanceTo(t+1.81)
 for i,row in ipairs(rows) do check(x(row)<=before[i]+.12,"native AI resumes chase on lease exit") end
 return "040 one-second warning reverses only three actual neutral tracks, with unchanged HP, clocks and resumed AI"
end

function growthCases.reversal060()
 local s,origin,rows=setUp(2)
 place(rows[1],origin,5.3,0);place(rows[2],origin,6.9,1)
 local t=now
 activate(player,"C")
 check(rootPart.Anchored and snapshot(s).energy==55,"one authorized flight and E45")
 advanceTo(t+.39)
 check(rootPart.Position.Y>origin.Y+3.8 and rootPart.Position.Y<=origin.Y+4.01 and not landing(s)
  and rows[1].h.Health==96 and rows[2].h.Health==96,"S0 capped apex and no aerial hit")
 advanceTo(t+.92)
 check(not rootPart.Anchored and rootPart.Position.X>origin.X+4.5 and math.abs(rootPart.Position.Y-origin.Y)<.1
  and landing(s) and rows[1].h.Health==86 and rows[2].h.Health==96,
  "one existing HP wave after safe settled landing: "..rows[1].h.Health.." / "..rows[2].h.Health
  .." / "..(rootPart.Position.X-origin.X).." / "..(rootPart.Position.Y-origin.Y)
  .." / "..tostring(rootPart.Anchored).." / "..tostring(landing(s)))
 return "060 existing bounded flight performs one real neutral-only hit after confirmed landing"
end

function growthCases.reversal012()
 local s,origin,rows=setUp(2)
 local start=place(rows[1],origin,7.7,0,2.5)
 place(rows[2],origin,5.65,1)
 local t=now
 activate(player,"D")
 check(tell(s),"real combined warning accepted")
 local sig=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 activate(player,"D")
 check(tell(s) and snapshot(s).energy==100 and player:GetAttribute("EGGRUMBLE_SkillCastSignature")==sig,"same pending receipt neither replays nor prepays")
 advanceTo(t+.999)
 local before=x(rows[1])
 check(before<start.X-.5 and not rootPart.Anchored,"real chase before full telegraph")
 advanceTo(t+1.295)
 check(x(rows[1])>before+.25 and not rootPart.Anchored and snapshot(s).energy==100,"real reversal before flight")
 advanceTo(t+1.49)
 check(rootPart.Anchored and snapshot(s).energy>=20 and snapshot(s).energy<23,
  "real success commits one E80 including at most one natural flight sample: "
  ..tostring(rootPart.Anchored).." / "..snapshot(s).energy.." / "..(x(rows[1])-before))
 advanceTo(t+2.4)
 check(not rootPart.Anchored and math.abs(rootPart.Position.Y-origin.Y)<.12 and not landing(s)
  and rows[1].h.Health==96 and rows[2].h.Health==96,
  "combo only controls then flies, with no 060 attack")
 for _,id in ipairs({"TRAPPER-040","TRAPPER-060","COMBO-012"}) do
  check(not s.swarm.trapperReversalReady(player,player.Character,0,1,{[id]=1}),"one atomic component deadline "..id)
 end
 return "012 real CONTROL then FLIGHT then LAND commits one E80, all deadlines, and zero damaging side effect"
end

local function deny(kind)
 local s,origin,rows=setUp(1)
 local row=rows[1]
 place(row,origin,7.7,0,if kind=="static" then 0 else 2.5)
 local t=now
 activate(player,"D")
 check(tell(s),"original true warning")
 local old=tools().D
 if kind=="latewall" then
  advanceTo(t+1.001)
  local at=row.model.PrimaryPart.Position
  wall(s,at+Vector3.new(row.model.PrimaryPart.Size.X*.53+.06,1,0),Vector3.new(.18,6,4))
 elseif kind=="egg" then
  s.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=="avatar" then
  local model=Instance.new("Model")
  local fresh=Instance.new("Part");fresh.Name="HumanoidRootPart";fresh.CFrame=rootPart.CFrame;fresh.Parent=model
  local h=Instance.new("Humanoid");h.Parent=model;model.PrimaryPart=fresh;model.Parent=workspace
  player.CharacterRemoving:Fire(character);player.Character=model
 elseif kind=="off" then
  workspace:SetAttribute(FLAG,false);drainDeferred();standard()
  check(not old.Parent,"stale actual server Tool retired")
  old.Activated:Fire()
 end
 advanceTo(t+2.41)
 check(not tell(s) and not rootPart.Anchored and row.h.Health==96 and not landing(s),"failed "..kind.." does not create trajectory or damage")
 local growth=snapshot(s)
 if growth then check(growth.energy==100,"no failed E80 debit") end
 return "012 denied for "..kind.." without flight, damage, or E80"
end
for _,kind in ipairs({"static","latewall","egg","avatar","off"}) do
 growthCases["reversal_deny_"..kind]=function() return deny(kind) end
end

function growthCases.reversal_switch()
 local stand=scenes:FindFirstChild("ROLE_TRAPPER")
 trigger(player,stand,"職業選択")
 local keys={}
 for _,item in ipairs(stand:GetChildren()) do
  if item:IsA("ProximityPrompt") and item.Enabled then keys[item.ActionText]=item end
 end
 local option,swap,gravity=keys["刻環を装備"],keys["交換浮遊を装備"],keys["装備する"]
 check(option and option.KeyboardKeyCode==Enum.KeyCode.J and option.GamepadKeyCode==Enum.KeyCode.ButtonB
  and swap.KeyboardKeyCode==Enum.KeyCode.G and swap.GamepadKeyCode==Enum.KeyCode.ButtonX
  and gravity.KeyboardKeyCode==Enum.KeyCode.F and gravity.GamepadKeyCode==Enum.KeyCode.ButtonY,"three disjoint actual stand inputs")
 trigger(player,stand,"刻環を装備")
 check(player:GetAttribute(LABEL),"real J")
 trigger(player,stand,"交換浮遊を装備")
 check(not player:GetAttribute(LABEL) and player:GetAttribute("EGGRUMBLE_LobbyTrapperSwapLoadoutName"),"real G cleans J")
 trigger(player,stand,"装備する")
 check(not player:GetAttribute("EGGRUMBLE_LobbyTrapperSwapLoadoutName") and player:GetAttribute("EGGRUMBLE_LobbyTrapperLoadoutName"),
  "real F cleans G")
 advanceTo(now+.52)
 trigger(player,stand,"刻環を装備")
 check(not player:GetAttribute("EGGRUMBLE_LobbyTrapperLoadoutName") and player:GetAttribute(LABEL),"real J cleans F")
 return "physical Trapper stand keeps F/Y gravity, G/X swap, J/B reversal and exclusive selection"
end
function growthCases.reversal_physical_off()
 local s,_,_,stand=setUp(0,false)
 check(not s.trapperReversalLoadouts and not s.swarm.reverseTrapperNeutrals,"physical parent lacks new Trapper path")
 for _,child in ipairs(stand:GetChildren()) do
  check(not child:IsA("ProximityPrompt") or child.ActionText~="刻環を装備","physical parent has no new selection")
 end
 return "physical parent retains standard A/B/C and no new Trapper authority"
end
end
