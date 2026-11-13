# EGG RAID RUMBLE — FREE HATCH → OWNED → EQUIP → SCOUT permission V1

Date: 2026-11-13 JST. UNIQUE owner lane: `CHAT-EGG-RUMBLE-REWARD-EQUIP-SCOUT-PURE-LUAU-20261113-01`. Product requirement: [Issue #275](https://github.com/kk051780/toy-wars-factory/issues/275). Internal `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`.

## What is actually delivered
`src/RewardEquipRules.luau` is an ORIGINAL, self-contained server-compatible pure Lua/Luau policy module (no Remote, no Roblox engine access). Guarantees free starter `starter_scout`, FREE one hatch per server-certified match epoch for each participating user, owner/collection/receipt records, a single class-validated tactical equip item, and server-only time/round validated **SCOUT permission token** with fixed five-second duration and 18-second cooldown. Common and rare variants have exactly the same battle effect. The illusion of rare strength is not sold; rarity is only a skin.

The server must call `finishRound` with authenticated final scores and a verified contested-rare-carrier roster; the module **never reads egg possession from clients**. The canonical server generates the RNG, not the client. Basic rare 50/10000 (0.5%) and special 500/10000 (5%) are only experiment variables; they are NOT yet approved public odds. 10,000 integer roll outcomes per tier and no paid rerolls. `claimFreeHatch` is idempotent for each match epoch and player.

`tests/test_rules.py` uses **lupa (Lua 5.4 compatible runtime)** to EXECUTE the ORIGINAL .luau source unchanged, with 16 positive/negative lifecycle tests. This is more than static text checking, but it is **NOT native Luau compile, Roblox Studio server/network physics, Android or actual child play**.

## What is not delivered
- A visible 3D summon and movement, real enemy counterplay, D18 original model wiring, world position/team validation, and real two-client replication. `requestScout` only returns a permission token, the real server adapter must spawn the creature. **NOT playable game feature yet**.
- Actual DataStore IO; `export`/`restore` are policy-only trusted server storage boundaries. An integrator must implement datastore write-through with `UpdateAsync`, rate limits, retry/journal receipt handling and session conflict safety.
- Integration with current H1/H2 Game.server, egg/score engine and round controller. This module DOES NOT introduce duplicate game/egg/HP/reward authority.
- Purchase features, shop enablement, keys, monetization or automatic game publication.

## Next acceptance in the #275 chain
1. Independent QA of source contract, a real native Luau compile/replay negative test.
2. New separately owned thin server adapter to authoritative H1/H2 round end; finishRound calls only once and server Random.new():NextInteger(1,10000); full loadout snapshot on start.
3. Real D18 model + true replicated summoned SCOUT in a private Studio place, server validated position/team, enemy sees and can counter, Android one-tap. Two clients, reconnect persistence, anti-duplicate receipt and FPS measured.
4. Sole #220 RC author product-selects after owner H1 FUN baseline, no feature branch writer touches official RC.

## Secure play balance
All seven existing classes can equip scout in one flexible slot. First-time players start with a free tactical ability. Rare affects appearance only, so it cannot add score, combat damage, speed or hatch chance. No paid random items. Visible hatch/collection/equip UI can be built after server rules are independently vetted. Match and score authority stay with the one original Game controller.

## Reproduce
```sh
python -m pip install lupa==2.6
python -m unittest discover -s handoffs/P0D-HATCH-EQUIP-SCOUT-20261113-01/tests -v
```

## Protection
Original source only; public GitHub permissions limited to TRAP RAIDERS. No main writes, merges, Roblox publish, paid features, PC Codex, P0A/B/C CAS changes, or automation changes. Official sole #220 S1 remains 75/100 last reported; OWNER fun gate NO_GO. No release recommendation.
