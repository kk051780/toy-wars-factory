# Latest canonical successor — CANDIDATE-REAL62 (2026-11-19)

Owner #839 naming: Real62 means **62 selected Luau scripts**, never 62% completion.
Actual formal branch is `rc/p0d-s1-kids-rc01` Real59 private companion,
HEAD `38d11f0bf311491ba76fe03f818948e5d4b06889` (PR #829).
The legacy S1 active rich51 is NOT replaced. Candidate Real62 combines
**59/59 original current official Real59 HUD+Fog/Host/Swarm/Shop sources
byte-exact** with the 3 scoped scripts from PR #838, no other gameplay
authority, Remote or DataStore writer. A source-count increase does not
activate the private companion or enable live item trading.

`compose_real62.py` uses the proven #829 Real59 Place from run 44400478849,
plus exact official Real55 Place from run 44393525211, hard-checks both
immutable original 55 scripts, all current 59 sources/class/routes and four
original HUD/Fog author files, and composes an exact 59→62 selected project.
OFF59 rebuild is byte-exact. Dedicated candidate gate
`.github/workflows/gq8-trade-escrow-real62-hud-union.yml`, and formal
same-new-official-HEAD CI `.github/workflows/p0d-rc-eggrumble-v3-real62.yml`.
Formal release manifest `rc_fastlane/EGGRUMBLE_V3_REAL62.json` records
source locks and authenticated B #220 CAS requirements. Historic Real57/58
pipelines are manual-only to avoid stale a602 canonical fence failures.

Third added ModuleScript: `GQ8_TradeEscrowReducer.luau` implements a
pure two-account FREE_EARNED unique-instance protocol for a future verified
Store callback. PREPARE locks offered items, ESCROW isolates serialized
ownership, CREDIT inserts incoming items but keeps them unusable,
FINALIZE releases that hold only after durable global COMMIT.
It is executable in Native Luau with synthetic dual-profile crash/replay,
version, owner, paid-origin, duplicate-instance and cross-stage tests.
This is **not** a working transaction implementation: no known existing
Store has yet been verified to persist per-instance IDs or global trade
journal and session-lock epochs; the reducer is not wired to DataStore and
does not mutate real players. Roblox PolicyService and all age/region
rules, sender restrictions, reports, inventory UI, real two-client Studio,
Android 15min, visual/fun gates and Robux remain OFF/NOT_TESTED.

## Earlier Real57 historical branch design

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
