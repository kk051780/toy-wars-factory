# GQ8 boss result｜既存31源・実カウントだけ表示

- Feature: `GQ8_BOSS_RESULT_TRUE_CREDIT_20261118` / #470 / FB-008 / #420
- Unique scope: result-only presentation of the existing server-owned Stone Giant defeat count; *not* a new boss/KO/score producer.
- Source of truth: original `EGGRUMBLE_NeutralStoneGiant` invokes server Host `onDefeat`; the original server increments player `EGGRUMBLE_BossDefeats` once per confirmed defeat. Existing GQ514 resets it after each round. The selected `EGGRUMBLE_MatchResultService` retains all original KO/egg/castle score logic and shows a compact `中立 44 / 巨人 2` only for positive recorded boss count. Zero/invalid count preserves previous string byte-for-byte. No additional HUD/GUIs.
- Current canonical parent: `d5f912a7cdf5e7882ed703abee96e4ba03ba356b` 31-source, 54-flag RC with GQ732 and GQ504 already adopted.
- PREP only: the new selected source and independent `.rbxlx` are **not** the official RC Place until the sole authenticated writer #220 advances the canonical selected Place under non-force expected-SHA CAS, increments the feature registry, and verifies *same-HEAD* RC CI + artifact bytes.
- QA: source-inverse OFF `patch/unpatch` byte-exact, 30 other modules untouched, 31 actual Luau compilation, 31 real Rojo Script/Class/Source exact, native positive+negative 8 cases and failing mutant. Source-only verification is not Studio/Android/FUN/OWNER acceptance.
- Rollback: unselect this one result source. Keep GQ732 decor, GQ504 hit audio, GQ514 boss counter reset, other 30 scripts, and older S1 `rich51` byte-identical. No changes to main/Publish/paid actions/Roblox Studio.
- Integrator `#220`: adopt *only after* latest official RC head/source/PR/flag check; if head drifts, recompose from newest existing GQ732 result source, run same HEAD verified workflow, record `RC_INTEGRATED` only after canonical Place selection. No original author ACK needed.
