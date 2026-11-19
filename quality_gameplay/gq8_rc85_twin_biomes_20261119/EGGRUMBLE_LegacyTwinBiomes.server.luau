--!strict
-- RC85/RC86 unique TWIN_BIOMES_4NPC, TWIN_CREATURE_TRAINING and TWIN_BOND
-- REAL68: ONE existing V3 WCS realm world, 4 species mirrored on both banks.
-- No Game/HP/Score/Store/Remote/egg/round controller or purchase writer.
local Workspace=game:GetService("Workspace")
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local HttpService=game:GetService("HttpService")
if not RunService:IsStudio() then return end
local FEATURE="GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119"
local LOBBY="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local SPECIES={
 {id="AWARIN",name="アワリン",rarity="COMMON",kind="REEF",
  x=-9,z=-24,color=Color3.fromRGB(93,210,226),effect="TIDE_VEIL"},
 {id="SANGORU",name="サンゴル",rarity="RARE",kind="REEF",
  x=9,z=-24,color=Color3.fromRGB(248,121,119),effect="ROUTE_LANTERN"},
 {id="RAIKO",name="ライコ",rarity="EPIC",kind="STORM",
  x=-9,z=24,color=Color3.fromRGB(248,211,101),effect="THUNDER_SIGNAL"},
 {id="KUMONON",name="クモノン",rarity="LEGENDARY",kind="STORM",
  x=9,z=24,color=Color3.fromRGB(213,195,250),effect="CLOUD_COMPASS"},
}
local installed:{[Instance]:boolean}={}
local lobbyBound:{[Instance]:boolean}={}
local function primitive(folder:Instance,name:string,cf:CFrame,size:Vector3,color:Color3,
 material:Enum.Material,solid:boolean):Part
 local p=Instance.new("Part")
 p.Name=name;p.CFrame=cf;p.Size=size;p.Anchored=true
 p.CanCollide=solid;p.CanTouch=false;p.CanQuery=solid
 p.Material=material;p.Color=color;p.Parent=folder
 return p
end
local function textLabel(part:BasePart,line:string):TextLabel
 local gui=Instance.new("BillboardGui")
 gui.Name="CreatureReadout";gui.Size=UDim2.fromOffset(155,48)
 gui.StudsOffsetWorldSpace=Vector3.new(0,3.8,0)
 gui.MaxDistance=55;gui.AlwaysOnTop=false;gui.Parent=part
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1)
 label.BackgroundColor3=Color3.fromRGB(17,34,52)
 label.BackgroundTransparency=.28;label.Text=line
 label.Font=Enum.Font.GothamBold;label.TextColor3=Color3.fromRGB(245,246,255)
 label.TextScaled=true;label.Parent=gui
 return label
