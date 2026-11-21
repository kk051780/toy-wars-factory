# GQ470 FB-015 — true local damage clarity (A PREP, not RC)

The owner needs recognizable actual combat feedback, without permanent neon UI or expensive phone effects. This separate client LocalScript reacts **only to replicated local Humanoid HealthChanged with a genuine decrease**. It creates at most one client ColorCorrectionEffect (not 3D Parts) and a 0.24 s low-glare warm pulse, throttled to once every 0.30 s. It **does not** trigger on healing, air swings, fake-hit events, dead/respawned bodies, or disabled ReducedEffects. It cancels tweens and connections across death/respawn, changing nothing about HP/KO/egg/score/Store/Remote.

- Feature: `GQ470_FB015_TRUE_LOCAL_DAMAGE_CUE_REAL69_20261121`.
- Formal base: `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f`.
- A candidate only: adds `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LocalDamageCue` `LocalScript` to PRIVATE companion REAL69 -> PRIVATE A REAL70. All original 69 selected Luau routes untouched.
- Nonoverlap: #966 existing ART15, #949/#952/#954 attacker hit feel, #939 realm ambient grade, #968 ground-contact FX. No touch in any of those parent paths.
- Tests: source safety/fail-closed mutations, native Luau original69+candidate70, pinned Rojo OFF69 byte-exact and candidate ON70, source/class/hash, original 17 families/48-accounting unchanged, B-only one new client-source packet, art evidence manifest.
- **ART remains NO_GO**: required 8 scenes x 2 devices x before/after = 32 human screenshots missing (0/32). Studio Solo/2client, Android median/p10 FPS heat, child 3-minute fun, human art and owner acceptance are NOT_TESTED.
- B writer #220 sole authorized; no formal RC write from A, no whole PR merge, no automatic Publish/monetization, Work or Codex. If B decides DEFER_P0_FIRST that is valid, and this remains an isolated non-destructive source candidate.
- Rollback: omit the new LocalScript and build OFF69; original Place and all 69 Source/Class SHA remain exact.

Source QA cannot prove visual attractiveness. Input-to-tint perceptual validation must be measured in actual Studio before promoting ART_PASS.
