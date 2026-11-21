# GQ470 / FB-015 — flagship far-sky matte facets (A source candidate)

## Intent

Create distant stylized cloud **silhouettes**, not glowing spheres, with a deterministic finite budget. Client-local WedgePart geometry gives sky depth behind the flagship battlefield while leaving castles, egg paths, gameplay authority, water and weather scripts untouched. Three shallow, overlapping faceted wedges form each bank.

- 6 banks × 3 wedges = **18 local parts maximum** for keyboard/desktop.
- 4 banks × 3 wedges = **12 local parts maximum** for touch-only clients.
- SmoothPlastic, transparency 0.36–0.52, CastShadow OFF, CanCollide/CanQuery/CanTouch OFF.
- No Neon, particles, billboards, per-frame loops, external IDs, downloaded assets, camera overrides, Lighting edits or monetization.
- The builder runs once, and a folder guard prevents scene duplication on re-entry.

## Unique scope / provenance

- FEATURE_ID: `GQ470_FB015_FAR_SKY_MATTE_CLOUD_BANKS_20261121`
- Parent official RC: `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f`
- Independent source: `EGGRUMBLE_FarSkyFacets.client.luau`
- Candidate Rojo route: `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_FarSkyFacets`
- **No edits** to #942 coast, #939 Realm grade, #916/#934/#956 FieldArt, #926 Forest, #937 Stage or any Game/Host/Swarm/HUD source.
- Claim registered under #218; final path grant, approval, and adoption are separate.

## Source-only QA / integration boundary

Run: `python3 -m unittest discover -s quality_gameplay/gq470_far_sky_real69_20261121 -p test_*.py -v`

Prepare a source-only packet: `python3 quality_gameplay/gq470_far_sky_real69_20261121/pack_candidate.py --out /tmp/gq470-sky-packet`.

The packet is **not** a runnable 70-source Place. Only #220's authenticated integrator can select it from a *fresh* official 69-source baseline, run Luau Native / Rojo ON and OFF / full nonloss / actual Rojo class+source + reverse test, and execute nonforce expected-SHA CAS. The official RC and ACTIVE rich51 are unchanged by this PR.

## ART gate evidence required

1. PC/Android old-new screenshots at the same fixed field viewpoints; inspect horizon contrast, silhouette shape, whiteout, castle visibility, and foreground obstruction.
2. Low-end Android 15-minute FPS median≥30 and p10≥25, no crashes, thermal degradation≤20%; performance values are targets, **not measured**.
3. Human aesthetic review PC≥4.5/5 / Android≥4.0/5 and actual first-three-minute fun proof; OWNER decision.
4. If flat wedge geometry looks cheap or scene clutter reduces orientation, **REWORK/REJECT** instead of inserting simply because code compiles.

Status: `A_PREP_SOURCE_ONLY / NATIVE_NOT_TESTED / ROJO_NOT_TESTED / STUDIO_NOT_TESTED / ART_NO_GO / OWNER_ACCEPTED=0`. Priority #910 playable core remains first.


## 2026-11-21 actual CI strength

Same-head Actions #44840674214 verified the *genuine pinned original* official REAL69 sources: Luau Native 69 OFF + 70 ON = 139 scripts PASS, exact 69 original Source/Class/Route conservation, Rojo original 798390-byte private Place full inverse, and constructed the 801950-byte 70-script private candidate. This does **not** assert human-visible beauty or Roblox engine success. Additional deterministic geometry model checks conservative radial scene clearance, lowest decorative cloud height, and touch/PC geometry budgets. New `ART_CHECK_REPORT.json` explicitly enumerates the 32 unprovided before/after PC/Android screenshots and all unverified runtime/device/human gates. Only a new same-HEAD CI and official #220 fresh-CAS can advance adoption.
