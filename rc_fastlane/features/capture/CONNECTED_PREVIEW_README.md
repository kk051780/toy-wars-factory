# P0D-018 actual-Game capture integration child (private67)

This is a **separate QA/integration preview**, branching from original A-prepared [PR #358](https://github.com/kk051780/toy-wars-factory/pull/358), not a replacement or permission to edit its author branch. Current official baseline **RC66** SHA \`9feb2ec9f5ad8e96b6b727e9f77260b0a5f60991\`.

## Real proposed gameplay
- Use the existing **TRAPPER** job's original \`JOB_SKILL\` action as a server-side capture attempt, keeping the old four-direction PvE strike.
- The original Game selects targets using true player positions, forward facing, 9-stud radius, health, invulnerability, egg carrying, existing NET binding, and server raycast. No client-selected target/distance.
- The existing \`RESCUE\` action rescues a trapped teammate at 7 studs with real LOS, while Guardian NET continues unchanged.
- A short-lived **4-bar noncolliding welded neon cage** and small billboard mark the trapped character; visual and speed/jump are removed via the same original \`restoreSlow\` on rescue, 4s expiry, round end, death, leave or map recovery.
- One per captor team, 18s attacker cooldown, no secondary damage, score, egg, persistent state, Remote or Game.
- \`P0D_ENABLE_ADV_CAPTURE_V1\` is explicit Studio-only opt-in in the **private 67-source** Project. Never change public runtime.

## Safety/CI
- \`apply_capture_preview.py\` validates actual 66-source current source Game git blob \`e6f47b31e37a9209d2ddc5a52647498d0747ee79\`, complete 66 \`SOURCE_LOCK.json\` and \`RC_FEATURE_LOCK.json\`, authored native policy blob, and exactly one insertion per Game anchor.
- \`--enabled false\` performs **zero reads/writes against Project or original source**. \`--enabled true\` creates an *entirely separate scratch copy* of the original private-source DIST, changes only original \`Game.server.luau\` and adds \`CapturePolicy.luau\` (66→67), updating scratch lock+Project.
- Canonical CI still compiles/builds/tests the unchanged official 66 source. **After** official build, a separate step compiles all 67, makes a real Rojo \`.rbxlx\`, checks exact 67 source texts in XML and unchanged source directory, and uploads independent \`P0D-018-PRIVATE67-STUDIO-CAPTURE\` artifact.
- Existing native A-policy 18 tests are run by A's isolated workflow.
- This proposal is not official RC, not Game source adoption, not Studio/Android/FUN tested, not \`P0D_PREP_READY_V1\`, and not a grant to merge/modify main/publish/paid. The A author should review and own final READY code while #220 solely owns official RC CAS integration.

## Remaining review questions
- Roblox engine Studio 1/2-client actual movement/targeting/GUI display, and Android control reachability.
- Sourcery P0/P1 source review plus game-native behavior coverage beyond Luau pure policy, UI discoverability and 4s capture game balance.
- Recheck exact baseline if official RC HEAD changes before legitimate adoption.
