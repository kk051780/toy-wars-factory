# TRAP RAIDERS — D18 Batch6 six-worlds original 3D collectible preview source
2026-11-13 JST | P0D-D18-BATCH6-SIX-WORLDS-20261113-01 | PRELAUNCH S2+ | PUBLIC_SOURCE_V1 / NO KEY

Source claim https://github.com/kk051780/toy-wars-factory/issues/219#issuecomment-6837674703
Predecessor immutable Batch5 9049cd8edf66f565c76683543fcc3b8590c773af
Original canonical Atlas sha256 cf5ec26836842ce55a764c5ad66c711f00da0ed4cc30d80dad0df851e2656e01

These SIX original hand-authored source-only miniature WorldModel 3D previews intentionally have different silhouettes, story hooks, colors and bounded motion poses:
| ID | Name | World | Rarity | Near / Far | 3 recognizable silhouette cues |
|---|---|---|---|---|---|
| TRCA-BE-099 | 夢菓子の空竜 | 夢菓子の遊園 | レジェンド | 14 / 12 | star_wing; lollipop_tail; jelly_crown |
| TRCA-SP-108 | 七鈴の光 | 暁鐘の王城 | レジェンド | 16 / 16 | seven_bells; golden_halo; sunbeam_ribbon |
| TRCA-TR-072 | 布跳ね台 | 月縫いの墓園 | レジェンド | 14 / 13 | stitched_crescent; pillow_bounce; up_arrow |
| TRCA-VE-054 | 海鐘の灯台車 | 泡音の水都 | レジェンド | 15 / 14 | lighthouse_roof; coral_wheels; anchor_bell |
| TRCA-WE-018 | 葉笛ホルン | 苔灯の深森 | ミシック | 13 / 12 | rolled_leaf_tube; mushroom_keys; butterfly_note |
| TRCA-ZO-099 | 観覧車の呼び込み兵 | 夢菓子の遊園 | レジェンド | 14 / 13 | ferris_hat; ticket_flag; uneven_shoes |

They have editable hand-authored part specs and actual generated original Luau. 86 parts total in near LOD; far keeps all three distinctive traits per character. Poses are static group transform previews, NOT real combat/AI animation.

## Repro / safety
`python3 tools/generate_catalog.py --check`
`python3 -m unittest discover -s tests -v`

The factory is the **byte-identical previous safe original D18BatchFactory**. Its Build accepts a WorldModel only (typically in a ViewportFrame), cap12, bounded CFrame, anchored and no collision/touch/query/shadow; four poses, near/far, yaw 45deg and Destroy. This batch contains no gameplay authority, Remotes, server spawn, actual ride/trap/damage/effects, inventory or purchase/loot/reward. Standalone Rojo project maps original catalog+factory; test demo is explicitly OFF. Real Roblox Studio2client/phone/human NOT_TESTED until verified.

Counting: previously authored42/72 (not all CI qualified); after this new six original preview sources48/72=66.67% authored, 24 unmodeled. These are NOT integrated into official release S1, which last sole #220 audited75/100; no production live release without OWNER.
