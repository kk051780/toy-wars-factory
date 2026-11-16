# EGGRUMBLE V3 — TEAM/BRフィールドアイテム所属ゲート（独立候補）

**State:** SOURCE_WIP / CLAIM_SOFT_NOT_GRANTED / OFFICIAL_RC_ADOPTION=0 /
STUDIO_ANDROID_FUN_OWNER=NOT_TESTED. This is not a playable/approved RC.

## Evidence-backed gap
Original #489 EGGRUMBLE_FieldItemPickups.luau validates alive castle,
session ACTIVE, server proximity/LOS, egg-carry restrictions, cooldown and
single-use claim. It does **not** verify that the player is still a member
of **this live session**. Original #482 lobby can hand a disconnected user's
castle to an AI while retaining that user's original castle ID. On rejoin
or mode switch, a stale roster membership must never authorize picking a
TEAM item while the actor is currently in BR (or vice versa).

## Exact non-overlapping implementation
- Reuse the original #482 lobby Game, the original #489 ITEM effect code,
  #517's separate HEAL fairness proposal and #484 composition. Do not copy
  or own any of them.
- patch_sources.py is a **two-file exact-source overlay generator**, not
  another server Game, ITEM implementation, inventory or Remote.
- In the existing lobby session, create a **server-only predicate** requiring
  the same live sessions[mode], current joined[userId], living Player
  object and ACTIVE round.
- In existing Items.canUse, require that predicate for TEAM/BR only;
  missing/failing callback **fails closed**. Original standalone
  field-item preview without TEAM/BR remains unchanged.
- All source owners' other code paths remain byte-equivalent. It adds
  one bounded check at item claim, not a scheduler/network event.

## Pinned author inputs
- #482 author head fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9,
  lobby Git blob 7162b209bf67b74a71553217f3f744e072a0365d.
- #489 author head 03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd,
  ITEM Git blob 107046cb0bf81fed9e3cba1699ada31571e44a22.
- #517 HEAL overlay must be source-selected **after** original-author ACK;
  re-pin the exact resulting ITEM blob and rerun all checks. Do not
  overwrite #517 or silently claim combined QA.
- Official RC last observed head
  d2f3ed1a47558fdaf07be0181c83c698bdb2ce34.
  **Always re-read latest #220 head and claim before adoption.**

The isolated workflow checks Git blob locks, negative test cases, exact
two-site minimal deltas and Luau native **compile**. This is not proof of
Roblox engine execution or Play testing.

## Integration/rollback path
1. #218 explicitly grants a unique CLAIM (SOFT currently only); #482 Game
   and #489 ITEM authors ACK, #517 author reconciles HEAL variant.
2. Source-select these **two changes** in #484's one-game composition;
   native behavior VM, cross-author source lock, Rojo class/source-exact,
   negative two-session/leave/rejoin/round-stop tests; nonfatal YELLOW
   requires flag OFF and rollback, authority/lock RED blocks.
3. Only #220 authenticated non-force CAS writer applies the 2-hunk
   source change to the latest official RC, publishes same-HEAD CI,
   measured real Place/ZIP bytes, SHA ledger and adoption ACK.
4. Studio human+15AI TEAM/BR, 2-client, Android 15m, #420 visual/FUN,
   and OWNER re-test are separate **required** acceptance gates.

**Rollback:** omit both source-selected hunks and restore the two
exact original author blobs. Never merge this stacked branch wholesale.
No main or other author's branch writes, Roblox Publish, paid operations,
forced CAS or Windows/Studio control.
