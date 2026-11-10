# S1 D15 match epoch and anti-flood guard (V1.2)

Game: TRAP_RAIDERS / p0d-siege-v19 / P0D-S1-KIDS-RC01

## Failure cases identified in V1.1 source

The V1.1 bridge trusted `getPhase()=="ACTIVE"` without proving the true
`match.serial` still matched `beginRound`'s serial. If the Game owner switched
rounds without delivering the callback, old D15 effects might process while
a *new* round is also ACTIVE.

A malicious client also could send numerous increasing `seq` values and cause
`handleIntent()` to call `update()` (and loop over the entire player roster)
on each request, despite the original D15 Core's cast cooldown. This is a
performance abuse **risk** from source review, not an observed exploit report.

## V1.2 safety contract

- Require `getRoundSerial()` exactly equal to `match.serial` at start and during
  both periodic tick and intent acceptance. Old epoch means `STALE_ROUND`.
- Do not create, reset, or update the game RoundCoordinator; the single
  original Game controller owns all phase, seq, HP/damage, and Remote handling.
- Use the existing absolute trusted `serverNow()` clock to allow at most one
  D15 intent per Player per 0.15s, **before** O(players) full-roster scan.
  Rejected original Core casts still use this interval. Poison ticks remain
  scheduled only by the original Core against elapsed server time.
- Clear per-player cooldown on `removePlayer`, and all cooldowns on
  `beginRound` / `endRound`. A new round is not blocked by old rate state.
- The original D15 Core must be byte-identical to recovered source; neither
  this patch nor Python regressions replace native Luau engine QA.

## Required Game owner integration

Callback table MUST contain `getRoundSerial = function() return match.serial end`.
Game still consumes `Rules.validSeq(data.seq,lastSeq[player])` in its ONE
OnServerEvent listener. Do not send fake client serial, target, clock,
position, team, role, or HP to the adapter. After `STALE_ROUND`, owner verifies
its real lifecycle wiring and does not advance old effects.

## Real Studio acceptance remaining

Run 2client timed trap attempts at <0.15s/>=0.15s, late escape and rescue,
12s recast, reset while poison pending then active next round, leave/rejoin,
lag/clock rollback, and game egg/score/castle victory baseline. Native
Luau parse, FPS and mobile touch UX also remain NOT_TESTED.
