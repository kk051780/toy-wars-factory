do
local FLAG="P0D_ENABLE_PRIVATE_BUILDER_GUARD_PLATFORM"
local GUARD="EGGRUMBLE_BuilderEscortDevice"
local PAD="EGGRUMBLE_BuilderSpringPad"
local EAST=Vector3.new(1,0,0)

local function tool(slot)
 for _,holder in ipairs({player:FindFirstChildOfClass("Backpack"),character}) do
  for _,entry in ipairs(holder:GetChildren()) do
   local tag=entry:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(tag)=="string" and tag:match("^EGGRUMBLE_SKILL_"..slot.."_") then return entry end
  end
 end
end

local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function near(actual,expected) return math.abs(actual-expected)<.018 end

local function start(selectWorks)
 local stand=scenes:FindFirstChild("ROLE_BUILDER")
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 if selectWorks then
  trigger(player,scenes:FindFirstChild("ROLE_BUILDER_WORKS"),"護衛器を装備")
  check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="護衛機・跳躍台・護衛跳台","current choice stays visible")
 end
 local live=ready("PRIVATE_BUILDER_WORKS_ACTUAL_TOOL","BUILDER")
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local at=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 rootPart.AssemblyLinearVelocity=Vector3.zero
 humanoid.HipHeight=2;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.FloorMaterial=Enum.Material.Grass
 workspace.Gravity=196.2
 advanceTo(now+.39)
 if selectWorks then
  for slot,id in pairs({B="BUILDER-025",C="BUILDER-075",D="COMBO-015"}) do
   check(tool(slot) and tool(slot):GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"existing equipped Tool "..id)
  end
 end
 return live,floor,at
end

local function moveOnPad(pad)
 local at=pad.Position+Vector3.new(0,2.55,0)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 rootPart.AssemblyLinearVelocity=Vector3.new(.28,0,-.32)
 humanoid.FloorMaterial=Enum.Material.WoodPlanks
end

local function contact()
 advanceTo(now+.103)
end

local function obstacle(live,at,size)
 local part=Instance.new("Part")
 part.CanCollide=true;part.CanQuery=true;part.Anchored=true;part.Size=size;part.CFrame=CFrame.new(at)
 part.Parent=live.world
 return part
end

local function protection(kind,id)
 return dependencies.EGGRUMBLE_InvulRuntime.filterDamage(humanoid,100,kind,id,rootPart.Position+EAST*3)
end

function growthCases.builder_works_guard()
 local live,floor,at=start(true)
 local mob=spawnCurrentNeutral(live)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 for _,m in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  if m.PrimaryPart then
   m:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   m:PivotTo(CFrame.new(floor+Vector3.new(-39,2,31)))
  end
 end
 advanceTo(now+.39)
 local t=now
 activate(player,"B")
 local guard=live.world:FindFirstChild(GUARD)
 check(guard and guard.PrimaryPart and not guard:FindFirstChildOfClass("Humanoid")
  and energy(live)==60 and not live.world:FindFirstChild(PAD),"one real owned device occupies original build capacity, no second AI")
 check(near(protection("NEUTRAL","SWARM_MELEE"),95) and protection("PLAYER",second.UserId)==100
  and protection("NEUTRAL","OTHER")==100 and protection("BOSS","SWARM_MELEE")==100,
  "only existing verified contact path receives five percent")
 local spawn=floor+Vector3.new(2.75,2*(mob.PrimaryPart.Size.Y/2.5),.1)
 mob:PivotTo(CFrame.new(spawn))
 mob:SetAttribute("EGGRUMBLE_NeutralSpecies","BANNER_KNIGHT")
 local hp=humanoid.Health
 for _=1,10 do
  if humanoid.Health<hp then break end
  advanceTo(now+.10)
 end
 check(near(hp-humanoid.Health,3.8),"actual Swarm contact reduces 4 HP to 3.8, observed "..(hp-humanoid.Health))
 mob:PivotTo(CFrame.new(floor+Vector3.new(-38,2,32)))
 advanceTo(t+3.015)
 check(not guard.Parent and protection("NEUTRAL","SWARM_MELEE")==100,"three-second expiry restores exact old prehit")
 return "one guard consumes E40, follows its owner and mitigates the actual neutral contact for three seconds"
end

