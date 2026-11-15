# FB030 — Real Stage weapon pickup / reach blocked by castle walls (PRIVATE86)

**Feature owner:** Game product quality gate #470, source-selective repair of the already implemented StagePickupLoot module, **not a competing pickup system**.

## Concrete source defect and repair

The real previous RC86 `StagePickupLoot.hitOrigin` moved the origin of `Horde:hit` **3.5 studs forward** whenever WIND_SPEAR was equipped. It did so without verifying whether a solid wall or closed castle portcullis stood between the original position and the projected origin. The original Horde then checked LOS only from the **shifted** point onward. That can bypass physical gate geometry in principle; Roblox Studio engine behavior is not yet measured.

The source-authorized `ProximityPrompt` for a six-pedestal collectible accepted a server distance of 10 studs but did **not** test line of sight, so a closed wall could let a player claim an item from its other side. Both are corrected with one server-only helper using `workspace:Raycast` and `RaycastParams.RespectCanCollide = true`, excluding the claimant avatar and cosmetic pickup model but **not** solid walls or castle gates. Blocked reach keeps original strike origin; blocked prompt returns before assigning any buff. No extra Remote, Game, HP, score, attack or item authority.

## Exact implementation

- Immutable parent: [GitHub native86 + Rojo86 CI #43716032711](https://github.com/kk051780/toy-wars-factory/actions/runs/43716032711) artifact `14162143450`, physical Place **844814 bytes** SHA256 `b614def362c7dad77341e75b568ab153e3001b9a146defe93ff2e9fa94f0dc6d`.
- Output private Studio Place **845972 bytes**, SHA256 `d67f9f68912cb67de0e184844d57649fbe50e5b70ab30cffbe3ee320e6a15cd8`.
- Exactly one Luau source changed: `ServerScriptService.TrapRaidersS1.StagePickupLoot` (GitBlob `3fb954f4...` -> `450ba944...`); other **85/86 script bodies byte identical**. Retains Warrior/Ninja wind Q, Necromancer three-zombie, all seven weapons, physical 3-pickup types and six pedestals, enemy egg escape, physical castle siege, score, official Game, HUD, Trapper warp.
- `python3 -m unittest -v test_stage_los.py`: **24/24 local actual XML/source-lock/negative-regression PASS**. Native Luau/Rojo **not claimed until corresponding same-HEAD Actions passes**, real Studio/Android **NOT RUN**.
- Python `extract_rojo86.py` enumerates and locks all 86 real Roblox Script class/path/Source and generates a pinned Rojo project. The workflow uses native pinned Luau & Rojo and checks exact full script GitBlob mapping, not a mock fixture.

## Rebuild

Place the GitHub artifact ZIP in this directory as `parent_rc86_ci.zip` (the workflow downloads it automatically). Run `python3 build_stage_los.py`, followed by `python3 -m unittest -v test_stage_los.py`. The frozen parent SHA rejects unrelated inputs; a second overlay is refused. Downloadable owner ZIP contains this parent as a reproducibility convenience.

**No official RC adoption**: the newer #476 private RC82 lineage with 3D lobby, wild Beast mounts and 7-job X/C skills is unavailable in this chat (only limited GitHub patch/handoff files). This private RC86 is NOT that full consolidated version. Do not merge the current branch wholesale into official `rc/`, overwrite #476 private Game or duplicate its four alternate loot Tools. #220 sole authorized source integrator must apply the one module hunk to the actual current source after source-claim/CAS/CI, then observe real Roblox Studio and Android wall-gate tests. Product/Art/FUN/OWNER are all NO_GO until verified.
