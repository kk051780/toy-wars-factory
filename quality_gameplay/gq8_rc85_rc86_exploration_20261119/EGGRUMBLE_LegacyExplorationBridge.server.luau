--!strict
-- GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119
-- Port original RC86 four-landmark RealmHunt and six-fragment StarShardHunt
-- into the single V3 TEAM/BR match world; never start legacy Game/HP/Store/Remote.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local origin=workspace:WaitForChild("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW",40)
if not origin then warn("[GQ8 LEGACY] canonical world missing"); return end
local modes={TEAM_Arena="TEAM",BATTLE_ROYALE_Arena="BATTLE_ROYALE"}
local S={
 {"REALM_SKY","空のひみつ","REALM",-245,-310,Color3.fromRGB(123,207,245)},
 {"REALM_SEA","海のひみつ","REALM",245,-310,Color3.fromRGB(75,177,209)},
 {"REALM_EMBER","炎のひみつ","REALM",-245,310,Color3.fromRGB(231,127,102)},
 {"REALM_STAR","星のひみつ","REALM",245,310,Color3.fromRGB(172,150,239)},
 {"SHARD_1","星のかけら1","SHARD",-170,-240,Color3.fromRGB(248,221,132)},
 {"SHARD_2","星のかけら2","SHARD",170,-240,Color3.fromRGB(248,221,132)},
 {"SHARD_3","星のかけら3","SHARD",-170,-75,Color3.fromRGB(248,221,132)},
 {"SHARD_4","星のかけら4","SHARD",170,75,Color3.fromRGB(248,221,132)},
 {"SHARD_5","星のかけら5","SHARD",-170,240,Color3.fromRGB(248,221,132)},
 {"SHARD_6","星のかけら6","SHARD",170,240,Color3.fromRGB(248,221,132)},
}
local installed:{[Instance]:boolean}={}
local function makePart(name:string,size:Vector3,pos:CFrame,color:Color3,mat:Enum.Material,parent:Instance)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=pos;p.Color=color;p.Material=mat
 p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
 p.Parent=parent
 return p
