# P0D AUTO_QUEUE_BALANCE_V1 (isolated PREP candidate)

Owner goal: the moment verified RC intake READY inventory gets low, A must prepare more playable features while B keeps adopting the latest accepted candidates. This is a **read-only planning aid**, not an alternative writer, and does not merge or modify the official RC.

## State machine

| True READY inventory | State | Target A PREP : B integration | A suggested distinct features |
|---|---|---|---|
| 0 | QUEUE_RED | 70:30 | up to 2 |
| 1 | QUEUE_LOW | 60:40 | up to 2 |
| 2–3 | QUEUE_BALANCED | 50:50 | up to 1 |
| 4+ | QUEUE_STOCKED | 30:70 | up to 1 |

The targets are a suggested WIP budget, **not a command to launch additional automations, ChatGPT conversations, Codex, or GitHub writers**. Actual A has one existing hourly WORKER, B one hourly META, and #220 remains the only authenticated CAS RC writer. Studio 2client, Android and owner FUN never inherit CI PASS.

## Procedure / how to run after sole writer reviews candidate code

1. Generate current read-only inbox using the trusted current official script `tools/p0d_two_lane_queue.py`. It rejects stale base/HEAD, drafts, duplicate FEATURE_IDs, or latest non-green full RC CI. The output is `P0D_PREP_INBOX.json`.
2. Read the same official source's `rc_fastlane/FEATURE_CATALOG.json`, **not** a mutable feature-PR supplied catalogue. Catalog's `verified_rc_head` metadata can lag the true Git ref; do not use that historical metadata as current HEAD.
3. Gather a small external `CLAIMS.json` array of genuinely in-progress FEATURE_IDs from #219/#250/PR heads, if verified. An absent claims file is **not** a verified claim-free universe. Always check GitHub active authors before initiating any feature write.
4. Run:
   ```bash
   python3 -B tools/p0d_queue_balance.py \
     --queue P0D_PREP_INBOX.json \
     --catalog rc_fastlane/FEATURE_CATALOG.json \
     --claims CLAIMS.json \
     --out P0D_BALANCE_PLAN.json
   python3 -m unittest discover -s tests -p test_p0d_queue_balance.py -v
   ```
5. A chooses one not-already-claimed SOURCE item (not merely a new IDEA), implements actual Luau/3D/rollback and exact-HEAD QA under its own valid feature-branch permissions, updates latest PR head and obtains READY contract. B cross-checks the current official HEAD **again** before authenticated CAS intake and re-queues all other candidates against the new base.
6. OWNER P0 exceptions: #340 combat HUD and #341 solo Studio start must be checked in the **actual latest official RC**; source fixes have been adopted at official `b151a6f38f0fb7127b506ef993a3bdf1918c823e`, but there is **no proven Studio/Android FUN pass** yet. Reopen a code fix only when new real evidence demonstrates a remaining defect. Do not duplicate PR #342/#346.

## Output and exclusions

Result contains `QUEUE_STATE`, stage counts, `a_suggested_feature_ids`, `b_ready_prs` and role targets with proof-adjacent immutable SHA. It never marks its A target complete, never changes a source or registration, and never labels a DRAFT or old-head candidate READY. A/B report actual source/CI, adoption, ZIP bytes, Studio Place bytes, and unresolved FUN separately. Severe Sourcery findings require genuine new-head review and must not be bypassed.

Status of this branch: **separate DRAFT proposal, no official RC adoption; CI and engine verification pending**. Main, Roblox publication, payments, automated merge and extra cloud costs are out of scope.

## V1 event + artifact acceptance (after authorized RC adoption)
- Every official `rc/p0d-s1-kids-rc01` push recomputes the plan; no `paths` guard may suppress gameplay-only updates to the official RC HEAD.
- Each RC-target PR `opened/synchronize/reopened/ready_for_review/edited` triggers the same **trusted official branch** read-only checkout, never PR-supplied executable code. Manual dispatch also works.
- The runner always executes both selector and balancer tests (under the canonical checkout) and stores **both** `P0D_PREP_INBOX.json` and `P0D_BALANCE_PLAN.json` under the one seven-day `P0D-TWO-LANE-PREP-INBOX` Actions artifact.
- ZERO job write scopes: `permissions: contents:read, actions:read, pull-requests:read`. Suggestions from the balance JSON must not be treated as a legitimate author claim, source production, preview validation, or sole-writer RC approval.
- Preserve the queue's current rule requiring the latest success on the actual HEAD. If P0/P1 Sourcery reviews are outstanding, the B writer still rejects adoption even if selector emits a candidate.

## Fail-closed rollout on RC-target PR events before adoption
A PR can carry the *future* workflow before the official RC has the balancer script. GitHub runs that workflow with `checkout ref: rc/p0d-s1-kids-rc01` for safety. If the trusted checkout lacks either script or tests, the balance step logs `P0D_BALANCE_NOT_YET_ADOPTED_IN_TRUSTED_RC` and succeeds **without running PR code**; the original verified queue JSON still uploads. Once #220 legitimately admits both trusted files into the official RC, no manual switch is needed: ordinary RC pushes and PR updates generate both JSONs. The artifact upload uses `if: always()` so a failed balance test cannot hide a previously valid queue snapshot.
