# P0D TALKING NPC V1 — PREP source candidate

**Origin:** #333 (OWNER proposal); #219 (PRODUCT_DRI); #250 (adoption); #220 (sole canonical RC writer).
**Head:** PR #334 (draft, not READY). BASE_RC recorded in PREP_SOURCE_LOCK.json; canonical RC moves independently.

## Implemented source (not yet mounted in official RC)
- TalkingNPCDirector.luau: deterministic server-authorized Japanese greeting, observed enemy, carried egg, visible star fragments, suspect rumor and unlocked realm hints. Voice IDs 701/702. Shared per-user 30s normal/15s urgent cooldown helper.
- TalkingNPCRuntime.server.luau: four original nonblocking floating 3D NPCs (NAVI x2, MADRON, ORACLE), server proximity validation, existing Game RemoteEvent FireClient (no second Remote), LOS+45-stud private enemy observations, current event checks, opt-in ServerStorage attribute. No rewards, XP, HP, save or new round authority.
- TalkingNPCClient.client.luau: smartphone-safe caption bubble, voice ON/OFF, AudioTextToSpeech with AudioDeviceOutput+Wire; silent subtitle fallback when TTS is not available or throttled.
- PREP_SOURCE_LOCK.json pins all 3 script Git blobs. tests/test_p0d_talking_npc_prep.py provides source-only safety/lock tests.

## Required integration by #220 only
1. Rebase feature on current official RC, preserving existing author source bytes and single Game/Remote/Store.
2. Copy the locked director ModuleScript + runtime ServerScript under the original server collection, and only the client LocalScript under StarterPlayerScripts. Add to Rojo project tree/source locks and feature registry; do not duplicate original Game/Remote.
3. Add a missing/false=OFF ServerStorage boolean attribute P0D_RC_ENABLE_TALKING_NPC_V1; keep OFF until verified, then only explicitly opt in for private Studio test.
4. Build updated .rbxlx with one-HEAD exact source-lock QA, Sourcery review, source-only tests; capture ZIP and Place individual byte sizes, PR head & canonical RC head.
5. Studio 2 clients: a RED observer must never learn an unseen BLUE player's position; direct LOS should announce only observer's area. Confirm that prompts require distance/team/alive checks and throttle; 4 NPCs present and float without collision; 25+ conversations do not flood audio. On Android verify voice toggle/subtitles.
6. Test hidden realm clue gating (0/1/3 stamps), star bridge only when actually open, TTS failure -> caption, feature disabled -> no NPC changes, no reward/XP/save differences.

**Release safety:** Roblox Studio/Android/TTS playback/FUN are NOT_TESTED; no PREP_READY contract, RC adoption or production permission. Text is authored deterministic dialogue; no generative AI and no Restricted 18+ free-form chat. 100% original P0D character names and visuals.

Reference: https://create.roblox.com/docs/reference/engine/classes/AudioTextToSpeech
