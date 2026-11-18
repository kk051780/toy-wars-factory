# GQ800 CurseConversion live runtime — successor to #801 / #815

FEATURE_ID: `GQ800_CURSE_REAL44_SINGLE_SWARM_20261119`.
Target formal RC: `rc/p0d-s1-kids-rc01`.
No new neutral spawn authority, no remote, no DataStore, no duplicated damage owner.

This is the **one missing gameplay bridge**: #801 already has the immutable Pure Luau curse policy and #815's genuine source43 already has 8 neutral personalities and real hit/KO reactions. This lane only selects the existing original #801 policy as one ModuleScript and applies a scoped overlay to the **single original #815 Swarm**. Source43→44: 42 original scripts byte-identical; only Swarm changed + one original policy source added.

When a live ZOMBIE successfully hits an existing neutral, the original owner-controlled HP loss produces a unique server hit receipt. At HP ≤35%, second sigil (fourth for BABY_GOLEM) converts that **same Model**; charmed neutrals leave hostile target selection, follow their living owner without walking through solid walls, and attack other neutral models at max 8HP/1.5s through the existing Swarm. Same original KO credit route. Aura uses one occluded Highlight per converted neutral, no full-screen HUD. Death / 14s expiry / owner death, team-castle death / role change / round end destroys aura and restores enemy selection.

**Current deliberate limitation / YELLOW:** Original #582 per-owner summons aren't exposed to this selected Swarm as a verified authoritative count. To avoid total >4, the original three summon slots are *always reserved*; therefore only **one** converted neutral can follow a ZOMBIE in this first bridge. Requirement for dynamic **up to three** neutral conversions and GUARD/FOCUS cross-source orders remains incomplete, not a tested claim. Next successor must source-select #582's real count and orders without creating a second AI authority.

Source gate:
- Immutable source43 original #815 Git blob `0f4774c543d60b91c261cc6e871d77aa937149cb`.
- Original #801 CursePolicy Git blob `0bd81a807ff6a935642a660b9fe9e0fd05ef484c`.
- Exact original REAL43 artifact: run 44372491757, 43 original source/class. Not formal RC.
- This branch's new source is `EGGRUMBLE_SwarmCombat_Curse44.server.luau` as **working source text only**; selected portable project's correct Roblox class is `ModuleScript` from generated `EGGRUMBLE_SwarmCombat_Curse44.luau`. No accidental Script-class install.
- Workflow `gq800-curse-real44.yml`: actual source44 Native Luau, unchanged original43, actual Rojo source/class, OFF43 byte-exact, policy negative cases, source-lock.
- Flag OFF/rollback: select original portable Real43 and delete Curse module; existing source42 ancestor remains unchanged.

**RC adoption:** Only authenticated nonforce fresh-expected-SHA CAS with same official HEAD build evidence can mark integrated. Until then, this is *private candidate*, not actual official RC. Studio2client / Android15min / art / FUN are NOT_TESTED. Never merge to main or publish/charge.
