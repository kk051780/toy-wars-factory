do
local FLAG="P0D_ENABLE_PRIVATE_WARRIOR_FIELD_TECH"
local EAST=Vector3.new(1,0,0)
local labels={"剣の三技","間合い三技","守りの三技","野戦の三技","地形の三技"}
local items={
 hilt={id="WARRIOR-004",kit=4,slot="A",energy=30,tell=.24},
 flight={id="WARRIOR-006",kit=4,slot="B",energy=35,tell=.30},
 cross={id="WARRIOR-009",kit=4,slot="C",energy=45,tell=.38},
 push={id="WARRIOR-013",kit=5,slot="A",energy=30,tell=.25},
 mark={id="WARRIOR-014",kit=5,slot="B",energy=30,tell=.26},
 drop={id="WARRIOR-017",kit=5,slot="C",energy=45,tell=.80},
}

local function tool(slot)
 for _,holder in ipairs({player:FindFirstChildOfClass("Backpack"),character}) do
  for _,item in ipairs(holder:GetChildren()) do
   local name=item:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(name)=="string" and name:match("^EGGRUMBLE_SKILL_"..slot.."_") then return item end
  end
 end
end

local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function power() return dependencies.EGGRUMBLE_CombatBalance.skill("WARRIOR","A").damage end
local function near(actual,expected) return math.abs(actual-expected)<.03 end
local function tell(live,row) return live.world:FindFirstChild("EGGRUMBLE_WarriorTech_"..row.id.."_Tell") end

