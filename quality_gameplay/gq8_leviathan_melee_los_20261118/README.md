# GQ8 neutral Leviathan melee: server wall-occlusion

- Claim: issue #470 comment 6976810448; unique source-owner slice.
- Original author: PR #764 at immutable HEAD c51de1ed4feb7a7500ada95d21282402053ef988.
- Exact original server Git blob: 1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1.
- Formal source profile: V3 eggrumble_v3_core36 (36 scripts; Realm server already present). Original 31 baseline and S1 rich51 are not touched.
- Defect from actual source: Leviathan melee applies 6 HP every 2 seconds within 13 studs without a wall-occlusion check.
- Exact fix: source-locked replacement of one neutral melee branch. Workspace:Raycast blocks collision-enabled reefs/geometry; noncolliding ocean visuals do not block. Preserves 3 creatures, target selection, 6 damage and 2-sec cadence. No new Game/Combat/Host/Swarm/Remote/Store or extra script.
- Tests: corrupt author blob -> RED, inverse corruption -> RED, duplicate anchor -> RED, Luau native syntax in CI. These do not prove Studio/mobile actual play.

## Integrator handoff

Only authenticated #220 B writer may integrate to formal rc/p0d-s1-kids-rc01. Fetch latest HEAD and exact source lock, apply patch to original #764 EGGRUMBLE_RealmBattleCore.server.luau BEFORE passing it into existing #780 Core36 composer; do not add a 37th script. Run same-HEAD Core36 Native36/Rojo36 Source+Class, source-lock and original OFF31 byte-exact verification; nonforce expected-SHA CAS and post-CAS CI readback. Do not await original author ACK. RED on conflicting overlapping code or identity drift.

Rollback to exact #764 original server or private V3 OFF31. Do not change main/rich51/Publish/Store/Score/paid features. Studio 2client, Android 15min, ART and FUN remain NO_GO.

Eight domains: character/field/battle/neutral improve underwater cover fairness; castle/item/lobby unchanged; balance preserves original 6HP/2s and 3 creatures, refusing only invalid through-cover hits.
