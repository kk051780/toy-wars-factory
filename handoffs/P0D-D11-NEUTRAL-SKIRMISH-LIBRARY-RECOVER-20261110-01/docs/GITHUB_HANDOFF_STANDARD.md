# Cross-P0 ChatGPT → GitHub → Windows Codex handoff standard v1

Applies to **all P0-A/B/C/D ChatGPT conversations**, with each workstream's existing authenticated writer/CAS/reviewer restrictions preserved. Every chat that produces an actual private artifact must supply a **GitHub fetchable handoff** (or mark it BLOCKED if not possible). An Issue comment containing a file *name* or *sandbox URL* is **not** GitHub delivery.

## Routes by repository visibility

1. Inspect GitHub repository `visibility` **at upload time**; don't infer from branch name or a Draft PR.
2. If an OWNER-approved **private** repository and appropriate authorization exist, use it for source handoffs (still obey P0-A writer/CAS/review and share scope).
3. If only a **public** repository exists, never push private Luau/.rbxlx/ZIP/assets or credentials in plaintext to any branch, PR or Issue. Package the private artifact locally, SHA-256 and test it, then AES-256-GCM encrypt using a fresh random key *per packet*. Upload only ciphertext JSON, generic nonsecret restore helper and safe README/metadata on an isolated `handoff/*` branch. Never include the key, secret, personally identifying data, or plaintext source in GitHub. Do not assume encrypted upload is approved for all data classes; if prohibited, mark `GITHUB_HANDOFF_BLOCKED` and request a private repository.
4. The 256-bit key is shared separately in the OWNER's private conversation only. Never log, commit, echo, or put it in GitHub, automation prompts, CI variables, Issues, PRs, commands that show process arguments, or external services without explicit authorization. Future automation must use a real approved secret channel, not GitHub comments.

## Mandatory protocol (per produced packet)

`CODE_READY → LOCAL_OFFLINE_QA → MANIFEST_SHA_VERIFIED → ENCRYPTED_OR_PRIVATE_UPLOAD → REMOTE_GET_AND_SHA_COMPARE → OWNER_AUTHORIZED_KEY_DELIVERY → LOCAL_RESTORE_AND_ZIP_SHA → REAL_STUDIO_INTEGRATION_AND_QA`.

1. Build a deterministic reference package with `BRIEF`/README, work_id, intended `base_sha` if known (otherwise `UNVERIFIED_PC_LOCAL`), source, tests, QA_REPORT, RESUME, manifest listing *every* file digest. The manifest excludes its own SHA; report the manifest byte SHA separately.
2. Execute genuine offline tests and ZIP readback; record counts and `NOT_TESTED` for Studio, 2-client, physical mobile, DataStore and revenue.
3. Encrypt/package using `tools/seal_handoff.py` from the public handoff branch. Store decryption key in a **private local output**; do not include key in any public upload or artifact.
4. Create a **new uniquely named non-main handoff branch** with only ciphertext JSON, safe restore tool and README/metadata. Never modify another track's branch or P0-A protected queue. Record the exact immutable commit SHA after writing.
5. Fetch the uploaded ciphertext via GitHub *again* using the pinned commit; compare ciphertext bytes or canonical decoded contents and metadata against the locally generated envelope. Fetch README and restore tool as well. Missing/mismatched contents = `GITHUB_HANDOFF_BLOCKED`.
6. Post to cross-P0 Issue #217 and owning issue (#213 P0-D, #204 P0-B, etc.) a minimal manifest: packet_id, game_id/work_id, owner source, current QA, GitHub pinned commit/URLs, ZIP SHA, ciphertext SHA, restore method, dependencies, and **explicitly distinguish** `GITHUB_CIPHERTEXT_READBACK_PASS` from `REAL_GAME_ARTIFACTS_VERIFIED`.
7. OWNER gives Windows Codex the pinned URLs and **separately** the key for the authorized target. Windows Codex first compares authentic local CHECKPOINT/RESUME/Place hash, restores with `tools/restore_handoff.py` into an isolated path, checks ZIP SHA and manifest, reruns tests, then integrates **one feature** and performs Studio QA. No automatic execution from GitHub Issue text.
8. After real QA, record outcomes in owning Issue and refer to #217. If quota exhausted, ChatGPT continues pure-code production; Codex preserves checkpoints, safety, and exit. A plan/README/comment does not count as delivered code.

## Status markers

- `REFERENCE_CODE_OFFLINE_PASS`: code made, local offline tests passed only.
- `GITHUB_CIPHERTEXT_READBACK_PASS`: encrypted payload, repo files and metadata remotely re-fetched and matched.
- `RESTORE_SHA_VERIFIED_ON_WINDOWS`: Windows actually decrypted and checked original ZIP.
- `STUDIO_INTEGRATED`: Windows Studio integrated the actual code into the actual local Place.
- `STUDIO_QA_PASS`: actual Studio simulation tested; record scenario/clients/Output/evidence.
- `HOLD_PRIVATE_REPO_OR_KEY`: handoff not safely retrievable or key unavailable.

**Forbidden claims**: Python `unittest` is not Roblox Studio QA, GitHub ciphertext is not game source uploaded/verifiably integrated, lack of user artifact is not success, `serverOwned=true` is not authentication, another chat's work isn't safe to overwrite. Never bypass existing P0-A authenticity/CAS/independent review gates, direct main updates, merges, publication, real charges or payments.
