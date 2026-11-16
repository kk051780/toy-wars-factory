# GQ V3 field egg castle clearance — source-only candidate

**Original author #482** HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`; original only host Git blob `7162b209bf67b74a71553217f3f744e072a0365d`. Exact immutable geometry in the original author-owned `EGGRUMBLE_LobbyCastleModesPreview.server.luau` builds 16 personal castle foundations per mode (72×72 each) and 24 physical FIELD_1..24 eggs on a common 8×3 grid.

## Actual defect and isolated fix
Original `z=290+row*200` places **8 of 24 TEAM eggs and 4 of 24 BATTLE_ROYALE eggs horizontally inside a personal castle's 72×72 StandardFoundation** (egg 2.6×3.3×2.6), making field-egg distribution unfair and risking collision/visually embedded objectives. This is exact deterministic source AABB geometry, NOT a Roblox Studio observation. No claim that all twelve eggs are unusable.

Patch ONLY the existing host field-egg row Z coordinates:
- TEAM: `[338,506,610]`
- BATTLE_ROYALE: `[338,448,676]`

Each mode still has 24 original FIELD IDs, 3 unique route rows, 8 grid columns, and the same original Rules `takeFieldEgg`, physical sphere, server Prompt, AI, Score, CASTLE HP, USER/BOT and token authority. No second Game, Boss, Spawn, Store, Remote or Score. Candidate mode row values were validated against all 16 true castle foundations in both modes, the original 890×1050 floor and unchanged HEAL/DASH/SHIELD site coordinates. TEAM additionally checks original central ridge, tree cover and valley landmark.

## Ownership and integration
Own only `quality_gameplay/v3_field_egg_clearance_20261116/**` and dedicated read-only workflow; original #482 file is **never changed in Git branch**. Existing #520 owns *central ridge blocking ITEM SHIELD*, a DIFFERENT defect in the SAME host. Their reviewed source change is to the ridge hunk; ours is only the egg Z hunk. #482 must review both before the #220 single authenticated CAS-writer optionally makes a **source-selective two-hunk composition**, not a blind whole-file overlay.

## Gates
- `patch_field_eggs.py` exact original blob and two-small-hunk source-identity patch; fails closed on changed source or double application.
- Python actual-original-source contract, reproduced old 8 TEAM+4 BR overlaps, repaired zero both, floor/item/ridge/forest clearances, negative mutant, 24 field token and existing item authority.
- `make_native_geometry_test.py` imports the **real new Luau row expression** and executes old-bad/new-good AABB checks using pinned native Luau.
- `private21.py` reuses and compiles the original 21 Game/7-role/field/AI/battle/castle/neutral/ITEM/lobby/balance scripts, changes only one generated host; builds unpublished genuine Rojo Place and verifies embedded Source/class byte exact. Original source suites retained.
- Formal RC `rc/p0d-s1-kids-rc01` remains untouched; OWNER/Studio/Android/ART/FUN NO_GO until human measurement. No main write, merge, Roblox Publish, paid services or PC operations.

**Rollback:** source-select the exact original host blob from #482; remove only the egg-row change. If also adopting #520 ridge correction, undo field egg row without undoing ridge. #220 is the sole official RC writer.
