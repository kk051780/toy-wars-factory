do
local FLAG="P0D_ENABLE_PRIVATE_BUILDER_COVER"
local names={"盾機","電磁障壁","発泡盾","小壁"}
local ids={"BUILDER-026","BUILDER-048","BUILDER-066","BUILDER-072"}
local tags={"ShieldUnit","MagneticBarrier","FoamShield","FieldPanel"}
local facing=Vector3.new(0,0,-1)

local function tools()
 local result={}
 for _,folder in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,tool in ipairs(folder:GetChildren()) do
   local value=tool:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(value)=="string" and value:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then check(not result[slot],"one physical role tool per slot");result[slot]=tool end
  end
 end
 return result
end

local function old(t)
 check(t.A.Name=="技A・電磁射撃" and t.B.Name=="技B・多弾ロケット" and t.C.Name=="技C・自動砲塔",
  "existing physical ABC names")
end

local function start(index)
 local stand=scenes:FindFirstChild("ROLE_BUILDER")
 trigger(player,stand,"職業選択")
 if index then
  for i=1,index do
   trigger(player,stand,"遮蔽を装備")
   check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")==names[i],"real lobby cycling to "..names[i])
   advanceTo(now+.51)
  end
 end
 local live=ready("PRIVATE_BUILDER_COVER","BUILDER")
 local t=tools()
 old(t)
 if index then
  check(live.builderCoverLoadouts[player.UserId]==ids[index] and t.D:GetAttribute("EGGRUMBLE_FixedAbilityId")==ids[index],
   "exact server-selected D identity")
 else
  check(not t.D,"standard Builder retains three slots")
 end
 local field=live.world:FindFirstChild("TacticalBattlefield")
 local floor=field.Position+Vector3.new(170,field.Size.Y*.5,-115)
 local origin=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(origin,origin+facing)
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.FloorMaterial=Enum.Material.Grass
 return live,origin,field
end

local function cover(live,index)
 return live.world:FindFirstChild("EGGRUMBLE_BuilderCover_"..tags[index])
end

local function stamina(live)
 return live.swarm.getRoleGrowthSnapshot(player).energy
end

local function barrier(live,index,checkLife)
 local t=now
 activate(player,"D")
 local item=cover(live,index)
 check(item~=nil and item.Anchored and item.CanQuery and item.CanCollide and not item.CanTouch,"real blocking geometry")
 check(item:GetAttribute("EGGRUMBLE_FixedAbilityId")==ids[index]
  and item:GetAttribute("EGGRUMBLE_ConstructOwner")==player.UserId
  and item.Size.X==(if index==2 then 3 else 2),"exact S0 geometry and owner")
 check(stamina(live)==60 and player:GetAttribute("EGGRUMBLE_SkillCastSignature"):match("^BUILDER:D:"),"actual one E40 cost")
 local point=item.Position
 local ray=RaycastParams.new()
 ray.RespectCanCollide=true
 local hit=workspace:Raycast(point+Vector3.new(0,0,1.7),facing*3.4,ray)
 local miss=workspace:Raycast(point+Vector3.new(item.Size.X*.5+.6,0,1.7),facing*3.4,ray)
 check(hit and hit.Instance==item and (not miss or miss.Instance~=item),"new construct really blocks an in-band ray, outside remains open")
 local accepted=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 activate(player,"D")
 check(cover(live,index)==item and stamina(live)==60 and player:GetAttribute("EGGRUMBLE_SkillCastSignature")==accepted,
  "existing shared owner cap with no second debit")
 if checkLife then
  local life=if index==3 then 1.5 else 2
  advanceTo(t+life-.001)
  check(item.Parent==live.world,"wall does not disappear before authored life")
  advanceTo(t+life+.001)
  check(not item.Parent,"fallible physical wall cleans up on the exact lifespan")
  activate(player,"D")
  check(not cover(live,index) and stamina(live)==60,"current canonical cooldown retains the debit")
 end
 return item
end

for index=1,4 do
 growthCases["cover_"..index]=function()
  local live=start(index)
  barrier(live,index,true)
  return ids[index].." exact real Tool, S0 width, blocking ray, one debit, owner cap and expiry"
 end
end

