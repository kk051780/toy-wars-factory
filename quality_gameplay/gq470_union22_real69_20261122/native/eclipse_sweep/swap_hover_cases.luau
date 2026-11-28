do
local function tool(slot)
 for _,container in ipairs({player:FindFirstChildOfClass("Backpack"),character}) do
  for _,entry in ipairs(container:GetChildren()) do
   local id=entry:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(id)=="string" and id:match("^EGGRUMBLE_SKILL_"..slot.."_") then return entry end
  end
 end
end
local function near(actual,wanted)
 return (actual-wanted).Magnitude<.035
end
local function sameTile(actual,wanted)
 return math.abs(actual.X-wanted.X)<.035 and math.abs(actual.Z-wanted.Z)<.035
end
local function aim(at)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
end
local function setup(withTarget)
 local stand=scenes:FindFirstChild("ROLE_TRAPPER")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"交換浮遊を装備")
 local match=ready("TRAPPER_SWAP_ACTUAL_TOOL","TRAPPER")
 check(match.trapperSwapHoverLoadouts[player.UserId],"Host keeps only chosen legal deck")
 for slot,id in pairs({B="TRAPPER-025",C="TRAPPER-054",D="COMBO-011"}) do
  check(tool(slot) and tool(slot):GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"legitimate "..id)
 end
 check(tool("A").Name=="技A・念動衝撃","original A")
 local target=if withTarget then spawnCurrentNeutral(match) else nil
 local floor=match.world:FindFirstChild("TacticalBattlefield")
 local level=floor.Position.Y+floor.Size.Y*.5
 local origin=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 local neutralFolder=match.world:FindFirstChild("NeutralHorde")
 for _,other in ipairs(neutralFolder:GetChildren()) do
  if other.PrimaryPart then
   other:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
   other:PivotTo(CFrame.new(origin+Vector3.new(-36,8,25)))
  end
 end
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 humanoid.MoveDirection=Vector3.zero
 rootPart.AssemblyLinearVelocity=Vector3.zero;rootPart.AssemblyAngularVelocity=Vector3.zero
 aim(origin)
 advanceTo(now+.39)
 if target then
  local height=2*(target.PrimaryPart.Size.Y/2.5)
  local targetAt=Vector3.new(origin.X+3.45,level+height,origin.Z)
  target:PivotTo(CFrame.new(targetAt))
  local health=target:FindFirstChildOfClass("Humanoid")
  health.Health=120
  return match,origin,target,targetAt,health
 end
 return match,origin
end
local function energy(match)
 return match.swarm.getRoleGrowthSnapshot(player).energy
end
local function gates(match)
 local count=0
 for _,entry in ipairs(match.world:GetChildren()) do
  if entry.Name=="EGGRUMBLE_TrapperExchangeGate" then count+=1 end
 end
 return count
end
local function block(match,at,size)
 local wall=Instance.new("Part");wall.Size=size;wall.CFrame=CFrame.new(at)
 wall.Anchored=true;wall.CanQuery=true;wall.CanCollide=true;wall.Parent=match.world
 return wall
end
local function swapped(origin,actorAt,target,neutralAt)
 return near(rootPart.Position,Vector3.new(actorAt.X,origin.Y,actorAt.Z))
    and near(target.PrimaryPart.Position,Vector3.new(origin.X,neutralAt.Y,origin.Z))
end

function growthCases.swap_pair()
 local match,origin,target,to,hp=setup(true)
 local t=now
 activate(player,"B")
 check(energy(match)==55 and gates(match)==2,"one E45 and two actual endpoint tells")
 advanceTo(t+.599)
 check(near(rootPart.Position,origin) and near(target.PrimaryPart.Position,to),"nothing moves before .60")
 advanceTo(t+.601)
 check(swapped(origin,to,target,to) and gates(match)==0,"both real bodies exchanged")
 check(hp.Health==120 and match.swarm.getTotal()==0,"no attack on the exchanged neutral")
 return "B exact two confirmations and a safe atomic position exchange"
end

function growthCases.swap_hover()
 local match,origin=setup(false)
 local t=now
 activate(player,"C")
 check(rootPart.Anchored and energy(match)==65,"real hover E35 once")
 advanceTo(t+.25)
 check(rootPart.Position.Y>origin.Y+.85 and math.abs(rootPart.Position.X-origin.X)<.03,
  "actual vertical hover, no horizontal movement")
 advanceTo(t+.54)
 check(not rootPart.Anchored and near(rootPart.Position,origin),"same-position safe touchdown")
 return "C rises by real bounded height and releases its caster"
