# TOY WARS — FREE-FIRST idle audit cadence (PR #12, reconciled 2026-11-06 JST)

## Exact scope of this candidate

This is a **DRAFT, not an applied main change**. PR #12 has been reconciled to accepted main `e5deff4d5681bca4823a3da0f848e01bc089ae6e` without discarding historical PR commits. Only the read-only `.github/workflows/loop-watchdog.yml` schedule is reduced:

- Old cron `7,27,47 * * * *`: three scheduled audit attempts per hour (72/day nominal).
- Candidate cron `7 0,6,12,18 * * *`: four scheduled audit attempts per day.
- Its manual `workflow_dispatch`, `contents: read`, Ubuntu execution, Lua/Python audit and scope disclosure are unchanged.
- `.github/workflows/handoff-sync.yml` is **byte-identical to current accepted main** in this candidate. Its existing push trigger, state generation and schedule are preserved; separate protected PR #181 owns any future privilege split of that workflow.
- `.github/workflows/bootstrap-quality.yml` and all PR/push quality checks, source code, AI inference HOLD and Roblox publish HOLD are unchanged.

The proposed reduction is **68 nominal audit starts per day** for `loop-watchdog`, or 94.4% fewer scheduled *watchdog triggers only*. It does **not** mean 94.4% fewer total Actions jobs, 94.4% fewer executed events, or 94.4% lower bills. GitHub can delay/drop scheduled events and observed runs have already been much sparser than the configured 20-minute crons. A full account usage/remaining-allowance receipt was not available from this connector. Never claim an actual billed saving or zero billed usage based on schedule math.

## Why this supersedes the old two-workflow proposal

The original 2026-10-24 draft reduced both `loop-watchdog.yml` and `handoff-sync.yml`. Its old handoff snapshot cannot safely be replayed over protected [PR #181](https://github.com/kk051780/toy-wars-factory/pull/181), which introduces a separate read-only QA / status-only writer design. Replaying the old snapshot would risk undoing that security work. This reconciliation deliberately leaves the handoff file out of the PR's final diff and rebases the candidate by a normal Git merge ancestry, with no main commit/merge/publish.

Original GitHub audit on 2026-11-05 identified 118 completed scheduled runs between Oct 24 and Nov 05 03:44Z (59 per workflow). A subsequent live schedule query on 2026-11-06 observed 122 records total, most recent watchdog [#42089386208](https://github.com/kk051780/toy-wars-factory/actions/runs/42089386208) and handoff [#42088640006](https://github.com/kk051780/toy-wars-factory/actions/runs/42088640006). These are discrete delivered events, **not** evidence of reliable 20-minute automation or an account invoice. The frequent draft-PR QA runs must remain intact.

## Before accepting this candidate

1. A genuinely separate authorized reviewer must check the exact HEAD, its merge ancestry, all changed paths and hosted CI; this document/author's own test result is not independent approval.
2. Confirm that the reduced watchdog observation frequency (potentially up to six hours when not delayed) is acceptable without sacrificing required PR/push QA or new-chat status freshness.
3. Check current GitHub Actions account metered usage, spending stop controls and pending PR #181 before integration. Do not upgrade GitHub plans, change billing settings, or bypass private-main protection.
4. After a separately authorized integration, run QA on the resulting main. No credentials, AI inference or Roblox test place are touched in this PR.

**Cost:** No paid service or spending setting changes are proposed. **Outcome:** watchdog-only scheduling proposal, still DRAFT and not production autonomous coding.
