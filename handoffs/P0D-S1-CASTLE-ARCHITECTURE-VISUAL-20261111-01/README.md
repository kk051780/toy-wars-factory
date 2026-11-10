# TRAP RAIDERS / S1 castle architecture — optional original source (2026-11-11)

Game `TRAP_RAIDERS`, work `p0d-siege-v19`; packet `P0D-S1-CASTLE-ARCHITECTURE-VISUAL-20261111-01`.

**Purpose:** Add deterministic, distinctive, lightweight 3D battlements / castle roof crowns / safe boundary landmark **above the existing, collidable map pieces**. It creates exactly **50 purely decorative Part instances** (plus one Folder), mirroring red and blue map architecture. No external asset IDs, textures, commercial brand, copyrighted third-party art, power, randomized paid loot, or player tracking. This is ORIGINAL LOW-POLY source art, not a final Studio-rendered model.

**Non-overlap:** The existing `MapBuilder.build` alone makes terrain, cores, egg, spawn, collidable walls and towers. This package adds decoration only and **never alters those objects**. D17 castle banners / egg glow / victory confetti and D18 collectible mascot models are excluded. D07 boss, D08 chooser, D11 neutral, rewards, server damage and all HUD/routes remain unchanged. Not a second map generator or event scheduler.

**Source files:** `src/CastleArchitecture.luau` (opt-in-only, idempotent ModuleScript) + `src/CastleArchitecturePlan.luau` (auto-generated from authoritative `assets/architecture_spec.json`). Generator `tools/generate_architecture.py`; deterministic 40 negative/positive Python tests; `BUILD_MANIFEST.json` canonical PUBLIC_SOURCE_V1.

Run: `python tools/generate_architecture.py --check` and `python -m unittest discover -s tests -v`. This validates file source, geometry and safety invariants, **NOT Roblox native Luau parsing, 2client performance, device collisions or actual Studio appearance**.

**Status:** Candidate only, **OFF unless the sole RC writer explicitly calls the ModuleScript once**. PC newest local Place/content unknown. The #220 S1 Chat integrator is the only writer to `rc/p0d-s1-kids-rc01`; see `docs/INTEGRATION.md`. No P0-A/B/C CAS/auth change, main write, merge, production Roblox publish, purchases, billing, or automation changes. This source packet can be reviewed/ignored without blocking first release.
