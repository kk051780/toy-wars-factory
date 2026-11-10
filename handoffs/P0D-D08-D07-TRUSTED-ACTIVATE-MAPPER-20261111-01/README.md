# TRAP RAIDERS — D08 to D07 trusted ACTIVATE mapper (keyless, opt-in)

- `game_id`: `TRAP_RAIDERS`
- `work_id`: `p0d-siege-v19`
- `packet_id`: `P0D-D08-D07-TRUSTED-ACTIVATE-MAPPER-20261111-01`
- `delivery_mode`: OWNER-approved `PUBLIC_SOURCE_V1` under Issue [#218](https://github.com/kk051780/toy-wars-factory/issues/218), *not an old encrypted source recovery*.

## Why this exists

These are five already-public, already-keyless original-source packets. They are not to be re-uploaded or edited in this package:

| Original | Immutable commit |
| --- | --- |
| D08 canonical v40 single-event bridge | `70dcc3b50129c288441452776360588184ca6c22` |
| D07 Gorogan combined runtime | `80a1f0ce15adfb475df0c95677f9966bb760a8ae` |
| D07 Gorogan server AI | `d65adccef6ce08ec48854ff2cc99f77e69e0765e` |
| D07 Gorogan server physical rig/damage/receipt | `14935dca217391a7d82d809a3856ee602c446704` |
| D07 Gorogan client visual | `e9b0a7496a69bda3e0e6527ff4d112d50cf70e80` |

D08 `CanonicalEventBridge` supplies an `onBossActivate` envelope with `{phase,stage,validUntil,kind,subtype,matchId,epoch}`. D07 `GoroganCombinedRuntime:start()` requires `{event="ACTIVATE",kind="BOSS",subtype="GOROGAN",matchId,untilAt}` and an independently verified `deps.isCanonicalActivation`. Blindly passing a D08 envelope to D07 will reject legitimate activation.

This package supplies **one small, off-by-default, server-only conversion boundary**. It uses genuine server RoundCoordinator match/stage/epoch/clock/deadline and exactly-one activation per match+epoch. It passes **the exact newly created table instance** to D07, and attests that table's identity only during the currently executing server callback; a look-alike/client-provided table does not pass. It rejects the wrong stage, weather, replay, short lifespan, stale epoch, expired callback, clock reversal and re-entrant delivery. A failed or stale/throwing start requires confirmed owner `abortCombined()`; failure to confirm abort is a critical disabled state, not success.

It **does not** make another event scheduler/RNG/AI/humanoid rig/real damage/visual prefab/RemoteEvent, and it does not change the actual OWNER Windows PC game. It cannot prove the origin of its own input by inspecting a table; security requires it to be wired as a direct **server-only** `onBossActivate` callback **inside the already-approved D08 bridge**, never exposed to a RemoteEvent or client. Its callback equality is a supplementary anti-forgery gate, not a replacement for source-provenance review.

## Contents

`luau/TrustedGoroganActivationMapper.luau` is the real new implementation. `tests/oracle.py` and `tests/test_mapper.py` model its state semantics with 35 stdlib Python tests. `docs/OWNER_CODEX_QA.md` is the Windows implementation gate. `BUILD_MANIFEST.json` records byte size and SHA-256 of all four files. No source is encrypted; no password or key is necessary.

## Independent Windows Codex integration (not auto-authorized)

Preserve the latest PC real Place/HEAD/CHECKPOINT/source SHA and the proven 21/21 source receipt. Compare this candidate with the newest actual PC code. **Do nothing if PC already has a working single trusted mapper.** If genuinely missing, install in an isolated/unpublished test Place only and wire as follows, *not into the real game by copying this pseudocode blindly*:

```lua
-- SERVER-only wiring sketch after trusted callback verification; not a second D08 bridge.
local mapper -- must be initialized before any event is emitted
local combined = Combined.new({
    -- All existing D07 dependencies must be supplied from reviewed server objects.
    isCanonicalActivation = function(a) return mapper:isCanonicalActivation(a) end,
    -- ... all remaining required D07 dependencies unchanged ...
})
mapper = Mapper.new({
    enabled = false, -- change ONLY after actual OWNER-approved native Luau/Studio review
    approvedByOwner = false,
    readRound = function() return RoundCoordinator.readTrustedRound() end,
    startCombined = function(a) return combined:start(a) end,
    abortCombined = function(roundId)
        local a = combined.active -- example only, verify actual PC version
        if not a or a.roundId ~= roundId then return true end
        local stopped = combined:stop(a.roundId, a.eventId)
        return stopped == true
    end,
})
-- Configure this as the already-reviewed D08 bridge's ONLY boss callback:
-- onBossActivate = function(d08Envelope) return mapper:handle(d08Envelope) end
```

**Never** install `GoroganServerRuntime` and `GoroganCombinedRuntime` together, create two D08 selectors, or trust a client-supplied activation. The PC integrator must independently supply D07 `mintServerEventId`, ground anchor, genuine callback receipt and damage checks. A correct mapping does **not** complete D07 combat, client visual tracking, damage/telegraph, or Studio QA.

## Reported check boundaries

- Local Python reference/unittest: **35/35 PASS** (including mutable round snapshot on callback yield, after-callback expiry, abort fail-closed, source static contract).
- Native Luau parse / Roblox Studio 2 clients / phone / PC integration / normal Studio exit: **NOT_TESTED**.
- Old original-source migration count: unchanged **21**, because this is a NEW interoperability candidate.
- No `main`/merge/Roblox public publish/billing/P0-A/B/C or active-automation changes.
