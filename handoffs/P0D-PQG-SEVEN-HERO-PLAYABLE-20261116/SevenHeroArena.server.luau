
--!strict
-- EGGRUMBLE / independent, Studio-only seven hero PLAYABLE prototype.
-- Source is not authoritative official RC; no Game/Store/Remote/egg modifications.
-- Copy to ServerScriptService as SevenHeroArena.server.luau for private Studio Play.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")
if not RunService:IsStudio() then return end

local ROLE_ORDER = {"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local ROLES: {[string]: {name:string,color:Color3,weapon:string,a:string,b:string}} = {
 WARRIOR={name="武神",color=Color3.fromRGB(238,87,45),weapon="大太刀・槍・拳・飛翔斬撃",a="武器自在＋飛翔斬撃",b="武神・大地震撃"},
 MAGE={name="魔法使い",color=Color3.fromRGB(64,165,255),weapon="魔導杖",a="魔力弾",b="雷光＋治癒"},
 NINJA={name="暗殺者",color=Color3.fromRGB(93,94,157),weapon="双短剣",a="瞬影斬",b="風走り＋透明化"},
 TRAPPER={name="超能力者",color=Color3.fromRGB(179,88,255),weapon="念動キューブ",a="重力衝撃",b="重力牢獄＋空間交換"},
 BUILDER={name="マッドサイエンティスト",color=Color3.fromRGB(65,238,196),weapon="未来銃",a="電磁射撃",b="自動砲台＋ロケット"},
 BEAST={name="魔獣使い",color=Color3.fromRGB(235,171,69),weapon="獣笛・進化餌",a="獣牙衝撃",b="進化魔獣召喚"},
 ZOMBIE={name="呪術師",color=Color3.fromRGB(160,74,169),weapon="呪杖",a="呪印波動",b="不死兵召喚＋呪い"},
}
local cd: {[Player]: {[string]: number}} = {}
local folder = workspace:FindFirstChild("P0D_SEVEN_HERO_STUDIO_ONLY")
if folder then folder:Destroy() end
folder=Instance.new("Folder")
folder.Name="P0D_SEVEN_HERO_STUDIO_ONLY"
folder.Parent=workspace

local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true) :: SpawnLocation?
local origin=(spawn and spawn.Position or Vector3.new(0,4,0))+Vector3.new(0,3,42)
local function part(parent:Instance,name:string,size:Vector3,pos:Vector3,color:Color3,shape:Enum.PartType?,anchored:boolean?):Part
 local p=Instance.new("Part")
 p.Name=name; p.Size=size; p.Position=pos; p.Color=color
 p.Material=Enum.Material.SmoothPlastic; p.CanCollide=false
 p.Anchored=(anchored~=false); if shape then p.Shape=shape end
 p.Parent=parent; return p
end
local function glow(p:Part,c:Color3)
 p.Color=c; p.Material=Enum.Material.Neon
end
local function label(at:Part,title:string,subtitle:string)
 local b=Instance.new("BillboardGui"); b.Name="HeroLabel"; b.AlwaysOnTop=true
 b.Size=UDim2.fromOffset(210,74);b.StudsOffset=Vector3.new(0,4,0);b.Parent=at
 local t=Instance.new("TextLabel");t.BackgroundTransparency=0.22
 t.BackgroundColor3=Color3.fromRGB(15,20,35);t.TextColor3=Color3.fromRGB(255,255,255)
 t.TextScaled=true;t.Font=Enum.Font.GothamBold;t.Size=UDim2.fromScale(1,1)
 t.Text=title.."\n"..subtitle;t.Parent=b
 local corner=Instance.new("UICorner");corner.CornerRadius=UDim.new(0,9);corner.Parent=t
end
local function flash(pos:Vector3,radius:number,color:Color3)
 local sphere=part(folder,"Impact",Vector3.new(1,1,1),pos,color,Enum.PartType.Ball)
 glow(sphere,color);sphere.Transparency=.3
 local tween=TweenService:Create(sphere,TweenInfo.new(.32,Enum.EasingStyle.Quad),{
 Size=Vector3.new(radius*2,radius*2,radius*2),Transparency=1})
 tween:Play(); Debris:AddItem(sphere,.44)
