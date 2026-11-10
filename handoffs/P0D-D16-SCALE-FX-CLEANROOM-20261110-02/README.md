# TRAP RAIDERS D16 — no-key independent cosmetic scale reference

`game_id=TRAP_RAIDERS` · `work_id=p0d-siege-v19` · `packet_id=P0D-D16-SCALE-FX-CLEANROOM-20261110-02`.

**This is a NEW independent implementation, NOT recovered plaintext from original encrypted D16 `P0D-D16-SCALE-FX-20261110-01`** (historical zip SHA256 `d5df52cd3b2fdf26bca05bc38123ac81d27024c944c4a465d66e3a4e0ad0c7cd`). The owner's Library metadata lists the old unencrypted ZIP, but exact source bytes could not be exported in this chat. Do not treat this as byte-identical migration or replace the old archive.

## Implementation

- `luau/D16ScaleFxCore.luau`: pure server-side cosmetic event state, without Roblox Instance writes or networking. Requires a trusted **server-only** caller which has already verified the one canonical D08 event chooser, match, epoch, time, roster, and authorization. Boolean/event data within the pure core is **not** an authentication boundary.
- `GIANT_ONE`: cosmetic reference scale 1.6 for one current roster member. `MINI_ALL`: cosmetic scale 0.7 for all valid roster members. Both expire after 8 seconds and return immutable-in-intent copied visual DTOs (no actual model scaling).
- Fail-closed round replay check, max 128 rounds held until state recreation by trusted game lifecycle. One event at once, monotonic time guard, deterministic roster ordering, rejection of bad/stale requests. No random/event scheduler, damage, hitbox, avatar physics, DataStore, currency, monetization, or live Roblox effect.
- `tests/`: stdlib Python oracle and negative tests (reference behavioral contract + static Luau policy inspection, **not native Luau execution**).

## Offline test command

After extracting this package into a fresh directory, run `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python -m unittest discover -s tests -q` on Linux/macOS, or in PowerShell `$env:PYTHONPATH = "tests"; py -m unittest discover -s tests -q`. This executes only Python oracle tests; Roblox Luau execution and Studio QA are not covered.

## Windows Codex handoff — ONLY by direct OWNER instruction

Read latest #218, #217, #213 and source/Place CHECKPOINT before integrating. Stage the immutable commit into a **new** isolated worktree. Verify `BUILD_MANIFEST.json` with canonical `p0d_public_pack.py` from governance commit `b519a17a3152613666822b7d9660742f93a739b7`, compare all files, and audit the real code. Compare against original D16 if subsequently recovered and choose **one** implementation only. Do not install this fallback and the old original together. No automatic activation or second event chooser. Native Luau parser, 2-client/phone landscape experience and Studio normal exit have **NOT** been tested.

No main write, PR merge, Roblox production release, player records, secrets, paid services, shared CAS/locks, or modification of five existing Automations.
