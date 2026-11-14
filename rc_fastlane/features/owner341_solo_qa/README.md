# OWNER #341: real compiled StudioSolo policy QA, not a new game implementation

Current source baseline: canonical RC `b151a6f38f0fb7127b506ef993a3bdf1918c823e` (65 native Luau).

This QA-only branch adds `StudioSoloNativeAcceptance.luau` (24 deterministic behavior assertions) and one step to the existing canonical RC fastlane workflow. The workflow first **assembles the actual Game and StudioSoloPreviewRules source**, source-locks the complete 65 originals, and only then appends the 24 tests to the actual final `StudioSoloPreviewRules.luau` body (not a Python reimplementation). The existing pinned native `luau-compile` and `luau` execute the policy.

Cases include Studio solo red/blue starts, server-side public prohibition of solo starts, 2-player both-team rule, unassigned/empty invalid cases, isSoloRound latch, and empty-team result when real multiplayer loses a team. The original Game's three calls to this policy must be unique and present. No new Game/Remote, no XP/egg/score/HP/storage changes and no new gameplay LocalScript. The final 65-source exact-Rojo build is still required.

The new test does **not** prove Roblox Studio/Android UI, 7s real countdown, player spawning or fun. OWNER must still run an engine 1-client/2-client trial. This branch is PREP QA only; it must never be treated as formal #220 canonical adoption or permission to change main or publish.

Current HUD fix was already integrated to official RC by sole writer in #342/#346; stale optional HUD PREP #345 was CLOSED NOT MERGED to avoid duplicate overlays. This QA helps test that official existing solo functionality remains correct without adding a second solo engine. 
