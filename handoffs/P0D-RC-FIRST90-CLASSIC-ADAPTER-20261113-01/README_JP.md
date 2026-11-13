# P0D S1 FIRST90 Classic waypoint — source-only RC admission prototype

**P0D-FUN-H1-001 | Integrator #220 | 2026-11-13 JST**

Status: **SOURCE_ONLY_PREVIEW / NOT_MOUNTED / OFFICIAL_RC_ADOPTION_BLOCKED**.

This isolated branch starts from the immutable official RC commit
`1263a03701211a652b99b91d2339575dc8104eff`. It does **not**
modify official `rc/p0d-s1-kids-rc01`, `main`, another feature owner's branch,
or any existing original `releases/P0D_S1_KIDS_RC01/**` file.

## Real playable delta sought (once formally adopted)
The existing official S1 already has **one original Game + one Remote**
and a **client-only first-60-second Coach**. B42 has a separate First90
guide and a server-provided waypoint. Naïve B42 Game/HUD full replacement
would replace a distinct 703-line original authority with a 2115-line
experimental authority, duplicating/overwriting Guardian trap, mode, save,
XP and score assumptions.

This file provides one **pure server-only Classic-mode target selector**:
- at 0–89s, living authenticated RED/BLUE: pick the true original opponent
  egg **only when original Prompt enabled, visible and server ownership free**;
- while carrying, point home to original actual scorePad **only when own
  egg is present**;
- if own egg is missing, emit **RECOVER without revealing hidden carrier position**;
- reject no target, stale phase, >=90s, broken coordinates and unknown state;
- no map movement, no new Game, Remote, client trusted coordinates, timers,
  damage, score, inventory, DataStore or purchase.

## Formal adaptation still required by sole #220 writer
After private Studio trials + explicit #250 `product_official_rc_selected=YES`:
1. **Server**: mount the pure module under original `ServerScriptService/TrapRaidersS1`, add exact server-derived argument construction inside the original `snapshotFor(player)`, using true `match.phase`, `match.serial`, `match.startedAt`, `getTeamName`, `healthy`, `carry`, `match.eggOwners`, `map.teams`. Never trust a target from Remote client input. Keep one Game.
2. **Client**: extend **existing Coach** to consume optional `first90Target`; do not mount a second B42 HUD/Coach. B42 Waypoint visual implementation is a **separate upstream owner's source** needing explicit hunk and Android/HUD QA; this module alone is not a visible arrow.
3. **Proof**: native Luau compiler/executable positive-negative tests; exact 21+source Rojo unpublished Place build and independent actual-RC QA, then owner 2-client/Android Studio and first90 FUN. Recompute source lock/manifest on actual RC commit. This branch's Python tests are *source/static + reference-model* only, NOT native Luau/Studio.
4. **Rollback**: official original `1263a03701211a652b99b91d2339575dc8104eff`.

## Test and source evidence
Run from repository root: `python -m unittest discover -s handoffs/P0D-RC-FIRST90-CLASSIC-ADAPTER-20261113-01/tests -p 'test_*.py' -v`.

Original frozen public source blobs checked: Game
`7c5229f600f17537bc1bbbb0b96b6a2435875374`,
Coach `63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9`,
FirstMinuteModel `fcdc399bf95b6cd0532691718f5a54e8a4fd84b4`.

B42 source `837853e66278e38bb79f6399c3e8bfc9a2403be6`,
comparison A40 V6 `4b09de3eb70abb2e79268ce41bdecc4b614d39df`.
A separate isolated B42+V6 source candidate already exists (not official RC)
at `63442fb415d361855d72f5a15171f7cdd4a2486f`;
**do not duplicate/replace its full Game**.

Source only, not formal product select, real Studio, human FUN, official S1
score improvement, release permission or Codex/PC command.
