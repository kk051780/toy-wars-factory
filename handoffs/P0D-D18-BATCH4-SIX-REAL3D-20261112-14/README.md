# TRAP RAIDERS D18 Batch4 — six authentic manually authored Roblox low-poly 3D previews
2026-11-12 JST | game_id=TRAP_RAIDERS | PRELAUNCH | packet=P0D-D18-BATCH4-SIX-REAL3D-20261112-14

**Six complete 3D part-definition sources + real Luau catalog/factory, source-only preview, not in live S1.** Cannot claim rendered Studio visual or real owned inventory. The 6 gameplay powers in prior design card are proposals ONLY: this code provides no gameplay powers. Parent frozen D18 Batch3 `74dc24dca8510fb10c00df30d5d64e8aec9e8660`; prior editorial designs `8ca5ffbd142643fa920c9009ebfabc41a7a21a1d`; original atlas SHA256 `cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01`.

| ID | Category/name | near/far Parts | Three far-visible unique cues |
| --- | --- | --- | --- |
| TRCA-BE-036 | 魔獣 / 永久晶ドラ | 15/13 | hex_ice, one_horn, floating_shield |
| TRCA-SP-009 | 魔法 / 鐘を帰す星歌 | 14/12 | broken_star_bell, silver_music_arc, yellow_home_ribbon |
| TRCA-TR-027 | 罠 / 歯輪の跳ね台 | 14/12 | half_copper_gear, big_direction_arrow, double_spring |
| TRCA-VE-009 | 乗り物 / 星帰りの観測台 | 13/12 | asymmetric_three_wheels, star_telescope, visible_seat |
| TRCA-WE-009 | 武器 / 星音ホルン | 13/11 | two_horn_mouths, cracked_star_stone, note_antenna |
| TRCA-ZO-018 | ゾンビ / 森番もこもこ兵 | 14/12 | giant_leaf_hat, soft_cloth_body, mismatched_mushroom_boots |

## Real source and reproducible test
- `src/D18BatchCatalog.luau`: original six authored 3D definitions, deterministic from `data/six_pilot_geometry.json` and `tools/generate_catalog.py`. Intended to map into an unpublished Rojo preview.
- `src/D18BatchFactory.luau`: exact previous safe factory reused, creates only local `WorldModel` preview Part models, anchored/noncolliding/nontouch/nonquery/no shadows. Valid CFrame; cap12; Build, four poses, near/far LOD, 45-degree yaw, GetStatus, Destroy.
- `src/DisabledPilotDemo.client.luau`: opt-in is explicitly `ENABLED=false`. No gameplay server round, NPC combat/AI, inventories, award, Marketplace, DataStore or Remotes.
- `python tools/generate_catalog.py --check`, `python -m unittest discover -s tests`, `python tools/verify_manifest.py` are required **to be executed by CI or a trusted Python runner**; do not count them as PASS merely because source was committed.
- The 36 remaining canonical flagship 3D ID queue is in `data/next54_source_queue.json` (retained historical filename), 30 prior frozen + new6 = 36 source authored, NOT integrated.

## Originality and future integration
Child-readable silhouettes are visually distinct in outline as well as hue. These are display previews only; `S1` has no new monsters, loot, magic, vehicles, weapons, traps, zombies or UI from this batch. Actual Studio/mobile/2client legibility, memory/FPS, no overlap and gameplay symmetry are NOT_TESTED. Neither SOURCE_QA nor any 3D art number increments the official #220 whole-game 75/100 gate. Only #220 sole integrator can authorize future S2+ INCLUDE/SKIP after engine QA and OWNER approval. No main/official RC/merge/publish/paid/Codex/P0A/B/C/5 automations changes.
