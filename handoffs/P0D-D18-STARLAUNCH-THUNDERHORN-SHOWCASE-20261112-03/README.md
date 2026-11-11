# TRAP RAIDERS | D18: Star-launcher & Thunderbird-horn original showroom source

`packet_id=P0D-D18-STARLAUNCH-THUNDERHORN-SHOWCASE-20261112-03`  
`game_id=TRAP_RAIDERS` / `work_id=p0d-siege-v19`  
`delivery_mode=PUBLIC_SOURCE_V1` (PLAINTEXT; no AES/password/key)

**Actual source-only content:** two new, distinct noncombat procedural 3D display assets based on existing editorial v8 only.

- `TRCA-TR-009` **星跳ねの発射台** (trap category, MYTHIC): sideways crescent-shaped wide base, sideways L telescope, yellow star button, return-ribbon, night-navy/brass blue. Never launches real objects or players.
- `TRCA-WE-045` **雷鳥ホルン** (weapon category, LEGENDARY): lightning zigzag horn, asymmetric wings, cloud-bell end and blue feather tag. No attacks or knockback.

`data/showcase_models.json` is human-readable source art; `tools/generate_catalog.py` renders the **exact** `luau/ShowcaseCatalog.luau` deterministic data. `luau/D18ShowcaseFactory.luau` creates safe anchored/no-collision Parts with explicit Build/SetPose/SetLod/GetStatus/Destroy; `DisabledShowcaseDemo.server.luau` is OFF and not mounted into any existing game.

Quick offline checks:
```
python tools/generate_catalog.py --check
python -m unittest discover -s tests -v
python tools/verify_pack.py
```

These tests are structural and source-level, not native Luau or Roblox Studio runtime tests. Real 2client/mobile visual appearance, frame-rate and children's preferences: **NOT_TESTED/UNKNOWN**. D18 3D sample source count is cumulative only, never an S1 release metric. No D01-D17, D18 canonical source, #220 sole RC branch, main, unlock ledger, monetization, production game or existing automations are modified.

See `docs/INTEGRATION.md` for evaluation gates and rollback.