end
local function rootOf(model:Model):BasePart?
 return model:FindFirstChild("HumanoidRootPart")::BasePart? or model.PrimaryPart
end
local function nearby(pos:Vector3,range:number,exclude:Model?):{Humanoid}
 local result={};local used={}
 for _,piece in ipairs(workspace:GetPartBoundsInRadius(pos,range)) do
  local m=piece:FindFirstAncestorOfClass("Model")
  if m and m~=exclude and not used[m] and m:GetAttribute("P0D_DUMMY")==true then
   local h=m:FindFirstChildOfClass("Humanoid")
   if h and h.Health>0 then
    used[m]=true;table.insert(result,h)
   end
  end
 end
 return result
end
local function hit(pos:Vector3,radius:number,dmg:number,color:Color3,source:Model?)
 flash(pos,radius,color)
 local count=0
 for _,h in ipairs(nearby(pos,radius,source)) do
  h:TakeDamage(dmg);count+=1
 end
 return count
end
local function getRig(player:Player):(Model?,BasePart?,Humanoid?)
 local char=player.Character
 if not char then return nil,nil,nil end
 local root=char:FindFirstChild("HumanoidRootPart")::BasePart?
 local hum=char:FindFirstChildOfClass("Humanoid")
 if not root or not hum or hum.Health<=0 then return nil,nil,nil end
 return char,root,hum
end
local function forward(root:BasePart,dist:number):Vector3
 return root.Position+root.CFrame.LookVector*dist
end
local function effectsPart(parent:Instance,name:string,pos:Vector3,size:Vector3,color:Color3)
 local p=part(parent,name,size,pos,color)
 glow(p,color);return p
end
local function beastBody(name:string,at:Vector3,color:Color3,humanoid:boolean):Model
 local m=Instance.new("Model");m.Name=name;m.Parent=folder
 local b=part(m,"HumanoidRootPart",Vector3.new(2.3,2.5,2.2),at,color)
 m.PrimaryPart=b
 local head=part(m,"Head",Vector3.new(1.5,1.3,1.6),at+Vector3.new(0,1.8,-.1),color,Enum.PartType.Ball)
 local eye=effectsPart(m,"Eyes",head.Position+Vector3.new(0,0,-.77),Vector3.new(1.15,.22,.15),Color3.fromRGB(255,239,155))
 for _,off in ipairs({-1,1}) do
  part(m,"Paw",Vector3.new(.55,1.2,.6),at+Vector3.new(off*.85,-1.2,-.5),color)
 end
 if humanoid then
  local h=Instance.new("Humanoid");h.MaxHealth=120;h.Health=120;h.Parent=m
 end
 return m
end
local function summonAI(player:Player,units:{Model},lifetime:number,damage:number)
 task.spawn(function()
  local endAt=os.clock()+lifetime
  while os.clock()<endAt do
   local _,ownerRoot,_=getRig(player)
   if not ownerRoot then break end
   for i,m in ipairs(units) do
    if m.Parent then
     local mr=rootOf(m)
     if mr then
      local best:Humanoid?=nil;local bestDist=1e9
      for _,h in ipairs(nearby(mr.Position,55,nil)) do
       local tr=rootOf(h.Parent::Model)
       if tr then
        local d=(tr.Position-mr.Position).Magnitude
        if d<bestDist then bestDist=d;best=h end
       end
      end
      local focus:Vector3=ownerRoot.Position+Vector3.new((i-2)*3,0,-4)
      if best then
       local tr=rootOf(best.Parent::Model)
       if tr then focus=tr.Position end
      end
      local delta=focus-mr.Position
      if delta.Magnitude>2 then
       m:PivotTo(CFrame.new(mr.Position+delta.Unit*math.min(delta.Magnitude,3.3)))
      end
      if best and bestDist<5 then best:TakeDamage(damage);flash(mr.Position,2,Color3.fromRGB(181,109,246)) end
     end
    end
   end
   task.wait(.6)
  end
  for _,m in ipairs(units) do if m.Parent then m:Destroy() end end
 end)
end
local function curse(h:Humanoid)
 local old=h.WalkSpeed;h.WalkSpeed=math.min(old,7)
 task.delay(2.7,function() if h.Parent and h.WalkSpeed<=7 then h.WalkSpeed=old end end)
