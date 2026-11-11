# WF-13 宇宙・星の無重力ドーム / implementation prototype

**Status: REAL SOURCE, ISOLATED OPT-IN, NOT STUDIO-TESTED.**
Owned slice `WF13-LOCAL-GRAVITY-PROTOTYPE-20261112-01`, task https://github.com/kk051780/toy-wars-factory/issues/223, design source https://github.com/kk051780/toy-wars-factory/issues/222, keyless V2 design SHA `4a75a271fda7afbf786493edd42bc2c645a18b60`.

## What is actually created

- `src/WF13Policy.luau`: original pure numeric ellipsoid/force/landing/clamping contract.
- `src/WF13ZoneController.luau`: one server-owned original local VectorForce per character, server-only position checks, ownership-state restore, two-second landing taper, time cap, duplicate-zone guard, death/respawn/removal/stop cleanup, below-map safe-pad recovery.
- `src/WF13Scene.luau`: original lightweight purple sphere / 18 colored orbit signs / 26 stars / castle deck and tower / **15 physical free stairs** / Japanese kid-readable bubble sign / fallback recovery pad.
- `src/WF13Demo.server.luau`: actual Roblox server entrypoint **DISABLED BY DEFAULT**; refuses an existing S1 map to avoid duplicate game authority.
- `default.project.json`: standalone Rojo map for a protected test Place, NOT the official #220 game RC.
- Python contract and malicious-code mutation tests, native Luau policy test runner, strict public-source SHA manifest validator.

## Safety and limitations

Does **not** patch TRAP RAIDERS S1 Game/MapBuilder, D07/D08 boss, roles, eggs, health, remote, ranks, rewards or D18 catalogue. Existing public source permission for TRAP RAIDERS applies, not Roblox game publish approval. No code is run automatically in production.

The `Workspace.Gravity` property is global and is only read, never set. The server verifies ellipsoid membership from the actual HumanoidRootPart Position; the client cannot choose eligibility, force, egg theft, winner, or a network owner. During the zone, the server conservatively takes physics network ownership; this may cause input jitter on actual phones, and must be tested. On exit it restores the old owner or auto ownership. Basepart geometry may need adjustment after real engine collision and StreamingEnabled testing.

`VectorForce` can cause unbounded speeds without controls, hence timed residence + horizontal/vertical limits + short landing fade and emergency pad. A multiplayer Studio/physical phone test is **required** to prove that humanoids can jump, land and carry eggs safely; source-only unit tests do **not** prove real 3D performance.

## Build and test in an ISOLATED test place (owner final batch only)

1. Use latest parent Issue #222 and P0-D #218/#220 state before integrating.
2. Copy the source folder into a dedicated Rojo project using `default.project.json`, build/test in a **new backed-up nonproduction Place**, not the existing protected S1.
3. For a test only, set `ENABLE_WF13_ISOLATED_DEMO = true` in the standalone bootstrap (NEVER flip this in official RC without sole integrator's approval).
4. Run Studio two-client test: both sides can walk to the same bubble and reach deck via the free stairs; test death/rejoin, out of zone, 18s timeout, disconnect, reentry, and safe falling; no duplicate force or full-map gravity change.
5. On mobile: verify motion responsiveness, FPS / memory and camera sickness; disable feature if input jitter occurs.
6. Freeze exact SHA, independent QA and owner release decision before a real game inclusion.

## Safe rollout

H0: existing S1 map unchanged. H1: one WF13 dome opt-in, disabled unless #220 elects inclusion (S2+ preferred). Entire rollback: turn feature flag OFF/remove WF13 optional Rojo mappings; do not touch Game.server or other map assets. If native and Studio tests fail, do not publish an ad as live game feature.

No real Studio, two-client or phone QA was performed by this Chat. No actual player satisfaction, retention or revenue uplift is claimed.
