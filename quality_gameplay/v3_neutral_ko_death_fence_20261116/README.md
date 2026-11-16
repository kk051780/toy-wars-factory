# EGGRUMBLE V3 — genuine neutral KO death attribution fence

Owner boundary: independent SOURCE-only QA candidate from #470. Source parent **#482 HEAD fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9**. Exclusive new root `quality_gameplay/v3_neutral_ko_death_fence_20261116/`. Soft claim only, no coordinator grant, no original author write.

## Reproducible source-level defect

The original `EGGRUMBLE_SwarmCombat.luau` checks `phase == ACTIVE` in `strike()` but the real `Humanoid.Died` callback credits any `LastAttackerId` contained in `session.rules.castles`, without retesting match state, castle alive, or that the dying Model belongs to this live horde. A final in-flight death after a castle falls or the winner is decided may incorrectly raise personal KO, level, result and feedback. This is a **source-level potential race**; Studio reproduction is **NOT_TESTED**.

## ORIGINAL_AUTHOR_HOOK (only original #482 owner may edit its source)

Insert exactly one sibling ModuleScript named `EGGRUMBLE_NeutralKoDeathFence` into the *existing* original V3 server project. In its original SwarmCombat header:

```luau
local KoFence = require(script.Parent:WaitForChild("EGGRUMBLE_NeutralKoDeathFence"))
```

In the original `h.Died:Connect(function()` callback replace:

```luau
if type(id)=="string" and session.rules.castles[id] then
```

with:

```luau
if KoFence.mayCredit(session, id, m, all) then
```

Keep the original `ImpactFeedback.ko`, `credit(id)`, existing `live[m]=nil` and cleanup unchanged. The original author must source-lock the upstream 21 scripts, add this one helper to Rojo, test both modes/TEAM/BR and old-round callbacks, then ask #484 to compose latest ART/SCORE without rewriting other authors.

## Acceptance / rollback

Positive: current active match, living owner castle, actual owned neutral `Humanoid.Died` -> one original credit. Negative: winner set, match finished/draw/abandoned, eliminated owner castle, stale/foreign model, destroyed world or prior horde -> zero. No fabricated hit/KO; never move neutral HP authority. Rollback removes the helper and original callback hook. Fail closed if helper cannot load; do **not** retain unguarded fallback.

Python contract tests examine source and semantic mirror but do NOT prove native Luau execution. Native Luau VM + exact private Place, Studio TEAM/BR with real kills and results, Android 15m, #420 ART/FUN and OWNER remain mandatory. #220 is the only authenticated official RC writer; never merge this DRAFT, alter main or canonical RC, publish, or spend.

## 2026-11-16: upstream #494 already fixed part of this defect

This lane does **not** reimplement #494's post-match / eliminated-castle KO guard. Existing [#494](https://github.com/kk051780/toy-wars-factory/pull/494) patched those state checks into the **single original** `SwarmCombat.h.Died` callback. Our narrow independent addition is **physical model + horde + current Arena/world lifecycle identity**. In the 28-source private candidate, the original 26 ART/AI/Game/SCORE sources are reused by #484's existing composer, #494's original 27 source *is not duplicated*, and this lane adds one pure identity module plus one Boolean condition to that same original callback. No new scoring writer, connection or enemy spawner. Original-owner approval and #220 official CAS are still required. The private 28-source Place proves packaging / source exact only, not Studio runtime, Android, FUN or OWNER GO.