function growthCases.builder_works_pad()
 local live=start(true)
 activate(player,"C")
 local pad=live.world:FindFirstChild(PAD)
 check(pad and pad.CanCollide and not pad.CanTouch and pad.CanQuery and energy(live)==60
  and not live.world:FindFirstChild(GUARD),"one usable actual legal platform after E40")
 secondRoot.AssemblyLinearVelocity=Vector3.zero
 secondRoot.CFrame=CFrame.new(pad.Position+Vector3.new(0,2.55,0))
 contact()
 check(pad.Parent and rootPart.AssemblyLinearVelocity.Y==0 and secondRoot.AssemblyLinearVelocity.Y==0,
  "touch by a different hero cannot launch either avatar")
 secondRoot.CFrame=CFrame.new(rootPart.Position+Vector3.new(16,2,0))
 moveOnPad(pad)
 contact()
 local v=rootPart.AssemblyLinearVelocity
 check(not pad.Parent and near(v.Y,math.sqrt(workspace.Gravity*4)) and near(v.X,.28) and near(v.Z,-.32),
  "actual same-owner support contact launches one exact +2stud arc keeping horizontal velocity")
 contact()
 check(rootPart.AssemblyLinearVelocity==v,"consumed platform cannot trigger a second time")
 return "one owner-authoritative physical launch, with no remote or stored reward"
end

function growthCases.builder_works_blocked()
 local live,floor=start(true)
 local wall=obstacle(live,floor+Vector3.new(3.55,.45,0),Vector3.new(1.2,1,2.2))
 activate(player,"D")
 check(energy(live)==100 and not live.world:FindFirstChild(GUARD) and not live.world:FindFirstChild(PAD),
  "blocked legal construction denies the whole pair before energy")
 wall:Destroy()
 activate(player,"D")
 check(energy(live)==20 and live.world:FindFirstChild(GUARD) and live.world:FindFirstChild(PAD),"same account can cast once after a clean retry")
 return "blocked geometry never produces half of a pair or charges energy"
end

function growthCases.builder_works_ceiling()
 local live=start(true)
 activate(player,"C")
 local pad=live.world:FindFirstChild(PAD)
 check(pad and energy(live)==60,"legal initial platform")
 moveOnPad(pad)
 local ceiling=obstacle(live,rootPart.Position+Vector3.new(0,2.3,0),Vector3.new(3,.3,3))
 contact()
 check(pad.Parent and rootPart.AssemblyLinearVelocity.Y==0,"late solid ceiling prevents launch without consuming pad")
 ceiling:Destroy()
 contact()
 check(not pad.Parent and rootPart.AssemblyLinearVelocity.Y>0,"same physical pad works after removal of the obstruction")
 return "vertical sweep prevents clipping a late overhead obstacle"
end

function growthCases.builder_works_combo()
 local live=start(true)
 local t=now
 activate(player,"D")
 local guard,pad=live.world:FindFirstChild(GUARD),live.world:FindFirstChild(PAD)
 check(guard and pad and energy(live)==20 and near(protection("NEUTRAL","SWARM_MELEE"),95),
  "one E80 for two valid old-capacity slots")
 activate(player,"D")
 check(live.world:FindFirstChild(GUARD)==guard and live.world:FindFirstChild(PAD)==pad and energy(live)==20,
  "no duplicate device or platform")
 moveOnPad(pad)
 contact()
 check(not pad.Parent and guard.Parent==live.world and near(rootPart.AssemblyLinearVelocity.Y,math.sqrt(workspace.Gravity*4)),
  "guard and one legitimate jump execute in the same fixed combo")
 advanceTo(t+3.01)
 check(not guard.Parent,"normal expiry after a successful jump")
 return "exact guard, placement and verified jump receipts use one E80 and no extra life"
end

function growthCases.builder_works_egg_and_air()
 local live=start(true)
 local owner=live.rules.castles[tostring(player.UserId)]
 owner.heldEggs=1
 activate(player,"D")
 check(not live.world:FindFirstChild(PAD) and not live.world:FindFirstChild(GUARD),"real egg carrier cannot begin construction")
 owner.heldEggs=0
 humanoid.FloorMaterial=Enum.Material.Air
 activate(player,"D")
 check(energy(live)==100 and not live.world:FindFirstChild(PAD),"air misuse costs no energy")
 humanoid.FloorMaterial=Enum.Material.Grass
 activate(player,"C")
 local pad=live.world:FindFirstChild(PAD)
 moveOnPad(pad)
 owner.heldEggs=1
 contact()
 check(rootPart.AssemblyLinearVelocity.Y==0,"same owner's new egg pickup also prevents using the old pad")
 return "current custody and a safe grounded start are checked at both boundaries"
end

function growthCases.builder_works_live_off()
 local live=start(true)
 activate(player,"D")
 local guard,pad=live.world:FindFirstChild(GUARD),live.world:FindFirstChild(PAD)
 check(guard and pad,"both instances exist before rollback")
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 check(not guard.Parent and not pad.Parent and protection("NEUTRAL","SWARM_MELEE")==100 and not tool("D")
  and not player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName"),"OFF retires new existing state and restores normal gear")
 return "independent runtime rollback clears devices, contact reduction and optional Tools"
end

function growthCases.builder_works_physical_off()
 local live=start(false)
 check(not scenes:FindFirstChild("ROLE_BUILDER_WORKS") and not live.builderWorksLoadouts and not tool("D"),
  "byte-exact predecessor has no new state, keeps its original role and options")
 return "the actual prior build keeps the original Builder kit"
end
end
