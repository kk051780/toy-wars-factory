# Handoff workflow: read-only QA + snapshot-only writer (protected draft)

## Confirmed current deployment state
Accepted main `e5deff4d5681bca4823a3da0f848e01bc089ae6e` still has the old single-job `.github/workflows/handoff-sync.yml` that executes repository tests under `contents: write` and pushes generated status files directly into main. This PR is **not merged/deployed** and is not a production Actions writer proof.

GitHub's private-repository main protection readbacks were refused: `GET /rulesets` returned HTTP403 `Upgrade to GitHub Pro or make this repository public to enable this feature`; `GET /branches/main/protection` returned HTTP403 `Resource not accessible by integration`. The latter is NOT proof that branch protection is absent. GitHub docs document plan limits for private protections. Because provider-enforced main review cannot be authenticated, **do not automatically push status data to main**.

## Proposed least-privilege execution

1. The **verify** job has `contents: read`; check out accepted `github.sha` with `persist-credentials: false`, run original offline Python tests/quality gates and handoff generator, and upload exactly `CHAT_HANDOFF.md`, `LATEST_STATE.json` and a two-entry SHA256 manifest as passive data. Preserve the `13,33,53 * * * *` schedule, main-push and manually dispatched events.
2. The **status_writer** job is main-only and depends on a successful verify. It has `contents: write` but **does not execute source Python**. Using only immutable-pinned GitHub actions and built-in shell/git/jq, it verifies filenames/count, size, symlinks, checksum, schema, canonical repository, HOLD, source SHA syntax and the exact substantive revision derived from the full checked-out main history.
3. It constructs a new Git tree containing **only** `status/CHAT_HANDOFF.md` and `status/LATEST_STATE.json` from the verified files with `git hash-object` / `git mktree` / `git commit-tree`. This tree does not inherit or include the game's source, credentials or executable scripts. It publishes only `refs/heads/twf-handoff-snapshots` via a **non-force** push, never to `refs/heads/main`. The initial snapshot commit is an orphan root; later commits fast-forward the previous snapshot tip if its tree still has exactly the two allowlisted paths. A changed main before push or a concurrent snapshot writer results in rejection (no retry/force). Unchanged contents result in NO_CHANGE.
4. The two files in the snapshots branch are a **generated read model**, not authoritative game source or a substitute for reviewed main code. New chats may read their portable status, but must fetch actual accepted main HEAD/QA/PRs separately. The snapshot branch is not a GitHub merge target. Do not assume `contents: write` is branch-scoped: GitHub's workflow token still has repository contents scope, and our shell logic is not provider-enforced branch isolation.

## Provenance, test stages and active holds

Original 2026-11-02 author Library artifact `/ToyWars/Handoff_LeastPrivilege_TwoJob_24tests_20261102.zip` (SHA256 `013918895ceb4e08c1c6928b30adb1a762e42bc82ada4912e4429c8f6484927b`) supplied the starting **read/write job separation** and had 24/24 local tests. Subsequent commits to protected PR #181 added independent shell/Git and checksum/JSON/source-revision regressions. That original ZIP SHA is NOT a hash of the new snapshot-branch workflow; inspect the current PR's actual head.

Previous original hosted CI evidence: 863 Python tests OK at [Actions #41451340970](https://github.com/kk051780/toy-wars-factory/actions/runs/41451340970), testing the *old candidate with direct main push*. The snapshot-only redesign has separate exact-head checks and is **not** certified by the old run. This design was motivated by the private-main protection API/plan readbacks, not by a witnessed live breach.

**HOLD:** No merge, token scope/policy settings change, private-main protection bypass, privileged workflow dispatch, registered ChatGPT WORKER identity grant, AI spend, Gemini release, Roblox engine test or publication was performed. Requires independent reviewer inspection of source, action SHAs, status contract, current-head CI, branch behavior and GitHub native policy constraints. Snapshot `twf-handoff-snapshots` is deliberately not created in the live private repo by this PR author; it is created only when a reviewed workflow is eventually deployed and actually executes successfully. An Actions test using a local bare Git remote cannot prove GitHub `GITHUB_TOKEN` real write privileges.

Older unrelated draft PRs #12, #19 and #22 also change `handoff-sync.yml`; cherry-pick their intended changes only after source-level conflict review. Source history/characters and established QA/HOLD gates must be preserved.

Original work handoff: <https://github.com/kk051780/toy-wars-factory/issues/57#issuecomment-6572319582>.

## Snapshot reader cutover — protected proposal, not deployed (2026-11-07)

PR181 also updates AGENTS.md, two registered task source prompts and the generated handoff resume instructions. This corrects the documented read-side mismatch but does NOT mean active saved ChatGPT Automations prompts have been updated or executed. Those must be verified separately after review and deployment.

Main remains canonical for code, security, current PR/CI and release holds. Read both `twf-handoff-snapshots/status/CHAT_HANDOFF.md` and `status/LATEST_STATE.json` at one immutable snapshot ref, if available. Validate schema=2, exact canonical_repo, HOLD_ENGINE_UNVERIFIED, 40-hex source_revision. Verify with authenticated GitHub compare that source_revision is identical to, or an ancestor of, current main and the intervening diff contains **only status/** changes. Stale, absent, unavailable or unverified compares mean UNTRUSTED_STALE; use current main/CI/PR directly. Main's generated status is historical fallback only.

The current public-main ruleset #26750913 has PR required, required GitHub Actions App ID 15368 checks offline and compile_hold, required approvals set to 0 by OWNER, no bypass and no force/delete. This does not certify independent code security review. Protected workflow PR remains draft; no source release, scheduled actor write privilege, main merge, extra spending, or Roblox engine test is attested.
