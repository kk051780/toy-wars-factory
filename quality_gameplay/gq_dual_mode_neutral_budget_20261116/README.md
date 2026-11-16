# GQ-528: simultaneous TEAM/BR live neutral-model capacity (source-only)

## Distinct scope

The original #482 V3 host starts two independent TEAM and BATTLE_ROYALE matches in one Studio server. Each original `EGGRUMBLE_SwarmCombat.luau` has local `LIMIT=110`. Thus combined live models may reach **220**, without a proven shared ceiling. 220 is a source-derived *upper bound*, NOT observed runtime population or Android FPS. The original #494 neutral spawn pacing, #501 human/bot target fairness, #505 skill FX quota, #527 bot siege damage, #500 castle defense, #489/#517/#525 items and #482 Game/Host are **not edited** here.

This isolated pure Luau ledger implements one shared atomic ticket for each *live neutral Model*:
- Separate TEAM / BATTLE_ROYALE session generations and idempotent release after Died or teardown
- Configurable global cap, per-mode cap, and reserve for another active mode
- No global Remote, score, DataStore, fake KO, AI hit, spawn loop, visuals, or client trust
- No duplicate authoritative Swarm or Game; privately wired to original Host/Swarm in ON22 only, NOT a Studio-playtested or officially adopted game

**Provisional test-only policy:** global 128, per-mode 96, opposite reserve 32. These numbers are *not* measured/approved for performance, gameplay, or 30k KO; calibrate against #494 pacing and low-end Android 15-minute tests. Never silently enable in live games.

## Source workflow and authority

Fixed original author #482 HEAD: `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`.
Original git blobs held byte-identical: Swarm `fea147ac51411e626b410d172aad5cd72615bd45`, Host `7162b209bf67b74a71553217f3f744e072a0365d`, Combat `66e666418b7c23d41f87faa5d61eb6e2770a463e`.

GitHub workflow compiles the pure Luau on pinned f46d879e Luau CLI and executes **actual native VM** cases for TEAM96+BR32, double release, stale callback, stale epoch, restart, and invalid caps. Python tests only enforce source boundaries. Native assertions do not prove in-engine spawn behavior. The new source-locked staging builds **two real unpublished Rojo Place files**, the exact original 21-script OFF and the optional integrated 22-script ON. Verified first source-exact run [Actions #43831676648](https://github.com/kk051780/toy-wars-factory/actions/runs/43831676648) (13 Python tests; Native Luau VM + Luau compile 21/21 OFF, 22/22 ON; Rojo original21/21 and integrated22/22 Source/Class PASS). Original OFF Place **149,589 bytes** SHA256 `351322501a8e98dafd9f1955c1a679dadf718d81a51d8311d8c3458cdd70bc95`; private ON Place **154,567 bytes** SHA256 `cca63394e669bbaa829667fcc4f0edca4b350d4d61c84ea91a91c8e276c44995`. Those are PRIVATE Place bytes, NOT official RC.

The PRIVATE ON22 source-selective hook is now implemented by `tools/compose_private_v3.py` (OFF21 keeps all author bytes intact); it remains strictly a candidate until #218 real `CLAIM_GRANTED` and #482/#494/#501 ACK:
1. Instantiate exactly **one shared** budget in the original two-mode Host. Call `begin(mode)` once per session.
2. Before original neutral `addEnemy`, call `acquire(mode,epoch)`; no ticket = no spawn. Attach the returned ticket to that neutral model in the server-only closure.
3. On original `Humanoid.Died`, cleanup, and destroy, call `release(ticket)` at most once; the policy safely rejects duplicates.
4. At match end, `retire(mode,epoch)` atomically frees that session without touching the opposite mode. The original #494 spawn pacing remains the only spawn timing/KO source.

**Rollback:** use the generated OFF21 project (all 21 original author files byte-exact), rather than merging the proposed ON22 Host/Swarm overlays. Production acceptance must provide a real default-OFF flag and a two-way tested rollback before RC adoption.

## 8-domain compatibility and outstanding gates

| Domain | Existing authority retained | To confirm after live integration |
|---|---|---|
| Character | 7Role / BotActors | no actor desync when spawn denied |
| Field | Host TEAM+BR separate arena | no opposite-mode neutral leak |
| Battle | server-owned HP/HIT | no dropped hit events/double KO |
| Castle/egg | CastleMatchRules | neither outcome nor egg ledger changes |
| Neutral | original Swarm, #494, #501 | global live <= budget; real KO throughput |
| Item | #489/#517/#525 | no effect on pickups |
| Lobby | original queue and session epoch | no stale release after replay |
| Balance | per-mode fairness/author skill | 15-min survival/30k KO targets/Android |

PRIVATE_SOURCE_EXACT_READY only; no `P0D_PREP_READY_V1`, source-intake/Studio/Android/FUN/OWNER acceptance unknown, official RC adoption **0**. The private Host+Swarm integration is an actual Luau script composition but its running Roblox game behavior is not yet measured. #220 remains the sole authenticated RC writer; branch `rc/p0d-s1-kids-rc01` observed unprotected, so no unsafe direct write. Main, merge, Publish, billing, PC access forbidden.

Request record: #218 comment 6910676980. Integrator #220 needs real author ACK, protected coordination/auth/CAS, same-HEAD native+Rojo+real Place and ZIP size, flag rollback, Studio and Android evidence.
