# GQ V3 — Castle/egg world-board distance fix (source-only)

**FEATURE_ID:** GQ_V3_CASTLE_BOARD_DISTANCE_CULL_20261116
**Existing #218 claim:** https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6911409880
**Area:** EGGRUMBLE V3 / eight-area quality gate #470
**Original author:** PR #482; original Luau files NOT modified
**Pinned author HEAD:** fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9
**Pinned original Host blob:** 7162b209bf67b74a71553217f3f744e072a0365d
**Separate official RC HEAD:** d2f3ed1a47558fdaf07be0181c83c698bdb2ce34 (unchanged)

## Real source evidence (not Studio visual proof)
The V3 Host's original board function sets BillboardGui.AlwaysOnTop=true, Size=230x82 with no MaxDistance. It is called for each core and EggVault. Two 16-seat matches may therefore have up to 64 labels in the source model. Actual on-screen overlap has NOT been measured. FB-001/015 reports world label clutter. Existing #485 ART LOD hides only original noninteractive ART decoration, not the authoritative health/egg boards. This is continuation of the existing #218 claim, not a duplicate feature.

## Minimal generated Host-only delta
- Existing castle core BillboardGui: AlwaysOnTop=false, MaxDistance=65, Size=160x48.
- Existing EggVault BillboardGui: AlwaysOnTop=false, MaxDistance=40, Size=115x36.
- Reuses the two existing GUI instances; no new UI/HUD, Game, Remote, Store or duplicated actor authority.
- Original board factory, session.refresh HP and egg values, 7 roles, siege/egg Rules, 3 field routes, bot/neutral/boss state, items and TEAM/BR lobby are intact.
- Fail-closed original Git blob lock and one exact source anchor per UI.
- Reversible OFF = original author's exact unchanged 21-source V3 project (no migration).

Local source QA / composer commands:

    python3 -m unittest discover -v -s quality_gameplay/v3_castle_board_distance_20261116/tests
    python3 quality_gameplay/v3_castle_board_distance_20261116/tools/compose.py --out quality_gameplay/v3_castle_board_distance_20261116/_private_stage

Dedicated GitHub Actions runs Python source/negative regressions, native Luau syntax for all original and changed sources, Rojo 7.7.0 true private .rbxlx build and XML-verification of 21 original/selected script classes/source texts. This CI is NOT engine play or formal RC.

## Eight-domain impact (no author duplication)

| Area | Change | Preserved |
|---|---|---|
| Character | None | Seven roles/weapons |
| Field | Less distant board occlusion | Three original paths |
| Battle | Better long-range sight lines | Damage and cooldowns |
| Castle | Two GUI properties after original calls | HP, eggs, gate/siege physics |
| Neutral | None | Soldiers, AI, boss |
| Item | None | HEAL/DASH/SHIELD and egg pickup |
| Lobby | None | TEAM/BR, role selection |
| Balance | None | KO/score/economy |

## Acceptance & ownerless handoff
Current stage until verified: SOURCE_WIP; #218 CLAIM_SOFT_NOT_GRANTED; P0D_PREP_READY_V1=NO; OFFICIAL_RC_ADOPTED=0; STUDIO/ANDROID/FUN/ART/OWNER=NO_GO.

Stacked branch is based on pinned #482, not official RC. The #220 sole authenticated nonforce-CAS writer must source-select this one Host delta into the latest author composite (#484/#531/#537) **without overwriting** their castle ramp, membership checks, egg refresh or other original work, then run same-head official CI and record ZIP/Place bytes and ACK. Studio near/far view, inside castle, reachable Prompt, 16+16 game load, Android visuals/performance and OWNER acceptance still require real evidence.

Source preparation can continue without stopping for original author approval. Do not bypass authentic writer permissions, exclusive CLAIM, source lock, nonforce CAS or any safety gate. No main edits, PR merge, Publish, paid actions or Windows operation.
