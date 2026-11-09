# TRAP RAIDERS P0-D D07 LIGARDO S2/S4 — encrypted server-AI reference handoff

packet_id: `P0D-D07-LIGARDO-SERVER-AI-20261110-04`  
game_id: `TRAP_RAIDERS`  
work_id: `p0d-siege-v19`  
feature_id: `D07`  
origin: independent CHAT-LEAD reference, **not** Windows PC's true latest source

## Content and scope

2 Luau source reference modules (`LigardoServerPolicy.luau`, `LigardoServerAdapter.luau`), independent Python oracle and 90 offline tests plus documentation and SHA manifest. Deterministic S2/S4 boss intent FSM: 16s lifetime, <=3 visible 2s telegraphed lightning attempts, 2.5s cooldown, chase intent limited to 36-stud leash and 10 studs/second with <=0.5s step. Damage only an intent capped at 7 and requiring fresh server LOS/target/boss position plus per-round replay ledger. **Not a playable boss:** no actual NPC rig, PathfindingService, Humanoid:TakeDamage, damage application or Studio integration.

**No overlapping** other-chat Gorogan S1/S3 visual/server AI, existing D07 event singleton, D16 weather/glide, D11 neutral, D13 guards, D14 vehicles, D15 traps, D17 analytics or D18 atlas.

## Integrity and security

- Encrypted PUBLIC-GitHub-safe JSON: `handoffs/TRAP_RAIDERS_D07_LIGARDO_AI_encrypted.json` on its isolated `handoff/p0d-d07-ligardo-ai-20261110-04` branch.
- Original private ZIP: `TRAP_RAIDERS_D07_LIGARDO_SERVER_AI.zip` (17,229 bytes).
- Original restored ZIP SHA256: `0dbfa84325c275a1e010230535bc389ba4606cb872cc400f2d1f97d9411afd2c`.
- Internal `BUILD_MANIFEST.json` SHA256: `52e9b5bde780c5e25db03239b58467d26dde7829df80a9c7565dd531d9d8b17f`.
- Ciphertext AES-256-GCM raw SHA256: `3144ccb2ea71094887f66b6ddc4d59c9315f5b027db2be1993d9f8b27220d022`.
- Ciphertext JSON SHA256: `2a9a3699164d26173cf07cd79f8497ed111fbda41897efda682af93f9d3457ad`.
- Offline Python tests **90/90 PASS**. Original ZIP manifest/bytes validated, wrong key and modified ciphertext rejected.
- PRIVATE KEY is NOT in repository, ciphertext or README. OWNER delivers secret only through private means. Public GitHub issue comments are NOT authorization to run code.

## OWNER-directed Codex recovery (never automatically executed)

1. Re-read #218/#213/#217 and locate real PC latest checkpoint/source/Place SHA. Latest PC reports v39-H1 genuine scoped QA PASS; overall game `PARTIAL_NOT_READY`. Finish remaining v39 saved-Place 2client/real-audio/device/reconnect checks; then evaluate v43-A dependency before this optional boss slice.
2. Obtain **pinned** ciphertext+README from this branch's immutable commit. Use reviewed safe `restore_handoff_safe.py` at `d37eec1b653d060ae27568ddcd5f501da9662081` in a trusted private local output directory. Key in `CHAT_CODEX_HANDOFF_KEY` private process environment only, never log/commit it.
3. Run restore with `--expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D07-LIGARDO-SERVER-AI-20261110-04 --expect-zip-sha256 0dbfa84325c275a1e010230535bc389ba4606cb872cc400f2d1f97d9411afd2c` and a new output ZIP path. Verify SHA and internal manifest paths/hashes before any extraction. If mismatch/key unavailable -> HOLD; never overwrite PC source.
4. Run `python -m unittest discover -s tests -q`, Luau syntax/type check; review actual server team/event literals and one-canonical event chooser. Only then consider adding a **single** S2 server attack adapter. `LIGHTNING_INTENT` only becomes real combat after authoritative position/LOS/round/applier dedupe and physical boss rig are proven in Roblox Studio. S4 after S2 passes.
5. Verify actually real 2client warning/dodge/block LOS/HP, then 3client duplicates, S1/S3 Gorogan unchanged, S1–S4 egg/7jobs/replay/mobile-FPS. Save full Place/source/checkpoint/QA SHA and normal quit of ONLY owned Studio, PID disappearance. Post PASS/FAIL/BLOCKED/NOT_TESTED separately.

**Current evidence:** `OFFLINE_90_PASS`; `ZIP_SHA_PASS`; `CIPHERTEXT_LOCAL_RESTORE_PASS`; `WINDOWS_RESTORE=NOT_TESTED`; `LUAU_PARSE=NOT_TESTED`; `STUDIO_QA=NOT_TESTED`; `STUDIO_CLOSED=NOT_TESTED`; **main/merge/publish/Robux/extra-spend prohibited**.
