# Codex follow-up / restore

1. Read #218/#213/#217 latest. Verify actual PC CHECKPOINT/RESUME/Place/source hashes; preserve newest source and unused backups. Finish v39 final-saved QA and v43A safety dependencies before optional D14.
2. With OWNER-provided **private key** (never in public GitHub/logs/command text), use fixed handoff commit + known `tools/restore_handoff_safe.py`, strict game_id/work_id/packet_id/expected ZIP SHA and O_EXCL owned private directory. Inspect restored files/manifest/luau syntax; run Python tests. No automatic merge or publish.
3. Isolated S1: trust only canonical existing D14 `VehicleSeatCore`; proof two authorized crew, only active driver can advance; passenger/enemy/egg carrier/spoofed packets never move. 1→2, 2→3 nodes as discrete manual server requests. Server heartbeat status, 10 Hz interpolation, stop on dismount/team change/round end. Test no flag/damage ownership regression.
4. Roblox Studio 2/3-client and mobile low-end/motion reduced, S1–S4, egg lifecycle, 7 jobs, FPS, log; no direct creation or modification of the other-chat D14 decorative CART/RAFT. Its separately owned visual client may be attached only after PC review. Stop→Edit→Save→Quit and only owned PID exit, publish/charges disabled.

Minimum negative cases: route 1/25 nodes, edge 5/81 studs, NaN/Inf, coordinate ±2001, max speed >16, replay sequence, stale round/team, passenger, unmounted driver, carrying egg, snared, dt >100ms, abrupt dismount on moving leg, endRound after repeat command.

**Result statuses:** Python offline only; Roblox Luau parsing: NOT_TESTED; Studio: NOT_TESTED; PC decrypt/integration: NOT_TESTED; true physics: NOT_INCLUDED. Return separate evidence at #213 and #218.
