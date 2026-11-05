# Studio Autopilot — roadmap to a licensable product

## Product promise (target, not a current capability)

Configure a *different* Roblox game, then let supervised AI author, check, independently review, test, improve and report in a bounded cycle. The system is reusable, not a Toy Wars-only code copier. It cannot promise a hit game, 100% zero human work, or automatic sales.

## Product interfaces

**Control plane**: tenant and project registry, permissions, project-type templates, scheduler, lifecycle and evidence accounting.
**Execution adapters**: GitHub connector, AI author provider, independent reviewer, Roblox Open Cloud engine, optional Studio workers, telemetry and feedback. Each has per-tenant scope and explicit capabilities.
**Experience layer**: game-design brief -> hypotheses -> acceptance contracts -> source/tests -> build preview -> two-player/device smoke -> opt-in player playtest -> analytics and feedback.
**Commerce layer**: Studio plugin as front end for Roblox creators; backend orchestration as a separately delivered paid service, not as a fake Creator Store model.

## Commercial acceptance checklist

| Phase | Proof required | Today |
| --- | --- | --- |
| P1 Configurable multi-game manifests | At least two distinct genre manifests validate; unsafe project claims rejected | PR prototype; not main accepted until QA and review |
| P2 Verified live GitHub adapter | Repo isolation, auth boundary, exact-head CI, no_write simulations | NOT_BUILT |
| P3 Multi-project dispatch | Separate tasks/leases/repos; 100 collision and fairness trials | NOT_BUILT |
| P4 Failure self-repair and monitoring | Duplicate dispatch/no_update/main regression recovered in staged faults | NOT_BUILT |
| P5 Secure AI provider gateway | Actual hard budget limits, provider outage and cost reconciliations | NOT_BUILT; GEMINI ON HOLD |
| P6 Cloud Roblox engine proof | Private place test logs with source/version IDs | NOT_BUILT |
| P7 Studio clients and mobile | Actual 2-player/device run logs and snapshots | NOT_BUILT |
| P8 Experience quality loop | At least two game concepts tested with actual players and measurable iteration | NOT_BUILT |
| P9 Plugin/dashboard UX | Can configure different games without editing source | NOT_BUILT |
| P10 Distribution/licensing | Auth, tenant isolation, terms, license ownership and refunds/support | NOT_BUILT |
| P11 Multi-game pilot | Two independent repositories run several safe cycles with verifiable independent QA | NOT_BUILT |
| P12 Commercial launch | Seller requirements, real support docs, payments and version policy verified | NOT_BUILT |

## Marketplace and intellectual-property constraints

- Roblox Creator Store supports selling **Studio-use models/plugins** in USD, not arbitrary hosted orchestration subscriptions represented as marketplace assets.
- Real seller account/onboarding, regional payment availability, 2-step verification, ownership and third-party asset licensing must be checked prior to sale.
- Backend SaaS/service billing may require separate site/terms and must never infer an API key from a creator's account without explicit authorization.
- Never bundle third-party competitors' restricted source/assets or sell their work as original.
- Brand name is provisional. Before launch, check trademarks and license/redistribution rights. Do not publish the private prototype just to demonstrate a demo.

## Primary official references (checked 2026-10-25)

- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://create.roblox.com/docs/cloud/reference/features/luau-execution
- https://create.roblox.com/docs/studio/cli
- https://create.roblox.com/docs/production/creator-store
- https://en.help.roblox.com/hc/en-us/articles/21308223046932-Creator-Store-Terms

## Product-independent progress accounting

Toy Wars 57%/38% does not become Studio Autopilot 57%/38%. No commercial completion % is assigned until these 12 P-milestones have evidence-backed acceptance/weighting.
Do not mark P1 as accepted while this work is still a draft, and never count the demo parkour manifest as a launched game.
