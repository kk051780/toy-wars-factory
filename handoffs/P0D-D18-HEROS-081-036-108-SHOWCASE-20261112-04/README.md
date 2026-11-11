# TRAP RAIDERS — D18 original three-mascot showroom source

- Packet: `P0D-D18-HEROS-081-036-108-SHOWCASE-20261112-04`
- Source mode: `PUBLIC_SOURCE_V1`; unencrypted, no external assets, keys or licenses.
- Evidence: immutable v8 hero-art source commit `176bfc400ef6ec561b129a8163a0f4776e1b9ee4`, README Git blob `d68eb6e464b1a1ac9a6415e5241a3d283e50ae6e`.
- **Status: unintegrated SOURCE ONLY; native Luau parser, Roblox Studio, 2-client mobile, FPS, real child preference and revenue NOT TESTED.**

## New original collectible art, no performance bonuses

| ID | Original name | Concept | Parts (near / far visible) |
|---|---|---|---|
| TRCA-SP-081 | 黄金の種まき | Oversized wooden hand bearing one golden seed and three wheat spokes | 13 / 11 |
| TRCA-VE-036 | 永久晶観測台 | Sled, tilted octagonal cracked ice mirror and one taller crystal | 20 / 14 |
| TRCA-ZO-108 | 七鈴の大隊長 | Seven-bell semicircle crown, uneven boots and white return roster | 21 / 15 |

Original 3D is made entirely from Roblox primitive `Part`/`WedgePart` calls (static and anchored). All models are display props: `CanCollide=false`, `CanTouch=false`, `CanQuery=false`. Factory exposes `Build`, `SetPose(idle/tap/win/loss)`, `SetLod`, `GetStatus`, `Destroy`. Maximum 12 simultaneously parented models in this isolated factory. `DisabledShowcaseDemo.server.luau` is OFF by default and is not in the S1 Rojo project.

The v8 free-unlock concepts are only editorial hypotheses; no item rewards, player inventory, D17 entitlements, D11 NPC, D14 vehicle, combat/trap/magic mechanics, storage, remotes, sounds, animation heartbeat, random or time-based urgency are implemented.

To verify independently: `python tools/generate_catalog.py --check`, `python -m unittest discover -s tests -p 'test_*.py' -v`, `python tools/verify_pack.py`. To integrate, **only #220 sole CHAT-INTEGRATOR** may opt into copied isolated source after full code review; see `docs/INTEGRATION.md`. No writes to main or the official RC branch were made by this packet.
