# P0D-FAST-FEATURE-GATES-001: profile-aware SAFE feature gates

## Why
The current canonical RC HEAD `50bf5b4851fc0eb7c16052f578d6360ec54cd63a`, ACTIVE profile rich51, has only profile-wide rollback rich51→rich47→legacy21. An isolated prior bridge (P0D-BATTLE-DOJO-BRIDGE-001) duplicates **already-present** result/waypoint in source-rich47; do not integrate it blindly.

## New author-owned isolated source
Pure Luau `src/FeatureGatePolicy.luau` provides `resolve(profileId, overrides)` returning immutable allowlist or fail-closed error and `isEnabled(snapshot,feature)`. IDs exactly match currently shipped RC feature registry: CORE_S1, EGG_DUAL_MODE, H1_SKYV5, H1_MUSOU_V7, H1_AUTO_DOJO_2, V4_SIX_SKILL_SESSION. Unknown IDs/types/profile denied, core cannot be disabled, V4 depends on H1 dojo, and old profile cannot opt in missing files.

**Crucial limit:** NO LIVE GAME HOOKS. None of the original Game/Remote/Store/Rojo/ACTIVE files changed. This source is integration-ready policy, not actual toggling. Official RC feature flags still NOT_IMPLEMENTED until the sole #220 writer connects to specific subsystem entrypoints with per-feature rollback, and verifies one Game authority. Do not count this as 51-source active RC or Studio pass.

## Fastlane integration contract / #220 only
- Add one read-only import to original authoritative Game or source assembler, not a second Game or Remote.
- Gates should check Game server decision points for EGGS/MUSOU/SKY/DOJO; client must not be able to raise enabled feature IDs.
- Avoid runtime switch of persistent storage/schema with existing profile data. Do not gate crucial round/HP/score/Store. Any feature with no safe server hook remains profile fallback only, and is marked UNSWITCHABLE.
- Rollback: remove one import/hook + this policy file, or choose prior rich47/legacy21 profile by ACTIVE.json. Build from fixed SHA, validate exact Rojo source & full negative QA.
- #219 owns design, #250 tracks selection, #220 sole RC writer. Not selected/adopted yet. Owner Studio and FUN remain publish gates, not per-RC integration gates.
- No main/merge/publish/paid/PC/automations.

## Evidence to obtain
11 Python static contract cases prepared (run status separately recorded); native Luau cases/real hook/51→52 Rojo/CI/Studio/Android/FUN NOT_TESTED. 1/6 required gates achieved = source prepared; 5 remain source QA, native QA, integrator contract, official RC hook, RC exact build. Game overall 75/100 FUN_NO_GO last official.
