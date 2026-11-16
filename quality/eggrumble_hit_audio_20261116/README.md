# EGGRUMBLE GQ — seven-role real-hit sound (2026-11-16)

**Scope/soft claim:** `quality/eggrumble_hit_audio_20261116/**` only. #218 claim request is pending; this is an isolated **DRAFT candidate**, not an authorized RC writer. No overlap with #482 gameplay, #484 composer, #485 ART, #487 SCORE, #488 device evidence, #490 drift, #496 compass, #492 spectator or official #220 RC.

## Gameplay contribution
Reuses #482's server-confirmed `EGGRUMBLE_ImpactSequence`, `ImpactRole`, `ImpactSlot` and `ImpactWeight`; adds **only one Studio-only client sound** that plays on a confirmed real hit, never a predicted miss. Seven distinct role profiles use bundled Roblox character sound files, per-skill pitch and multi-hit weight. Four pooled voices, six sounds per second at most, volume cap 0.30, separate `EGGRUMBLE_SFXMuted` player preference, no sound for dead/eliminated character, duplicate-script prevention. Source does not write any game state. This is a functional prototype; bespoke, high-quality original recordings and human audibility/ART testing are still required.

## Integration evidence
`EGGRUMBLE_V3_AUDIO_STUDIO.project.json` references original 21 scripts from fixed #482 author's parent without copying/editing them, plus the one LocalScript. Native Luau parser, Rojo source-exact private Place, Studio PC/Android A/B sound and mute/performance checks, and #420/#470 gates must run on the actual candidate HEAD. CI success by itself is **not** Studio/Android/game quality proof.

Owner rules: **no main write, no auto merge, no official RC write outside #220 nonforce CAS, no publishing or spend.** Once coordinator confirms exclusive claim and source-only QA passes, #220 can source-selectively adopt the script into an authenticated next official RC with source-lock/rollback/Place bytes.

Rollback: remove the one `EGGRUMBLE_RealHitAudio` StarterPlayer LocalScript, leaving all original gameplay scripts unchanged. OWNER_ACCEPTED=0 until audible Studio/Android comparison and explicit acceptance.
