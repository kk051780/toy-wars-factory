# P0D / TRAP RAIDERS — H1 4-way actual source independent QA
Date: 2026-11-13 JST. Independent reviewer Issue #258; existing original H1 four-way product integration Issue #255. Scope: **source/real native policy runtime tests only; never official S1 RC write**.

## Frozen full game
- Actual pre-release #255 integrated H1 source commit: `1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b`.
- Existing independently verified native full 28-Luau compiler, original full Rojo 7.7.1 private `.rbxlx` XML 28/28 source-byte match **already green** from #255 GitHub CI run `43342087215`; build includes original server single Game, 2 players/team, RAIDER Wind vs GUARDIAN trap, #253 corrected alternate physical source SKY/SEA route parts, 2 moving neutral creatures, local-only original D18 mascot guide. This is not a physical Studio traversal or multiplayer test.
- Original H0: `3120b9d3c0a5ec58c9f2613c5d186f3493b54f83`.
- **Do not accidentally select #256** as initial H1 scene: that is a later separate optional 15%-detour route tuning; #255 source uses the current #253 original wall-clear candidate blob `cc764b9caaa293ff747489e02e607af4502ddca4`.

## What this QA does beyond #255 integration's own CI
`tests/test_h1_fourway_source.py` first loads the **genuine 28 generated full-game Luau files**; it fails until actual unchanged `#255 tools/assemble.py --assemble` has produced them. Checks byte-exact original Game/HUD/Wind/Map/World/D18 blobs, unchanged 25 original whole-game scripts except the one dedicated world path, one authoritative Game/Remote, original server egg/score/traps, Replay sequence, wind ability/egg exclusion/trap counter, D18 read-only guide + ordered snapshot + actual matching client Rojo mount, actual geometric original castle/rock collision boxes and 6 connected sea/sky walkway parts. More importantly, it rejects injected unsafe authority, 7-role fake, no-egg-carry gating, wall collisions, unapproved paid world, fake D18 FireServer/guide replay acceptance, broken waypoint continuity and disappeared creature. The source geometry gate uses a **3D slope-aware oriented path ribbon and real rock heights**, not a false-positive flat X/Z shadow: the existing elevated SKY ramp passes over original low stone pillars without touching them. A deliberately wall-crossing ramp is still rejected.

`tools/generate_native_policy_test.py` then reads the EXACT assembled `S1RaiderWindRules.luau`, `S1TrapRules.luau`, and `D18MascotGuideRules.luau` after checking their real Git blob hashes, wraps each original pure Luau module in its own local function, and writes a single standalone native Luau script. Its assertions actually call the original Luau functions: 2 teams, wind eligibility, speed/cooldown, egg carry, Guardian slow/traps, enemy/friendly/expired traps, client-side guide to enemy egg or own pad, stale update/round rejection, spoofed event/invalid payload. In the GitHub CI the runtime is built from pinned upstream Luau git SHA `f46d879e28302a430029304f7f6a162aed66f103` and executed, NOT a Python model of Luau. **This still cannot execute Roblox APIs, original whole Game's physics or real Studio 2-client.**

## Execute in an isolated checkout
```sh
python3 -B handoffs/P0D-H1-WOW-4WAY-20261113-01/tools/assemble.py --verify
python3 -B handoffs/P0D-H1-WOW-4WAY-20261113-01/tools/assemble.py --assemble
python3 -B -m unittest discover -s handoffs/P0D-H1-FOURWAY-INDEPENDENT-QA-20261113-01/tests -p 'test_*.py' -v
python3 -B handoffs/P0D-H1-FOURWAY-INDEPENDENT-QA-20261113-01/tools/generate_native_policy_test.py --write /tmp/p0d_h1_native_policy.luau
# The pinned Luau CLI binary executes /tmp/p0d_h1_native_policy.luau in the dedicated GitHub Action.
```

## Known UX/product risks explicitly NOT cleared by source QA
- The RAIDER wind action is server-denied while carrying egg, but original H1 HUD still displays the wind button during ACTIVE RAIDER even when carrying. **Child clarity follow-up:** disable or visually gray out unavailable Wind action with concise "卵運搬中" hint and preserve sequence authority; don't silently count source security as an intuitive mobile UI.
- D18 mascot draws four near-start glowing breadcrumbs toward a straight-line target; these are directional hints, not guaranteed physical turn-by-turn sky/sea castle pathfinding. No real-world player success rate measured.
- Even six source-defined 3D route segments with zero *estimated* original solid wall footprints may not be genuinely walkable or safe against Roblox engine collisions, camera angles, wind speed or low-end mobile conditions. A source PASS is NOT Studio PASS, kid enjoyment, measurable retention or publication approval.
- Existing #256 route pacing improvement may be selected after private H1 gameplay comparison, not substituted during current independent QA.

## H1 next blockers / ownership
Current gate is #250 `INDEPENDENT_QA`; this branch is separate from #255 release candidate composer and from #220 protected sole official RC. After actual independent script CI evidence, **#220 solely** decides if an H1 candidate can proceed to official private integration/testing; OWNER conducts real Roblox Studio H0/H1 2clients + Android mobile; records first 90 seconds, egg retrieval and return, RAIDER vs GUARDIAN, sea/sky camera/physical landing, original moving neutral interaction, guide prompt clarity, winner/rematch, Output errors/FPS, Studio shutdown. Humans must find H1 materially more fun; **FUN_GATE=NO_GO** until genuine feedback.

No main change/merge/live Roblox publication/paid features/extra spending/Windows Codex or P0A/B/C/five automations. The last sole S1 release score remains 75/100 and WorldField parent 4/8=50%; do not manufacture completion points from source code.

## Source QA regression refinement
In the first independent run, the 2D footprint check conservatively flagged the SKY_RAMP_RED over a low stone pillar even though the ramp rises to 16 studs and the original pillar ends at y=6.5. The full author's Rojo source was unchanged. A corrected 3D swept-ribbon source-space test now accounts for slab collision with the original 4 solid castle walls and 5 stone rock volumes, with explicit negative wall-clipping tests. This is stronger source geometry reasoning, but is still **not** Roblox physics proof. Total QA Python methods: 20 integration/unsafe+4 receipt; native runtime policy checks are separate. Read real CI logs before claiming overall PASS.
