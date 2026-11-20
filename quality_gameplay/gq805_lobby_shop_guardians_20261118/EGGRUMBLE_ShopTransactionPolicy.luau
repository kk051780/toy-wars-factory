--!strict
-- GQ805: pure shop check + proposal; NEVER a wallet, receipt processor, Remote, purchase prompt or grant.
local Catalog=require("./EGGRUMBLE_LobbyShopCatalog")
local M={}
local function validNum(n:any):boolean
 return type(n)=="number" and n==n and n>=0 and n~=math.huge and n~=-math.huge and n==math.floor(n)
end
function M.request(state:any,req:any):any
 if type(state)~="table" or type(req)~="table" then return nil end
 if state.serverAuthorized~=true or state.phase~="LOBBY" or state.profileLoaded~=true
   or state.accountEligible~=true or state.walletAvailable~=true then return nil end
 if type(state.userId)~="string" or type(req.userId)~="string" or state.userId~=req.userId then return nil end
 local e=Catalog.get(req.itemId)
 if not e or state.owned and state.owned[e.id]==true then return nil end
 if e.role~="ANY" and state.role~=e.role then return nil end
 if not Catalog.tier(state.level) then return nil end
 if req.currency=="BP" then
  if not validNum(state.points) or state.points<e.battlePoints then return nil end
  if type(req.uniqueOrderId)~="string" or #req.uniqueOrderId<8 then return nil end
  -- persistent Store must CAS balance + ownership in ONE transaction, checking replay key.
  return {kind="BP_PURCHASE_PERMIT",userId=state.userId,itemId=e.id,
   orderId=req.uniqueOrderId,pointsToSubtract=e.battlePoints,
   proposedBalance=state.points-e.battlePoints,
   requiresAtomicStore=true,requiresIdempotentOrder=true}
 elseif req.currency=="ROBUX" then
  -- Never guess a Roblox product ID, platform Robux price, or grant on button callback.
  if not validNum(e.robuxProductId) or e.robuxProductId==0 then
   return {kind="ROBUX_NOT_CONFIGURED",itemId=e.id,serverGrantsNothing=true}
  end
  return {kind="ROBUX_PLATFORM_PROMPT_ONLY",itemId=e.id,productId=e.robuxProductId,
   requireSingleProcessReceipt=true,grantOnReceiptOnly=true,requirePurchaseIdIdempotence=true}
 end
 return nil
end
return M
