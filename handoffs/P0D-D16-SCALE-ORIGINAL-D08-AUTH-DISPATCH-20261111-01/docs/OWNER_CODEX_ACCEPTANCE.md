# OWNER Windows Codex — D16 exact-original event dispatch compatibility and acceptance

**This is an optional future task, not a command that GitHub issue comments can execute on Windows.** Owner-direct Codex instruction is required. Do **not** interrupt or replace the current P0-D D07 S1 2-client safety QA which remains PARTIAL_NOT_READY.

## Immutable sources to verify independently

| Role | Immutable original/source commit | Interface |
|---|---|---|
| D16 authentic original | `584b11ef24cf3d44695d86b505207491bbd3844e` | `Core.new(matchId)` / `begin(state, matchId, eventId, kind, actorId, roster, nowSeconds)` / `advance` / `leave` / `close` / `snapshot` |
| D08 canonical event bridge original | `70dcc3b50129c288441452776360588184ca6c22` | single v40-approved `onWeatherActivate(envelope)` and `onCleanup` |
| D16 cleanroom V1/V2 gates **INCOMPATIBLE, DO NOT INSTALL WITH ORIGINAL** | `ac50372942712503f836fb84d6331ef3bcc4b8f2` / `1877222d4817153435bc5cfacdf1bb4e90d75aff` | call different CLEANROOM core `.new()` and `.begin(state,args)` / milliseconds |
| New original-compatible opt-in bridge | this package's committed SHA (see #218 delivery) | original core method signatures; no real visual renderer |

The upstream 22nd source helper commit `72fa23177c1fdce8433a9ecc565787d1ca5dcd6e` verifies the newly published original without adding it to the previous `21/21` Windows receipt. **Do not claim 22/22 Windows receipt until actual local SHA readback.**

## Required integration checks — source comparison first, NO-OP if already working

1. Re-read #218 top/newest, #217, #213 actual Windows evidence. Verify current PC HEAD/Place/source/QA/CHECKPOINT manifest and backup, compare against historical pinned SHA. Do not overwrite newer passing code.
2. Only after current priority D07 QA, verify exact D16 source and all manifest SHA. Select authentic original, not cleanroom, and compare current PC D08 weather consumer. If a true original-compatible dispatch already exists, document it and **do not** add this gate.
3. Inspect genuine D08 `onWeatherActivate` and `onCleanup` callback identity. Provide **reference-equality attestation** to this pure gate in the same server-owned callback chain; do not infer authority from `phase` or `kind` strings alone. Do not create a new RNG, event chooser, server heartbeat or `RemoteEvent` subscription. If current v40 callback calls this optional module and its weather subtype does not have a preapproved mapping, route it to the already-approved original handler rather than falsely returning failure to D08.
4. Owner explicitly confirms if, and only if, particular v40 weather subtypes should map to `GIANT_ONE` or `MINI_ALL`. The package ships **no** default mapping. Sample suggested mapping is intentionally omitted; do not guess from an English name. Without approval keep `enabled=false` and/or empty map.
5. Map `getTrustedRoster` to a genuine server ID list, 1–16 unique stable strings, not raw Player Instances or client Remote fields. `chooseTrustedGiantActor` chooses an actual roster ID; `mintServerEventId` returns a unique server ID. Ensure `readRound.now` is the *same server seconds time base* passed to original Core; do not convert to milliseconds or use client `os.clock()`.
6. Wire genuine round cleanup, owner stop and roster player leave; the existing game tick (if already approved) calls `:tick()`; `:snapshot()` is server-only and emits value-state only. D08 event `validUntil`, Core 8-second TTL, and round deadline all independently close effects. The visual renderer/replication contract is another integration decision — no scale visuals are generated in this module.
7. Run actual native Luau parse/require and isolated 2-client server tests: original `MINI_ALL` & `GIANT_ONE` mapping only if owner-approved, one 8s effect, correct `scaleMilli`, no actual hitbox/speed/HP change, no duplicated v40 events, no stale/yielding callback activation after cleanup, false client Remote rejected, invalid/stale match/epoch, reentrant duplicate, roster bounds, player leave, stop, round transition. Verify client visual source is separately authorized before showing effects.
8. Verify Studio Stop/Edit/Save, source and Place hashes, normal Studio PID exit. Preserve gate statuses separately: `22ND_ORIGINAL_SOURCE_RECEIPT`, `NATIVE_LUAU_PARSE`, `D08_DISPATCH_ORIGINAL_API`, `STUDIO_2CLIENT`, `MOBILE_EMULATOR`, `STUDIO_CLOSED_VERIFIED`; do **not** turn offline Python PASS into Studio PASS. Preserve protected GitHub PR/CAS/independent review gates and never upload private Place, user data or credentials.

## Non-goals and safety

No original recovery credit, no main edit/merge, no paid feature/Roblox production publish, no changes to P0-A/B/C CAS or existing automations. This source candidate must remain OFF by default until explicit real Windows approval. If CLEANROOM V1/V2 dispatch is present with the original D16 core, HOLD rather than silently adapt the mismatched APIs. Existing D07 boss test has precedence.
