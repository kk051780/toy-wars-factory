--!nonstrict
-- EGGRUMBLE mobile HUD + filtered fog map, isolated from combat and purchase authority.
-- This client never creates a damage/score RemoteEvent and never receives hidden world positions.
local Players=game:GetService("Players")
local UserInputService=game:GetService("UserInputService")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
local player=Players.LocalPlayer
local view=require(ReplicatedStorage:WaitForChild("EGGRUMBLE_HudPresentationPolicy"))
local remote=ReplicatedStorage:WaitForChild("EGGRUMBLE_MapIntelUpdate_V1",20)
if not remote then return end
local playerGui=player:WaitForChild("PlayerGui")
if playerGui:FindFirstChild("EGGRUMBLE_CombatHudIntel") then return end
local gui=Instance.new("ScreenGui")
gui.Name="EGGRUMBLE_CombatHudIntel"
gui.DisplayOrder=20
gui.IgnoreGuiInset=false
gui.ResetOnSpawn=false
gui.ZIndexBehavior=Enum.ZIndexBehavior.Sibling
gui.Parent=playerGui
local function rounded(obj,r)
 local c=Instance.new("UICorner")
 c.CornerRadius=UDim.new(0,r)
 c.Parent=obj
end
local function frame(name,parent)
 local f=Instance.new("Frame")
 f.Name=name
 f.BorderSizePixel=0
 f.BackgroundColor3=Color3.fromRGB(17,28,40)
 f.BackgroundTransparency=.28
 f.Parent=parent
 rounded(f,9)
 return f
end
local function label(name,parent,text,size)
 local t=Instance.new("TextLabel")
 t.Name=name;t.Text=text;t.TextSize=size
 t.Font=Enum.Font.GothamBold
 t.TextColor3=Color3.fromRGB(232,244,248)
 t.BackgroundTransparency=1;t.TextWrapped=false
 t.TextTruncate=Enum.TextTruncate.AtEnd
 t.Parent=parent
 return t
end
local function button(name,parent,text)
 local b=Instance.new("TextButton")
 b.Name=name;b.Text=text;b.TextSize=13
 b.Font=Enum.Font.GothamBold;b.TextColor3=Color3.new(1,1,1)
 b.BackgroundColor3=Color3.fromRGB(43,65,84)
 b.BackgroundTransparency=.13;b.BorderSizePixel=0
 b.AutoButtonColor=true
 b.Parent=parent;rounded(b,14)
 return b
end
local mapBox=frame("FilteredMinimap",gui)
mapBox.ClipsDescendants=true
mapBox.ZIndex=2
local mapTitle=label("MapTitle",mapBox,"地図",11)
mapTitle.Size=UDim2.new(1,-8,0,20)
mapTitle.Position=UDim2.fromOffset(4,1)
mapTitle.ZIndex=4
local canvas=Instance.new("Frame")
canvas.Name="Tiles"
canvas.Position=UDim2.fromOffset(2,21)
canvas.Size=UDim2.new(1,-4,1,-23)
canvas.BackgroundTransparency=1
canvas.ClipsDescendants=true
canvas.ZIndex=2
canvas.Parent=mapBox
local mapToggle=button("ToggleMap",mapBox,"")
mapToggle.BackgroundTransparency=1
mapToggle.Size=UDim2.fromScale(1,1)
mapToggle.ZIndex=10
local mapExpanded=false
local refreshMapLayout=function() end
local layerButton=button("MapLayer",mapBox,"陸/海/空")
layerButton.Size=UDim2.fromOffset(66,20)
layerButton.AnchorPoint=Vector2.new(1,0)
layerButton.Position=UDim2.new(1,-4,0,1)
layerButton.Visible=false
layerButton.ZIndex=12
local activeLayer="LAND"
local mapSnapshot=nil
local tilePool={}
local markerPool={}
local function tile(index)
 local f=tilePool[index]
 if not f then
  f=Instance.new("Frame")
  f.Name="FogCell"
  f.BorderSizePixel=0
  f.BackgroundColor3=Color3.fromRGB(81,120,92)
  f.BackgroundTransparency=.12
  f.ZIndex=2
  f.Parent=canvas
  tilePool[index]=f
 end
 return f
