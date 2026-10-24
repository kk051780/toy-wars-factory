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
