do
local FLAG="P0D_ENABLE_PRIVATE_NINJA_DIRECTION_STEPS"
local EAST=Vector3.new(1,0,0)
local rows={
 back={slot="A",id="NINJA-032",tell=.18,price=30},
 side={slot="B",id="NINJA-033",tell=.18,price=30},
 land={slot="C",id="NINJA-034",tell=.45,price=35},
 diagonal={slot="D",id="NINJA-036",tell=.18,price=35},
}

local function equipped(slot)
 for _,holder in ipairs({player:FindFirstChildOfClass("Backpack"),character}) do
  for _,entry in ipairs(holder:GetChildren()) do
   local tag=entry:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(tag)=="string" and tag:match("^EGGRUMBLE_SKILL_"..slot.."_") then return entry end
  end
 end
end

local function start(opt)
 trigger(player,scenes:FindFirstChild("ROLE_NINJA"),"職業選択")
 advanceTo(now+.51)
 if opt then trigger(player,scenes:FindFirstChild("ROLE_NINJA_CUTS"),"方向技を装備") end
 local live=ready("NINJA_DIRECTION_STEP_ACTUAL_TOOL","NINJA")
 local floor=live.world:FindFirstChild("TacticalBattlefield")
 local at=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 rootPart.AssemblyLinearVelocity=Vector3.zero;rootPart.AssemblyAngularVelocity=Vector3.zero
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.MoveDirection=Vector3.zero
 advanceTo(now+.39)
 return live,at
end

local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function fx(live,row) return live.world:FindFirstChild("EGGRUMBLE_DirectionStep_"..row.id) end
local function near(a,b) return (a-b).Magnitude<.04 end

local function release(live,row,at,to)
 check(equipped(row.slot):GetAttribute("EGGRUMBLE_FixedAbilityId")==row.id,"existing server issued registered Tool")
 local t=now
 local hp=humanoid.Health
 activate(player,row.slot)
 local cue=fx(live,row)
 check(cue and not cue.CanCollide and energy(live)==100-row.price,"one real appearing direction or arrival cue and exact E")
 activate(player,row.slot)
 check(fx(live,row)==cue and energy(live)==100-row.price,"no duplicate active direction event")
 advanceTo(t+row.tell-.001)
 check(near(rootPart.Position,at) and humanoid.Health==hp,"existing physical avatar held for the full preview")
 if row.slot=="C" then check(near(cue.Position,to-Vector3.new(0,2.91,0)),"the visible mark is the exact legal arrival surface") end
 advanceTo(t+row.tell+.005)
 check(near(rootPart.Position,to) and not cue.Parent and humanoid.Health==hp
  and rootPart.CFrame.LookVector:Dot(EAST)>.995 and live.swarm.getTotal()==0,
  "actual current avatar moved along its promised route, retains facing, HP and no attack credit: "
  ..tostring(rootPart.Position.X-at.X)..","..tostring(rootPart.Position.Z-at.Z))
 return t
end

function growthCases.ninja_step_back()
 local live,at=start(true)
 release(live,rows.back,at,at-EAST*3)
 return "actual three-stud backward step without turning or immunity"
end

function growthCases.ninja_step_side()
 local live,at=start(true)
 humanoid.MoveDirection=Vector3.new(0,0,-1)
 release(live,rows.side,at,at+Vector3.new(0,0,-3))
 return "captured lateral movement selects the indicated side"
end

function growthCases.ninja_step_land()
 local live,at=start(true)
 release(live,rows.land,at,at+EAST*3)
 return "visible destination remains the same safe ground for 0.45 seconds before arrival"
end

function growthCases.ninja_step_diagonal()
 local live,at=start(true)
 humanoid.MoveDirection=Vector3.new(0,0,-1)
 release(live,rows.diagonal,at,at+Vector3.new(1,0,-1).Unit*4)
 return "four-stud selected diagonal uses the same checked pivot and no damage"
end

local function wall(parent,at)
 local part=Instance.new("Part")
 part.CanCollide=true;part.CanQuery=true;part.Anchored=true
 part.Size=Vector3.new(.34,8,5);part.CFrame=CFrame.new(at);part.Parent=parent
 return part
end

function growthCases.ninja_step_late_wall()
 local live,at=start(true)
 local t=now
 activate(player,"C")
 check(energy(live)==65 and fx(live,rows.land),"valid initial ground and complete one activation")
 wall(live.world,at+EAST*1.45)
 advanceTo(t+.48)
 check(near(rootPart.Position,at) and not fx(live,rows.land),"late solid wall cannot redirect or move the avatar")
 return "the newly blocked arrival is rechecked before any movement"
end

function growthCases.ninja_step_castle_floor()
 local live,at=start(true)
 local realCastle=live.castleModels[tostring(second.UserId)].model
 local floor=Instance.new("Part")
 floor.CanCollide=true;floor.CanQuery=true;floor.Anchored=true;floor.Size=Vector3.new(2,.34,2)
 floor.CFrame=CFrame.new(at+Vector3.new(3,-2.72,0));floor.Parent=realCastle
 activate(player,"C")
 check(energy(live)==100 and not fx(live,rows.land) and near(rootPart.Position,at),
  "own existing castle-model provenance is rejected before debit for the selected arrival")
 return "an actual other castle's floor may not become this ability's destination"
end

function growthCases.ninja_step_egg_and_speed()
 local live,at=start(true)
 local actor=live.rules.castles[tostring(player.UserId)]
 actor.heldEggs=1
 activate(player,"A")
 check(not fx(live,rows.back) and near(rootPart.Position,at),"current egg carrier cannot start movement")
 actor.heldEggs=0
 rootPart.AssemblyLinearVelocity=Vector3.new(100,0,0)
 activate(player,"B")
 check(energy(live)==100 and not fx(live,rows.side),"invalid existing movement velocity cannot consume energy or widen path")
 return "egg custody and actor speed are checked before any preview"
end

function growthCases.ninja_step_live_off()
 local live,at=start(true)
 activate(player,"B")
 check(fx(live,rows.side),"the current cast is pending before flag change")
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 advanceTo(now+.3)
 check(near(rootPart.Position,at) and not fx(live,rows.side) and not equipped("D") and equipped("A").Name=="技A・瞬影斬",
  "independent live OFF retires current cast and retains the original role")
 return "live flag rollback keeps current position and restores old gear"
end

function growthCases.ninja_step_old_kit()
 local stand=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 trigger(player,scenes:FindFirstChild("ROLE_NINJA_CUTS"),"方向技を装備")
 advanceTo(now+.51)
 trigger(player,stand,"装備する")
 advanceTo(now+.51)
 local live=ready("NINJA_DIRECTION_STEP_LEGACY_KIT","NINJA")
 check(not live.ninjaStepsLoadouts[player.UserId] and equipped("B"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="NINJA-031"
  and equipped("D"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-008",
  "existing F kit selection still owns the actual old Blink and combo")
 return "old movement kit remains individually available after using the new option"
end

function growthCases.ninja_step_physical_off()
 start(false)
 local station=scenes:FindFirstChild("ROLE_NINJA_CUTS")
 for _,object in ipairs(station:GetChildren()) do
  check(not object:IsA("ProximityPrompt") or object.ActionText~="方向技を装備","physical parent no optional step action")
 end
 check(not equipped("D") and equipped("A").Name=="技A・瞬影斬","previous ordinary kit begins unchanged")
 return "actual complete older profile still owns prior cut and default kits without directional skill"
end
end
