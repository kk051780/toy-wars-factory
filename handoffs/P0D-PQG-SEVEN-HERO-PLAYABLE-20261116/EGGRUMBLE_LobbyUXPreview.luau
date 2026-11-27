--!strict
-- Independent LOBBY UX preview; not connected to match host or production queue.
-- Two readable physical mode portals, seven job plaques and transient selection feedback.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local Lobby={}
local JOBS={
 {"武神","大剣",Color3.fromRGB(227,102,76)},
 {"魔法使い","魔導杖",Color3.fromRGB(120,128,239)},
 {"暗殺者","双短剣",Color3.fromRGB(118,205,174)},
 {"超能力者","念動",Color3.fromRGB(208,142,242)},
 {"マッドサイエンティスト","発明兵器",Color3.fromRGB(242,191,96)},
 {"魔獣使い","召喚",Color3.fromRGB(96,187,111)},
 {"呪術師","呪符",Color3.fromRGB(177,125,214)},
}
local function platform(parent:Instance,name:string,at:Vector3,size:Vector3,color:Color3):Part
 local p=Instance.new("Part");p.Name=name;p.Size=size;p.Anchored=true;p.Position=at
 p.Color=color;p.Material=Enum.Material.SmoothPlastic;p.Parent=parent
 return p
end
local function plaque(parent:BasePart,text:string):()
 local ui=Instance.new("BillboardGui");ui.Name="WorldPlaque";ui.Size=UDim2.fromOffset(190,66)
 ui.StudsOffsetWorldSpace=Vector3.new(0,4,0);ui.AlwaysOnTop=false
 ui.MaxDistance=42;ui.Parent=parent
 local label=Instance.new("TextLabel");label.Name="Title";label.Size=UDim2.fromScale(1,1)
 label.BackgroundTransparency=0.22;label.BackgroundColor3=Color3.fromRGB(20,26,38)
 label.TextColor3=Color3.new(1,1,1);label.TextScaled=true;label.TextWrapped=true
 label.Font=Enum.Font.GothamBold;label.Text=text;label.Parent=ui
end
local function action(parent:BasePart,label:string,callback:(Player)->()):()
 local prompt=Instance.new("ProximityPrompt");prompt.ActionText=label;prompt.ObjectText=parent.Name
 prompt.MaxActivationDistance=9;prompt.RequiresLineOfSight=true;prompt.HoldDuration=0.15
 prompt.Parent=parent;prompt.Triggered:Connect(callback)
end
function Lobby.build(parent:Instance,origin:Vector3):any
 assert(RunService:IsStudio(),"private lobby UX preview only")
 local model=Instance.new("Model");model.Name="EGGRUMBLE_LobbyUX";model.Parent=parent
 platform(model,"LobbyFloor",origin+Vector3.new(0,-1,0),Vector3.new(100,2,95),Color3.fromRGB(55,72,86))
 local selected:{[number]:string}={}
 local modeSelected:{[number]:string}={}
 for i,job in ipairs(JOBS) do
  local x=(i-4)*12
  local stand=platform(model,"JOB_"..i,origin+Vector3.new(x,2,-19),Vector3.new(8,4,7),job[3]::Color3)
  plaque(stand,(job[1]::string).."\n"..(job[2]::string))
  action(stand,"この職業を選ぶ",function(p)
   selected[p.UserId]=job[1]::string
   p:SetAttribute("EGGRUMBLE_LobbyPreviewRole",selected[p.UserId])
  end)
 end
 for _,gate in ipairs({
  {name="TEAM",x=-15,color=Color3.fromRGB(218,88,78),title="チーム戦\n味方の城を守れ"},
  {name="BATTLE_ROYALE",x=15,color=Color3.fromRGB(77,144,231),title="バトルロワイヤル\n最後の城が勝者"},
 }) do
  local portal=platform(model,gate.name.."_PORTAL",origin+Vector3.new(gate.x,6,19),
   Vector3.new(11,12,2),gate.color)
  portal.Material=Enum.Material.Neon
  plaque(portal,gate.title)
  action(portal,"モード選択",function(p)
   -- Preview only. Do not claim to queue or teleport a real player.
   modeSelected[p.UserId]=gate.name
   p:SetAttribute("EGGRUMBLE_LobbyPreviewMode",gate.name)
  end)
 end
 Players.PlayerRemoving:Connect(function(p)
  selected[p.UserId]=nil;modeSelected[p.UserId]=nil
 end)
 return {model=model,roles=7,portals=2,selected=selected,modeSelected=modeSelected}
end
return Lobby
