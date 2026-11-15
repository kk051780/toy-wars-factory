# P0D GAME PRODUCT QUALITY GATE — Issue #470
**Status at creation: PRODUCT_NO_GO / NOT_MEASURED.** This gate measures the *game product*, not script counts or an AI's opinion. It does not run Roblox, scrape competitor maps, see videos or certify art. All third-party KPI numbers are date-stamped and never imply retention, conversion or actual revenue.

## Relationship to existing work
- #470: competitive gameplay, field, combat, roles, retention-loop and fair monetization gate.
- #420: separately required ART/MOBILE/KID FUN real Studio evidence. A source-only PASS never makes #420 GO.
- #364: OWNER feedback ledger, existing P0 fixes before new features.
- #219: A prepares distinct verified features and measurements, never writes canonical RC.
- #220: sole authenticated RC writer, one CAS writer and exact-HEAD CI, no unauthorized merges.
- #218: role split. Avoid duplicate implementations by FEATURE_ID and touched subsystem.

## Measuring before scoring
Capture: game title+universe/place ID, date/version, device/graphics, source URL or recorded play+timecode, same scenario for each title, evidence of measurement and comparison method.
For the field: travel seconds, meaningful walkable routes, reachable branches, vertical alternatives, camera sightline and collisions; compare normalized **travel time** when speed differs rather than claiming unknown stud dimensions.
For combat: input-to-hit latency, kills per 30s, simultaneous valid hits, mob density, recovery, movement skill and summon follow.
For retention: egg captures, mob kills, rewards, subsequent session voluntary replay. Visits and average session DO NOT measure D1/D7; D1/D7 stay unknown until owned telemetry after authorized publication.
For catalog: count DISTINCT modeled-and-usable roles, beast types, weapons and items. A promised list of 100 is not 100 implemented.

**No-guess rule:** Unknown external map size, item count, animation quality, or monetization conversion stays null. No fabricated gameplay scores.
Use `competitors_20261115.json` for initial public KPI baseline; replace observations only with verifiable capture.
Use `CANDIDATE_TEMPLATE.json` per source-locked RC candidate; populate each manually evaluated dimension with proof URLs and a named reviewer.

## Scoring and gate
| Category | Weight |
|---|---:|
| `field_freedom` — 経路・広さ・基地間移動時間・卵を運ぶ逃走余地 | 20 |
| `combat_impact` — 多体ヒット・被撃反応・風走り/重撃/魔獣追従 | 20 |
| `first_time_clarity` — 職選択・HUD簡素化・勝利条件理解 | 15 |
| `roles_collectibles` — 職差別化・魅力的な魔獣/アイテムの実動作 | 15 |
| `replay_growth` — 卵/撃破スコア・再戦/育成/放置報酬 | 15 |
| `ethical_monetization` — 公平で分かりやすい商品価値 | 10 |
| `art_coherence` — 世界観統一（#420は別途必須） | 5 |
| **TOTAL** | **100** |

Full product acceptance proposal: >=80/100, each of field_freedom (>=14/20), combat_impact (>=14/20), first_time_clarity (>=10.5/15), zero P0 defects, and independent #420 ART / Android real-device GO, Studio evidence and explicit OWNER acceptance.
If any dimension is NULL or lacks reviewer / real evidence / benchmark reference => **UNSCORED and PRODUCT_NO_GO**, not 0-invented or PASS. Manual evidence is declared, not inferred from static source. The checker only tests coverage/invariants; a human still audits evidence authenticity.

## Fast lane and integration contract
- PQ-G0: benchmark statistics with provenance, competitor gameplay research **not yet verified**.
- PQ-G1: before feature work, a measurable hypothesis and named source/FB ID/FEATURE_ID.
- PQ-G2: source and proof for changed critical dimension, source-lock, rollback and safety QA.
- PQ-G3: product precheck: no known competitive regression, missing gameplay comparison is **BLOCKED** for major gameplay submissions; source work can still continue. B #220 alone determines if official RC admission is authorized. Do not bypass RC CAS/CI.
- PQ-G4: full game score + actual gameplay Studio + #420 mobile/art/fun + OWNER signoff. No inferred success.

