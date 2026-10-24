# TWF-0004 — Owner-authorized Copilot trial: unsupported models, no PR

Date: 2026-10-24
GitHub Actions: https://github.com/kk051780/toy-wars-factory/actions/runs/40051896515
Issue: https://github.com/kk051780/toy-wars-factory/issues/8

## Proven outcomes
- The owner expressly approved one single AI coding invocation with a 25 AI Credit main cap; a separate 25 AIC cap was set on threat detection. No recurring AI schedule was enabled.
- gh-aw compiled and produced lock at `.github/workflows/twf-first-approval.lock.yml` and run was triggered only by unique marker `ops/ONE_SHOT_APPROVED_20261024.json`.
- `pre_activation` and `activation` succeeded. Copilot CLI installed and started.
- **Main agent:** auto-selected `claude-sonnet-5.5`; GitHub Copilot reported `400 The requested model is not supported`. The harness stopped without retry. `Changes +0 -0`; no AI-created PR.
- **Independent threat detection:** model alias `detection` resolved to `claude-haiku-5.5` and got the same 400, so fail-closed detection also failed. No safe outputs were applied.
- The job logs say **No token usage data found**, but that is not definitive billing evidence. Actual provider and Actions billing needs independent checking.

## Root cause and corrective action
The linked Copilot token was present and the engine launched, but the models selected by CLI defaults were unsupported for this account/token. A valid stored secret is not proof of usable inference rights.

1. Never auto-pick a model for the next limited-budget trial. Identify the account's actual Copilot plan and permitted models; consider a pinned lower-cost model (`gpt-5-mini` if enabled).
2. Model selection applies to **both** main agent and independent threat detection. Retain fail-closed threat detection and separate 25 AIC cap.
3. The Copilot Free tier can be incompatible with gh-aw inference despite `model: gpt-5-mini`; investigate https://github.com/github/gh-aw/issues/46531 before spending on another attempt.
4. The existing single-use marker must never be modified/reused, and no second inference run may start until the owner explicitly re-approves it.
5. Keep recurring 20-minute agent proposal PR #6 unmerged. Store new candidate and compile/verify lock on a separate branch without inference.
6. Independent QA remains required for every future AI-generated PR and game code.

## Quality and accumulation
Actual Lua source change: 0 files, 0 lines, 0 bytes. Character roster unchanged. Game Studio/cross-client/mobile tests never claimed. A failed trial improves the **development infrastructure** only via failure evidence and prevention, not the game release status.

Status: `BLOCKED_MODEL_NOT_SUPPORTED`. No automatic follow-up invocation authorized.
