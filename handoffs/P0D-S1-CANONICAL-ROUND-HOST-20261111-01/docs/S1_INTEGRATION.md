# S1 D08/D07 canonical round-host integration (opt-in, not yet in playable RC)

Game: TRAP_RAIDERS; work: p0d-siege-v19. Owner sole integrated game: #220.
This is NEW S1 glue, not a replacement implementation of D07 or D08. It
physically includes eight byte-preserved original Luau modules and one new
`S1CanonicalRoundHost.luau`. ALL code is source-only until the #220 sole
integrator reviews and wires it.

## Exact original sources reused

- v40 `ChaosEventCore` from SHA `3c40c7dd80e6ec134f3124b6a6a0f625951792f4`
- original `CanonicalEventBridge` from `70dcc3b50129c288441452776360588184ca6c22`
- approved-envelope-identity `TrustedGoroganActivationMapper` from `d3159f9b5369ff28163a92ffc8123f4f3e816631`
- original D07 `GoroganCombinedRuntime` from `80a1f0ce15adfb475df0c95677f9966bb760a8ae`
- original AI `GoroganServerAICore` from `d65adccef6ce08ec48854ff2cc99f77e69e0765e`
- D07 physical `GoroganRigDriver`, `GoroganDamageBoundary` and `GoroganAttackReceiptWindow` from `14935dca217391a7d82d809a3856ee602c446704`.

Do not include earlier cleanroom AI, second v40 event selector, old D08-D16 gate,
or extra RigDriver in the same running game. The immutable source blobs are
independently re-hashed by tests; a copy is NOT active merely because it is
present in the repository.

## Actual S1 integration prerequisites

1. Single writer #220 controls `Game.server.luau`; update ONLY its newest own
   source. It already owns `match.serial`, `match.startedAt`,
   `match.deadline`, `match.phase`, `match.alarm`, `match.alarmUntil`,
   `serverNow` and the single `TrapRaidersS1Remote`.
2. Copy the nine `src/*.luau` files to the same ServerScriptService
   module folder, then explicitly add their nine unique entries to the
   Rojo server module tree. Do NOT map `CanonicalEventServerAdapter.server.luau`
   or a second server Script. No other script should auto-start events.
3. Remove the **entire original fake alarm scheduler** (original current
   `match.nextAlarmAt`, IDLE->WARNING->SIGNAL->IDLE at 55/62 sec). Retain
   only the existing HUD snapshot fields; the SINGLE original
   `CanonicalEventBridge` is the chooser/phase owner when enabled.
4. After `resetRound` creates a fresh ACTIVE `match.serial`, create **one**
   Host from server-owned callbacks. After `stopRound` call `host:stop()`,
   and from the existing `tickRound` active branch call `host:tick()`.
   NO secondary `while`, `Heartbeat`, `task.spawn` or Remote receiver.
5. Host is DISABLED unless both `approvedByOwner=true` and
   `enableCanonicalS1=true` are supplied. These are explicit trusted
   server-only integrator decisions. Never read them from client packets.
6. The integrator must provide `makeCombined(mapper)` constructing
   the actual `GoroganCombinedRuntime.new(deps)` with approved
   `integrationApproved=true`, `deps.isCanonicalActivation(activation)`
   returning `mapper:isCanonicalActivation(activation)`, authentic
   Driver/DamageBoundary/ReceiptWindow, authoritative roster, LOS, safe
   zone, damage-window and existing match-clock callbacks.
7. The integrator MUST supply `abortCombined(roundId)` that genuinely
   stops the physical boss rig and disarms damage after a partial/yielding
   D07 start; returning true from a no-op is unsafe. It must work even
   after an incomplete start, not only after `combinedActive` becomes true.
8. `setAlarm(state,untilAt,epoch)` owns the existing match HUD state.
   If epoch no longer matches match.serial, it must perform **no
   mutation** and return true (safe stale-clear acknowledgement).
   `broadcast()` sends the usual SERVER-owned snapshot to both sides.
   Both callbacks may return false on genuine failure. Do not send a
   new Remote event or source client damage.
9. The existing single host receives a server-only `serverRoll` function
   returning an integer 0..99. Original D08 calls it at most once
   per round after +20 seconds. Host does not create another RNG.
   WEATHER without a reviewed runtime fails closed before an unfulfillable
   visual warning. This is a known gap, not "weather integrated".
10. At original match serial 1024 the recovered D08 epoch contract
    rejects new games; the owner must design an authenticated epoch
    strategy before live production. Never silently wrap/reuse an old
    epoch in a running server.

### Example shape (non-runnable until real D07 safety callbacks are supplied)

```lua
local Host = require(script.Parent:WaitForChild("S1CanonicalRoundHost"))
-- In the ONE existing S1 resetRound, AFTER serial/clock setup:
host = Host.new({
    approvedByOwner = RELEASE_REVIEW_APPROVED,
    enableCanonicalS1 = CANONICAL_S1_ENABLED,
    readMatch = function() return match end,
    serverTime = serverNow,
    serverRoll = function(_matchId, _epoch)
        return math.random(0, 99) -- SERVER only, not a second scheduler
    end,
    setAlarm = function(state, untilAt, epoch)
        if match.serial ~= epoch then return true end
        match.alarm, match.alarmUntil = state, untilAt
        return true
    end,
    broadcast = broadcast,
    makeCombined = function(mapper)
        -- Return actual original Combined.new with server-authenticated
        -- isCanonicalActivation = function(a)
        --   return mapper:isCanonicalActivation(a)
        -- end and existing approved genuine D07 driver/damage callbacks.
        error("REQUIRED_REAL_D07_DAMAGE_RIG_WIRING_NOT_DONE")
    end,
    abortCombined = function(_roundId)
        error("REQUIRED_REAL_D07_BOSS_ABORT_BOUNDARY_NOT_DONE")
    end,
})
-- In ONE tickRound ACTIVE path after existing match checks: host:tick()
-- In stopRound and final exit: host:stop("ROUND_END")
```

This example intentionally fails until owner supplies real D07 callbacks.
No fake activation, no bypassing `Mapper:isCanonicalActivation`, and NO
owner-approval implied by a Chat-authored source package.

## Validation and limits

The included Python tests verify eight original Git object SHAs plus the
new host's explicit static safety constraints. They DO NOT execute Luau,
Roblox physics, pathfinding, real 2-client/phone input or real server rolls.
A read-only GitHub Actions workflow runs them against the immutable source.
Original S1 initial source 80/80 offline tests were passed in separate CI,
but those tests do NOT demonstrate this host has been game-integrated.
S1 original v43-A Windows/PC source and Place are separate from this new
Chat-built S1 initial Game. This pack does not modify either.

Once the #220 integrator completes genuine wiring, make a NEW full S1
source SHA, regenerate strict PUBLIC_SOURCE_V1 manifest, actual assembly plan,
Python receipt and independent source+gameplay QA before OWNER final Studio.
The initial public Roblox release, paid features and production publish
remain separately OWNER-authorized; none happened here.
