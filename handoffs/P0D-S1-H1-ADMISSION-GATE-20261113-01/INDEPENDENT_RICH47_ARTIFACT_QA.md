# P0D-S1 independent actual 47-source H1 artifact audit — 2026-11-13 JST

**Result: STATIC_SOURCE_INTEGRITY_PASS / PRODUCT_RC_ADOPTION_BLOCKED.** Independent original private 45 and 47 ZIPs were downloaded through linked GitHub Actions artifact downloads and inspected as **real bytes**. Roblox engine execution was **not** performed; this is not independent Studio/fun approval.

## Original locked inputs
- Baseline 45-luau original artifact: [author Actions](https://github.com/kk051780/toy-wars-factory/actions/runs/43415851018/artifacts/14030858994), archived ZIP SHA256 `55e32af239f0c6ce94db56b65880345f406692720751225b06e0897cb156a186`, extracted .rbxlx SHA256 `96dada63baa2b99e321b5f9eb35a0f335aa22925212e66a8a9b32c48cf5ffd2d`.
- Latest 47-luau real original artifact: [author Actions](https://github.com/kk051780/toy-wars-factory/actions/runs/43427940337/artifacts/14038093469), archived ZIP SHA256 `ba71ab61f63956c7b916becaa08e8fa9cf22109be0ed092a59e74be4b6065ed5`, extracted .rbxlx `P0D_H1_SKYV5_DOJO_RESULT7_PRIVATE.rbxlx` SHA256 `083fb72539472f62aa7c7afe551e20ed4282e3d5fc7172d7511706070eb22f2f`.
- Latest source commit `4f6c335508ffb6dd9939b1664256c917e1c9e199`. Baseline source commit `646cd9bd18b3428235ada06a763f9c5ac65b6883`.
- Both ZIP CRC clean. Real .rbxlx parsed as Roblox XML. Older script counts: 2 Script + 6 LocalScript + 37 ModuleScript =45. New: 2+7+38=47.
- Old SOURCE_LOCK multiset vs 45 **actual extracted embedded UTF8 Lua Git blob SHA1**: **45/45 exact**. New SOURCE_LOCK vs 47 real Lua Git blob: **47/47 exact**.
- **All 45 old script source bodies byte-identical**. Only new `ModuleScript:NextStepAdvisor` + `LocalScript:ResultNextStep`. Advisor actual Git blob `d212dae56b328d48bfed5dafa742caff9afe82c7`, matching original author's fixed source; one existing Game and one H1FunWorld.
- New UI source is Studio-only (RunService:IsStudio guard), 7s delayed dismiss + manual dismissal, server SNAPSHOT display. No new client :FireServer/:InvokeServer, DataStore update, marketplace receipts or new RemoteEvent creation in these 2 added scripts. **Static source review, not dynamic security proof.**
- Independent local Python 10/10 tests PASSED (real archive comparison and negative forged source/ZIP/status tests).

## Real admission gate retested against actual 47 XML
Existing fail-closed admission verifier with the **actual** extracted .rbxlx now reports `static_place_scan.source_count=47`, exact expected SHA256 matched, and no place checksum/count blocker. Result remains **BLOCKED**, as intended, for:
`PRODUCT_NOT_OFFICIALLY_SELECTED, INDEPENDENT_RC_QA_NOT_VERIFIED, STUDIO_2CLIENT_NOT_VERIFIED, ANDROID_NOT_VERIFIED, OWNER_FUN_NOT_VERIFIED, SOURCE_LOCK_VERIFIED_NOT_VERIFIED, SINGLE_AUTHORITY_REVIEW_NOT_VERIFIED`.

The `SOURCE_LOCK_VERIFIED_NOT_VERIFIED` blocker concerns the **latest official #220 RC admission/source lock**, not this already-verified optional private preview lock.

## What this proves and does not prove
Proves **the optional 47-script private file was built, original 45 code preserved, original two added Lua sources present, and static integrity**. It does **not** prove gameplay in real Studio, score/physical terrain, server anti-exploit, Android layout, 2clients, or child FUN. Actual original author Native/Rojo CI PASS belongs to author run43427940337. Formal product private selection remains the original B42 baseline; rich47 optional variant **NOT_SELECTED**, `product_official_rc_selected=NO`. Official S1 last `1263a03701211a652b99b91d2339575dc8104eff`, **75/100 FUN_NO_GO** unchanged.

## Next
OWNER privately tests rich47 and selected B42 in real Studio (solo→egg over walkable sky docks→score, drop/reset negative, BEAST/WEAPON dojo, 7s result card and 2client/Android), #219 Product DRI records H0/H1 FUN & #250 selection, and only #220 sole RC writer may inspect narrow source admission, authority, rollback, independent QA and formal RC update.

No main/direct official RC writes, merge, Roblox publish, actual paid sales, new spend, Windows Codex execution or P0ABC/CAS/5 automations touched.
