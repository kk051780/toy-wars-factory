# P0-D v43-A restore handoff v2 (generic tool, no private game source)

Scope: TRAP RAIDERS / game_id=TRAP_RAIDERS / work_id=p0d-siege-v19 / owner Issue #213. This isolated branch is based on the previously fixed v43-A encrypted-handoff commit db734240f0157cc125b563656dbd09668226f3ab. No P0-A CAS/controller, P0-B Studio bridge, P0-C Windows receiver, production source, main branch, publication, payments or automation changed.

## Fixed issue
The older tools/restore_handoff.py called output_file.exists() and later output_file.write_bytes(). A file created by another process between those two operations could be overwritten/truncated. Do not use that old restore implementation for new Windows handoff runs.

tools/restore_handoff_safe.py uses OS-level exclusive creation (O_CREAT | O_EXCL, plus O_NOFOLLOW where available). Existing files or symlinks block restoration. An existing private output directory is required. A malicious concurrent replacement of a parent directory remains a limitation: restore only into an owner-controlled, non-shared directory.

Extra checks: immutable caller-pinned ZIP SHA256 and work_id; authenticated AAD containing game_id/work_id/packet_id/ZIP SHA; AES-256-GCM authenticated decrypt; envelope bounds; ZIP CRC, zip-slip, special-files, case-collisions, expansion and count bounds; no extraction or execution; secret comes only from private CHAT_CODEX_HANDOFF_KEY or P0D_HANDOFF_KEY environment variable and is never echoed.

## Previous v43-A immutable artifact
Encrypted file in original GitHub commit:
https://github.com/kk051780/toy-wars-factory/blob/db734240f0157cc125b563656dbd09668226f3ab/handoffs/TRAP_RAIDERS_v43A_encrypted.json

Expected plaintext ZIP SHA256:
a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b

packet_id:
v43A-neutral-skirmish-chatlead-20261110

The private decryption key remains in the OWNER private channel. It is not stored or reissued here.

## Windows Codex manual procedure — after v37 and v39 gates
1. First read the latest authentic local CHECKPOINT, RESUME, QA_REPORT, BUILD_MANIFEST and Place/ZIP SHAs. Preserve the latest v37 local version. Complete final-saved-Place 2/3-client QA and v39-H1 prerequisite checks before considering v43-A game integration.
2. Download the original pinned encrypted JSON and tools/restore_handoff_safe.py from THIS isolated branch at its pinned final commit (recorded in #213). Do not fetch arbitrary movable main.
3. In a newly created private folder that no other process can write, place the JSON and restore script. Supply the existing private v43-A key only through an owner-approved environment variable, never GitHub/Issue/command args/log.
4. Run the following shell command without putting the secret on the command line:

    py restore_handoff_safe.py TRAP_RAIDERS_v43A_encrypted.json --out TRAP_RAIDERS_v43A_ChatLead.zip --expect-game-id TRAP_RAIDERS --expect-work-id p0d-siege-v19 --expect-packet-id v43A-neutral-skirmish-chatlead-20261110 --expect-zip-sha256 a731bea80cdaa69e360d86743d437e19afe27b5e95119d21bf79bfdedd4bdd8b

5. Check the ZIP SHA independently with Get-FileHash, then verify all manifest paths/sha with the ZIP's bundled verify_packet.py BEFORE extraction; do not execute any untrusted ZIP files. Wrong key, missing key, invalid SHA, suspicious path, existing output or unavailable directory means HOLD.
6. Only after independent read/review may Codex test ONE v43-A S1 neutral skirmish feature in a backed-up, private nonproduction Place. Verify server-owned match context, contested capture, 8s lease/4s cooldown, team caps, egg-carrier/dead-player rejection, cleanup, 2/3-client QA and existing four maps/7 classes unaffected. Do not claim these were tested by this GitHub transport-only repair. Stop/Exit only Studio instances Codex opened; log PID disappearance and SHA.
7. Status separate: GENERIC_RESTORE_TOOL_OFFLINE_31_PASS; GITHUB_REMOTE_TOOL_SHA_MATCH (after GitHub readback); WINDOWS_PRIVATE_KEY_RESTORE_NOT_TESTED; STUDIO_NOT_TESTED; SOURCE_REVIEW_PENDING. No main write, merge, unapproved sharing of plaintext game source, Robux monetization, public release or extra spend.

## Tests
Run: python -m unittest discover -s tests -p 'test_*.py' -q

31 synthetic offline tests passed locally (Python + cryptography). Includes existing output, symlink, wrong key/identity, AAD tampering, malformed JSON, ZIP slip, zip bomb, case-collision, archive special file and boundary checks. Windows, actual private payload restoration, Lua/Studio/mobile, CI and independent review have not been performed.

This is generic safe tool code that can be publicly reviewed. It is not the game source or a new game feature.