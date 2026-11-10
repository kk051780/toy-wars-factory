# P0-D S1: castle-rush vs egg-steal balance quantitative gate

- **Packet:** `P0D-S1-CASTLE-EGG-FIRST-LAUNCH-BALANCE-20261111-01`; `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`.
- **Provenance:** exact Chat S1 initial integrated source `35d7d0525388e885aac8281eff2315a59831e0cf`, NOT the unknown latest OWNER Windows Place. `data/source_contract.json` pins actual original `Config.luau`, `MapBuilder.luau`, and `Game.server.luau` Git blob SHAs. This feature owns no match/damage/event authority.
- **Finding:** Under highly simplified no-defender straight-line **optimistic lower bounds** (not an achievable player result), original Raider castle-rush requires ~26.11 s versus 2 egg captures ~34.89 s. Castle lower bound is only ~75% of egg lower bound. This is a **balance-risk hypothesis**, NOT proof of competitive dominance in Studio.
- **Candidate:** pure review-only `src/S1LaunchBalanceProfile.luau` sets `CastleMaxHp=420` (was 300), `CastleAttackDamage.RAIDER=12` (was 14), GUARDIAN remains 10. No other values change. Model estimated lower bounds: Raider castle ~37.16 s versus egg ~34.89 s; GUARDIAN castle ~45.32 s versus egg ~43.82 s. Restoring parity is a design hypothesis; final balance requires human and 2-client testing.
- **Expected behavior:** preserve both methods of winning; stealing an egg still requires enemy→own pad twice, server remains authoritative, 2-player start, 6-minute round, 2 capture win. No paid advantage or purchase added.

## Run the actual tests

```bash
python -m unittest discover -s tests -v
python tools/balance_model.py --contract data/source_contract.json
```

Only Python scenario/oracle tests are executed here; native Luau parse, Roblox game test, subjective fun, retention and live match statistics are **NOT_TESTED**. The lower-bound formulas ignore enemy defense, map obstacles, ping, client action tapping, vertical height, camera, D07 boss and late join. The path stages independently subtract interaction-radius disks, so the egg lower bound may not be physically attainable over the whole route.

See `docs/INTEGRATION.md` before optional integration. This is plaintext public source and no AES key. No edits to `main`, the sole #220 integrator branch, Roblox public Place, price or paid inventory.
