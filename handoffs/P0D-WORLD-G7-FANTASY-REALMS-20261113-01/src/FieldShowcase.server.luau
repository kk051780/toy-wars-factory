--!nocheck
-- World G7: standalone PRIVATE ROBLOX STUDIO 3D showroom only, not an H1 game/egg/role/physics integration.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Workspace=game:GetService("Workspace")
if Workspace:FindFirstChild("G7_FANTASY_REALM_SOURCE_PREVIEW") then return end
local Director=require(script.Parent:WaitForChild("RiftDirector"))
local root=Instance.new("Folder")
root.Name="G7_FANTASY_REALM_SOURCE_PREVIEW"
root:SetAttribute("G7_SourcePreviewOnly",true)
root:SetAttribute("NoLiveGameplayAuthority",true)
root.Parent=Workspace
local function color(r,g,b) return Color3.fromRGB(r,g,b) end
local navy=color(32,41,72)
local gold=color(255,210,108)
local sky=color(195,227,255)
local ember=color(238,111,69)
local purple=color(157,116,244)
local mist=color(190,210,227)
local function block(name,size,x,y,z,col,solid,material,transparency)
 local p=Instance.new("Part")
 p.Name=name
 p.Size=Vector3.new(size[1],size[2],size[3])
 p.Anchored=true
 p.CanCollide=solid==true
 p.CanTouch=false
 p.CanQuery=solid==true
 p.CastShadow=solid==true
 p.Material=material or Enum.Material.SmoothPlastic
 p.Color=col
 p.Transparency=transparency or 0
 p.Position=Vector3.new(x,y,z)
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=root
 return p
end
local function orb(name,x,y,z,radius,c)
 local p=block(name,{radius,radius,radius},x,y,z,c,false,Enum.Material.SmoothPlastic,0)
 p.Shape=Enum.PartType.Ball
 return p
end
local function label(anchor,headline,subline)
 local g=Instance.new("BillboardGui")
 g.Name="G7Sign"
 g.Size=UDim2.fromOffset(250,77)
 g.StudsOffsetWorldSpace=Vector3.new(0,5,0)
 g.AlwaysOnTop=false
 g.MaxDistance=85
 g.Parent=anchor
 local t=Instance.new("TextLabel")
 t.Name="G7Title"
 t.Size=UDim2.fromScale(1,1)
 t.Text=headline.."\n"..subline
 t.BackgroundColor3=navy
 t.BackgroundTransparency=.12
 t.TextColor3=Color3.new(1,1,1)
 t.TextWrapped=true
 t.TextScaled=true
 t.Font=Enum.Font.GothamBold
 t.Parent=g
 local round=Instance.new("UICorner")
 round.CornerRadius=UDim.new(0,12)
 round.Parent=t
 return t
end
local area={
 SPACE={x=-96,z=0,tint=purple},
 HEAVEN={x=0,z=96,tint=sky},
 ABYSS={x=96,z=0,tint=ember}
}
-- The free and permanent 14-stud bridges remain open in every event phase.
block("G7_FREE_HUB",{50,1,50},0,-.5,0,color(76,127,124),true,Enum.Material.Grass)
block("G7_SPACE_PERMANENT_BRIDGE",{96,1,14},-48,-.5,0,color(109,110,155),true)
block("G7_HEAVEN_PERMANENT_BRIDGE",{14,1,96},0,-.5,48,color(204,218,230),true)
block("G7_ABYSS_PERMANENT_BRIDGE",{96,1,14},48,-.5,0,color(160,111,92),true)
local spawn=Instance.new("SpawnLocation")
spawn.Name="G7_Private_Showcase_Start"
spawn.Size=Vector3.new(9,1,9)
spawn.Position=Vector3.new(0,.5,0)
spawn.Anchored=true
spawn.CanCollide=true
spawn.Neutral=true
spawn.Transparency=.2
spawn.Color=color(106,219,163)
spawn.Parent=root
label(block("G7_HUB_RULE",{1,1,1},0,5,0,gold,false,Enum.Material.SmoothPlastic,1),
 "G7 まぼろしの三つの世界","どの橋もみんな無料で通れるよ")
