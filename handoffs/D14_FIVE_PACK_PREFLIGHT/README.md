# TRAP RAIDERS / P0-D: D14 five-sealed-packet preflight (PUBLIC SAFE)

- `game_id=TRAP_RAIDERS`, `work_id=p0d-siege-v19`, `packet_id=P0D-D14-FIVE-PACKET-PREFLIGHT-20261110-01`
- Purpose: let OWNER-directed Windows Codex verify **the five original sealed D14 envelopes** and optional ciphertext-only staging **before** keys are used. The other chats own all D14 gameplay code; this is a distinct read-only import-audit tool.
- This code does **not** authenticate Studio gameplay, decrypt AES-GCM, access private keys, install scripts, start Codex or Studio, merge, publish, charge money, or write main. Passing is `SEALED_TRANSPORT_READY_ONLY`.

## Package order

| Step | Role | Fixed commit | Integration order |
|---|---|---|---|
| 1 | `SEATS` | `0bcf39c22c583604d72ccac47d29fc9d87b7e662` | One actual server seating authority |
| 2 | `CART_RAIL` | `2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12` | Server-only cart authored route, no 3D |
| 3 | `VISUAL` | `3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0` | CART/RAFT decorative client renderer |
| 4 | `RAFT` | `027fd926a9d315a84f701086448fa5c1febc6697` | OPTIONAL water navigation, requires genuine S1/S2 map |
| 5 | `RIDER` | `0af53f121b35f2e822c63514112360d220c92227` | OPTIONAL disabled-default rider Weld policy |

**Never use** former D14 cart 3D overlap `cae5691b622045af57674d922a08a96764354412` or older D14 seats v1 `250658457392e016c668de8d3c368499f39714bc`. This preflight rejects them explicitly.

The [public-safe CART three-packet contract QA](https://github.com/kk051780/toy-wars-factory/tree/5b93243006c486faf5bbe8867ce7d2702f0c0917/handoffs/D14_TRIAD_CONTRACT) remains separate; it verifies a normalized synthetic/server-sanitized *event trace*, not the source of any private ZIP.

## OWNER Windows preflight

Within this packet's source directory, using Python >=3.11:

```powershell
python -m unittest discover -s tests -p 'test_p0d_d14_preflight.py' -v
python tools/p0d_d14_preflight.py --manifest d14_packets.json --receipt "C:\private\d14-preflight-receipt.json"
```

The `--receipt` path **must not exist yet**. This fetches the five encrypted JSONs and five READMEs directly from immutable SHA URLs, verifies Git Blob SHA-1, envelope packet ID, expected restored ZIP SHA256 and README consistency, and writes a new receipt (no decryption). **A `0` exit only means ciphertext integrity.** On network failure, stale branch/commit, missing item or hash mismatch it exits `2` without granting integration.

To download encrypted references to an **already-created, empty, owner-only** directory (no key files in it):

```powershell
python tools/p0d_d14_preflight.py --manifest d14_packets.json --stage "C:\private\d14-new-empty-staging"
```

Staging is **opt-in**, refuses non-empty/symlink paths, and writes `SEATS_encrypted.json`, `SEATS_README.md` etc. via exclusive create. The staging directory must have OWNER-controlled filesystem ACLs: this tool does not set those on Windows. No plaintext code, key, `.rbxlx` or archive is written.

## Blockers outside this tool

- OWNER supplies **five separate private keys** through a secure channel (one per encrypted packet); do not upload secrets to GitHub, issues, repository, command-line args, or logs. This tool cannot assert key availability.
- Codex must first check latest real Windows Place/source/QA; the last PC proof on #213 was v43-A S1 scoped QA and correct Studio exit, *not* D14 integration. Another OWNER instruction prioritizes v43-A cold restart / D07 Gorogan work; don't supersede it without OWNER decision.
- Once OWNER decides to integrate D14, restore one encrypted package at a time with the pinned safe AES tool and **per-packet expected ZIP SHA**. Review real Lua module APIs and resolve server event/seat epoch/round semantics, Luau parse, physical rider sync and 2/3-client mobile Studio QA.
- D14 actual Windows restore and Studio tests remain `NOT_TESTED` until real PC reports them. Never claim 5/5 Studio PASS because this preflight passes.

## Evidence

The encrypted JSON and README files were read directly from fixed GitHub commits and their Git Blob SHA1 and envelope `packet_id`+`zip_sha256` were verified for **5/5 pairs** by the GitHub connector. This is independent of the new Python script being run on the OWNER Windows PC; the latter is **NOT_TESTED**. Local synthetic Python unittest **41/41 PASS**, including superseded/stale/replay-friendly ID mixups, malicious paths, wrong ZIP, tampering, nonempty output, rollback and key-free staging. Current result: `PUBLIC_SAFE_IMPLEMENTED; PC_NOT_RUN`.
