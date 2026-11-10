# P0-D D18 — 648-item collector atlas / v4 wave-2 twelve heroes
As-of 2026-11-10 JST | game_id=`TRAP_RAIDERS` | work_id=`p0d-siege-v19`
packet_id=`P0D-D18-COLLECTION-ATLAS-20261110-01`
revision=`D18-EDITORIAL-12-WORLD-HERO-WAVE2-20261110-V4`

## What was actually prepared
- Original D18 conceptual catalog **648** entries remains byte-identical to its initial private ZIP (sha256 `72486fad3490cb1e71de1f11b7afe55385f95587d305eb61e4ad44395aa82dda`).
- v2: 6 hand-edited COMMON designs; v3: 12 hand-edited flagships; **v4: an additional, non-overlapping 12 hand-edited flagships**, one per lore region and two from each of six families (魔獣/魔法/乗り物/武器/ゾンビ/罠).
- Cumulative individualized design briefs **30/648**, unreviewed first drafts **618**. Flagships individualized **24/72**, unreviewed **48**. This does NOT mean 30 playable models or 30 independently art-approved characters.
- 12 entries have individually authored three-scene stories, original silhouettes, imperfections, touch/win/lose/idles, original sound prompts, family connections, deterministic always-available free unlock proposals, 3D Part+LOD suggestions, and integration protection.
- Legacy `B09` is preserved for `TRCA-TR-099`; it must NOT become a duplicate trap/second ability. Rarity never changes PvP HP, damage, speed or hitbox.
- Offline **42 design assertions** and **36 independently runnable Python unit tests** PASS. These do **not** prove player enjoyment, Roblox Luau compilation, Studio/mobile behavior, artist-rights clearance, or revenue.

## Private owner artifacts — not exposed in public GitHub
**Full self-contained ZIP**: `TRAP_RAIDERS_D18_COLLECTION_V4_PRIVATE_HANDOFF.zip`
- Bytes: **598638**
- SHA256: **`6ebdf5f3bb5de5b84c6fb456331764f2e3f347ca1d8a1b14c75b7903c1260867`**
- Location: OWNER's ChatGPT private Library at `/TRAP_RAIDERS/企画室/TRAP_RAIDERS_D18_COLLECTION_V4_PRIVATE_HANDOFF.zip`.
- Contains exact prior V3 ZIP (which contains V2 + base 648), the V4 twelve-item JSON overlay, original story/art bible, summary, structural QA, `test_editorial_v4.py`, workbook, Codex acceptance instructions, and `P0D_D18_V4_BUILD_MANIFEST.json` with all 8 component lengths and SHA256s.

**v4 workbook**: `TRAP_RAIDERS_COLLECTION_ATLAS_648_v4.xlsx`
- Bytes: **193593**
- SHA256: **`7f3b5b7fea7c5fc5c5e2641e1bd96f44c4e73d7b5bca4436e06b0804c360114f`**
- Location: OWNER's private ChatGPT Library `/TRAP_RAIDERS/企画室/TRAP_RAIDERS_COLLECTION_ATLAS_648_v4.xlsx`.
- Preserve the original 648 records, earlier v2/v3 sheets, add new twelve, detailed character cards, formula-driven v4 progress and collection-experience design.

The **PUBLIC** branch has only this README and a safe checksum manifest. **The full ZIP, XLSX, unpublished original stories, game source and any keys have NOT been sent to this GitHub repository.** A GitHub URL here cannot deliver the ZIP to the Windows PC; OWNER must transfer the private ZIP securely and verify SHA256. GitHub Issue comments never launch Codex.

## Safe Windows Codex contract — owner instruction required
1. Re-read #218 latest coordinated claims, #213 latest real PC source+Studio report, #217 P0 authorization and the active integration queue. Back up and compare the real saved PC source/Place SHA; never override local latest with reference artifacts.
2. Only when OWNER explicitly authorizes, securely receive ZIP, verify outer SHA256 + inner `BUILD_MANIFEST` SHA256/size, reject symlink/path traversal and preserve original V3 hash `a490615a6a3d82b8d9f2e7eec6d52edb4bb5c94d049a41aa907fc25c9d5b60ab`.
3. Run extracted `python test_editorial_v4.py` (36 tests expected). Treat that as **offline data integrity**, not live Studio or UX evidence.
4. First inspect original D01 match, D06 free stamp, D07 boss, D11 zombie, D14 vehicle, D17 cosmetics and existing B09 trap. Do not duplicate gameplay ownership.
5. Future optional smallest 3D test, only after owner's explicit instruction and existing gates: **two noncombat static lobby/library visual previews** SP009 (`鐘を帰す星歌`) and TR099 (`ぼよん跳ね玉`, legacy B09). NO new combat trap, 2-seat vehicle movement, server rewards/ownership, payment, live analytics, or stat increase. Asset status remains NOT_CREATED until real Studio verified.
6. Test phone silhouette legibility, reduced motion/mute, 3-second recognition, initial-load time, FPS/memory, actual Studio Play/Stop/save/normal close. Mark any unrun scenario NOT_TESTED.

## Design sources / scope
- [Roblox official Core loops](https://create.roblox.com/docs/production/game-design/core-loops)
- [Roblox official Onboarding: goals and moments of joy](https://create.roblox.com/docs/production/game-design/onboarding)
- [Roblox official Performance](https://create.roblox.com/docs/performance-optimization/improve)
- Original D18 claim: https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6753347530
- Market/design ledger #219, PC evidence #213, cross-P0 security #217.

**RELEASE / main direct push / merge / new real-paid products / random paid eggs / P2W / added spend = HOLD**.
