# GQ8 REAL HORDE squad-fan — actual neutral encounters (2026-11-17)

**Scope:** existing singleton `EGGRUMBLE_SwarmCombat` only, selected source/QA overlay. No new Spawn script, Combat, AI owner, Remote, persistent state, damage, credits or UI. Formal RC remains separate; no main/publish/payment.

## Difference from existing work

- #494 controls spawning throughput; **this does not change the existing SpawnPacing policy, requested batch cardinality or server-budgeted live cap**.
- #501 controls humans/bots encounter target distribution; **this keeps the current server-owned per-soldier EncounterFair.chooseIndex choice and epoch** in the existing swarm.
- #528 owns cross-mode server budget; **no added actors**.
- #710 owns spawn physical clearance and arena footprint; this overlay **requires its already-selected collision gate** and leaves it intact.
- #723 already added real-KO-driven coast visual feedback in optional #714; this patch creates **no FX/KO/score**, only changes where the existing real HordeSoldiers are deployed.

In each original spawn batch, the existing server-paced batch of real neutral soldiers uses a shared randomized bearing and a narrow fan of 0.12 radian between adjacent slots (wraps safely after five) at 38–48 studs from their own original target. This produces locally denser enemy formations when a human is the chosen target (especially solo matches), improving the chance that existing server-validated AoE attacks can hit multiple physical soldiers. The new code modifies only a 1-source candidate overlay on the exact official SpawnPacing + EncounterFair selected Swarm; other 30 canonical files remain **byte-identical** and inverse OFF is exact.

**Important:** this is a formation/source implementation, **not a larger 110-enemy cap or proof of actual FUN**. In TEAM/BR multi-target rounds, each original soldier still chooses its own candidate, so a complete 5-person group at one human is not guaranteed. The existing physical spawn guard may reject some placements. A successful source CI alone is not gameplay evidence.

## Integration path

1. Reuse original #721 current31 extraction and verify an exact **successful latest formal V3 31-source artifact**, not an old mock.
2. Reconstruct original31 and select only this Swarm source as new candidate31, prove all other30 exact and inverse Swarm original bytes.
3. Compose existing #714 optional32 on top of the selected fan31, build both 31 and 32 true Rojo with pinned Luau, actual Lua-source class/route checks and native pure fan geometry mutation RED.
4. Source candidate may be merged to #714 feature branch **as tooling only**, never assume the change is active unless its generated new Swarm source is selected into a Studio Place.
5. Authenticated #220 RC writer must rebase on most recent RC, rerun same-head full Native/Rojo31+optional32, source lock, OFF reversibility and required Studio2client/Android15/FUN gates. Nonforce expectedSHA CAS only.

## Status

- Code: new reversible source selector + real current31/selected31/selected32 CI
- Studio physics, actual AOE hit count, 15-minute Android FPS, official RC adoption: **NOT TESTED / NOT ADOPTED**
- Rollback: select the unchanged original 31-source Swarm and omit optional32; no NPC/KO/score persistence changes
