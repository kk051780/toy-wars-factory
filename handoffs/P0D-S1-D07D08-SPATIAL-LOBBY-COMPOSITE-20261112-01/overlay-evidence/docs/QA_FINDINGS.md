# Independent preintegration QA and remaining proof

Status: TWO_SOURCE_CORRECTIONS_WRITTEN / NOT_INTEGRATED_RC / NATIVE_LUAU_NOT_TESTED / 2CLIENT_NOT_TESTED.

## Actual source evidence

The full source from `4b66dd8a9b34a45cf12e58684e0e4372df3f8b07` was read as Git blobs. V40 original Core classifies rolls 0..64 as NORMAL and sets DONE; original CanonicalEventBridge retires successful rounds with `self.current=nil` and a retired match:epoch key; original NEW Host polls the bridge again and mishandles the next rejection. Host fix checks BOTH D08 retirement and `bridge.enabled=true`, cleans up, and returns stable terminal success only for same currently ACTIVE Game serial. Genuine D08 error/failure returns false as before. The original D07 Binding generates target IDs with `tostring(Player.UserId)` but its resolver accepts only positive digits; revised lookup uses exact server Players identity and rejects aliases/duplicated identities.

## Source-only evidence from this chat

45/45 JS static+boundary-model checks PASS against actual revised Luau Git blobs and original source. Cases include v40 roll boundary 0/64/65/89/90/99; active/inactive terminal Game status; first terminal success, future same-round repeat, replay/unknown terminal and disabled bridge; positive/Studio-negative Player IDs, malicious malformed IDs, padding, unknown IDs, and duplicate server roster. This **does NOT** prove Lua runtime parse, Roblox physical boss stomp, lag timing, real CPU load, or S1 release.

## Essential integration QA blockers

- The sole #220 RC branch was still initial `35d7d0525388e885aac8281eff2315a59831e0cf` at this review and does not contain the Game/HUD/D07/D08 complete candidate.
- The new complete candidate has both the runtime opt-in gates set to `false` as designed. It is not a running boss until explicit reviewed private enablement.
- Source plan and assembly receipt pinned to the OLD two Luau source hashes must be regenerated for any patched composite. A source patch is not a receipt.
- Original recovered D07 gameplay code and true Studio client/player/visual synchronization still require real native validation. Re-test red/blue telegraph symmetry, attack duplicate receipts, boundary LOS, spawn immunity and normal Studio stop/exit.
- The old initial S1 source manifest bug was resolved only in separate isolated handoff; the sole RC needs its own genuine canonical manifest commit after integration.