end
local function mapPin(index)
 local v=markerPool[index]
 if not v then
  v=Instance.new("TextLabel")
  v.Name="MapPin"
  v.Font=Enum.Font.GothamBold
  v.TextSize=12
  v.TextColor3=Color3.fromRGB(255,255,255)
  v.BackgroundColor3=Color3.fromRGB(33,46,61)
  v.BackgroundTransparency=.08
  v.TextScaled=false
  v.ZIndex=5
  v.Parent=canvas
  rounded(v,8)
  markerPool[index]=v
 end
 return v
end
local function redraw()
 local s=mapSnapshot
 if not s then
  mapTitle.Text="地図｜城から出撃"
  for _,p in ipairs(tilePool) do p.Visible=false end
  for _,p in ipairs(markerPool) do p.Visible=false end
  return
 end
 mapTitle.Text=(mapExpanded and "探索マップ" or "MAP").." ["..activeLayer.."]"
  ..(s.scanActive==true and " 索敵中" or "")
 local visited={}
 for _,key in ipairs(s.explored or {}) do
  if type(key)=="string" then visited[key]=true end
 end
 local width=canvas.AbsoluteSize.X
 local height=canvas.AbsoluteSize.Y
 if width<30 or height<30 then return end
 local cell=s.cell or 40
 local span=mapExpanded and 960 or 640
 local cx,cz=s.x,s.z
 local count=0
 local nx=math.min(12,math.max(7,math.floor(width/12)))
 local nz=math.min(10,math.max(7,math.floor(height/12)))
 for ix=1,nx do
  for iz=1,nz do
   count+=1
   local x=cx+((ix-.5)/nx-.5)*span
   local z=cz+((iz-.5)/nz-.5)*span*height/width
   local index=math.floor(x/cell)..":"..math.floor(z/cell)
   local f=tile(count)
   f.Visible=true
   f.Position=UDim2.fromScale((ix-1)/nx,(iz-1)/nz)
   f.Size=UDim2.fromScale(1/nx+.004,1/nz+.004)
   f.BackgroundColor3=visited[index]
     and Color3.fromRGB(75,119,88) or Color3.fromRGB(30,49,59)
   f.BackgroundTransparency=visited[index] and .1 or .06
  end
 end
 for i=count+1,#tilePool do tilePool[i].Visible=false end
 local k=0
 for _,m in ipairs(s.markers or {}) do
  if type(m)=="table" and m.layer==activeLayer then
   local dx=(m.x-cx)/span+.5
   local dz=(m.z-cz)/(span*height/width)+.5
   if dx>=0 and dx<=1 and dz>=0 and dz<=1 then
    k+=1
    local pin=mapPin(k)
    pin.Visible=true
    pin.Text=if m.kind=="CASTLE" then "城"
      elseif m.kind=="SELF" then "▲"
      elseif m.kind=="ALLY" then "味"
      elseif m.kind=="ENEMY" then "敵"
      elseif m.kind=="NEUTRAL" then "兵"
      elseif m.kind=="CASTLE_GATE" then "門"
      elseif m.kind=="EGG" then "卵"
      elseif m.kind=="MAGIC_TREASURE" then "宝"
      elseif m.kind=="RESOURCE" then "物"
      elseif m.kind=="ENEMY_TRAIL" then "跡"
      else "•"
    pin.BackgroundColor3=if m.kind=="SELF" then Color3.fromRGB(49,154,197)
      elseif m.kind=="ENEMY" then Color3.fromRGB(166,76,89)
      elseif m.precision=="SECTOR" then Color3.fromRGB(132,107,64)
      else Color3.fromRGB(71,105,119)
    pin.AnchorPoint=Vector2.new(.5,.5)
    pin.Position=UDim2.fromScale(dx,dz)
    pin.Size=UDim2.fromOffset(mapExpanded and 26 or 20,mapExpanded and 24 or 19)
    pin.TextSize=mapExpanded and 13 or 10
   end
  end
 end
 for i=k+1,#markerPool do markerPool[i].Visible=false end