end
local function install(arena:Instance,mode:string)
 if installed[arena] or arena.Parent~=origin or arena.Name~=mode.."_Arena" then return end
 local floor=arena:FindFirstChild("TacticalBattlefield")
 if not floor or not floor:IsA("BasePart") or not floor.Anchored or not floor.CanCollide
  or floor.Size.X<750 or floor.Size.Z<900 or arena:FindFirstChild("GQ8_LegacyExploration") then return end
 installed[arena]=true
 local folder=Instance.new("Folder");folder.Name="GQ8_LegacyExploration"
 folder:SetAttribute("FeatureId","GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119")
 folder:SetAttribute("SessionOnly",true);folder:SetAttribute("NoScoreDamageStoreRemote",true)
 folder:SetAttribute("Realms",4);folder:SetAttribute("Shards",6);folder.Parent=arena
 local found:{[number]:{[string]:boolean}}={}
 local count:{[number]:{realms:number,shards:number}}={}
 for _,spec in ipairs(S) do
  local id=spec[1]::string
  local kind=spec[3]::string
  local point=floor.CFrame:PointToWorldSpace(Vector3.new(spec[4]::number,floor.Size.Y/2+3.1,spec[5]::number))
  makePart(id.."_Pedestal",Vector3.new(3.8,.45,3.8),CFrame.new(point-Vector3.new(0,1.3,0)),
   Color3.fromRGB(65,78,99),Enum.Material.Slate,folder)
  local core=makePart(id.."_Artifact",Vector3.new(2.2,2.2,2.2),
   CFrame.new(point)*CFrame.Angles(math.rad(22),math.rad(45),math.rad(20)),
   spec[6]::Color3,Enum.Material.SmoothPlastic,folder)
  makePart(id.."_Relief",Vector3.new(.28,1.9,.28),
   CFrame.new(point+Vector3.new(0,.05,-1.4))*CFrame.Angles(0,0,math.rad(45)),
   Color3.fromRGB(245,237,205),Enum.Material.Metal,folder)
  local prompt=Instance.new("ProximityPrompt")
  prompt.Name="LegacyExplorePrompt";prompt.ActionText="発見する";prompt.ObjectText=spec[2]::string
  prompt.HoldDuration=.35;prompt.MaxActivationDistance=8;prompt.RequiresLineOfSight=true
  prompt.Parent=core
  prompt.Triggered:Connect(function(p:Player)
   if folder.Parent~=arena or arena.Parent~=origin
    or p.Parent~=Players or p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode
    or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
   local char=p.Character
   local hum=char and char:FindFirstChildOfClass("Humanoid")
   local root=char and char:FindFirstChild("HumanoidRootPart")
   if not hum or hum.Health<=0 or not root or not root:IsA("BasePart")
    or (root.Position-point).Magnitude>10 then return end
   -- ProximityPrompt.RequiresLineOfSight is presentation-only. Reject forged
   -- Triggered attempts through the original solid castle gate or rock walls.
   local rayStart=root.Position+Vector3.new(0,1.5,0)
   local rayDirection=point-rayStart
   if rayDirection.Magnitude>12 then return end
   local rayParams=RaycastParams.new()
   rayParams.FilterType=Enum.RaycastFilterType.Exclude
   rayParams.FilterDescendantsInstances={char,folder}
   rayParams.RespectCanCollide=true
   local occlusion=workspace:Raycast(rayStart,rayDirection,rayParams)
   if occlusion and occlusion.Instance and occlusion.Instance.CanCollide then return end
   local uid=p.UserId
   if not found[uid] then found[uid]={};count[uid]={realms=0,shards=0} end
   if found[uid][id] then return end
   found[uid][id]=true
   local status=count[uid]
   if kind=="REALM" then status.realms+=1 else status.shards+=1 end
   p:SetAttribute("EGGRUMBLE_LegacyExplore_Mode",mode)
   p:SetAttribute("EGGRUMBLE_LegacyExplore_Realms",status.realms)
   p:SetAttribute("EGGRUMBLE_LegacyExplore_Shards",status.shards)
   local completed=status.realms==4 and status.shards==6
   p:SetAttribute("EGGRUMBLE_LegacyExplore_Complete",completed)
   if completed then
    local glow=Instance.new("Highlight")
    glow.Name="EGGRUMBLE_LegacyExploreComplete"
    glow.FillTransparency=.83;glow.OutlineTransparency=.2
    glow.FillColor=Color3.fromRGB(233,205,125)
    glow.OutlineColor=Color3.fromRGB(243,230,191)
    glow.Adornee=char;glow.Parent=char
    task.delay(12,function() if glow.Parent then glow:Destroy() end end)
   end
  end)
 end
 arena.Destroying:Connect(function()
  for uid in pairs(found) do
   local player=Players:GetPlayerByUserId(uid)
   if player and player:GetAttribute("EGGRUMBLE_LegacyExplore_Mode")==mode then
    player:SetAttribute("EGGRUMBLE_LegacyExplore_Mode",nil)
    player:SetAttribute("EGGRUMBLE_LegacyExplore_Realms",nil)
    player:SetAttribute("EGGRUMBLE_LegacyExplore_Shards",nil)
    player:SetAttribute("EGGRUMBLE_LegacyExplore_Complete",nil)
   end
  end
  installed[arena]=nil;table.clear(found);table.clear(count)
 end)
end
local function tryMount(child:Instance)
 local mode=modes[child.Name]
 if not mode then return end
 task.spawn(function()
  local floor=child:WaitForChild("TacticalBattlefield",12)
  if floor then install(child,mode) end
 end)
end
for _,child in ipairs(origin:GetChildren()) do tryMount(child) end
origin.ChildAdded:Connect(tryMount)
