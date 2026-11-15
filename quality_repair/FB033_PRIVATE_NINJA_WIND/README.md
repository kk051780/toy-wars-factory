# FB033 — RC90 private Ninja wind authority parity / actual 86-source Place

**Real bug:** existing RC89 HUD exposed wind to an ACK-selected NINJA in Studio *or* the explicitly opted-in OWNER private PvE match. Original sole authoritative Game `applyWind` instead checked `RunService:IsStudio()` only. When private server was NonStudio, an Assassin whose classic role was Guardian saw a wind button but the server treated them as Guardian and rejected it; even RAIDER otherwise stayed within the old wind arena unless separate adaptive flag was set.

**Real Game fix (three exact source anchors only):**
1. `selectedJob` now uses `(RunService:IsStudio() or privateHordeTrialAllowed())` + `P0D_RC_ENABLE_SEVEN_JOBS_PVE~=false` + `sevenJobSelected[player]==true`, the same authoritative gates used by the existing `snapshotFor` HUD and job skills.
2. The original `NINJA`-only role filter remains; explicitly opted-in private Ninja can use the server-derived wide-field `S1RaiderWindRules` via existing `WIND_BURST` without new client authority, Remote, Game, HP, score, egg or Store code.
3. Existing real-geometry walkable floor server Raycast (Anchored/CanCollide/NormalY>=.65) is now also mandatory for private nonStudio acknowledged Assassin; traditional public server permission remains unchanged. Cooldown18s/2.5s/Speed27 from unchanged WindRules.

**Immutable parent:** PR #481 FB032 real RC89 artifact #14181260699 / 847911B sha256 `088f06d11c543c6d62fbc70359adad9a49dc2c12a8b9ca6835fed1adb79e4d2d`.

**New actual private Studio Place:** `P0D_RC90_FB033_PRIVATE_NINJA_WIND_PARITY.rbxlx` **848560B SHA256 `4302da965a6a29fe8dc472cd97691a0dbfffa9f713dee556323afe73941941bc`**, 86 source scripts: **Game only modified, other 85 byte-exact**. Local 31/31 Python source-lock, exact binary replay, private permission and safety contract, failed-parent tests PASS.

**Genuine new CI:** [GitHub Actions #43765890971](https://github.com/kk051780/toy-wars-factory/actions/runs/43765890971) commit `f0519024aaf5de38df2e530bb7a6123a15c8fcb5`, SUCCESS. Actual output SHA and 848560 B verified; native Luau compiled actual 86/86, pinned Rojo7.7.1 verified real class/path/GitBlob 86/86. Downloaded artifact #14181889105 and compared real .rbxlx with OWNER copy byte-for-byte exact.

**Owner ChatGPT ZIP:** `TRAP_RAIDERS_FB033_RC90_NATIVE86_ROJO86_PRIVATE_WIND_PLAYTEST.zip` 471579B SHA256 `058b84a826ed262c7786750eef42c7e16b3344086f693a5f86b61a62032f2d5f`: real RC90 Place + exact RC89 parent + full repeatable builder `build_rc90.py` + guarded `portable_apply_to_latest.py` (requires caller-supplied parent SHA and Game GitBlob, only three exact anchored Game hunks, fail-closed for unknown latest Game) + 31 tests + README+receipts+CI_PROOF.

**Critical non-overlap:** Parallel #476 FB029 five-source private latest (3D lobby, seven secondary skills, Mage revive, bridge, beast mount) remains unavailable as raw Place; **RC90 is NOT the fully merged latest #476**. Absolutely no source-overwriting of #476 Game/HUD; the original authors/#220 should examine only these 3 Game hunks and test same-head source CAS.

**Still NO_GO**: actual Roblox Studio 1/2 client, Android, player FUN, art quality and OWNER acceptance NOT_RUN. Official rc/ HEAD `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34` stays unchanged 82 source / catalog31/67. main/merge/Roblox publish/extra paid actions prohibited.
