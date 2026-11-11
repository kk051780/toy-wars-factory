# TRAP RAIDERS D18 / two ORIGINAL 3D low-poly showroom samples (2026-11-12)

- `packet_id=P0D-D18-RESONANCE-SANDSHIP-SHOWCASE-20261112-02`
- `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`
- **PUBLIC_SOURCE_V1: real source in plaintext; no passwords or encryption**.
- Baseline from canonical D18 editorial v8: commit `176bfc400ef6ec561b129a8163a0f4776e1b9ee4`, blob `d68eb6e464b1a1ac9a6415e5241a3d283e50ae6e`, only original names/silhouettes/setting retained.

This packet adds **two unique characters** not previously modeled in the three D18 showroom samples:

1. `TRCA-SP-027` 大地の共鳴 / Mythic Magic / 歯車の赤峡谷: a broken gear circle, floating little stone, and three heavy resonance pillars. 15 anchored primitives; 12 visible in far LOD.
2. `TRCA-VE-090` 時帰りの砂船 / Legendary Vehicle / 砂時計の迷宮: an inverted hourglass hull, striking keyhole mast, and square clock window. 21 anchored primitives; 15 visible in far LOD.

All objects are *display-only* and have no Humanoid, no network events, no DataStore, no damage/physics, no paid products and no vehicle seats. Only one optional demo script exists, **disabled by default**. Static `idle/tap/win/loss` pose targets are available, not a timed animation system. Near/far LOD toggles visibility of minor details, not networked gameplay.

## Portable source

- `data/characters.json`: new hand-authored pure original geometry.
- `tools/generate_catalog.py`: deterministic Luau catalog generator, strict validation and `--check`.
- `luau/ShowcaseCatalog.luau`: actual generated data ModuleScript.
- `luau/ShowcaseFactory.luau`: actual Roblox Build/SetPose/SetLod/GetStatus/Destroy factory, capped at 16 instances.
- `luau/ShowcaseDemo.server.luau`: separate uninstalled/disabled demo.
- `tests/test_showcase.py`: executable stdlib Python safety/geometry/source/protocol tests.
- `BUILD_MANIFEST.json`: canonical six-root-key `P0D_PUBLIC_SOURCE_V1` sha256/size inventory.

Generate and test: `python tools/generate_catalog.py --check` then `python -m unittest discover -s tests -v`.

This packet is NOT a Roblox Studio Play, not a native Luau compiler/renderer pass, not included in #220 S1 RC. The 648-catalog editorial progress is independent of the display-source count. Before any adoption, the sole integrator should compare actual current RC data, verify native Luau parse and 2-client/mobile FPS; skip this entirely if it affects first-release reliability. No main/merge/production publish or purchases are performed.
