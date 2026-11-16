# EGGRUMBLE V3 — central-ridge pass-through quality patch (private candidate)

**Unique owner scope:** `EGGRUMBLE_V3_CENTRAL_RIDGE_ITEM_CLEARANCE_20261116` (SOFT_CLAIM_NOT_GRANTED on #218). **No official RC write or author-source edit.** This is **actual one-block Luau replacement generator**, not a report-only feature and not an ITEM duplicate.

## Source-derived gameplay defect
- Immutable original author: [PR #482](https://github.com/kk051780/toy-wars-factory/pull/482), host source commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, host Git blob `7162b209bf67b74a71553217f3f744e072a0365d`.
- In `EGGRUMBLE_LobbyCastleModesPreview.server.luau`, TEAM `CentralRidge` is a single **collidable** box, center `(-620,+15,475)` vs shared root, size `54×34×190`. Its X bounds are `[-647,-593]`, Z bounds `[380,570]`, Y bounds `[-2,+32]`.
- Original `RaidItemIntake` fixed Latin-square item site `{x=0,z=470,kind="SHIELD"}` resolves to `(-620,+1.8,470)` for TEAM, fully **inside** the solid ridge. Original `FieldItemPickups` places a radius 1.1 pickup there with `ProximityPrompt.RequiresLineOfSight=true`. It cannot be approached normally through the solid center of the contested corridor. This is a geometry inference; Studio physics has **not** been observed.
- The same ridge obstructs the tactical center route (route 2, Z≈465); AI, battle pathing and one third of the item choices are affected together.

## One-source fix and exact rollback
`patch_ridge.py` refuses source drift by checking the actual Git blob, original ridge anchor and author ITEM coordinates. It emits a generated **PRIVATE host only**:
- Replace one 54-wide solid rock with **two 15-wide collidable rock shoulders**, same height and Z span, leaving a **24-stud noncolliding central passage**. Original outer bounds, visual material, neutral controllers, arena world authority, original mode, lobby portals, and 9 ITEM placements remain the same.
- The existing `CentralRidge` name is retained for the left shoulder to preserve old source contracts; right shoulder named `CentralRidgeRight`.
- SHIELD radius leaves **10.9 studs clearance** from each shoulder. Human and AI may traverse the center route and reach the pickup; actual pathfinding/LOS must be verified in Studio.
- Exactly one original host block is changed **only in generated copy**, with byte-preserved remainder. No `Game/Remote/Store/Score` or second ITEM/ART/AI script.
- **Rollback:** drop the generated preview host and use the exact original `#482` host Git blob `7162b...`; in a candidate Place, disable/remove only this geometry overlay before #220 reassessment.

## Verification and handoff
Run `python3 -m unittest discover -s quality_gameplay/v3_central_ridge_clearance_20261116 -p test_patch_ridge.py -v`, then `python3 quality_gameplay/v3_central_ridge_clearance_20261116/patch_ridge.py --output /tmp/EGGRUMBLE_LobbyCastleModesPreview.private.server.luau`.

**Source-level pass is not engine certification.** Stage progression: SOURCE_WIP → source-contract PASS → original #482 host owner ACK and #218 CLAIM_GRANTED → pinned native Luau/Rojo private Place same HEAD → #220 authenticated CAS official RC + same-HEAD CI + exact Place/ZIP capacity and rollback receipt → 1-human/AI + 2-human TEAM/BR Studio traversability and pickup/LOS → Android15min/#420 ART-FUN → OWNER_ACCEPTED. **No main push, merge, Publish, Windows interaction, extra spend, or paid services.**

**Do not duplicate other work:** #482 owns world/game; #484 AI/ramp; #485 ART; #489 ITEM; #517 HEAL consumption. This slice only changes the *collision topology of the TEAM ridge* and must be applied by its original owner/sole integrator.
