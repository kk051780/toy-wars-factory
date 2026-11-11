# P0-D WORLD FIELD G5 — original Scene.build native Luau executable proof

Original product + route source is **unchanged and pinned** to `2ef409420eff477abb1d6c1b9c95964f29684e42`. This new independent QA lane is issue [#225](https://github.com/kk051780/toy-wars-factory/issues/225), keeping [source owner #224](https://github.com/kk051780/toy-wars-factory/issues/224) and parent [#222](https://github.com/kk051780/toy-wars-factory/issues/222) intact.

## What is executed

- The complete, original `WorldLinkScene.luau` Lua function `Scene.build(world)`, not a summary or copy of its calculations. A test-only Roblox `Instance`, `Workspace`, `Vector3`, `CFrame`, `Color3`, `UDim2`, and `Enum` environment surrounds the original source in the **real pinned native Luau interpreter**, built via GitHub Actions.
- The original `WorldLinkRoutes.luau` is imported intact into the native source wrapper; the only source redirection is the original Roblox `require(script.Parent.WorldLinkRoutes)` to the exact original Routes closure, inside the **test runner only**.
- The generated scene's actual fake-engine Part objects are inspected for land hub, sea/dry aquarium visual, dock, glass sea castle, sky castle, anchored solid ramp geometry, two free ways to each destination, sign Parts + BillboardGui + TextLabel, noncolliding decorative fog/clouds, actual neutral SpawnLocation, and fail-closed duplicate world/existing S1 guards.
- Real route **endpoint geometry** is reconstructed from each generated Part's CFrame rotation, Size, and Position to test seven slope segments' exact start/end alignment, not merely checking words in source.
- Five distinct deliberately corrupted variants of the unchanged original Scene source must FAIL the same native test: noncollidable route surfaces, secret sea shortcut disconnected, one sky route too low to reach castle, missing green direction sign, duplicate-map prevention removed.
- CI reads and verifies original public `BUILD_MANIFEST.json` 12/12 and exact original Git blob SHAs, plus verifies the original frozen source subtree has no changes relative to immutable original commit.

## Limitations

**Engine API doubles are not actual Roblox Studio.** This is executable Luau source proof for creation and structural geometry only. It does not prove Roblox movement physics, collisions, actual moving avatars/vehicles, cross-platform camera, StreamingEnabled, water swimming, eggs, rare NPCs, child fun, lighting or actual mobile FPS. The scene is still **default disabled** in the original Rojo Place; no game integration or owner PC action is authorized by this pack.

## Final owner Studio test plan (NOT performed)
On an OWNER-approved isolated backed-up Place, enable only the source's standalone test switch, then run genuine 2-client and mobile tests. At first spawn, follow blue port bridge and blue deep ramp to glass sea castle, return; then green alternative from land and return; yellow lower+upper route to sky castle and back, purple route and back. Each class should have a free walkable option. Observe lost players, ramp discontinuity, collisions, touch inputs and visual legibility; record actual Place SHA, device/Roblox Studio build, 2-client IDs and independent video before considering any S2+ release integration. Verify no `TRAP_RAIDERS_S1` interference and no duplicated S1 Game authority.

Current official first-release S1 progress remains sole #220 metric; no percentage increment from this optional S2+ world QA.
