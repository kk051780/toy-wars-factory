# GQ470 FB-015 — Twin NPC silhouettes (REAL69 A PREP)

This is a **game-source patcher**, not a QA-only proposal. It creates replacement Luau for the EXISTING ServerScriptService/EGGRUMBLE_LegacyTwinBiomes Script, modifying only makeGuide body, eyes, crest and ornaments of eight already spawned neutral NPCs. It does not modify the coral-garden route or bonded companion.

- Four massing patterns: bubble AWARIN, upright coral SANGORU, angular-accent thunder RAIKO, wide cloud KUMONON.
- Real existing 3D Parts keep their original count. SmoothPlastic reduces Neon overdraw; antler/horn CFrame angles distinguish existing silhouettes without new assets.
- Same eight actors, same PrimaryPart, same server ProximityPrompt, practice/Bond authorization, collision and motion path. No new Game, Remote, Store, HP, score, paid action or runtime scripts.
- Studio appearance, readability and Android performance are **not proven**.

## Isolated test

Run:
python3 quality_gameplay/gq470_twin_npc_silhouettes_real69_20261121/patch_twin_npc69.py --fixture quality_gameplay/gq8_rc85_twin_biomes_real68_20261119/EGGRUMBLE_LegacyTwinBiomes.server.luau --output /tmp/twin_npc_candidate.luau --report /tmp/twin_npc_qa.json

Fixture testing uses only historical authored source anchors, rejects nine mutation inputs, and labels the report FIXTURE_ONLY_NOT_FORMAL. It is **not** an admission packet for the sole formal RC.

## Exact official REAL69 admission prerequisite

Only formal branch at authoring: rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f.
The selected LegacyTwinBiomes source after prior adopted reef revision must SHA256-match c8a78277b74669caebfb7ac6e1dc18f065c537f2da00cf22d8fd7fbca0bf5a00 before the --source option can emit the real candidate.
Do not substitute original historical REAL68 or an RC85/86 candidate.
Then prove 1/69 changed, 68/69 selected source bytes+class unchanged, Native Luau ON/OFF69, Rojo actual Place ON/OFF69, original OFF69 Place byte-exact, 17 family anchors and 48 legacy inventory, source lock/rollback and same HEAD CI. GitHub fixture CI alone **does not** establish those results.

## Non-overlap and handoff

- Unique #218 scoped soft claim: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7052312373
- #921 TwinBiome reef+sign touches a different block within the same selected script; B must re-check current head and source conflict instead of merging entire PRs.
- #910 P0 first, then already verified #931 six ART sources, then #250 admission decision for this candidate.
- Only #220 authenticated B writer may exact-source select and fresh expected-SHA non-force CAS into the formal RC; no main writes, force, publish, payments, or Work/Codex consumption.
- Current A status: PATCH_CREATED, FIXTURE_CI_PENDING; P0D_PREP_READY_V1=NO, RC_INTEGRATED=NO, SOURCE_NATIVE_ROJO=NOT_TESTED, STUDIO/ANDROID/FUN=NOT_TESTED, OLD_NEW_ART_PNG=0/32, OWNER_ACCEPTED=0.
