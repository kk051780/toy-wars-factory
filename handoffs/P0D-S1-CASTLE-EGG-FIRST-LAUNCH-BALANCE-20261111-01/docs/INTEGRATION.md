# Sole CHAT-INTEGRATOR #220 review: OPTIONAL S1 combat objective parity candidate

**Do NOT blindly import.** This module is source-only, not automatically mapped into any Roblox project. This is a balance hypothesis derived from pinned public Chat S1 initial game commit `35d7d0525388e885aac8281eff2315a59831e0cf`, *not* the up-to-date local Windows source/Place. When S1 RC evolves, rerun the model with actual source-reviewed values. Never overwrite unknown OWNER PC changes.

## Finding in source

`src/shared/Config.luau`: `CastleMaxHp=300`; `CastleAttackDamage={RAIDER=14,GUARDIAN=10}`; `AttackCooldown=.85`, `RoleWalkSpeed.RAIDER=19`, `CastleReach=18`, `CapturesToWin=2`, `InteractDistance=12`. `src/server/MapBuilder.luau`: RED spawn x-68, BLUE castle core x+107, BLUE egg x+98 z-20, RED scorePad x-82 z+20. `src/server/Game.server.luau` resets attacker cooldown and keeps one round/damage/objective owner. `MapBuilder.prompt()` uses `HoldDuration=.35` for egg and score pads. All are source-derived; candidate numbers are not empirical match measurements.

No-defender, 2D travel-only lower-bound estimates: original RAIDER castle=26.11316 s and egg twice=34.89332 s (ratio 0.74837); proposed profile RAIDER castle=37.16316 s, egg twice=34.89332 s (ratio ~1.065). Guardian castle ~45.31667 s and egg ~43.82488 s (ratio ~1.034). These are optimistic individual-strategy bounds; comparing two lower bounds does **not** prove actual outcomes.

## Exact optional config edit (sole #220 writer ONLY)

In the latest **reviewed** single S1 `Config.luau`, if the same source identity and values still apply, change only:

```diff
-    CastleMaxHp = 300,
-    CastleAttackDamage = {RAIDER = 14, GUARDIAN = 10},
+    CastleMaxHp = 420,
+    CastleAttackDamage = {RAIDER = 12, GUARDIAN = 10},
```

The original `src/S1LaunchBalanceProfile.luau` in this package is **opt-in data**, not a runtime auto-run module. If importing it under `ReplicatedStorage`, do **not** add a second Game / Round / Damage / Remote authority. Prefer changing the canonical single Config with the reviewed diff; do not run two parallel configs.

## Acceptance gates and rollback

1. Confirm actual up-to-date single canonical `Config`, map geometry and Game require graph; if changed, re-evaluate before proposing numbers. Owner's latest PC source must not be replaced by this snapshot.
2. Run local test: `python -m unittest discover -s tests -v` and `python tools/balance_model.py`; document exact verified source SHA and accepted config delta. Tests do not execute Luau.
3. Perform comparative human 2-client Studio test with both objective wins, actual input fatigue, PvP, defenders, interruptions, respawn, and visual clarity. Required final Studio QA only by OWNER direct instruction after Chat full-game RC assembly.
4. Evaluate a minimum of 3 repeated private rounds per strategy/side using real timestamps and record distribution of time-to-win and failed attempts. Do not claim statistically valid retention from 3 sessions; use as sanity check.
5. If attacking becomes tedious or egg route frustrating, revert only the two canonical Config lines to previous reviewed values; no core code rewrite.

**No auto-merge, public Roblox release, paid features, store purchase, Codex request, or automation changes.** Handoff comments are not a direct PC command.
