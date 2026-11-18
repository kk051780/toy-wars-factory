--!strict
-- GQ805 additive physical showroom; Studio private source ONLY.
-- No Remote, wallet, Store, purchase, combat, castle or score authority.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local existing=workspace:FindFirstChild("GQ805_LobbyGuildShop",true)
if existing then return end
local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)
local origin=spawn and spawn.Position or Vector3.new(0,4,0)
local center=origin+Vector3.new(43,0,6)
local world=Instance.new("Model")
world.Name="GQ805_LobbyGuildShop"
world:SetAttribute("EGGRUMBLE_ShopPreviewOnly",true)
world:SetAttribute("EGGRUMBLE_NoPurchaseAuthority",true)
world.Parent=workspace
local made=0
local function piece(parent:Instance,name:string,localAt:Vector3,size:Vector3,color:Color3,collide:boolean,material:Enum.Material?):Part
 local p=Instance.new("Part")
 p.Name=name;p.Anchored=true;p.CanCollide=collide;p.CanTouch=false
 p.CanQuery=collide;p.Material=material or Enum.Material.SmoothPlastic
 p.Size=size;p.Position=center+localAt;p.Color=color;p.Parent=parent
 made+=1
 return p
end
local function plaque(part:BasePart,title:string,height:number)
 local gui=Instance.new("BillboardGui")
 gui.Name="GQ805_ShopCaption"
 gui.Size=UDim2.fromOffset(175,height)
 gui.StudsOffsetWorldSpace=Vector3.new(0,1.8,0)
 gui.AlwaysOnTop=false
 gui.MaxDistance=45
 gui.Parent=part
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1);label.BackgroundTransparency=.3
 label.BackgroundColor3=Color3.fromRGB(18,29,44)
 label.TextColor3=Color3.fromRGB(255,241,194)
 label.Font=Enum.Font.GothamBold
 label.TextScaled=true;label.TextWrapped=true
 label.Text=title;label.Parent=gui
end
piece(world,"GuildFloor",Vector3.new(0,-1,0),Vector3.new(29,2,25),Color3.fromRGB(96,116,127),true,Enum.Material.Slate)
-- The lobby spawn and storefront must be physically connected without assuming prebuilt terrain.
-- Bridge spans x=-45..-14 in this model, meeting the existing spawn at x=-43 and shop floor edge x=-14.5.
piece(world,"GuildApproachWalkway",Vector3.new(-29.5,-1,-3),Vector3.new(31,2,7),Color3.fromRGB(119,133,128),true,Enum.Material.Slate)
for _,offset in ipairs({-12,12}) do
 piece(world,"GuildPillar",Vector3.new(offset,5,8),Vector3.new(2,11,2),Color3.fromRGB(166,134,94),true,Enum.Material.Wood)
end
piece(world,"GuildRoof",Vector3.new(0,11,2),Vector3.new(29,2,17),Color3.fromRGB(67,89,138),false,Enum.Material.Slate)
piece(world,"GuildBack",Vector3.new(0,4,10),Vector3.new(29,8,1),Color3.fromRGB(84,109,138),true,Enum.Material.Brick)
local door=piece(world,"GuildEntry",Vector3.new(0,2,-10),Vector3.new(8,4,1),Color3.fromRGB(236,195,87),false,Enum.Material.Neon)
plaque(door,"ギルドショップ\n守護兵14種 / 商品を見る",55)
local prompt=Instance.new("ProximityPrompt")
prompt.Name="GQ805_ShopReadOnlyPrompt"
prompt.ActionText="商品を見る"
prompt.ObjectText="ギルドショップ（購入機能準備中）"
prompt.MaxActivationDistance=11;prompt.HoldDuration=.2
prompt.RequiresLineOfSight=true;prompt.Parent=door
-- All 14 miniatures are *cosmetic models*, NEVER free combat guardians.
-- Identity follows #808 guardian catalog role order; no copied shop prices.
local roles={
 {"WARRIOR","武神",Color3.fromRGB(235,108,71),Enum.PartType.Block},
 {"MAGE","魔法使い",Color3.fromRGB(94,157,235),Enum.PartType.Ball},
 {"NINJA","暗殺者",Color3.fromRGB(121,112,184),Enum.PartType.Block},
 {"TRAPPER","超能力者",Color3.fromRGB(187,107,237),Enum.PartType.Ball},
 {"BUILDER","科学者",Color3.fromRGB(77,204,178),Enum.PartType.Block},
 {"BEAST","魔獣使い",Color3.fromRGB(230,177,89),Enum.PartType.Ball},
 {"ZOMBIE","呪術師",Color3.fromRGB(162,104,177),Enum.PartType.Block},
}
for i,r in ipairs(roles) do
 for variant=1,2 do
  local figurine=Instance.new("Model")
  figurine.Name="ShopPreview_"..r[1].."_"..variant
  figurine:SetAttribute("EGGRUMBLE_GuardianPreviewOnly",true)
  figurine:SetAttribute("EGGRUMBLE_RoleId",r[1])
  figurine.Parent=world
  local x=(i-4)*3.8
  local z=if variant==1 then -3 else 4
  local stand=piece(figurine,"Stand",Vector3.new(x,0.15,z),Vector3.new(2.6,.3,2.6),Color3.fromRGB(212,173,101),false)
  local torso=piece(figurine,"GuardianBody",Vector3.new(x,1.35,z),Vector3.new(1.35,2.1,.95),r[3],false)
  local head=piece(figurine,"GuardianHead",Vector3.new(x,2.9,z),Vector3.new(1,1,1),Color3.fromRGB(247,217,166),false)
  head.Shape=r[4]
  local weapon=piece(figurine,"SignatureGear",Vector3.new(x+1,1.7,z),Vector3.new(.35,if variant==1 then 1.8 else 2.4,.5),Color3.fromRGB(243,222,160),false,Enum.Material.Metal)
  if i==4 then weapon.Shape=Enum.PartType.Ball end
  if i==6 then head.Shape=Enum.PartType.Ball end
  if variant==1 then plaque(stand,r[2].."\n守護兵 2種類",38) end
 end
end
world:SetAttribute("EGGRUMBLE_KioskPartCount",made)
print("[GQ805 SHOP KIOSK] Studio-only world preview ready; catalog and purchases external; parts",made)
