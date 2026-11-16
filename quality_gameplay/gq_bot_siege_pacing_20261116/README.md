# EGGRUMBLE V3 game-quality unique slice: bot siege focus-fire pacing

**Status:** isolated SOURCE_WIP. No official RC write or OWNER Studio verification.

## Evidence and defect
Pinned author #482 head `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, original `EGGRUMBLE_BotActors.luau` Git blob `fa38f24a26a619238e4c6a62b3ee582dc14cfe7a`. Existing bot action loop deals **26 castle HP every 1.6 s per bot**, with no per-castle shared budget. A castle with 1,000 HP could take about 62 seconds of uninterrupted siege by one bot, or approximately 16 seconds by four simultaneously attacking bots (idealized steady-state, ignoring travel, pathing, shields, egg raids and any human attacks). This is a **source-derived exposure**, not a measured match time.

The OWNER target is an enjoyable 15-minute-default strategic TEAM/BR experience, with legitimate earlier wins allowed. This patch protects single castle sites from robot swarm instant-collapse **without weakening actual human players, neutral combat, item buffs, AI movement, eggs or siege ownership**. Real 2-client/Android game balance requires measurement.

## Implemented source and author reuse
- `EGGRUMBLE_BotSiegePacing.luau`: real pure Luau target-level server permit. All attacking bots share **one 26-damage siege allowance per castle every 7 seconds**, scoped independently to each active TEAM or BATTLE_ROYALE match. It rejects finished rounds, invalid/non-AI/eliminated/friendly attackers and already fallen castles.
- `tools/stage_private_v3.py`: strict Git blob lock. Reuse all **21 original author source files**; patch exactly one conditional in `EGGRUMBLE_BotActors.luau` and add exactly one ModuleScript. Do not edit author source file or create a second Game/Remote/Store/AI host. Output is a private **22-source Rojo project**, not the official RC.
- `tools/generate_native_harness.py`: executable genuine Luau VM rejection/rollback/two-mode scenarios.
- `tests/test_siege_private_composition.py`: source SHA-locked regression that all **other 20 original scripts remain byte-exact**.
- `tools/verify_private_place.py`: check real Rojo XML Place source and class against staged source files; must produce 22/22 before making any claim.
- `.github/workflows/p0d-gq-bot-siege-pacing-private22.yml`: source regression, pinned native Luau compiler/VM, pinned Rojo 7.7.1 + private source/class fidelity, byte-size receipt.

**Flag OFF/rollback:** set `session.gqBotSiegePacingEnabled=false` when selecting this optional overlay, or remove only the one added BotActors require/guard and extra ModuleScript; all original 21 source bytes remain recoverable. New independent match sessions automatically reset their pacing state.

**Important:** 7 seconds and 26 HP are **testable initial tuning parameters**; no game-fun or FPS pass is implied. Target-level limit is intentionally bot-only. Original human castle attacks keep their original 120 HP action and server guards. This is source-selective author coordination work; the current original author #482 must ACK before actual RC use.

## 8-lane duplicate-free cross-check

| Lane | Reused canonical author | This patch changes |
|---|---|---|
| Character | #482 seven skills, #522 builder | no role or weapon |
| Field | #520 ridge, #523 egg clearance | no geometry |
| Battle | #516 DOT, #524 dash/warp, #518 giant | no combat damage |
| Castle / eggs | #500 defenses, #523 eggs | only **AI attack cadence on castle**, not HP/castle model |
| Neutral | #494/#501 horde supply, original giant | no enemy spawn/reward |
| Items | #517 heal and #525 mode fence | no item code |
| Lobby | #492 spectator, #496 compass | no HUD/queue |
| Balance | this one-purpose pure server permit | **per-target bot-only siege pacing** |

## RC adoption gates (never infer completed from a draft)
1. **SOURCE_WIP:** independent code committed, source-lock check and tests submitted.
2. **SOURCE_QA:** same-HEAD workflow SUCCESS, source original 20 exact + one patched + new one, native VM, 22/22 Rojo evidence + ZIP/Place bytes.
3. **ORIGINAL_CLAIM:** author #482/#218 accepts conditional source-selective overlay. No unsolicited edit to original author branch.
4. **INTEGRATOR:** #220 sole authenticated writer applies reviewed exact difference to **latest official** `rc/p0d-s1-kids-rc01` via non-force CAS; same-HEAD official build+source lock+artifact byte receipt.
5. **STUDIO / ANDROID:** 2 sessions, solo bots, 2-client battle, 15-minute low-end Android FPS and match duration distribution measured against OFF.
6. **OWNER_ACCEPTED:** gameplay, visual and kids-fun acceptance under #420/#470.

This document is not a request to merge into main, publish, pay, or run Windows Studio remotely. No unverified QA result counts as PASS.
