# P0-D H1 Field Independent QA — Castle wall / route conflict (Issue #253)
Date JST 2026-11-13. Scope: **independent quality review and UNMOUNTED candidate fix**; not an S1 RC or adopted #248 H1 game. Candidate is not connected to default.project.json. Its sole purpose is for the H1 owner to import after full independent review.

## Exact source pinned
H1 original complete full-game World overlay origin fixed immutable commit `c73f305fb412927aee05b399a4f54a2a16d0579f` from issue #248:
`handoffs/P0D-H1-WORLD-CREATURES-20261113-01/src/server/H1FunWorld.server.luau`, Git blob `6de8a8b4f17afd4e11c4be8eb1db556506d9c8df`.
Original H1 unmodified S1 MapBuilder Git blob `94655d019fdf9798fa24a350ebf49f8290465ac0`. Existing castle walls are collision enabled with x center ±103, z centers ±44, size40×14×5, y center7.

## Actual STATIC geometry defect found (before true Studio testing)
- H1 original SKY_RAMP_RED x−91..−52 at z43 overlaps solid RED_N wall x−123..−83 z41.5..46.5 y0..14.
- H1 original SKY_RAMP_BLUE x52..91 at z43 overlaps solid BLUE_N wall.
- H1 original SEA_LOW_CAUSEWAY x−99..99 at z−45 overlaps **both** RED_S/BLUE_S solid side walls.
- These overlaps are real source-defined Part volumes; the source code alone does not establish full real player collision, pathfinding, mobile access or successful egg scoring. Thus do not claim "fully playable route" from native source compilation alone.

## Proposed correction — isolated real Luau copy, not official game
`candidate/H1FunWorld_wall_clearance_REVIEW_ONLY.server.luau` copies the *exact original* H1 overlay and changes only the sky/sea route geometry block. Sky: RED ramp (−86,0,32.5)→(−46,16,32.5), horizontal bridge (−46,16,32.5)→(46,16,32.5), BLUE ramp (46,16,32.5)→(86,0,32.5), 12-stud ramps and 16-stud bridge. This keeps ramp approach footprint z≥26.5 clear of the original team score pads ending at z=26 and wall starts at z=41.5. Sea: causeway (−72,0,−55)→(72,0,−55) plus free surface return corridors at x±72 from z−55 to z−20, with short center-only safety rails leaving junction openings. Both concept routes connect back to existing original physical ground/egg/pads and preserve original current two roles, current single Game authority and all creature systems. **Only Studio can confirm real avatars traverse and carry the egg.** If any new trap/LOS/physics failure is found, reject/revise candidate; no existing live source is rewritten.
Important: the candidate is intentionally kept *outside the Rojo project's mounted src tree*. It must never be interpreted as #248's updated H1 implementation.

## Regression and real ownership
Run locally in a clean checkout: `python3 -B -m unittest discover -s handoffs/P0D-H1-ROUTE-OVERLAP-QA-20261113-01/tests -p 'test_*.py' -v`.
The fixed actual H1 source and unchanged original MapBuilder are re-verified by exact git-blob SHA; geometry tests check 4 original wall intrusions (expected negative), 0 of same collisions on the candidate, route continuity, slope, x/z bounds, sea connector clearance, preservation of source code outside route art, and 8 deliberately unsafe candidate mutations, including a score-pad-occluding sky-ramp regression. This is math/source QA, NOT real Roblox Studio physical movement.
H1 #248 writer may choose to incorporate only after review. The sole #220 RC writer separately decides official adoption; no direct main/merge/Roblox publication or payment. Future private actual Roblox Studio pass: test both roles + both teams with/without egg, score pad and core attack LOS, two routes when the other is closed, fall/respawn, Guardian trap legality, low-end Android FPS, kid fun H0/H1, and normal Studio shutdown. Never mark those PASS before actual evidence.

Parent #222 G1–G4=4/8=50%; P0D official #220 last S1 75/100; this optional QA gives neither a release score increase nor validated child play.