end

function growthCases.swap_combo()
 local match,origin,target,to,hp=setup(true)
 local t=now
 activate(player,"D")
 check(energy(match)==20 and gates(match)==2,"one E80 for the real sequence")
 advanceTo(t+.601)
 check(swapped(origin,to,target,to) and rootPart.Anchored,"physical exchange authorizes hover")
 advanceTo(t+.845)
 check(rootPart.Position.Y>origin.Y+.85,"actual hover after exchange")
 advanceTo(t+1.17)
 check(not rootPart.Anchored and swapped(origin,to,target,to) and hp.Health==120,
  "safe grounding at the exchanged endpoint and no attack: "..tostring(rootPart.Position.X)..","..
   tostring(rootPart.Position.Y).." expected "..tostring(to.X)..","..tostring(origin.Y)..
   " anchor "..tostring(rootPart.Anchored).." target "..tostring(target.PrimaryPart.Position.X).." hp "..tostring(hp.Health))
 return "D performs exchange, hover and landing after one paid opportunity"
end

function growthCases.swap_late_wall()
 local match,origin,target,to=setup(true)
 local t=now
 activate(player,"D")
 check(gates(match)==2 and energy(match)==20,"cast confirmed before obstruction")
 local wall=block(match,origin+Vector3.new(1.65,0,0),Vector3.new(.40,8,8))
 local rays=RaycastParams.new()
 rays.FilterType=Enum.RaycastFilterType.Exclude
 rays.FilterDescendantsInstances={character,target}
 rays.RespectCanCollide=true
 local hit=workspace:Blockcast(CFrame.new(origin+Vector3.new(0,.23,0)),Vector3.new(2.1,3.5,2.1),to-origin,rays)
 check(hit and hit.Instance==wall,"test wall actually intercepts the measured hero sweep")
 advanceTo(t+.82)
 check(sameTile(rootPart.Position,origin) and sameTile(target.PrimaryPart.Position,to) and not rootPart.Anchored
  and gates(match)==0,"late wall invalidates both mutations and the hover: "..tostring(rootPart.Position.X)..
   " versus "..tostring(origin.X).." neutral "..tostring(target.PrimaryPart.Position.X)..
   " anchor "..tostring(rootPart.Anchored).." gates "..tostring(gates(match)))
 return "late corridor obstruction cancels the pair without partial exchange"
end

function growthCases.swap_ceiling()
 local match,origin=setup(false)
 block(match,origin+Vector3.new(0,2.55,0),Vector3.new(6,.3,6))
 activate(player,"C")
 check(energy(match)==100 and near(rootPart.Position,origin) and not rootPart.Anchored,
  "known ceiling rejected before energy")
 return "real overhead geometry blocks unpayable hover"
end

function growthCases.swap_egg()
 local match,origin,target,to=setup(true)
 local castle=match.rules.castles[tostring(player.UserId)]
 local t=now
 activate(player,"B")
 check(gates(match)==2,"real no-cargo start")
 castle.heldEggs=1
 advanceTo(t+.62)
 check(castle.heldEggs==1 and near(rootPart.Position,origin) and near(target.PrimaryPart.Position,to),
  "the real castle ownership boundary rejects the pending exchange on carry")
 return "real held egg cancels movement rather than changing custody"
end

function growthCases.swap_live_off()
 local match,origin,target,to=setup(true)
 local t=now
 activate(player,"B")
 check(gates(match)==2,"pending current warning")
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_TRAPPER_SWAP_HOVER",false)
 check(gates(match)==0 and tool("C").Name=="技C・空間転移" and not tool("D"),"runtime flag restores original tools")
 advanceTo(t+.72)
 check(near(rootPart.Position,origin) and near(target.PrimaryPart.Position,to),"stale callback cannot swap")
 return "real OFF stops pending movement and restores A/B/C"
end

function growthCases.swap_physical_off()
 local match=ready("TRAPPER_SWAP_PRIOR_PARENT","TRAPPER")
 local stand=scenes:FindFirstChild("ROLE_TRAPPER")
 for _,entry in ipairs(stand:GetChildren()) do
  check(not entry:IsA("ProximityPrompt") or entry.ActionText~="交換浮遊を装備","physical old source offers no new deck")
 end
 check(match.isCurrentHuman(player) and tool("C").Name=="技C・空間転移" and not tool("D"),"same physical old A/B/C")
 return "physical OFF keeps the original role and no exchange prompt"
end
end
