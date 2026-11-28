do
local FLAG="P0D_ENABLE_PRIVATE_BEAST_ORDERS"
local LABEL="EGGRUMBLE_LobbyBeastOrdersLoadoutName"
local THUNDER="P0D_ENABLE_PRIVATE_BEAST_THUNDER"
local function deck()
 local tools={}
 for _,parent in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,item in ipairs(parent:GetChildren()) do
   local id=item:GetAttribute("EGGRUMBLE_InternalToolId")
   local slot=type(id)=="string" and id:match("^EGGRUMBLE_SKILL_([ABCD])_")
   if slot then tools[slot]=item end
  end
 end
 return tools
end
local function oldDeck(t)
 check(t.A.Name=="技A・獣牙撃" and t.B.Name=="技B・巨獣餌" and t.C.Name=="技C・分裂餌" and not t.D,
  "actual original Beast A/B/C")
end
local function readyOrder(enabled)
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 if enabled then
  check(workspace:GetAttribute(FLAG)==nil,"normal private opt-in available at nil")
  trigger(player,stand,"指令笛を装備")
  check(player:GetAttribute(LABEL)=="追え笛・戻れ笛・守れ笛","actual lobby opt-in")
 end
 local live=ready("PRIVATE_BEAST_ORDERS","BEAST")
 local text=deck()
 if enabled then
  check(live.beastOrderLoadouts[player.UserId] and not live.beastThunderLoadouts[player.UserId]
   and text.B.Name=="技B・巨獣餌" and text.B:GetAttribute("EGGRUMBLE_FixedAbilityId")==nil,"same B summon")
  for slot,id in pairs({A="BEAST-091",C="BEAST-092",D="BEAST-093"}) do
   check(text[slot]:GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"real new Tool "..id)
  end
 else oldDeck(text) end
 return live
end
local function witness(s)
 local model,res
 for _,child in ipairs(s.world:GetChildren()) do
  if child:GetAttribute("EGGRUMBLE_BeastCompanion")==true then
   check(not model,"only one active pet")
   model=child
  end
 end
 if model then res=model:FindFirstChildOfClass("Humanoid") end
 return model,res
end
local function prep(s)
 local neutral=spawnCurrentNeutral(s)
 local nh=neutral:FindFirstChildOfClass("Humanoid")
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local center=floor.Position+Vector3.new(170,floor.Size.Y*.5,-115)
 rootPart.CFrame=CFrame.lookAt(center+Vector3.new(0,3,0),center+Vector3.new(1,3,0))
 secondRoot.CFrame=CFrame.new(center+Vector3.new(-45,3,0))
 humanoid.FloorMaterial=Enum.Material.Grass;humanoid.Sit=false;humanoid.PlatformStand=false
 for _,mob in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  mob:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
  mob:PivotTo(CFrame.new(center+Vector3.new(-55,3,30)))
 end
 nh.Health=140
 advanceTo(now+.39)
 local g=s.swarm.getRoleGrowthSnapshot(player)
 check(g and g.stage==0 and g.energy==100,"real S0 / E100")
 return center,neutral,nh
end
local function summon(s,at)
 activate(player,"B")
 local pet,h=witness(s)
 check(pet and h and pet:GetAttribute("EGGRUMBLE_OwnerId")==player.UserId,"normal B created one original registered pet")
 pet:PivotTo(CFrame.lookAt(at,at+Vector3.new(1,0,0)))
 h.FloorMaterial=Enum.Material.Grass
 return pet,h
end
local function order(pet)
 return pet.PrimaryPart and pet.PrimaryPart:FindFirstChild("EGGRUMBLE_BeastOrderCue")
end
local function energy(s)
 local g=s.swarm.getRoleGrowthSnapshot(player)
 return g and g.energy
end
local function tag()return player:GetAttribute("EGGRUMBLE_SkillCastSignature") end
local function wall(s,point)
 local part=Instance.new("Part")
 part.Name="NativeBeastOrderWall";part.Size=Vector3.new(.4,7,4)
 part.CFrame=CFrame.new(point);part.Anchored=true;part.CanCollide=true;part.CanQuery=true;part.Parent=s.world
 return part
end
local function position(model,at)
 model:PivotTo(CFrame.new(at))
end
local function cueName(model)
 local cue=order(model)
 local text=cue and cue:FindFirstChildOfClass("TextLabel")
 return text and text.Text
end