end
local function cast(player:Player,role:string,slot:string)
 local special=(slot~="A")
 local entry=ROLES[role]
 if not entry then return end
 local char,root,hum=getRig(player)
 if not char or not root or not hum then return end
 local key=role.."_"..slot
 cd[player]=cd[player] or {}
 local now=os.clock();local duration=(slot=="C" and 22) or (special and 11 or 1.0)
 if (cd[player][key] or 0)>now then return end
 cd[player][key]=now+duration
 local c=entry.color; local front=forward(root,8)
 if slot=="C" then
  -- Signature abilities: separate from ordinary/special input, always server-owned.
  if role=="WARRIOR" then
   local divine=player:GetAttribute("P0DPreviewKami") or "STORM"
   player:SetAttribute("P0DPreviewDivineActive",true)
   task.delay(6,function() if player.Parent then player:SetAttribute("P0DPreviewDivineActive",false) end end)
   if divine=="OROCHI" then
    local center=forward(root,16)
    -- Original eight-headed serpent-like divine avatar, not an AI pet.
    for n=1,8 do
     local a=n*math.pi/4
     local p=effectsPart(folder,"OrochiDivineHead_"..n,center+Vector3.new(math.cos(a)*12,4+math.sin(a)*3,math.sin(a)*12),Vector3.new(3.3,3.3,3.3),Color3.fromRGB(104,224,159))
     p.Shape=Enum.PartType.Ball
     TweenService:Create(p,TweenInfo.new(.45),{Position=center+Vector3.new(0,3,0),Transparency=.7}):Play()
     Debris:AddItem(p,.55)
    end
    task.delay(.38,function() hit(center,25,92,c,char) end)
   elseif divine=="FLAME" then
    hit(forward(root,17),19,82,Color3.fromRGB(255,115,48),char)
   else
    for n=1,3 do
     local at=forward(root,9+n*5)
     task.delay(n*.12,function() hit(at,10,35,Color3.fromRGB(130,202,255),char) end)
    end
   end
  elseif role=="MAGE" then
   local impact=forward(root,24)
   local meteor=effectsPart(folder,"Meteor",impact+Vector3.new(0,28,0),Vector3.new(5,5,5),c)
   meteor.Shape=Enum.PartType.Ball
   TweenService:Create(meteor,TweenInfo.new(.45),{Position=impact,Size=Vector3.new(9,9,9)}):Play()
   task.delay(.46,function() if meteor.Parent then meteor:Destroy() end; hit(impact,18,73,c,char) end)
  elseif role=="NINJA" then
   root.CFrame=root.CFrame+root.CFrame.LookVector*24
   hit(forward(root,4),10,70,c,char)
  elseif role=="TRAPPER" then
   local p1=effectsPart(folder,"EsperPortalA",root.Position+root.CFrame.LookVector*6,Vector3.new(5,7,.6),c)
   local p2=effectsPart(folder,"EsperPortalB",root.Position+root.CFrame.LookVector*33,Vector3.new(5,7,.6),c)
   local touched={}
   p1.Touched:Connect(function(other)
    local m=other:FindFirstAncestorOfClass("Model")
    local pr=m and Players:GetPlayerFromCharacter(m)
    if not pr or touched[pr] or (pr:GetAttribute("P0DPreviewCarryingEgg")==true) then return end
    local rr=m:FindFirstChild("HumanoidRootPart")::BasePart?
    if not rr then return end
    touched[pr]=true;rr.CFrame=p2.CFrame+Vector3.new(0,2,-6)
    task.delay(1,function() touched[pr]=nil end)
   end)
   Debris:AddItem(p1,8);Debris:AddItem(p2,8)
   hit(forward(root,15),7,12,c,char)
  elseif role=="BUILDER" then
   local craft=Instance.new("Model");craft.Name="MadScientistUFO";craft.Parent=folder
   local disc=effectsPart(craft,"FlyingSaucer",root.Position+Vector3.new(0,-2,0),Vector3.new(12,.9,12),c)
   disc.Shape=Enum.PartType.Cylinder; craft.PrimaryPart=disc
   local dome=effectsPart(craft,"Dome",root.Position+Vector3.new(0,.1,0),Vector3.new(6,3,6),Color3.fromRGB(95,165,255))
   dome.Shape=Enum.PartType.Ball;dome.Transparency=.45
   local seat=Instance.new("Seat");seat.Name="PilotSeat";seat.Size=Vector3.new(2,1.1,2)
   seat.CFrame=CFrame.new(root.Position+Vector3.new(0,.7,0));seat.Anchored=true;seat.Parent=craft
   -- The craft visibly flies over the field; this is a controlled preview, not full vehicle controls.
   task.spawn(function()
    for i=1,35 do
     if not craft.Parent then break end
     craft:PivotTo(craft:GetPivot()+root.CFrame.LookVector*1.5+Vector3.new(0,math.sin(i/4)*.16,0))
     task.wait(.08)
    end
    if craft.Parent then craft:Destroy() end
   end)
   hit(forward(root,10),13,53,c,char)
  elseif role=="BEAST" then
   local mode=player:GetAttribute("P0DPreviewBeastFeed") or "GIANT"
   local creatures={}
   local amount=if mode=="SPLIT" then 3 else 1
   for i=1,amount do
    local at=forward(root,7)+Vector3.new((i-2)*4,0,0)
    local creature=beastBody("GreatBeast_"..mode.."_"..i,at,c,false)
    creature:ScaleTo(if mode=="GIANT" then 3.1 elseif mode=="SPLIT" then 1.15 else 2.0)
    table.insert(creatures,creature)
    flash(creature:GetPivot().Position,7,c)
   end
   summonAI(player,creatures,14,if mode=="SPLIT" then 13 else 25)
  elseif role=="ZOMBIE" then
   local shade=beastBody("DarkWorldCreature",forward(root,12),c,false)
   shade:ScaleTo(2.7)
   summonAI(player,{shade},14,22)
   for _,h in ipairs(nearby(front,23,char)) do curse(h) end
   flash(front,22,c)
  end
 elseif role=="WARRIOR" then
  local divineActive=player:GetAttribute("P0DPreviewDivineActive")==true
  local boost=if divineActive then 1.55 else 1
  local function warHit(at:Vector3,radius:number,base:number)
   local num=hit(at,radius,base*boost,c,char)
   -- Real single-target dummy bonus illustrates duelist design without changing PvP authority.
   if num==1 then
    for _,target in ipairs(nearby(at,radius,char)) do target:TakeDamage(base*.32*boost) end
   end
  end
  if special then
   warHit(root.Position,17,65)
   local shock=effectsPart(folder,"EarthRing",root.Position-Vector3.new(0,2,0),Vector3.new(1,.35,1),c)
   shock.Shape=Enum.PartType.Cylinder
   TweenService:Create(shock,TweenInfo.new(.55),{Size=Vector3.new(34,.35,34),Transparency=1}):Play()
   Debris:AddItem(shock,.6)
  else
   local stance=player:GetAttribute("P0DPreviewWarlordStance") or "KATANA"
   if stance=="SPEAR" then
    warHit(forward(root,15),7,37)
   elseif stance=="FIST" then
    warHit(forward(root,4),8,22)
    task.delay(.18,function() warHit(forward(root,5),8,22) end)
   else
    warHit(front,10,31)
    -- Weapon mastery: airborne slashing arc reaches distant neutral enemies.
    local flying=effectsPart(folder,"WarGodFlyingSlash",forward(root,8)+Vector3.new(0,1,0),Vector3.new(9,5,.5),c)
    flying.Orientation=Vector3.new(0,root.Orientation.Y,22)
    TweenService:Create(flying,TweenInfo.new(.32),{Position=forward(root,30)+Vector3.new(0,1,0),Transparency=.95}):Play()
    task.delay(.31,function() warHit(forward(root,30),9,38) end)
    Debris:AddItem(flying,.40)
   end
  end
 elseif role=="MAGE" then
  if special then
   hit(front,17,32,c,char)
   for _,p in ipairs(Players:GetPlayers()) do
    local pc,pr,ph=getRig(p)
    if pc and pr and ph and (pr.Position-root.Position).Magnitude<22 and (p==player or (player.Team~=nil and p.Team==player.Team)) then
     ph.Health=math.min(ph.MaxHealth,ph.Health+28)
     flash(pr.Position,3,Color3.fromRGB(86,255,165))
    end
   end
  else hit(front,7,22,c,char) end
 elseif role=="NINJA" then
  if special then
   local old=hum.WalkSpeed
   hum.WalkSpeed=math.max(36,old*1.7)
   local oldTrans={}
   for _,d in ipairs(char:GetDescendants()) do
    if d:IsA("BasePart") and d~=root then oldTrans[d]=d.Transparency; d.Transparency=.72 end
   end
   flash(root.Position,5,c)
   task.delay(4,function()
    if hum.Parent then hum.WalkSpeed=old end
    for p,t in pairs(oldTrans) do if p.Parent then p.Transparency=t end end
   end)
  else
   local old=root.CFrame
   local dir=root.CFrame.LookVector
   root.CFrame=old+dir*math.min(12,12)
   hit(forward(root,4),7,29,c,char)
  end
 elseif role=="TRAPPER" then
  if special then
   local targets=nearby(front,22,char)
   if #targets>=2 then
    local ar=rootOf(targets[1].Parent::Model)
    local br=rootOf(targets[2].Parent::Model)
    if ar and br then
     local aPos,bPos=ar.CFrame,br.CFrame
     ar.CFrame=bPos;br.CFrame=aPos
     flash(aPos.Position,5,c);flash(bPos.Position,5,c)
    end
   end
   for _,h in ipairs(targets) do
    local tr=rootOf(h.Parent::Model)
    if tr then
     local saved=tr.CFrame
     tr.CFrame=saved+Vector3.new(0,5,0)
     h:TakeDamage(18)
     task.delay(1.2,function() if tr.Parent then tr.CFrame=saved end end)
    end
   end
   flash(front,17,c)
  else hit(front,8,23,c,char) end
 elseif role=="BUILDER" then
  if special then
   local spot=forward(root,14)
   local turret=part(folder,"MadScientistTurret",Vector3.new(3,4,3),spot,c)
   local barrel=effectsPart(folder,"TurretBarrel",spot+Vector3.new(0,2,-2),Vector3.new(1,1,4),c)
   Debris:AddItem(turret,10);Debris:AddItem(barrel,10)
   task.spawn(function()
    for _=1,13 do
     if not turret.Parent then break end
     local t=nearby(turret.Position,40,char)
     if #t>0 then
      local h=t[1];local tr=rootOf(h.Parent::Model)
      if tr then h:TakeDamage(12);flash(tr.Position,3,c) end
     end
     task.wait(.65)
    end
   end)
  else hit(front,8,25,c,char) end
 elseif role=="BEAST" then
  if special then
   local mode=player:GetAttribute("P0DPreviewBeastFeed") or "GIANT"
   local units={}
   local amount=if mode=="SPLIT" then 3 else 1
   for i=1,amount do
    local at=forward(root,6)+Vector3.new((i-2)*3,0,0)
    local m=beastBody("BeastCompanion_"..mode.."_"..i,at,c,false)
    m:ScaleTo(if mode=="GIANT" then 2.15 elseif mode=="SPLIT" then .75 else 1.0)
    if mode=="ARMORED" then
     local shell=effectsPart(m,"ArmorShell",at+Vector3.new(0,1.4,0),Vector3.new(3.1,3.0,2.9),Color3.fromRGB(150,161,178))
     shell.Transparency=.58
    end
    table.insert(units,m)
    flash(m.PrimaryPart.Position,4,c)
   end
   summonAI(player,units,12,if mode=="SPLIT" then 7 elseif mode=="ARMORED" then 10 else 17)
  else hit(front,9,25,c,char) end
 elseif role=="ZOMBIE" then
  if special then
   local units={}
   for i=1,3 do
    local m=beastBody("UndeadMinion",forward(root,5)+Vector3.new(i*3-6,0,0),c,false)
    table.insert(units,m);flash(m.PrimaryPart.Position,3,c)
   end
   summonAI(player,units,11,7)
   for _,h in ipairs(nearby(front,17,char)) do curse(h) end
  else
   hit(front,9,17,c,char)
   for _,h in ipairs(nearby(front,9,char)) do curse(h) end
  end
 end
