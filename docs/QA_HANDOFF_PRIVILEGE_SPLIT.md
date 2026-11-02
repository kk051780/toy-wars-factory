# Handoff workflow: least-privilege split (protected candidate)

Current accepted main `e5deff4d5681bca4823a3da0f848e01bc089ae6e` has a one-job `handoff-sync.yml` with `contents: write`, mutable `actions/checkout@v4` and persisted credentials while executing repository tests. This proposal only changes the handoff workflow to split that blast radius; no GitHub settings or main files are modified before review.

## Proposed boundaries

1. `verify` has `contents: read`. Checkout with `persist-credentials: false`, run existing Python tests, repository gate, portable handoff generator and summary, then upload the **two named status files** and a SHA256 manifest as passive data. The same 20-minute cron and push/manual triggers are preserved.
2. `status_writer` requires a successful `verify` and runs only for `refs/heads/main`. It has `contents: write`, no repository Python execution, an immutable checkout, a same-run artifact download, explicit three-file/size/symlink/hash validation and exact two-status-file staging. GitHub credentials are explicitly used only in the final push step, with a latest-main SHA check and one no-retry push.
3. Four marketplace actions are pinned to full SHA refs. This is still GitHub-hosted code: its job token and publisher actions require independent audit; do not call it absolute token secrecy.

## Evidence and limitations

This is an adoption of the **existing prepared owner Library candidate**, not a second implementation: `/ToyWars/Handoff_LeastPrivilege_TwoJob_24tests_20261102.zip`, SHA256 `013918895ceb4e08c1c6928b30adb1a762e42bc82ada4912e4429c8f6484927b`. The candidate itself was locally re-run with **24/24 tests successful** (real temporary bare Git remote and artifact adversarial controls). The branch workflow Git blob matches its exact prepared candidate: `4ca9b5a00a1a0c8ada5b6d3637437dd65723bee0`. Hosted regression tests are in `tests/test_handoff_privilege_split.py` and require actual exact-head GitHub Actions evidence.

This candidate does **not** prove production handoff success: its rewritten workflow is only in a protected draft branch, not installed on accepted main. Green regular PR CI only tests the source; it does not dispatch the new writer or prove live permissions. Private-main provider branch protection is not attested and might reject direct status pushes. Once a true provider-required independent review gate is enabled, change the status writer to a reviewed status-branch/PR strategy instead of bypassing protection. No ChatGPT WORKER run identity or GitHub Pro setup is supplied here.

Non-overlapping purpose with older unrelated open drafts #12 (cron budget), #19 (shallow history) and #22 (Gemini budget), though those PRs also edit this same file. **Do not blindly merge** their old source paths over this candidate; review exact main→head diffs and conflicts. This is not an auto-AI writer, Gemini inference or Roblox testing/publishing.

Original work handoff: <https://github.com/kk051780/toy-wars-factory/issues/57#issuecomment-6572319582>.
