# TOY WARS FACTORY — development constitution

1. Preserve previous work. Read PROJECT_STATE.json, docs/PRODUCT_VISION.md, config/characters.json, latest commits and QA before writing.
2. The product is a **toy factory strategy game** with PvE, planned PvP blueprint capture and co-op. Do not present planned items as built.
3. Modify small isolated modules, add regression checks, review actual diffs, and record rationale when source size decreases.
4. Never weaken QA or approval gates to pass a test. Policy changes require the delegated approval process and regression evidence; never waive objective quality or spending limits.
5. Never claim Roblox Studio, multiplayer, mobile UX, character visuals, player retention, or fun are verified without objective dated evidence.
6. Source code and assets from competing titles must not be copied; general mechanisms may inspire original implementations.
7. Changes from unattended agents go to a branch/draft PR; no automatic publishing, purchases, billing changes, scope escalation or Roblox releases.
8. If tests or permissions block progress, report BLOCKED with a concrete next step instead of declaring success.
9. Owner works through Android ChatGPT; don't require PC, command line or manual debugging.
10. Every meaningful development cycle must log tested functionality, changed files, file size delta, characters touched, defects, evidence URLs and next task.

## Cross-chat continuity (mandatory)
- At the start of any new chat/task/agent cycle, first read current main HEAD, PROJECT_STATE.json, AGENTS.md, config/quality_policy.json, latest Actions runs, PRs and open issues. Main is the authoritative source for code, permissions, quality and policy.
- Optional generated read-model: fetch status/CHAT_HANDOFF.md and status/LATEST_STATE.json from `twf-handoff-snapshots` at the SAME immutable snapshot commit if it exists. Require schema=2, canonical_repo=kk051780/toy-wars-factory, release_decision=HOLD_ENGINE_UNVERIFIED and 40-hex source_revision; independently verify via GitHub compare that source_revision is at/behind current main and only status/ paths changed since it. Otherwise label UNTRUSTED_STALE and fall back to current main/PR/CI directly. Main's status files are historical only after cutover. Snapshots never override main policy, security, approvals, QA, coordinator or release holds.
- Snapshot generations: when the first 512-commit data-only history fills, read a contiguous set of `twf-handoff-snapshots`, `twf-handoff-snapshots-g0002`, etc.; select the highest generation but only after checking all archived generations, exact 100644 two-file trees, bounded linear history and successor orphan root `prior-snapshot-tip` links. Read both passive files by ONE immutable SHA. If list/ancestry/compare cannot be authenticated, UNTRUSTED_STALE and consult current main/PR/CI directly. Never force/rewrite/archive-delete refs.
- Canonical source: public GitHub main; chat memory, snapshot branches and old archives can be stale. Never treat generated status as a reviewed source.
- Commit all actual improvements to reviewable branches and preserve reproducible tests, defect root causes and file-size history. Never equate 20-minute scheduled audit to an autonomous coding agent.
- From an Android chat, the user may send only: TOY WARS再開. The assistant retrieves current GitHub state before acting; it must not ask the user to restate prior requirements.
- If the product cannot auto-inject instructions into a completely new conversation without a trigger, be truthful about that limitation.

## Standing delegated authority and shared execution (2026-10-25, mandatory)
- The owner explicitly delegated approval decisions to the assistant and prioritized careful autonomous progress toward completion. Ordinary game/system PR integration no longer requires an owner reply. This supersedes older checkpoint statements about per-PR owner approval.
- Read docs/AUTONOMOUS_INTEGRATION.md, docs/COMPLETION_ROADMAP.md and the current owner delegation/configuration before acting. Preserve objective quality, evidence truth, incident holds and spending caps.
- Manual go joins the existing game task. Do not start a parallel editor. Idle requests use the fenced DISPATCH protocol; active work is joined.
- WORKER, META, REVIEWER and manual CONTROLLER share twf-repair-coordinator / ops/REPAIR_COORDINATOR.json. Commit on the observed head, update with expected_sha/force=false, reread ownership/epoch/expiry before writing, and release only the owned lease. Expiry alone is not takeover permission.
- Authors produce small isolated draft PRs and fix their failures. A separate registered reviewer task/context evaluates current head CI, actual behavior, source ledger and protected controls before integrating one PR at a time. Authors cannot approve their own task/run.
- Every integration checks actual main QA before continuing. Main failures and concrete WORK_REQUESTS take priority over new features. Never disable the schedule merely to wait.
- Show independent-review/integration status with PR, actual contents, current head CI, outcome and next actor. Do not request a routine owner approval sentence.
- The daily system/game review remains mandatory: inspect real failures and effectiveness, open current primary web sources, implement a minimal tested system improvement and create concrete game experiments. Do not freeze the architecture or mistake research/coverage for a game fix.
- Follow the explicit additional-module/installer/regression path before expanding a source module. Preserve accepted regressions, baseline provenance, character identity and release evidence requirements.
- The current engine/release HOLD reflects missing objective evidence, not a routine owner-approval bottleneck. Never claim Studio/physics/multiplayer/mobile/visual/fun verification without actual dated results.
