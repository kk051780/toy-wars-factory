# TRAP RAIDERS — S1 original FIRST60 FTUE on D07/D08/spatial/lobby composite

**Game** `TRAP_RAIDERS` · **Work** `p0d-siege-v19` · **Date** 2026-11-12 JST  
**Status:** actual keyless game SOURCE composite, both server D07/D08 activation flags OFF; 30 source manifest and 21-unit plan are authored. Native Studio / mobile and real gameplay remain **NOT_TESTED**. No main/RC changes or release authority.

## Real code included in this one standalone Rojo game candidate

- Exact previous 28-file source/project/docs/test S1 full composite, pinned to `9de6496282c7bd4dcea586563f75da71d08d77ec`: one real `Game.server.luau`, D07 physical Gorogan, D08 v40 canonical chooser, corrected owner Host/Binding, server-authenticated local STOMP danger rings, one existing Remote, and lobby-only team rebalance/COUNTDOWN both-team guard.
- Original **unchanged** author FirstMinuteModel `fcdc399bf95b6cd0532691718f5a54e8a4fd84b4` under `candidate/src/shared/FirstMinuteModel.luau`, automatically in existing Rojo `TrapRaidersShared` folder.
- Original **unchanged** author FirstMinuteCoach LocalScript `63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9` under `candidate/src/client/FirstMinuteCoach.client.luau`. Explicitly mapped as `TrapRaidersCoach` in `candidate/default.project.json`, alongside unchanged HUD and D07 local warning. Only consumes existing server `SNAPSHOT` and presents an optional Japanese goal hint during the first minute, carry/score/rematch prompts and hide/help. No remote send or gameplay authority.
- An exact copy of the **original separate FTUE author's source/test/doc packet** at `ftue-original-evidence/`, keeping all 6 Git blobs and the 20-case Python oracle test independently accessible. The original reviewed author source commit is `2efa3315317315d34682c1ecb0d8bbdb2d868aa1`.

### Genuine original source manifest defect recovered

The original standalone FTUE `BUILD_MANIFEST.json` is *not* strict `P0D_PUBLIC_SOURCE_V1` and describes each of its two Luau source files with a **phantom final LF** (+1 byte and therefore wrong SHA256 relative to original Git blobs). For example the original LocalScript Git blob has **3865 bytes**, not its original manifest's 3866; original Model has **5367**, not 5368. If one appends a final `\n` to the exact fetched Git source, the old manifest hashes match, proving the one-byte historical packaging discrepancy. **Do not copy this old standalone source manifest into the playable release.**

The NEW `candidate/BUILD_MANIFEST.json` is instead the canonical 6-root-key `P0D_PUBLIC_SOURCE_V1` with 30 actual source files and exact Git-fetched source bytes; manifest SHA256 `9a46a134f441f0f6e649c0293b052f7c3a60d596d149092ab84014b963c7dcd4`. This digest was independently implemented and SHA-256 test-vectored in JS, with byte-for-byte old canonical manifest serialization reproduced; read-only GitHub CI official Python source verifier is the follow-up confirmation. New Coach actual SHA256 `d01bf2998e9498e196da29b3d74ff942daf468cd87116f7b04765542a8cfac31`; new Model actual SHA256 `ee04f48ac3508c3f5c314510f98fd3507f99b3623feba1c27e403f629853a53e`.

The new actual source plan `SOURCE_PLAN_FTUE.json` has **21** unique project/Luau source units, all pinned to an immutable candidate source Git commit `ed0d79d2eb8ad2dbefcf673b29403d813991d4b0`. Only the existing `s1_game_server` declares [round,event_chooser,damage] authorities. The two new FTUE sources are non-authoritative, the Coach depends on the pure Model.

## CI gates and their truthful status

Three independent read-only GitHub Actions workflows were registered on this isolated branch:

1. `p0d-s1-ftue-d07d08-lobby-source-20261112.yml`: real original S1 Python 80; current composed S1 D07/D08 spatial/lobby+FTUE source tests 70; original lobby author 66; original D07/D08 corrective author 34; original First60 author 20; **target 270 actual unit tests**, plus official 30 SHA source verifier.
2. `p0d-s1-ftue-d07d08-native-luau-20261112.yml`: pinned official `luau-lang/luau` compiler commit `f46d879e28302a430029304f7f6a162aed66f103`; compile **all 20 actual Luau files** (original full game plus two client FTUE modules), one intentionally invalid negative syntax control. Native parser is not Roblox Studio runtime.
3. `p0d-s1-ftue-21-source-assembly-20261112.yml`: actual original Python Chat release assembler on **21** source/project units; verifies byte and SHA256 identities, source plan hash and emits a genuine `CHAT_RC_RECEIPT.json` into temporary CI output.

**Do not mark any of the above PASS without a completed SUCCESS run and readback evidence.** Earlier 28-file composite was already verified at 238/238 Python and 19/19 assembly; those earlier results DO NOT prove this changed 30-file FTUE candidate.

## Integrator adoption checklist

The exclusive #220 `CHAT-INTEGRATOR` must compare latest RC to these **only three new candidate files/changes**: copy `src/shared/FirstMinuteModel.luau`, copy `src/client/FirstMinuteCoach.client.luau`, and insert `TrapRaidersCoach` into existing StarterPlayerScripts Rojo mapping. Never add a second Game Script or Remote. Distinct overlays currently read the same Remote `SNAPSHOT`; client does not send any new commands.

Review actual landscape/mobile panel fit, touch button overlap, timing 12/32/60s, role/score/carry messages, hide/reopen, rematch, stale serial and a first meaningful action in <=60 seconds using real Studio QA. UI first-minute engagement and retention outcomes are NOT measured by offline source tests. Toggle-off/rollback by deleting only the two original files and project mapping.

D07/D08 source game flags remain **false** and the known native WARN/time-to-react, WEATHER10%, lifetime 14s vs17s, match serial>=1024 and other game features require independent acceptance. This source is NOT a publishing or owner-final-approval request. Windows Codex remains reserved for OWNER-directed near-final consolidated Roblox Studio 2-client/mobile/normal exit QA. No protected `main`/`rc/p0d-s1-kids-rc01` writes, merges, Roblox public release, paid operations or edits to P0A/B/C CAS or the 5 existing ChatGPT automations.
