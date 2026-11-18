from pathlib import Path
import re
R=Path(__file__).parent
server=(R/"GQ805_LobbyGuildShop.server.luau").read_text()
client=(R/"GQ805_ShopKioskClient.client.luau").read_text()
assert "GQ805_LobbyGuildShop" in server and "GQ805_ShopReadOnlyPrompt" in server
assert "for variant=1,2" in server and "for i,r in ipairs(roles)" in server
assert "ProximityPromptService.PromptTriggered" in client
assert 'Catalog.list()' in client and 'View.mount(' in client
assert 'points="未接続"' in client and "robuxEnabled=false" in client
assert "nil)" in client and 'cat:IsA("ModuleScript")' in client and 'view:IsA("ModuleScript")' in client
for forbidden in ("MarketplaceService","DataStoreService","RemoteEvent","ProcessReceipt","PromptProductPurchase","TakeDamage(","Humanoid.Health=","SetAsync(","UpdateAsync("):
    assert forbidden not in server+client,forbidden
assert "if not RunService:IsStudio() then return end" in server
assert "if not RunService:IsStudio() then return end" in client
print("GQ805_READONLY_3D_KIOSK_PYTHON_CONTRACT_PASS")