end
local statusBox=frame("CompactStatus",gui)
statusBox.ZIndex=3
local hp=label("HP",statusBox,"HP --/--",12)
hp.Size=UDim2.new(.45,-3,1,0);hp.Position=UDim2.fromOffset(6,0)
local buffs=label("Buffs",statusBox,"属性 --  |  状態 --",11)
buffs.Size=UDim2.new(.55,-5,1,0);buffs.Position=UDim2.new(.45,2,0,0)
local progress=frame("MusouCharge",gui)
progress.BackgroundTransparency=.2
local fill=Instance.new("Frame")
fill.BackgroundColor3=Color3.fromRGB(225,189,93)
fill.BorderSizePixel=0;fill.Size=UDim2.fromScale(0,1)
fill.Parent=progress;rounded(fill,3)
local actions={}
for _,name in ipairs({"ATTACK","JUMP","DODGE","INVUL","MUSOU","ITEM","SKILL"}) do
 actions[name]=button(name,gui,({
  ATTACK="攻撃",JUMP="跳ぶ",DODGE="回避",
  INVUL="無敵",MUSOU="無双",ITEM="道具 ▼",SKILL="技 ▼",
 })[name])
 actions[name].ZIndex=6
end
-- Native Roblox thumbstick/jump are retained, no competing movement joystick.
actions.JUMP.Visible=false
actions.DODGE.Visible=false -- requires an existing authorized dodge owner
-- Reuse the reserved dodge-area anchor for the selected existing special Tool
-- until a true server-backed dodge exists. No extra HUD footprint.
local skillUse=button("SelectedSkillUse",gui,"技B")
skillUse.ZIndex=6
local drawer=frame("ChoiceDrawer",gui)
drawer.Visible=false;drawer.ZIndex=11
local drawerType=""
local drawerOptions={}
local choices={}
for i=1,4 do
 choices[i]=button("Choice_"..i,drawer,"")
 choices[i].Size=UDim2.new(1,-12,0,37)
 choices[i].Position=UDim2.fromOffset(6,5+(i-1)*40)
 choices[i].ZIndex=12
