# GQ470 / FB-015 — matte lobby floor-edge masonry (2026-11-21)

This is **real client Luau** for the existing V3 REAL69 PRIVATE_COMPANION GQ646 lobby, not a new lobby, new SpawnLocation, new gameplay mode or officially adopted feature. It makes the original rectangular safety floor visually less placeholder-like, with eight low-glare wedge-shaped edge stones with alternating opposed bevels. Existing floor position, walkability, collisions, participant movement and gameplay flow stay unchanged.

## Non-overlap / quality purpose

* #980 owns **early floor/spawn timing** (P0 player absent); this candidate only observes the already existing `GQ646_LOBBY_SAFE_GROUND`.
* #925 owns lobby signage/roof; #974 owns brief avatar arrival particles; #982 owns castle foundation, not lobby. Do **not** install this script as a duplicate of those PRs.
* Only a uniquely named LocalScript `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LobbyEdgeMasonry` would be selected if #220 B explicitly adopts. No existing 69 sources are changed by this PR.
* Eight matte Slate wedges, no lights/neon/surfaces/GUI, no physics, touch, shadow or query. Camera-position-based nearby-one-floor LOD (works with spectating; character root fallback before camera): 115 studs Touch or 175 desktop, checked every 2.5 s; streamed removal and `EGGRUMBLE_ReducedEffects` remove all decor.
* Uses local geometry relative to actual floor dimensions. Static six-size geometry cases keep wedge tops below original walkable floor top. Full Roblox visual inspection has NOT happened; this can still look poor on the actual Stage.

## Acceptance gates

1. A SOURCE: current official HEAD equals immutable `e80973c354f14a0d0088577f3cc1a875454f0f8f`; original artifact Place is 798390 bytes with SHA256 `fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934`; exact 69/69 source SHA/class/route; 70th script only this LocalScript; full OFF69 real Rojo equals original Place; Native Luau OFF69+ON70 compile; actual ON70 Place Source/Class verify; 14 mutant-source negatives and no-go receipt.
2. #250 `DEFER` until visible player P0, #910 true one-match acceptance and high-value #983 ART16 intake. Avoid PR #983 / #980 / #981 duplicate source selection.
3. If later adopted, **only certified #220 B writer** re-GETs fresh formal HEAD, checks #218 scope/CLAIM and #250 value, source-selects only the new LocalScript from the pinned A artifact, performs non-force expected-SHA CAS and same-head full official ZIP/Place/Native QA. Do not merge this entire PREP PR.
4. Runtime pass requires real PRIVATE Studio Play (not Run) and two-client, 8-scene PC/Android old/new images (32), human PC ART>=4.5/5 and Android>=4/5, low-end Android 15min FPS p50>=30/p10>=25 and thermal loss<=20%, first-3min kid FUN>=4/5, OWNER acceptance. Static source QA is **not** any of these real tests.

## Manual runtime checks for eventual stage

On exact official/adopted Private Place, compare without and with feature after the owner-visible-player P0 is resolved: (a) initial spawn/character never falls or disappears; (b) no stones until GQ646 floor exists; (c) stones remain below walkable surface and do not cover class selector/portal; (d) 8 parts max, no collisions, both touch and desktop; (e) simulated StreamingEnabled floor disappearance/return does not leave geometry; (f) ReducedEffects immediately removes and restores decor; (g) camera far than LOD removes; (h) same 69 gameplay scripts and server states, eggs/score/AI unaffected. Any failure reopens FB-015.

No new gameplay effect, player retention benefit, performance gain or ART_PASS is claimed. `STUDIO=NOT_TESTED`, `ANDROID=NOT_TESTED`, `ART_NO_GO`, `OWNER_ACCEPTED=0`, `OFFICIAL_RC_ADOPTED=NO`.
