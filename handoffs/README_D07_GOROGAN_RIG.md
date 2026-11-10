# TRAP RAIDERS / D07 Gorogan real rig / navigation / damage *reference* handoff

`game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, `packet_id=P0D-D07-GOROGAN-RIG-NAV-DAMAGE-20261110-03`.

This **separate, sealed source packet** adds original server-owned physical R6-like Gorogan rig, bounded PathfindingService/Humanoid MoveTo navigation, one-frame server attack receipt and the final Humanoid damage boundary. It is an opt-in reference for the already delivered `GoroganServerRuntime` AI and its client-only visual. It does **not** overwrite those or the existing game's true RoundCoordinator/event chooser.

GitHub `toy-wars-factory` is PUBLIC. This handoff contains **AES-256-GCM ciphertext only** and public-safe instructions, not any plaintext game source, ZIP, unpublished Place, copyrighted assets, player records or secret key. Encrypted handoff is transport-only, **not Studio/game acceptance**.

## Exactly what was tested

- New ZIP 24,293 bytes, **19 source/test/doc files plus SHA manifest**.
- Restored ZIP SHA256 `9ceadcf6d2af1361e92683021e3d174da058b5e4aeeda748f90a8f69309e047c`.
- Manifest SHA256 `df0d3ece4181b45415e285dbfe4322520065f85fd91eefe70bfe6316627ef756`.
- Encrypted JSON SHA256 `0fed9bae40380c7342cf449f18ec120129ce352005e6c0a6b9ca1246c257641d`.
- Offline Python unittest **86/86 PASS** (independent policy reference, static Luau contract, ZIP path/manifest, AES tamper/wrong-key). Clean extract re-run **86/86 PASS**. AES-256-GCM roundtrip yields ZIP **byte-for-byte identical**, wrong key rejected.
- **NOT_TESTED:** actual Luau parser/compiler, R6 rig validity/physical locomotion in Studio, terrain/path collision and actual 2-client hits, PC source/Place/manifest, mobile/real devices, studio exit, source merge/release. The positive test results above do **not** imply a functioning boss in the user's game.

## How Windows Codex should receive it

1. **OWNER direct instruction required.** First re-read #218, #213 and #217 plus actual latest PC checkpoint. Preserve latest unpublished Place and source. The priority remains v39 residual saved-place QA and then v43-A neutral S1 minimum Studio QA before introducing D07 boss code.
2. On an OWNER-controlled private Windows directory, download this branch's encrypted `handoffs/TRAP_RAIDERS_D07_GoroganRigNavDamage_encrypted.json` and the **reviewed safe restore** `tools/restore_handoff_safe.py` from immutable `d37eec1b653d060ae27568ddcd5f501da9662081`. Never use an unreviewed generic restore from a moving `main`.
3. Supply the separate private 256-bit key via the `CHAT_CODEX_HANDOFF_KEY` or `P0D_HANDOFF_KEY` environment variable, not command arguments, GitHub, Issue or log. Restore into an owner-only directory with exclusive-create output. Example after downloading both files and reviewing code:

```powershell
py restore_handoff_safe.py TRAP_RAIDERS_D07_GoroganRigNavDamage_encrypted.json --out TRAP_RAIDERS_D07_GoroganRigNavDamage.zip --expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D07-GOROGAN-RIG-NAV-DAMAGE-20261110-03 --expect-zip-sha256 9ceadcf6d2af1361e92683021e3d174da058b5e4aeeda748f90a8f69309e047c
Get-FileHash .\TRAP_RAIDERS_D07_GoroganRigNavDamage.zip -Algorithm SHA256
```

4. Verify ZIP safety and per-file manifest SHA **before extraction** and inspect `docs/CODEX_INTEGRATION.md`. Run `python -m unittest discover -s tests -q`, Luau parse and source review. Then **only after previous v39/v43-A gates**, test one S1 non-production boss rig + true 2s attack telegraph + 1 server-authoritative stomp in private Studio with both teams, obstacles and safezones. Important: `GoroganServerRuntime` requires a reviewed *local* one-frame `STOMP_RESOLVE` receipt-window integration; **do not bypass** `isCanonicalAttackReceipt` with a dummy boolean. Source does not include a second event scheduler.
5. Record separate `WINDOWS_RESTORE`, `LUAU_PARSE`, `STUDIO_INTEGRATED`, `STUDIO_QA`, `STUDIO_CLOSED_VERIFIED`, actual source/place SHA and problems to #213/#218 without publishing source or keys. If NPC fails to move/animate or attack boundary is unsafe, STOP and preserve the last known-good local build.

No `main` write, merge, public release, payment enablement, added spend or P0-A/B/C / existing automation change. Other D07 Ligardo and D14 vehicles are separate parallel chat scopes.
