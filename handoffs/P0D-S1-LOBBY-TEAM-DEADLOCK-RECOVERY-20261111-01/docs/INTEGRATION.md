# Integrator-only S1 team-deadlock fix

## Exact source scope

- Official Chat S1 `rc/p0d-s1-kids-rc01`, source baseline commit `35d7d0525388e885aac8281eff2315a59831e0cf`.
- Canonical game path `releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau`, Git blob `0f2c34fe25c00e3251b9ca53952b9ec75400f365`.
- Only the #220 **sole CHAT-INTEGRATOR** may modify its branch. This packet is isolated and has no automatic install.
- **Known bug:** `chooseTeam` runs on join only. A 4-person 2v2 match losing both BLUE players can leave two RED players in LOBBY without any new arrival; LOBBY always requires both teams nonempty, so it never starts. Losing the last BLUE during COUNTDOWN while two RED remain also passes original total-count-only precheck, briefly starting a one-sided round.

## Deterministic adoption steps

1. Compare your actual latest RC `Game.server.luau` to immutable baseline. If different, **do not run this exact-source patch** until reviewing the differences and adapting it safely to newest RC. This tool deliberately fails on any base Git blob mismatch.
2. Copy this packet's `src/LobbyTeamRecovery.luau` into your existing game's `src/server/LobbyTeamRecovery.luau`. In the existing Rojo project `ServerScriptService/TrapRaidersS1` maps the whole `src/server` folder: the file becomes **one ModuleScript**, with no second Script or MapBuilder authority.
3. Use `python tools/apply_game_patch.py --source /path/to/base/src/server/Game.server.luau --output /separate/isolated/Game.server.luau`. This checks original Git blob and refuses in-place edits. Review its transformed output and then let the #220 integrator copy the reviewed diff into their OWN RC branch.
4. Re-run original S1 project offline tests and combined independent QA; update the actual RC source hash, manifest, release plan and receipt. Final Windows Studio/2client/mobile only after OWNER direct near-final instruction.

## Gameplay contract and invariants

- Planner is pure `LobbyTeamRecovery.plan(roster)` and returns minimal deterministic team moves; no mutation of roster. Accepts positive/negative **integer UserId** (negative Studio IDs allowed), rejects unknown teams, duplicates, fractional/nonfinite UserId, malformed/sparse arrays, and over-64 roster.
- Only `LOBBY` calls the move executor. `COUNTDOWN`, `ACTIVE`, `RESULTS` do not rebalance. On LOBBY move, clear any stale carried egg, change only the player's Team and Neutral flag and reposition their living character to its own base; opponent objective, attacks and score are untouched.
- If at least two players remain all on RED, move exactly one (largest userId) to BLUE, achieving 1v1 without a new connection. If 3 RED+1 BLUE, move one to BLUE, becoming 2v2. A sole player is left alone and original `Config.MinPlayers=2` still enforced.
- Countdown must recheck nonempty RED/BLUE in addition to total count. If one team goes empty, go back to LOBBY and correct it on the next tick; never resetRound into a one-sided ACTIVE.
- If roster is unknown/unsafe (unsupported team or duplicate ID), planner returns nil and makes no changes. The old minimum-player/team guards remain authoritative.
- The 0.5s existing `SNAPSHOT` broadcast should update team HUD after moving; **no new RemoteEvent or FireServer**. No changes to S1 Results countdown, Game damage, egg handling, D07/D08 boss adapter, D15 snare, persistence, monetization or Studio runtime.

## Acceptance before inclusion

- Must have genuine Luau parse/Roblox Studio 2-client run (not proven by Python).
- Check 2RED/0BLUE LOBBY -> red1/blue1 -> countdown -> round; 3RED/1BLUE lobby -> 2v2; during ACTIVE no team flip, during COUNTDOWN losing last BLUE -> LOBBY not one-sided round; `RESULTS` no auto-switch until next LOBBY; idempotent LOBBY snapshot/tick with no further changes.
- Verify moved player's team-colored name, spawn location, no stuck egg, no UX teleport once ACTIVE.

## Rollback

Remove one new `require`, the new `rebalanceLobbyTeams` function, its LOBBY invocation, the COUNTDOWN side check and the pure ModuleScript. Original source untouched in this packet; rollback to prior #220 RC commit if adopted patch causes regression.