end
local selectedSlot="B"
local selectedItem=nil
local function toolWith(prefix)
 local backpack=player:FindFirstChildOfClass("Backpack")
 local character=player.Character
 local out={}
 for _,container in ipairs({backpack,character}) do
  if container then
   for _,child in ipairs(container:GetChildren()) do
    if child:IsA("Tool") and string.sub(child.Name,1,#prefix)==prefix then
     table.insert(out,child)
    end
   end
  end
 end
 return out
end
-- Match exact tool IDs from the source-selected, original server Combat and Invul.
-- Tool existence means the player has the server-owned ability; never mint it here.
local function ownedToolByName(name)
 for _,tool in ipairs(toolWith("")) do
  if tool.Name==name then return tool end
 end
 return nil
end
local function musouTool()
 return ownedToolByName("EGGRUMBLE_MUSOU_AWAKEN")
end
local function counterTool()
 return ownedToolByName("迎撃覚醒")
end
local function slotTool(slot)
 for _,tool in ipairs(toolWith("EGGRUMBLE_SKILL_")) do
  if string.match(tool.Name,"^EGGRUMBLE_SKILL_"..slot.."_") then return tool end
 end
 return nil
end
local function activeItem()
 if not selectedItem then return nil end
 for _,t in ipairs(toolWith("EGGRUMBLE_ITEM_")) do
  if t.Name==selectedItem then return t end
 end
 return nil
end
local function activate(t)
 if not t then return end
 local ch=player.Character
 local h=ch and ch:FindFirstChildOfClass("Humanoid")
 if not h or h.Health<=0 then return end
 local old=ch:FindFirstChildOfClass("Tool")
 if t.Parent~=ch then h:EquipTool(t) end
 -- Tool:Activate uses the existing server-authoritative Tool.Activated handler.
 if t.Parent==ch then t:Activate() end
 if old and old~=t and old.Parent==ch then
  -- Restoring an old tool can interrupt the action; leave selection equipped.
 end
end
local function closeDrawer()
 drawer.Visible=false;drawerType=""
end
local function openDrawer(which)
 if drawerType==which then closeDrawer();return end
 drawerType=which
 local options={}
 if which=="SKILL" then
  for _,slot in ipairs({"A","B","C"}) do
   local t=slotTool(slot)
   if t then table.insert(options,{id=slot,name=slot.." "..t.Name:sub(19),tool=t}) end
  end
 else
  for _,t in ipairs(toolWith("EGGRUMBLE_ITEM_")) do
   table.insert(options,{id=t.Name,name=t.Name:sub(16),tool=t})
  end
 end
 drawerOptions=options
 for i,b in ipairs(choices) do
  local item=options[i]
  b.Visible=item~=nil
  if item then b.Text=item.name end
 end
 drawer.Visible=#options>0
 if #options==0 then closeDrawer() end
end
for i,b in ipairs(choices) do
 b.Activated:Connect(function()
  local item=drawerOptions[i]
  if not item then return end
  if drawerType=="SKILL" then selectedSlot=item.id
  elseif drawerType=="ITEM" then
   selectedItem=item.id
   -- Selecting an already-owned consumable performs its existing Tool action.
   -- This never calls MarketplaceService, a store Remote or client damage.
   activate(item.tool)
  end
  closeDrawer()
 end)
end
actions.ITEM.Activated:Connect(function()openDrawer("ITEM")end)
actions.SKILL.Activated:Connect(function()openDrawer("SKILL")end)
actions.ATTACK.Activated:Connect(function()
 closeDrawer()
 local basic=toolWith("EGGRUMBLE_BASIC_")
 -- The current 55-source server has no dedicated basic attack Tool.
 -- Use only its real A skill (clearly labeled) until Combat owner adds basic.
 activate(basic[1] or slotTool("A"))
end)
skillUse.Activated:Connect(function()
 if not mapSnapshot then return end
 closeDrawer()
 activate(slotTool(selectedSlot))
end)
-- Both buttons activate ONLY original server-owned Tools; every activation
-- is re-checked by the original singleton server policy (not this HUD).
actions.MUSOU.Activated:Connect(function()
 if not mapSnapshot then return end
 local tool=musouTool()
 local phase=player:GetAttribute("EGGRUMBLE_MusouPhase")
 if tool and phase~="MUSOU" and phase~="RUSH" and phase~="KAKUHEN" then
  closeDrawer();activate(tool)
 end
end)
actions.INVUL.Activated:Connect(function()
 if not mapSnapshot then return end
 local tool=counterTool()
 local defense=mapSnapshot and mapSnapshot.defense
 local phase=(type(defense)=="table" and defense.phase)
  or player:GetAttribute("EGGRUMBLE_InvulPhase")
 if tool and phase~="ARMED" and phase~="AWAKENED" then
  closeDrawer();activate(tool)
 end
end)
mapToggle.Activated:Connect(function()
 mapExpanded=not mapExpanded
 if mapExpanded then closeDrawer() end
 layerButton.Visible=mapExpanded
 refreshMapLayout()
 redraw()
end)
layerButton.Activated:Connect(function()
 activeLayer=if activeLayer=="LAND" then "SEA"
   elseif activeLayer=="SEA" then "SKY" else "LAND"
 redraw()
end)
remote.OnClientEvent:Connect(function(s)
 if type(s)~="table" or s.version~=1 then return end
 if s.kind=="MAP_RESET" then
  mapSnapshot=nil;mapExpanded=false;activeLayer="LAND"
  layerButton.Visible=false
  closeDrawer();refreshMapLayout();redraw()
  return
 end
 if s.kind~="MAP_INTEL" then return end
 if type(s.x)~="number" or type(s.z)~="number"
  or type(s.markers)~="table" or type(s.explored)~="table"
  or #s.markers>30 or #s.explored>500 then return end
 mapSnapshot=s
 if not mapExpanded then activeLayer=s.layer or "LAND" end
 redraw()
end)
local lastW,lastH,lastHand=-1,-1,nil
local function updateLayout()
 local camera=workspace.CurrentCamera
 local size=camera and camera.ViewportSize
 if not size or size.X<=0 or size.Y<=0 then return end
 local w,h=size.X,size.Y
 local hand=player:GetAttribute("EGGRUMBLE_LeftHanded") and "LEFT" or "RIGHT"
 if w==lastW and h==lastH and hand==lastHand then return end
 lastW,lastH,lastHand=w,h,hand
 local data=view.layout(w,h,hand)
 local p=data.anchors
 for name,b in pairs(actions) do
  if p[name] then
   b.AnchorPoint=Vector2.new(.5,.5)
   b.Size=UDim2.fromOffset(p[name].size,p[name].size)
   b.Position=UDim2.fromOffset(p[name].x,p[name].y)
  end
 end
 local reserved=p.DODGE
 skillUse.AnchorPoint=Vector2.new(.5,.5)
 skillUse.Size=UDim2.fromOffset(reserved.size,reserved.size)
 skillUse.Position=UDim2.fromOffset(reserved.x,reserved.y)
 local mx=p.MAP.x
 if mapExpanded then
  mapBox.Size=UDim2.fromOffset(math.floor(math.min(w*.43,340)),math.floor(math.min(h*.66,285)))
  mapBox.Position=UDim2.fromOffset(9,math.max(8,math.floor(h*.12)))
 else
  mapBox.Size=UDim2.fromOffset(p.MAP.size,p.MAP.size)
  mapBox.Position=UDim2.fromOffset(math.max(5,mx-p.MAP.size/2),8)
 end
 local chrome=data.chrome
 local status=chrome.status
 local bar=chrome.musouBar
 statusBox.Position=UDim2.fromOffset(status.x,status.y)
 statusBox.Size=UDim2.fromOffset(status.w,status.h)
 progress.Position=UDim2.fromOffset(bar.x,bar.y)
 progress.Size=UDim2.fromOffset(bar.w,bar.h)
 drawer.Size=UDim2.fromOffset(math.min(178,w*.23),170)
 drawer.Position=UDim2.fromOffset(math.max(w-195,w*.72),math.min(h*.35,147))
 redraw()
end
refreshMapLayout=function()
 lastW=-1
 updateLayout()
end
local elapsed=0
RunService.RenderStepped:Connect(function(dt)
 elapsed+=dt
 if elapsed<.16 then return end
 elapsed=0
 updateLayout()
 local char=player.Character
 local h=char and char:FindFirstChildOfClass("Humanoid")
 if h then
  hp.Text=string.format("HP %d/%d",math.max(0,math.floor(h.Health)),math.floor(h.MaxHealth))
 else hp.Text="HP --/--" end
 -- Status expiry timestamps are server os.clock, which is NOT safely
 -- comparable to the client process os.clock. Use the filtered server flags.
 local status=(mapSnapshot and mapSnapshot.statuses) or {}
 if type(status)~="table" then status={} end
 local attr=player:GetAttribute("EGGRUMBLE_Attribute") or "--"
 buffs.Text="属性 "..tostring(attr).." "..table.concat(status," ")
 -- The actual Real55 server sends MusouReadyIn and MusouPhase.
 -- Invul uses the original Japanese named server Tool, and ARMED/AWAKENED
 -- are two different server-published states. Do not invent Ready attributes.
 local musou=musouTool()
 local invul=counterTool()
 local phaseM=player:GetAttribute("EGGRUMBLE_MusouPhase")
 local readyIn=player:GetAttribute("EGGRUMBLE_MusouReadyIn")
 local activeM=phaseM=="MUSOU" or phaseM=="RUSH" or phaseM=="KAKUHEN"
 local verifiedM=musou~=nil and phaseM=="OFF" and type(readyIn)=="number"
  and readyIn>=0 and readyIn<=0.05
 if activeM then
  actions.MUSOU.Text=if phaseM=="KAKUHEN" then "確変中"
    elseif phaseM=="RUSH" then "連チャン" else "無双中"
 elseif verifiedM then
  actions.MUSOU.Text="無双 発動"
 elseif musou and type(readyIn)=="number" and readyIn>0 then
  actions.MUSOU.Text="無双 充填"
 else
  actions.MUSOU.Text="無双 --"
 end
 -- Current V2 server policy is delivered in the existing private map update;
 -- unlike a stale Player attribute it returns to NONE when the 3s arm expires.
 local defense=mapSnapshot and mapSnapshot.defense
 local phaseI=if type(defense)=="table" then defense.phase
   else player:GetAttribute("EGGRUMBLE_InvulPhase")
 local awakened=phaseI=="AWAKENED"
 local armed=phaseI=="ARMED"
 local remain=if type(defense)=="table" and type(defense.remaining)=="number"
   then math.max(0,defense.remaining) else 0
 actions.INVUL.Text=if awakened then string.format("無敵 %.0fs",remain)
  elseif armed then string.format("迎撃 %.0fs",remain)
  elseif invul then "迎撃" else "迎撃 --"
 actions.MUSOU.BackgroundTransparency=verifiedM and .08 or .48
 actions.INVUL.BackgroundTransparency=(invul and not awakened and not armed)
  and .08 or .48
 actions.INVUL.BackgroundColor3=if awakened then Color3.fromRGB(37,132,165)
   elseif armed then Color3.fromRGB(122,97,158)
   else Color3.fromRGB(43,65,84)
 -- A bar is only server-snapshot progress, not a client-forged READY timer.
 local charge=0
 if musou and type(readyIn)=="number" and readyIn>=0 then
  charge=1-math.clamp(readyIn/70,0,1)
 end
 fill.Size=UDim2.fromScale(charge,1)
 -- Keep base attack tappable without an optional skill slot.
 actions.ATTACK.Visible=#toolWith("EGGRUMBLE_BASIC_")>0 or slotTool("A")~=nil
 actions.ATTACK.Text=toolWith("EGGRUMBLE_BASIC_")[1] and "攻撃" or "技A"
 skillUse.Text="技"..selectedSlot
 skillUse.Visible=slotTool(selectedSlot)~=nil
 actions.ITEM.Text=#toolWith("EGGRUMBLE_ITEM_")>0 and "道具 ▼" or "道具 0"
 -- A second existing S1 screen is authoritative for its own combat.
 local s1=playerGui:FindFirstChild("TrapRaidersS1HUD")
 if s1 and s1:IsA("ScreenGui") and s1.Enabled then
  actions.ATTACK.Visible=false
 end
 local inMatch=mapSnapshot~=nil
 gui.Enabled=inMatch -- no V3 combat chrome over the separate lobby
 mapBox.Visible=inMatch
 actions.ITEM.Visible=inMatch
 actions.SKILL.Visible=inMatch
 actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch
 skillUse.Visible=skillUse.Visible and inMatch
 -- Disabled mode buttons stay visible in combat without claiming server READY.
 actions.INVUL.Visible=inMatch
 actions.MUSOU.Visible=inMatch
 if not inMatch then closeDrawer() end
end)
