# TOY WARS FACTORY | Private autonomous development

> **Status: GitHub is connected; real GitHub offline QA passed.**
> **Not yet running an unattended AI coder. No Roblox Studio/mobile/multiplayer proof.**

This repository is the persistent, source-controlled home for TOY WARS FACTORY, a Roblox toy-factory battle strategy game. Owner controls and final approvals are designed for Android ChatGPT, not PC work.

## What exists today
- Verified original PvE source: server, HUD, common balance rules, Studio smoke test (**all four exact blob hash matches to v1.2 archive**).
- Source-based reproducible Studio Command Bar installer generation and SHA-256 source matching, run in GitHub Actions.
- Native Lua 5.4 gameplay rules: 37 assertions + 4,000 deterministic boundary/stress cases.
- Character definitions, game vision and policy/structure checks.
- Automatic GitHub quality workflow plus a *20-minute QA-only audit* configuration.
- A **compiled-only agent workflow probe**. It only validates generation of a candidate runtime: it does NOT run an AI developer.

**[Latest successful default-branch QA](https://github.com/kk051780/toy-wars-factory/actions/runs/40047378300)** · **[Compile-only proof](https://github.com/kk051780/toy-wars-factory/actions/runs/40047378021)** · **[Bootstrap merged PR](https://github.com/kk051780/toy-wars-factory/pull/1)**

## What's not complete
- 20-minute AI *coding* agent: **BLOCKED_AUTH_AND_LOCK_NOT_ACTIVE**. Copilot model inference for a personal repository normally requires credential setup and a cost allowance.
- Original mocked Roblox server integration QA from v2.3: not yet ported.
- Native Roblox Studio, cross-client networking and mobile screenshot review: unverified.
- PvP, blueprint capture, co-op, persistent save and monetization: planned, not built.
- Game is **not approved for publication**.

## Phone-friendly navigation
- [Actions runs (quality audit evidence)](https://github.com/kk051780/toy-wars-factory/actions)
- [Open development issues](https://github.com/kk051780/toy-wars-factory/issues)
- [Pull requests and code reviews](https://github.com/kk051780/toy-wars-factory/pulls)
- [Source of truth and next task](PROJECT_STATE.json)
- [Development constitution](AGENTS.md)
- [Toy character catalog](config/characters.json)
- [Game world and design](docs/PRODUCT_VISION.md)
- [Quality scope](docs/QA_SCOPE.md)
- [First size and evidence baseline](history/C00001_bootstrap.json)

Every cycle must add verifiable evidence, not self-reported claims. Size may decrease for justified refactoring; behavior regressions, missing character roles, or QA relaxation may not be silently accepted.

**The only mandatory owner interaction after approved account connection is security/billing exceptions and final publication approval; all ordinary coding and QA are being designed for unattended execution.**
