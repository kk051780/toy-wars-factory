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
5. GitHub Actions workflow p0d-art-quality-gate.yml downloads an **exact, verified artifact ID**, checks the real .rbxlx and emits ART_CHECK_REPORT.json. On a PR it waits, for at most ten minutes, for the newest matching p0d-rc-fastlane.yml run for that exact PR head and base. It requires success, the compatible PRIVATE80 Place and its same-run ART receipt, including the current synthetic merge SHA. A newer pending/failed run never falls back to an older success. Manual dispatch requires an explicit run ID and artifact name, with no expiring historical default. Strict mode FAILS on missing image evidence; preflight can be green with the explicit ART_NO_GO verdict.
6. Reviewer examines screenshots and Studio capture authenticity. Only an explicit OWNER acceptance linked to #420/#372 ends ART_NO_GO. Current [#1011](https://github.com/kk051780/toy-wars-factory/issues/1011) and [AGENTS.md](https://github.com/kk051780/toy-wars-factory/blob/18e4b04eb550ebf5195c3e287f97076dd9c92b6e/AGENTS.md) govern the exclusive development-RC writer; actual scoped authority, independent review and fresh non-force CAS are tracked in [#220](https://github.com/kk051780/toy-wars-factory/issues/220). ART OWNER acceptance remains separate from technical RC adoption.

## No-go rule

### Artifact identity and coverage

`resolve_artifact.py` checks the repository, producer workflow, PR number/head/base,
latest run attempt, and unique non-expired artifact metadata. It downloads the
selected IDs with the runner's read-only GitHub client, checks the ZIP byte count
and SHA256 against GitHub's digest, and requires exactly one real Place. PR inputs
also require matching Place bytes/hash in the source receipt and same-run ART
report, plus matching run ID, PR merge ref and synthetic merge SHA. It rechecks the
selection after download; drift, missing inputs or a bounded-wait timeout fail.
The producer also triggers for changes to this ART workflow, so the dependency is
actually scheduled. `ART_ARTIFACT_SELECTION.json` records the checked provenance.

This legacy-compatible 80-script audit preserves its existing authority names and
ten visual categories. It is separate from the current REAL69 composite source
gate and cannot replace that gate or prove current gameplay, Studio execution,
Android performance, child FUN or OWNER acceptance. Manual selection records its
actual producer SHA and is explicitly identified as `MANUAL_EXPLICIT`, not a
same-head PR result. The source/evidence/mobile/FUN checkers and thresholds are
unchanged; missing real evidence continues to produce ART_NO_GO.

Critical flags: missing visuals or stale Place SHA, blank/reused photos, scores below 4, obstructive leaves/meshes, unreadable Android, inadequate frame rate, generic placeholder art, UI occlusion, fake HIT visual, and no Studio test evidence. These remain NO_GO even if scripts compile perfectly. The gate never signs off its own art; result can reach REVIEW_READY_OWNER_PENDING only.

No main write, merge, Roblox publication, purchases, or unauthorized Windows operation. See #364 FB-015 and #372 all-art visual overhaul.

## 2026-11-15 strategy update — child-friendly stylized excellence, mobile hard gate

**Positioning:** Beautiful, instantly recognizable, high-end **stylized 3D fantasy** combined with clear fast combat and strategic egg theft — **NOT** a maximum-graphics photorealistic demo that drops frames on phones. Visual references searched via YouTube query: **ロブロックス リアル**. See REFERENCE_BENCHMARKS_V2.json and MOBILE_KID_WIN_STRATEGY_V1.json. YouTube metadata and stills do not equal full video review; never claim video playback confirmed without timeline/frame evidence.

Three deliberately separate benchmarks:
- **World/character/combat art**: aim >=4.5/5 in real PC Studio view, drawing on Fushimi Castle, Mist, Beyond the Dark and battle action references; measured Android appearance >=4/5 and readable enemy/attack silhouettes. Realism is a *technique*, not an end state.
- **Mobile playability**: 15 min **on actual devices**, not emulator. Low-end Android (2–4GB target) median >=30 FPS, p10 >=25; midrange Android median >=45 FPS, p10 >=30; PC p10 >=45. No crashes/OOM, warm-frame-rate decline <=20% versus initial; touch buttons work. These are initial internal thresholds, NOT official Roblox numeric standards. Actual hardware and scene must be recorded.
- **Kid enjoyment**: use appropriately consented supervised observations without personal identifiers. First move <=15s, visible attack <=45s, actual damaging hit <=75s, egg/castle objective learned by action <=180s; initial play enjoyment >=4/5, solo works, no constant instructional overlays. Do not replace actual user playtesting with scripted benchmarks.

Visual approach: strong castle silhouette, clear routes, appealing monsters, art-directed light/materials and short punchy hit effects before expensive texture/detail density. Reuse meshes and texture assets, streaming/LOD, restrained particles/transparency and smart visual scaling by hardware. Do **not** add permanent labels or more neon blocks to artificially increase quality. Optimize before lowering the visual target.

**Development speed rule:** Every source PR runs fast deterministic native/static checks; independent art workers produce source packages in parallel. Sample a changed scene in each milestone, not all 32 evidence screenshots on every PR. At each official RC art milestone perform full 8 scenes x before/after x PC/Android=32 plus four real motion samples and mobile 15-min + kid first 3-min check. Do not delay unrelated source preparation for owner screenshots; **only the final ART/FUN acceptance is blocked**. Critical bug and unsafe Game/Remote changes remain P0.

**Automation contract:** check_reference_benchmarks.py and check_mobile_fun.py emit honest reports. Even a complete form is only REVIEW_READY_OWNER_PENDING. No automatic metric or metadata can declare ART_GO/FUN_GO; Owner decides after seeing real Android/PC gameplay.
