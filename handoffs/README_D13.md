# D13 Siege Response Director — encrypted ChatGPT reference handoff

Game: `TRAP_RAIDERS` / work: `p0d-siege-v19` / packet: `P0D-D13-SIEGE-RESPONSE-20261110-A`. 2026-11-10 JST.

This delivery is a **pure reference decision module**, not a fully implemented NPC AI, and not a validated Studio game. Existing PC candidate v37/v39 takes precedence. No automatic deployment is authorized by this README.

- Encrypted envelope: `handoffs/TRAP_RAIDERS_D13_encrypted.json` (`P0D_AES256_GCM_HANDOFF_V1`).
- Restored ZIP SHA256: `2caba203e55acf1afff12da90ac4dc4de64fcf8e4bafaded4ce8134f90f80ccb`; bytes: `9183`.
- Manifest SHA256: `75438b4f799a343549ab8112888ac38ba11e05aac3ecf4fdd4d8408dec78b8bf`; source files listed: 8 (plus BUILD_MANIFEST.json).
- Encrypted JSON SHA256: `bee5243c1389802a849782d1dc300b5eb10d98ab52d8bcb944b1d57f0243605c`; ciphertext SHA256: `f94cfd650ed599a2d24412e62e215efca13ca141b6862357584dc045901f6576`.
- Offline Python oracle tests: 27/27 PASS; AES-GCM roundtrip/wrong key/tamper and ZIP/manifest integrity: PASS. Roblox Luau parser/Studio/multiclient/mobile/Windows restore: NOT_TESTED.
- PC baseline: UNVERIFIED_PC_LOCAL. Public repo: no plaintext Luau, ZIP or decryption key.

## Owner-driven Windows Codex intake

1. Read [#218](https://github.com/kk051780/toy-wars-factory/issues/218) and [#213](https://github.com/kk051780/toy-wars-factory/issues/213); verify real latest PC CHECKPOINT/RESUME/Place SHA and preserve it. v37 final QA then v39-H1 integration take priority; D13 is queued.
2. **OWNER** supplies this packet's private AES key via private ChatGPT attachment, NOT GitHub, Issues, PR, CI, logs or automation. Key cannot be retrieved from this repository. The envelope alone is deliberately not readable.
3. Download the pinned envelope and pinned audited `restore_handoff_safe.py` from the v43-A restoration-safety branch at commit `d37eec1b653d060ae27568ddcd5f501da9662081`. Use a new, trusted, unshared local directory and require `--expect-work-id p0d-siege-v19 --expect-packet-id P0D-D13-SIEGE-RESPONSE-20261110-A --expect-zip-sha256 2caba203e55acf1afff12da90ac4dc4de64fcf8e4bafaded4ce8134f90f80ccb`; use the tool's current `--help` and its official README for complete CLI arguments. If any check fails, HOLD. Do not use legacy overwrite-prone restore.
4. After restoring, verify ZIP and BUILD_MANIFEST.json, inspect code and run Python oracle tests. Integrate on an isolated unpublished S1 studio only after prerequisites, implementing a server-authenticated adapter and real pathfinding. Server MUST never forward client-claimed gate_damage/line-of-sight/egg events.
5. Test front/flank responses against v37/neutral guard lifecycle with 2client, preserve egg-room and other route defenders; no teleport, NPC spawn or power buff. Record failed paths/stuck behavior/real Studio QA. Save and normally close only the owned Studio PID. Stop before protected Github writer/CAS/main/merge/Roblox publish/paid spend.

## Claimed scope
D13/v38 only: front gate diversion, side-route LoS, egg carrier escape, server-driven guard reassignment intents and bounded state. Excludes D14 vehicle, D15 trap, D16 transformations, D17 commerce and all existing v37 game source. Packet is immutable once pinned. 
