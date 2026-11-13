# P0D RC58 WCS-F01/C01 official-RC57 rebase (isolated candidate)

## Source provenance
- RC57 **exact base** `34d6d384d04ba1d4a394331a3e5c74f798e57a22` / hosted Actions [43508562967](https://github.com/kk051780/toy-wars-factory/actions/runs/43508562967) SUCCESS. Authentic ZIP artifact 14076842489 SHA256 `552c506ef2812b220285f716562edfb17cdb285fc985b4cacec82996c88ecbdf`, authentic RBXLX SHA256 `15521b7dadbd96c0ef1ed12367b5fcf2f3738c4428ebf2fb8c43532b39b8b1a8`.
- Exact author #293 / Draft PR #294 source from prior RC56 prep (blob `c3cf119e26ab0241a7bd2b0b25acca75a4250e10`), upgraded **only** by #295 gate closing safety source blob `3edcb19d91de509afd3de227cbfbca5d75125ec2` (whole bridge occupancy -> gate-zone only, cooldown from actual close). Maintains original independent additive world implementation. New combined WCS server source Git blob `331af98fec1b55c74eaa1febe8cb7bc6b580c607`.
- Only one new Script `WCS_CrystalCanyon` inside original `ServerScriptService.TrapRaidersS1`; original **all 57 Luau script texts MUST be byte-for-byte retained**. No additional Game, Store, Remote, egg, score, HP or XP authority.
- `WCS_F01_C01_FLOATING_CANYON`: floating canyon, symmetric land-to-SkyV5 ramps, two Moguron prompts, 14-second gate, wait until gate zone clear before closing and start 4-second cooldown after closing. Always-open detour. Studio-only guard and `ServerStorage.P0D_RC_ENABLE_WCS_F01_C01=false` feature OFF.
- Source bytes come from #293/#295 and previous RC56 adapter; this branch is **separate adoption adapter**, not another change to feature-author branches.

## Usage
```bash
python3 -m unittest discover -s handoffs/P0D-WCS-F01C01-RC57-REBASE-20261114-01/tests
python3 handoffs/P0D-WCS-F01C01-RC57-REBASE-20261114-01/tools/build_from_rc57.py \
  P0D_RC57_OFFICIAL.zip P0D_WCS_F01C01_RC58_PRIVATE.rbxlx receipt.json
```

The builder hard-rejects a different ZIP, duplicate script, changed Game/Remote, source drift, or script count mismatch. Produced private RC58 is a **source-edited Roblox XML candidate**, not an official #220 RC and not evidence of an actual Rojo/source-lock official build. A branch-only read-only Actions job is required for independent native Luau compilation / artifact proof.

## Only #220 may integrate
1. Re-get live canonical RC HEAD + exact GitHub Actions conclusion; if advanced, **rebase again** (do not copy an older private Place over newer Game).
2. Verify this sole script against actual source lock, #295 safety behavior, map existing model/sky walk, and independent OFF rollback. Add it to official `rc_fastlane` as a single optional script.
3. ONE official native 58/58 and pinned Rojo source-exact CI on the new current HEAD. Reconcile registry/catalog **only after pass**. Original 57 code and saved BEAST/SCOUT SPECIES must remain intact.
4. Studio 2client/Android/real persistence + owner FUN are **NOT_TESTED** and remain mandatory before first release. Last S1 quality 75/100, FUN_NO_GO. No main, merge, publish, paid, cost, or PC operation.

**Work ownership:** isolated source-only branch; no canonical RC write, no automatic PC or Studio command.
