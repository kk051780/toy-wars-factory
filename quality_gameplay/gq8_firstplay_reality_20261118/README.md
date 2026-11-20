# GQ8_FIRSTPLAY_REALITY_20261118 — independent quality lane

CLAIM: first-play release classification ONLY. No Game, Host, Combat,
Castle, Swarm, Item, Lobby, HUD, Store or 10-lane #765 runtime source ownership.
No duplicate of #780 Realm×Regen composition or #581 stale CI receipt gate:
this checks whether successful V3 source tests imply real default gameplay.

Formal RC at branch creation: 261b75d0a7093db5c13db3b95dad9a2911f78689.
During development #220 sole writer adopted original Realm #764 and Regen #775
into official private V3 Core36, readback f77b4d4393d9e9b19b65566413432a7a9f13962b.
The active S1 primary remains rich51. This QA now checks both retained 31
and selected private Core36 manifests and singleton runtime authority.
Original author #482 source pinned to:
fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9.
The original LobbyCastleModesPreview Host has a direct IsStudio-only return.
The current ACTIVE.json selects rich51 for the primary experience, while
EGGRUMBLE_V3_ACTIVE.json registers V3-31 as a companion. Source success and
playability are different. No source profile or engine gate is modified.

## Acceptance and exact proof

- Read immutable original Host from the pinned source commit.
- Read current active and companion manifests; assert single Host/Combat/AI/Swarm.
- Check eight SOURCE-presence flags: character, field, battle, castle,
  neutral, item, lobby, balance. These ARE NOT engine/FUN acceptance.
- Test 12 actual/mutant classifications including false claims of primary
  profile, Studio guard removal, fake PASS metadata, missing source, duplicate
  Host, missing neutral and commented-out guard.
- Success of this QA workflow means correct NO_GO classification. It does
  not establish Studio two-client, low-end Android 15 minutes, 3-minute FUN,
  visual art quality or OWNER_ACCEPTED.

## Checkpoint / no-ACK handoff

FEATURE_ID=GQ8_FIRSTPLAY_REALITY_20261118
P0D_PREP_READY_V1=QA_ONLY_AFTER_SAME_HEAD_GREEN
RC_GAMEPLAY_SOURCE_ADOPTED=NO

Sole authorized B writer: #220. Re-fetch formal 40-char SHA; reuse only
the original nonduplicate gameplay source authors; native/Rojo, exact OFF
rollback and immutable source locks; nonforce expected-SHA CAS/readback;
post-write same-HEAD Actions + exact ZIP/Place bytes.

This QA PR is never a substitute for game source adoption and MUST NOT
be merged as a gameplay feature. No original author ACK wait is necessary
but writer authorization and RED fail-close are mandatory. Do not edit
main, release a Roblox experience, merge other PRs or incur paid usage.

Rollback: drop this isolated QA branch/PR. All original V3 sources,
formal RC flags, Host/Combat/Remote/Store and game scripts remain intact.
