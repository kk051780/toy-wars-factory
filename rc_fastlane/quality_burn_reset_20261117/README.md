# GQ8 BURN REPLAY RESET — Current31 source-only RC candidate

**Scope:** Existing `EGGRUMBLE_RoundReplay.resetHuman` ONLY. Original V3 Combat `secondaryEffect` stores `EGGRUMBLE_BurnUntil` to prevent repeated BURN/PREDATOR; the existing replay reset cleared `EGGRUMBLE_OriginalWalkSpeed`, `EGGRUMBLE_SlowExpiry`, `EGGRUMBLE_MarkedUntil` but left `EGGRUMBLE_BurnUntil`. This potentially prevents valid opening burns in the next round when the same avatar is reused. Source-derived risk; NOT Studio-reproduced or confirmed exploit.

- Exact input: **official RC parent** `cd4d41a2a8ad4c856604120281d89dd5bd60ca84` with full `GQ8_MULTI_SHIELD_SELECTED31` from formally adopted #686.
- Unique owner slice: `GQ8_BURN_REPLAY_RESET_20261117`, #218 claim [6946146896](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6946146896).
- The overlay inserts one `hum:SetAttribute("EGGRUMBLE_BurnUntil",nil)` after existing MarkedUntil cleanup; does NOT replace shield cleanup.
- 31 selected scripts, 30 unchanged source bytes, exact inverse to shield-selected RoundReplay. No new Game/Remote/Store, no authority addition, no additional runtime script; original 41 inherited source-backed feature flags preserved.
- Build-time: real 31 Luau compile; extracted true selected RoundReplay native 6 cases; negative mutant expected RED; Rojo source/class exact 31; latest canonical Place now burn-selected; optional32 spectator auto-follows via existing #692 resolver.
- Off rollback: remove this workflow step and choose original `GQ8_MULTI_SHIELD_SELECTED31` Place, leaving #686 shields, #684 HIT, seven roles, Boss LOS, Builder WALL, eggs, lobby, AI etc intact.
- Studio2client, Android15m, art/fun, OWNER acceptance: NOT TESTED.
- **Formal RC adoption is pending**, only #220 authenticated single writer uses nonforce expected-SHA CAS after candidate V3+S1 green, then verifies two official postpush same-HEAD workflows and actual canonical Place bytes; no stale branch merge, main/publish/paid.

## Run
`python3 -B -m unittest discover -v -s rc_fastlane/quality_burn_reset_20261117 -p test_burn_reset.py`

Only the GitHub CI has native Luau compiler + Rojo tools. Full source receipt is produced into `artifacts/gq515_official_select/GQ8_BURN_RESET_RECEIPT.json` during same-head CI.