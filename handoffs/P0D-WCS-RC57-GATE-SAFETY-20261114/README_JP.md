# P0D WCS-F01/C01 — official RC57 source safety handoff (SOURCE ONLY)

**No official RC write, Roblox Studio QA, publication, main merge, or paid feature activation.**

## Known tested base
- Canonical RC: `rc/p0d-s1-kids-rc01`, fixed handoff base `34d6d384d04ba1d4a394331a3e5c74f798e57a22`
- Official exact-head run: https://github.com/kk051780/toy-wars-factory/actions/runs/43508562967, success (57/57 compiled & Rojo source-exact).
- Prior source-only floating canyon adapter original fixed commit: `de60f7024077d4b3135693a4ca5a87ddcd4ee4a7`, unchanged at `handoffs/P0D-WCS-FLOATING-CRYSTAL-RC55-20261114-01/rc56_rebase/src/WCS_Integrated.server.luau`, Git blob `5eb76749414c33c11eb70310b2d1c59c1f945c21`.
- Independent safety fix: https://github.com/kk051780/toy-wars-factory/pull/295 , author corrected standalone source Git blob `3edcb19d91de509afd3de227cbfbca5d75125ec2`, child branch HEAD `dc8f1e038224d1d2d0d64fd9efb0a9c0b1c89303`.

## Exact deliverable
`src/WCS_Integrated_Safe.server.luau` copies the existing floating canyon bridge adapter with **five unique, source-locked, minimal replacements**, including a header correction. It preserves the original accessible canyon at (0,32,-23), SkyV5 bridge approach, equal-red/blue world access, always-open detour, and current independent boot-only OFF switch. #295 semantics are added only to gate occupancy and close-time cooldown: X <= 3.5 studs rather than ±27; the 4-second rearm starts on actual gate closing, including occupancy-delayed close.

Run offline source integrity tests: `python -m unittest discover -s handoffs/P0D-WCS-RC57-GATE-SAFETY-20261114/tests -v` (8 methods). This checks exact five-patch transformations, old original Git blob, server single-authority abstention, and safety invariants. It **does not** prove a native Luau compile or real Roblox Studio physics. Until execution, test result is NOT_RUN.

## Next by sole authorized #220 writer
1. Re-fetch actual RC HEAD (may have advanced), verify clean current-game exact 57 scripts. Reuse only **one new world server script**, never another Game/Remote/Store or the old RC56 Place binary.
2. Do not adopt original raw de60f adapter unchanged: its gate rearm was faulty and PR295 fixed the intended behavior. Incorporate only this corrected script or equivalent proven minimal diff with no old Game overwrites. Preserve OFF switch and explicit SkyV5 dependency.
3. Add the isolated WCS feature to `rc_fastlane/FEATURE_SWITCHES.json` and the build manifest/source lock. Verify one native Luau compiler 58/58, Rojo source-exact 58, negative test of single server authority and no duplicated or removed source. Only after exact new-head GitHub CI SUCCESS acknowledge official RC adoption.
4. Studio 2client, Android, actual DataStore save/rejoin, player FUN are deferred **before initial Roblox publish**, not evidence of source adoption. Historic release readiness 75/100, FUN_NO_GO unchanged.

No merge/publish/paid/main/Automations/owner's Studio actions authorized by this handoff.
