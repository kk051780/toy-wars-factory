# TOY WARS FACTORY — development constitution

1. Preserve previous work. Read PROJECT_STATE.json, docs/PRODUCT_VISION.md, config/characters.json, latest commits and QA before writing.
2. The product is a **toy factory strategy game** with PvE, planned PvP blueprint capture and co-op. Do not present planned items as built.
3. Modify small isolated modules, add regression checks, review actual diffs, and record rationale when source size decreases.
4. Never weaken QA or approval gates to pass a test. Policy changes require owner approval.
5. Never claim Roblox Studio, multiplayer, mobile UX, character visuals, player retention, or fun are verified without objective dated evidence.
6. Source code and assets from competing titles must not be copied; general mechanisms may inspire original implementations.
7. Changes from unattended agents go to a branch/draft PR; no automatic publishing, purchases, billing changes, scope escalation or Roblox releases.
8. If tests or permissions block progress, report BLOCKED with a concrete next step instead of declaring success.
9. Owner works through Android ChatGPT; don't require PC, command line or manual debugging.
10. Every meaningful development cycle must log tested functionality, changed files, file size delta, characters touched, defects, evidence URLs and next task.

## Cross-chat continuity (mandatory)
- At the start of any new chat/task/agent cycle, read status/CHAT_HANDOFF.md, status/LATEST_STATE.json, PROJECT_STATE.json, AGENTS.md, config/quality_policy.json, latest Actions runs, PRs and open issues.
- Canonical source: private GitHub main; chat memory and older zip packages can be stale. If snapshot is missing or behind the current source, inspect GitHub HEAD and regenerate it rather than guessing.
- Commit all actual improvements to reviewable branches and preserve reproducible tests, defect root causes and file-size history. Never equate 20-minute scheduled audit to an autonomous coding agent.
- From an Android chat, the user may send only: TOY WARS再開. The assistant retrieves current GitHub state before acting; it must not ask the user to restate prior requirements.
- If the product cannot auto-inject instructions into a completely new conversation without a trigger, be truthful about that limitation.

## Shared execution and actionable approvals (mandatory)
- Read docs/REPAIR_COORDINATION.md and the live twf-repair-coordinator branch before any game/system write. GitHub is the cross-chat lock; a local flag or an in-progress check alone is insufficient.
- Manual go uses the same game task. Join an active run; never launch a parallel editor. If idle with capacity, first acquire the DISPATCH ticket using expected_sha and force=false, recheck the service, then request that task once.
- Scheduled game workers, daily system reviewers and manual controllers share the fenced coordinator. Use the observed ref head as commit parent, confirm the ref update, recheck ownership/expiry before every write and release only the owned epoch. Never steal a lease based only on elapsed time.
- When approvals block progress, always list each PR, actual contents, kind, exact-head CI link, approval scope and a ready-to-send approval sentence. Manual status/go replies always include the items; scheduled deduplication starts only after a complete request has been recorded.
- A general go is not approval to merge game PRs or publish Roblox. Approved integration uses the exact listed heads and fresh CI under a CONTROLLER lease.
- The daily system/game review is mandatory: inspect actual failures and effectiveness, open current primary web sources, propose a minimal experiment/fix with regression checks, save measured results and game candidates. Do not treat the current architecture as the best or final one. Read docs/SYSTEM_REVIEW.md and its saved task prompt.
- A research-only cycle is not a code improvement. Keep source fixes, added coverage, proposals, applied changes and real engine evidence distinct. Preserve existing accepted tests, approval gates, provider/billing caps and release holds.