for name,info in pairs(area) do
 block("G7_"..name.."_ISLAND",{47,1,47},info.x,-.5,info.z,info.tint,true,Enum.Material.SmoothPlastic)
 -- A consistent luminous gate is the instant visual "enter" cue.
 block("G7_"..name.."_GATE_LEFT",{2,14,2},info.x-7,7,info.z,info.tint,false,Enum.Material.Neon,.18)
 block("G7_"..name.."_GATE_RIGHT",{2,14,2},info.x+7,7,info.z,info.tint,false,Enum.Material.Neon,.18)
 block("G7_"..name.."_GATE_TOP",{16,2,2},info.x,13,info.z,info.tint,false,Enum.Material.Neon,.18)
 local light=orb("G7_"..name.."_BEACON",info.x,16,info.z,4,info.tint)
 light.Material=Enum.Material.Neon
 local card=Director.CARDS[name]
 local txt=label(block("G7_"..name.."_SIGN",{1,1,1},info.x,5,info.z-10,info.tint,false,Enum.Material.SmoothPlastic,1),
  card.label,card.cue.."・橋はいつも通れる")
 area[name].beacon=light
 area[name].sign=txt
end
-- Distinct scenic silhouettes: no copied IP and NO actual zero-G / damaging lava mechanics.
for i=1,12 do
 local a=(i/12)*math.pi*2
 local p=orb("G7_SPACE_STAR_"..i,-96+math.cos(a)*18,18+((i%3)*3),math.sin(a)*18,1.6,gold)
 p.Material=Enum.Material.Neon
 p.Transparency=.18
end
orb("G7_SPACE_SAFE_PLANET",-96,28,0,12,color(75,97,157))
for i=1,7 do
 local a=(i/7)*math.pi*2
 orb("G7_HEAVEN_CLOUD_"..i,math.cos(a)*15,13+(i%2)*2,96+math.sin(a)*15,8,mist).Transparency=.12
end
block("G7_HEAVEN_SKY_CASTLE",{21,6,18},0,21,96,color(243,241,219),false,Enum.Material.Marble)
for _,x in ipairs({-8,8}) do
 block("G7_HEAVEN_TOWER_"..x,{5,12,5},x,30,96,sky,false,Enum.Material.Marble)
end
for i=1,9 do
 local a=(i/9)*math.pi*2
 local x=96+math.cos(a)*17
 local z=math.sin(a)*17
 block("G7_ABYSS_OBSIDIAN_SPIRE_"..i,{2,8+i%4*3,3},x,6,z,color(76,49,57),false,Enum.Material.Slate)
 orb("G7_ABYSS_WARM_GLOW_"..i,x,12+i%4*3,z,2,gold).Transparency=.22
end
block("G7_ABYSS_SAFE_LAVA_BELOW_FLOOR",{42,.3,42},96,-1.25,0,color(229,99,48),false,Enum.Material.Neon,.32)
local status=label(block("G7_EVENT_STATUS",{1,1,1},0,8,-11,gold,false,Enum.Material.SmoothPlastic,1),
 "まぼろしイベント","20秒後にひとつの世界が光る")
local start=os.clock()
local lastPhase=""
local lastRealm=""
local heartbeat
local budget=0
heartbeat=RunService.Heartbeat:Connect(function(dt)
 if not root.Parent then heartbeat:Disconnect(); return end
 if type(dt)~="number" or dt<=0 or dt>.5 then return end
 budget+=dt
 if budget<.25 then return end
 budget=0
 local s=Director.state(os.clock()-start,0)
 if not s then return end
 local active=s.phase=="ACTIVE"
 local announced=s.phase=="ANNOUNCE"
 if s.phase~=lastPhase or s.realm~=lastRealm then
  local card=Director.CARDS[s.realm]
  status.Text=if active then "いま光る世界："..card.label
   elseif announced then "もうすぐ："..card.label
   else "三つの世界へ自由に行こう\nイベントは交代で光るだけ"
  lastPhase=s.phase
  lastRealm=s.realm
 end
 for name,areaInfo in pairs(area) do
  local selected=name==s.realm and (active or announced)
  areaInfo.beacon.Transparency=if selected then .0 else .44
  areaInfo.sign.TextColor3=if selected then gold else Color3.new(1,1,1)
 end
end)
script.Destroying:Connect(function()
 if heartbeat then heartbeat:Disconnect() end
 root:Destroy()
end)
