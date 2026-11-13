# TRAP RAIDERS H1 企画室：卵の初成功を気持ちよくするオリジナル演出

## Why this slice?
Roblox official Creator Hub onboarding emphasizes showing the core loop immediately, and the retention guide recommends a joyful moment after the first completion. The 2026 official discovery FAQ ranks first-play bounce and playtime among the key signals. We will evaluate actual child satisfaction without copying any third-party game.

References:
- https://create.roblox.com/docs/production/game-design/onboarding
- https://create.roblox.com/docs/production/analytics/retention
- https://create.roblox.com/docs/discovery-faq

**Single existing adoption**: P0D-FUN-H1-001 #250. New product studio source issue #266. Source owner: CHAT-H1-FTUE-EGG-JOY-MOMENT-20261113-01. Base genuine previous #260 kid-HUD entire game SHA2b0b8cafa9faad621b996b83eacfc99007a2e278 with 28 Luau scripts. Other teams' files and protected #220 RC **never modified**.

## Selected first 90 seconds micro-joy

| Real server SNAPSHOT change | Child-visible local client response | Correctness |
|---|---|---|
| Actual already-active player starts carrying enemy egg | 🥚 お宝ゲット！ じぶんの陣地へ持って帰ろう！ | Only empty→enemy-egg same round, no initial join / pickup replay |
| Team RED/BLUE score increases | ✨ チーム得点！ みんなで一歩リード！ | Does not say **you** scored, counts teammates too |
| Same round ACTIVE→RESULTS and own team won | 🏆 勝利！ チームの大成功！ | Not shown for DRAW, defeat, first join, stale old round |

All three use the existing server's immutable SCORE/CARRY/WINNER/serial/updateId. The effect is at most 1.57 seconds; eight tiny local gem decorations, no screen flash, no music, no external IP, no monetization/loot/XP promise. Original game HUD/role/mobile taps and D18 directional guide stay untouched. The joyful feedback has no collision, part, physics or authority changes. Gated to RunService:IsStudio for a private test only.

## Actual reproducible full-game integration

- src add-only client/EggJoyRules.luau (one pure transition module) and client/EggJoy.client.luau (view-only GUI listening to original Remote OnClientEvent; never sends actions).
- tools/assemble.py first runs preexisting #260 complete 28-script approved original assembler, then proves all 28 original Luau files unchanged byte-exact and mounts only 2 new client scripts in StarterPlayerScripts, resulting in exactly30 scripts (Script2, LocalScript5, ModuleScript23) and one Rojo project.
- tests/check_built.py verifies real generated .rbxlx contains all 30 exact Luau sources by XML/source strings, original Game single Remote, no new client remote/marketplace/DataStore/damage.
- tests/generate_native_test.py generates genuine Luau code executing EggJoyRules against RED/BLUE, snapshot replay, stale IDs, fake egg, score rollback, new round, team reassignment, own win, loss and DRAW. It must pass native pinned upstream CLI, not pseudo JS simulation.
- Own CI `.github/workflows/p0d-h1-first90-egg-joy-native-rojo-20261113.yml` uses SHA-verified Rojo7.7.1, pinned Luau f46d879e... and only produces unpublished Studio-only Place if proof succeeds.

## OWNER acceptance (before #220 official RC)

1. First 15 seconds: explain 'enemy egg → carry → own score pad' in one child sentence. Did the player understand without reading long tips?
2. First 30–90s: actual egg grab triggers small authentic celebration, not fake on initial sync; guide is not blocked on small Android landscape screen.
3. First score: team credit vs individual message is accurate, victory/defeat/draw never misreported; 2 real clients independently confirm.
4. Ground/sky/sea physical routes, original Guardian trap vs RAIDER Wind, local fantasy creatures and D18 guide remain operational. Test Play→Server+2 clients and Android physically.
5. H0/H1 comparison: ask child 'was stealing the egg clear and fun?' and 'would you play again?'; log actual reaction; target (hypothesis only) ≥4/5 can state objective within30s, ≥3/5 report a joyful moment within90s. **Not results, only proposed acceptance criteria.**
6. Capture performance and crashes, fix if phone FPS/UX degrade. Before full production the sole #220 RC writer must separately review and OWNER approve. First release/PSE/pay/Robux disabled.

Progress separation: own source/QA pipeline percentage separately reported, official whole game last #220 75/100, source H1 candidate in private Studio only, real physical tests and owner fun NOT_TESTED. No main, protected RC, merges, publish, paid, Windows Codex, P0A/B/C CAS or 5 Automations modifications.
