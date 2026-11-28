do
local FLAG="P0D_ENABLE_PRIVATE_COMMON_FOOTING"
local VERB="空中足場を装備"
local PLATFORM="EGGRUMBLE_CommonAirFooting"
local GUARD="EGGRUMBLE_LightShieldFooting"
local EAST=Vector3.new(1,0,0)

local function fixed(slot)
 for _,container in ipairs({player:FindFirstChildOfClass("Backpack"),character}) do
  for _,entry in ipairs(container:GetChildren()) do
   local id=entry:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(id)=="string" and id:match("^EGGRUMBLE_SKILL_"..slot.."_") then
    return entry:GetAttribute("EGGRUMBLE_FixedAbilityId")
   end
  end
 end
end

local function stage(role,combo,optIn)
 local stand=scenes:FindFirstChild("ROLE_"..role)
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 if combo then
  for _=1,3 do
   trigger(player,stand,"剣技を装備")
   advanceTo(now+.51)
  end
 end
 if optIn then
  trigger(player,scenes:FindFirstChild("ROLE_FOOTING"),VERB)
  check(player:GetAttribute("EGGRUMBLE_LobbyFooting")==true,"real server chose the common C")
 end
 local live=ready("PRIVATE_COMMON_FOOTING_ACTUAL_TOOL",role)
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local at=floor+Vector3.new(0,5.0,0)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 rootPart.AssemblyLinearVelocity=Vector3.new(0,-1.2,0)
 humanoid.HipHeight=2;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.FloorMaterial=Enum.Material.Air;humanoid.MoveDirection=Vector3.zero
 advanceTo(now+.39)
 return live,floor,at
end

function growthCases.footing_loadout_exclusive()
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 for _=1,8 do
  trigger(player,stand,"装備する")
  advanceTo(now+.51)
  if player:GetAttribute("EGGRUMBLE_LobbyMageProjectileName")=="水弾＋連鎖雷" then break end
 end
 check(player:GetAttribute("EGGRUMBLE_LobbyMageProjectileName")=="水弾＋連鎖雷","selected the original water-chain kit")
 local live=stage("MAGE",false,true)
 check(fixed("C")=="COMMON-025" and not fixed("D"),
  "selecting common C must not expose the previous kit's D recipe")
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 check(fixed("C")~="COMMON-025" and fixed("D")=="COMBO-004",
  "turning off common C restores the existing Mage recipe")
 return "shared C keeps recipe component selection consistent and restores the previous Mage kit"
end

local function energy(live)
 return live.swarm.getRoleGrowthSnapshot(player).energy
end

local function count(live,name)
 local n=0
 for _,entry in ipairs(live.world:GetChildren()) do
  if entry.Name==name then n+=1 end
 end
 return n
end

local function settle(part,shift)
 local at=part.Position+Vector3.new(shift or 0,3.15,0)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 rootPart.AssemblyLinearVelocity=Vector3.zero
 humanoid.FloorMaterial=Enum.Material.WoodPlanks
end

local function approx(a,b) return math.abs(a-b)<.02 end

