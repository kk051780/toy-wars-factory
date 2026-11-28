do
local FLAG="P0D_ENABLE_PRIVATE_NINJA_COMBO_009"
local OLD="P0D_ENABLE_PRIVATE_NINJA_COMBO_008"
local LABEL="EGGRUMBLE_LobbyNinjaFlightLoadoutName"
local OLD_LABEL="EGGRUMBLE_LobbyNinjaLoadoutName"
local function slot(key)
 for _,folder in ipairs({player:FindFirstChildOfClass("Backpack"),player.Character}) do
  for _,tool in ipairs(folder:GetChildren()) do
   local id=tool:IsA("Tool") and tool:GetAttribute("EGGRUMBLE_InternalToolId")
   if type(id)=="string" and id:match("^EGGRUMBLE_SKILL_"..key.."_") then return tool end
  end
 end
 return nil
end
local function closedDeck()
 check(slot("A").Name=="技A・瞬影斬" and slot("B").Name=="技B・風走り"
  and slot("C").Name=="技C・千刃旋風" and not slot("D"),"exact non-opt-in A/B/C and no D")
end
local function start(selected)
 local stand=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,stand,"職業選択")
 if selected then
  check(workspace:GetAttribute(FLAG)==nil,"new optional kit available at default nil flag")
  trigger(player,stand,"宵翼を装備")
  check(player:GetAttribute(LABEL)=="走影・宵翼飛行・宵翼囮行","actual default-enabled but opt-in lobby")
 end
 local live=ready("PRIVATE_NINJA_009","NINJA")
 check(live.isCurrentHuman(player) and live.rules.phase=="ACTIVE","actual active Host")
 if selected then
  check(live.ninjaFlightLoadouts[player.UserId] and not live.ninjaLoadouts[player.UserId],
   "one server-frozen alternative deck")
  check(slot("A").Name=="技A・瞬影斬","actual untouched original A")
  for k,id in pairs({B="NINJA-025",C="NINJA-060",D="COMBO-009"}) do
   check(slot(k):GetAttribute("EGGRUMBLE_FixedAbilityId")==id,"actual server-owned fixed Tool "..id)
  end
 else
  closedDeck()
 end
 return live
end
local function pose(s)
 local mob=spawnCurrentNeutral(s)
 local h=mob:FindFirstChildOfClass("Humanoid")
 h.Health=96
 local floor=s.world:FindFirstChild("TacticalBattlefield")
 local at=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(at,at+Vector3.new(1,0,0))
 rootPart.AssemblyLinearVelocity=Vector3.zero
 rootPart.AssemblyAngularVelocity=Vector3.zero
 secondRoot.CFrame=CFrame.new(at+Vector3.new(-45,0,0))
 humanoid.FloorMaterial=Enum.Material.Grass
 humanoid.Sit=false;humanoid.PlatformStand=false;humanoid.MoveDirection=Vector3.zero
 local head=character:FindFirstChild("Head")
 if not head then head=Instance.new("Part");head.Name="Head";head.Parent=character end
 if head:IsA("Part") then head.Shape=Enum.PartType.Block end
 head.CFrame=CFrame.new(at+Vector3.new(0,1.3,0))
 for _,neutral in ipairs(s.world:FindFirstChild("NeutralHorde"):GetChildren()) do
  neutral:SetAttribute("EGGRUMBLE_NeutralSpeed",0)
  neutral:PivotTo(CFrame.new(at+Vector3.new(-38,0,25)))
 end
 advanceTo(now+.4)
 local g=s.swarm.getRoleGrowthSnapshot(player)
 check(g and g.role=="NINJA" and g.stage==0 and g.energy==100,"actual S0/E100")
 return at,h,mob
end
local function energy(s)return s.swarm.getRoleGrowthSnapshot(player).energy end
local function cue(s,name)return s.world:FindFirstChild(name) end
local function ghost(s)return cue(s,"EGGRUMBLE_NinjaMovingDecoy") end
local function signature()return player:GetAttribute("EGGRUMBLE_SkillCastSignature") end
local function visual(s)
 local g=ghost(s)
 check(g and g:IsA("Folder") and g:GetAttribute("FixedDecoyId")=="NINJA-025","real one bounded replicated visual folder")
 local count=0
 for _,child in ipairs(g:GetDescendants()) do
  check(child:IsA("BasePart") and child.Anchored and child.Massless and not child.CanCollide and not child.CanTouch
   and not child.CanQuery and not child.CastShadow,"only noninteractive silhouette geometry, no Humanoid/Tool/tag")
  count+=1
 end
 check(count>=5 and count<=15,"bounded copied silhouette and foot fragments")
 check(g:FindFirstChild("Mirror_Head"),"retained recognizable actual avatar geometry")
 return g,g:FindFirstChild("Mirror_Head")
end
local function wall(s,point,size)
 local part=Instance.new("Part")
 part.Name="NinjaNativeSolid";part.Anchored=true;part.CanCollide=true;part.CanQuery=true
 part.Size=size;part.CFrame=CFrame.new(point);part.Parent=s.world
 return part
