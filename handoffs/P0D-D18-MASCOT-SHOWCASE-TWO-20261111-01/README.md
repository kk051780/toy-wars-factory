# TRAP RAIDERS / D18: 2 flagship mascot low-poly showroom (source-only candidate)

- `game_id=TRAP_RAIDERS` / `work_id=p0d-siege-v19`
- `packet_id=P0D-D18-MASCOT-SHOWCASE-TWO-20261111-01`
- **Source mode: PUBLIC_SOURCE_V1, no AES/no keys; original game code only.**
- **State: generated Luau source + offline Python structural tests. Native Luau parse and Roblox Studio QA are NOT_TESTED.**
- Original source of editorial names/silhouettes: [D18 v8 12-hero packet, immutable SHA `176bfc400ef6ec561b129a8163a0f4776e1b9ee4`](https://github.com/kk051780/toy-wars-factory/tree/176bfc400ef6ec561b129a8163a0f4776e1b9ee4/handoffs/P0D-D18-HERO72-FINAL12-20261111-01). This is a **NEW 3D draft**, not a recovered or modified older game asset.

## What this delivers

`TRCA-BE-018` **祖樹の角鹿** (forest deer, asymmetric branched tree antlers, tiny leaf, wooden door saddle), and `TRCA-ZO-054` **灯台のお迎え兵** (lighthouse hat, unequal boots, wave flag, shell button). Both are silhouette-differentiated, original, child-friendly, noncombat stationary showroom props created from Roblox primitive Parts. No external meshes, images, sounds, asset IDs, or unlicensed material are included.

- `data/mascot_geometry.json`: two immutable-identity geometry descriptions with part palette, pose offsets, and far LOD flags. **21** Parts for deer, **16** for greeter; distant visible **17** / **12**.
- `data/editorial_source_excerpt.json`: original v8 art-direction ID/name/world/rarity/character story provenance.
- `tools/generate_catalog.py`: deterministic JSON-to-Luau generation; `--check` avoids JSON/runtime divergence.
- `luau/MascotPreviewCatalog.luau`: generated catalog.
- `luau/MascotPreviewFactory.luau`: `Build(parent, characterId, origin)`, `SetPose(model, "idle"|"tap"|"win"|"loss")`, `SetLod(model, bool)`, `GetStatus(model)`, `Destroy(model)`.
- `luau/ShowcaseDemo.server.luau`: disabled sample. No startup integration, remote, listener, heartbeat, DataStore, Humanoid, physics, or purchase.
- `tests/test_mascot_preview.py`: structural contract assertions, not Roblox QA.

## Non-negotiable boundaries

**Zero gameplay authority.** All created parts are anchored, `CanCollide=false`, `CanTouch=false`, `CanQuery=false`, `CastShadow=false`. No combat, targeting, AI, spawn, trap, summon, zombie resurrection, physics, nav, reward, cosmetic entitlement, store, analytics, map or event director. Neither model is a true D11 NPC or a D07 boss. **No automatic insertion into live source or main**. Demo remains `ENABLED=false` unless the OWNER's Windows Codex explicitly enables it in a **copied, unpublished, isolated Studio Place** after the current D07 safety QA.

The static `SetPose()` feature provides deterministic *pose targets*, not timed animation or sound playback. Distant LOD hides detail Parts without destroying them. No claims about FPS, readability, colors, child preference, Roblox native parsing, or revenue before true tests.

## Source use

```powershell
python -m unittest discover -s tests -p test_mascot_preview.py -v
python tools/generate_catalog.py --check
# In approved isolated Studio: keep three Luau ModuleScripts/Script as siblings
# The ShowcaseDemo script is disabled by default, and requires deliberate OWNER flip.
```

Codex integration, QA and rollback gates: `docs/CODEX_ACCEPTANCE.md`. Original art/legal boundary: `docs/ORIGINALITY.md`. Standalone package only; no third-party IP or owner-private Place is included.
