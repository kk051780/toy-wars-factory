# P0-D v42.3 — Server result evidence bridge (reference only)

Status: `CHAT_LEAD_QUOTA / PURE_REFERENCE / GAME_INTEGRATION_NOT_TESTED`.
Game `TRAP_RAIDERS`; work `p0d-siege-v19`; target **after authentic v36 QA and v42.2 compatibility check**. Do not overwrite existing v36 code. This packet adds a separately reviewed reference module and input fixture, not a substitute for the v42.2 ZIP.

## Server-owned data path

1. `MatchCoordinator` (server-only) creates globally unique matchId and server immutable round/participant snapshots, including participantTeams roster. The target user and egg carrier must both match the authoritative roster. Never accept `round`, `player`, `activeSeconds`, `actionCounts`, `assistFlags`, or `winnerTeam` from client Remotes or attributes writable by clients. `serverOwned=true` is a sanity assertion, **not authentication**.
2. After the match result is finalized and its membership/teams/objectives are reconciled from server logs, for every participant call `RoundEvidenceGate.derive(roundSnapshot, participantSnapshot, Player.UserId)`.
3. On any error return, **do not award XP**. Log a sanitized error code and source match id, not raw player input.
4. Map returned evidence to the **actual inspected v42.2 `ProgressionCore` input interface**. No assumption that names already match. Crucially, this shape validator **does not** output `serverValidated` or `isCurrentActiveMatch`: those attestations must be supplied exclusively by the real server MatchCoordinator with live round identity, not inferred from a boolean field in this snapshot. Core must perform the authoritative completed/active/action threshold checks, per-match capped XP (max 104) and mastery points (max 57), job validity, duplicate match guard.
5. Invoke store adapter through `UpdateAsync` outside of pure-module side effects, merging only the progression namespaced fields into existing player save; retain existing schema fields. A callback may execute repeatedly. Do not grant rewards based on callback side effects.
6. If save fails, surface an unambiguous `NOT_SAVED` state. After success, send sanitized `ProgressionViewModel` display values to the owner only. `CONFIRMED_STORED` alone **does not demonstrate new award**; never trigger an exactly-once fanfare/cosmetic purchase/unlock based solely on it.
7. A match ID must not be replayable from client input, persistent rematch logs, old server sessions, or new server reconnect. v42.2's last-128 record alone cannot establish infinite replay prevention. Build a monotonic server epoch/age window backed by trusted match lifecycle before deployment.

## Semantics and open risks

- Current game data schema, MatchCoordinator exact API, Core function signature, and actual NPC/round implementation are **unknown** here. The adapter validates *shape*, not producer authenticity. The Codex integration must inspect actual local sources and demonstrate the source trust boundary.
- `activeSeconds` is server-sampled engagement, not connected wall-clock. An AFK player with zero actions remains zero XP under Core rules; this adapter deliberately **does not mint XP**.
- The three assist flags must be server-derived, disjoint factual categories (`defense/rescue/siege`) and not directly affected by repeated client-claimed hits. Core applies max-three types.
- The egg receipt may only be credited when server-owned egg delivery has a participantUserId and a winning team consistent with the finalized result.
- `winnerTeam=DRAW` is valid only with no egg-delivery receipt. Neither draw nor loss creates win bonus, but participation may still count.
- v37–v41 bosses/weather/time/vehicles remain design backlog, not integrated.

## Required Windows Codex QA after quota recovery

- Phase 0: verify newest v36 `CHECKPOINT.md`, `RESUME.md`, `BUILD_MANIFEST.json`, `QA_REPORT.md`, `FEATURE_MATRIX.md`, `.rbxlx`, source and ZIP hashes, proper work_id and Studio PID owner.
- Phase 1: finish v36 visual polish and S1–S4 lobby→match→egg→result→lobby replay; 7 jobs, NPC motion, attributes, zombie, 2-client/mobile when truly tested; safe owned-Studio Stop/Edit/Save/normal Quit/PID absence.
- Phase 2: verify v42.2 *actual* ZIP SHA before attempting level/store/UI integration. **Then** review this additive v42.3 mapper against v42.2 Core and actual server-owned match events. Do not assume source files from an Issue summary are enough.
- Phase 3: Studio with new/old characters, AFK/partial match, wrong team/egg receipt, disconnect/rejoin, duplicate match, UpdateAsync retry and failure, 2-client spoof, all 7 jobs, S1–S4. No persistent strength benefits at Lv25 vs Lv1. Close only Codex-owned Studio.

Gate results: offline Python tests = reference evidence only; Luau runtime, Studio, DataStore, 2 client, physical phone, current v36 source integration are **NOT_TESTED**.

Safety: no GitHub public game-source/Place/ZIP push, main/merge, publish, paid API, Robux or additional spending. Existing P0-A/C auth/CAS and independent review holds unchanged.
