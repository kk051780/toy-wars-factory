# P0D-FUN-H1-001 / D18 Living Mascot Guide (isolated REAL H1 game candidate)

This single Rojo root clones all 24 EXACT existing real H1 game Luau source files from commit c73f305fb412927aee05b399a4f54a2a16d0579f (#248). No existing Game.server/HUD/world overlay/boss/creature or remote/score code changed. It ADDs the existing original D18 Batch8 catalog (exact blob 41079553d2141940fc3fee57b23969e292770614 from 7bfb7bd5a4d4531ceaf2deaaf19f7591d3c218cd) plus two original local scripts for read-only game-guided cosmetic mascot interactions.

## What this changes in ACTUAL private gameplay
- In Studio, COUNTDOWN/ACTIVE first-person participants see the original 17-Part 「熔炉の角竜」 next to their own actual team spawn, with a friendly bob/tail movement and an E/tap proximity prompt.
- Tapping asks the actual original S1 map for enemy team EGG and shows four short gold ground stepping lights. If the authoritative S1 snapshot says this player carries an egg, it instead points to their own team SCORE_PAD. The extra helper has no rewards/HP/inventory/damage/mobility or fake enemy/capture goals.
- Client-only graphics, one model per local player, no user data stored, all Parts noncolliding/nonquery/nontouch. Existing 24 S1/H1 game sources are byte exact; original 2 H1 moving rare creatures continue independently.
- One old 8safe+H1 body, no new RemoteEvent, server authority, monetization, spawn/egg pads, or existing roster roles. This is a meaningful kid-friendly visual world interaction, NOT S2-only catalog preview.

## Boundaries
- RunService:IsStudio guard: LIVE Roblox never runs this new guide without separate owner approval and adaptation. The existing H1 source is also Studio-gated. No main/protected RC/other feature branch changes or game publication.
- Pure Rule module rejects wrong/stale serial or updateId, unsupported team/phase, malformed carry. It does not send server actions.
- Single new H1 candidate project cloned under own unique handoffs directory, same original full game. No RC adoption, no private 2-client/mobile/FPS tests or owner human H0/H1 verdict yet.
- #250 adoption_id=P0D-FUN-H1-001; #219 claim https://github.com/kk051780/toy-wars-factory/issues/219#issuecomment-6839305557; #220 sole RC integrator decides inclusion.