end
function growthCases.n09_run_shadow()
 local s=start(true)
 local at,h=pose(s)
 local t=now
 activate(player,"B")
 local g,head=visual(s)
 local origin=head.Position
 check(energy(s)==65 and signature():match("^NINJA:B:"),"E35 once on real B")
 local stamp=signature()
 activate(player,"B")
 check(ghost(s)==g and energy(s)==65 and signature()==stamp,"no reissue and just one live decoy")
 advanceTo(t+.56)
 check(head.Position.X-origin.X>1.9 and math.abs(head.Position.Z-origin.Z)<.001,"straight actual visual movement")
 local px=head.Position.X
 advanceTo(t+.97)
 check(head.Position.X>=origin.X+3.85 and head.Position.X<=origin.X+4.01 and head.Position.X>px,"S0 endpoint 4 bounded")
 check((rootPart.Position-at).Magnitude<.01 and h.Health==96 and s.swarm.getTotal()==0
  and player:GetAttribute("EGGRUMBLE_StealthUntil")==nil,"illusion does not move actor/affect HP/KO/PvP/stealth")
 advanceTo(t+1.01)
 check(not ghost(s),"exact short expiry")
 return "real B moves one noninteractive mirror up to four studs in one second; no player or neutral mutation"
end
function growthCases.n09_shadow_wall()
 local s=start(true)
 local at=pose(s)
 local t=now
 activate(player,"B")
 local _,head=visual(s)
 local x=head.Position.X
 advanceTo(t+.22)
 local barrier=wall(s,at+Vector3.new(3.1,0,0),Vector3.new(.6,10,9))
 advanceTo(t+.54)
 local stop=head.Position.X-x
 check(stop>.55 and stop<1.95,"actual continuous sweep stops at new solid wall")
 barrier:Destroy()
 advanceTo(t+.93)
 check(math.abs(head.Position.X-x-stop)<.01,"wall terminates this illusion path")
 advanceTo(t+1.01)
 check(not ghost(s),"wall-stopped illusion still expires")
 return "one straight illusion stops at a late solid wall and cannot resume"
end
function growthCases.n09_flight()
 local s=start(true)
 local at,h=pose(s)
 local t=now
 activate(player,"C")
 check(signature():match("^NINJA:C:") and energy(s)==55 and rootPart.Anchored
  and cue(s,"EGGRUMBLE_NinjaWingLeft") and not ghost(s),"real E45 grounded flight starts with restrained wings only")
 advanceTo(t+.4)
 check(rootPart.Position.Y-at.Y>=3.75 and rootPart.Position.Y-at.Y<=4.02,"actual fixed S0 four-stud apex")
 advanceTo(t+.91)
 check(not rootPart.Anchored and (rootPart.Position-at).Magnitude>4.6 and math.abs(rootPart.Position.Y-at.Y)<.07
  and not ghost(s) and not cue(s,"EGGRUMBLE_NinjaWingLeft") and h.Health==96,"flight lands safely without adding attack or stealth")
 return "real C uses the bounded flight motor and lands at S0/E45 without a hit or decoy"
end
function growthCases.n09_combo()
 local s=start(true)
 local at,h=pose(s)
 local t=now
 activate(player,"D")
 local stamp=signature()
 check(stamp:match("^NINJA:D:") and energy(s)==20 and rootPart.Anchored and not ghost(s),"real D pays E80 once and begins flight")
 advanceTo(t+.79)
 check(not ghost(s) and rootPart.Anchored,"no fake before actual flight and land")
 advanceTo(t+.92)
 local g=visual(s)
 check(not rootPart.Anchored and math.abs(rootPart.Position.Y-at.Y)<.07 and h.Health==96,"actual clean land produces only next receipt")
 local e=energy(s)
 activate(player,"B");activate(player,"C");activate(player,"D")
 check(signature()==stamp and energy(s)==e and ghost(s)==g,"same-kit deadlines reject components and duplicate")
 advanceTo(t+1.9)
 check(not ghost(s) and h.Health==96 and player:GetAttribute("EGGRUMBLE_StealthUntil")==nil,"once-only fake expires; no damage")
 return "real D E80 once, verified flight/landing, one moving decoy with inherited B/C/D clocks"
end
function growthCases.n09_denied()
 local s=start(true)
 local at=pose(s)
 local blocker=wall(s,at+Vector3.new(3,3,0),Vector3.new(7,1,8))
 activate(player,"C")
 activate(player,"D")
 check(not rootPart.Anchored and energy(s)==100 and not ghost(s),"low roof rejects both flight casts before spend")
 blocker:Destroy()
 s.rules.castles[tostring(player.UserId)].heldEggs=1
 activate(player,"B");activate(player,"C");activate(player,"D")
 check(s.swarm.getRoleGrowthSnapshot(player)==nil,"carrying is outside the shared role eligibility")
 s.rules.castles[tostring(player.UserId)].heldEggs=0
 advanceTo(now+.42)
 check(not rootPart.Anchored and energy(s)==100 and not ghost(s),"egg holder cannot cast this deck")
 return "blocked geometry and egg authority reject the real Tools without charging"