for _,role in ipairs({"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}) do
 growthCases["footing_role_"..role:lower()]=function()
  local live,_,at=stage(role,false,true)
  check(fixed("C")=="COMMON-025" and live.footingLoadouts[player.UserId],"actual C slot belongs to the chosen current role")
  local t=now
  activate(player,"C")
  local plank=live.world:FindFirstChild(PLATFORM)
  check(plank and plank.Parent==live.world and plank.Anchored and plank.CanCollide and plank.CanQuery
   and not plank.CanTouch and plank.Size.X==2 and plank.Size.Z==2,
   "one true collidable S0 board underneath the avatar")
  check((rootPart.Position-at).Magnitude<.02 and plank.Position.Y<at.Y and energy(live)==55,
   "physical support only, one E45 with no hero movement")
  activate(player,"C")
  check(count(live,PLATFORM)==1 and energy(live)==55,"no stacking or duplicate E")
  advanceTo(t+.98)
  check(plank.Parent==live.world,"actual temporary platform lasts one second")
  advanceTo(t+1.01)
  check(not plank.Parent,"the plank expires and is de-registered")
  return role.." current authorized C placed a collidable S0 platform at its real position"
 end
end

function growthCases.footing_grounded_and_ascending()
 local live=stage("MAGE",false,true)
 humanoid.FloorMaterial=Enum.Material.Grass
 activate(player,"C")
 check(energy(live)==100 and count(live,PLATFORM)==0,"grounded cast does not pay or create support")
 humanoid.FloorMaterial=Enum.Material.Air
 rootPart.AssemblyLinearVelocity=Vector3.new(0,4,0)
 activate(player,"C")
 check(energy(live)==100 and count(live,PLATFORM)==0,"ascending avatar does not pay or create support")
 rootPart.AssemblyLinearVelocity=Vector3.new(0,-1,0)
 activate(player,"C")
 check(energy(live)==55 and count(live,PLATFORM)==1,"same legal slot still works after rejected casts")
 return "airborne and descending, with no loss on rejected input"
end

function growthCases.footing_obstacle()
 local live,floor=stage("MAGE",false,true)
 local block=Instance.new("Part")
 block.Size=Vector3.new(2,.4,2)
 block.CFrame=CFrame.new(floor+Vector3.new(.65,1.4,0))
 block.CanCollide=true;block.CanQuery=true;block.Anchored=true;block.Parent=live.world
 activate(player,"C")
 check(energy(live)==100 and count(live,PLATFORM)==0,"blocked physical placement costs no energy")
 block:Destroy()
 activate(player,"C")
 check(energy(live)==55 and count(live,PLATFORM)==1,"clean placement still works")
 return "real overlapping world geometry denies placement before spending"
end

function growthCases.footing_egg_or_off_field()
 local live,_,at=stage("MAGE",false,true)
 local owner=live.rules.castles[tostring(player.UserId)]
 local signature=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 owner.heldEggs=1
 activate(player,"C")
 check(count(live,PLATFORM)==0 and player:GetAttribute("EGGRUMBLE_SkillCastSignature")==signature,
  "current egg custody prevents footing")
 owner.heldEggs=0
 rootPart.CFrame=CFrame.new(at+Vector3.new(3000,0,0))
 activate(player,"C")
 check(count(live,PLATFORM)==0 and player:GetAttribute("EGGRUMBLE_SkillCastSignature")==signature,
  "outside field denies placement")
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 check(energy(live)==100,"rejected footing has not spent energy")
 return "carried egg and out-of-arena positions cannot enable physical footing"
end

function growthCases.footing_combo_landing()
 local live=stage("WARRIOR",true,true)
 check(fixed("A")=="WARRIOR-018" and fixed("C")=="COMMON-025" and fixed("D")=="COMBO-003",
  "original selected Diamond guard plus common footing composes one actual D")
 local t=now
 activate(player,"D")
 local plank=live.world:FindFirstChild(PLATFORM)
 check(plank and energy(live)==20 and count(live,GUARD)==0,"one E80 creates only the platform before contact")
 advanceTo(t+.11)
 check(count(live,GUARD)==0,"unlanded hero has no guard")
 settle(plank,0)
 advanceTo(t+.146)
 check(count(live,GUARD)==1,"the server's actual downward ray hit the caster's own platform")
 local invul=dependencies.EGGRUMBLE_InvulRuntime
 local here=rootPart.Position
 check(approx(invul.filterDamage(humanoid,44,"PLAYER",second.UserId,here+EAST*7),40.48)
  and approx(invul.filterDamage(humanoid,44,"PLAYER",second.UserId,here-EAST*7),44),
  "real pre-hit path reduces frontal HP by 8% and does not reduce a back attack")
 check(invul.currentPolicySnapshot(player).phase=="NONE","guard does not create invulnerability")
 settle(plank,1.4)
 here=rootPart.Position
 check(approx(invul.filterDamage(humanoid,44,"PLAYER",second.UserId,here+EAST*7),44)
  and count(live,GUARD)==0,"leaving own support immediately cancels the guard")
 advanceTo(t+1.02)
 check(not plank.Parent,"platform expires on existing clock")
 return "D uses one E80, own contact, finite front 8%, and immediate contact loss"
end

function growthCases.footing_stage_four()
 local live,floor=stage("MAGE",false,true)
 local base=floor+Vector3.new(0,3,0)
 local moves={Vector3.new(0,0,0),Vector3.new(1.2,0,0),Vector3.new(1.2,0,1.2),Vector3.new(0,0,1.2)}
 humanoid.FloorMaterial=Enum.Material.Grass
 rootPart.AssemblyLinearVelocity=Vector3.zero
 for tick=1,600 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==4 then break end
  local at=base+moves[(tick-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(at,at+EAST)
  advanceTo(now+.39)
  for _,mob in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if mob:FindFirstChildOfClass("Humanoid") then
    mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    mob:PivotTo(CFrame.new(floor+Vector3.new(-38,2,32)))
   end
  end
 end
 check(live.swarm.getRoleGrowthSnapshot(player).stage==4,"genuine active-time route reaches S4")
 local at=base+Vector3.new(0,2,0)
 rootPart.CFrame=CFrame.lookAt(at,at+EAST)
 rootPart.AssemblyLinearVelocity=Vector3.new(0,-1,0)
 humanoid.FloorMaterial=Enum.Material.Air
 local t=now
 activate(player,"C")
 local plank=live.world:FindFirstChild(PLATFORM)
 check(plank and plank.Size.X==4 and plank.Size.Z==4,"actual S4 4-stud platform")
 advanceTo(t+2.98)
 check(plank.Parent==live.world,"S4 stays for its whole window")
 advanceTo(t+3.01)
 check(not plank.Parent,"S4 actual 3-second expiry")
 return "real active-time stage four grows the support footprint and duration to the fixed S4 values"
end

function growthCases.footing_combo_wrong_contact()
 local live=stage("WARRIOR",true,true)
 local t=now
 activate(player,"D")
 local plank=live.world:FindFirstChild(PLATFORM)
 check(plank and energy(live)==20,"paid one sequence")
 local other=Instance.new("Part")
 other.Size=Vector3.new(2,.2,2);other.CFrame=CFrame.new(plank.Position+Vector3.new(0,.65,0))
 other.CanCollide=true;other.CanQuery=true;other.Anchored=true;other.Parent=live.world
 settle(other,0)
 advanceTo(t+.31)
 check(count(live,GUARD)==0,"interposed different physical surface is not the caster's platform")
 advanceTo(t+1.02)
 check(not plank.Parent and count(live,GUARD)==0,"timed out sequence cannot arm after expiry")
 return "another actual surface never satisfies the ownership-checked landing receipt"
end

function growthCases.footing_live_off()
 local live=stage("MAGE",false,true)
 activate(player,"C")
 check(fixed("C")=="COMMON-025" and count(live,PLATFORM)==1,"active platform before runtime rollback")
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 check(not player:GetAttribute("EGGRUMBLE_LobbyFooting") and fixed("C")~="COMMON-025"
  and count(live,PLATFORM)==0,"rollback retires real geometry and restores the original equipped C")
 return "live independent OFF restores the native skill and destroys the existing support"
end

function growthCases.footing_physical_off()
 local live=stage("MAGE",false,false)
 check(not scenes:FindFirstChild("ROLE_FOOTING") and not live.footingLoadouts and fixed("C")~="COMMON-025",
  "independent physical parent has actual original lobby and C")
 return "immediate exact parent has no common footing or new prompt"
end
end
