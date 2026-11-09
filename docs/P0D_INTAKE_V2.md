# P0-D read-only intake v2 — 14 sealed packets + additive D18 design backlog

**Scope:** PUBLIC-safe index and status only, not game source, new gameplay, PC Codex control or Roblox Studio QA. Isolated branch built on the v1 intake branch at `6f680f287463663a05542739e574821b1c1f3b4c`.

## Real GitHub source checks (2026-11-10 JST)

The 12 original packet entries were source-checked by the earlier pinned registry readback. The two newly indexed packets were fetched from their exact immutable commit via GitHub and the ciphertext JSON `packet_id`, `zip_sha256`, and ciphertext/README Git Blob SHA1 were checked:

- D16 glide: `P0D-D16-GLIDE-AUTH-20261110-04` at `c3de5d94eae25e566bdf29452ed1980dae35909d`, ZIP SHA `872e8f9ec5ef38535ee3b295bf301a612e2063835e85cae67ab87bb370aee2cc` (reference permission FSM, **not actual gliding physics**).
- D07 Gorogan: `P0D-D07-GOROGAN-VISUAL-20261110-01` at `5128e288c7bd119a470c253a9792f4d829c569ec`, ZIP SHA `7d6bb8f1cc31348c8461d0b5e0381a62a02eb3aad888be9789fbd78d992ff917` (model + warning *reference*, **not true boss AI or damage**).

Existing D16 has four separate packets; D17 has two. Never treat packet count as a count of completed features. D18 is a new **design-only** collectibles scope and **not** part of the original 17-feature baseline. Another chat delivered a private draft with 648 textual catalog entries, 72 story cards and a public hash manifest at commit `275695238e1278e8fb9e60e82af4b574f2f2dcb6`; the private ZIP was **not uploaded to the public repository**. There are no 648 3D models or playable character assets. D18 increases known scope to 18 but not gameplay-code candidate count.

## Read-only commands (only when OWNER asks Windows Codex)

```powershell
python -m unittest discover -s tests -p 'test_p0d_*audit.py' -v
python -m unittest discover -s tests -p 'test_p0d_progress_rollup.py' -v
python tools/p0d_progress_rollup.py --registry docs/P0D_INTAKE_REGISTRY.json --format markdown
python tools/p0d_progress_rollup.py --registry docs/P0D_INTAKE_REGISTRY.json --format json --output P0D_STATUS_NEW.json
# Optional, requires network; READ ONLY fetch of 28 pinned PUBLIC files, no decrypt/extract:
python tools/p0d_intake_audit.py --registry docs/P0D_INTAKE_REGISTRY.json --verify-remote --output P0D_REMOTE_AUDIT_NEW.json
```

The `--output` flag **refuses to overwrite** existing evidence. The progress rollup itself does **not** contact the network; it summarizes the pinned registry. The optional `--comments` argument accepts a downloaded GitHub issue comments **array**, but reported deliveries are merely *unverified discovery hints* until a person checks immutable artifact bytes. No public issue comment can promote a Windows restore or Roblox Studio PASS.

**Do not copy source ZIPs, private keys, `.rbxlx`, or commercial assets into PUBLIC GitHub.** Real PC progression remains: verify PC latest Place and v37 QA, then only v39-H1 single-packet safe restore and Studio validation. Do not replace newer PC builds with historic SHA. Merge, publication, paid products, and P0-A/B/C locks are outside this handoff.

## Evidence limits

- New progress rollup unit tests: 19/19 PASS offline on this ChatGPT container. Existing intake v1 suite updated to 14-packet assumptions; its actual execution after this update is not independently shown by the 18 new tests.
- No Lua parser or Studio QA was run. Windows restores remain 0/14 **verified by GitHub evidence**, not proof that a PC user has never privately restored.
- This status is a snapshot as of 2026-11-10. A newer GitHub claim or genuine PC result supersedes it after verification.
