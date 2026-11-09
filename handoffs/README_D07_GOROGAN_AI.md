# P0-D D07 Gorogan SERVER-AI isolated handoff

- `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`.
- `packet_id=P0D-D07-GOROGAN-SERVER-AI-20261110-02`.
- Dedicated safe encrypted handoff branch; PUBLIC repository contains **AES-256-GCM sealed JSON and this README only**; no private source files, ZIP, Place, sound asset, token or key.
- Private ZIP name `TRAP_RAIDERS_D07_GoroganServerAI.zip`, **20,043 bytes**, 16 manifest-listed files + `BUILD_MANIFEST.json`.
- Restored ZIP SHA256: `0dc7a15c821eb957e1e2a4f16d10922fd32a576c38544c789cb5bb0b16a41516`.
- Manifest SHA256: `5f928e3eeeb9d42170248ef4cd0341d920f674ee974be504531feb7cd66abe9b`.
- Cipher JSON SHA256: `68696823012f8d15f12844a379af02a129e0f4222c457d5a8d19a9fd3232c8c7`.
- Local AES256-GCM decryption ZIP-byte-exact PASS; wrong-key and tampering negative tests PASS.
- **87/87 Python offline tests PASS** (55 oracle tests, 18 Luau static contract checks, 14 transport/ZIP cryptographic tests). No Luau VM/Roblox Studio/Windows PC/2client/physical mobile tests performed.

## Functional contract

`luau/GoroganServerAICore.luau` is a pure server decision core: 1 boss per round, S1/S3 only; two-sided neutral targeting; 14s max TTL; 2s initial visual-only phase then up to 3 stomps each warned 2s, radius 7 and damage **intended** 8; movement intents ≤8 studs with 42-stud leash. Neither this core nor transport executes live game damage or actual pathfinding.

`luau/GoroganServerRuntime.luau` is an opt-in game-server callback adapter. Requires actual canonical `ChaosEventCore` BOSS/GOROGAN activation, trustworthy match ID/time/team/roster, current server collision/LOS/ground, live rig `MoveTo`/pathfinding, and server-authoritative `Humanoid` damage callbacks. `integrationApproved=true` by itself is **not** origin authentication. No standalone boss RNG or second event scheduler. Existing D07 visual-only pack at immutable commit `5128e288c7bd119a470c253a9792f4d829c569ec` handles optional client-only 3D/telegraph and must remain separate from server collision/HP.

## OWNER Windows Codex restore (never automatically triggered by GitHub Issue)

1. First read P0-D common ledger #218, game QA #213 and P0-A/B/C contract #217. Check **actual PC latest source, Place SHA and CHECKPOINT**. Back up; v37 final SHA multiplayer QA then v39 safe integration remain higher-priority blockers.
2. Download `handoffs/TRAP_RAIDERS_D07_GoroganAI_encrypted.json` from this pinned commit. Download validated **safe restore helper** from `d37eec1b653d060ae27568ddcd5f501da9662081/tools/restore_handoff_safe.py`. Supply decryption key via OWNER's private channel to `CHAT_CODEX_HANDOFF_KEY` in the PC environment, never console/log/Issue/GitHub.
3. Restore with explicit options (use owner-only empty output directory):

```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D07_GoroganAI_encrypted.json --out TRAP_RAIDERS_D07_GoroganServerAI.zip --expect-zip-sha256 0dc7a15c821eb957e1e2a4f16d10922fd32a576c38544c789cb5bb0b16a41516 --expect-work-id p0d-siege-v19 --expect-game-id TRAP_RAIDERS --expect-packet-id P0D-D07-GOROGAN-SERVER-AI-20261110-02
```

4. Verify ZIP manifest SHA before opening modules; run `python -m unittest discover -s tests -q` for OFFLINE tests. Run actual Luau parser/Studio QA in a separate unpublished Place only after prior dependencies pass; DO NOT adopt unreviewed source automatically.
5. S1 only: attach to canonical boss event, physically present actual server NPC rig and navigation, telegraph both teams, validate real player positions/LOS at impact, and test simultaneous client abuse, 3 max attacks, stale match cleanup, phone FPS/Studio exit. S3 only after S1 acceptance.
6. Record actual `WINDOWS_RESTORE`, `LUAU_PARSE`, `STUDIO_QA`, `STUDIO_CLOSED` outcomes separately in #213 and #218. No public plaintext code, no main merge, no production publish, no real purchases, no spend.

**State:** `PYTHON_87_PASS / LOCAL_ZIP_AND_AEAD_VERIFIED / GITHUB_SEALED_DELIVERY (after immutable readback) / WINDOWS_RESTORE_NOT_TESTED / STUDIO_NOT_TESTED`.
