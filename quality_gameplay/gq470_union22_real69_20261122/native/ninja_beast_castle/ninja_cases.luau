do
local FLAG="P0D_ENABLE_PRIVATE_NINJA_CUTS"
local EAST=Vector3.new(1,0,0)
local labels={"影刃・背切・逆手","残影刃・二重切・暗月"}

local function skill(slot)
 for _,pack in ipairs({player:FindFirstChildOfClass("Backpack"),character}) do
  for _,entry in ipairs(pack:GetChildren()) do
   local id=entry:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(id)=="string" and id:match("^EGGRUMBLE_SKILL_"..slot.."_") then return entry end
  end
 end
end

local function near(a,b) return math.abs(a-b)<.03 end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function tell(live,id) return live.world:FindFirstChild("EGGRUMBLE_NinjaCut_"..id) end
local function power() return dependencies.EGGRUMBLE_CombatBalance.skill("NINJA","A").damage end

local function start(kit)
 local stand=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 if kit then
  for i=1,kit do
   trigger(player,scenes:FindFirstChild("ROLE_NINJA_CUTS"),"斬技を装備")
   check(player:GetAttribute("EGGRUMBLE_LobbyNinjaLoadoutName")==labels[i],"actual narrow lobby selection")
   advanceTo(now+.51)
  end
 end
 local live=ready("PRIVATE_NINJA_CUTS_ACTUAL_TOOLS","NINJA")
 if kit then check(live.ninjaCutLoadouts[player.UserId]==kit and not skill("D"),"one legal current optional kit") end
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local ground=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 rootPart.CFrame=CFrame.lookAt(ground+Vector3.new(0,2.6,0),ground+Vector3.new(1,2.6,0))
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.MoveDirection=Vector3.zero;rootPart.AssemblyLinearVelocity=Vector3.zero
 advanceTo(now+.39)
 return live,ground
end

local function mark(model,ground,x,z,facing)
 model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
 model:SetAttribute("EGGRUMBLE_NeutralSpecies","BANNER_KNIGHT")
 local where=ground+Vector3.new(x,2*(model.PrimaryPart.Size.Y/2.5),z)
 model:PivotTo(CFrame.lookAt(where,where+(facing or EAST)))
 local hp=model:FindFirstChildOfClass("Humanoid")
 hp.Health=150
 return {model=model,hp=hp,where=where}
end

local function warm(live,ground,amount)
 local models={}
 for _=1,56 do
  table.clear(models)
  for _,m in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if m.PrimaryPart and m:FindFirstChildOfClass("Humanoid") and m:FindFirstChildOfClass("Humanoid").Health>0 then
    mark(m,ground,-35,30)
    table.insert(models,m)
   end
  end
  if #models>=amount then return models end
  advanceTo(now+.35)
 end
 error("real neutral spawning could not supply the requested current roster")
end

