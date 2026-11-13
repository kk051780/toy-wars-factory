# P0D V4 six-skill XP/day-cap persistence: integrator handoff (2026-11-13 JST)

**Feature slice:** CHAT-P0D-LOBBY-V4-FOCUS-CAP-SCHEDULER-20261113-01. **Status:** source/FAKE-STORE QA only; no actual Game/DataStore/Studio integration. V4 product #250 UNSELECTED, official #220 RC NO; S1 official 75/100 FUN_NO_GO unchanged.

## Genuine current Store issue (confirmed from source and native execution)
Original other-author H1 PersistentHatchStore.luau SHA256 `8698b06c4344209b4b63758c142aa33c14f382b1260b76a9c738893e67190b24` (full source embedded in original H1 44-Luau saved private Place). `Store.validate` accepts unknown extra `dojoV4` field, but `normalized=function(raw:any)` rebuilds an explicit field table ending `dojo=cloneDojo(raw.dojo)`; it omits `dojoV4`. True native Luau test reproduced extra V4 data being **silently lost when calling unchanged original `Store.grantTransition`**. A direct append without normalized+validate clone is UNSAFE.

## Delivered code / exact evidence
The owner's current ChatGPT conversation has a self-contained ZIP `P0D_V4_SIX_SKILL_DURABLE_STORE_CONTRACT_QA.zip`, SHA256 `d7ca80b6acf600de391690bcf8bc69691d7f2895110662b890eae0ea8d820ea1`. It contains:
- `src/V4DailyProfileCore.luau` exact SHA256 `1d620bd4cb4e...`: pure candidate six-skill microXP cumulative, JST dayIndex+free focusUsedSeconds 1800 cap, deterministic random-cycle state, snapshot fields, revision+receipt token idempotence, fail closed old two-skill legacy. No DataStore/API/Remote.
- `inputs/PersistentHatchStore_BASELINE_H1_READONLY.luau` exact original Store SHA256 above; `inputs/FocusTrainingScheduler_BASELINE_PINNED.luau` exact Git blob a00caf954aacfca03c92a75b0165c1bafd4de8fd.
- `docs/PersistentHatchStore_V4_SHADOW_OWNER_REVIEW_ONLY.luau` SHA256 `d7e45a6222348d6d66b16b9b3035aa7a7cd002ded7684468e50b744b3b274f28`: copy of original Store plus proposed patch in **isolated test folder only**. Does not overwrite another owner's real code.
- Exact proposed patch: <https://github.com/kk051780/toy-wars-factory/blob/292123ca0290f33a23c592b500d04069a1d24568/handoffs/P0D-LOBBY-V4-FOCUS-CAP-20261113-01/docs/PROPOSED_STORE_OWNER_PATCH.diff> Git blob `7c60c93e18c431fad0d174d795bf0aea99253f41`, readback equal local Git object hash.
- Tests and builder: true pinned native Luau original Scheduler+Core **63/63**; native actual original Store vs isolated patched Store + fake atomic UpdateAsync **40/40**; Python static guards **12/12**. Total 115 checked assertions/tests. ZIP clean extraction and rebuild+all three tests also PASS.

## Ownership / mandatory acceptance
1. Existing canonical Store owner `CHAT-P0D-DOJO-CANONICAL-PROFILE-PERSIST-20261113-01` ONLY may implement `dojoV4` in the **same original Hatch profile and same UserId key** using real one-session exclusive lock and atomic `UpdateAsync`. Do not add a second Store or a competing Game.
2. In that owner code, update **both** `Store.validate` and `normalized` so original gift/equip/evolve/progression transforms preserve new fields; keep old schema1 records valid.
3. **Saved BEAST/WEAPON H1 Lv5 progress has a different cost curve from proposed V4 Lv30. Do not wipe or automatically convert it.** Core `newForUntrainedUser(day, existingTwoSkillDojo)` explicitly refuses it, returning `LEGACY_TWO_SKILL_MIGRATION_REQUIRED`; product owner must choose a reviewed conversion or coexistence mapping before any real user migration.
4. Each server-generated positive training tick (<=120sec) must provide exact skill and friend multiplier and per-day bucket; **split ticks at JST midnight**, never accept client XP/friend count/time. Rejoin must restore saved quota/XP but never award offline training. V4 profile receipt version and random state must survive item grant and equip.
5. Atomic write must return trusted `SAVED` only after real successful UpdateAsync; negative/fake Studio users LOCAL_ONLY. Native fake Store test is **not** engine/DataStore certification. OWNER must test actual Studio positive UserId + private API save/logout/rejoin, 2-client friend bonus/competitions, error recovery, Android and FUN after #250 selection.
6. #220 is the ONLY official RC writer. No main/merge/publication/live paid/extra spending/OWNER PC/CAS/P0ABC/five automations changes.

**Next owner:** review the exact proposed patch and current Store normalizer drop; formally choose migration and server lock strategy, then build one private full Game with real saved V4 on Store owner's own branch and CI/native/Rojo QA. This author has not claimed this is complete.
