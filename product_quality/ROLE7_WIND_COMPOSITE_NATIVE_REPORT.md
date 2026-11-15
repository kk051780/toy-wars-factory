# P0D FB004 7職選択＋風走り 実ソース統合 V1（source native / NOT GAME GO）

Date: 2026-11-15 JST. OWNER #470 retains repair accountability.

## Fixed original author inputs
- Formal RC82 base HEAD: `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34`.
- Exact official RC82 original Actions: https://github.com/kk051780/toy-wars-factory/actions/runs/43677046865 .
- Original 7-class author #297 source-stage Actions: https://github.com/kk051780/toy-wars-factory/actions/runs/43686957256 ; artifact `14149978467`.
- Original author's unpublished 82-script Place: 775,548 B SHA256 `349f5258d1bf10829ace6a0b455acf1b646f89d20ac989a4c5d7ca57c34017ed`.
- Prior FB004 adaptive wind private source: fixed original Game and WindRules blobs. Do not use old unconditional 178/140 wind limit.

## Actual source repair composition
`product_quality/role7_wind_composite.py` pins author Game/HUD/Wind Source blobs, checks 82/82 SHA-locked original source bodies, and replaces exactly:
1. Original author Game WindRules input call with actual server GrassArena Size/CFrame check, behind a default-OFF server attribute `P0D_ADAPTIVE_WIND_FIELD`.
2. Existing `S1RaiderWindRules` coordinate limits with default original 120/65 or trusted existing floor 370x294 allowed 178/140, each checked against world OOB 182/144.
No additional authority / Game / HUD / Remote / Store / eggs / Horde. All original #297 selection ACK, skill-before-job and READY revocation plus old Game fixes preserved.

**Source-exact output:** 82 actual existing scripts; 80/82 source bodies byte-exact versus original author's stage, original HUD exact unchanged. New unpublished Place **777,023 B** SHA256 `4f82548f1213675937fe6e8431cd29031fe37abc5c54ef0ceb02ab7d05e88d9a`. Both SOURCE_LOCK and RC_FEATURE_LOCK match all 82 real source bodies. Game blob `19a5a3a0f24255502f6956e114092d3b4273afcf`, WindRules blob `d66efccbf90028627cd65aa0fb33173506819c11`.

## Real GitHub Actions CI evidence
- PR #471 source QA HEAD `d24bfc8b1449550c9f54d14cffd732b2830fc0e2`.
- [REAL original-author+wind same-HEAD workflow #43687686478](https://github.com/kk051780/toy-wars-factory/actions/runs/43687686478) **COMPLETED SUCCESS**.
- Pinned upstream Luau compiler f46d879e28302a430029304f7f6a162aed66f103 compiled **all 82/82 actual composed Luau scripts**, not just Python static signatures.
- GitHub artifact #14150764660, ZIP 241,524 B; independently downloaded and extracted. Reproduced unpublished stage SHA256 and byte size were **byte-for-byte identical** to independently constructed local Place.
- Malformed input fails closed. No Studio execution, Android playback, AI navigation, 2-client session, art quality, children FUN, or OWNER acceptance from this result.

## Actual status and follow-through
Source repair candidate is prepared and native-compile validated. **Formal RC adoption 0.** The existing official RC remains d2f3ed1a, baseline 82 sources, 772,452 B Place, 243,612 B ZIP. User-facing seven-role full ability quality and physical wind movement are still unaccepted; PRODUCT_NO_GO. No main/auto-merge/publish/paid actions.

#297 original writer should now source-selectively apply the *one wind Game input hunk plus one WindRules policy hunk* atop its latest Game/HUD and other author feature patches, preserving Assassin V5, role7 job ACK, builder, beast/zombie, etc. #220 only does authenticated nonforce expected-head CAS, same-head native/Rojo/Play testing. When 7 job role abilities or wind still fail Studio/Android, reopen same FB004 until OWNER accepts. This report does not confer writer permission.
