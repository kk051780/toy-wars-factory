# D18 v8 / 2 original opt-in static showroom models

Scope: `TRCA-TR-009` Star return launcher, and `TRCA-WE-045` Thunderbird horn. These are **display-only concept source assets**, not usable trap/weapon instances. Canonical IDs, names, rarities and story come from immutable v8 hero72 README Git SHA `176bfc400ef6ec561b129a8163a0f4776e1b9ee4`.

- `ShowcaseCatalog.luau` and `D18ShowcaseFactory.luau` must be siblings when manually evaluating a standalone unpublished Studio Place. No RunService, heartbeat, DataStore, RemoteEvent, game-level ModuleScript nor engine authority is created.
- Disabled sample script is **not a production entrypoint**. It must remain OFF by default. The `Build` operation creates anchored non-colliding cosmetic Parts in a private Folder/Model parent, then `SetPose`, `SetLod`, `GetStatus`, and `Destroy` can be exercised manually.
- Scene placement, visibility, mobile FPS, near/far LOD, Studio 2-client and color-blind silhouette tests remain NOT_TESTED. The #220 S1 sole integrator can INCLUDE_OR_SKIP. Do not wait for this optional content before S1 release.
- Test plan if later chosen: backup latest PC Place/source/HEAD, validate fixed SHA/manifest, inspect native Luau parser, show each from several cameras incl 48px black-white silhouette, verify star/L-telescope and lightning/asymmetric wing, 2-client visibility and mobile FPS, delete both and shut Studio normally. Failure is a rollback of the optional two-module import, not the core game.
- Forbidden: projectile, jumping, traps, weapon damage, knockback, paid ownership, event scheduling, rare loot purchase, free unlock awards, duplicate D07/D11/D17 or other match/egg/HP code. This pack does not imply any in-game free unlock mechanism exists.
- No main branch write, merge, Roblox production publication, spending or PC Codex per-packet instruction. Integrator solely owns release RC selection.
