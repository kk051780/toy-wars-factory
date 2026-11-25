#!/usr/bin/env python3
"""Fast adversarial contract checks. Full 48/50 native and Rojo runs in dedicated CI."""
from pathlib import Path
import ast,sys,tempfile,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compose_social50 import ROUTES
root=Path(__file__).parent
assert len(ROUTES)==2
plaza=(root/"GQ8_LobbySocialPlaza.server.luau").read_text()
trade=(root/"GQ8_TradePolicy.luau").read_text()
for word in ('RunService:IsStudio()','GQ8_TradeSettlementDisabled','GQ8_TradeExplanation','GQ8_PhotoOptIn','MeetingRug_'):
    assert word in plaza,word
for word in ("function M.new(","function M.setOffer(","function M.lock(","function M.confirm(","function M.proposeSettlement(","function M.cancel(","item.version","ownerUserId","tradeable","REVISION_MISMATCH","REVIEW_COUNTDOWN","INVENTORY_CHANGED","requiresExistingStoreAtomicJournal","DUPLICATE_GLOBAL_INSTANCE","paidOrigin==true","EGG=true"):
    assert word in trade,word
for forbidden in ("RemoteEvent","DataStoreService","ProcessReceipt","PromptProductPurchase","FireServer(","MarketplaceService","SetAsync(","UpdateAsync("):
    assert forbidden not in plaza+trade,forbidden
assert 'trade.finished=true' in trade
print("GQ8_SOCIAL_AND_TRADE_NO_AUTHORITY_STATIC_NEGATIVE_TESTS_PASS")