function growthCases.beast091_chase()
 local s=readyOrder(true)
 local center,mob,hp=prep(s)
 local pet,h=summon(s,center+Vector3.new(-.3,1.55,0))
 position(mob,center+Vector3.new(5.1,2.15,0))
 local original=pet.PrimaryPart.Position
 local t=now
 activate(player,"A")
 local shown=tag()
 check(shown:match("^BEAST:A:") and energy(s)==75 and cueName(pet)=="追え笛","actual A spends exact E25")
 check(h._nativeMoveGoal.X>center.X+2.3 and h._nativeMoveGoal.X<center.X+2.5,"existing pet MoveTo points toward the chosen actual neutral")
 check(pet.PrimaryPart.Position==original and witness(s)==pet and hp.Health==140,"server did not warp, duplicate, or attack")
 activate(player,"A")
 check(energy(s)==75 and tag()==shown,"duplicate command is rejected by original role cooldown ledger")
 advanceTo(t+.42)
 check(h._nativeMoveGoal.X>center.X+2.3 and hp.Health==140,"existing escort loop retains chosen order without authorizing damage")
 advanceTo(t+2.01)
 check(not order(pet) and witness(s)==pet and hp.Health==140,"order expires without replacing or extending the original escort")
 return "actual A retasks one current server-owned companion towards a legal neutral for two seconds"
end

function growthCases.beast092_return()
 local s=readyOrder(true)
 local center=prep(s)
 local pet,h=summon(s,center+Vector3.new(-4.8,1.55,0))
 local initial=pet.PrimaryPart.Position
 local t=now
 activate(player,"C")
 check(cueName(pet)=="戻れ笛" and tag():match("^BEAST:C:") and energy(s)==75,"actual C E25")
 local first=h._nativeMoveGoal
 check(Vector3.new(first.X-center.X,0,first.Z-center.Z).Magnitude<2.4 and pet.PrimaryPart.Position==initial,
  "real owner return issues legal near-owner walk goal without teleporting pet")
 rootPart.CFrame=CFrame.lookAt(center+Vector3.new(-1,3,0),center+Vector3.new(0,3,0))
 advanceTo(t+.43)
 check(h._nativeMoveGoal.X<first.X-.8 and witness(s)==pet,"same real desired point follows current owner position")
 advanceTo(t+2.01)
 check(not order(pet) and witness(s)==pet,"expiry removes the order while preserving the real beast")
 return "actual C returns the same animal by its old MoveTo path, with no relocation shortcut"
end

function growthCases.beast093_guard()
 local s=readyOrder(true)
 local center,mob,hp=prep(s)
 local pet,h=summon(s,center+Vector3.new(-2.4,1.55,0))
 position(mob,center+Vector3.new(5.5,2.15,0))
 local t=now
 activate(player,"D")
 check(cueName(pet)=="守れ笛" and tag():match("^BEAST:D:") and energy(s)==65,"actual D E35")
 local originalGoal=h._nativeMoveGoal
 check(Vector3.new(originalGoal.X-center.X,0,originalGoal.Z-center.Z).Magnitude<=2
  and Vector3.new(originalGoal.X-center.X,0,originalGoal.Z-center.Z).Magnitude>=1.9,"guard stays inside real S0 radius3")
 position(pet,originalGoal)
 advanceTo(t+.43)
 check((h._nativeMoveGoal-originalGoal).Magnitude<.03 and hp.Health==140,"hold order overrides prior autonomous chase")
 advanceTo(t+2.01)
 check(not order(pet) and witness(s)==pet,"guard expires on the same pet")
 return "actual D posts the existing companion to a bounded guard point without changing HP"
end

function growthCases.beast_orders_denied()
 local s=readyOrder(true)
 local center,mob,hp=prep(s)
 local fake=Instance.new("Model")
 fake.Name="UnregisteredEscortProbe";fake:SetAttribute("EGGRUMBLE_OwnerId",player.UserId);fake.Parent=s.world
 local root=Instance.new("Part");root.CFrame=CFrame.new(center+Vector3.new(-2,2,0));root.Parent=fake;fake.PrimaryPart=root
 local f=Instance.new("Humanoid");f.Parent=fake
 activate(player,"A");activate(player,"C");activate(player,"D")
 check(energy(s)==100 and not order(fake) and not witness(s),"owner tag without registry does not authorize any order")
 local pet=summon(s,center+Vector3.new(-3,1.55,0))
 position(mob,center+Vector3.new(5.5,2.15,0))
 mob:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",tostring(second.UserId))
 activate(player,"A")
 check(not order(pet) and energy(s)==100,"do not select another owner's converted target")
 mob:SetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId",nil)
 local blocker=wall(s,center+Vector3.new(2.2,2.1,0))
 activate(player,"A")
 check(not order(pet) and energy(s)==100 and hp.Health==140,"covered target and obstructed route denied")
 blocker:Destroy()
 s.rules.castles[tostring(player.UserId)].heldEggs=1
 activate(player,"A");activate(player,"C");activate(player,"D")
 check(not order(pet),"carrying gates all commands")
 s.rules.castles[tostring(player.UserId)].heldEggs=0;advanceTo(now+.42)
 check(energy(s)==100,"no hidden charges on failed orders")
 return "registered pet, neutral allegiance, cover, and carrying are all checked before debit"
