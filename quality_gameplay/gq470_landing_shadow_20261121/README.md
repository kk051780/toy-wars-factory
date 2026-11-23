# GQ470 / FB-015 — landing silhouette matte 3D (isolated A PREP)

## The actual visual change

Add **one local 3D landing marker** for the player's own avatar only, visible while descending in Freefall and a real non-water, opaque walkable surface is detected within 4.5–48 studs. It is an original low-glare disc with an amber chevron aligned to the avatar's facing direction and the terrain slope. This improves air-to-ground spatial legibility without a minimap overlay, spawn/hit logic, camera replacement, score rules, or remote messages. The marker hides for dead/seated/swimming/spectating avatars, invisible/water/steep surfaces, ascent and no streamed ground. No fake exact landing promise is made when a collision target cannot be established.

This scope is deliberately **different** from existing visual PR lanes: #970 ART16 composite, existing footstep/ground dust PR, castle path tiles and minimap PRs, #949/952 hit FX, #939 underwater tone, and lobby HUD. No existing `ServerScriptService`/`Game`/`Combat`/`Host` source is edited.

## Source-level budget and safeguards

- Exactly **3 local, anchored, non-collidable, non-queryable, non-touchable, no-shadow SmoothPlastic Parts**: one dark disc + two amber chevron strips.
- Exactly **1 downward raycast per 0.12s** (at most ~8.34 Hz). Nothing per enemy/egg/AI or per frame.
- **0 Neon, lights, particle emitters, sounds, textures, marketplace calls, remotes, damage, money, persistent state or server mutations.**
- HUD screen-space occupancy: **0px**. Ground marker disappears outside short descent proximity, preserving combat readability.
- Easy per-feature rollback: unselect one `StarterPlayerScripts/EGGRUMBLE_LandingShadow` LocalScript; retain every existing source byte.

## Independent checks / negative cases

`python3 -B compose_landing70.py --self-test` checks 14 code-mutation RED cases (collision/touch/query, shadows, Neon, particles, remotes, marketplace, health write, excess raycast, changed fall/spectator guard, excessive Part/sample rates) and a dummy **69 to 70 ON / 69 OFF** selected-Source composition. These are STATIC SIMULATION tests, *not* Roblox-engine tests. CI also compiles actual Luau source with pinned Luau CLI and builds a one-script Rojo Place with pinned Rojo. Every CI pass is labeled `SOURCE_PREP_ONLY`.

For real ART16/ART17 candidate ingestion, the authorized B integrator first pins source artifact and actual 69-source `EGGRUMBLE_REAL69.project.json`, then executes:

```bash
python3 -B quality_gameplay/gq470_landing_shadow_20261121/compose_landing70.py \
  --base /path/to/verified/real69-art-bundle \
  --out /tmp/GQ470_LANDING_REAL70_CANDIDATE
```

The composer refuses a non-69 or missing base, preexisting route, path escape, or unexpected change to any of 69 source SHA256s; it produces ON70 and exact OFF69 candidate trees and an evidence receipt. **Do not use the resulting 70-script candidate as the formal single RC** until #220 authenticated B CAS, same-HEAD native+Rojo+source-lock/safety QA, and integration ledger reconcile it. If B is already integrating newer 70+ scripts from other chats, port only this one unique LocalScript to the new exact HEAD, don't replace the whole profile with an older count.

## Studio / Android ART gate (still NO_GO)

For the eventual integrated official RC HEAD, capture paired unedited PC and Android screenshots/brief clips of airborne descent over flat grass, stone path, near water and castle roof, plus no-marker frames during swimming, spectator mode, death, steep slopes and far altitude. Test low graphics & StreamingEnabled while 16 players and neutral swarm remain visible. Verify camera no longer blocks hero and the landing cue never hides eggs, objectives, enemy silhouettes or attack VFX. Run low-end Android 15 minutes (median >=30fps, p10 >=25fps, thermal degradation <=20%), 8 scene * PC/Android * before/after = **32 genuine captures** for the full #420 gate. A true engine test may reject the feature; disable by unselecting the file, not by waiving the gate.

**State:** source-only A PREP, not an official RC integration; Studio/Android/human FUN untested and OWNER ART not accepted. P0 game start, egg deposit and victory remain higher priority than this art enhancement.