end
local function interrupted(kind)
 local s=start(true)
 pose(s)
 local t=now
 activate(player,"D")
 check(rootPart.Anchored,"issued genuine flight before interrupt")
 advanceTo(t+.25)
 if kind=="carry" then
  s.rules.castles[tostring(player.UserId)].heldEggs=1
 elseif kind=="avatar" then
  local stale=player.Character
  local nextAvatar=Instance.new("Model")
  local nr=Instance.new("Part");nr.Name="HumanoidRootPart";nr.CFrame=rootPart.CFrame;nr.Parent=nextAvatar
  local nh=Instance.new("Humanoid");nh.Parent=nextAvatar
  nextAvatar.PrimaryPart=nr;nextAvatar.Parent=workspace
  player.Character=nextAvatar
  check(stale~=player.Character,"actual fixture avatar changes")
 elseif kind=="round" then
  s.rules.phase="FINISHED"
  s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED")
 elseif kind=="off" then
  local stale=slot("D")
  workspace:SetAttribute(FLAG,false);drainDeferred()
  closedDeck()
  stale.Activated:Fire()
 end
 advanceTo(t+.97)
 check(not rootPart.Anchored and not ghost(s) and not cue(s,"EGGRUMBLE_NinjaWingLeft"),
  "interrupted real flight retires owned effect and cannot emit decoy: "..kind)
 return "old cast cannot mint a visual after "..kind
end
for _,kind in ipairs({"carry","avatar","round","off"}) do
 growthCases["n09_interrupted_"..kind]=function()return interrupted(kind)end
end
function growthCases.n09_switch_kit()
 local stand=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"宵翼を装備")
 check(player:GetAttribute(LABEL)~=nil and player:GetAttribute(OLD_LABEL)==nil,"new lobby deck owns current selection")
 trigger(player,stand,"装備する")
 check(player:GetAttribute(LABEL)==nil and player:GetAttribute(OLD_LABEL)=="瞬歩・煙玉・霞瞬歩","old F can replace G cleanly")
 advanceTo(now+.51)
 trigger(player,stand,"宵翼を装備")
 check(player:GetAttribute(LABEL)~=nil and player:GetAttribute(OLD_LABEL)==nil,"G can replace F independently")
 workspace:SetAttribute(OLD,false);drainDeferred()
 check(player:GetAttribute(LABEL)~=nil,"old feature toggle does not clear new selection")
 advanceTo(now+.51)
 trigger(player,stand,"宵翼を装備")
 check(player:GetAttribute(LABEL)==nil,"G toggle returns to default lobby path")
 start(false)
 return "new G, old F, standard and independent toggles stay reversible in actual Host"
end
function growthCases.n09_prompt_guard()
 local stand=scenes:FindFirstChild("ROLE_NINJA")
 trigger(player,stand,"宵翼を装備")
 check(not player:GetAttribute(LABEL),"unselected role cannot equip")
 trigger(player,stand,"職業選択")
 advanceTo(now+.51)
 local prompt=nil
 for _,child in ipairs(stand:GetChildren()) do
  if child:IsA("ProximityPrompt") and child.ActionText=="宵翼を装備" then prompt=child;break end
 end
 check(prompt and prompt.Enabled,"actual default flag leaves the opt-in available")
 rootPart.CFrame=CFrame.new(stand.Position+Vector3.new(18,0,0))
 prompt.Triggered:Fire(player)
 check(not player:GetAttribute(LABEL),"registered server prompt rejects distance even if triggered")
 trigger(player,stand,"宵翼を装備")
 local selected=player:GetAttribute(LABEL)
 check(selected,"current correct role and distance admitted")
 trigger(player,stand,"宵翼を装備")
 check(player:GetAttribute(LABEL)==selected,"exact per-prompt cooldown rejects duplicate")
 return "the real new prompt enforces role choice, distance, and the shared guard cooldown"
end
function growthCases.n09_shadow_retired()
 local s=start(true)
 pose(s)
 activate(player,"B")
 local old=visual(s)
 advanceTo(now+.2)
 s.rules.castles[tostring(player.UserId)].heldEggs=1
 advanceTo(now+.07)
 check(not old.Parent and not ghost(s) and not rootPart.Anchored,"owned moving visual retires immediately on carry")
 return "a live noninteractive visual cannot outlive its same-session caster eligibility"
end
function growthCases.n09_physical_off()
 local s=start(false)
 check(not s.ninjaFlightLoadouts,"physical parent has no alternative path")
 pose(s)
 activate(player,"B")
 check(signature():match("^NINJA:B:") and energy(s)==100 and player:GetAttribute("EGGRUMBLE_StealthUntil")>now
  and not ghost(s),"physical parent uses exact legacy B")
 return "physical 69 source parent honors old standard motion and stealth, with no 009 state"
end
end
