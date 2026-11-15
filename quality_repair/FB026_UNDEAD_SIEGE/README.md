## V3 increment (2026-11-15)
The latest source-selective 85-script quality candidate now overlays the **native84 siege V3** parent (first AI strike reach and 3-hit gate feedback), not the earlier 84 siege clock parent. Immutable parent Actions #43707427582, artifact #14158224534, Place 822592 B SHA256 `0f256dfd46cad4ff1f94d09730eb6bc1d285ed6fc29f4801cae6e59ea8f4e63a`. This rebase preserves all 84 parent scripts except original Game, then adds the independent Necromancer module: 83/84 parent script bodies exact, new Place **833538 B SHA256 `5192304d75e933e98ccffa20a4ac8abaa1349d4ce156bf63c5353607ec36f084`**. Python 17/17 source/negative tests PASS locally; native/Rojo V3 pending separate exact same-HEAD CI. #476 newest private lobby/item/Beast/7-job X actions remain a separate unretrievable private source lineage; DO NOT replace it with this branch. Product/Art/Studio/Android/OWNER still NO_GO.

# FB026 private cumulative RC85 — Undead squad + castle siege / egg escape / trapper warp

**Implementation, not a release.** Exact parent is the successfully compiled 84-script siege/egg-carrier escape candidate from Actions 43705934185 (artifact 14158253950), SHA256 `89b47d4d919a04b4ea72304681749f2b8f01da768698bf5a1838b8bb5c331e7e` (819,866 B). This is an **independent private candidate**, *not* current official RC82 and *not* #476's latest lobby, field pickups, or new wild-beast features. Do not overwrite either with this Place.

**Real game change:** original Game `JOB_SKILL` Necromancer first Q summons 3 animated actual server NPCs. Repeated authorized Q switches ATTACK/GUARD/FOLLOW; minions track the player or neutral enemies, use original `sevenJobStrike` to reach genuine `MusouHorde:hit` / score / KO; 48-second maximum life / 3 summoned / 0.2-second bounded server ticks. Original Game selected-role ACK, server match epoch, current avatar, team, no egg/stun, private/Studio guards remain. Rebalance, role change, player death/respawn, leave, game end/reset revoke all models.

**Verified newly in this cumulative slice:** enemy hitbox raycasts are explicitly allowed without letting closed doors or castle walls through; a distant zombie cannot teleport through closed castle gates while catching up. Visual parts are noncolliding and don't corrupt bot route. **Only** `server/Game.server.luau` and `server/UndeadSquad.luau` are new/changed, other 83 native84 parent script bodies byte identical (including `MapBuilder`, `SoloTeamBots`, `TrapperWarpService`, HUD, 7 weapons, Beast companion, horde, egg and score).

- New actual source-only `.rbxlx` for the prior V2 parent: `830812 B`, SHA256 `fdd7ed3397c02825c67e986ca0fb1755dbe15f9523ac065cbef1cdc66d81d978` (superseded by V3 above).
- Rebuild and 15 offline XML + source locks + negative/identity tests: **15/15 PASS** with Python 3.
- GitBlob Game: `2c525415f3d22077e40e7079e61a3ddc949c8f6f` / new Module: `4d1e7012e8ab2cd5c40ba6e51db1d52bb2812341`.
- Native Luau 85/85 and Rojo85 workflow provided but **NOT_RUN**, Studio/Android **NOT_RUN**, official RC integrated **NO**, OWNER accepted **NO**, Product/Art **NO_GO**. Do not claim gameplay is fully validated.

## Rebuild

`python3 -m unittest -v test_undead_rc85.py` — pins the actual parent 84 ZIP, source identities, deterministic full 85 Place, actual negative Q and original module identity.

Workflow `p0d_fb026_native85.yml` includes pinned upstream native compiler & Rojo, actual 85-source full rebuild (no source path/class substitutions), and artifact. Copy to `.github/workflows/p0d-fb026-undead-siege-native85.yml` on an isolated draft branch under authenticated existing writer, not to main. The script and parent are in the owner-delivered ZIP. A matched GitHub branch must contain `quality_repair/FB026_UNDEAD_SIEGE/{UndeadSquad.luau,build_undead_rc85.py,test_undead_rc85.py}` to execute the CI; the workflow downloads original parent exactly from successful Actions.

**Next:** source-select into most current authorized #220 RC, after coordinating other writers and avoiding old Game clobber; run sameHEAD native / Rojo, then Roblox Studio 1+2 clients, Android 15min, ART/FUN/OWNER acceptance. YELLOW not release-stopping during private builds, RED stops.