end
local function watchArena(arena:Instance,mode:string,lobby:Instance)
 if installed[arena] or arena.Parent~=lobby then return end
 local wcs=arena:FindFirstChild("GQ8_RC85_WCS_Canyon")
 local west=wcs and wcs:FindFirstChild("WestBank")
 local east=wcs and wcs:FindFirstChild("EastBank")
 local safe=wcs and wcs:FindFirstChild("AlwaysOpenSafeRoute")
 if not wcs or not west or not east or not safe or not west:IsA("BasePart")
  or not east:IsA("BasePart") or not safe:IsA("BasePart")
  or not west.Anchored or not west.CanCollide or not east.Anchored
  or not east.CanCollide or not safe.CanCollide then return end
 if arena:FindFirstChild("GQ8_RC85_TwinBiomes") then return end
 installed[arena]=true
 local token=HttpService:GenerateGUID(false)
 arena:SetAttribute("EGGRUMBLE_TwinBondSession",token)
 local world=Instance.new("Model")
 world.Name="GQ8_RC85_TwinBiomes"
 world:SetAttribute("FeatureId",FEATURE)
 world:SetAttribute("PreviousWCS","WCS_F01_C01")
 world:SetAttribute("Species",4);world:SetAttribute("Models",8)
 world:SetAttribute("Biomes",2)
 world:SetAttribute("TrainingCapXP",7)
 world:SetAttribute("TrainingCooldownSeconds",20)
 world:SetAttribute("BondLifetimeSeconds",180)
 world:SetAttribute("BondSwitchCooldownSeconds",20)
 world:SetAttribute("BondMaxPveBonus",1.2)
 world:SetAttribute("SessionOnly",true)
 world:SetAttribute("NoDamageScoreStoreRemote",true)
 world.Parent=arena
 local progress:{[Player]:{[string]:any}}={}
 local bond:{[Player]:any}={}
 local buddies:{[Player]:Part}={}
 local function validPlayer(p:Player):(BasePart?,Humanoid?)
  if p.Parent~=Players or arena.Parent~=lobby or world.Parent~=arena
   or p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode
   or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return nil,nil end
  local char=p.Character
  if not char then return nil,nil end
  local hum=char:FindFirstChildOfClass("Humanoid")
  local root=char:FindFirstChild("HumanoidRootPart")
  if not hum or hum.Health<=0 or not root or not root:IsA("BasePart")
   or hum.Sit or root.Anchored then return nil,nil end
  return root,hum
 end
 local function clearBond(p:Player)
  local old=buddies[p]
  if old then if old.Parent then old:Destroy() end;buddies[p]=nil end
  bond[p]=nil
  if p.Parent==Players and p:GetAttribute("EGGRUMBLE_TwinBondSession")==token then
   for _,name in ipairs({"EGGRUMBLE_TwinBondSession","EGGRUMBLE_TwinBondSpecies",
    "EGGRUMBLE_TwinBondLevel","EGGRUMBLE_TwinBondExpires",
    "EGGRUMBLE_TwinBondServerGranted"}) do p:SetAttribute(name,nil) end
  end
 end
 local function activateBond(p:Player,info:any,level:number)
  if level<2 then return end
  local now=os.clock()
  local old=bond[p]
  if old and old.expires>now and old.species~=info.id and now<old.switchAt then return end
  local same=old and old.expires>now and old.species==info.id
  if old and old.species~=info.id then clearBond(p) end
  local lease={
   species=info.id,level=level,
   expires=if same then old.expires else now+180,
   switchAt=if same then old.switchAt else now+20,
   character=p.Character}
  bond[p]=lease
  p:SetAttribute("EGGRUMBLE_TwinBondServerGranted",true)
  p:SetAttribute("EGGRUMBLE_TwinBondSession",token)
  p:SetAttribute("EGGRUMBLE_TwinBondSpecies",info.id)
  p:SetAttribute("EGGRUMBLE_TwinBondLevel",level)
  p:SetAttribute("EGGRUMBLE_TwinBondExpires",lease.expires)
  if not buddies[p] or not buddies[p].Parent then
   local orb=primitive(world,"GQ8_TwinBondCompanion_"..info.id,
     CFrame.new(0,20000,0),Vector3.new(1.7,1.7,1.7),
     info.color,Enum.Material.Neon,false)
   orb.Shape=Enum.PartType.Ball
   orb.CanQuery=false
   orb:SetAttribute("NoDamageAuthority",true)
   orb:SetAttribute("BoundUserId",p.UserId)
   buddies[p]=orb
  end
 end
 local function sign(x:number,z:number,name:string,description:string,col:Color3,base:CFrame):Part
  local pole=primitive(world,name.."_sign",base*CFrame.new(x,3,z),
    Vector3.new(.9,5,.9),col,Enum.Material.Wood,true)
  local plaque=primitive(world,name.."_plaque",base*CFrame.new(x,5,z),
    Vector3.new(8,3,.4),col,Enum.Material.SmoothPlastic,false)
  plaque.CanQuery=false
  textLabel(plaque,description)
  return pole
 end
 local function buildOnBank(side:string,bank:BasePart)
  local anchor=bank.CFrame*CFrame.new(0,bank.Size.Y/2,0)
  local reefColor=Color3.fromRGB(69,151,179)
  local thunderColor=Color3.fromRGB(139,132,194)
  local beach=primitive(world,side.."_CoralReefGarden",anchor*CFrame.new(0,.32,-24),
   Vector3.new(44,.6,33),reefColor,Enum.Material.Slate,true)
  local storm=primitive(world,side.."_ThunderCloudLookout",anchor*CFrame.new(0,.32,24),
   Vector3.new(44,.6,33),thunderColor,Enum.Material.Slate,true)
  beach:SetAttribute("Biome","CORAL")
  storm:SetAttribute("Biome","STORM")
  sign(0,-37,side.."_CoralSign","珊瑚の庭園",reefColor,anchor)
  sign(0,37,side.."_StormSign","雷雲の展望台",thunderColor,anchor)
  for i=1,7 do
   local xx=-21+i*5
   local reef=primitive(world,side.."_CoralBranch_"..i,anchor*CFrame.new(xx,2,-33),
    Vector3.new(1.2,if i%2==0 then 2.5 else 3.6,1.2),
    Color3.fromRGB(252,118+i*4,131),Enum.Material.Neon,false)
   reef.Shape=Enum.PartType.Cylinder;reef.CanQuery=false
   local bolt=primitive(world,side.."_StormRod_"..i,anchor*CFrame.new(xx,3.5,34),
    Vector3.new(.3,5,.3),Color3.fromRGB(242,218,122),Enum.Material.Metal,false)
   bolt.CanQuery=false
  end
  for _,sp in ipairs(SPECIES) do
   local model=Instance.new("Model");model.Name="Twin_"..side.."_"..sp.id
   model:SetAttribute("Species",sp.id)
   model:SetAttribute("Biomes",sp.kind)
   model:SetAttribute("TrainingLevelMax",3)
   model:SetAttribute("NoHordeHPScoreWriter",true)
   model.Parent=world
   local base=anchor*CFrame.new(sp.x,3,sp.z)
   local body=primitive(model,sp.id.."_Body",base,Vector3.new(3.4,3.2,2.6),
    sp.color,Enum.Material.SmoothPlastic,false)
   body.Shape=if sp.id=="SANGORU" then Enum.PartType.Block else Enum.PartType.Ball
   body.CanQuery=true
   body:SetAttribute("CosmeticOnly",true)
   model.PrimaryPart=body
   local eyeColor=Color3.fromRGB(21,38,61)
   for _,x in ipairs({-0.73,0.73}) do
    local eye=primitive(model,sp.id.."_Eye",base*CFrame.new(x,.35,-1.35),
     Vector3.new(.43,.54,.26),eyeColor,Enum.Material.SmoothPlastic,false)
    eye.Shape=Enum.PartType.Ball;eye.CanQuery=false
   end
   if sp.id=="SANGORU" or sp.id=="RAIKO" then
    for _,x in ipairs({-1.1,1.1}) do
     local crest=primitive(model,sp.id.."_Crest",base*CFrame.new(x,2.1,0),
      Vector3.new(.46,2.2,.5),sp.color,Enum.Material.Neon,false)
     crest.CanQuery=false
    end
   end
   if sp.id=="KUMONON" then
    local cloud=primitive(model,sp.id.."_Cloud",base*CFrame.new(0,1.6,0),
     Vector3.new(3.5,.8,3),Color3.fromRGB(241,226,255),Enum.Material.Neon,false)
    cloud.Shape=Enum.PartType.Ball;cloud.CanQuery=false
   end
   local label=textLabel(body,sp.name.."\n"..sp.rarity)
   local prompt=Instance.new("ProximityPrompt")
   prompt.Name="GQ8_RC85_TwinPractice_"..sp.id
   prompt.ActionText="交流・修行";prompt.ObjectText=sp.name
   prompt.HoldDuration=.5;prompt.MaxActivationDistance=10
   prompt.RequiresLineOfSight=true;prompt.Parent=body
   prompt.Triggered:Connect(function(p:Player)
    local root=validPlayer(p)
    if not root or (root.Position-body.Position).Magnitude>12 then return end
    local rayParams=RaycastParams.new()
    rayParams.FilterType=Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances={p.Character,model}
    rayParams.RespectCanCollide=true
    local from=root.Position+Vector3.new(0,1.3,0)
    local hit=Workspace:Raycast(from,body.Position-from,rayParams)
    if hit and hit.Instance.CanCollide then return end
    local bySpecies=progress[p]
    if not bySpecies then bySpecies={};progress[p]=bySpecies end
    local state=bySpecies[sp.id]
    if not state then state={xp=0,nextAt=0,level=1};bySpecies[sp.id]=state end
    local now=os.clock()
    if now>=state.nextAt and state.xp<7 then
     state.xp+=1
     state.nextAt=now+20
     state.level=if state.xp>=7 then 3 elseif state.xp>=3 then 2 else 1
     p:SetAttribute("EGGRUMBLE_TwinPractice_"..sp.id,state.xp)
     p:SetAttribute("EGGRUMBLE_TwinLevel_"..sp.id,state.level)
     label.Text=sp.name.."\nLv"..state.level
     if state.level>=3 then
      model:SetAttribute("EvolutionStage",3)
      body.Material=Enum.Material.Neon
     end
    end
    -- Studio original species have level2+ companion choice with a 180s lease.
    activateBond(p,sp,state.level)
   end)
  end
 end
 buildOnBank("WEST",west)
 buildOnBank("EAST",east)
 local acc=0
 local hb:RBXScriptConnection?
 hb=RunService.Heartbeat:Connect(function(dt:number)
  if world.Parent~=arena or arena.Parent~=lobby then
   if hb then hb:Disconnect() end
   for p in pairs(bond) do clearBond(p) end
   return
  end
  acc+=dt
  if acc<.2 then return end
  acc=0
  for p,lease in pairs(bond) do
   local root=validPlayer(p)
   if not root or p.Character~=lease.character
    or os.clock()>=lease.expires then
    clearBond(p)
   else
    local orb=buddies[p]
    if orb and orb.Parent then
     orb.Position=root.Position+root.CFrame.RightVector*2.9+Vector3.new(0,2,0)
    end
   end
  end
 end)
 local leaving=Players.PlayerRemoving:Connect(function(p:Player)
  progress[p]=nil;clearBond(p)
 end)
 arena.Destroying:Connect(function()
  if hb then hb:Disconnect() end
  leaving:Disconnect()
  for p in pairs(bond) do clearBond(p) end
  for p,record in pairs(progress) do
   if p.Parent==Players then
    for id in pairs(record) do
     p:SetAttribute("EGGRUMBLE_TwinPractice_"..id,nil)
     p:SetAttribute("EGGRUMBLE_TwinLevel_"..id,nil)
    end
   end
   progress[p]=nil
  end
  if arena:GetAttribute("EGGRUMBLE_TwinBondSession")==token then
   arena:SetAttribute("EGGRUMBLE_TwinBondSession",nil)
  end
  installed[arena]=nil
 end)
end
local function bindLobby(lobby:Instance)
 if lobbyBound[lobby] or lobby.Parent~=Workspace or lobby.Name~=LOBBY then return end
 lobbyBound[lobby]=true
 local function observe(arena:Instance)
  local mode=if arena.Name=="TEAM_Arena" then "TEAM"
   elseif arena.Name=="BATTLE_ROYALE_Arena" then "BATTLE_ROYALE" else nil
  if not mode then return end
  task.spawn(function()
   while arena.Parent==lobby and (arena:FindFirstChild("GQ8_RC85_WCS_Canyon")==nil
    or not arena:FindFirstChild("TacticalBattlefield")) do task.wait(.3) end
   if arena.Parent==lobby then watchArena(arena,mode,lobby) end
  end)
 end
 for _,child in ipairs(lobby:GetChildren()) do observe(child) end
 lobby.ChildAdded:Connect(observe)
 lobby.Destroying:Connect(function()lobbyBound[lobby]=nil end)
end
for _,child in ipairs(Workspace:GetChildren()) do
 if child.Name==LOBBY then bindLobby(child) end
end
Workspace.ChildAdded:Connect(function(child:Instance)
 if child.Name==LOBBY then bindLobby(child) end
end)
