---
on:
  push:
    branches:
      - main
    paths:
      - 'ops/ONE_SHOT_APPROVED_20261024.json'
# Guardrails; these caps are not approval to spend money.
max-ai-credits: 25
max-daily-ai-credits: 25
max-turns: 20
timeout-minutes: 16
permissions:
  contents: read
  issues: read
  pull-requests: read
safe-outputs:
  create-pull-request:
    title-prefix: '[TWF autonomous] '
    draft: true
    max: 1
    allowed-files:
      - 'src/**'
      - 'tests/**'
      - 'studio/**'
      - 'evidence/**'
      - 'docs/EXPERIMENT_LOG.md'
    protected-files: blocked
  threat-detection:
    max-ai-credits: 25
    continue-on-error: false
  create-issue:
    title-prefix: '[TWF blocked] '
    max: 1
---

# TOY WARS FACTORY — SINGLE APPROVED AI DEVELOPMENT TRIAL (2026-10-24)

Read AGENTS.md, PROJECT_STATE.json, config/characters.json, config/quality_policy.json, docs/PRODUCT_VISION.md and recent change history before changes. You are an implementation worker, **not** the game's publisher or its owner. Avoid editing governance, workflows, credentials, secrets, GitHub settings, funding or payment configuration.

Work within approved task scope: identify a meaningful incremental improvement that preserves previous features, write well-structured source files with deterministic tests, and run all available repository quality commands. Read existing tests first. If a reproducible defect is discovered, add a failing test, fix it, run again and record root cause and prevention. Do not silence, weaken or delete tests to create a false PASS.

Never claim the Roblox Studio runtime, game visuals, multiplayer, mobile performance, retention or fun has been verified without actual engine/visual/user evidence. Current repository is being bootstrapped, and the full PvE server/HUD/installer migration must be completed before asserting a complete game. If required files or connected tools are missing, create an issue and report the limitation instead of implementing imaginary behavior.

Preserve progress; report precise file changes, before/after source size, relevant character roles and appearance, verified QA logs, unresolved risks and next task. Study popular Roblox gameplay mechanics for their **general design patterns**, without copying exact characters, graphical assets, names, audio or proprietary code.

Only propose validated game code and draft PRs; never merge, release, monetize, escalate scopes, disable QA or edit branch protections.

Before writing any code, check recent PRs and Actions. If an earlier autonomous PR is still pending review, or if the backlog has no small verifiable item, stop without producing duplicate changes. Prefer a tiny patch plus reproducible regression test over large unreviewed work. Every PR description must include the exact testing and source-size delta, character audit, and a link to the issue or backlog item. Save discoveries to docs/EXPERIMENT_LOG.md only when backed by evidence. If there is no authenticated model or budget, stop and report a clear BLOCKED_AGENT_NOT_AUTHENTICATED status.


## This run's one task (strictly one execution, no scheduled repeat)
On the authorized push marker, implement **one small, meaningful gameplay or regression improvement** on the current PvE vertical slice; choose a demonstrable bug or a small feature with independent tests. Ensure existing native Lua 37-case + 4,000-stress tests and Python policy/character gate still pass; do not claim the Roblox engine was tested. Produce a **draft pull request** with exactly the changed file paths, source-size deltas, tests/evidence, gameplay significance, character audit, remaining limitations, and next task. If no safe meaningful change is feasible, produce a truthful BLOCKED record instead of manufacturing a PR.

This workflow is intentionally **NOT scheduled**, and has no workflow_dispatch trigger. It responds only to a single specifically named owner-authorized marker change on main. Any future execution requires another explicit owner authorization. Never modify the trigger path, create a new trigger file, change access settings, or migrate this experiment to the 20-minute recurring worker.
