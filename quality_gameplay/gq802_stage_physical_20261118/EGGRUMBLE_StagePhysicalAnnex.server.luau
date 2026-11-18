--!strict
-- GQ802 physical tile annex: opt-in Studio-only, no canonical field replacement.
-- Consumes original #803 immutable stage manifest; never owns weather, gravity,
-- Player/Match/Combat/Swarm/Castle/Egg/Item/Remote, Game or Teleport.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Workspace=game:GetService("Workspace")
local Players=game:GetService("Players")
local StageManifest=require(script.Parent:WaitForChild("EGGRUMBLE_StageManifestPolicy"))
local PhysicalPlan=require(script.Parent:WaitForChild("EGGRUMBLE_StagePhysicalPlan"))
local LOBBY_NAME="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local SCENE_NAME="EGGRUMBLE_STAGE_PHYSICAL_ANNEX"
local occupied={}
local watching={}
local surfaces={
 COSMOS=Color3.fromRGB(107,98,187),
 HEAVEN=Color3.fromRGB(188,221,242),
 UNDERWORLD=Color3.fromRGB(197,95,61),
 TIME=Color3.fromRGB(192,166,89),
 SEA=Color3.fromRGB(66,153,188),
 DREAM=Color3.fromRGB(215,133,197),
 SKY=Color3.fromRGB(123,183,212),
 ICE=Color3.fromRGB(123,213,234),
 FOREST=Color3.fromRGB(90,167,113),
 REGAL=Color3.fromRGB(164,156,214),
}
local function makePart(parent:Instance,name:string,x:number,y:number,z:number,
 sizeX:number,sizeY:number,sizeZ:number,color:Color3,collides:boolean):BasePart
 local p=Instance.new("Part")
 p.Name=name;p.Anchored=true;p.CanCollide=collides;p.CanTouch=false
 p.Size=Vector3.new(sizeX,sizeY,sizeZ)
 p.CFrame=CFrame.new(x,y,z)
 p.Color=color;p.Material=if collides then Enum.Material.Slate else Enum.Material.Neon
 p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function install(world:Instance)
 if occupied[world] or not world:IsA("Folder") then return end
 local mode=if world.Name=="TEAM_Arena" then "TEAM"
  elseif world.Name=="BATTLE_ROYALE_Arena" then "BR" else nil
 if not mode then return end
 local lobby=world.Parent
 if not lobby or lobby.Name~=LOBBY_NAME or not lobby:IsDescendantOf(Workspace) then return end
 local floor=world:FindFirstChild("TacticalBattlefield")
 if not floor or not floor:IsA("BasePart")
  or floor.Size.X<600 or floor.Size.Z<700 then return end
 if world:FindFirstChild(SCENE_NAME) then return end
 -- Server chooses exactly once per arena. No client-supplied seed or reroll.
 local seed=Random.new():NextInteger(1,2147483646)
 local count=math.clamp(#Players:GetPlayers(),2,16)
 local manifest,reason=StageManifest.build(seed,mode,count)
 if not manifest or reason or not StageManifest.validate(manifest) then return end
 local frame={x=floor.Position.X,y=floor.Position.Y+floor.Size.Y/2,
  z=floor.Position.Z,halfX=floor.Size.X/2,halfZ=floor.Size.Z/2}
 local plan,errorText=PhysicalPlan.plan(manifest,frame)
 if not plan or errorText then return end
 if #plan.tiles~=6 or #plan.bridges~=8 or plan.maxParts>48 then return end
 -- Every output cell lies strictly beyond the old east-side battlefield edge.
 -- No existing castle/egg spawn or combat flooring is replaced or moved.
 for _,tile in ipairs(plan.tiles) do
  if tile.x-tile.size/2<=frame.x+frame.halfX+24 then return end
 end
 occupied[world]=true
 local scene=Instance.new("Folder")
 scene.Name=SCENE_NAME;scene.Parent=world
 scene:SetAttribute("ServerStageSeed",manifest.seed)
 scene:SetAttribute("StagePolicyVersion",manifest.version)
 scene:SetAttribute("ExpectedWeatherPhase2",manifest.weather[2].id)
 scene:SetAttribute("ExpectedWeatherPhase3",manifest.weather[3].id)
 scene:SetAttribute("WeatherIsOwnedByRealm",true)
 scene:SetAttribute("PhysicalPadCount",6)
 local partCount=0
 local function add(name:string,x:number,y:number,z:number,sx:number,sy:number,sz:number,
  color:Color3,collidable:boolean):BasePart
  partCount+=1
  assert(partCount<=plan.maxParts,"GQ802_STAGE_PART_BUDGET_RED")
  return makePart(scene,name,x,y,z,sx,sy,sz,color,collidable)
 end
 for _,tile in ipairs(plan.tiles) do
  local tone=surfaces[tile.theme] or Color3.fromRGB(125,150,180)
  local pad=add("Tile_"..tile.slot.."_"..tile.prefabId,
   tile.x,tile.y,tile.z,tile.size,2,tile.size,tone,true)
  pad:SetAttribute("PrefabId",tile.prefabId)
  pad:SetAttribute("SafeGroundRoute",tile.safeExit)
  pad:SetAttribute("ItemHintOnly",tile.itemHint)
  pad:SetAttribute("NoActualLootAuthority",true)
  -- Three non-collidable silhouettes per tile keep the walking surface clear.
  -- Art will replace these with approved geometry; never claim finished art.
  for i=1,3 do
   local height=8+((#tile.prefabId+i*7)%12)
   add("FantasySilhouette_"..tile.slot.."_"..tostring(i),
    tile.x+(i-2)*24,tile.y+1+height/2,tile.z+(i%2==0 and 35 or -35),
    7,height,7,tone,false)
  end
  local billboard=Instance.new("BillboardGui")
  billboard.Name="StageReadableLabel"
  billboard.Size=UDim2.fromOffset(200,42)
  billboard.StudsOffsetWorldSpace=Vector3.new(0,11,0)
  billboard.AlwaysOnTop=false;billboard.MaxDistance=135
  billboard.Parent=pad
  local caption=Instance.new("TextLabel")
  caption.BackgroundTransparency=0.28
  caption.TextColor3=Color3.fromRGB(255,255,255)
  caption.BackgroundColor3=Color3.fromRGB(21,30,47)
  caption.TextScaled=true
  caption.Font=Enum.Font.GothamBold
  caption.Size=UDim2.fromScale(1,1)
  caption.Text=tile.slot.." / "..tile.prefabId
  caption.Parent=billboard
 end
 for i,bridge in ipairs(plan.bridges) do
  add("SafeWalkway_"..bridge.kind.."_"..tostring(i),
   bridge.x,bridge.y,bridge.z,bridge.sizeX,2,bridge.sizeZ,
   Color3.fromRGB(158,175,181),true)
 end
 -- The physical annex has no new weather controller or item spawner.
 -- Destruction is owned by the existing round world, not a new loop.
 world.Destroying:Connect(function() occupied[world]=nil end)
 print("[GQ802][STUDIO_ONLY] six physical tiles, three grounded entries, source seed",
  manifest.seed,"parts",partCount)
end
local function watchWorld(world:Instance)
 if not world:IsA("Folder") or watching[world] then return end
 watching[world]=true
 local signal
 signal=world.ChildAdded:Connect(function(part)
  if part.Name=="TacticalBattlefield" then
   task.defer(function() if world.Parent then install(world) end end)
  end
 end)
 world.Destroying:Connect(function()
  if signal then signal:Disconnect() end
  watching[world]=nil
  occupied[world]=nil
 end)
 task.defer(function() if world.Parent then install(world) end end)
end
local function watchLobby(lobby:Instance)
 if lobby.Name~=LOBBY_NAME or not lobby:IsA("Folder") then return end
 for _,world in ipairs(lobby:GetChildren()) do watchWorld(world) end
 lobby.ChildAdded:Connect(watchWorld)
end
for _,child in ipairs(Workspace:GetChildren()) do
 if child.Name==LOBBY_NAME then watchLobby(child) end
end
Workspace.ChildAdded:Connect(function(child)
 if child.Name==LOBBY_NAME then watchLobby(child) end
end)