end

local function addTool(player:Player,role:string,slot:string)
 local special=(slot~="A")
 local entry=ROLES[role]
 local tool=Instance.new("Tool")
 tool.Name=slot.." "..(slot=="A" and entry.a or (slot=="B" and entry.b or (role=="WARRIOR" and "神威降臨" or (role=="BEAST" and "進化魔獣・超覚醒" or "究極技"))))
 tool.ToolTip=entry.name.." / "..entry.weapon
 tool.CanBeDropped=false;tool.RequiresHandle=true
 tool:SetAttribute("P0DPreviewTool",true)
 local handle=Instance.new("Part")
 handle.Name="Handle";handle.Size=Vector3.new(.45,2.6,.45)
 handle.Color=entry.color;handle.Material=Enum.Material.Neon
 handle.CanCollide=false;handle.Parent=tool
 if role=="WARRIOR" then handle.Size=Vector3.new(.8,4.6,.24)
 elseif role=="NINJA" then handle.Size=Vector3.new(.28,2,.2)
 elseif role=="TRAPPER" then handle.Shape=Enum.PartType.Ball;handle.Size=Vector3.new(1.4,1.4,1.4)
 elseif role=="BUILDER" then handle.Size=Vector3.new(.8,.9,2.8)
 elseif role=="ZOMBIE" then handle.Size=Vector3.new(.8,3.8,.4) end
 tool.Activated:Connect(function()
  if player:GetAttribute("P0DPreviewRole")==role then cast(player,role,slot) end
 end)
 tool.Parent=player:WaitForChild("Backpack")
