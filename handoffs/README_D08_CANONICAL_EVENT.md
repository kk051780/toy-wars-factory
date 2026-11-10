# P0-D D08 — canonical v40 server event bridge (encrypted GitHub handoff)

**game_id:** `TRAP_RAIDERS` · **work_id:** `p0d-siege-v19`  
**packet_id:** `P0D-D08-CANONICAL-EVENT-BRIDGE-20261110-01`  
**status:** `CHAT_REFERENCE_CODE / PY64_PASS / STUDIO_NOT_TESTED / PC_RESTORE_NOT_TESTED`

This folder carries **AES-256-GCM encrypted reference ZIP only**. The public GitHub repository contains no plaintext commercial Luau, Roblox Place, asset or decryption key.

## Exact artifact identity

- Encrypted JSON: `handoffs/TRAP_RAIDERS_D08_CanonicalEventBridge_encrypted.json`
- Restored ZIP: `TRAP_RAIDERS_D08_CanonicalEventBridge.zip` (17,831 bytes)
- Restored ZIP SHA256: `576921a613b8330549b2e8fd89c7fa96e6b9e3d9a26146903072f1bde969058f`
- Inner `BUILD_MANIFEST.json` SHA256: `1ddf6e96ed5a672ce677d05c014484c675c9623157dfb3fdc05dea26b86fd3dd`
- Encrypted JSON SHA256 (terminal newline included): `ec17bb8c282df04138071e9be6975fb34642917f48de61682c2538bddfe81803`
- Ciphertext SHA256: `ce9d39d4aa77a3ead1e0d8e9c3c033c7c59f0b333a4a5912a39b214b8473ee34`
- 12 inner source/test/doc files + manifest; local ZIP/manifest/path/CRC verifier PASS, Python 64/64 PASS on independent extraction.

## How OWNER Windows Codex should receive

1. **Read the latest #218/#213/#217 and the actual PC Place/CHECKPOINT**. The latest confirmed v39 and v43-A game QA is scoped PASS, not whole-game readiness. Do not overwrite newer PC data with old historical SHA.
2. Check that the original [v40 `ChaosEventCore`](https://github.com/kk051780/toy-wars-factory/tree/c0b0bf692410cb651893c38f1a453c93d9f8b3b5/handoffs) was independently restored and SHA-validated. The original Luau core is **not duplicated** in this packet. Its reference module SHA256 is `f6d6901a8dcb61cec1095e383e485950144d39ea43737c9b33d4351a66e88726`.
3. Use the reviewed [safe restoration tool](https://github.com/kk051780/toy-wars-factory/blob/d37eec1b653d060ae27568ddcd5f501da9662081/tools/restore_handoff_safe.py), with **this packet's private AES key supplied by OWNER in private ChatGPT**, never by GitHub, command arguments, logs, Issue or CI. Validate exact packet ID, associated data, ZIP SHA and every inner manifest member. Do not overwrite files on error.
4. Review the new `CanonicalEventBridge.luau` and **disabled-by-default** `CanonicalEventServerAdapter.server.luau`. Run `python -m unittest discover -s tests -q` and the Luau syntax parser before engine integration.
5. **Do not create a second boss/weather event chooser.** Verify the genuine PC RoundCoordinator does not already have another live chooser. Only one real server controls time, match epoch, event RNG, weather runtime and boss activation. The old pure v40 core needs an actual reviewed server hookup; it does not install itself. This packet dispatches its existing one-choice event lifecycle. No client input or RemoteEvent can authorize events.
6. **S2/S4 naming mismatch:** original v40 chooses `RAIGALD`; recent D07 model uses `LIGARDO`. Default BLOCKED until game-spec and PC IDs are reviewed; never silently rename. **Weather** is also disabled without an approved runtime handler (no fake visual-only success).
7. S1 test: one warning, one boss activation, one cleanup; no false replays, server-authoritative 0..99 roll and Match/epoch/round-close checks. Existing D07 Gorogan AI + rig + visual modules need a separate one-slice physical 2/3-client Studio integration. Require real saved-Place cold-reopen, FPS and Studio normal Quit/PID disappearance.

### Explicit exclusions

No new event probability RNG (existing v40: 65% NORMAL, 25% BOSS, 10% WEATHER), no real S2/S4 alias until reviewed, no weather VFX, no attack/AI/rig source, no v43-A source changes, no permanent DataStore, no player identifiers or real purchases. The packet is **not** proof of Luau compilation, Roblox Studio QA or Windows integration. Main merge, game publishing, paid services, P0-A/B/C auth/CAS/independent review changes and additional spend are prohibited.
