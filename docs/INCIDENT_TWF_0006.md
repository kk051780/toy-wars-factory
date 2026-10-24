# TWF-0006: Gemini one-shot usage control failed (critical)

Date: 2026-10-24 (JST)
Actual GitHub Actions: https://github.com/kk051780/toy-wars-factory/actions/runs/40060119253
Issue: https://github.com/kk051780/toy-wars-factory/issues/16

## Owner authorization vs actual execution

| Item | Approved/configured | Evidence |
|---|---|---|
| Frequency | One run only; no 20-minute AI cron | Unique ops/GEMINI_TRIAL_APPROVED_FUTURE.json trigger, consumed |
| Main AI | Gemini 3.8 Flash | Executed, model authenticated |
| Credits | max-ai-credits:10, max-daily-ai-credits:10 | **33.713 modeled AI Credits logged**, exceeded configuration |
| Turns | 12 | **12/12** consumed; `429 max_runs_exceeded` |
| Duration | 12-minute action limit | Action **timed out** |
| Output | One draft game-code PR max | **No patch/bundle, no game PR** |
| Independent safety | Fail-closed custom static+Gemini review | **FAIL** because no patch; safe outputs skipped |
| Real charges | API Free Tier intended | **UNVERIFIED**: model AIC figure is not a Google bill or GitHub Actions bill |

## Technical observations
- The runner successfully reached the actual Gemini CLI; old Copilot "model not supported" fault no longer blocked the main agent.
- Agent spent its 12 turns reading project metadata and source, checking CLI help, and attempted local native Lua + Python tests only at the end.
- Local test shell step returned `Tool execution denied by policy.` It did **not** execute the claimed QA.
- Agent then retried a terminal `429 max_runs_exceeded` until the 12-minute timeout.
- GH-AW token-usage summary: **417,432 input tokens; 961 output tokens; 272,648 cache-read tokens; 33.713 AIC**. The figure may be recomputed by gh-aw accounting; precise provider billing is not available.
- No patch or bundle files were found. No new game code, no new characters, no AI-generated PR.
- The presence of `max-ai-credits:10` in the workflow source and generated lock is not sufficient proof of a hard cap. The **specific enforcement gap has not been root-caused**.

## Stop rule (highest priority)
**No further AI inference, no re-use of consumed one-shot marker, no 20-minute agent deployment, no automatic merging or publishing until a new owner's explicit consent AND an independently validated enforcement mechanism.** This applies even if a later unrelated QA job passes.

## Remediation plan
1. Inspect gh-aw proxy AIC cap mechanics and token usage semantics against the compiled `GH_AW_MAX_AI_CREDITS` and the proxy request budget. Record reproducible discrepancy without using a paid model call.
2. Move from broad autonomous discovery to a single preselected scoped change with explicit source files, 1-2 quick read steps and the exact regression command. Use deterministic tests run by GitHub Actions after patch, not extra model turns.
3. Preserve fail-closed custom security review and forbid weakened gates. Determine why the test execution shell command was denied under agent policy.
4. Enforce independent provider-side hard request/token/daily quota; otherwise treat the run as **not financially bounded**. A time/turn limit is a backstop, **not** a dollar guarantee.
5. Require code-diff size/characters/test evidence to be checked independently for any generated PR, with no automatic merge. Failures become an incident with regression tests and guardrail improvements.
6. Reconcile actual Gemini Free Tier project billing and GitHub Actions minutes in their authoritative dashboards; don't claim the bill was zero.

## Actual result
Status = `SEVERE_HOLD_AIC_CONFIG_OVERRUN`.
Game source delta 0, gameplay QA changes 0, character changes 0, generated PR 0, Roblox runtime/mobile/multiplayer unverified. This trial generated **infrastructure defect evidence only**.
