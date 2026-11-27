# P0D / EGGRUMBLE — eight-lane RC intake gate (2026-11-16)

## Owner progress convention

Never call isolated prototypes integrated or playable in the official RC merely because their source files exist. Report **SOURCE / CI / STUDIO / ANDROID / OFFICIAL_RC / OWNER_ACCEPT** separately. The numerator of RC progress is only the number of independently verified lanes accepted in the official RC by #220, out of eight; source preparation is a separate leading indicator. This document is a **handoff checklist**, not authority to merge.

| Lane | Independent source | Source tests | Studio gameplay | Android | Official RC | OWNER |
|---|---|---|---|---|---|---|
| CHARACTER | SevenRoleVisualKit | authored | not verified | not verified | not verified | pending |
| FIELD | ValleyLandmarkKit | authored | not verified | not verified | not verified | pending |
| BATTLE | MusouComboPreview | authored | not verified | not verified | not verified | pending |
| CASTLE | EnterableCastleInterior | authored | not verified | not verified | not verified | pending |
| NEUTRAL | NeutralStoneGiant | authored | not verified | not verified | not verified | pending |
| ITEM | FieldItemPickups | authored | not verified | not verified | not verified | pending |
| LOBBY | LobbyUXPreview | authored | not verified | not verified | not verified | pending |
| BALANCE | BalanceMetrics | authored | not verified | not verified | not verified | pending |

**Verified RC integration: 0/8 (0%) from evidence in this isolated branch.** This does **not** assert the official RC lacks any of these functions from other writers. It means this handoff has no verified #220 RC acceptance record for these eight independent slices. Source coverage 8/8 (100% presence) does not equal game completion.

## #220 intake acceptance

1. Freeze exact candidate SHA and inspect the authoritative #220 CLAIM map before modifying the official RC; reuse existing owners' implementation and avoid duplicate source files.
2. Run native Luau syntax and source contract tests against the frozen SHA. Record test command, run ID and conclusion; CI failure is not a PASS.
3. For each slice, integrate into a *single* game loop instead of running all standalone preview scripts at once; strip Studio-only assertions only through authenticated RC implementation and review.
4. Validate physical 3D interactions: player enters castle through gate, steals eggs inside, deposits at own vault, castle takes siege damage; AI must obey same geometry; neutral boss warns and damages; items consume once; seven distinct weapon rigs and skill effects; lobby portals start actual TEAM/BR.
5. Studio acceptance: full TEAM and BR matches, egg conservation, elimination/winner, LOS, no invisible blockers, mobile camera, no permanent large HUD.
6. Android acceptance: input, frame-time/memory on target phone, FX readability, control hit targets and collision; #420 art gate comparisons.
7. Only authenticated #220 can mark an integrated lane and advance its RC numerator. No main merge, publishing, charges or fake test claims.

## Evidence commands

`python3 -B handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/tests/p0d_rc_intake_readiness.py`

`python3 -B -m unittest discover -s handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/tests -p 'test_*contract.py' -v`

A future #220 acceptance log should store each lane's RC commit, test run URL, Studio evidence, Android evidence, rollback flag, and OWNER sign-off. Without those, keep its status unverified.
