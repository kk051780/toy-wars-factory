# P0D #470 FB026 real game source-composite RC86

**What is actually implemented**: On immutable GitHub-Actions compiled native85 staging source (original seven physical role weapons, castle 3-hit siege/gate AI, stolen-egg return AI, solo team bots, Trapper 2-point portal, original Beast follow), preserve the already-complete three-stage weapon loot ModuleScript and 6 physical pickup pedestals, while applying only the original previously compiled Necromancer three-undead summon/cycling ATTACK/GUARD/FOLLOW to original Game, plus one new `UndeadSquad` server ModuleScript. No new Remote/score/save/egg owner or second game. The StageLoot BUFF damage and range still passes through original authoritative Game M1 to original Horde:hit / KO / per-user score. The Undead squad uses original sevenJobStrike and real Horde, with server auth.

## Real source provenance

- Exact compiled parent: Actions #43709500167 / artifact #14159797047. `P0D_RC85_3_USEABLE_STAGE_WEAPONS_SIEGE_BEAST_TRAPPER_SOLO_PRIVATE.rbxlx` 832695B, SHA256 `501688966820ae80833a7cae1d5a8b4fc908b9b30062dd1c3f727a356cc15387`.
- New exact source-composite Place: `P0D_RC86_SIEGE_V3_STAGE_WEAPONS_UNDEAD_PRIVATE.rbxlx` **843641B**, SHA256 **`11fa894c4ebfa2303e3f7cef8590d14a6a26f359699b6eda3d2e692bc161c707`**. Actual scripts 86, **84/85 original body byte-identical**, changed `Game`, added one sibling `UndeadSquad`. `StagePickupLoot` is byte-identical. Game GitBlob `9affc8697c55c1b6d0158216bfa75c4e9fa7e36d`.
- Full XML/SourceLock/FeatureLock & independent negative tests **24/24 Python PASS** locally, deterministic rebuild and duplicate source drift refusals.
- Same-HEAD CI validates **all 86** native Luau compilation and Rojo 7.7.1 exact source name, class, path and GitBlob; do not claim PASS until the CI run completes.

## How to reproduce

In this directory: `python3 -m unittest -v test_rc86.py` or `python3 build_rc86.py`. Original `stage_loot_parent85.zip` is the exact two-deep Actions downloaded ZIP and contains source-locked 85 Place. `undead_patch_v3.py` carries the minimum previously verified exact Game hunk. Wrong parent, changed Game anchor, missing StageLoot, changed script body all fail closed.

## Release status / non-duplication

This is a **PRIVATE / SOURCE CANDIDATE**, not official `rc/p0d-s1-kids-rc01`. Never blindly overwrite the newer distinct #476 PRIVATE lineage (physical role lobby, four item types, newer wild beast AI/ride, all-role alternate skills, Mage revive, builder bridge and traps) with this older separate 86 source lineage. #476 actual private binary/source patch is not on public PR #476 as of this build, so #476 functionality is **not claimed as integrated**. In particular #476 has an independent **two-zombie** Q implementation, whereas this compiled line carries **three-zombie** server module. Choose one after source-and-OWNER review; installing both is forbidden.

Official merge/publish/pay: **NO**. Official RC source CAS/writer: **NO**. Studio 1+2 clients: **NOT_RUN**. Android: **NOT_RUN**. 15 minute gameplay/owner Product Quality #470 and Art #420: **NO_GO**. This ZIP is a true Studio source/playtest candidate; test with private accounts before any public release.