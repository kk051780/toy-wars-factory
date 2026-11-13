-- Standalone unpublished Studio-only WF32 level. No egg, PvP, payout or combat powers.
local Workspace=game:GetService("Workspace")
local RunService=game:GetService("RunService")
local Gate=require(script.Parent:WaitForChild("ForestGateRules"))
if not RunService:IsStudio() then return end
if Workspace:FindFirstChild("WF32_Standalone") then return end
local folder=Instance.new("Folder"); folder.Name="WF32_Standalone"; folder.Parent=Workspace
local state=Gate.initial()
local function p(name,size,pos,color,solid,mat)
 local x=Instance.new("Part"); x.Name=name; x.Size=size; x.Position=pos
 x.Color=color; x.Anchored=true; x.CanCollide=solid==true; x.CanTouch=false
 x.CanQuery=solid==true; x.Material=mat or Enum.Material.SmoothPlastic
 x.Parent=folder; return x
end
local function sign(parent,text)
 local g=Instance.new("BillboardGui"); g.Size=UDim2.fromOffset(230,60)
 g.StudsOffsetWorldSpace=Vector3.new(0,7,0); g.AlwaysOnTop=true; g.MaxDistance=90
 g.Parent=parent
 local l=Instance.new("TextLabel"); l.Size=UDim2.fromScale(1,1)
 l.BackgroundTransparency=1; l.TextScaled=true; l.Font=Enum.Font.GothamBold
 l.TextColor3=Color3.new(1,1,1); l.TextStrokeTransparency=0.3; l.Text=text; l.Parent=g
end
local green=Color3.fromRGB(90,185,113)
local glow=Color3.fromRGB(73,245,183)
local pink=Color3.fromRGB(244,118,193)
local gold=Color3.fromRGB(245,180,64)
-- Real collidable public ground and faster northern root road; paired approaches.
p("SAFE_GROUND_ROAD_ALWAYS_OPEN",Vector3.new(308,2,22),Vector3.new(0,-1,0),green,true)
p("NORTH_SHORTCUT_ROAD",Vector3.new(214,2,18),Vector3.new(0,-1,42),green,true)
for _,x in ipairs({-96,96}) do
 p("PUBLIC_SIDE_CONNECTION_"..x,Vector3.new(16,2,61),Vector3.new(x,-1,21),green,true)
end
p("RED_CASTLE_MARKER",Vector3.new(8,17,8),Vector3.new(-130,8.5,0),Color3.fromRGB(240,80,90),true)
p("BLUE_CASTLE_MARKER",Vector3.new(8,17,8),Vector3.new(130,8.5,0),Color3.fromRGB(70,150,242),true)
local clue=p("PUBLIC_ROAD_HINT",Vector3.new(1,1,1),Vector3.new(0,3,-13),glow,false)
clue.Transparency=1; sign(clue,"ちかみち と いつものみち！")
-- Tangible northern blockade. Both teams can activate the same timed opening.
local door=p("SOLID_ROOT_GATE",Vector3.new(5,12,18),Vector3.new(0,6,42),Color3.fromRGB(115,71,44),true,Enum.Material.Wood)
sign(door,"ひかる きのこを タップ！")
local marker=p("GATE_LIGHT",Vector3.new(6,1,19),Vector3.new(0,12.6,42),gold,false,Enum.Material.Neon)
for _,x in ipairs({-25,25}) do
 local sw=p("PUBLIC_SWITCH_"..x,Vector3.new(5,4,5),Vector3.new(x,2,42),glow,false,Enum.Material.Neon)
 local prompt=Instance.new("ProximityPrompt")
 prompt.ActionText="みちを ひらく"; prompt.ObjectText="ひかるきのこ"
 prompt.KeyboardKeyCode=Enum.KeyCode.E; prompt.HoldDuration=0.1
 prompt.MaxActivationDistance=11; prompt.RequiresLineOfSight=false; prompt.Parent=sw
 prompt.Triggered:Connect(function(player)
  local character=player and player.Character
  local hrp=character and character:FindFirstChild("HumanoidRootPart")
  local hum=character and character:FindFirstChildOfClass("Humanoid")
  if not hrp or not hum or hum.Health<=0 then return end
  local accepted,nextState=Gate.activate(state,Workspace:GetServerTimeNow(),(hrp.Position-sw.Position).Magnitude)
  if accepted then state=nextState end
 end)
end
-- Bounded source-only creature silhouettes: six minions, one elite and one boss.
for i=1,10 do
 local x=-108+(i-1)*24; local z=i%2==0 and 69 or 22
 p("MUSHROOM_STEM_"..i,Vector3.new(3,7,3),Vector3.new(x,3.5,z),Color3.fromRGB(227,217,179),false)
 local cap=p("MUSHROOM_GLOW_"..i,Vector3.new(12,5,12),Vector3.new(x,8,z),i%2==0 and glow or pink,false,Enum.Material.Neon)
 cap.Shape=Enum.PartType.Ball
end
local minions={}
for i=1,6 do
 local x=-62+i*17; local z=85+i%2*7
 local m=p("POKOSPO_VISUAL_MINION_"..i,Vector3.new(4,4,4),Vector3.new(x,3,z),pink,false)
 m.Shape=Enum.PartType.Ball
 table.insert(minions,{part=m,x=x,z=z,index=i})
end
local elite=p("TSUTAHUNTER_VISUAL_ELITE",Vector3.new(8,10,7),Vector3.new(-13,5,98),green,false)
local tell=p("ELITE_TELEGRAPH_NO_DAMAGE",Vector3.new(14,0.15,14),Vector3.new(-13,0.15,98),gold,false,Enum.Material.Neon)
tell.Shape=Enum.PartType.Cylinder; sign(elite,"よける よこく（えんしゅつ）")
local boss=p("MORINOS_VISUAL_BOSS",Vector3.new(17,18,12),Vector3.new(55,9,98),Color3.fromRGB(58,112,82),false)
local crown=p("MORINOS_CROWN",Vector3.new(17,4,5),Vector3.new(55,20,98),gold,false,Enum.Material.Neon)
sign(boss,"きょだいな もりの おう")
local ticked=0
local heartbeat
heartbeat=RunService.Heartbeat:Connect(function(dt)
 if not folder.Parent then heartbeat:Disconnect(); return end
 ticked=ticked+dt; if ticked<0.1 then return end; ticked=0
 local now=Workspace:GetServerTimeNow()
 local opened=Gate.isOpen(state,now)
 door.CanCollide=not opened; door.CanQuery=not opened
 door.Transparency=opened and 0.82 or 0; marker.Color=opened and glow or gold
 tell.Transparency=(now%12<1.5) and 0.3 or 1
 for _,m in ipairs(minions) do
  m.part.Position=Vector3.new(m.x,3+math.sin(now*3+m.index)*0.6,m.z)
 end
 elite.Position=Vector3.new(-13+math.sin(now*0.7)*4,5,98)
 local y=math.sin(now*0.7); boss.Position=Vector3.new(55,9+y,98)
 crown.Position=Vector3.new(55,20+y,98)
end)
