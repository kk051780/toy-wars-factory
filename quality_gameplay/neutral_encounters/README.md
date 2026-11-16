# EGGRUMBLE V3 — Neutral encounter fairness (isolated source candidate)

**State: SOURCE_WIP; official RC adoption 0; Studio/Android/OWNER not tested.** Scope claim: [#218 comment 6906559751](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6906559751). This is deliberately distinct from #494 neutral *throughput*, #482 original horde behaviour, #484 AI/composer, #485 ART, #487 SCORE, and #220 protected official integration.

## Actual issue (from #482 source, not a guess)
`EGGRUMBLE_SwarmCombat.luau` creates spawn candidates from alive human avatars **plus** the 16-seat bot roster, then uses `math.random(1,#candidates)`. With one human plus fifteen bot actors, expected spawn-centre sampling near the human is **1/16=6.25%**, even though solo players need frequent real neutral encounters and combo opportunities. Actual observed encounters still depend on NPC movement/terrain and **have not been measured**.

## Real Luau fix

`EGGRUMBLE_NeutralEncounterFairness.luau` is a **pure server policy**. One server-owned per-session state and the existing 1-to-1 candidate-index list yield a deterministic human share of **at least 40%** when bots are present, retain the natural human proportion above 40%, rotate across humans and bots within each group, and reject bot-only rounds. Epoch change resets the quota. The original author's neutral soldier, KO, move, hit, line-of-sight, MAX=110 and actual randomized offset/radius remain unchanged. This policy alone NEVER spawns, attacks, rewards or increases throughput.

### Original author's only integration hook (not applied to #482)

This needs the **#482 original source owner** to add a sibling ModuleScript into the V3 project and in **`EGGRUMBLE_SwarmCombat`**:
1. Require `EGGRUMBLE_NeutralEncounterFairness` and create one `spawnFairState={}` inside `Swarm.start(session)`.
2. Extend the existing `aliveTargets()` to return a **second aligned array** `kinds` alongside its current `Vector3` positions. Append `"HUMAN"` only for an actually live humanoid (Health>0 and valid root), and `"BOT"` only for a live owned bot with valid root. Preserve old first return for the movement/AI loop.
3. Only in the EXISTING spawn loop replace `local target=candidates[math.random(1,#candidates)]` by `local idx=Fair.chooseIndex(spawnFairState, session, kinds)` and `local target=idx and candidates[idx]`; skip this spawn attempt if nil. Keep existing random angle, radius, `soldier`, `LIMIT`, `SPAWN_BATCH`, `SPAWN_TICK`, and KO code.
4. On end/cleanup call `Fair.clear(spawnFairState)`; use a fresh state per round. Never expose client control of the list, epoch or share.

**Safety:** This is a source-only optional policy and must not be inferred to be in live V3 or official RC. Switch OFF/rollback = omit helper mapping and retain original uniform random selection; no persistence/schema/economy impact. The choice policy does not solve total KO supply cap (#494). After author hook, run the original 8-domain tests + exact Rojo/native tests, then authenticated #220 CAS/same-HEAD official RC and actual Studio one-human+AI / TEAM+BR 15-minute Android performance + #420 and owner FUN gates.

## Self QA
`python3 -m unittest discover -s quality_gameplay/neutral_encounters/tests -p 'test_*.py' -v`

Dedicated GitHub Actions additionally compiles **the exact Luau source** and executes native VM assertions: solo 40/100, 8+8=50/100, all-human, bot rotation, no human, malformed input, epoch reset. This is a proposed behaviour quota, **not a proven fun/real-spawn outcome**.

## Balanced 8-domain interface
- Characters: one-human solo and all-human sessions both included.
- Field: only spawn location distribution changes; existing 3 routes remain.
- Battle: actual attacks/HIT, combo and KO untouched.
- Castle: siege/egg authority unchanged.
- Neutral units: the sole modified behaviour is which **existing** live target a new neutral spawns near.
- Items: pickup/respawn and egg-carrier constraints untouched.
- Lobby: mode and explicit readiness unchanged; bot-only no-spawn protection.
- Balance: >=40% human share under bot-heavy conditions; source exact tests, device balance pending.

**Formal gate:** claim only SOFT, code prepared => source-native CI => original author wiring => full source-exact Place => #220 authenticated RC integration => Studio+Android+OWNER acceptance. No main write, PR merge, publish or costs.
