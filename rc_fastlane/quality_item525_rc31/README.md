# GQ525 RC31 — existing-author TEAM/BR ITEM membership intake

## Purpose and ownership
- Reuse **existing original author PR #525** source (fixed Git SHA `253aa73530eea5c3954c07b546b67e49292c4639`) without duplicating any item/host authority.
- This adapter source-selects the *exact two original author's source hunks* into the existing **31-script EGGRUMBLE V3 companion** after GQ586 deposit membership.
- Only current single **Host** and **FieldItemPickups** change; all other **29 scripts** must be byte-identical. No new Script, Game, Combat, Remotes, Store, score, or server state authority.
- Baseline at preparation: canonical RC branch `rc/p0d-s1-kids-rc01` at `d2a14b3e4c20918c2a92f1410886c85548123e68` after merged #607 GQ586. Re-fetch before any official adoption.

## Player-facing bug
Original ITEM `canUse` checks a living castle and ACTIVE phase, but an old TEAM/BR session could still retain a roster entry after the person left or switched mode. Source-derived risk: an unrelated-current-mode player collects an item from an old ACTIVE match.

## Fixed author source, reversible selection
- `quality_gameplay/v3_item_mode_ownership_20261116/patch_sources.py` from original #525 (checkout only, no changes) owns the server-only `session.canCollectWorldItem` closure.
- Host checks the current server's `sessions[mode] == session`, `joined[actor.UserId] == mode`, living player and ACTIVE phase.
- FieldItemPickups checks the closure for TEAM/BR; missing or failing callback rejects claim. Standalone preview remains untouched.
- Reuses existing #517 HEAL no-waste, #489 ITEM, #607 GQ586 deposit guard, all previous 7-role/field/combat/castle/neutral/item/lobby/balance authors.
- Adapter `select_existing_author525.py` never rewrites original author. Strict source anchor, inverse hunk, singleton and exact 31-source checks; prove 29 other scripts unchanged.
- Optional OFF/rollback: exclude both original #525 hunks, retaining existing #607 single Host and #517 Item; all 31 previous sources byte exact.

## Gates — distinguish outcomes
1. **PREP**: this PR native compiles exact selected 31 Luau sources, executes existing author #525 source tests, builds actual Rojo and checks the 31 embedded script Sources/Classes, author SHA and inverse rollback. **Do not claim green before same-head GitHub Actions success**.
2. **RC admission**: ONLY authenticated #220 sole CAS writer re-GETs latest `rc/p0d-s1-kids-rc01` HEAD, reconciles other newly integrated work, selects these TWO hunks (not full PR merge), validates same-head source/CI/Place/ZIP, records adoption SHA/ACK and runtime flag.
3. **Human gates**: Studio 2-client TEAM/BR, solo 1+15AI, low-end Android 15 min, #420 ART and fun, OWNER private acceptance **NOT_TESTED / NO_GO** until actual evidence. Never equate CI with runtime play.
4. **Rules**: original-author personal reply is NOT a blocker. Source identity/CI, duplicate authority, stale HEAD, CAS mismatch are RED. Nonfatal YELLOW can be logged with flag OFF & rollback. No main push, unreviewed release merge, Roblox publish, payment, Windows operation.

## Handoff
- Independent claim: **original #525 current-session item pickup fence**; do not start a new competing implementation.
- PR must target `rc/p0d-s1-kids-rc01`, remain separate from #525's original DRAFT and earlier #603 duplicated deposit patch.
- NEXT: same-head CI → #220 latest-CAS selective intake → official same-head Actions/artifact → Studio/Android/FUN. A source candidate is not official adoption.
- Need record official RC script count 31, full HEAD, source-locked SHA, Actions run status, provider artifact ZIP bytes vs actual Place bytes separately, plus last S1 completion 75/100 and human FUN NO_GO until evidence.
