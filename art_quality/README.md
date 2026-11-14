# P0D ART QUALITY GATE — FB-015 / Issue #420

Status: **CODE PREP ONLY / ART_NO_GO** until verified screenshots and OWNER acceptance. This gate audits the **actual Studio .rbxlx**, not the number of PRs, scripts or gimmicks. It does **not** render Roblox Studio, estimate beauty from source, or fabricate human scores.

## Three-level quality checks

**SOURCE_GATE (automatic, read-only).** Parses the real Rojo Studio .rbxlx XML, verifies one original Game, one TrapRaidersHUD and BattleHUDGovernor, and attack Activated. Records SHA256, bytes, actual script count, and ten category source coverage. Reports Neon/Part/BillboardGui risk indicators only (not beauty scores). Missing categories and duplicated Game/HUD FAIL.

**EVIDENCE_GATE (automatic coverage + manually captured images).** Requires eight camera scenes, BEFORE and AFTER, on PC and Android: **32 real Studio PNG images**. Checks file existence, duplicate/reused screenshots, PNG structure, unsafe paths, resolution and precise candidate Place SHA256. Does NOT claim uploaded pictures depict Roblox or that arbitrary camera angles match; a reviewer verifies.

**ART+PERFORMANCE (real human review).** Each of ten categories is scored separately on PC and Android from 1 to 5. Pass threshold for review: **every score >=4**, zero critical blockers, named real device, graphics settings and 10th-percentile frame rate (targets PC >=45, Android >=25 FPS). Actual route traversal, attacks, camera occlusion, creature readability and game visual quality require Studio playtest. OWNER must accept explicitly; scripts and green CI cannot approve art.

## Ten distinct visual categories

| Category | What has to look/feel good |
|---|---|
| terrain | Three readable strategic routes, scale, slopes, materials and vistas |
| castle | Towers, battlements, gates and recognizable castle silhouette at distance |
| sea | Continuous water, coast, foamy waves, depth and crossing |
| forest | Varied foliage, depth, path readability and no camera/movement blockage |
| neutral | Basic/elite soldier silhouettes, equipment, hit response and animation |
| beast | Giant creature identity, scale, material, movement and attack telegraph |
| roles | Recognizable jobs, players/AI clothing and animation without huge labels |
| combat | Short responsive effects, visible actual hits, legible enemies and HP |
| lobby | Inviting spawn/hub, easy exit and no permanent battle instructions |
| atmosphere | Coherent light, sky, weather, contrast and Android low-quality legibility |

## Eight fixed Studio observation scenes

| ID | Camera/scene reference |
|---|---|
| lobby | Spawn-facing dojo and start destination at eye height |
| field_wide | Hill/view from which three routes and objectives are recognizable |
| castle | Ground-level enemy gate approach and turrets in one frame |
| sea | Center of crossing, coast/water/bridge visible |
| forest | Actual forest route with foreground leaves between avatar and camera |
| neutral | Normal and elite minions visible at melee distance |
| beast | Active boss at safe fixed approach distance |
| combat | Actual melee event and compact HUD visible; extra hit/miss clips welcome |

For each BEFORE/AFTER pair, reproduce position, camera direction, zoom/FOV, weather and phase. Capture unedited PC >=1280x720 and landscape Android >=720x400 PNG, at the actual game settings listed in manifest. Record a real device model and graphics quality. If a scene cannot be captured, mark it as blocked rather than comparing unrelated scenes.

## How to use

1. Copy art_quality/EVIDENCE_TEMPLATE.json to art_quality/evidence/manifest.json. Fill before_head, after_head, after_place_sha256 (the **real candidate .rbxlx SHA256**), 32 PNG files at art_quality/evidence/{before|after}/{pc|android}/{scene}.png, the 20 human scores, both p10 FPS/device profiles, reviewer and critical blockers. Never invent a screenshot, score or OWNER approval.
2. Run: python3 -B -m unittest discover -s art_quality -p test_art_quality.py -v
3. Run source preflight: python3 -B art_quality/check_art_quality.py --place candidate.rbxlx --out ART_CHECK_REPORT.json
4. Run strict evidence gate: python3 -B art_quality/check_art_quality.py --place candidate.rbxlx --evidence art_quality/evidence/manifest.json --screenshots art_quality/evidence --out ART_CHECK_REPORT.json --strict
5. GitHub Actions workflow p0d-art-quality-gate.yml downloads the **exact run/artifact selected**, checks the real .rbxlx and emits ART_CHECK_REPORT.json. The dispatch default is a **pinned RC80 historical artifact**, NOT the evolving latest RC. For a new candidate, pass its exact run ID and artifact name. Strict mode FAILS on missing image evidence; preflight can be green with the explicit ART_NO_GO verdict.
6. Reviewer examines screenshots and Studio capture authenticity. Only an explicit OWNER acceptance linked to #420/#372 ends ART_NO_GO, and only B #220 may formally integrate into canonical RC using authenticated non-force CAS.

## No-go rule

Critical flags: missing visuals or stale Place SHA, blank/reused photos, scores below 4, obstructive leaves/meshes, unreadable Android, inadequate frame rate, generic placeholder art, UI occlusion, fake HIT visual, and no Studio test evidence. These remain NO_GO even if scripts compile perfectly. The gate never signs off its own art; result can reach REVIEW_READY_OWNER_PENDING only.

No main write, merge, Roblox publication, purchases, or unauthorized Windows operation. See #364 FB-015 and #372 all-art visual overhaul.
