# P0-D D07 – Gorogan Combined Server Wiring (reference only)

New **standalone server-only** `GoroganCombinedRuntime.luau` reuses four previously delivered modules without modifying their logic: `GoroganServerAICore`, `GoroganRigDriver`, `GoroganDamageBoundary` and `GoroganAttackReceiptWindow`. The client's independent `GoroganVisualPolicy/Prefab` remains unchanged. Existing `GoroganServerRuntime` is **NOT** to run simultaneously with this adapter.

Why this packet exists: the original AI Runtime omitted the `now` argument required by the new navigation driver and did not itself open/close the server attack receipt window or stop the physical rig/damage gate. This packet supplies those cross-module contracts, anchored to a single authoritative v40 ACTIVATE.

**Only a reference:** Requires the PC's real RoundCoordinator, true canonical event identity, server round epoch, trusted stage anchor, server roster/Humanoids, Roblox pathfinding, a physically moving R6 NPC and an unpublished Studio. `integrationApproved=true` is not proof of server authenticity. No real PC source/Place has been inspected by this packet; code has not been executed in Roblox Studio or Luau VM.

Read `docs/CODEX_INTEGRATION.md` before considering integration. **One** boss scheduler and **one** damage pipeline only; no client Remote may invoke the adapter. The v43-A S1 capture functionality is independently verified by PC; keep its owner/epoch logic intact.

Offline developer tests: `python -m unittest discover -s tests -q` (independent Python oracle + Luau static checks + ZIP failure tests). Read-only ZIP verifier: `python tools/verify_packet.py <ZIP_PATH>`. Neither is Studio QA.

Public GitHub repository has only AES-GCM ciphertext and an unclassified README. The AES key is delivered to OWNER in a separate private conversation; never upload it to Issues, GitHub repo, CI or automation prompts. All main/merge/Roblox publish/payment/extra spend actions remain forbidden.
