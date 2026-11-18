# GQ8 Core36 post-CAS receipt reconciliation (isolated nonoverlap)

## Observed actual bug
The authenticated B writer #220 adopted Core36 into the formal **private** RC at
`f77b4d4393d9e9b19b65566413432a7a9f13962b` (PR #783) and same-HEAD post-CAS Actions #44232589275
COMPLETED SUCCESS with ZIP artifact 14396515259 / 366128 bytes.
But the accepted formal RC manifests still say **PENDING_CANDIDATE** and
`official_nonforce_expected_sha_cas=false`. These statements are stale
and can cause a false 0% adoption/false pending status.

## Scope and proof
- Only existing `rc_fastlane/ACTIVE.json` and `EGGRUMBLE_V3_CORE36.json`
  **receipt metadata**, an independent Python regression and a QA workflow.
- 36 canonical original-author Luau sources are **unchanged**. No source
  duplication, re-selection, new Game/Host/Combat/HP/Store/Remote, modified
  Roblox Place, default rich51 switch or public publish.
- Source-adoption receipt is **historical**, bound to verified SHA, workflow,
  and ZIP bytes; consumers MUST re-fetch live RC SHA when making a current claim.
- Distinct from PR #790 (first-play source-vs-engine truth), #581 (old RC31
  workflow stale SHA), #787/#780 (cross-lane runtime composers).
- Negative mutations prove the receipt rejects switched primary profile, fake
  Studio acceptance, drifted HEAD, mismatched run, ZIP mislabeled as RBXLX,
  and false publication.

## Exact source evidence
- Official RC: f77b4d4393d9e9b19b65566413432a7a9f13962b
- Older B writer expected-SHA: 261b75d0a7093db5c13db3b95dad9a2911f78689
- Native36/Rojo36/OFF31 + sameHEAD canonical Actions:
  https://github.com/kk051780/toy-wars-factory/actions/runs/44232589275
- Official adoption PR: https://github.com/kk051780/toy-wars-factory/pull/783

**NOT proven:** actual Studio 2-client, low-end Android 15 minutes,
3-minute player FUN, arts quality, native RBXLX single-file size or Roblox Publish.
Do not transform this historical metadata repair into runtime-verified gameplay.

## RC handoff
A (this PR) owns the isolated patch and source-status QA. Only authenticated
B #220 writer can rebase and adopt the metadata into live formal RC using
nonforce expected-SHA CAS, after checking current HEAD and green checks.
No author ACK wait, no main/other PR merge/publish/spend. Rollback: restore
the two manifest JSON blobs at base f77b4d4393d9e9b19b65566413432a7a9f13962b; no gameplay rollback needed.
