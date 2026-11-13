# P0D H1 — release-gate staged candidate, LIVE OFF by default

**2026-11-13 JST | game=TRAP_RAIDERS | adoption=P0D-FUN-H1-001 | Issue #264**

This is a technically real full H1 game staging build, NOT release approval. Original H1 #255 fixed source `1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b` is unchanged. Existing Windows Roblox Studio owner playtest and first-90s H0-v-H1 fun gate are still **NOT_TESTED**. Sole protected official #220 RC has not adopted this.

## Actual blocker
The existing REAL 28-Luau H1 whole-game code contains `RunService:IsStudio()` early returns in two key features:
- `server/H1FunWorld.server.luau`: actual sea, sky, moving creature, signs and visual routes
- `client/D18MascotGuide.client.luau`: original D18 lava-dragon egg/score path guidance

In the unchanged H1, these two systems do not run in a real published server/client; being able to see them in Studio proves nothing about a live release.

## Exact staged fix (one shared immutable gate)
This separate packet adds `inputs/H1ReleaseGate.luau` as **one** replicated ModuleScript in `ReplicatedStorage/TrapRaidersShared`. The exact original full H1 world and guide scripts are staged as `inputs/H1FunWorld.server.luau` and `inputs/D18MascotGuide.client.luau`, modified only in (1) replacing Studio early return with an explicit fail-closed require of the one shared gate, (2) setting cosmetic PreviewOnly to RunService:IsStudio() and (3) one guide comment. Original Game server, original two roles, RAIDER wind, GUARDIAN trap, authoritative enemy egg, own score pad, model catalogs, HUD and every other 26 Luau bytes remain EXACT original.

Release Gate behavior:
| Environment / approval | H1 world & mascot |
|---|---|
| Roblox Studio play, no approved IDs | **ALLOW** (private preview unchanged) |
| Ordinary published/client play, default packaged flags | **DENY**, features not spawned |
| Live flag accidentally true but GameId/PlaceId unset (0) | **DENY** |
| Live flag true, positive IDs but different game or Place | **DENY** |
| **Future** explicit sole-#220 + OWNER authorized live flag TRUE and matching positive UniverseId **AND** PlaceId | **ALLOW only in that exact approved game** |

The real packaged source permanently has `LIVE_ENABLE=false`, `APPROVED_GAME_ID=0` and `APPROVED_PLACE_ID=0`. No Remote, Attributes, Internet, player input or client messages can change that source flag, and no admin debug bypass is present. The Luau runtime test generates a **synthetic enabled variation only in /tmp** to validate future semantics; that variation is not a GitHub file, real Place, mounted ModuleScript, or release authorization. The stage's actual 29-script Place remains LIVE OFF.

## Repro / independent evidence
- Source builder `tools/assemble.py` executes the ORIGINAL #255 deterministic builder, copies original real 28 scripts to new own isolated staging directory, swaps only world and guide source, adds exactly one shared ModuleScript. Pins source Git blobs and verifies **26/26** unchanged old sources plus no new Game/Remote.
- `tests/test_live_gate_source.py` 17 Python actual-script safety/provenance and deliberately unsafe mutation checks.
- `tools/generate_native_gate_test.py` runs the **original** source-pinned actual Luau release gate policy through the pinned native Luau runtime, with live denial, positive exact allowlist, wrong/zero/fractional/invalid ID, studio no-ID behavior and spoofing. Temporary approved variant never mounted.
- Dedicated GitHub CI `.github/workflows/p0d-h1-live-gate-failclosed-20261113.yml` builds true Rojo7.7.1 `.rbxlx`, verifies **all 29/29 actual embedded XML source bodies** vs original new generated Luau, exact native compile **29/29**, and genuine native Luau gate matrix. The output is PRIVATE and must never be published as-is.
- Original #255 H1 independent source/native 24+76 policies passed CI `43348622975` on a different branch; this new gate's own test results must be verified independently.

## Mandatory before any real release
1. OWNER first opens original #259 unpublished QA-only 30-source H1 through Roblox Studio, Test → Server + 2 clients, records RED/BLUE/SERVER logs, actual sky and sea egg routes, wind/traps, D18 mobile E/tap, camera/framerate, and first90s comparison to H0. Source QA alone does not satisfy that requirement.
2. Sole official #220 RC integrator reviews this gate branch and existing #260/#261 UI patch: choose combine or skip based on test evidence, not opportunistic auto-merge. No public game written by this branch.
3. Only after successful OWNER two-client + mobile + human fun evidence, official RC acceptance/approved UniverseId and PlaceId can the same **single shared module** be edited through controlled sole-owner change review. No other scripts are intended to contain a live toggle.
4. Validate the explicitly approved build in a **separate private experience**, re-run exact 29 native / Rojo + source + 2-client + mobile tests, then human OWNER authorizes publishing. Use H0 rollback if unsupported.

Current whole P0D release official progress #220 last75%, World Field #222 last50%, both delta0; current FUN_GATE NO_GO. No public release, original protected main/RC, merge, fees, Codex, P0ABC or automations changed.
