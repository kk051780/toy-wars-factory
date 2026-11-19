# EGGRUMBLE #470 — neutral-horde 30k supply-source candidate (actual private Place)

Status: ISOLATED_SOURCE_PRIVATE_ROJO_PASS / NOT_OFFICIAL_RC / NOT_REAL_STUDIO / ART_FUN_OWNER_NO_GO. This scope owns only quality_gameplay/neutral_pacing/ and its read-only workflow. Original #482 game/7role/neutral/field/castle/egg/item/lobby, #484 composite/AI, #485 ART, #487 SCORE and #220 sole authorized RC writer remain separate.

## Confirmed design gap

#482 original SwarmCombat has SPAWN_BATCH=5, SPAWN_TICK=.18, and live actor cap 110. Ideal supply ceiling 27.78/s = 25,000 in 15min, mathematically less than OWNER's 30,000 REAL neutral KOs target. New pure server-only policy EGGRUMBLE_NeutralSpawnPacing.luau provides nominal 40 spawns/s (36,000 ideal supply per 15min), actor cap 110, batch max 8, overload slowdown to 26/16/s, no deferred debt after cap/idle/finished, epoch fencing and input validation. No second NPC, combat, score, Remote, Castle, Lobby or Store authority.

36,000 is a ZERO-LAG THEORETICAL SUPPLY, not measured gameplay kills or low-Android performance. Real 110-live actor limits, Humanoid AI cost, actual death speeds and client FPS will reduce throughput and must be measured.

## Real private 21-original + 1-pacing isolated Place

Fail-closed source composer tools/compose_private_v3.py checks original #482 AUTHOR_HEAD fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9, original Rojo project Git blob 1d3e5bdc9ac2ac3fb6e70110ff3c6636d70fc714, and original SwarmCombat Git blob fea147ac51411e626b410d172aad5cd72615bd45. It preserves 20 original source bodies BYTE-EXACT, changes ONLY the original Swarm spawn batch scheduling with one source-level splice, and adds the independent planner as the 22nd server ModuleScript. The original Humanoid.Died, KO credit, LOS, bot/HIT source and all other existing 20 sources remain intact. The planner's match ID comes from server-only world name and session start clock. Pressure is measured excess time above the original .18s tick, not the full tick.

Same-head full CI [run #43799384775](https://github.com/kk051780/toy-wars-factory/actions/runs/43799384775) at HEAD ed5e704d8dd733c9ad8751e3c009f5e9e121299c SUCCESS:
- Python composer/original-source drift cases PASS.
- True native Luau compiler 22/22 PASS, native Luau VM 27 assertions PASS, hypothetical zero-lag 15min supply 36,000.
- SHA-pinned Rojo 7.7.1 built UNPUBLISHED .rbxlx, independent actual Place script Class/Source/path validator PASS 22/22.
- Actual isolated Place: 152,910 bytes, SHA256 3d33ff04d2b27aca8242b5df6a2657f6ab64f958fc1e9bb82028a729ff4ca53d. GitHub artifact ZIP: 48,824 bytes (not Place bytes), artifact 14196046773.
- This private Place includes #482's original game 21 plus pacing 1; #484 latest ART+SCORE 26-source combined game is a DIFFERENT candidate. No claim those are merged.

## Authenticated RC integration responsibilities

1. #482 original Swarm author to review and import only the source-exact spawn scheduling splice and module into their **latest** branch. No second enemy controller or loop. If low-end Android FPS requires a lower rate, tune under measured QA and update the objective.
2. #484 existing composite owner to source-selectively include the AUTHOR-APPROVED new module into latest complete game+ART+SCORE composite; preserve all new #482 author features and latest #484 route corrections.
3. #220 only authenticated, nonforce CAS writer to adopt reviewed source into official RC with same-HEAD full CI, source-lock, real Place/ZIP receipt. No main push, ordinary merge, Roblox Publish or paid actions.
4. Actual Roblox Studio TEAM/BR, 1human+15AI / 2human+14AI, 15min real kills/lag, low Android FPS, #420 #470 and OWNER acceptance remain required.
5. Rollback is omission of planner and restoration of EXACT original #482 Swarm source with 5/.18 spawn pacing. No unrelated gameplay changes.

Progress: scoped engineering checks 4/7 PASS (policy; native; source-pinned original V3 splice; real 22-source Rojo). Remaining gates: latest original-author+composite intake; authenticated official RC adoption+same-HEAD receipt; real Studio/Android/ART/FUN/OWNER proof. Official RC adoption 0/1 = 0%. S1 historical 75/100 unchanged. PRODUCT/ART/FUN NO_GO.