function growthCases.cover_neutral_break()
 local live,origin=start(3)
 local sw=live.world:FindFirstChild("NeutralHorde")
 local prepared={}
 for _=1,48 do
  table.clear(prepared)
  for _,model in ipairs(sw:GetChildren()) do
   local hp=model:FindFirstChildOfClass("Humanoid")
   if hp and hp.Health>0 and model.PrimaryPart then
    model:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    model:PivotTo(CFrame.new(origin+Vector3.new(39,0,30)))
    table.insert(prepared,model)
   end
  end
  if #prepared>=2 then break end
  advanceTo(now+.35)
 end
 check(#prepared>=2,"two actual fixture-spawned Swarm members")
 local item=barrier(live,3,false)
 local oldHealth=humanoid.Health
 local castle=live.rules.castles[tostring(player.UserId)]
 local ownerHP=castle.hp
 local home=item.Position
 rootPart.CFrame=CFrame.lookAt(Vector3.new(home.X,origin.Y,home.Z+1.45),home)
 local first,second=prepared[1],prepared[2]
 first:PivotTo(CFrame.new(Vector3.new(home.X,origin.Y-.45,home.Z-1.65)))
 local started=now
 advanceTo(started+.39)
 check(item.Parent and item:GetAttribute("EGGRUMBLE_ConstructGuardHits")==1 and humanoid.Health==oldHealth,
  "real existing Swarm melee ray hits cover once and preserves victim HP")
 first:PivotTo(CFrame.new(origin+Vector3.new(39,0,30)))
 second:PivotTo(CFrame.new(Vector3.new(home.X,origin.Y-.45,home.Z-1.6)))
 advanceTo(started+.81)
 check(item.Parent==nil and humanoid.Health==oldHealth and castle.hp==ownerHP and live.swarm.getTotal()==0,
  "second real neutral swing exhausts foam early with no victim/castle/KO write")
 return "existing authoritative neutral swings physically break a covered player route before TTL"
end

local function rejected(kind)
 local live,origin,field=start(1)
 if kind=="carrier" then
  live.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=="route" then
  local route=live.world:FindFirstChild("TacticalRoute_1")
  local at=route.Position+Vector3.new(0,3,0)
  rootPart.CFrame=CFrame.lookAt(at,at+facing)
 elseif kind=="castle" then
  local at=live.castleLocations[tostring(player.UserId)]+Vector3.new(16,3,-22)
  rootPart.CFrame=CFrame.lookAt(at,at+facing)
 elseif kind=="actor" then
  secondRoot.CFrame=CFrame.new(origin+facing*5.5)
 elseif kind=="air" then
  humanoid.FloorMaterial=Enum.Material.Air
 end
 activate(player,"D")
 if kind=="carrier" then live.rules.castles[tostring(player.UserId)].heldEggs=0 end
 check(not cover(live,1) and stamina(live)==100 and player:GetAttribute("EGGRUMBLE_SkillCastSignature")==nil,
  "reject without energy or cue for "..kind)
 return "physical actor/terrain and objective guard refuses "..kind
end
for _,kind in ipairs({"carrier","route","castle","actor","air"}) do
 growthCases["cover_reject_"..kind]=function() return rejected(kind) end
end

function growthCases.cover_off()
 local live=start(2)
 local item=barrier(live,2,false)
 local stale=tools().D
 workspace:SetAttribute(FLAG,false)
 drainDeferred()
 old(tools())
 check(not item.Parent and not tools().D and not stale.Parent and not live.builderCoverLoadouts[player.UserId],
  "dynamic OFF removes existing geometry and original owner ability state")
 stale.Activated:Fire()
 check(not cover(live,2) and stamina(live)==60,"old physical callback cannot respawn")
 return "OFF retires old wall and D Tool, same legacy Builder ABC stays"
end

function growthCases.cover_avatar()
 local live=start(4)
 local item=barrier(live,4,false)
 player.CharacterRemoving:Fire(player.Character)
 drainDeferred()
 check(not item.Parent and not cover(live,4),"old avatar removes any still-live wall")
 return "character removing retires active structure before the authored TTL"
end

function growthCases.cover_legacy_construct()
 local live,origin=start(2)
 local part=barrier(live,2,false)
 local tool=player:FindFirstChildOfClass("Backpack"):FindFirstChild("EGGRUMBLE_SKILL_CONSTRUCT_WALL")
 check(tool and tool:IsA("Tool"),"existing GQ522 wall remains physical")
 local nextOrigin=origin+Vector3.new(15,0,0)
 rootPart.CFrame=CFrame.lookAt(nextOrigin,nextOrigin+facing)
 tool.Parent=player.Character
 tool.Activated:Fire()
 local legacy=live.world:FindFirstChild("EGGRUMBLE_BUILDER_WALL")
 check(legacy and legacy.CanCollide and part.Parent and stamina(live)==60,"both sit in the existing construction cap without paying a second growth bill")
 advanceTo(now+2.01)
 check(not part.Parent and legacy.Parent,"legacy wall TTL and construction route are unchanged")
 return "existing GQ522 Tool physically builds its original wall beside the new short cover"
end

function growthCases.cover_physical_off()
 start(nil)
 local stand=scenes:FindFirstChild("ROLE_BUILDER")
 for _,child in ipairs(stand:GetChildren()) do
  check(not child:IsA("ProximityPrompt") or child.ActionText~="遮蔽を装備","physical OFF has no new affordance")
 end
 return "unchanged parent Builder A/B/C and original specialized gear suit remain"
end
end
