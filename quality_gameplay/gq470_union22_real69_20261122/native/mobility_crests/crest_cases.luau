do
local FLAG="P0D_ENABLE_PRIVATE_PLAYER_TEAM_CRESTS"
local NAME="GQ470_PlayerTeamCrests"
local ROUND="EGGRUMBLE_RelayPresentationRoundV1"
local TEAM="EGGRUMBLE_RelayPresentationTeam"
local MODE="EGGRUMBLE_QueuedMode"
local R6={"Head","Torso","Left Arm","Right Arm","Left Leg","Right Leg"}
local R15={"Head","UpperTorso","LowerTorso","LeftUpperArm","RightUpperArm","LeftLowerArm","RightLowerArm",
 "LeftHand","RightHand","LeftUpperLeg","RightUpperLeg","LeftLowerLeg","RightLowerLeg","LeftFoot","RightFoot"}

local function scene(touch,at,subject)
 for _,p in ipairs(currentPlayers) do
  local h=p.Character:FindFirstChildOfClass("Humanoid")
  if h then h._props.AncestryChanged=h._props.AncestryChanged or signal() end
 end
 local camera=Instance.new("Camera")
 camera.CFrame=CFrame.new(at+Vector3.new(0,4,-12))
 camera.CameraType=Enum.CameraType.Custom
 camera._props.CameraSubject=subject
 local fixtureBlocked,offScreen={},{}
 local projectileRay=workspace.Raycast
 workspace.Raycast=function(self,origin,delta,params)
  if #params.FilterDescendantsInstances==2 and params.RespectCanCollide~=true then
   check(origin==camera.CFrame.Position,"crest LOS starts at the actual view camera")
   check(params.FilterDescendantsInstances[1]==Players.LocalPlayer.Character,"ray excludes viewer first")
   local target=params.FilterDescendantsInstances[2]
   return if fixtureBlocked[target] then {Instance=ground} else nil
  end
  return projectileRay(self,origin,delta,params)
 end
 camera.WorldToViewportPoint=function(_,point)
  return Vector3.new(100,300,1),not offScreen[point]
 end
 workspace.CurrentCamera=camera
 workspace._props.DescendantRemoving=signal()
 Players.LocalPlayer=player
 local baseService=game.GetService
 game.GetService=function(self,kind)
  if kind=="UserInputService" then
   return {TouchEnabled=touch,WindowFocusReleased=signal(),WindowFocused=signal()}
  end
  return baseService(self,kind)
 end
 local script=Instance.new("LocalScript")
 script.Name="NativeMountedCrestLOD"
 script.Parent=playerGui
 local mounted=script
-- INSERT_PHYSICAL_ART_LOD
 return mounted,camera,fixtureBlocked,offScreen
end

local function actor(id)
 local p=Instance.new("Player")
 p.Name="CrestSeat"..id;p.UserId=id;p.Parent=Players
 Instance.new("PlayerGui").Parent=p
 Instance.new("Backpack").Parent=p
 local ch=Instance.new("Model");ch.Name="CrestRig"..id;ch.Parent=workspace
 local root=Instance.new("Part");root.Name="HumanoidRootPart";root.Parent=ch
 local h=Instance.new("Humanoid");h.Parent=ch
 p.Character=ch;ch.PrimaryPart=root
 table.insert(currentPlayers,p)
 Players.PlayerAdded:Fire(p)
 return p
end

local function rig(p,kind,at)
 local ch=p.Character
 local root=ch:FindFirstChild("HumanoidRootPart")
 root.CFrame=CFrame.new(at)
 local h=ch:FindFirstChildOfClass("Humanoid")
 h.RigType=Enum.HumanoidRigType[kind]
 for _,label in ipairs(if kind=="R6" then R6 else R15) do
  local part=Instance.new("Part")
  part.Name=label
  part.CFrame=CFrame.new(at+Vector3.new(0,if label=="Head" then 2 else 1,0))
  part._props.Transparency=0;part._props.LocalTransparencyModifier=0
  part.Parent=ch
 end
end

