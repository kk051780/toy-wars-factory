do
local FLAG="P0D_ENABLE_PRIVATE_BUILDER_TRANSFORM"
local heading=Vector3.new(1,0,0)
local function tool(slot)
 for _,container in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(container:GetChildren()) do
   local name=item:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(name)=="string" and name:match("^EGGRUMBLE_SKILL_"..slot.."_") then return item end
  end
 end
 return nil
end
local function legacy()
 check(tool("A").Name=="技A・電磁射撃" and tool("B").Name=="技B・多弾ロケット" and tool("C").Name=="技C・自動砲塔" and not tool("D"),
  "actual original default A/B/C")
end
local function start(equip)
 local stand=scenes:FindFirstChild("ROLE_BUILDER")
 trigger(player,stand,"職業選択")
 if equip~=false then
  trigger(player,stand,"変形を装備")
  check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="超機変形・超機磁甲","real role offer")
 end
 local live=ready("PRIVATE_BUILDER_TRANSFORM","BUILDER")
 if equip~=false then
  check(tool("A").Name=="技A・形態切替・機甲" and not tool("A"):GetAttribute("EGGRUMBLE_FixedAbilityId")
   and tool("B"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="BUILDER-060"
   and tool("C"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="BUILDER-048"
   and tool("D"):GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-014"
   and tool("D").ToolTip:find("E80",1,true),"exact physical B/C/D and owner-only A selector")
 else legacy() end
 local veld=live.world:FindFirstChild("TacticalBattlefield")
 local floor=veld.Position+Vector3.new(170,veld.Size.Y*.5,-115)
 local origin=floor+Vector3.new(0,3,0)
 rootPart.CFrame=CFrame.lookAt(origin,origin+heading)
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false;humanoid.PlatformStand=false
 rootPart.AssemblyLinearVelocity=Vector3.zero
 rootPart.AssemblyMass=8;workspace.Gravity=196.2
 return live,floor,origin
end
local function evolve(live,floor,origin,stage)
 local steps={Vector3.zero,Vector3.new(0,0,1),Vector3.new(1,0,1),Vector3.new(1,0,0)}
 for i=1,590 do
  if player:GetAttribute("EGGRUMBLE_RoleAbilityStage")==stage then break end
  local at=origin+steps[(i-1)%4+1]
  rootPart.CFrame=CFrame.lookAt(at,at+heading)
  advanceTo(now+.39)
  for _,unit in ipairs(live.world:FindFirstChild("NeutralHorde"):GetChildren()) do
   if unit:FindFirstChildOfClass("Humanoid") and unit.PrimaryPart then
    unit:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
    unit:PivotTo(CFrame.new(floor+Vector3.new(-42,2,29)))
   end
  end
 end
 rootPart.CFrame=CFrame.lookAt(origin,origin+heading)
 check(live.swarm.getRoleGrowthSnapshot(player).stage==stage,"normal active match growth is authoritative")
end
local function stance(id) return player.Character:FindFirstChild("EGGRUMBLE_Transform_"..id) end
local function preview() return player.Character:FindFirstChild("EGGRUMBLE_TransformTell") end
local function barrier(live) return live.world:FindFirstChild("EGGRUMBLE_BuilderCover_MagneticBarrier") end
local function energy(live) return live.swarm.getRoleGrowthSnapshot(player).energy end
local function approx(a,b) return math.abs(a-b)<.02 end
local function hostileHit(floor)
 local start=floor+Vector3.new(20,3,0)
 secondRoot.CFrame=CFrame.lookAt(start,start-heading)
 local before=humanoid.Health
 activate(second,"A")
 return before-humanoid.Health
end
local function cast(live,slot,expectedEnergy)
 local t=now
 activate(player,slot)
 local signature=player:GetAttribute("EGGRUMBLE_SkillCastSignature")
 check(signature and signature:match("^BUILDER:"..slot..":") and energy(live)==expectedEnergy,
  "same server Growth issues one cast and one debit")
 activate(player,slot)
 check(player:GetAttribute("EGGRUMBLE_SkillCastSignature")==signature and energy(live)==expectedEnergy,"same current state cannot double charge")
 return t
end

function growthCases.transform_armor()
 local live,floor=start()
 activate(player,"A")
 check(player:GetAttribute("EGGRUMBLE_BuilderFormSelection")=="機甲" and energy(live)==100,"S0 only admits armor and selecting is free")
 local t=cast(live,"B",50)
 check(preview() and not stance("ARMOR"),"same avatar visible preview is not the form")
 advanceTo(t+.799)
 check(not stance("ARMOR"),"locked .8 forewarning")
 advanceTo(t+.801)
 check(stance("ARMOR") and not preview() and approx(hostileHit(floor),44*.88),
  "actual hostile Player A is mitigated by exactly 12% without immunity")
 check(humanoid.MaxHealth==100 and rootPart.Size.Y>0 and not stance("DRIVE") and not stance("GLIDE") and not barrier(live),
  "one loadout effect, no alternate HP or extra wall")
 advanceTo(t+2.801)
 check(not stance("ARMOR") and approx(hostileHit(floor),44),"same ordinary actual hit restores after duration")
 return "S0 one real armor form reduces known real damage by twelve per cent only for two seconds"
end

function growthCases.transform_drive()
 local live,floor,origin=start()
 evolve(live,floor,origin,1)
 activate(player,"A")
 check(player:GetAttribute("EGGRUMBLE_BuilderFormSelection")=="走行","S1 unlocks only driving")
 local initial=humanoid.WalkSpeed
 local t=cast(live,"B",50)
 advanceTo(t+.799)
 check(humanoid.WalkSpeed==initial and not stance("DRIVE"),"no boost before preview ends")
 advanceTo(t+.801)
 check(stance("DRIVE") and not stance("ARMOR") and not stance("GLIDE") and approx(humanoid.WalkSpeed,initial*1.10),
  "actual existing walk owner grants exactly +10 percent")
 activate(player,"A")
 check(player:GetAttribute("EGGRUMBLE_BuilderFormSelection")=="走行","one active form cannot be changed")
 advanceTo(t+3.301)
 check(not stance("DRIVE") and humanoid.WalkSpeed==initial,"same old walk baseline restored")
 return "S1 selecting driving changes only real WalkSpeed and retires the same lease"
end

function growthCases.transform_glide()
 local live,floor,origin=start()
 evolve(live,floor,origin,3)
 activate(player,"A")
 advanceTo(now+.251)
 activate(player,"A")
 check(player:GetAttribute("EGGRUMBLE_BuilderFormSelection")=="滑空","S3 admits third shape only")
 local t=cast(live,"B",50)
 advanceTo(t+.801)
 local model=stance("GLIDE")
 local force=model and model:FindFirstChild("EGGRUMBLE_BuilderGlideForce")
 check(force and force.Force.Magnitude==0 and not stance("DRIVE") and not stance("ARMOR"),"no force on ground")
 humanoid.FloorMaterial=Enum.Material.Air
 rootPart.AssemblyLinearVelocity=Vector3.new(1,-9,0)
 advanceTo(t+.95)
 RunService.Heartbeat:Fire(1/60)
 check(approx(force.Force.Y,workspace.Gravity*rootPart.AssemblyMass*.30)
  and force.Force.X==0 and force.Force.Z==0,"existing current falling avatar gets one capped physical counterforce")
 rootPart.AssemblyLinearVelocity=Vector3.new(0,5,0)
 advanceTo(t+1.08)
 RunService.Heartbeat:Fire(1/60)
 check(force.Force.Magnitude==0,"no lift on upward travel")
 advanceTo(t+4.301)
 check(not model.Parent and not rootPart:FindFirstChild("EGGRUMBLE_BuilderGlidePoint"),"force and attachment are removed at exact lifetime")
 return "S3 current falling avatar gets actual VectorForce allocation below gravity and old motion returns"
end

function growthCases.transform_combo()
 local live=start()
 local original=live.swarm.tryRoleGrowthCast
 local granted
 local grants=0
 live.swarm.tryRoleGrowthCast=function(actor,role,cd,energy,deadlines)
  local value=original(actor,role,cd,energy,deadlines)
  if value~=nil then
   grants+=1
   granted=deadlines
  end
  return value
 end
 local t=cast(live,"D",20)
 check(preview() and not stance("ARMOR") and not barrier(live),"combo charge authorizes no premature construction")
 advanceTo(t+.799)
 check(not stance("ARMOR") and not barrier(live),"actual world waits the full 0.8 seconds")
 advanceTo(t+.801)
 local item=barrier(live)
 check(stance("ARMOR") and item and item.CanCollide and item.CanQuery and item.Size.X==3
  and item:GetAttribute("EGGRUMBLE_ConstructOwner")==player.UserId and item:GetAttribute("EGGRUMBLE_FixedAbilityId")=="BUILDER-048",
  "valid form settles before exact shared physical placement")
 check(grants==1 and granted["BUILDER-060"]==35 and granted["BUILDER-048"]==27
  and granted["COMBO-014"]==40 and energy(live)==20,"one actual Growth call commits both component and combo clocks")
 activate(player,"C")
 check(barrier(live)==item and energy(live)==20,"component cannot make a duplicate or charge its own bill")
 advanceTo(t+2.801)
 check(not item.Parent and not stance("ARMOR"),"existing cover TTL and form lease both retire")
 return "actual D activates one shape then original 048 geometry and commits one E80/Cooldown set"
end

function growthCases.transform_cover_only()
 local live=start()
 cast(live,"C",60)
 local item=barrier(live)
 check(item and item.CanCollide and not stance("ARMOR") and not preview(),"standalone original 048 still builds through same owner")
 return "standalone C uses the same owned barrier without deploying or charging armor"
end

local function denial(kind)
 local live,floor=start()
 if kind=="prewall" then
  local wall=Instance.new("Part")
  wall.Name="TestSolidWall";wall.Anchored=true;wall.CanCollide=true;wall.CanQuery=true
  wall.Size=Vector3.new(.28,7,6);wall.CFrame=CFrame.new(floor+Vector3.new(4,2.5,0));wall.Parent=live.world
  activate(player,"D")
  check(energy(live)==100 and not preview() and not barrier(live),"invalid preflight does not charge")
  return "illegal initial geometry rejects the real combo before E"
 end
 local t=cast(live,"D",20)
 if kind=="latewall" then
  local wall=Instance.new("Part")
  wall.Anchored=true;wall.CanCollide=true;wall.CanQuery=true;wall.Size=Vector3.new(.25,7,6)
  wall.CFrame=CFrame.new(floor+Vector3.new(4,2.5,0));wall.Parent=live.world
 elseif kind=="avatar" then
  player.CharacterRemoving:Fire(player.Character)
  player.Character=Instance.new("Model")
 elseif kind=="off" then
  advanceTo(t+.802)
  check(stance("ARMOR") and barrier(live),"OFF witnesses live installed composite first")
  workspace:SetAttribute(FLAG,false)
  drainDeferred();legacy()
 end
 advanceTo(t+.92)
 check(not preview() and not stance("ARMOR") and not barrier(live),"stale actor, wall or OFF clears both effects")
 return "live combo releases no residual form or wall after "..kind
end
for _,kind in ipairs({"prewall","latewall","avatar","off"}) do
 growthCases["transform_deny_"..kind]=function() return denial(kind) end
end

function growthCases.transform_physical_off()
 start(false)
 for _,offer in ipairs(scenes:FindFirstChild("ROLE_BUILDER"):GetChildren()) do
  check(not offer:IsA("ProximityPrompt") or offer.ActionText~="変形を装備","true rollback has no new offer")
 end
 return "immediate physical predecessor keeps its original default, cannon and cover source"
end
end
