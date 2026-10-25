# Studio Autopilot — reusable multi-game control plane (prototype v0)

**This directory is a commercial-product R&D prototype, not an autonomous game generator or a supported product.**
Toy Wars is the first *bound* project. Skyline Parkour is an explicitly unbound, invented demonstration, not a live game or GitHub repository.

## Scope of the first implementation

- Project manifests describe game concept, gameplay loop, author/reviewer/meta task identities, repo and shared lease, quality evidence and restrictive policy.
- The portfolio loader rejects duplicate game IDs, duplicate repositories, reused task identities, unsafe local paths and unauthorized publication/inference/spend.
- The planner accepts optional **untrusted observations** and produces read-only advice. It cannot dispatch, merge, call external AI, access Roblox, or publish.
- A stalled daily META (`no_update`) is surfaced as an alert without blocking an independent game worker. An exact-main-CI mismatch blocks main integration.
- All decisions carry ADVISORY_ONLY and release_eligible=false. Observations supplied to the CLI are **not proof** of a real GitHub/Roblox outcome.

## Try the independent core

From repository root:

    python3 studio_autopilot/core.py validate
    python3 studio_autopilot/core.py plan
    python3 -m unittest discover -s tests -p 'test_multigame_core.py' -v

To simulate a check, create a local observations JSON with `schema: 1` and an observations `projects` map keyed by `game_id`, then use `plan --observations PATH`.
Simulation is read-only and its fields are untrusted; no production actions occur.

## Multi-game architecture

    Portfolio -> isolated project manifest -> game-specific authorized tasks
      -> project's own repository + fenced coordination ref -> draft source PR
      -> different reviewer task -> exact-head CI -> approved merge -> main QA
      -> Roblox engine + device + 2-client proof -> player test -> iterative design

Each project must have its **own repository, coordination state and task identities**. A shared service may schedule *which project gets a turn*, but must never grant a project access to another project's repository, keys, lease or budget.
The portfolio is separate from the game product vision: a new game should not require renaming every Toy Wars-specific source, test or task.

## Built-in safety / hard limits

- Prototype is OBSERVE-ONLY, with zero external-model spending, no automatic publication, no credential handling and no automatically authorized new games.
- The status planner does not trust developer summaries as CI; production integrations must use live, exact-head provider evidence under review.
- Existing Toy Wars game quality, Gemini trial incident hold, and Roblox release HOLD are unchanged.
- A future executable adapter must implement scoped GitHub auth, per-repository CAS lease, bounded quotas/cost reconciliation, branch-only writes, independent review and post-merge rollback/repair.
- Engineering completion is not the same as fun. Player playtests, retention and performance must be measured outside code mocks before commercial release.

## Existing game vs product state

Toy Wars project progress is tracked in `config/progress_milestones.json` and currently scores automation 57% and game 38% by separately defined acceptance criteria.
**Those values are not a completion percentage for Studio Autopilot itself.** The product has a separate road map and no validated sales readiness.

## Next executable upgrades

1. Add a GitHub read-only connector that turns live per-repo CI/ref/PR data into verified observations. Negative-test forged CI and foreign repos.
2. Add safe portfolio scheduler with per-game fairness, task/run correlation, and lease fencing; do not simply copy a single-game task UUID.
3. Isolate per-game credentials, API budgets and installation policy before enabling a second real game.
4. Connect private Roblox Cloud engine smoke tests, then hosted Studio two-client/device tests, with evidence records.
5. Add genuine player sessions, playtest KPIs and game-quality iteration; test at least two distinct real games.

Docs are truthful about known gaps; avoid marketing the present prototype as fully autonomous. See PRODUCT_ROADMAP.md.
