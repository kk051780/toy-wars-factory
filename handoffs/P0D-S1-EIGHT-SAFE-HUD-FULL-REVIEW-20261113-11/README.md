# TRAP RAIDERS S1 — eight-safe full-source Rojo preview (isolated review only)

## Scope / ownership

**This is an original-game S1 review candidate, NOT an official RC branch update or Roblox release.** Official sole S1 RC writer: P0D-CHAT-INTEGRATOR-S1-RC01-B (Issue #220). Current official RC at intake was `1263a03701211a652b99b91d2339575dc8104eff`.

This branch was created from the completed seven-safe full-source review `179dfa7f91d735594f3c58c9d1b76fbab0f7e6e7` (seven production source commit `6cc131d3de06fe8799d00f475fc446a526e4b2c4`). Exactly **two existing release files** have changed versus the seven-safe review: complete original `src/client/HUD.client.luau` and the 37-entry `BUILD_MANIFEST.json`. Other 36 tracked release files and all existing game rules/authority unchanged. New files exist only in this QA handoff root and own Actions workflow.

The HUD source is **byte-identical** to independent upstream #240 candidate at fixed commit `82847cb97d06394f8fba5ec5c88e644dce0a336b`, Git blob `50823390853989ccdda78e28c16ea4757bbe0715`, 9,549 UTF-8 bytes, SHA256 `ab9155c3e62522cf32f69ba18a042ff3f32c3e6064e483f48147e8c043edeee8`. Upstream genuine Luau native 43/43 HUD behavior assertions and 6/6 intentional unsafe mutations passed in run `43220513814`.

## What eighth change fixes

Existing seven-safe Game.server already sends a server-only monotonically increasing `SNAPSHOT.updateId`. Child first-minute Coach already rejects stale same-round views. The **existing HUD** lacked this guard; out-of-order old packets could overwrite later phases, roles, displayed scores and mobile Guardian-trap visibility. Exact approved upstream candidate tracks `lastUpdateId`, validates integer nonnegative bounded IDs, rejects duplicate/older IDs and legacy packets after a versioned packet, commits the ID only after accepted score/hp/serial data. No new remote, no client-selected combat/teleport/damage, and BOSS_VISUAL branch unchanged.

## Release adoption contract

1. Run own eight-safe GitHub Actions workflow; require all 37 manifest source sizes/hashes verified, exact HUD git blob and SHA; 18 Python review test functions and existing release tests pass.
2. Pinned Rojo 7.7.1 builds an **unpublished** complete `.rbxlx`. Independent XML verifier compares **all 21 actual embedded Luau script bytes** to checked-in source and rejects 12 malicious XML mutations including erased HUD monotonic gate.
3. Pinned original upstream Luau compiler compiles all 21 scripts and rejects bad syntax. Actual previous complete seven-safe source has already passed native Game/Coach 164 assertions run `43217618848` and Game arena/egg/updateId 158 assertions run `43219786586`. Note: those separate old run IDs do not automatically certify this new eight-source project.
4. Only the exclusive #220 official integrator can select INCLUDE_OR_SKIP and update official RC. After that, independently rerun complete official RC builds/source QA and OWNER directly authorizes Windows Studio *real* two-client, mobile, physics, lag/order, reconnect, clean-stop, child playtest and final separate publication decision. The GitHub Actions native tests are NOT Roblox Studio evidence.

Public-source repo may contain this original fictional game's code under `PUBLIC_SOURCE_V1`; no credentials, personal user data, copyrighted third-party assets, billing, D07/D08 boss activation, main writes, merge, Roblox publication, Windows Codex, P0ABC CAS/security, or five existing Automations changes.

Status of initial S1 *game* remains last sole #220 audit **75/100**, not increased by our independent preview. Stage PRELAUNCH, CHAT_RC_READY=NO, actual Studio 2client/phone/Human test NOT_DONE, public release NOT_APPROVED. The unique isolated QA 5 acceptance gates are evaluated separately.
