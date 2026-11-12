# TRAP RAIDERS D18 batch 3 — six original fantasy signature source models

**Public keyless noncombat source only.** Packet `P0D-D18-BATCH3-SIX-FANTASY-SIGNATURES-20261112-12`; new isolated `handoff/` branch. DOES NOT modify S1, prior original factories, 12-character gallery, real inventories, monsters, damage, hits, traps or Robux. All preview model parts are anchored and do not collide or touch, and can be placed only inside local `WorldModel` of a `ViewportFrame`.

Original owner atlas `TRAP_RAIDERS_COLLECTION_ATLAS_648_v8.xlsx` SHA256 `cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01`, original 72 flagship registry unchanged. Previous frozen batch source `d99a18065ec28c11597672fab8931df1cb46160b`, source owner claim #219 comment `6821895304`.

## Newly authored six original distinct silhouettes

| ID | Class | Japanese name | Near/far Part counts | far LOD distinctive features |
|---|---|---|---|---|
| `TRCA-BE-054` | BE | 海鐘クジラ | 18/16 | crescent_flukes, pearl_bubbles, hanging_bell |
| `TRCA-SP-072` | SP | やさしい月の復帰 | 22/16 | stitched_crescent, lantern_thread, return_star |
| `TRCA-VE-099` | VE | 終わらない観覧台 | 24/18 | ferris_ring, open_bench, ticket_mast |
| `TRCA-WE-090` | WE | 時告げホルン | 19/13 | hourglass_bell, clock_marks, sand_capsule |
| `TRCA-ZO-063` | ZO | 炎炉の門番兵 | 21/18 | peak_helmet, ring_key, odd_mittens |
| `TRCA-TR-036` | TR | 六花跳ね台 | 18/15 | sixfold_snowflake, upward_arrow, soft_spring |

Each of six model source definitions has THREE original distinct `signature_tags` retained in far LOD, original Japanese story/rarity/world and no server/gameplay function. This is not a mass-completed 648 catalog or 72 model game release.

## Truthful progress accounting

- Previously produced original source-only 3D preview models: 24/72. Newly authored distinct originals: 6. **Cumulative source-only models: 30/72 (41.67%).** 42/72 are **NOT_STARTED** (queue 6 categories x7; none auto-claimed).
- Source-only preview models MAY FAIL native Luau/Roblox Studio before genuine engine/mobile QA. No native Luau interpreter/parser, real Studio render, mobile FPS, 2-client or child-human preference confirmation was done in this packet.
- Official S1 full game release readiness determined ONLY by #220 integrator; currently 75/100 from its latest audit, with Studio user tests and public release permission still outstanding. This packet earns zero S1 audit points.

## Source files and reproducibility

- `data/six_pilot_geometry.json` original authored primitive Part geometry of six subjects.
- `data/archetype_rules.json` per-class authored visual distinctiveness and far cue contract.
- `data/batch_claims.json` claims current 6 and frozen previous 24 (no overlap).
- `data/flagship72_registry.json` frozen canonical 72 exact names/rarities/worlds/story source.
- `data/next54_source_queue.json` **legacy filename/schema only** for compatibility with previous generator; actual count is **42** after this batch. Queue rows remain NOT_STARTED, grouped 7 each.
- `tools/generate_catalog.py` deterministic generator. Run `python tools/generate_catalog.py --check` and `python -m unittest discover -s tests -v`; both MUST pass.
- `src/D18BatchCatalog.luau` generated deterministic Lua catalog; `src/D18BatchFactory.luau` byte-identical to previous original safe WorldModel-only prototype factory (4 poses, LOD, yaw45, Destroy).
- `default.project.json` standalone optional Rojo map only, sample `src/DisabledPilotDemo.client.luau` intentionally `ENABLED=false`.
- `BUILD_MANIFEST.json`: strict PUBLIC_SOURCE_V1 SHA256 plus length of all other real source files (one manifest, no encrypted keys).

## QA / integration gate

Only #220 sole integrator may choose INCLUDE_OR_SKIP in a future S2+ release, after independent native Luau parser check, Studio visual/multi-client/mobile QA, original silhouettes at 48px and actual child reactions. Never attach to the real S1 Round/Game/MapBuilder/Marketplace/Remotes as a stealth unlock and never delay S1 first public release for optional 3D collectibles. No protected RC/main edits, Roblox publish, spending or Codex PC actions in this packet.
