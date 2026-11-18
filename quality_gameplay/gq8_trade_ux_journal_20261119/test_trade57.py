#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).parent
s=(p/"GQ8_TradeJournalContract.luau").read_text()
ui=(p/"GQ8_TradeReview.client.luau").read_text()
for a in ("PREPARE_A","PREPARE_B","ESCROW_A","ESCROW_B","CREDIT_A","CREDIT_B","COMMIT",
          "ESCROW_RECOVERY_REQUIRED","IDEMPOTENT_REPLAY","REPLAY_CONFLICT",
          "requiresExistingStoreAtomicJournal","storeWriterAttested"):
 assert a in s,a
for a in ('RunService:IsStudio()','ProximityPromptService','GQ8_TradeExplanation',
          'GQ8_TradeReviewPreview','disabled.Active=false','交換を確定（未接続）',
          'gui.Enabled=false','Activated:Connect'):
 assert a in ui,a
for prohibited in ('DataStoreService','MarketplaceService','ProcessReceipt','RemoteEvent','FireServer(','UpdateAsync(','SetAsync('):
 assert prohibited not in s+ui,prohibited
print("GQ8_TRADE57_NO_AUTHORITY_NO_PAYMENT_PREVIEW_AND_JOURNAL_STATIC_PASS")
