# TRAP RAIDERS — Chat-first S1 whole-game vertical slice RC01

**Status: CHAT_INTEGRATION_IN_PROGRESS / Roblox Studio NOT_TESTED / NOT_RELEASE_APPROVED.**

This is a **real, independently source-reconstructible Roblox game project**, not just a collection of reference modules or a PC Codex instruction. It belongs to the owner-authorized PUBLIC source `TRAP_RAIDERS / p0d-siege-v19`, the sole CHAT-INTEGRATOR claim at Issue #220. It is a standalone new S1 implementation because the actual newest owner Windows Place/Source remains unavailable to this chat. **Do not claim it is a byte-preserving reconstruction of v43-A or a tested improvement to the local saved PC Place.**

## What the source actually implements

- Single server script owns S1 match lifecycle: 2+ players, auto-balanced RED/BLUE, 7-second countdown, 6-minute match, 9-second results, automatic rematch. Player exit/suspension is bounded.
- Procedural source-created arena with two colored castles, eggs, enemy egg pickup ProximityPrompts, own base delivery pad, map landmarks and spawns. A fall rescue sends players back to spawn.
- Score 2 captured opponent eggs **or** destroy enemy castle HP (starts at 300) to win. Own egg must be home to score.
- Server-only combat using server-observed player facing, range, raycast obstruction, invulnerability window, role-specific damage and cooldown. No client-provided target, coordinates, score, health or damage.
- RAIDER and GUARDIAN roles differ in speed, health and damage; role selection only outside active round (never mid-combat healing).
- Keyboard `F` / mobile tap attack; native Roblox thumbstick, jump and ProximityPrompt input. Japanese HUD for score/time/roles/objectives/result.
- One deterministic cosmetic alarm state sequence (not Gorogan boss): WARN 3s, SIGNAL 6s. No duplicate selector, weather RNG, economy, save writes, paid items or DataStore.
- Multi-file Rojo `default.project.json` into ServerScriptService, ReplicatedStorage and StarterPlayerScripts. No external asset IDs, private Roblox Place, secret API keys or plugins in the scripts.

## How to load, when final owner-directed Studio QA starts

1. On an isolated, unpublished empty Place, with Rojo installed (owner Windows Codex final QA only), use `rojo serve` then the Studio Rojo sync plugin. Source tree: `default.project.json`, `src/server`, `src/shared`, `src/client`.
2. Verify only ONE server entry `TrapRaidersS1/Game.server.luau` is running and no other game owns RED/BLUE teams or `TrapRaidersS1Remote`. The script deliberately errors on collisions rather than silently overriding the PC game.
3. Test 2 clients (RED/BLUE), native touch/mobile, steal/recover/deliver egg, castle melee, death/drop/rejoin, fake RemoteEvent payload, role switch, results/rematch, Studio Play/Stop and clean exit.
4. See `docs/QA_AND_GAPS.md` before deciding anything about full-game readiness. These are instructions, not evidence tests happened.

## Intentional limits

This is the **first genuine integrated S1 executable vertical slice**, not yet a final release candidate. **D07 original Gorogan 3D/AI/D08 canonical event, D11 neutral capture, 7-job full system, D14 vehicle, D16 original SCALE+VISUAL and D18 648-character library are not imported into the runnable project yet.** The alarm is cosmetic only; it does *not* substitute for the original D07 boss or count toward the full game QA. The direct owner/PC source comparison and actual Studio parse, server replication, 2-client, mobile and finish checks have not been run. Chat-side static / Python behavior regressions are only development evidence.

Build policy, governance and readback: [Issue #218](https://github.com/kk051780/toy-wars-factory/issues/218), [Chat S1 release train #220](https://github.com/kk051780/toy-wars-factory/issues/220), [policy SHA ae80548...](https://github.com/kk051780/toy-wars-factory/tree/ae80548d0c6905b4ee35e7cdedd3928d344ff239/handoffs/P0D_CHAT_FIRST_RELEASE_FACTORY_V2_20261111_01). `main`, production Roblox publish and payment remain unauthorized.
