--!strict
-- GQ805: local read-only opening of the original #808 ShopView.
-- No fabricated wallet, no Client->Server Remote, no purchase callback or grant.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ProximityPromptService=game:GetService("ProximityPromptService")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
local busy=false
ProximityPromptService.PromptTriggered:Connect(function(prompt:ProximityPrompt)
 if prompt.Name~="GQ805_ShopReadOnlyPrompt" then return end
 local building=prompt:FindFirstAncestor("GQ805_LobbyGuildShop")
 if not building or building:GetAttribute("EGGRUMBLE_ShopPreviewOnly")~=true then return end
 if prompt.Parent==nil or not prompt:IsDescendantOf(workspace) then return end
 local ch=player.Character
 local root=ch and ch:FindFirstChild("HumanoidRootPart")
 local hum=ch and ch:FindFirstChildOfClass("Humanoid")
 if not root or not root:IsA("BasePart") or not hum or hum.Health<=0 then return end
 local door=prompt.Parent
 if not door:IsA("BasePart") or (root.Position-door.Position).Magnitude>13 then return end
 if player:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
 if busy then return end
 busy=true
 local folder=ReplicatedStorage:FindFirstChild("GQ805Shop")
 local cat=folder and folder:FindFirstChild("EGGRUMBLE_LobbyShopCatalog")
 local view=folder and folder:FindFirstChild("EGGRUMBLE_LobbyShopView")
 if not cat or not view or not cat:IsA("ModuleScript") or not view:IsA("ModuleScript") then
  warn("[GQ805 KIOSK] Original #808 Catalog/ShopView ModuleScript source not selected; keep purchases OFF")
  busy=false
  return
 end
 local ok,err=pcall(function()
  local Catalog=require(cat)
  local View=require(view)
  local snapshot={
   catalog=Catalog.list(),
   points="未接続",
   owned={[Catalog.freeStarter()]=true},
   robuxEnabled=false,
  }
  local gui=View.mount(player:WaitForChild("PlayerGui"),snapshot,nil)
  gui:SetAttribute("EGGRUMBLE_ReadOnlyPreview",true)
 end)
 if not ok then warn("[GQ805 KIOSK] read-only UI unavailable",err) end
 busy=false
end)
