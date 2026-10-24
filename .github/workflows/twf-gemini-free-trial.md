---
on:
  push:
    branches:
      - main
    paths:
      - 'ops/GEMINI_TRIAL_APPROVED_FUTURE.json'
engine:
  id: gemini
  model: gemini-2.5-flash
max-ai-credits: 10
max-daily-ai-credits: 10
max-turns: 12
timeout-minutes: 12
permissions:
  contents: read
  issues: read
  pull-requests: read
safe-outputs:
  create-pull-request:
    title-prefix: '[TWF Gemini trial] '
    draft: true
    max: 1
    allowed-files:
      - 'src/**'
      - 'tests/**'
      - 'studio/**'
      - 'evidence/**'
      - 'docs/EXPERIMENT_LOG.md'
    protected-files: blocked
  create-issue:
    title-prefix: '[TWF Gemini blocked] '
    max: 1
  threat-detection:
    engine: false
    continue-on-error: false
    steps:
      - uses: actions/checkout@v4
      - name: Independent static and Gemini API security check
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python3 tools/gemini_patch_gate.py --online
---

# TOY WARS FACTORY — Gemini Free-tier candidate (NOT AUTHORIZED TO RUN)

This is a **disabled one-shot candidate** until the owner explicitly approves a new model invocation and creates the required secret. No 20-minute automated AI coding or billing is authorized.

Before acting, read AGENTS.md, PROJECT_STATE.json, status/CHAT_HANDOFF.md, config/quality_policy.json, config/characters.json, docs/PRODUCT_VISION.md, recent GitHub Actions runs, open issues and PRs. Preserve all verified work.

Choose **one small PvE gameplay or regression improvement**, implement changes only in allowed game/test paths, run existing native Lua and independent Python tests, add one regression for the changed behavior, report precise files/size delta and character-impact audit. Never weaken tests or modify security/workflow/owner authorization files. Do not claim that offline Lua tests prove Roblox Studio multiplayer or mobile behavior.

Produce at most one DRAFT PR with a clear test log or explain BLOCKED with evidence. The reviewer must approve before merging. Do not publish to Roblox, start a paid service, modify secrets, widen access, or activate recurring development.

Free tier request/quota limits may stop the run; treat 429 or missing secret as BLOCKED and fail closed. Built-in gh-aw threat-detect does not support Gemini, so this prototype runs a **separate fail-closed static+Gemini patch scanner** before safe outputs. This is custom defense-in-depth, NOT official gh-aw detector equivalence. No real PR or source upload is authorized until the owner accepts this difference. Google may use free-tier prompts/responses for service improvement; do not include secrets, production user data or personally identifiable information. Owner's private source code is provided to the API only after owner approval.