`python3 product_quality/check_product_quality.py --candidate product_quality/CANDIDATE_TEMPLATE.json --report PRODUCT_QUALITY_REPORT.json` writes a machine-readable report and exits 1 while not ready. This intentional negative is NOT a regression and must not be attached as a blocking universal CI step until #220 formally installs milestone gates. A positive exit does NOT prove screenshots or ratings are authentic.

No main writes, automatic merges, Roblox publishing, paid purchases, unapproved PC operations. Competitors' assets/IP must not be copied. No dark patterns or underage gambling pressure.

## P0 field freedom: source-derived baseline (FB-009)
Run `python3 -B product_quality/field_baseline.py --out FIELD_BASELINE_REPORT.json` on the **same checked-out source HEAD**. This reads actual `releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau` and `rc_fastlane/features/owner361_castle/CastleBattlefield.server.luau`, not a hand-edited fictitious map model.
- Original `GrassArena`: **250 × 142 = 35,500 stud²** (ground plan footprint).
- The `CastleBattlefield` script enlarges grass to **370 × 294 = 108,780 stud²** (**3.064×** baseline). **This entire script is guarded `if not RunService:IsStudio() then return end`**. Therefore this expansion is *not proven in a public/non-Studio session*; it is not safe to equate Studio screenshot and published field scale.
- The two named flanks (`NORTH_WOODLAND_TRAIL`, `SOUTH_WETLAND_TRAIL`) center on **z=-112 and z=111**, beyond the original 142-stud deep grass half-span of ±71. Their names/geometry are **not pathfinding or actual reachability evidence**.
- Objective straight-line *lower bounds* derive from the canonical `_SPAWN` (±68,0), `_EGG` (±98,-20), and `_SCORE_PAD` (±82,+20): **136 studs** between spawns, **167.201 studs** from red spawn to blue egg, **184.391 studs** from blue egg to red home scoring pad. Real walking time/path length is UNKNOWN and must be observed in Studio/live equivalent.
- Other overlay/scripts may generate additional geometry. **Do not assert the public live effective map is exactly 250 × 142 from these two files alone**. These numbers describe the base generator and one Studio-only expansion only.

**Required next field evidence:** fixed-version real Place+source SHA, server mode (Studio/private/live), one human and one AI crossing, map bounds query, 3 independent traversable approaches verified using actual Pathfinding/position trace, egg capture-to-pad timing, out-of-bounds/fall/camera obstruction rate, device. Compare with *verified gameplay captures* of relevant competitors, not hypothetical stud sizes.

The scanner is intentionally read-only and cannot approve `field_freedom` or override `#420` / OWNER. Other lanes own actual 3D map, live art, combat, AI. This lane owns only measured field criteria / regression audit.
### Optional real Studio pathfinding probe (not part of official RC)
`product_quality/P0DFieldRouteProbe.server.luau` provides a **one-shot, opt-in, read-only** Studio server instrumentation source for `CENTER (z=0)`, `NORTH (z=-112)`, `SOUTH (z=111)`. It is **not registered in canonical Rojo, nor executed automatically**. To test under an owner-authorized private Studio place, insert a server Script containing this exact source, set **ServerStorage Attribute `P0D_FIELD_ROUTE_PROBE = true`** before server startup, run once, and capture the single Studio Output line prefixed `P0D_FIELD_ROUTE_PROBE_JSON`. Missing/false attribute or non-Studio mode exits without changing gameplay.

The probe makes at most **12 PathfindingService ComputeAsync** calls: for each lane red spawn→midpoint→blue egg and blue egg→midpoint→red home pad. It reports arena dimensions, path status, waypoint counts, path length if found, and why a route was not found. It does **not move characters, touch eggs/score/HUD, grant items, call stores, or calculate player travel times**. Pathfinding success does not prove real player or AI usability; actual traversals and Android tests are mandatory. Failed paths are diagnostic only (could be navmesh settings, runtime scope or terrain timing).

No authorized Studio run has been performed here: all runtime results remain UNKNOWN; do not invent lane success. This probe stays isolated to #471 until #220 and the OWNER decide to stage it.

## 2026-11-15 owner feedback fix-to-pass addendum (PR #471, source-only)
The source gate now requires **15 independently evidenced gameplay scenarios** before `PRODUCT_GO_REVIEWABLE`, including all 7 functional roles, correct player-facing **暗殺者** (with internal `NINJA` retained), egg carry/return/score, many-enemy KO, AI objective play, 3 traversable routes, compact Android HUD, personal results, and manual READY replay. Each scenario record needs a **same-official-HEAD**, date, device, human reviewer, observed effect and recorded gameplay URL; missing, stale or malformed records must be `PRODUCT_NO_GO`. A complete declaration never certifies video authenticity or changes official release status. No official RC or existing Game/HUD/Store writers are altered by this work.

