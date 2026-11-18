--!strict
-- GQ805 candidate lobby shop UI renderer; caller owns server snapshot & purchase callback.
-- Does not create remotes, call MarketplaceService, change currency or start purchases.
local Shop={}
local CATEGORIES={"GUARDIAN","WEAPON","ABILITY","BEAST","CASTLE","COSMETIC"}
local LABELS={GUARDIAN="守護兵",WEAPON="武器",ABILITY="能力",BEAST="魔獣",CASTLE="城",COSMETIC="装飾"}
function Shop.mount(parent:Instance,snapshot:any,onRequest:((string,string)->())?):ScreenGui
 assert(parent and parent:IsA("PlayerGui"),"shop is only a local PlayerGui renderer")
 assert(type(snapshot)=="table" and type(snapshot.catalog)=="table","trusted catalog snapshot required")
 local old=parent:FindFirstChild("EGGRUMBLE_LobbyShop")
 if old then old:Destroy() end
 local gui=Instance.new("ScreenGui")
 gui.Name="EGGRUMBLE_LobbyShop";gui.ResetOnSpawn=false;gui.Enabled=true;gui.DisplayOrder=20;gui.Parent=parent
 local frame=Instance.new("Frame")
 frame.Name="ShopWindow";frame.AnchorPoint=Vector2.new(.5,.5)
 frame.Position=UDim2.fromScale(.5,.5);frame.Size=UDim2.new(.9,0,.78,0)
 frame.BackgroundColor3=Color3.fromRGB(25,33,51);frame.BorderSizePixel=0;frame.Parent=gui
 local size=Instance.new("UISizeConstraint");size.MinSize=Vector2.new(240,260)
 size.MaxSize=Vector2.new(720,520);size.Parent=frame
 local corner=Instance.new("UICorner");corner.CornerRadius=UDim.new(0,14);corner.Parent=frame
 local title=Instance.new("TextLabel")
 title.BackgroundTransparency=1;title.Text="EGGRUMBLE ギルドショップ"
 title.Font=Enum.Font.GothamBold;title.TextScaled=true
 title.TextColor3=Color3.fromRGB(247,225,151)
 title.Size=UDim2.new(1,-52,0,42);title.Position=UDim2.fromOffset(12,5);title.Parent=frame
 local close=Instance.new("TextButton")
 close.Name="Close";close.Text="×";close.TextScaled=true;close.Font=Enum.Font.GothamBold
 close.Size=UDim2.fromOffset(35,35);close.Position=UDim2.new(1,-40,0,6);close.Parent=frame
 close.Activated:Connect(function() gui:Destroy() end)
 local balance=Instance.new("TextLabel")
 balance.BackgroundTransparency=1;balance.Font=Enum.Font.Gotham
 balance.TextScaled=true;balance.TextColor3=Color3.fromRGB(214,233,245)
 balance.Text="保有ポイント "..tostring(snapshot.points or 0).." BP"
 balance.Size=UDim2.new(1,-22,0,26);balance.Position=UDim2.fromOffset(11,48);balance.Parent=frame
 local tabs=Instance.new("ScrollingFrame")
 tabs.BackgroundTransparency=1;tabs.ScrollBarThickness=2;tabs.ScrollingDirection=Enum.ScrollingDirection.X
 tabs.CanvasSize=UDim2.fromOffset(600,0);tabs.Size=UDim2.new(1,-22,0,40)
 tabs.Position=UDim2.fromOffset(11,78);tabs.Parent=frame
 local list=Instance.new("UIListLayout");list.FillDirection=Enum.FillDirection.Horizontal
 list.SortOrder=Enum.SortOrder.LayoutOrder;list.Padding=UDim.new(0,6);list.Parent=tabs
 local products=Instance.new("ScrollingFrame")
 products.Name="Products";products.Size=UDim2.new(1,-22,1,-132)
 products.Position=UDim2.fromOffset(11,120);products.BackgroundTransparency=1
 products.CanvasSize=UDim2.fromOffset(0,0);products.AutomaticCanvasSize=Enum.AutomaticSize.Y
 products.ScrollBarThickness=4;products.Parent=frame
 local layout=Instance.new("UIListLayout")
 layout.Padding=UDim.new(0,6);layout.SortOrder=Enum.SortOrder.LayoutOrder
 layout.Parent=products
 local function render(category:string)
  for _,item in ipairs(products:GetChildren()) do if item~=layout then item:Destroy() end end
  for _,entry in ipairs(snapshot.catalog) do
   if entry.category==category then
    local card=Instance.new("Frame")
    card.Size=UDim2.new(1,-6,0,94);card.BackgroundColor3=Color3.fromRGB(40,52,72)
    card.BorderSizePixel=0;card.Parent=products
    local name=Instance.new("TextLabel");name.Text=entry.label
    name.Font=Enum.Font.GothamBold;name.TextColor3=Color3.fromRGB(242,242,246)
    name.BackgroundTransparency=1;name.TextScaled=true
    name.TextXAlignment=Enum.TextXAlignment.Left
    name.Position=UDim2.fromOffset(8,4);name.Size=UDim2.new(1,-145,0,35);name.Parent=card
    local details=Instance.new("TextLabel")
    details.BackgroundTransparency=1;details.TextScaled=true
    details.TextXAlignment=Enum.TextXAlignment.Left;details.Font=Enum.Font.Gotham
    details.TextColor3=Color3.fromRGB(196,212,230)
    details.Text= tostring(entry.personality or entry.category).." ・ "..tostring(entry.battlePoints).."BP"
    details.Position=UDim2.fromOffset(8,41);details.Size=UDim2.new(1,-145,0,25);details.Parent=card
    local buy=Instance.new("TextButton")
    buy.Text=if snapshot.owned and snapshot.owned[entry.id] then "所有済" else "BP購入"
    buy.Font=Enum.Font.GothamBold;buy.TextScaled=true
    buy.Size=UDim2.fromOffset(112,30);buy.Position=UDim2.new(1,-118,0,12)
    buy.Parent=card
    buy.Active=onRequest~=nil and not (snapshot.owned and snapshot.owned[entry.id])
    buy.AutoButtonColor=buy.Active
    buy.Activated:Connect(function()
     if onRequest and buy.Active then onRequest(entry.id,"BP") end
    end)
    -- Real Roblox product IDs/prices must be supplied by the server. Disabled by default.
    local robux=Instance.new("TextButton")
    robux.Name="RobuxPurchase"
    local productConfigured=snapshot.robuxEnabled==true and
      type(entry.robuxProductId)=="number" and entry.robuxProductId>0
    robux.Text=if productConfigured then "Robux購入" else "Robux準備中"
    robux.Font=Enum.Font.GothamBold;robux.TextScaled=true
    robux.Size=UDim2.fromOffset(112,30);robux.Position=UDim2.new(1,-118,0,51)
    robux.Parent=card
    robux.Active=productConfigured and onRequest~=nil and
      not (snapshot.owned and snapshot.owned[entry.id])
    robux.AutoButtonColor=robux.Active
    robux.Activated:Connect(function()
     if onRequest and robux.Active then onRequest(entry.id,"ROBUX") end
    end)
   end
  end
 end
 for i,category in ipairs(CATEGORIES) do
  local tab=Instance.new("TextButton")
  tab.LayoutOrder=i;tab.Text=LABELS[category] or category;tab.Font=Enum.Font.GothamBold
  tab.TextScaled=true;tab.Size=UDim2.fromOffset(88,34);tab.Parent=tabs
  tab.Activated:Connect(function() render(category) end)
 end
 render("GUARDIAN")
 return gui
end
return Shop
