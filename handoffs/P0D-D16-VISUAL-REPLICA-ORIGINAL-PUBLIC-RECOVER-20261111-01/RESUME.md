# Codex handoff: D16 visual replica addon

- `work_id=p0d-siege-v19`; `packet_id=P0D-D16-VISUAL-REPLICA-20261110-02`.
- Dependency: previous D16 scale pure FSM pinned `7242b32760327a527b868f5405d7782265388fe2`; **do not replace or re-apply** previous ZIP.
- Integration priority remains: backup latest v37 local Place/manifest and QA -> v39-H1 -> v43-A -> conflict-check event packs -> **only then** test this optional D16 addon.
- First action on Windows: verify encrypted ZIP SHA and manifest; run tests; inspect only the additive source files and study real v37 server event and display paths.
- Base PC SHA unknown, Studio QA NOT_TESTED, actual Luau parse NOT_TESTED. No auto-run from Issue text.
- Sanity: `remainingSeconds` MUST be computed from *same server-side round clock* as first D16 `expiresAt`; do not substitute `workspace:GetServerTimeNow` in clients.
- Restrictions: main/merge/Roblox publish/real purchases/extra spending HOLD. Do not modify D13/14/15/17, P0-A/B/C or other ChatGPT branches.
