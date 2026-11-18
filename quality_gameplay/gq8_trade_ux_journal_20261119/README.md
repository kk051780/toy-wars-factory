# EGGRUMBLE Trade UX + durable-journal contract (Real55→57)
Feature: GQ8_TRADE_UX_JOURNAL_20261119. Official RC parent HEAD a6020867fac80fa3b2ca47478625873fc6f3678e (#834), profile eggrumble_v3_real55.

This is a nonoverlap successor of the **existing** Real55 trade policy and 3D lobby from PR #831. Do NOT re-author #831, #826, #808, #816, gameplay Host/Swarm/Store, or official RC branch. Two NEW source routes only:
- StarterPlayer/StarterPlayerScripts/GQ8_TradeReview (LocalScript) opens an accessible 2-column *read-only, Studio-only* trade explanation with category tabs from existing GQ8_TradeExplanation prompt, clear disabled confirm.
- ServerScriptService/GQ8_TradeJournalContract (ModuleScript) is a native-testable 7-step durable receipt state-machine CONTRACT. It never reads or writes player inventory, DataStore, Remote, or Marketplace; it only consumes attested receipts passed by trusted Store code.

Journal stages: PREPARE_A / PREPARE_B / ESCROW_A / ESCROW_B / CREDIT_A / CREDIT_B / COMMIT. Before escrow, cancellation is possible; once escrow begins a future Store must resume recovery until a durable commit, not falsely refund or release items. Must hold session locks for both players and a durable global trade ledger, ensuring no minted/duplicated items across a crash. Never trust client-supplied receipt flags or item ownership. The sample code deliberately does not pretend to make two UpdateAsync calls into an atomic multi-key transaction.

Existing old 55 source remains byte-identical. New candidate builds a reversible 57-source private artifact; OFF55 is original exact 55-source Place. Trade item transfer, profile persistence, tradable inventory, escrow writes, two-client final trade, and Roblox production are NOT connected. New storefront UI is a mock review screen, no item grant. External PaidItemTrading must be checked per player by PolicyService.GetPolicyInfoForPlayerAsync in the real Store, and defaults disabled.

Roblox references:
- https://create.roblox.com/docs/cloud-services/data-stores/player-data-purchasing
- https://create.roblox.com/docs/scripting/security/client-server-boundary
- https://create.roblox.com/docs/reference/engine/classes/PolicyService/GetPolicyInfoForPlayerAsync

Requirements for accepting formal RC: #220 authenticated nonforce fresh expectedSha CAS, same HEAD Native Luau/VM, Rojo Class/Source, OFF55 byte-identical, receipts / artifact bytes / rollback. Studio2-client and Android 15-min plus kid FUN separately not tested.
