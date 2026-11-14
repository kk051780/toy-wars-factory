# P0D TALKING NPC V1 — PREP source candidate

**Origin:** #333 (OWNER proposal); #219 (PRODUCT_DRI); #250 (adoption); #220 (sole canonical RC writer).
**Review:** PR #334; first source-exact PR preview green Actions #43539140466 on official RC65+3 = 68 scripts. Branch's fixed SHA/CI must be rechecked whenever revised. Canonical RC moves independently.

## Implemented source (not yet mounted in official RC)
- TalkingNPCDirector.luau: deterministic server-authorized Japanese greeting, observed enemy, carried egg, visible star fragments, suspect rumor and unlocked realm hints. Voice IDs 701/702. Per-speaker per-user 30s normal/15s urgent cooldown helper, plus 20s per-client TTS budget.
- TalkingNPCRuntime.server.luau: four original nonblocking floating 3D NPCs (NAVI x2, MADRON, ORACLE), server proximity validation, existing Game RemoteEvent FireClient (no second Remote), LOS+45-stud private enemy observations, current event checks, opt-in ServerStorage attribute. No rewards, XP, HP, save or new round authority.
- TalkingNPCClient.client.luau: caption bubble designed for mobile (Android UX NOT_TESTED), voice ON/OFF, AudioTextToSpeech with AudioDeviceOutput+Wire; silent subtitle fallback when TTS is not available or throttled.
- PREP_SOURCE_LOCK.json pins all 3 script Git blobs. tests/test_p0d_talking_npc_prep.py provides source-only safety/lock tests.

## Independent gameplay QA patch (not official RC)
- Accurate Oracle hints use actual per-player SKY/SEA/EMBER/STAR discovery attributes. Completed 4/4 gives truthful celebration, not a fictitious unlock.
- NAVI enemy alerts use existing Game-owned RED/BLUE egg-steal ProximityPrompt.Enabled as a read-only ACTIVE signal. Both egg prompts disabled mid-battle (both eggs carried) temporarily silences the optional warning; fail closed is safer than lobbying false alarms. Studio battle-phase verification remains necessary.
- Manual LOS: max 6 raycasts and 12 eligible opponents. Automatic alert scan: rotating observer start each 8-second pass, shared maximum 24 raycasts. An incomplete scan never clears a previous alert or generates a benign "no danger" greeting; NAVI prompts skip cooldown and are rate-limited to one scan attempt per 3 seconds. No new Game/Remote/Store authority.
- Source and Rojo CI is not real Roblox 2client/Android/FUN QA.

## Latest PREP build and sole-writer integration
1. PREP branch inherited official RC65 without dropping any official features. Rebase again only if HEAD advances; never use old PREP CI on new base.
2. PREP-only `apply_talking_npc.py` installs three source-locked scripts, one StarterPlayerScripts client mapping, and ServerStorage opt-in attribute **in a copied distribution**. It does not write the canonical RC. #220 must inspect this exact source for admission.
3. Runtime requires a true attribute P0D_RC_ENABLE_TALKING_NPC_V1 and Studio; absent/false disables it. During private Studio hot toggles, the server removes/recreates preview NPCs and publishes a replicated UI enable flag. PREP's private build sets true to permit future Studio trial; no public enablement authorized.
4. Previous pre-review preview PASS (head `06ecb7ea970dc6ebb92b02d2fde81fbdc83cd67d`): 68/68 exact Rojo scripts, 3/3 Luau compile, predecessor OFF byte-preservation; Place 617,122 bytes; candidate ZIP 174,057 bytes. CI https://github.com/kk051780/toy-wars-factory/actions/runs/43539140466. Sourcery found 13 medium issues on initial review; fixes are in progress and require fresh review and same-HEAD CI before marking PREP_READY.
5. Studio 2 clients: a RED observer must never learn an unseen BLUE player's position; direct LOS should announce only observer's area. Confirm that prompts require distance/team/alive checks and throttle; 4 NPCs present and float without collision; 25+ conversations do not flood audio. On Android verify voice toggle/subtitles.
6. Test hidden realm clue gating (0/1/3 stamps), star bridge only when actually open, TTS failure -> caption, feature disabled -> no NPC changes, no reward/XP/save differences.

**Release safety:** The prior PREP preview had CI success but Sourcery approval remains blocked. PR reverted to DRAFT while 13 findings are addressed; not adopted to canonical RC. Roblox Studio/Android/TTS playback/FUN are NOT_TESTED; no production permission. Text is authored deterministic dialogue; no generative AI and no Restricted 18+ free-form chat. 100% original P0D character names and visuals.

Reference: https://create.roblox.com/docs/reference/engine/classes/AudioTextToSpeech

Latest remediation: head/egg announcement, private automatic enemy alert, no stale completed-shard advice, per-NPC cooldown, hot-toggle teardown/restart, conditional HUD visibility, serial TTS load+instance cleanup, immutable transactional preview directory, and explicit enabled Realm Hunt prerequisite. These fixes are **SOURCE ONLY until exact-head CI/Sourcery re-review**.
