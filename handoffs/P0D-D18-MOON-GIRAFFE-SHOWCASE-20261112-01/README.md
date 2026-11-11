# TRAP RAIDERS D18 / 月冠キリン — 3D sample 3 of 72 flagship designs

- `game_id=TRAP_RAIDERS` / `work_id=p0d-siege-v19`
- `packet_id=P0D-D18-MOON-GIRAFFE-SHOWCASE-20261112-01`
- Existing canon: [D18 v8 immutable editorial hero source](https://github.com/kk051780/toy-wars-factory/blob/176bfc400ef6ec561b129a8163a0f4776e1b9ee4/handoffs/P0D-D18-HERO72-FINAL12-20261111-01/README.md), exactly `TRCA-BE-072` **月冠キリン**, `LEGENDARY`, 月縫いの墓園.
- **New isolated 18-Part (15 far) visual-only low-poly primitive model**, independent of existing `TRCA-BE-018` and `TRCA-ZO-054` samples. Distinctive long neck, left-open silver crescent crown, stitched cloth cape, one white sock. No external IP, asset ID or imported mesh.
- Luau implementation `src/MoonGiraffeShowcase.luau` exports `Build(parent, origin)`, `SetPose(model, 'idle'|'tap'|'win'|'loss')`, `SetLod(model, far)`, `GetStatus(model)`, `Destroy(model)`. Poses are **instant deterministic static poses**, not animation/player progression. The model does not spawn itself.
- All Part instances Anchored=true, CanCollide/CanTouch/CanQuery=false, CastShadow=false, no Humanoid, Remote, event, reward, ownership, premium purchase, AI, XP, DataStore, or physics authority. No paid random reward or P2W.
- The two existing D18 samples remain untouched; no branch/main/RC integration. **Source-only, Studio/Luau runtime/mobile/FPS/children's preference NOT_TESTED.** No revenue evidence.
- Public plaintext source & SHA256 manifest per `P0D_PUBLIC_SOURCE_V1`; no password, AES, secret, or third-party intellectual property.

## Offline source checks

```sh
python -m unittest discover -s tests -v
python tests/test_moon_giraffe.py
```

True Studio integration, optional inclusion, QA and rollback: `docs/INTEGRATION.md`.
