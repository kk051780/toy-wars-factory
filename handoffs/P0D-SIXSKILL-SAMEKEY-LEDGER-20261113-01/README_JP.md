# P0D — six-skill atomic SAME-PROFILE ledger (optional isolated adapter)

**Status: SOURCE/QA PROTOTYPE, NOT MOUNTED IN GAME, NOT OFFICIAL RC.** This is an independent, new lane and **does not** assume the authorship of original Store/Game, 47-script private Place, V4 training feature, or #220 sole official RC writer.

## Exact author-source pins
- Original V4 scheduler SOURCE Git blob: `a00caf954aacfca03c92a75b0165c1bafd4de8fd`.
- Original V4 XP preview SOURCE Git blob: `ceb8f4f6caca37954cb3d61ef3e1756368b966e0`.
- New unique proposal `src/SixSkillAtomicProfile.luau` Git blob: `aeadd5a8e0d367ddfa639df161843f9a74637c87`.
- Original canonical real H1 private47 source `PersistentHatchStore.luau` source length **20277**, SHA256 `2485b6e5c0f14383c03d2ee7f3a6a38eebbd05793630497cf54a34254c57fa8a`. Local private QA ZIP includes exact original source and generated complete proposed Store. **Repository original Store is UNCHANGED.**
- Actual original private47 game base: `4f6c335508ffb6dd9939b1664256c917e1c9e199` (author native+Rojo47 PASS); original binary optional candidate, not formally product selected.

## Real new SOURCE implementation
`SixSkillAtomicProfile` provides pure `blank/valid/clone/settle` on the six original disciplines, without DataStore/Remote/Marketplace calls; it uses exactly the original training scheduler and XP formula. A proposed four-hunk patch `proposed/PersistentHatchStore.patch` shows how original Store *owner* may insert the new optional `trainingV4` field in the SAME schema1 canonical profile and SAME original full `U_<realUserId>` key. Never add a second Profile/Store writer. The changed `normalized()` must copy optional `trainingV4` or existing hatch/equip/round writes otherwise erase the new field.

Server-certified grant MUST be assembled **only by original Game** after verifying station, alive/team/no egg/physical position, same-server friends, 30-120 measured seconds; never trust a remote boolean. UpdateAsync callback is pure, stable replay receipt and daily focus usage processed atomically; reject duplicate ticket, overlapping cross-server time, malformed/old day, large batch, ledger overflow. Every skill's XP is cumulative with LEVEL30 saturation; no paid chooser, PvP multiplier or client-granted rewards. Existing original two-pad H1 saved profile isn't silently changed or migrated; owning team must design that mapping.

## Actually tested, versus not tested
- Local Python exact-source 4-anchor Store contract **15/15 PASS**.
- Downloaded verified pinned upstream Luau source archive SHA256 `bdcd0c46226a501ad8f02e92ba8aaa6990ff7b0b97fb4edb3c1428e81e638ed9`, built native compiler/interpreter locally because upstream prebuilt GLIBC incompatible. **5/5 actual native Luau syntax compiles PASS**: original Scheduler, original XP, new Ledger, proposed whole Store, actual generated test harness.
- **69/69 native Luau runtime assertions PASS** against original two V4 author modules, new Ledger, original complete Store+exact 4-hunk proposal in a mock `UpdateAsync`. Includes focus->random cap, friends, duplicate receipt, multi-server overlap, pre-schema1 blank, same original key, duplicate UpdateAsync, hatch grant and equip preserving six-skill ledger. Local full pack with original raw source, proposed full source, exact native runnable test script and compile/build command is available to the user: `P0D_SIXSKILL_SAMEKEY_LEDGER_PRIVATE_QA_20261113.zip`, SHA256 `8ac224c660f899cef8e6488f533dc192a41b2a84ba740fd92cfa12b4f421aab5`. Native binary/compiler itself is NOT shared.
- **NOT TESTED:** Roblox engine Studio 1/2 client, actual live/test DataStore API, Android/OWNER FUN, V4 Game pad->profile grant wiring, real persistence after reconnect. **No private Studio Place artifact of this proposed adapter has been generated, and author Store/Game not modified.** Never call this an already released persistent six-skill feature.
- Existing V4 author's optional 47-script training preview `2cc2fa5b2f0026cf938438826e20e016a3a70b0a` remains *SESSION_ONLY, and its real 6 XP levels STILL RESET on reconnect*. Our source does not magically change that.

## Next integrator / DRI gates
1. Original `PersistentHatchStore` + original Game/Dojo two-skill owner to review and test exact four hunks/atomic profile migration, cap, value bounds and old two skill compatibility. Do not switch Store author.
2. #219/#250 product DRI to decide which private H1 build deserves actual trial; selection remains NO for rich47/V4 and original B42 only private baseline selected. Owner tests in unpublished real Studio then Android, actual same-key save/reconnect, duplicate receipt, friends, daytime bucket and FUN.
3. Sole #220 RC integrator may adopt narrow reviewed changes only after official product decision and independent real QA; no main/merge/Roblox publish/paid, additional spend, PC/Codex or five automation changes.

Last official S1: `1263a03701211a652b99b91d2339575dc8104eff`, 75/100 FUN_NO_GO. **Own source package acceptance: 4/6 (67%)**: source+proposal+local native+GitHub readback; actual game wiring and Studio datastore verification missing. This is NOT game-release progress.
