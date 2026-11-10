# P0-D V3 — progress-by-evidence, permanent 企画室, first-release / live-ops separation
Date: 2026-11-11 JST
Owner directive / game_id: TRAP_RAIDERS / work_id: p0d-siege-v19
Status: process contract; **not a game feature, source acceptance, or release authorization**.

## 0. Precedence / purpose
This V3 adds product management and reporting to the [CHAT-FIRST V2 owner contract](https://github.com/kk051780/toy-wars-factory/issues/218) without replacing the single CHAT-INTEGRATOR and independent QA design. No routine per-pack Codex. Github Issue comments do **not** execute Windows Codex. Never write main, merge, publish Roblox, spend, modify protected P0-A/B/C auth/CAS/reviews or the five existing automations without separate OWNER authorization.
Canonical lanes: #218 coordination, #220 S1 release train, #219 permanent 企画室 and market-to-game queue, #213 Windows/Studio factual QA, #109 research archive, #115 business/portfolio.

## 1. Mandatory per-chat progress report
On each substantive work turn and each deliverable, each P0-D chat posts **at least one up-to-date report** to its own canonical issue and links a compact pointer to #218. If the chat cannot write, show the same report to OWNER and state NOT_POSTED. One chat cannot force another active chat to wake up: other chats must read this rule on their next run/turn.
Report **own claimed scope** only. Do not fabricate a percent for a different lane, the integrated game, Studio QA, revenue or a backlog one never finished. Freeze the claim's acceptance checklist first; percent = 100 × accepted/evidenced items divided by that checklist's total. Count partial item as 0 until its acceptance test meets the defined exit. If no verifiable denominator yet, set `UNKNOWN` (never guessed 90%). Add acceptance numerator/denominator for audit. New requirements are separate scoped tickets, not retroactive endless denominator changes.
A completed isolated package is **100% of that package**, not 100% of the S1 game. Python 80/80 and GitHub 16/16 are source/QA evidence, not Roblox Studio readiness. Editorial 78/648 measures manuscripts, not 3D or integrated gameplay.

**Copy-paste report contract:**
```text
[P0D_PROGRESS_V3]
date_jst=YYYY-MM-DD HH:MM JST
game_id=TRAP_RAIDERS
work_id=p0d-siege-v19
release_id=P0D-S1-KIDS-RC01 | FUTURE | N/A
lane=CHAT-INTEGRATOR | CHAT-QA-* | CHAT-FEATURE-* | CHAT-PLAN-*
claim=<issue comment URL / packet_id>
scope=<unchanged acceptance checklist>
lane_progress_pct=<0..100|UNKNOWN>
accepted_items=<n>/<N> (one named acceptance item = binary with evidence)
evidence=<40-char commit, file SHA, tests, human playtest or actual Studio log>
game_release_progress_pct=<#220 official value|UNKNOWN; NOT local guess>
business_readiness=<RESEARCH|HYPOTHESIS|PRIVATE_PLAYTEST|PRELAUNCH_REVIEW|LIVE_MEASURED>
stage=<RESEARCH|SOURCE_IMPLEMENTED|CHAT_ASSEMBLED|CHAT_QA_PENDING|CHAT_RC_READY|STUDIO_PARTIAL|STUDIO_PASS|RELEASED>
quality=<PASS|PARTIAL|FAIL|NOT_TESTED>
blockers=<truthful actual open defects / prerequisites>
next_acceptance=<one specific verifiable next action>
new_market_idea=<ID or NONE>
owner_action=<only if truly required; otherwise NONE>
```
Each report also includes **remaining unaccepted checklist items**, timestamp, and clear distinction between offline/source QA, actual integrated RC, Studio, and live users. Do not emit false precision, turn historical reports into current progress, or count parallel drafts twice.

## 2. Only #220 owner computes release progress
S1 overall **release readiness score** is binary evidence points / 100, independently from each author's own percent. The CHAT-INTEGRATOR owns this calculation and must itemize and link exact artifacts:
- Differentiated first playable and player purpose (10): original hook/target/market hypothesis 5; understandable win/lose teaching plan 5.
- Real S1 gameplay (25): join/team/spawn 5; egg pickup/steal/score 10; server combat/HP 5; round end/reset/replay 5.
- Source-built map/mobile UX (15): traversable castle/map 5; mobile readable HUD/control 5; fast contextual onboarding 5.
- Whole-game reproducibility (10): project/wiring and bootstrap 5; immutable source locks and no duplicate event/HP/reward authority 5.
- Independent quality (15): negative/offline test 5; static integrated actual-source QA 5; actual integrated gameplay-trace QA 5.
- Actual platform acceptance (10): Roblox Studio real multiplayer/team/HP/win 5; mobile/performance/fail-safe/normal Studio exit 5.
- Prelaunch market/business readiness (10): human first-play observation & next-match desire 5; child-safe optional value/cosmetics + discovery/analytics and rollback plan 5.
- Explicit OWNER public-release approval (5). Until separately given, 0.
Totals 100. Give 0 points for UNKNOWN/BLOCKED/NOT_TESTED without claiming failed behavior. Log `unverified` separately. This is a **project progress measure, not probability of business success or proven monetization**. Only #220 may assign `game_release_progress_pct`, and only when each item has been audited. Otherwise UNKNOWN with named missing measurements.
No single editor or collector can hold the first release hostage by adding 648 assets, S2-S4 or novel feature lists to the mandatory S1 gate.

## 3. Permanent 企画室 #219: research + creative + product decisions
The 企画室 is **a permanent first-class lane**, not merely the D18 character factory. Open non-overlapping work for any available Chat via #219 independent SOFT_CLAIM and an identified sublane:
- `D18-COLLECTION`: 648 character concepts, 72 flagship revised designs, next characters, recognizable silhouettes, low-poly original 3D, free collection narrative. Count separately (a) original catalog ideas, (b) individually edited briefs, (c) committed actual 3D/Luau, (d) chosen/included in RC, (e) Studio-tested. Current known: 648 initial ideas; 78 edited; 72/72 flagship edited; two showroom Luau models are **source candidates**, not integrated/engine-PASS. This lane continues after launch but is not an S1 prerequisite.
- `MARKET-SCOUT`: examine Roblox first-party game pages/charts, source-dated concurrent-user trajectories, game loops, update cadence; investigate YouTube creators and developer postmortems with URL, publish date, **video timestamps** or transcript confidence. Never infer revenue from CCU or marketing anecdotes.
- `GAME-DESIGN`: convert evidence into unique original heist/trap/monster/team tactics, a one-sentence loop, minimum prototype, risk/anti-copy judgement, and a reversible H0-vs-H1 variant.
- `FTUE-UX`: first 60s goal clarity, one-touch rematch, mobile readability, fun and social play. Tie to actual first-player tests, not speculative KPI pass.
- `FAIR-COMMERCE`: non-pay-to-win cosmetic/value propositions, ethical age-appropriate monetization, policy verification, no pressure/random-paid loops. Payments OFF until separate OWNER approval.
- `LIVE-ANALYSIS`: after authorized release, Creator Analytics/legitimate feedback and real cohort metrics; select changes based on measured bottlenecks, not guessed uplift.
- `CONTENT-FEATURE`: approved actual Luau/3D assets on a new isolated branch, source manifest and tests; cannot write integrator `rc/`, or replace D01-D17 originals.
The 企画室 may propose, reject or park. Only the CHAT-INTEGRATOR selects compatible candidate source into the S1 branch after quality and OWNER priority agreement. It may not self-publish, change canonical authorities or modify another chat's source.

**Research intake IDEA_CARD** (one per prospect): unique ID; as-of date/time; game/video/chart URL; first-party vs third-party and confidence; observed mechanic and time-coded proof; why players choose/return/pay (HYPOTHESIS); TRAP RAIDERS original twist; target user; estimated implementation/QA cost; expected measurable outcome (without inventing uplift); security/child-safety/IP risks; H0 no-change alternative; status `SCOUTED → EVALUATED → PROTOTYPE_APPROVED → ISOLATED_SOURCE_READY → CHAT_RC_SELECTED/DEFERRED → REAL_PLAYER_TESTED → ADOPT/REVISE/REJECT`. Each approved experiment must have owner, test cases, rollback and a target stage (S1 hardening / post-release), and link its decision to #219.
Prioritization: 30% core-loop clarity, 20% distinctiveness, 20% cost-to-test, 15% evidence strength, 15% fairness/replay/retention potential; editorial scores never claim actual financial uplift. D18 art production and market analysis are **parallel sublanes** with separate claims and no competition for the same branch.

## 4. Three distinct product phases and stop gates
**PRELAUNCH (now, privately testable but NOT Roblox public release):** build a cohesive two-player game; verify complete game server authority, mobile, normal exit, replay, safety; evaluate market differentiation and credible voluntary cosmetic value; watch human players experience first action and desire a rematch, collect only safe minimum observations. The **initial release gate** is the OWNER decision that it is fun, technically safe, discoverable and has a plausible original monetization roadmap, NOT proof of earnings (impossible prelaunch). If gate fails, improve first before public launch. Small/private player tests also require OWNER authorization.
**FIRST RELEASE:** OWNER separately approves publishing, data/age safety and any spending or paid feature; release a *bounded S1* with version/rollback/analytics plan. Do not require S2-4 or all 648 concepts. No monetization switches silently enabled.
**POST-RELEASE LIVE OPS:** observe actual impressions/PTR, first-play bounce (<60s and 61-180s), first objective, round completion, repeat rate, D1/D7, co-play, spend conversion/Robux and real net revenue (platform proceeds less actual eligible costs). If events/samples absent, UNKNOWN; never mislabel estimated income as earned. Diagnose funnel, choose highest-impact experiment vs H0, branch/source QA, controlled release approved, observe cohorts, ADOPT/REVISE/ROLLBACK and feed learnings into the next game. This makes a reusable successful *process*, not a promise every game earns.
After reliable success evidence, codify reusable first-game -> research -> build -> QA -> release -> analyze -> improve loops as the P0-D-to-portfolio playbook, while preserving owner approval boundaries.

## 5. Operating principles — speed without sacrificing quality
Small independent exclusive slices in parallel; first-pass actual code and test, not endless documents. No duplicate scheduler/event/damage/economy authority. Reuse real original source by fixed SHA and check licenses/IP. Each lane keeps WIP 1 and reports next accepted deliverable. The release RC stays single-writer (#220); independent QA stays separate; Windows Codex only after Chat near-final RC unless OWNER-specific engine blocker exception. Feature additions cannot regress performance, fairness, mobile usability or existing evidence. Research must convert into a measurable experiment or explicit NO_BUILD; avoid building what a player cannot notice.

## 6. Dated evidence, not current business proof
2026-11-11 GitHub #220 reports a source-built S1 at commit `35d7d0525388e885aac8281eff2315a59831e0cf`, offline tests 80/80, source 16/16; original boss integration, real 2-client/mobile Studio, and overall RC QA remain open. #219 reports flagship concept editing 72/72 and two source-only 3D showcase model candidates. These are lane evidence **not** global release-percent or income measurements.
Roblox official discovery: https://create.roblox.com/docs/discovery
Analytics: https://create.roblox.com/docs/production/analytics
Engagement: https://create.roblox.com/docs/production/analytics/engagement
Onboarding: https://create.roblox.com/docs/production/game-design/onboarding
Roblox charts: https://www.roblox.com/charts
Market snapshots must carry observation timestamp. One example dated 2026-11-10 UTC is https://www.zing.co.uk/industry-resources/roblox/charts/ — unverified external CCU is not net earnings.
YouTube/source reference: https://www.youtube.com/watch?v=feQonouNMFM ; third-party interpretive notes https://ai-kidou.jp/video-report-roblox-claude-code-games/ . No video claim should override measured in-game player results.
