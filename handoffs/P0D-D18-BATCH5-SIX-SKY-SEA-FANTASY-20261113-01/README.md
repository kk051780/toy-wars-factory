# TRAP RAIDERS D18 Batch5 — original collectible source-only 3D previews

2026-11-13 JST | PRELAUNCH | P0D_PUBLIC_SOURCE_V1 / no decryption key

## Six hand-authored 3D models, original canonical Atlas IDs unchanged

| ID | Original name | World | Near/Far Parts | Three unmistakable retained cues |
|---|---|---|---|---|
| TRCA-BE-045 | 天鼓の雷獣 | 雷鳥の空庭 | 12/11 | bolt_mane, sky_drum, cloud_tail |
| TRCA-SP-054 | 灯台の大潮 | 泡音の水都 | 10/9 | wave_gate, lighthouse_beacon, pearl_foam |
| TRCA-TR-099 | ぼよん跳ね玉 | 夢菓子の遊園 | 12/11 | striped_candy_orb, visible_double_spring, large_up_arrow |
| TRCA-VE-018 | 祖樹の散歩台 | 苔灯の深森 | 12/11 | moss_canopy, open_bench, glow_lantern |
| TRCA-WE-072 | おばけホルン | 月縫いの墓園 | 12/11 | ghost_sheet, moon_horn, floating_note |
| TRCA-ZO-090 | 迷宮の道案内兵 | 砂時計の迷宮 | 11/10 | hourglass_helmet, direction_sign, uneven_boots |

Each uses original distinct proportions/poses, 3 retained silhouette cues in far LOD, 4 preview poses. The original 72 Atlas registry is pinned by its SHA256 and never renamed. This is NOT active gameplay, not a player-owned character, nor combat or magic power. The six classifications are 魔獣, 魔法, 乗り物, 武器, ゾンビ, 罠.

## Real source
- Hand-authored data/six_pilot_geometry.json (69 Part definitions total, near/far 69/63).
- tools/generate_catalog.py generates actual Roblox Luau src/D18BatchCatalog.luau.
- src/D18BatchFactory.luau is copied verbatim from the pre-existing original Batch4 fixed source; local WorldModel preview only, anchored noncolliding/nontouch/nonquery, cap12, poses, LOD/yaw, and Destroy.
- Standalone Rojo default.project.json, demo explicitly OFF; no new server, remote, combat, catalog ownership, Marketplace, DataStore, reward, Roblox live publication.

Reproduce CI: `python3 tools/generate_catalog.py --check` and `python3 -m unittest discover -s tests -v`.
This source-only preview is an optional S2+ candidate. No official S1 RC integration or native Roblox Studio 2-player/mobile QA, and no game release authorization.

## Bookkeeping
Parent exact fixed source: 882ac638cb3fcac1d396a5249eb43adc49d20710; own claim: https://github.com/kk051780/toy-wars-factory/issues/219#issuecomment-6836979440
Prior D18 source models 36/72 (50%), this wave six -> 42/72 (58.33%), queue30. Whole first-release S1 progress remains 75/100 per #220 latest official sole audit, not incremented by these previews. No existing 36 originals or main/RC/WorldField were modified. No spending, publish, merge or PC Codex.
