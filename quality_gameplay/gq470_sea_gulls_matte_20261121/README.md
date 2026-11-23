# GQ470 / FB-015 — matte sea-gull silhouettes over the existing coastal dock

**Source-only A PREP.** No official RC update, no Roblox Studio evidence, no Android 15-minute run, no visual acceptance. Original formal RC `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f` remains #220's sole certified integration target.

## Visual delta (game source, not a concept note)

An optional new **LocalScript** `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_SeaGullsMatte` draws small, stylized ivory/slate 3D sea birds near **the actual existing `PublicSeaDock`** only, to add life and scale to the coast. Each bird is one soft matte body plus two sculptural angled wings. Slow Tween motion in open air, no particle/neon/GUI/labels, zero server authority. Android 2 birds × 3 Parts = **6 local Parts max**; PC 3 × 3 = **9 max**. 165-stud culling, reduced-effects toggle, no birds if the player has no living character, streaming-aware world cleanup, cancelled Tweens on teardown. Cannot block traversal, damage, trigger touches or alter the boat route.

**Non-overlap** with existing source lanes: PR #942 replaces existing six shore foam parts; PR #969 implements a true boat wake when seated; #921 sculpts corals; PR #959 handles cloud ridges; our new client path changes none of their scripts or any official REAL69 source. The visual can still be rejected by #250/#420 after evaluating composition and device performance.

## Safety, QA and official admission

- All 69 selected ORIGINAL Luau source routes and the original Place are byte-/class-exact unchanged. Optional new route is the only new selected LocalScript in an A candidate. OFF rebuild must be byte identical to the original 798,390-byte Place. **Not a new official RC.**
- Native compile original69 + candidate70; authentic Rojo original OFF69 exact and ON70 source/class; fail-closed source receipt + B220 one-source source-select packet, tamper negatives; ART_CHECK_REPORT 0/32 real images, Studio/Android/FUN all NOT_TESTED, ART_NO_GO.
- Source tests: `python3 -m unittest discover -s quality_gameplay/gq470_sea_gulls_matte_20261121 -p "test_*.py" -v`.
- Manual Studio scenes: near dock, far >165 studs, dock streamed away/recreated, death/respawn, reduced effects switched mid Tween, long mobile 15-minute, user-visible avatar first, egg/score unaffected. Compare same-camera coastal BEFORE/AFTER and device FPS; no improvement claimed before human screenshots and measurements.
- **Priority/dependency:** player not appearing (#364; candidates #980/#981) and #910 single match loop remain P0. Defer optional cosmetic adoption until genuine B220 authenticated fresh-SHA nonforce CAS, scope approval, #250 feature selection and #420 quality evidence. Do not directly merge this PR or change `main`.
- Rollback: omit the new client route; original 69 sources/Place are exactly preserved and selected independently.

Core A packaging/receipt/ART report harness is adapted from the existing verified #982 pattern; the new in-game seabird behavior, safety caps, and source tests are distinct.

**States:** `A_SOURCE_PREP`, `CLAIM_GRANTED=NO`, `FORMAL_RC_ADOPTED=0`, `ENGINE_NOT_TESTED`, `ART_NO_GO`, `MOBILE_NO_GO`, `FUN_NO_GO`, `OWNER_ACCEPTED=0`.
