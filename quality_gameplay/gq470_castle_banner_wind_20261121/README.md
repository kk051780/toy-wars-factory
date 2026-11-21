# FB-015: Castle banner wind / optional A-only candidate

- Feature: `GQ470_FB015_CASTLE_BANNER_WIND_20261121`
- Official parent: `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f` (REAL69, not modified).
- Candidate route (when and only when adopted by #220): `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CastleBannerWind` of class `LocalScript`.
- **Non-overlap:** new source file only; existing FieldArt, Castle, Character, Host, Camera and 69 selected sources byte-unchanged. Independent of #934 castle geometry, #970 ART16, #974 arrival, #976 crest, #959 sky.
- Intended visible change: up to 20 already-existing castle banners gently hinge ±3.5 degrees. Only anchored non-collidable non-neon parts inside an ancestor model containing `StandardCore` qualify. No part/GUI/asset creation, physics or server authority. Nearby ≤110 studs; PC ≥0.18 s and touch ≥0.32 s ticks, reduced-effects OFF switch, restores original CFrame outside range, cleans up removed arenas.
- Rollback: do **not select** this optional LocalScript into the next 70-script companion; preserve the existing 69 routes. In a candidate ON test, remove that one route and recover the official original sources unchanged.
- P0 priority: owner-reported missing player/avatar remains unresolved; this animation is *not* a spawn fix. #910 Playable Loop and avatar visibility take priority over visual flavor.
- Art acceptance: SOURCE QA only if exact-head CI passes; Studio/2client, Android15 min FPS, PC+Android 32 actual before/after screenshots, human art rating, kid FUN and OWNER accepted all **NOT_TESTED / NO_GO**. Native Luau compile (if CI succeeds) is not Roblox engine proof.
- Official intake is #220 authenticated latest-head expected-SHA nonforce CAS; this A branch must never write formal RC/main, force-push, publish or monetize.