local function start(kit)
 local stand=scenes:FindFirstChild("ROLE_WARRIOR")
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 for i=1,(kit or 0) do
  trigger(player,stand,"剣技を装備")
  check(player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName")==labels[i],"real selected kit")
  advanceTo(now+.51)
 end
 local live=ready("WARRIOR_FIELD_TECH_ACTUAL_TOOLS","WARRIOR")
 local ground=live.world:FindFirstChild("TacticalBattlefield")
 local floor=ground.Position+Vector3.new(170,ground.Size.Y*.5,-115)
 local at=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.MoveDirection=Vector3.zero;rootPart.AssemblyLinearVelocity=Vector3.zero
 advanceTo(now+.39)
 return live,floor
end

local function setAt(model,floor,x,z,kind)
 local at=floor+Vector3.new(x,2*(model.PrimaryPart.Size.Y/2.5),z)
 model:PivotTo(CFrame.new(at))
 model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
 model:SetAttribute("EGGRUMBLE_NeutralSpecies",kind or "BANNER_KNIGHT")
 local hp=model:FindFirstChildOfClass("Humanoid")
 hp.Health=150
 return {model=model,hp=hp,at=at}
end

local function gather(live,floor,n)
 local roster={}
 for _=1,48 do
  table.clear(roster)
  for _,m in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if m.PrimaryPart and m:FindFirstChildOfClass("Humanoid") and m:FindFirstChildOfClass("Humanoid").Health>0 then
    setAt(m,floor,-40,34)
    table.insert(roster,m)
   end
  end
  if #roster>=n then return roster end
  advanceTo(now+.35)
 end
 error("original Swarm did not spawn enough current neutral units")
end

local function invoke(live,row)
 check(tool(row.slot) and tool(row.slot):GetAttribute("EGGRUMBLE_FixedAbilityId")==row.id,
  "actual fixed skill in the authorized selected kit")
 local t=now
 activate(player,row.slot)
 local warning=tell(live,row)
 check(warning and #warning:GetChildren()>0 and energy(live)==100-row.energy,"one energy debit and genuine warning")
 activate(player,row.slot)
 check(tell(live,row)==warning and energy(live)==100-row.energy,"duplicate cast did not replace pending work")
 return t,warning
end

local function wall(live,position,size)
 local part=Instance.new("Part")
 part.Size=size;part.CFrame=CFrame.new(position)
 part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=live.world
 return part
end

function growthCases.warrior_field_hilt()
 local row=items.hilt
 local live,floor=start(row.kit)
 local roster=gather(live,floor,2)
 local target=setAt(roster[1],floor,2.45,0)
 local second=setAt(roster[2],floor,3.25,.45)
 local t=invoke(live,row)
 advanceTo(t+row.tell-.001)
 check(target.hp.Health==150 and target.model.PrimaryPart.Position==target.at,"windup does not attack")
 advanceTo(t+row.tell+.003)
 check(near(target.hp.Health,150-power()) and target.model.PrimaryPart.Position.X>target.at.X+.88
  and second.hp.Health==150,"S0 hilt applies one genuine hit and one swept one-stud displacement")
 return "one short hilt strike and one actual neutral displacement"
end

function growthCases.warrior_field_push()
 local row=items.push
 local live,floor=start(row.kit)
 local roster=gather(live,floor,2)
 local target=setAt(roster[1],floor,2.3,.2)
 local other=setAt(roster[2],floor,4.0,-.4)
 local t=invoke(live,row)
 advanceTo(t+row.tell+.003)
 check(target.hp.Health==150 and other.hp.Health==150 and target.model.PrimaryPart.Position.X>target.at.X+.88
  and other.model.PrimaryPart.Position==other.at and live.swarm.getTotal()==0,
  "the nearest neutral moves once, remaining roster and HP stay as before")
 return "one swept shove with no damage, KO or score side effect"
end

function growthCases.warrior_field_push_weight()
 local row=items.push
 local live,floor=start(row.kit)
 local target=setAt(gather(live,floor,1)[1],floor,2.8,0,"BABY_GOLEM")
 local t=invoke(live,row)
 advanceTo(t+row.tell+.003)
 check(target.hp.Health==150 and target.model.PrimaryPart.Position==target.at,"existing heavy exception remains")
 return "the checked movement owner rejects a heavy neutral before applying the shove"
end

local function flight(blocked)
 local row=items.flight
 local live,floor=start(row.kit)
 local roster=gather(live,floor,2)
 local target=setAt(roster[1],floor,6.45,0)
 local other=setAt(roster[2],floor,5.4,2.9)
 local t=invoke(live,row)
 advanceTo(t+.38)
 local blade=live.world:FindFirstChild("EGGRUMBLE_WarriorGroundBlade")
 check(blade and blade.Position.Y<target.at.Y and target.hp.Health==150,"the blade travels low before contact")
 if blocked then wall(live,floor+Vector3.new(3.75,3,0),Vector3.new(.3,8,6)) end
 advanceTo(t+.86)
 check(near(target.hp.Health,150-(if blocked then 0 else power())) and other.hp.Health==150
  and not blade.Parent,"ground sweep obeys the actual wall and narrow lane")
 return if blocked then "the late solid wall intercepts the actual advancing blade"
  else "a blade follows valid floor and touches just the admitted lane once"
end

function growthCases.warrior_field_blade() return flight(false) end
function growthCases.warrior_field_blade_wall() return flight(true) end

function growthCases.warrior_field_cross()
 local row=items.cross
 local live,floor=start(row.kit)
 local roster=gather(live,floor,3)
 local center=setAt(roster[1],floor,2.5,0)
 local arm=setAt(roster[2],floor,4,1.04)
 local outside=setAt(roster[3],floor,2.5,2.55)
 local t,warning=invoke(live,row)
 check(#warning:GetChildren()==2,"two real strokes meet at a shared center")
 advanceTo(t+row.tell+.004)
 check(near(center.hp.Health,150-power()) and near(arm.hp.Health,150-power()) and outside.hp.Health==150,
  "the overlap target receives one hit and the second arm consumes the other slot")
 return "actual crossing lines share the target cap and never double hit at the center"
end

function growthCases.warrior_field_mark()
 local row=items.mark
 local live,floor=start(row.kit)
 local target=setAt(gather(live,floor,1)[1],floor,3.65,0)
 local t=invoke(live,row)
 check(not live.world:FindFirstChild("EGGRUMBLE_WarriorHitMark"),"no marker for a pending attack")
 advanceTo(t+row.tell+.002)
 local pin=live.world:FindFirstChild("EGGRUMBLE_WarriorHitMark")
 check(pin and near(target.hp.Health,150-power()) and near(pin.Position.X,target.at.X) and near(pin.Position.Z,target.at.Z),
  "marker only after actual HP contact at the confirmed point")
 advanceTo(t+row.tell+1.97)
 check(pin.Parent==live.world,"bounded S0 two-second point")
 advanceTo(t+row.tell+2.02)
 check(not pin.Parent,"the mark expires")
 return "real impact marker is local, noninteractive and lasts its fixed stage window"
end

local function drop(blocked)
 local row=items.drop
 local live,floor=start(row.kit)
 local roster=gather(live,floor,3)
 local one=setAt(roster[1],floor,4.55,-.4)
 local two=setAt(roster[2],floor,5.2,.4)
 local out=setAt(roster[3],floor,4.65,3.5)
 local t,warning=invoke(live,row)
 local circle=warning:FindFirstChild("LandingCircle")
 check(circle and near(circle.Size.Y,6) and near(circle.Position.X,floor.X+4.5),"ground radius warning matches actual target point")
 advanceTo(t+row.tell-.12)
 check(one.hp.Health==150 and two.hp.Health==150,"warning allows response")
 if blocked then wall(live,floor+Vector3.new(2.2,3,0),Vector3.new(.4,9,8)) end
 advanceTo(t+row.tell+.003)
 local expected=150-(if blocked then 0 else power())
 check(near(one.hp.Health,expected) and near(two.hp.Health,expected) and out.hp.Health==150 and not warning.Parent,
  "true ground attack honors the latest LOS and two-target stage budget")
 return if blocked then "late wall revokes the authored ground attack" else "two legitimate targets inside the warned circle"
end

function growthCases.warrior_field_drop() return drop(false) end
function growthCases.warrior_field_drop_wall() return drop(true) end

function growthCases.warrior_field_live_off()
 local row=items.drop
 local live,floor=start(row.kit)
 local target=setAt(gather(live,floor,1)[1],floor,4.55,0)
 local t=invoke(live,row)
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 advanceTo(t+row.tell+.2)
 check(target.hp.Health==150 and not tell(live,row) and tool("A").Name=="技A・飛翔斬撃",
  "independent OFF clears advanced kit and jobs while old kit stays available")
 return "changing newer field weapons OFF cancels pending hits and restores the original deck"
end

function growthCases.warrior_field_physical_off()
 local stand=scenes:FindFirstChild("ROLE_WARRIOR")
 trigger(player,stand,"職業選択")
 for i=1,4 do
  advanceTo(now+.51)
  trigger(player,stand,"剣技を装備")
 end
 check(not player:GetAttribute("EGGRUMBLE_LobbyWarriorTechLoadoutName"),"fourth original rotation restores default")
 local live=ready("WARRIOR_FIELD_TECH_PHYSICAL_OFF","WARRIOR")
 check(not live.warriorTechLoadouts[player.UserId] and tool("A").Name=="技A・飛翔斬撃",
  "physical prior role deck still cycles and equips normally")
 return "the exact prior build retains the original three optional kits and standard gear"
end
end