end

function growthCases.beast_orders_late_wall()
 local s=readyOrder(true)
 local center,mob=prep(s)
 local pet,h=summon(s,center+Vector3.new(-.3,1.55,0))
 position(mob,center+Vector3.new(5.2,2.15,0))
 activate(player,"A")
 check(order(pet),"actual order preexists interference")
 local barrier=wall(s,center+Vector3.new(1.6,2.1,0))
 advanceTo(now+.40)
 check(not order(pet),"late wall removes the order and its cue")
 check(h._nativeMoveGoal.X<=center.X+1.4,"the retained AI move goal cannot cross the cover")
 barrier:Destroy()
 advanceTo(now+.38)
 check(not order(pet),"old order never revives after cover opens")
 return "late wall cancels the live movement order without crossing or retaining the cue"
end

function growthCases.beast_orders_live_off()
 local s=readyOrder(true)
 local center=prep(s)
 local pet=summon(s,center+Vector3.new(-2.5,1.55,0))
 activate(player,"D")
 local stale=deck().D
 check(order(pet) and stale,"genuine current command")
 workspace:SetAttribute(FLAG,false);drainDeferred()
 oldDeck(deck())
 check(not order(pet) and not stale.Parent and witness(s)==pet,"runtime OFF retires order and old tools while existing pet lives")
 stale.Activated:Fire()
 check(not order(pet),"stale tool activation cannot restore old command")
 return "runtime OFF restores standard Tools without destroying or resummoning its still-live companion"
end

function growthCases.beast_orders_same_avatar()
 local s=readyOrder(true)
 local center=prep(s)
 local pet=summon(s,center+Vector3.new(-2.5,1.55,0))
 activate(player,"D")
 check(order(pet),"current real order before replacement")
 local newAvatar=Instance.new("Model")
 local nr=Instance.new("Part");nr.Name="HumanoidRootPart";nr.CFrame=rootPart.CFrame;nr.Parent=newAvatar
 local human=Instance.new("Humanoid");human.Parent=newAvatar;newAvatar.PrimaryPart=nr
 newAvatar.Parent=workspace;player.Character=newAvatar
 advanceTo(now+.39)
 check(not pet.Parent and not witness(s),"old escort and command retire with concrete previous avatar")
 return "a replacement player avatar cannot inherit the active old companion command"
end

function growthCases.beast_orders_switch()
 local stand=scenes:FindFirstChild("ROLE_BEAST")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"指令笛を装備")
 check(player:GetAttribute(LABEL)~=nil,"new prompt admitted")
 trigger(player,stand,"装備する")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute("EGGRUMBLE_LobbyBeastLoadoutName")=="雷角竜","old thunder selection replaces new orders")
 advanceTo(now+.51)
 trigger(player,stand,"指令笛を装備")
 workspace:SetAttribute(THUNDER,false);drainDeferred()
 check(player:GetAttribute(LABEL)~=nil,"independent old kill switch preserves real new choice")
 advanceTo(now+.51)
 trigger(player,stand,"指令笛を装備")
 check(player:GetAttribute(LABEL)==nil,"same new choice toggles to standard")
 readyOrder(false)
 return "the same live lobby supports switching between order, Thunder, and standard decks"
end

function growthCases.beast_orders_physical_off()
 local s=readyOrder(false)
 check(not s.beastOrderLoadouts,"physical PARENT contains no feature offer")
 local center=prep(s)
 local pet=summon(s,center+Vector3.new(-2.5,1.55,0))
 check(witness(s)==pet and not order(pet),"original B stays exactly usable on physical OFF")
 return "physical parent keeps standard BEAST and its one actual original companion"
end

function growthCases.builder_cover_offer_keys()
 local stand=scenes:FindFirstChild("ROLE_BUILDER")
 local offer=nil
 for _,prompt in ipairs(stand:GetChildren()) do
  if prompt:IsA("ProximityPrompt") and prompt.ActionText=="遮蔽を装備" then offer=prompt;break end
 end
 check(offer and offer.Enabled and offer.KeyboardKeyCode==Enum.KeyCode.G and offer.GamepadKeyCode==Enum.KeyCode.ButtonX,
  "mounted Builder has its original offered G/X selection")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"遮蔽を装備")
 check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="盾機","actual independent Builder offer reaches selection")
 return "Builder G/X offer remains physically registered and reaches the real deck selector"
end
end
