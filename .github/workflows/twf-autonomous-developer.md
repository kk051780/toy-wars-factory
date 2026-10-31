---
on:
  workflow_dispatch:
network: defaults
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
  create-issue:
    title-prefix: '[TWF blocked] '
    max: 1
---

# TOY WARS FACTORY — unattended game development (compilation candidate)

Read AGENTS.md, PROJECT_STATE.json, config/characters.json, config/quality_policy.json, docs/PRODUCT_VISION.md and recent change history before changes. You are an implementation worker, **not** the game's publisher or its owner. Avoid editing governance, workflows, credentials, secrets, GitHub settings, funding or payment configuration.

Work within approved task scope: identify a meaningful incremental improvement that preserves previous features, write well-structured source files with deterministic tests, and run all available repository quality commands. Read existing tests first. If a reproducible defect is discovered, add a failing test, fix it, run again and record root cause and prevention. Do not silence, weaken or delete tests to create a false PASS.

Never claim the Roblox Studio runtime, game visuals, multiplayer, mobile performance, retention or fun has been verified without actual engine/visual/user evidence. Current repository is being bootstrapped, and the full PvE server/HUD/installer migration must be completed before asserting a complete game. If required files or connected tools are missing, create an issue and report the limitation instead of implementing imaginary behavior.

Preserve progress; report precise file changes, before/after source size, relevant character roles and appearance, verified QA logs, unresolved risks and next task. Study popular Roblox gameplay mechanics for their **general design patterns**, without copying exact characters, graphical assets, names, audio or proprietary code.

Only propose validated game code and draft PRs; never merge, release, monetize, escalate scopes, disable QA or edit branch protections. If there is no authenticated model or budget, stop and report a clear BLOCKED_AGENT_NOT_AUTHENTICATED status.