`audit_catalog.py` independently reads the entire **67-row FEATURE_CATALOG**, checks unique IDs, stage vocabulary, all job feature identifiers `P0D-008..015`, and checks whether owner-mandated player-visible `P0D-011` says 暗殺者 rather than obsolete 忍者. The same-head CI uploads `CATALOG_AUDIT_REPORT.json`. Catalog metadata stages `IDEA/SOURCE/RC` do not count as engine-tested: `gameplay_engine_pass_count=null` unless actual separate gameplay evidence is supplied. This catalog report is advisory and **cannot** auto-merge, replace another creator's Game/HUD, or signal OWNER GO. Source-only CI success is not playable quality.

On observed official RC `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34`, the catalog metadata is **31 RC / 26 SOURCE / 10 IDEA**, with no STUDIO/FUN stage. Its `P0D-011` title still contains 忍者 despite #219 owner rename, so it needs an authorized source/metadata synchronization by #220. The actual private Assassin/Beast/Necromancer Game patch candidates belong to their original author #297/#219; this PR deliberately doesn't duplicate them. All human Studio/Android/FUN and OWNER product acceptance remain NO_GO until real tested integration.

### V3: Proof-to-build integrity gate (2026-11-15)
A product candidate must now declare an **official same-HEAD build receipt** in `source_evidence.official_build`: 40-char official RC commit, GitHub Actions run ID + SUCCESS + run URL, archive ZIP bytes, compiled Place bytes, script count, and 64-char Place SHA256. This is a *claim to verify* against GitHub Actions, not a cryptographic proof until an independent reviewer actually fetches the artifact.

The candidate also declares nonempty, unique `P0D-###` feature IDs; its base/source/official commit pins must have valid 40-char form. Every claimed successful gameplay scenario must refer to a recording URL listed in `studio_recordings`, to an observed device listed in `device_models`, and to the same declared official RC SHA. The mobile uncluttered-HUD scenario specifically requires an Android-identified device. Malformed or missing provenance returns `PRODUCT_NO_GO` even for a self-reported 100/100 score. The CI positive test uses explicitly *synthetic example.org declarations*, NEVER genuine gameplay evidence.

Review discipline: cross-check claimed build run/head/actual artifact ZIP and Place bytes/hash in GitHub before treating any scenario as reviewable; then watch footage and test the real Place. A green source-only CI in #471 may not be used to claim in-engine success, #420 art/Android quality or OWNER acceptance. All known role/gameplay failures remain open until a trusted, approved #220 integration verifies true Studio 1/2client and Android behavior. Multiwriter grants are not implied by this validator.

## V4 — Design-to-game trace matrix (2026-11-15)
\`DESIGN_TO_GAME_TRACE_MATRIX.json\` enumerates all **67 catalog IDs** and the OWNER's seven mandatory full-role contracts (P0D-009...015). This is an **inventory of unresolved comparisons**, not 67 verified game features. Each entry retains the old catalog release label, independently marks OWNER-release requirements, links the design source, and tracks required gameplay behavior, actual source file+SHA, same-official-HEAD recorded engine evidence, art gate, claim owner, gap classification, patch SHA and next action. P0D-011 player-visible text is **暗殺者 / Assassin**, while internal role code remains **NINJA**.

\`check_concept_trace.py\` fails closed for missing/duplicate IDs, unverified design contracts, old role names, release drift, source-only coverage, unknown engine behavior, unproven individual role abilities, and missing #420/OWNER approval. All 67 entries currently have **design_contract_status=PENDING_ORIGINAL_REVIEW**, engine proof absent, so the only defensible status is **DESIGN_NO_GO; inventory 67/67, design verification 0/67, full engine-tested roles 0/7**. This new CI check expects the NO_GO report and uploads it; it cannot promote a source count to gameplay quality. The trace will be independently extended with actual #219/#213 contract quotations and authored source/recordings without changing original Game/HUD writers.

This PR changes only the quality gate; official RC/main, Studio, Roblox publication, payment, and other authors' gameplay files remain untouched.
