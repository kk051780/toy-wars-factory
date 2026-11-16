# EGGRUMBLE V3: bounded neutral soldier melee against live heroes (GQ-V3-NEUTRAL-MELEE-20261116)

## Evidence-based design gap
Original #482 (commit fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9, Swarm blob fea147ac51411e626b410d172aad5cd72615bd45) contains real neutral Humanoid, movement/LOS to player attacks, death and KO attribution. However the regular HordeSoldier movement task never calls TakeDamage on a human/bot Humanoid. The stone giant shockwave is a separate boss and does not fix regular soldiers. Without counterattack, the sword-clash melee pressure/HP risk intended by #470/#219 is absent.

## Minimal actual source, not a second combat authority
- One new **pure Luau decision module** EGGRUMBLE_NeutralMeleePolicy.luau; attack power 4 HP, range 4.25 studs, one soldier swing per 1.4s, one successful melee hit per victim per 0.8s, maximum 24 attack rays in a 0.38s horde movement tick. Values are first-trial candidates, NOT Studio-balanced or Android-certified.
- compose_melee_candidate.py pins exactly the original author's Git blob, then generates ONE patch of the existing SwarmCombat (same original movement task and live mob table). It does not modify #482 original path/branch. Both real humans and existing bot actors are eligible only when their personal castle is alive and match ACTIVE. Server raycast with RespectCanCollide protects castle walls. Humanoid.TakeDamage respects shields. No new Game, Remote, leaderstats, KO credit, eggs, store or spawner.
- Restore original Swarm blob and omit the pure module for full OFF rollback. This private candidate does **not** include #494 neutral supply pacing or #501 fair target selection yet; source-selective reconciliation with those original owners is mandatory before formal RC.

## Gates
1. This is a **SOFT claim**, NOT CLAIM_GRANTED: #218 issue comment 6912080156. Exclusive new paths only: quality_gameplay/neutral_melee_pressure_20261116 and one CI.
2. Negative source-drift tests must pass, native Luau tests must execute, and private Rojo must embed EXACTLY 22 genuine source scripts without a second Swarm/Game.
3. Original owners #482/#494/#501 and #484 composer must approve this one Swarm overlay, ensuring neutral target fairness and player damage are combined in one code path; #220 alone can write official RC via nonforce CAS, source-lock, same-HEAD official CI/real Place.
4. Studio one-human/15-AI TEAM and BR, two-client, real castle LOS, force fields, 15-min Android performance, PC art #420, first-three-min FUN, OWNER acceptance remain **NOT_TESTED/NO_GO**. This README does not claim formal RC adoption.

No main, merge, Roblox publish, payment, PC automation, or unauthorized official-RC writes.
