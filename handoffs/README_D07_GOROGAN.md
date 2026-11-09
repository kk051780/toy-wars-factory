# P0-D D07: S1/S3 Gorogan 3D Visual (Encrypted Handoff)

**Packet:** `P0D-D07-GOROGAN-VISUAL-20261110-01`
**Game:** `TRAP_RAIDERS` • **work_id:** `p0d-siege-v19`
**Status:** Standalone reference source and Python static/policy tests, **NOT game-integrated or Studio-tested**.

## Delivery

- Encrypted payload: `TRAP_RAIDERS_D07_Gorogan_encrypted.json` on this pinned `handoff/*` commit.
- Restored ZIP SHA256: `7d6bb8f1cc31348c8461d0b5e0381a62a02eb3aad888be9789fbd78d992ff917`
- Manifest SHA256: `d230d4926905a6e15666eae22422fae8a05ab80bf85f387e524dce520cb62fd0`
- Encrypted JSON SHA256 (exact original bytes including newline): `fb64f3f937d4da72e88abe17a79185e5d0aab6a282c4ab1609b210fb403367d0`
- AES-GCM ciphertext SHA256: `2f68fb515fd05e92e0f76a0a61f77826b64841bd7e91c8a798499adb2ac9607d`
- File count: 17 listed source/test/doc/tools entries + `BUILD_MANIFEST.json` = 18 files, 21,088 ZIP bytes.
- Offline Python: **84/84 PASS**, seeded 4000-event property sequence, wrong-key/tamper/ZIP traversal rejection. Luau VM/Roblox Studio/mobile **NOT_TESTED**.

## Scope

Gorogan S1/S3 client-only original low-poly humanoid giant from anchored no-collide/no-query/no-touch Roblox Parts: moss, left/right boulders, glow core, 2s warning ring, max 3 STOMP visual cues, local TTL <=14 seconds, reduced motion and low-detail. Does **not** spawn/attack as NPC, implement real boss AI/damage, change egg/victory, schedule bosses, animate Dragon Raigald or offer any actual purchase.

## Restore into an isolated Windows folder

1. Download the encrypted JSON from this pinned GitHub commit; obtain the AES256-GCM key **privately from OWNER**, never from GitHub. Never commit/print the key.
2. Use the independently reviewed and immutable [safe restore tool](https://github.com/kk051780/toy-wars-factory/blob/d37eec1b653d060ae27568ddcd5f501da9662081/tools/restore_handoff_safe.py) (`cryptography` dependency, free) and a new secure output folder. For that script:

```text
py restore_handoff_safe.py TRAP_RAIDERS_D07_Gorogan_encrypted.json --out TRAP_RAIDERS_D07_GoroganVisual.zip --expect-zip-sha256 7d6bb8f1cc31348c8461d0b5e0381a62a02eb3aad888be9789fbd78d992ff917 --expect-work-id p0d-siege-v19 --expect-packet-id P0D-D07-GOROGAN-VISUAL-20261110-01
```

Use environment variable `CHAT_CODEX_HANDOFF_KEY` or `P0D_HANDOFF_KEY` only within the private Windows Codex process. Never upload key in scripts, GitHub Issue, CI or logs. `restore_handoff_safe.py` has not yet been formally certified by the P0-A security reviewer; verify independently and keep isolation.

3. Verify ZIP SHA and manifest via extracted `tools/verify_packet.py`, then run `py -m unittest discover -s tests -q` from the *isolated* extracted packet. Run Luau parse/Roblox Studio testing separately.
4. **Do not integrate now without the PC gate:** actual saved v37 final 2/3client QA, then v39 server reward integration. When the OWNER authorizes, use one server-authenticated external `ChaosEventCore` boss event; don't add a new scheduler. Existing `BOSS_GOROGAN` must be mapped to visual `GOROGAN` by the genuine server adapter, not by client self-report.
5. Test in a **private unpublished Studio duplicate Place**, including both clients, S1/S3 placement, FPS & reduced-motion, QA/clean Studio exit. No public game source/Place pushed, no main changes, merges, publishing, Robux/real purchases, additional spending.

## Access & audit

PUBLIC repository is intentionally storing only the ciphertext + this sanitized metadata. The plaintext commercial Luau/ZIP/.rbxlx and decryption key are **not** publicly stored. GitHub remote readback is proof of distribution only, NOT proof of source review or Roblox Studio QA. Other ChatGPT chats must check #218 feature claims to avoid writing a parallel D07 visual prefab.
