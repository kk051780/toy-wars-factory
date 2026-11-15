# FB029 | P0D GAME品質ゲート — 風走りの拡張判定と暗殺者での使用

**ISOLATED DRAFT / SOURCE SELECTIVE / NOT AN OFFICIAL RC WRITE.** このディレクトリは別ソース担当との競合を防ぐための持ち込みLuau。正規RCには配置/マージしていない。

## What is implemented now
ChatGPT USER-private ZIP `TRAP_RAIDERS_FB029_WIND_RC_INTEGRATED_PLAYTEST.zip` (684879 B; SHA256 `12a5ae5117104fa6a29e984a21a0c57ca951581b990bbf1c8abad82e14508018`) contains a real private Studio Place `TRAP_RAIDERS_RC82_FB029_WIND_INTEGRATED_PRIVATE_STUDIO.rbxlx` (812292 B; SHA256 `4d24c595db5492b830c85f4b21713ce92fce984a9435bef0159db2a3fccbf841`), `build_fb029.py`, `portable_apply.py`, `test_fb029.py`, pinned FB028 parent ZIP and receipt. Fixed source parent was the previous 83-script FB028 cumulative private Place SHA256 `09b35531587b8d82ced95fd93e390685294a95c5459058cee17c1416ce7095df`.

**Changed sources in private Place:** Game + TrapRaidersHUD + S1RaiderWindRules only (3/83), untouched source body 80/83 byte-exact. No new Remote/HP/egg/score/Store authority. Static 22/22 PASS, including synthetic FB020/#476-style source-selective rebase check and fail-closed unknown-source negative check. Native Luau/Rojo/Studio/Android/OWNER **NOT_RUN; PRODUCT_NO_GO**.

## Code handoff

`S1RaiderWindRules.private.luau` is a full runnable Luau policy function (functionally equivalent to the Place's policy module, comments differ). The source logic preserves standard RAIDER wind limit (X ±120, Z ±65, Y 1..12), but accepts optional `studioArena=true` plus bounded server-validated extents for private Studio. **Do not turn this into client input**.

Server integration on original Game's `applyWind`: only in `RunService:IsStudio()` and with a real server-side `sevenJobLastChoose[player]` plus `sevenJobs[player] == "NINJA"` may the role for the existing WindRules policy be mapped to RAIDER. Server must Raycast real anchored collidable floor and obtain arena dimensions from `workspace.TRAP_RAIDERS_S1.GrassArena`, then attach `windInput.studioArena=true` and `arenaMaxX=min(178, GrassArena.Size.X/2-7)`, `arenaMaxZ=min(140,GrassArena.Size.Z/2-7)`, `arenaMaxY=30`. UI existing `WIND_BURST` button/keypress is enabled for actual selected Assassin; no permanent HUD.

**Import warning:** PR #476 has its *own* private FB027 TEAMPLAY candidate with 7 role secondary skills, beast AI, castle/bridge; this latest full Place is not present in GitHub PR files and was NOT AVAILABLE for testing. Never overwrite its full Game/HUD with FB029's older Game/HUD. Existing #476 FB020 wind patch hands `windInput.arenaMaxX=178`/Z=140 to `WindRules`, but the RC82 original WindRules ignores these new fields. Confirm actual source before replacing module. The portable patch (inside private ZIP) adds the missing server-owned `studioArena` marker and policy only if exact known anchors match. Reject unknown changes automatically.

#220 ONLY: import approved source-selective delta at same HEAD CAS/native/Rojo + PC Studio and Android test, then #470 product quality/ #420 art/ OWNER. No main edits, merge, publishing, cost.