end
local function choose(player:Player,role:string)
 local backpack=player:FindFirstChildOfClass("Backpack")
 if not backpack then return end
 for _,container in ipairs({backpack,player.Character}) do
  if container then
   for _,t in ipairs(container:GetChildren()) do
    if t:IsA("Tool") and t:GetAttribute("P0DPreviewTool") then t:Destroy() end
   end
  end
 end
 player:SetAttribute("P0DPreviewRole",role)
 if role=="WARRIOR" then
  if not player:GetAttribute("P0DPreviewWarlordStance") then player:SetAttribute("P0DPreviewWarlordStance","KATANA") end
  if not player:GetAttribute("P0DPreviewKami") then player:SetAttribute("P0DPreviewKami","STORM") end
 elseif role=="BEAST" then
  if not player:GetAttribute("P0DPreviewBeastFeed") then player:SetAttribute("P0DPreviewBeastFeed","GIANT") end
 end
 addTool(player,role,"A")
 addTool(player,role,"B")
 addTool(player,role,"C")
end

local ground=part(folder,"ArenaGround",Vector3.new(108,1.5,104),origin+Vector3.new(0,-3,20),Color3.fromRGB(35,49,63))
ground.CanCollide=true
local brandMarker=part(folder,"EGGRUMBLE_BrandMarker",Vector3.new(4,1,4),origin+Vector3.new(0,0,-11),Color3.fromRGB(233,188,81))
label(brandMarker,"EGGRUMBLE","7職バトル実験場｜Studio専用")
for i,role in ipairs(ROLE_ORDER) do
 local data=ROLES[role]
 local c=data.color
 local x=(i-4)*14
 local stand=part(folder,role.."_Pedestal",Vector3.new(10,1,10),origin+Vector3.new(x,-1,0),data.color)
 stand.CanCollide=true
 local torso=part(folder,role.."_Torso",Vector3.new(2.5,3.2,1.45),stand.Position+Vector3.new(0,2.8,0),data.color)
 local head=part(folder,role.."_Head",Vector3.new(1.7,1.6,1.6),torso.Position+Vector3.new(0,2.4,0),Color3.fromRGB(234,201,159),Enum.PartType.Ball)
 for _,side in ipairs({-1,1}) do
  part(folder,role.."_Arm",Vector3.new(.9,3,.9),torso.Position+Vector3.new(side*1.8,-.05,0),data.color)
  part(folder,role.."_Leg",Vector3.new(.9,2.9,1),torso.Position+Vector3.new(side*.75,-3,0),Color3.fromRGB(30,32,49))
 end
 local weapon=effectsPart(folder,role.."_Weapon",torso.Position+Vector3.new(3.1,.1,0),Vector3.new(.45,3.8,.5),data.color)
 if role=="WARRIOR" then weapon.Size=Vector3.new(1,5,.32)
 elseif role=="TRAPPER" then weapon.Shape=Enum.PartType.Ball;weapon.Size=Vector3.new(1.6,1.6,1.6)
 elseif role=="BUILDER" then weapon.Size=Vector3.new(1.2,1.1,2.5)
 elseif role=="BEAST" then weapon.Shape=Enum.PartType.Ball;weapon.Size=Vector3.new(1.8,1.8,1.8) end
 -- Build class silhouettes using distinct shapes and wearable accents.
 if role=="WARRIOR" then
  part(folder,"WarriorShield",Vector3.new(.5,3.2,2.5),torso.Position+Vector3.new(-3,.2,0),Color3.fromRGB(113,131,149))
  for _,side in ipairs({-1,1}) do
   part(folder,"WarriorPauldron",Vector3.new(1.8,1.2,1.8),torso.Position+Vector3.new(side*1.8,1.2,0),Color3.fromRGB(222,183,86))
  end
 elseif role=="MAGE" then
  part(folder,"MageRobe",Vector3.new(3.2,3.8,.42),torso.Position+Vector3.new(0,-1.8,.8),Color3.fromRGB(33,44,101))
  for n=1,3 do
   local orb=effectsPart(folder,"MageOrb_"..n,head.Position+Vector3.new((n-2)*2.1,1.2,1.6),Vector3.new(.9,.9,.9),n==1 and Color3.fromRGB(255,134,44) or (n==2 and Color3.fromRGB(80,229,245) or Color3.fromRGB(248,240,92)))
   orb.Shape=Enum.PartType.Ball
  end
 elseif role=="NINJA" then
  local hood=part(folder,"AssassinHood",Vector3.new(2.25,2,2.2),head.Position+Vector3.new(0,.2,.15),Color3.fromRGB(28,28,47),Enum.PartType.Ball)
  hood.Transparency=.22
  effectsPart(folder,"SecondDagger",torso.Position+Vector3.new(-3,.12,0),Vector3.new(.32,2.6,.27),c)
 elseif role=="TRAPPER" then
  for n=1,4 do
   local a=n*math.pi/2
   local cube=effectsPart(folder,"EsperOrbitCube_"..n,torso.Position+Vector3.new(math.cos(a)*3,math.sin(a)*2.6,math.sin(a)*3),Vector3.new(1.1,1.1,1.1),c)
   cube.Orientation=Vector3.new(18,45,30)
  end
  effectsPart(folder,"EsperThirdEye",head.Position+Vector3.new(0,.2,-.9),Vector3.new(.65,.4,.22),c)
 elseif role=="BUILDER" then
  part(folder,"ScientistCoat",Vector3.new(3.1,4,.3),torso.Position+Vector3.new(0,-1.6,.82),Color3.fromRGB(228,234,220))
  local goggles=effectsPart(folder,"ScientistGoggles",head.Position+Vector3.new(0,.25,-.83),Vector3.new(1.5,.52,.25),c)
  goggles.Transparency=.13
  part(folder,"ScientistBackpack",Vector3.new(2.3,2.4,1.3),torso.Position+Vector3.new(0,.2,1.5),Color3.fromRGB(53,62,73))
 elseif role=="BEAST" then
  part(folder,"TamerCape",Vector3.new(3.1,4,.3),torso.Position+Vector3.new(0,-1.6,1),Color3.fromRGB(132,75,46))
  for _,side in ipairs({-1,1}) do
   part(folder,"BeastHorn",Vector3.new(.6,1.4,.7),head.Position+Vector3.new(side*.8,1.2,.1),Color3.fromRGB(223,190,105))
  end
 elseif role=="ZOMBIE" then
  part(folder,"CurseRobe",Vector3.new(3.2,3.9,.32),torso.Position+Vector3.new(0,-1.7,.92),Color3.fromRGB(40,19,69))
  local sigil=effectsPart(folder,"CurseSigil",torso.Position+Vector3.new(0,.4,-.87),Vector3.new(1.8,1.8,.14),c)
  sigil.Shape=Enum.PartType.Ball
 end
 if role=="MAGE" or role=="ZOMBIE" then
  local hat=effectsPart(folder,role.."_Sigil",head.Position+Vector3.new(0,1,0),Vector3.new(2.3,.17,2.3),data.color)
  hat.Shape=Enum.PartType.Cylinder
 end
 label(head,data.name,data.weapon.." | A通常 / B特殊 / C究極")
 local prompt=Instance.new("ProximityPrompt");prompt.ActionText="この職業で試す"
 prompt.ObjectText=data.name;prompt.HoldDuration=.2;prompt.MaxActivationDistance=12
 prompt.RequiresLineOfSight=false;prompt.Parent=stand
 prompt.Triggered:Connect(function(player) choose(player,role) end)
