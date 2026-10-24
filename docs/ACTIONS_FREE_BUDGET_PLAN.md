# TOY WARS — GitHub Free Actions time budget proposal (2026-10-24)

## Problem
Currently two idle QA/state workflows each run every 20 minutes, for about 2 * 72 * 30 = 4,320 jobs/month, without writing a line of gameplay code. GitHub Free private-repository standard runner allowance is advertised at 2,000 minutes/month, though account-specific billing and exact chargeable minutes must be checked. Even an average 1 minute per run would exceed that alone.

## Proposed low-cost arrangement (NOT MERGED until owner approves)
- `loop-watchdog.yml`: every six hours (4/day), **and still on-demand**.
- `handoff-sync.yml`: every six hours, offset by 2 hours, **and still on every code/state push**.
- All `bootstrap-quality.yml` / policy / character test checks remain triggered on actual changes and PRs: no reduction in required pass criteria.
- No recurring AI inference is switched on by this proposal. A single Gemini candidate exists separately in draft PR #11, awaiting owner privacy/API approval.
- Approx. 240 idle jobs/month after vs 4,320 before (94.4% fewer). Each still consumes GitHub Actions runner minutes.
- Start AI development once daily or event-driven after proof and quota tracking; consider 2/day only after measured run costs + provider limits support it.
- GitHub Actions scheduled jobs can be delayed or skipped in high-load conditions; the frequency is target, not a guarantee.

## Operational controls
1. Track actual GitHub Actions minutes per project from billing portal; do not infer the charge from count alone.
2. Do not merge untested code autonomously; agent generates draft PR only.
3. Throttle or disable AI jobs if Gemini 429, tier exhausted, Actions quota close, or QA fails.
4. Owner requirements prioritize quality and persistent progress; timestamped cycle logs distinguish source changes from idle audits.
5. Public Roblox releases or paid-tier upgrades need explicit separate owner approval.
