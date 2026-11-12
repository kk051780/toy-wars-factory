# H1 actual source route ↔ castle-wall geometry regression

Issue: #254 · Adoption: P0D-FUN-H1-001 (#250) · Author source: #248

## What this independently tests

Reads original unchanged H1 World and original MapBuilder from the **same pinned source tree**:
`c73f305fb412927aee05b399a4f54a2a16d0579f`.

- Actual original H1 World blob `6de8a8b4f17afd4e11c4be8eb1db556506d9c8df`
- Actual original MapBuilder blob `94655d019fdf9798fa24a350ebf49f8290465ac0`
- Separate #249 only checked frozen S1 route **conceptual feasibility**. This test checks actual newly delivered #248 physical H1 geometry.

The QA uses continuous three-dimensional centerline-to-AABB clipping rather than mere textual path presence. Original castle walls have `CanCollide=true`. It catches **four physically overlapping centerlines**: RED sky ramp, BLUE sky ramp, two sea causeway castle-wall intersections.

## Run using the pinned H1 source checkout

```sh
python handoffs/P0D-H1-ROUTE-WALL-QA-20261113-01/verify_routes.py --selftest
python handoffs/P0D-H1-ROUTE-WALL-QA-20261113-01/verify_routes.py --check
```

The first command should PASS all 10 regression tests. The second emits JSON and exits with code **2** while existing H1 is blocked. **Do not turn exit 2 into green "gameplay route pass"**; successful detection only proves the source collision audit.

## Defect fix contract for #248 original H1 author

To preserve current S1 wall/core/egg authority, candidate lines near z=+57 (sky) and z=-57 (sea), with grounded route end positions around x±72, avoid the four centerline intersections in the simplified source geometry. Adjust signs and railings, verify safe on-foot access to both red/blue eggs and score pads, fall recovery, real 2-client egg transport, mobile touch, and human side-by-side fun. The script's proposed route test only checks this one geometry constraint; actual traversal and safety are **NOT_TESTED**.

The existing floating sky island at y=62 is **decoration only**; its `CanCollide=false` and absent access route must not be misrepresented as a playable castle.

No source edits to #248 original branch, #251 roles, #220 official RC, protected main, Roblox publish/payments, P0A/B/C CAS or the 5 scheduled automations.