local function apply(live,slot,id,price)
 local specific=skill(slot)
 check(specific and specific:GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"fixed ID for actual equipped Tool")
 local t=now
 activate(player,slot)
 local visible=tell(live,id)
 check(visible and #visible:GetChildren()>0 and energy(live)==100-price,"one energy debit and visible warning")
 activate(player,slot)
 check(energy(live)==100-price and tell(live,id)==visible,"repeated activation cannot replace the active cast")
 return t,visible
end

function growthCases.ninja_cut_front()
 local live,floor=start(1)
 local models=warm(live,floor,3)
 local front=mark(models[1],floor,2.6,0)
 local next=mark(models[2],floor,3.4,.45)
 local rear=mark(models[3],floor,-2.4,0)
 local t,warning=apply(live,"A","NINJA-001",30)
 advanceTo(t+.239)
 check(front.hp.Health==150 and next.hp.Health==150 and rear.hp.Health==150,"actual windup protects every target")
 advanceTo(t+.244)
 check(near(front.hp.Health,150-power()) and next.hp.Health==150 and rear.hp.Health==150 and not warning.Parent,
  "S0 front fan admits precisely one nearest neutral")
 return "a real front warning then one short legal strike"
end

function growthCases.ninja_cut_backstab()
 local live,floor=start(1)
 local models=warm(live,floor,2)
 local front=mark(models[1],floor,2.15,-.3,-EAST)
 local rear=mark(models[2],floor,3.05,.2,EAST)
 local t=apply(live,"B","NINJA-002",30)
 advanceTo(t+.244)
 check(front.hp.Health==150 and near(rear.hp.Health,150-power()*1.05),
  "closer facing neutral stays untouched; actual rear contact receives 5 percent")
 return "rear orientation and its stage-zero bonus use one real hit"
end

function growthCases.ninja_cut_rear()
 local live,floor=start(1)
 local models=warm(live,floor,2)
 local front=mark(models[1],floor,2.3,0)
 local rear=mark(models[2],floor,-2.4,0)
 local t=apply(live,"C","NINJA-004",30)
 advanceTo(t+.244)
 check(front.hp.Health==150 and near(rear.hp.Health,150-power()),"actual rear fan and normal damage only")
 return "the held backward grip attacks behind the current avatar"
end

function growthCases.ninja_cut_echo()
 local live,floor=start(2)
 local models=warm(live,floor,2)
 local target=mark(models[1],floor,2.55,0)
 local other=mark(models[2],floor,3.45,.4)
 local t=apply(live,"A","NINJA-005",40)
 advanceTo(t+.27)
 check(near(target.hp.Health,150-power()/2) and other.hp.Health==150,"first half is real")
 advanceTo(t+.739)
 check(near(target.hp.Health,150-power()/2),"fixed half-second delay after first contact")
 advanceTo(t+.744)
 check(near(target.hp.Health,150-power()) and other.hp.Health==150 and not tell(live,"NINJA-005"),
  "one delayed half against the same admitted token, no extra damage budget")
 return "initial and echo strikes share one budget and one actual target"
end

function growthCases.ninja_cut_echo_dodge()
 local live,floor=start(2)
 local models=warm(live,floor,2)
 local target=mark(models[1],floor,2.55,0)
 local other=mark(models[2],floor,3.45,.4)
 local t=apply(live,"A","NINJA-005",40)
 advanceTo(t+.27)
 check(near(target.hp.Health,150-power()/2),"first half was served")
 target.model:PivotTo(CFrame.new(target.where+Vector3.new(10,0,0)))
 advanceTo(t+.75)
 check(near(target.hp.Health,150-power()/2) and other.hp.Health==150,
  "leaving geometry evades the echo and cannot redirect it to another opponent")
 return "delayed shadow hit is independently avoidable"
end

function growthCases.ninja_cut_pair()
 local live,floor=start(2)
 local models=warm(live,floor,3)
 local left=mark(models[1],floor,2.2,-1.65)
 local right=mark(models[2],floor,2.1,1.65)
 local outside=mark(models[3],floor,-2.5,0)
 local t,warning=apply(live,"B","NINJA-006",35)
 check(#warning:GetChildren()==2,"two physically distinct warning strokes")
 advanceTo(t+.244)
 check(near(left.hp.Health,150-power()/2) and right.hp.Health==150,"first left beat only")
 advanceTo(t+.534)
 check(near(left.hp.Health,150-power()/2) and near(right.hp.Health,150-power()/2) and outside.hp.Health==150,
  "second right beat shares one budget and one unique set")
 return "two indicated angles with separate hit times and one total damage budget"
end

local function flight(blocked)
 local live,floor=start(2)
 local models=warm(live,floor,2)
 local target=mark(models[1],floor,6.35,0)
 local outside=mark(models[2],floor,5.4,2.85)
 local t=apply(live,"C","NINJA-008",35)
 advanceTo(t+.311)
 check(target.hp.Health==150,"the actual stroke takes time to travel")
 if blocked then
  local part=Instance.new("Part")
  part.Size=Vector3.new(.35,9,6);part.CFrame=CFrame.new(floor+Vector3.new(3.35,3,0))
  part.CanCollide=true;part.CanQuery=true;part.Anchored=true;part.Parent=live.world
 end
 advanceTo(t+.76)
 check(near(target.hp.Health,150-(if blocked then 0 else power())) and outside.hp.Health==150
  and not tell(live,"NINJA-008"),"swept thin trajectory: near HP="..target.hp.Health
   ..", outside HP="..outside.hp.Health..", pending="..tostring(tell(live,"NINJA-008")~=nil))
 return if blocked then "late wall stops the flying cut" else "flight has one confirmed thin-lane contact"
end

function growthCases.ninja_cut_flight() return flight(false) end
function growthCases.ninja_cut_flight_wall() return flight(true) end

function growthCases.ninja_cut_hidden_egg()
 local live=start(1)
 player:SetAttribute("EGGRUMBLE_StealthUntil",now+2)
 activate(player,"A")
 check(energy(live)==100 and not tell(live,"NINJA-001"),"hidden casting is denied before energy")
 player:SetAttribute("EGGRUMBLE_StealthUntil",nil)
 local castle=live.rules.castles[tostring(player.UserId)]
 castle.heldEggs=1
 activate(player,"A")
 check(not tell(live,"NINJA-001"),"egg carrier cast is denied")
 castle.heldEggs=0
 check(energy(live)==100,"both rejected casts preserve energy")
 return "old stealth and actual egg custody cannot start the optional damage path"
end

function growthCases.ninja_cut_off()
 local live,floor=start(1)
 local target=mark(warm(live,floor,1)[1],floor,2.45,0)
 local t=apply(live,"A","NINJA-001",30)
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 advanceTo(t+.7)
 check(target.hp.Health==150 and not tell(live,"NINJA-001") and skill("A").Name=="技A・瞬影斬",
  "independent live OFF clears pending release and restores the original Tool")
 return "live OFF keeps HP unchanged and restores the base role"
end

function growthCases.ninja_cut_physical_off()
 start(nil)
 check(not scenes:FindFirstChild("ROLE_NINJA_CUTS") and skill("A").Name=="技A・瞬影斬",
  "actual predecessor's plain role tool and lobby remained")
 return "immediate exact parent has the original Ninja tool and no new plaque"
end
end
