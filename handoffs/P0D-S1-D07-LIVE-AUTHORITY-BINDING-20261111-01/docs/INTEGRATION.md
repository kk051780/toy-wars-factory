# S1 Gorogan physical server-authority binding — owner integration recipe

Feature `TRAP_RAIDERS / p0d-siege-v19`. This is a REAL new Luau server
callback-factory for the eight unchanged historical D07/D08 modules already
in the earlier source packet, not a new boss AI or event scheduler.
The only current #220 game source remains `35d7d0525388e885aac8281eff2315a59831e0cf`.
The combined NEW host+binding is not yet integrated into the sole-writer RC.

## Dependency lock and copy layout

On an isolated checked-out handoff branch, use both source roots:

- Host+eight byte-preserved ORIGINAL modules:
  `handoffs/P0D-S1-CANONICAL-ROUND-HOST-20261111-01/src/`
  at exact commit `aeb6aa748c70be2fab8e652ad6623d1b2c3989c6`
  (same physical original module Git blobs survive unchanged in this branch).
- This one NEW binding:
  `handoffs/P0D-S1-D07-LIVE-AUTHORITY-BINDING-20261111-01/src/S1GoroganLiveBindings.luau`
- The genuine game map/authority:
  `releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau` at original SHA
  `35d7d0525388e885aac8281eff2315a59831e0cf`.

Only the #220 SINGLE Chat integrator decides inclusion. If selected, copy all
NINE host/original modules plus this ONE new binding as sibling ModuleScripts
under existing `TrapRaidersS1` ServerScriptService tree. Do not copy a second
server `*.server.luau`, event scheduler, AI, rig driver or Remote.

## Trusted Game owner API

After the original `resetRound()` establishes a fresh `match.serial`
ACTIVE epoch, construct `Binding.new(deps)` with:

- `approvedByOwner=true` and `map=map`, the original map Folder
  `TRAP_RAIDERS_S1`; S1 stage and boss anchor (0,0,0) ONLY;
- `readMatch=function() return match end`, `serverTime=serverNow`;
- `getPlayerTeam=getTeamName` from existing server team instances,
  never from Remote payload;
- `getInvulnerableUntil=function(p) return invulnUntil[p] or 0 end`,
  from the original server-owned respawn immunity map;
- `sendBossVisual=function(packet) ... end`, a carefully bounded trusted
  SERVER emitter to each team using the existing unique
  `TrapRaidersS1Remote`, returning true only after dispatch. The current
  HUD does **not** render these boss packets; this is a **separate P0**
  UI visibility / synchronized WARNING–STOMP test gate before release.

Then construct exactly ONE previous `S1CanonicalRoundHost.new(...)`:

```lua
local Binding = require(script.Parent:WaitForChild("S1GoroganLiveBindings"))
local Host = require(script.Parent:WaitForChild("S1CanonicalRoundHost"))
-- These examples are deliberately server-only. Owner must actually select
-- a complete game integration with real release permission gates.
local binding = Binding.new({
    approvedByOwner = true, readMatch = function() return match end,
    serverTime = serverNow, map = map,
    getPlayerTeam = getTeamName,
    getInvulnerableUntil = function(p) return invulnUntil[p] or 0 end,
    sendBossVisual = function(packet)
        -- REVIEW FIRST: emit packet to RED and BLUE through existing Remote,
        -- AND implement client WARN/STOMP visibility with shared deadline.
        -- Merely returning true here without emitting is FORBIDDEN.
        error("REQUIRES_VERIFIED_REPLICATED_BOSS_VISUAL")
    end,
})
host = Host.new({
    approvedByOwner = true, enableCanonicalS1 = true,
    readMatch = function() return match end, serverTime = serverNow,
    serverRoll = function(_id, _epoch) return math.random(0, 99) end,
    makeCombined = function(mapper) return binding:makeCombined(mapper) end,
    abortCombined = function(id) return binding:abort(id) end,
    setAlarm = function(state, untilAt, epoch)
        if match.serial ~= epoch then return true end
        match.alarm = state
        match.alarmUntil = untilAt
        return true
    end,
    broadcast = broadcast,
})
```

The previous Host is disabled without explicit reviewed `approvedByOwner`
AND `enableCanonicalS1`. This example deliberately crashes at boss visual
dispatch, never silently claims to show a warning or hit.

**Must change in one-owner Game.source only after review:** remove the
ENTIRE fake `nextAlarmAt` 55/62 second IDLE→WARNING→SIGNAL cosmetic
scheduler, because genuine original v40/D08 becomes the ONE canonical chooser.
Call `host:tick()` ONLY inside existing `tickRound` loop, not another
RunService or while loop. On `stopRound` call `host:stop()` even when
the match has left ACTIVE; on any server cleanup stop/abort before creating
another match. Never enable two event schedulers.

D07 server-only original Combined runtime validates the unique
server-minted event token with exact `mapper:isCanonicalActivation()`
table identity. This NEW binding supplies legitimate S1 callbacks:
- Players:GetPlayers roster, per-player HumanoidRootPart/Health,
  integer user ID and server team; no client-selected boss target;
- S1 map center ground probe and path safety, actual physical rig server
  ownership; one eventId `G07_<round serial>`;
- true world obstruction Raycast, spawn-position safety and server
  respawn invulnerability; original Gate revalidates those at hit time;
- original AttackReceiptWindow opens only for real Core STOMP_RESOLVE,
  and Gate uniquely attests an attackId/target before Humanoid:TakeDamage;
- `abortCombined` attempts Combined.stop, Window.close, Gate.stop and
  physical Driver.stop, then fails if Combined/gate/rig remain active;
  stale round/event ID never authorizes new damage.

## Explicit blockers and limits

1. **STUDIO NOT TESTED** for this new binding. Only offline structural/negative
   contract tests are provided; not a Luau parser or Roblox physics run.
2. D07 `GoroganRigDriver` has genuine PathfindingService and Humanoid,
   so actual navigation/hits and 2-team synchronized visual telegraph must
   be proven using final OWNER-directed Studio QA.
3. D08 original 10% weather is NOT implemented here; original D08 bridge
   fails closed rather than advertising a nonexistent event.
4. Boss TTL original D07 14s vs original D08 v40 17s; verify early rig
   cleanup and no lingering SIGNAL as part of real gameplay QA.
5. Original D08 server epoch accepts only 1..1023 in this integration.
   A long-lived server needs a reviewed non-replay session strategy before
   production, not silent wrap.
6. If `sendBossVisual` fails, the existing CombinedRuntime MUST abort
   its partially spawned rig and disarm Gate. This binding cannot certify
   Roblox display or guaranteed network delivery.
7. New S1 initial source has no authenticated full D11 neutral gameplay,
   valid 2-player final studio logs, or real user retention/revenue.
8. The strictly canonical S1 PUBLIC_SOURCE_V1 manifest fix is available
   separately at `090646d8ec7bd2522a8d2b6798454fcc1b58ba13`. Rebuild
   manifest with official `p0d_public_pack.py` after adopting NEW code;
   do not use the historical 15-file manifest unchanged.

The OWNER controls deployment; no main merge, production publish, paid
operation, PC Codex per-package test or protected P0A/B/C changes are
initiated by this package.
