# TWF-0005 | Gemini API Free-tier AI runner — owner review candidate

Date 2026-10-24, source repo private: kk051780/toy-wars-factory.

## Why not Copilot Free
- First authorized trial: https://github.com/kk051780/toy-wars-factory/actions/runs/40051896515
- Main Copilot auto selected `claude-sonnet-5.5`, threat detector selected `claude-haiku-5.5`, both returned 400 unsupported.
- GitHub gh-aw issue https://github.com/github/gh-aw/issues/46531 documents the free-tier incompatibility even with pinned model. Do not retry prior owner single-use trigger.
- This is an **engine migration**, not a new game project; keep all code, character/world specs, history, and QA untouched.

## Chosen stack
- GitHub private repo and GitHub Actions (already connected).
- gh-aw `engine: gemini` with explicit `model: gemini-2.5-flash`.
- `GEMINI_API_KEY` from a Google AI Studio **Free Tier** project as GitHub Actions repository secret. No paid billing account to be linked unless owner explicitly authorizes.
- One-shot source: `.github/workflows/twf-gemini-free-trial.md`, generated lock `.lock.yml`.
- No schedule; unique placeholder `ops/GEMINI_TRIAL_APPROVED_FUTURE.json` is **not present** in main. Once owner approves and secret is verified, use a newly approved one-off invocation only.
- Main gate: max 10 AIC, max 10 daily AIC, max 12 turns, timeout 12min. AIC is a model-independent limiter, not a guaranteed dollar bill cap.
- Draft PR only, changes restricted to allowed game/test assets; independent native Lua + Python CI must pass before merging. Roblox Studio unverified.

## Independent security review
The built-in gh-aw threat-detect tool supports Copilot, Claude, Codex — **not Gemini**.
- This candidate sets `threat-detection.engine: false` and instead uses a **custom fail-closed** step.
- Offline static scan: `tools/gemini_patch_gate.py` validates patch paths, blocks obvious credential material, binary diffs and commands executing remote content.
- Independent Gemini API review of the generated patch is required to pass; same provider, separate prompt and job. Reject missing API key, broken JSON, false verdict, API errors, quota exhaustion, and uncertain results.
- Security verdict is written to the framework's expected `detection_result.json` only after BOTH checks pass. The test suite validates the fail-closed logic.
- This is **not functionally identical to GitHub's official AI detector**. AI review can still miss threats. All agent PRs stay DRAFT pending independent human/owner release approval; never auto merge.
- If policy requires official AI detector strictly, use a paid supported provider or keep AI generation disabled; never silently downgrade a security requirement.

## Financial limits and operational schedule
- Google Gemini API Free Tier has limited requests/tokens and, under its published terms, Google may use inputs/outputs to improve services. Owner must accept uploading this private game source to Google before inference.
- Ensure Google AI Studio project shows Free Tier with no linked billing account; a Google AI Studio subscription is not the same as Gemini Developer API key billing.
- GitHub Free private GitHub Actions quota advertised: 2,000 included runner-minutes/month (can change by account/runner), and extra usage may be billed or blocked depending on billing settings.
- Two existing 20-minute *QA-only* workflows each produce 72 executions/day, combined about 4,320/month; this may consume free minutes even with no AI. Recommendation: slow idle audits to 4 times/day each, retain on-push QA and run AI work initially 1 time/day, expanding only after actual resource/quality measurement.
- Low/no cost cannot guarantee 24/7 AI code changes. A realistic free-tier setup should prioritize meaningful work per run, not number of runs. Record actual GitHub Actions usage and API quotas.

## User interaction (Android ChatGPT)
1. Owner reviews official Gemini Free data-usage/privacy terms and explicitly agrees.
2. Owner creates Gemini API key using https://aistudio.google.com/api-keys without entering billing. Keep it secret.
3. Owner saves the key as GitHub repository Actions Secret named `GEMINI_API_KEY` at https://github.com/kk051780/toy-wars-factory/settings/secrets/actions. **Never paste any token in chat.**
4. Assistant triggers a no-inference secret presence check, then requests fresh explicit authorization for one Gemini real-run and provides a total expected cost scenario before activation.
5. Only after actual code PR + CI success should the owner consider a low-frequency recurring AI run with quotas/budget guardrails.

## Status/verification
- Source compiled with official gh-aw: https://github.com/kk051780/toy-wars-factory/actions/runs/40052683592
- Independent Python security tests + quality gate: https://github.com/kk051780/toy-wars-factory/actions/runs/40052824360
- Verified **only compiler/static/offline security tests**, no Gemini API used yet, no autonomous Gemini coding PR, no Roblox engine tests.
- Gemini CLI engine is currently deprecated but still supported; monitor Agy's maturity and independently benchmark before migrating, do not restart project.
