--!nocheck
-- G8: independent Studio-only, never the live egg/role Game. Five real server-validated free trips.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local Workspace=game:GetService("Workspace")
local Rules=require(script.Parent:WaitForChild("G8TravelRules"))
if Workspace:FindFirstChild("G8_PRIVATE_3LEVEL_TRAVEL") then return end
local root=Instance.new("Folder")
root.Name="G8_PRIVATE_3LEVEL_TRAVEL"
root:SetAttribute("SourceOnlyStudio",true)
root:SetAttribute("NoS1GameAuthority",true)
root.Parent=Workspace

local col={
 ink=Color3.fromRGB(35,54,86),
 gold=Color3.fromRGB(251,215,116),
 mint=Color3.fromRGB(117,234,204),
 deep=Color3.fromRGB(48,107,174),
 glass=Color3.fromRGB(156,228,254),
 cloud=Color3.fromRGB(236,244,253),
 sky=Color3.fromRGB(192,208,251),
 coral=Color3.fromRGB(255,138,168),
 navy=Color3.fromRGB(53,61,107),
 purple=Color3.fromRGB(177,142,240)
}
local function part(name,s,x,y,z,c,collide,mat,alpha)
 local p=Instance.new("Part")
 p.Name=name
 p.Size=Vector3.new(s[1],s[2],s[3])
 p.Anchored=true
 p.CanCollide=collide==true
 p.CanTouch=false
 p.CanQuery=collide==true
 p.CastShadow=collide==true
 p.Material=mat or Enum.Material.SmoothPlastic
 p.Color=c
 p.Transparency=alpha or 0
 p.Position=Vector3.new(x,y,z)
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=root
 return p
end
local function sphere(name,x,y,z,diam,c,alpha)
 local p=part(name,{diam,diam,diam},x,y,z,c,false,Enum.Material.SmoothPlastic,alpha)
 p.Shape=Enum.PartType.Ball
 return p
end
local function sign(anchor,text)
 local gui=Instance.new("BillboardGui")
 gui.Name="G8_GuidanceSign"
 gui.Size=UDim2.fromOffset(280,98)
 gui.StudsOffsetWorldSpace=Vector3.new(0,4,0)
 gui.AlwaysOnTop=false
 gui.MaxDistance=83
 gui.Parent=anchor
 local t=Instance.new("TextLabel")
 t.Name="GuideText"
 t.Text=text
 t.Size=UDim2.fromScale(1,1)
 t.TextScaled=true
 t.TextWrapped=true
 t.Font=Enum.Font.GothamBold
 t.BackgroundColor3=col.ink
 t.BackgroundTransparency=.1
 t.TextColor3=Color3.fromRGB(255,250,227)
 t.Parent=gui
 local c=Instance.new("UICorner")
 c.CornerRadius=UDim.new(0,12)
 c.Parent=t
end
local pads={
 PORT={x=0,y=0,z=0,color=col.mint,label="虹の港"},
 SEA={x=0,y=-28,z=150,color=col.glass,label="海底ガラス城"},
 SKY={x=0,y=48,z=300,color=col.sky,label="天空の城"}
}
for id,p in pairs(pads) do
 part("G8_"..id.."_FLOOR",{76,2,76},p.x,p.y-1,p.z,p.color,true,Enum.Material.SmoothPlastic)
 for _,sx in ipairs({-37,37}) do
  part("G8_"..id.."_SIDE_RAIL_"..sx,{2,6,76},p.x+sx,p.y+3,p.z,col.ink,true,Enum.Material.SmoothPlastic,.15)
 end
 for _,sz in ipairs({-37,37}) do
  part("G8_"..id.."_END_RAIL_"..sz,{76,6,2},p.x,p.y+3,p.z+sz,col.ink,true,Enum.Material.SmoothPlastic,.15)
 end
 sign(part("G8_"..id.."_LABEL_ANCHOR",{1,1,1},p.x,p.y+6,p.z-24,p.color,false,Enum.Material.SmoothPlastic,1),
  p.label.."\n光る輪で次の世界へ！")
end
local spawn=Instance.new("SpawnLocation")
spawn.Name="G8_Private_Harbor_Spawn"
spawn.Position=Vector3.new(0,1,0)
spawn.Size=Vector3.new(11,1,11)
spawn.Anchored=true
spawn.Neutral=true
spawn.CanCollide=true
spawn.Transparency=.18
spawn.Color=col.gold
spawn.Parent=root

-- Rainbow harbor: a distant ocean look, not Roblox swimming physics.
part("G8_PORT_HARBOR_DECK",{64,1,22},0,.4,-20,col.mint,true,Enum.Material.WoodPlanks)
for i=1,6 do
 local x=-28+(i-1)*11
 part("G8_PORT_PIER_"..i,{3,7,3},x,-4,-23,col.navy,false,Enum.Material.WoodPlanks)
 sphere("G8_PORT_LANTERN_"..i,x,4,-23,3,col.gold,.08).Material=Enum.Material.Neon
end
part("G8_PORT_HORIZON_SEA",{150,1,85},0,-6,36,col.deep,false,Enum.Material.SmoothPlastic,.28)