end

-- Prototype world buttons keep mobile UI compact: choose one technique/feed at preparation stands.
local function techniqueChoice(name:string,role:string,attribute:string,value:string,caption:string,pos:Vector3,color:Color3)
 local button=part(folder,name,Vector3.new(3.5,1.1,3.5),pos,color)
 glow(button,color)
 label(button,caption,"タップで選択")
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="TechniqueChoice";prompt.ObjectText=caption;prompt.ActionText="装備"
 prompt.MaxActivationDistance=10;prompt.RequiresLineOfSight=false;prompt.HoldDuration=.15
 prompt.Parent=button
 prompt.Triggered:Connect(function(p:Player)
  if p:GetAttribute("P0DPreviewRole")==role then
   p:SetAttribute(attribute,value)
   flash(button.Position,3,color)
  end
 end)
end
local armor=Color3.fromRGB(234,165,63)
techniqueChoice("WarlordKatana","WARRIOR","P0DPreviewWarlordStance","KATANA","大太刀",origin+Vector3.new(-50,0,-12),armor)
techniqueChoice("WarlordSpear","WARRIOR","P0DPreviewWarlordStance","SPEAR","槍",origin+Vector3.new(-45,0,-12),armor)
techniqueChoice("WarlordFist","WARRIOR","P0DPreviewWarlordStance","FIST","体術",origin+Vector3.new(-40,0,-12),armor)
techniqueChoice("KamiStorm","WARRIOR","P0DPreviewKami","STORM","雷神の神威",origin+Vector3.new(-50,0,-19),Color3.fromRGB(103,191,255))
techniqueChoice("KamiFlame","WARRIOR","P0DPreviewKami","FLAME","炎神の神威",origin+Vector3.new(-45,0,-19),Color3.fromRGB(255,115,61))
techniqueChoice("KamiOrochi","WARRIOR","P0DPreviewKami","OROCHI","八岐大蛇の幻影",origin+Vector3.new(-40,0,-19),Color3.fromRGB(119,216,142))
techniqueChoice("BeastFeedGiant","BEAST","P0DPreviewBeastFeed","GIANT","巨大化の餌",origin+Vector3.new(23,0,-12),Color3.fromRGB(242,162,64))
techniqueChoice("BeastFeedSplit","BEAST","P0DPreviewBeastFeed","SPLIT","分裂の餌",origin+Vector3.new(28,0,-12),Color3.fromRGB(245,114,208))
techniqueChoice("BeastFeedArmor","BEAST","P0DPreviewBeastFeed","ARMORED","装甲の餌",origin+Vector3.new(33,0,-12),Color3.fromRGB(113,192,194))

