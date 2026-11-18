# GQ800 LAND MUSOU × FRIENDLY NEUTRAL CONVERSION (P0 SOURCE PREP)
Feature: **GQ800_LAND_MUSOU_FINISH_AND_NEUTRAL_CHARM_20261118**
Owner issue: https://github.com/kk051780/toy-wars-factory/issues/800

Scope is DISTINCT from #582 Zombie Commander: that feature spawns 3 new temporary Humanoid servants. THIS policy converts **existing, server-owned, identifiable NeutralHorde models**, retains their personality/species and joins orders. Neither policy in this directory is wired into live combat yet. Preserve #582's original code, existing #508 neutral KO, #374 appearance, #381 hit slashes, #388/#390 neutral motion, #765 attribute VFX and #220's only official writer. Never create separate Game/Combat/Swarm/Remote/HP/Score/Store authority.

## Integration contract (not fulfilled by policy alone)
1. Existing single server Swarm assigns unique stable instance IDs and species to each real neutral model; not names. Retain existing native neutral HP/KO owner, LOS, encounter pacing, boss immunities.
2. When trusted Combat ZOMBIE's real hit is accepted, BEFORE lethal neutral death, call CurseConversionPolicy.seal with server-signed fields and *real current HP*; only the existing Swarm may set friendly team, skip hostile target list/KO, apply visible sigil and reuse existing AI/Hit callback. Never treat this candidate permit as a network authorization.
3. Call CurseConversionPolicy.step from the original Swarm tick, applying RELEASE and existing #582 command policy; no new heartbeat. Session/avatar/death/owner castle cleanup mandatory. Combined max 4 companion budget includes existing summoned units.
4. On each original server confirmed hit/KO event, call NeutralFinisherPolicy.select on client-only derived read-only receipt; 7 role choices × 8 species. Only true KO may hide/disappear. Reuse authored original #374 silhouette/#381 hits/#388 motion; do not duplicate art spawners. Max 12 concurrent hit reactions (LOW Android 5), cap particles, distance LOD, color-independent shape glyphs.
5. Validate real source with native Luau, same HEAD Rojo of current original31/Core36, inherited source locks, exact OFF rollback, authorized #220 nonforce expectedSHA CAS, then real Studio 2-client+low Android15min and FUN. Do not claim public playability before these are confirmed.

### Current stage
- New pure Luau decision policies and native tests: committed source candidate; native workflow will report GREEN/RED.
- Runtime wiring to existing Combat/Swarm: NOT YET DONE
- Official RC adoption: **NO**
- Engine FUN/Android: **NOT TESTED**
- main/publish/paid: unchanged, forbidden.
