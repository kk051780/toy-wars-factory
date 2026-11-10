# Integration notes for sole S1 CHAT-INTEGRATOR (#220), not an auto-execution request

**Pinned input source:** initial S1 built-source commit `35d7d0525388e885aac8281eff2315a59831e0cf` root `releases/P0D_S1_KIDS_RC01`. We inspected `src/server/MapBuilder.luau`: `build(Config)` creates `workspace.TRAP_RAIDERS_S1` plus `RED_CASTLE`, `BLUE_CASTLE`, map physical towers/walls, then returns. `default.project.json` mounts `src/server` as `ServerScriptService.TrapRaidersS1`. This packet does not claim equivalence to the current Windows PC Place.

**Optional integration (only #220 sole writer):**

1. Verify all files via `BUILD_MANIFEST.json` from the exact immutable commit. Copy two **Luau source modules** to `releases/P0D_S1_KIDS_RC01/src/server/CastleArchitecture.luau` and `.../CastleArchitecturePlan.luau` **without** an additional `Script`, branch fork or replacement of existing `MapBuilder`.
2. In the existing server-authoritative `MapBuilder.build(config)` after `folder.Parent = workspace` and existing required red/blue castle folders have been constructed (ideally just before final `return result`), insert **one explicit opt-in call**:

   ```luau
   local Architecture = require(script.Parent:WaitForChild("CastleArchitecture"))
   local ok, message = Architecture.build(folder)
   -- Only display/log as a review aid. Do not mutate gameplay on failure.
   if not ok then warn("S1_ARCHITECTURE_OPTIONAL_SKIPPED", message) end
   ```

   The model attaches to the already-built world folder. It is deliberately not automatically started when simply present. If rendering/phone QA reveals clutter, **omit this opt-in call**. Removing the call + these two new modules restores unchanged gameplay.
3. Recompute the unified RC source lockfile, manifest, SOURCE PLAN and receipt; run independent QA. Do not make this optional art a mandatory release blocker. #220 controls the S1 project and accepts/skips the slice. Native Studio / real device check only with final OWNER-directed Codex QA.

**Baked non-gameplay safety:** Each of 50 Parts is `Anchored=true`, `CanCollide=false`, `CanTouch=false`, `CanQuery=false`. Only `Folder S1_ARCHITECTURE_VISUAL_ONLY` is created beneath the known map; a second call fails `ALREADY_BUILT`. Source includes guard for map ownership, allowable piece counts, palette and spatial bounds. Builds off-tree then attaches on successful complete construction. No `Remote`, physics trigger, `Players`, `DataStore`, network, team assignment, round, time, score, egg, HP, pickups, VFX sales, animation or collisions.

**Quality and rollback conditions:** Ensure team silhouettes distinguishable at 480–720px phone landscape; roof crowns not visually occluding gameplay egg/score pad or D07 Gorogan; 2-client equal geometry; no >80-Part model; FPS and memory acceptable on real phone; no accidental false collision; no competing decorative D17 banner system. On unclear appearance or notable performance cost, skip. Actual Studio Luau parser, FPS, mobile and player appeal are **NOT_TESTED/UNKNOWN**.
