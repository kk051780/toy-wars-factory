# GQ8 Mage rescue current-human match membership fence

**NEW confirmed source gap, not a duplicate Mage implementation.** The immutable [#777](https://github.com/kk051780/toy-wars-factory/pull/777) `EGGRUMBLE_MageRevive.luau` checks castle/team/role, player parent and queued mode for the downed target and reviver, but not the existing canonical Host's `session.isCurrentHuman(player)` authoritative current-round membership. This can accept stale participant records after leaving/rejoining the same-mode game while the earlier TEAM session remains active.

## Exclusive change
- Original #777 HEAD `2f4c1e43a7802929de3f633370b32791f7bf8d96`, one original Mage source blob `c75c2db439a5a68f2bc866ad42562fc16687849d` used exactly; patch only two fail-closed check locations **inside the SAME Mage module**: target `current(e)` and both target/healer inside `allyMage(s,target,healer)`. Existing actual Host already defines `session.isCurrentHuman` via original #531 and subsequent RC overlays. If the callback is absent, revival safely refuses instead of trusting client-visible matching attributes.
- One private 31→original Mage32→fenced Mage32, no extra source or separate HP owner. The original Author #777 Host remains untouched. Other 30 base game scripts are byte exact; existing Combat, Castle, Swarm, Items, Lobby, BotActors, result, Realm, Store/XP/Remote unchanged.
- Full source inverse tested: patch removes exactly two additions to recover original #777 Mage module byte-exact; complete feature OFF restores official31.
- Actual original-author Luau VM fixture enhanced with server-supplied membership function. Test (a) stale target cannot enter downed state; (b) stale Mage cannot revive; (c) authenticated current-team Mage still revives, retains original 3s Prompt/40s CD/60s down/LOS/14stud/heal+25 original unchanged. Two source-derived missing-guard mutants must fail with `RED_STALE_TARGET_DOWNED` and `RED_STALE_HEALER_REVIVE`.
- Source-only candidate: real32 Native and Rojo32 Source/Class, OFF original31, sameHEAD formal RC source pin. No Studio2client/Android15/FUN/OWNER acceptance and no claim existing death-at-zero is recoverable.

## Duplication and integration safety
Unlike pre-existing #782/#785 triple/37 and #787 four-lane/39 composition PRs, this closes a specific unprotected **current-session human authorization boundary in the original Mage runtime**. Do not adopt a second Mage policy from #776/#779. Only #220 sole authenticated RC writer can select this source patch on the latest formal RC Host, pair it with #777, #775 and #764, verify Native/Rojo and OFF, then nonforce expected-SHA CAS/readback. Do not merge QA-only PR as a formal RC update; main/Publish/paid remain prohibited. Original authors' individual ACK is not a stop condition.

Status before CI: `PREP_SOURCE_WIP`; RC adoption `NO`.