-- SEA: bright DRY glass castle below the harbor's height; NO drowning or swimming.
part("G8_SEA_GLASS_ROOF",{57,2,49},0,-11,150,col.glass,false,Enum.Material.Glass,.52)
for _,x in ipairs({-26,26}) do
 part("G8_SEA_GLASS_SIDE_"..x,{2,19,52},x,-19,150,col.glass,false,Enum.Material.Glass,.48)
end
for _,z in ipairs({125,175}) do
 part("G8_SEA_GLASS_END_"..z,{52,19,2},0,-19,z,col.glass,false,Enum.Material.Glass,.48)
end
part("G8_SEA_CASTLE_KEEP",{19,16,15},0,-19,150,col.navy,false,Enum.Material.SmoothPlastic,.14)
for _,x in ipairs({-17,17}) do
 part("G8_SEA_CASTLE_TOWER_"..x,{8,21,8},x,-17,150,col.deep,false,Enum.Material.Marble,.25)
end
for i=1,8 do
 local a=i/8*math.pi*2
 sphere("G8_SEA_CORAL_"..i,math.cos(a)*29,-20,150+math.sin(a)*28,5,
  if i%2==0 then col.coral else col.gold,.15)
end
for i=1,10 do
 local a=i/10*math.pi*2
 sphere("G8_SEA_BUBBLE_"..i,math.cos(a)*20,-7+(i%3)*2,150+math.sin(a)*20,2.2,col.glass,.34)
end

-- SKY: silhouetted tall keep above the open accessible landing courtyard.
part("G8_SKY_CLOUD_RAMP_SYMBOL",{29,2,17},0,48,276,col.cloud,true,Enum.Material.Marble,.08)
part("G8_SKY_CASTLE_KEEP",{26,20,20},0,59,301,col.cloud,false,Enum.Material.Marble)
for _,x in ipairs({-19,19}) do
 for _,z in ipairs({281,319}) do
  part("G8_SKY_TOWER_"..x.."_"..z,{8,24,8},x,60,z,col.sky,false,Enum.Material.Marble)
  sphere("G8_SKY_TOWER_LIGHT_"..x.."_"..z,x,75,z,4,col.gold,.12).Material=Enum.Material.Neon
 end
end
for i=1,9 do
 local a=i/9*math.pi*2
 sphere("G8_SKY_CLOUD_"..i,math.cos(a)*32,48+(i%2)*2,300+math.sin(a)*32,9,col.cloud,.2)
end

local lastTrip={}
local trips={
 {from="PORT",to="SEA",short="あわの輪→海底",dx=-14},
 {from="SEA",to="PORT",short="港にもどる",dx=-14},
 {from="SEA",to="SKY",short="光の輪→天空",dx=14},
 {from="SKY",to="SEA",short="海底にもどる",dx=-14},
 {from="SKY",to="PORT",short="港にもどる",dx=14}
}
for _,link in ipairs(trips) do
 local b=pads[link.from]
 local bx=b.x+link.dx
 local bz=b.z+14
 local pillar=part("G8_PORTAL_"..link.from.."_TO_"..link.to,{9,1,9},
  bx,b.y+1,bz,col.gold,true,Enum.Material.Neon,.1)
 for _,side in ipairs({-5,5}) do
  part("G8_PORTAL_ARCH_"..link.from.."_"..link.to.."_"..side,{1.5,9,1.5},
   bx+side,b.y+6,bz,col.purple,false,Enum.Material.Neon,.06)
 end
 part("G8_PORTAL_TOP_"..link.from.."_"..link.to,{12,1.6,1.5},
  bx,b.y+11,bz,col.purple,false,Enum.Material.Neon,.06)
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="G8_FreeTrip_"..link.from.."_TO_"..link.to
 prompt.ActionText=link.short
 prompt.ObjectText="みんな無料"
 prompt.KeyboardKeyCode=Enum.KeyCode.E
 prompt.GamepadKeyCode=Enum.KeyCode.ButtonX
 prompt.HoldDuration=0
 prompt.RequiresLineOfSight=false
 prompt.MaxActivationDistance=12
 prompt.Parent=pillar
 prompt.Triggered:Connect(function(player)
  if not player or not player:IsA("Player") then return end
  local character=player.Character
  if not character or not character:IsDescendantOf(Workspace) then return end
  local hum=character:FindFirstChildOfClass("Humanoid")
  local hrp=character:FindFirstChild("HumanoidRootPart")
  if not hum or not hrp or not hrp:IsA("BasePart") then return end
  local delta=hrp.Position-pillar.Position
  local now=os.clock()
  local allowed=Rules.validate(link.from,link.to,delta:Dot(delta),
   lastTrip[player] or -100,now,hum.Health)
  if not allowed then return end
  local dst=Rules.destination(link.to)
  if not dst then return end
  lastTrip[player]=now
  character:PivotTo(CFrame.new(dst.x,dst.y,dst.z))
  hrp.AssemblyLinearVelocity=Vector3.zero
  print("G8_STUDIO_ONLY_TRIP_OK",link.from,link.to)
 end)
end
Players.PlayerRemoving:Connect(function(p)lastTrip[p]=nil end)
print("G8_STUDIO_ONLY_READY; 3 floors, 5 server validated free travel links; no egg/paid")
