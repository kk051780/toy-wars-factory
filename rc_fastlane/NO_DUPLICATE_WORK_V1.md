# P0D「作業被りゼロ」統合前予約・衝突検査 V1
OWNER 2026-11-15 / canonical coordination [#218](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6886441650) / sole official integrator [#220](https://github.com/kk051780/toy-wars-factory/issues/220).

## Existing gap
\`tools/p0d_two_lane_queue.py\` selects a latest verified READY candidate by FEATURE_ID. It does **not** stop two chats from independently preparing the same castle/sea/attack fix before READY, nor a renamed feature targeting the same source files. This new guard addresses **pre-work ownership**, in addition to (not instead of) queue selection, source CI, Sourcery and #420.

## Exclusive claim workflow
1. All Chat/Automation roles first look up #218/#219/#220/#364/#420, the latest official RC HEAD and related issues/PRs. Reuse an original implementation instead of creating another equivalent branch/PR.
2. New source work needs an accepted unique claim for \`release + feature_id + canonical resources + actual target file paths\`. Requests in GitHub issue comments **do not equal** grants. Only the authorized #219/#220 coordinator may allocate the unique owner. One owner per feature/resource/file scope; #220 remains the *only* official RC writer.
3. Proposed machine-readable source of truth: \`coord/p0d-work-claims:rc_fastlane/P0D_WORK_CLAIMS.json\`. It starts with **zero granted claims**, intentionally. Existing PRs are a triage/reuse backlog, not free-for-all invitations to remake. This registry is on a **separate coordination branch**, not the official RC. Update with GitHub's Contents API by presenting its current blob SHA (compare-and-swap). Keep an audit trail in #218. Do not grant on the basis of an unauthenticated Chat comment.
4. Each new PR body targeting official RC includes exactly one opt-in manifest:
   \`\`\`
   P0D_CLAIM_V1
   CLAIM_ID: <uniquely granted id>
   CLAIM_OWNER: <authorized owner lane>
   CLAIM_FEATURE_ID: ART_CASTLE
   CLAIM_RESOURCES: ART_CASTLE
   CLAIM_BASE_RC: <current official 40-hex SHA>
   \`\`\`
   Actual PR HEAD, base branch and changed-file list must be fetched from the trusted GitHub API, never from PR prose. The coordinator's grant contains \`claim_id, owner, feature_id, resources, target_paths, state=GRANTED, expires_at\`.
5. \`tools/p0d_work_claim_guard.py\` rejects duplicate active claims even when feature aliases differ; overlapping actual file paths; missing/expired/reassigned claims; changed files/resources outside grant; stale official SHA; missing metadata. Expiry is **not** automatic transfer: preserve source and explicitly hand off \`head/files/QA/blockers\`. Alias groups live in the coordination registry.
6. CI \`.github/workflows/p0d-work-claim-gate.yml\` is read-only; it checks out **trusted** official RC, gets latest remote refs/PR diff and the coordination registry by GitHub API. No branch write, merge, release, Roblox Studio, device control or charge. The guard result is **claim scope only**, not a certificate of good art/source/Android/FUN/OWNER acceptance.
7. The **sole** writer #220 still performs existing authenticated CAS + same-HEAD source exact/independent QA + real Place/ZIP size + ACK. The claim guard must be rechecked immediately before an actual write because the coordination record and official RC head can move after an earlier read. Once integrated, completed feature claims are closed by the coordinator and tied to the final RC SHA. Unassigned or conflicting work is BLOCKED; independent QA of existing original sources remains allowed.

## Old duplicates to retire by reuse, not rewriting
- #366/#368: CASTLE; #369/#370: SEA; #373/#374: MINION visual; #421 FOREST; #406 attack input issue.
- Original author's pinned source wins on evidence and suitability; a newer commit timestamp alone does not usurp ownership.
- P0-B/C work only on final Studio bridge and security handoff, QA reviews only, META reports duplicate flags and HEAD without creating feature source.

## Verification
Test with \`python3 -m unittest discover -s tests -p test_p0d_work_claim_guard.py -v\`. A local clean run covers 16 pass/fail cases: unique grant, aliases, overlapping paths/globs, stale lease, stale base, owner mismatch, duplicate claims, out-of-scope files, malicious paths, separate nonoverlapping work and missing manifest.

**Activation status:** this is an *isolated DRAFT proposal* and the coordination branch is initialized, not an authorized official RC merge. #220 must review/integrate under its existing sole-writer lease, then verify required CI/branch protection before calling the guard enforced. The governance rule in #218 and updated five task prompts are immediately operational; the PR check is not yet a required protected-branch status. main/unauthorized merges/publish/payments/PC actions remain forbidden.
