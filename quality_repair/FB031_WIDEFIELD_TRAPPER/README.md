# FB031 — Wide-field Trapper portal repair (real RC87→RC88 game source)

The existing RC87 real TrapperWarpService uses hard-coded old bounds (abs(X)>104 / abs(Z)>60) despite the enlarged castle-era GrassArena (up to 370×294). It also places all warp pads at fixed Y=0.45 even on raised walkable ground.

**Repair in the ONLY existing TrapperWarpService ModuleScript:**

- Server-derived GrassArena Size and CFrame:PointToObjectSpace with a 7-stud inner margin, hard global cap X±178 / Z±140; never client positions.
- Reject if a real collidable castle wall/gate occludes the placement ray.
- Raycast real anchored/collidable ground Normal.Y≥.65, reject large vertical mismatch, place pad relative to the actual ground point.
- Keep original Game JOB_SKILL server ownership, team, match epoch, egg check, 3-transit quota, 2.5s cooldown, collision-protected exit, cleanup, and Studio/private opt-in.

**Frozen parent:** PR #481 Actions https://github.com/kk051780/toy-wars-factory/actions/runs/43716038839 artifact #14162072403, actual 86 scripts, 845174 B SHA256 994d08c141cbd53f7b163c13f61f13ad9266a10c59dc7439a904172d032f07e2.

**Actual private output:** P0D_RC88_FB031_WIDEFIELD_WARP_NATIVE86_PRIVATE.rbxlx 846753 B SHA256 e207a79b777d3b0814ec9580bc9f7ffaffeb07581d6b1010ac89b2846c2accd8. 86 scripts; TrapperWarpService is the sole modified script; the other 85 are byte-exact. Local Python XML/source/negative/repro regression 25/25 PASS.

**Rebuild source:** quality_repair/FB031_WIDEFIELD_TRAPPER/build_rc88.py; fail-closed pinned exact RC87 / one exact original Trapper module GitBlob / anchor guard.

**Genuine native CI** .github/workflows/p0d-fb031-native86-warp.yml downloads pinned original RC87, reconstructs exact 846753 B output, compiles 86 actual Luau scripts and Rojo 7.7.1 verifies class/path/GitBlob for all 86.

**Non-overlap restriction:** Parallel #476 latest private FB029 lineage includes other 7-job and siege/bridge features unavailable as public raw source. Do not overwrite that Game/HUD; author and #220 should selectively adopt this module delta if absent. This RC88 does not claim to be the full #476 cumulative RC. Studio 1/2, Android, FUN, ART and OWNER acceptance are NOT_RUN. Official RC unchanged; no main edit/merge/publish/spend.
