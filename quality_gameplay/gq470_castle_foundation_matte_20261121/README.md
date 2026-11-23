# GQ470 FB-015: matte castle foundation (A source candidate, not formal RC)

One visual-only LocalScript (`EGGRUMBLE_CastleFoundationMatte.client.luau`) adds **8 faceted stone shoulder pieces per nearest StandardCore** beneath existing TacticalBattlefield castles. It does not create a new castle or claim a team allegiance. It complements independent existing #934/#956 (castle roof/field), #958 (gate HP), and #978/#979 (flags) without editing their originals.

## Identity and rollback
- Canonical official RC: `rc/p0d-s1-kids-rc01`, baseline `e80973c354f14a0d0088577f3cc1a875454f0f8f`.
- Trusted original PRIVATE Real69 Place: 798,390 B, sha256 `fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934`.
- New **A PREVIEW ONLY** route: `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CastleFoundationMatte` (`LocalScript`).
- All original 69 selected sources remain byte/class/path-identical. New source SHA must be verified against current A head and B packet; earlier ART green CI is **not** transferable across future commits.
- Reverse adoption by omitting this single new route and rebuilding original 69. Never rebase A candidate as a whole PR onto official RC; **source-select only** via certified #220.
- Older visual art source builds must not be labeled deployed Studio/Android or accepted just because compiled.

## Runtime visual invariants
1. Only anchored actual `StandardCore` beneath model/`TacticalBattlefield` counts as a candidate. All geometry local to client.
2. Source limits max 2 nearest castles on Touch (16 new parts), 3 desktop (24 new parts), each with exactly 8 wedges. Range 190 studs and 2.5s throttled refresh. No RenderStepped/Heartbeat.
3. `WedgePart` slate stone + smooth inset, flat muted colors, no Neon, 3D moving lights, GUI/Full-screen prompts, or new downloaded assets.
4. `CanCollide=false`, `CanTouch=false`, `CanQuery=false`, `CastShadow=false`. No egg/AI/castle HP/score/Store/Remote or spawn modifications.
5. Streaming descendant arrival may precede anchored/parent metadata. Track named candidate first and validate later; remove on stream-out.
6. Re-select nearest set as player moves, update positions when original core moves, clean up when a castle disappears or `EGGRUMBLE_ReducedEffects=true`.
7. If no valid LocalPlayer root/camera exists yet, render nothing rather than invent a spawn success signal.
8. Multiple independent art writers may contribute to one scene; B must test #970 ART16/#978 flags/#979 sway coexistence separately before adoption.

## #420 ART-GATE reproducible acceptance, all currently NOT_TESTED
- Studio solo: player actually spawns, can walk freely around castle, foundation remains visible above ground, cannot collide with it or block an egg; no phantom stones after a castle unload.
- Studio two client: identical intended team/castle state, no false RED/BLUE affiliation implied by the neutral stone; observer client’s cosmetic geometry does not appear as a server-created object.
- PC and Android fixed old/new same-view: 8 canonical scenes × 2 devices × 2 revisions = **32 actual screenshots** with immutable build SHA, evidence capture time and device model; inspect castle path legibility and occlusion.
- Android low-end 2–4 GB RAM 15min: median FPS≥30, p10≥25, thermal decrease≤20%, 0 crashes; mid-range Android median≥45/p10≥30 (targets, not measured).
- First-time child fun 3min: 15s movement, 45s combat feedback, 75s true enemy hit, 180s egg/castle objective, 4/5 enjoyment; obtained with consent and real time logs.
- Human PC aesthetics target 4.5/5 and Android 4.0/5; no assistant-generated score permitted.
- If imagery, user feedback, device FPS, or owner acceptance absent, retain `ART_NO_GO`, `FUN_NO_GO`, `MOBILE_NO_GO`, `OWNER_ACCEPTED=0`.

## Admission priority and documentation
P0 playable loop and actual player spawn bug (#980) outrank this cosmetic patch. Existing #970 ART16 source-only candidate also precedes this supplementary source if #220 authenticates and accepts it. Certified sole formal RC writer #220 must independently check fresh HEAD, source/class/route hash, no duplicate claim, and a non-force expected-SHA CAS; only then measure same-head official Place/ZIP and human ART at milestones.

Current scoped claim: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7056924980.