local function round(number)
 local peers={second}
 for i=3,number do table.insert(peers,actor(42+i-1)) end
 for _,p in ipairs(currentPlayers) do
  trigger(p,scenes:FindFirstChild("ROLE_WARRIOR"),"職業選択")
  trigger(p,scenes:FindFirstChild("TEAM_PORTAL"),"参加する")
 end
 advanceTo(now+12.1)
 local s=capturedSessions[#capturedSessions]
 check(s and s.rules.phase=="ACTIVE" and s.mode=="TEAM","actual Host READY starts TEAM")
 local field=s.world:FindFirstChild("TacticalBattlefield")
 local at=field.Position+Vector3.new(12,field.Size.Y*.5+3,11)
 rig(player,"R15",at)
 for i,p in ipairs(peers) do
  check(s.isCurrentHuman(p),"actual same-epoch Host membership")
  rig(p,if i==1 then "R6" else "R15",at+Vector3.new((i-1)*5+8,0,12))
  local relay=p.Character.PrimaryPart:FindFirstChild("EGGRUMBLE_ClassicEggRelay")
  check(relay and relay:GetAttribute(ROUND)==0 and relay:GetAttribute(TEAM)==s.rules.castles[tostring(p.UserId)].team,
   "actual Host publishes current faction and first-round epoch zero on the exact avatar")
 end
 return s,peers,at
end

local function folder(p)
 return p.Character:FindFirstChild(NAME)
end

local function tick()
 advanceTo(now+1.21)
 drainDeferred()
end

local function assertShape(p,side)
 local owned=folder(p)
 check(owned and #owned:GetChildren()==2,"two wedges on one eligible actor")
 local ch=p.Character
 local torso=ch:FindFirstChild("Torso") or ch:FindFirstChild("UpperTorso")
 local red=side=="RED"
 local size=if red then Vector3.new(.52,.20,.66) else Vector3.new(.35,.31,.63)
 local rgb=if red then Color3.fromRGB(174,79,73) else Color3.fromRGB(70,122,176)
 for _,name in ipairs({"LeftShoulderMatte","RightShoulderMatte"}) do
  local part=owned:FindFirstChild(name)
  check(part and part:IsA("WedgePart") and (part.Size-size).Magnitude<1e-7 and part.Transparency==.04,
   "source-mounted authored crest shape and material")
  check(part.Material==Enum.Material.SmoothPlastic and part.Color.R==rgb.R and part.Color.G==rgb.G and part.Color.B==rgb.B,
   "source-mounted authored faction palette")
  check(part.Massless and not part.Anchored and not part.CanCollide and not part.CanQuery and not part.CanTouch
   and not part.CastShadow,"no blocking, touch, ray or shadow geometry")
  local join=part:FindFirstChild("ClientOnlyShoulderWeld")
  check(join and join.Part0==torso and join.Part1==part,"exact own torso assembly; both R6 and R15")
 end
 return owned
end

local function budgets(touch,limit)
 local s,peers,at=round(5)
 scene(touch,at,humanoid)
 tick()
 local count=0
 local red,blue=false,false
 for i,p in ipairs(peers) do
  if i<=limit then
   local side=s.rules.castles[tostring(p.UserId)].team
   assertShape(p,side)
   count+=#folder(p):GetChildren()
   red=red or side=="RED";blue=blue or side=="BLUE"
  else
   check(not folder(p),"over-budget real human never instantiates cosmetic parts")
  end
 end
 check(count==2*limit and red and blue and not folder(player),"exact budget and both author's crests")
end

function growthCases.crest976_desktop()
 budgets(false,3)
 return "first real TEAM epoch zero; R6/R15 author RED width and BLUE height, six passive wedges maximum"
end

function growthCases.crest976_touch()
 budgets(true,2)
 return "two nearest real TEAM peers, four passive wedges maximum"
end

function growthCases.crest976_view()
 local _,peers,at=round(5)
 local _,camera,occluded,offScreen=scene(false,at,humanoid)
 occluded[peers[1].Character]=true
 local torso=peers[2].Character:FindFirstChild("UpperTorso")
 offScreen[torso.Position]=true
 local peer=peers[3]
 peer.Character.PrimaryPart.CFrame=CFrame.new(at+Vector3.new(67,0,0))
 tick()
 check(not folder(peers[1]),"wall excludes visible-range peer")
 check(not folder(peers[2]),"off-screen projection excludes peer")
 check(not folder(peer),"view or own avatar range excludes distant peer")
 check(folder(peers[4]),"one eligible same-round on-screen peer remains")
 camera.CameraSubject=secondHumanoid;drainDeferred()
 check(not folder(peers[4]),"observer subject removes existing geometry immediately")
 tick();check(not folder(peers[4]),"observer subject never reallocates")
 camera.CameraSubject=humanoid;tick();check(folder(peers[4]),"returned own live subject permits legal visible actor")
 local upper=peers[4].Character:FindFirstChild("UpperTorso")
 upper.Transparency=.51;drainDeferred();check(not folder(peers[4]),"R15 body cloak removes immediately")
 upper.Transparency=0;tick();check(folder(peers[4]),"unconcealed current R15 visible again")
 camera.CameraType=Enum.CameraType.Scriptable;drainDeferred();tick()
 check(not folder(peers[4]),"scriptable camera is excluded")
 return "nearby on-screen ray-gated targets only; observer and Scriptable cameras remove and suppress all crests"
end

function growthCases.crest976_cloak_stream()
 local _,peers,at=round(2)
 local peer=peers[1]
 scene(true,at,humanoid)
 tick();assertShape(peer,"BLUE")
 local arm=peer.Character:FindFirstChild("Left Arm")
 arm.LocalTransparencyModifier=.8;drainDeferred()
 check(not folder(peer),"R6 local cloak removes immediately")
 arm.LocalTransparencyModifier=0;tick();assertShape(peer,"BLUE")
 peer:SetAttribute("EGGRUMBLE_StealthUntil",999);drainDeferred()
 check(not folder(peer),"new authoritative stealth clock removes immediately")
 tick();check(not folder(peer),"server time is never guessed")
 peer:SetAttribute("EGGRUMBLE_StealthUntil",nil);tick();assertShape(peer,"BLUE")
 arm.Parent=nil;drainDeferred()
 check(not folder(peer),"R6 limb stream-out invalidates the old binding immediately")
 tick();check(not folder(peer),"partly streamed rig remains unmarked")
 arm.Parent=peer.Character;tick();assertShape(peer,"BLUE")
 local old=peer.Character
 peer.CharacterRemoving:Fire(old);peer.Character=Instance.new("Model")
 drainDeferred();check(not old:FindFirstChild(NAME),"old still-replicated avatar is retired")
 tick();check(not folder(peer),"new incomplete respawn cannot inherit an old marker")
 return "R6 transparency, server cloak and stream-out withdraw instantly; current avatar alone owns the decoration"
end

function growthCases.crest976_lifecycle()
 local s,peers,at=round(2)
 local peer=peers[1]
 local client=scene(false,at,humanoid)
 tick();assertShape(peer,"BLUE")
 local relay=peer.Character.PrimaryPart:FindFirstChild("EGGRUMBLE_ClassicEggRelay")
 relay:SetAttribute(ROUND,1);drainDeferred();tick()
 check(not folder(peer),"mismatched round has no color fallback")
 relay:SetAttribute(ROUND,0);tick();assertShape(peer,"BLUE")
 peer:SetAttribute(MODE,"BATTLE_ROYALE");drainDeferred()
 check(not folder(peer),"BR peer is retired immediately")
 peer:SetAttribute(MODE,"TEAM");tick();assertShape(peer,"BLUE")
 player:SetAttribute("EGGRUMBLE_ReducedEffects",true);drainDeferred();tick()
 check(not folder(peer),"accessibility cleanup and old post-poll zero allocation")
 player:SetAttribute("EGGRUMBLE_ReducedEffects",false);tick();assertShape(peer,"BLUE")
 workspace:SetAttribute(FLAG,false);drainDeferred();tick()
 check(not folder(peer),"live OFF and initial OFF share zero geometry")
 workspace:SetAttribute(FLAG,true);tick();assertShape(peer,"BLUE")
 player:SetAttribute("EGGRUMBLE_Eliminated",true);drainDeferred();tick()
 check(not folder(peer),"eliminated own avatar never retains a claim on visible peers")
 player:SetAttribute("EGGRUMBLE_Eliminated",nil);tick();assertShape(peer,"BLUE")
 s.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drainDeferred()
 check(not folder(peer),"real active arena expiry clears immediately")
 tick();check(not folder(peer),"results phase cannot allocate")
 s.world:SetAttribute("EGGRUMBLE_MatchPhase","ACTIVE");tick();assertShape(peer,"BLUE")
 client:Destroy();drainDeferred();tick()
 check(not folder(peer),"destroying while mounted clears watchers and prevents remount")
 return "round, mode, reduced effects, runtime OFF, arena phase, script disposal retire their own bindings"
end

function growthCases.crest976_physical_off()
 local _,peers,at=round(2)
 scene(true,at,humanoid)
 tick();check(not folder(peers[1]),"physical old parent retains zero crest geometry")
 check(workspace:FindFirstChild("EGGRUMBLE_FarSkyFacets_Local"),"physical old parent still renders its actual far sky")
 return "physical old ArtDistanceLOD keeps far sky and no player crests"
end
end