local function dummy(n:number)
 local ix=(n-1)%6;local iz=math.floor((n-1)/6)
 local base=origin+Vector3.new((ix-2.5)*12,0,27+iz*15)
 local m=Instance.new("Model");m.Name="TargetDummy_"..n;m:SetAttribute("P0D_DUMMY",true);m.Parent=folder
 local root=part(m,"HumanoidRootPart",Vector3.new(2.5,3.7,1.5),base+Vector3.new(0,1.5,0),Color3.fromRGB(197,75,82))
 local head=part(m,"Head",Vector3.new(1.7,1.7,1.7),root.Position+Vector3.new(0,2.4,0),Color3.fromRGB(229,184,139),Enum.PartType.Ball)
 m.PrimaryPart=root
 local h=Instance.new("Humanoid");h.MaxHealth=120;h.Health=120;h.Parent=m
 label(head,"敵ダミー "..n,"120 HP / 何度でも復活")
 h.Died:Connect(function()
  task.delay(2.5,function() if folder.Parent then m:Destroy();dummy(n) end end)
 end)
end
for n=1,12 do dummy(n) end
Players.PlayerRemoving:Connect(function(player) cd[player]=nil end)
print("[P0D PREVIEW] seven jobs, THREE active tools each, 12 respawning target dummies; Studio-only; official RC unchanged")
