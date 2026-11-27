# FB032 RC89: PR481 RC88 + PR479 wall-safe StagePickupLoot one-source merger

## Real result

- **Immutable main parent:** [PR481 RC88](https://github.com/kk051780/toy-wars-factory/actions/runs/43754971010), artifact #14178002762, sha256 `e207a79b777d3b0814ec9580bc9f7ffaffeb07581d6b1010ac89b2846c2accd8`, 846753 B, 86 scripts.
- **Exact incoming source:** [PR479 FB030](https://github.com/kk051780/toy-wars-factory/actions/runs/43754858996), artifact #14177514150, sha256 `d67f9f68912cb67de0e184844d57649fbe50e5b70ab30cffbe3ee320e6a15cd8`, 845972 B.
- **Actual composed private Studio Place:** `P0D_RC89_FB032_WIND_WARP_WALL_SAFE_PRIVATE.rbxlx`, **847911 B sha256 `088f06d11c543c6d62fbc70359adad9a49dc2c12a8b9ca6835fed1adb79e4d2d`**. The sole changed path is `ServerScriptService/TrapRaidersS1/StagePickupLoot`; other 85 original scripts are byte-exact (including original Game/HUD/UndeadSquad/TrapperWarpService/real wind/egg+score).

## Actual gameplay repair

Old StagePickupLoot let 10-stud ProximityPrompt claim weapons through closed castle walls and used up to 3.5 stud forward attack-origin projection without solid-wall LOS. The source from PR479 supplies a server-only Raycast with RespectCanCollide: line-of-sight through real geometry to pickup, and no forward origin through solid gate/walls. Physics and original server Horde authority remain intact. Unlike duplicating the feature, this is exactly one native-pass module imported on top of our RC88.

## Validation

- Local Python complete 86-source inventory and identity + negative parent/source/hash + deterministic XML reparse/replay **30/30 PASS** (Private ZIP).
- [FB032 true native CI run #43762244609](https://github.com/kk051780/toy-wars-factory/actions/runs/43762244609) **SUCCESS**, actual compiled Luau **86/86 PASS**, pinned Rojo 7.7.1 exact path/class/GitBlob **86/86 PASS**, output SHA check PASS, 85 old sources exact.
- CI artifact #14181260699 `P0D-FB032-RC89-MERGED-WALL-LOOT-NATIVE86-PRIVATE-NOGO` independently downloaded and exact bytes matched the user-private candidate.
- Public repository has only fail-closed reproducible merge code `quality_repair/FB032_RC89_MERGED_WIND_WARP_WALL_LOS/build_rc89_ci.py` + CI; private Place and exact parent are in OWNER ZIP, not published here.

## Non-overwrite constraints

Official RC branch remains separate HEAD `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34` with 82 scripts / RC-catalog31/67. Parallel PR #476 includes **different nonpublic FB029 5-source features**: 3D lobby, all 7 job secondary skills, Mage revive, bridge/snare, Beast mount and four tool kinds. **These were not integrated** because public #476 lacks the actual Game/HUD/Place source. Do not overwrite this latest author version with RC89 Game/HUD. #220 only authorized CAS sameHEAD writer can source-selectively adopt, then Studio 1- and 2-client/Android/ART/FUN/OWNER gating. No main/merge/Roblox publish/pay. Native compile is not in-game validation.
