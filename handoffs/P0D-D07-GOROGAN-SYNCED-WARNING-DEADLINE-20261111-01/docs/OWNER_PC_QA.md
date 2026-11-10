# OWNER Windows Codex QA gate — D07 Gorogan warning clock comparison

## Ownership and source precedence

Read GitHub #218 top and newest comments, #213 latest **actual PC** report, #217 top. OWNER must directly instruct the Windows Codex; a GitHub issue comment is not execution authorization. Preserve latest PC CHECKPOINT, Local HEAD, game Place/source SHA and genuine Studio instance first; do not overwrite newer or protected work. Existing exact D07 AI, combined server and visual sources are always preferred; this optional sidecar never replaces the game.

The actual PC isolated S1 Gorogan integration at #213 `6776360480` is PARTIAL, despite native Luau parse 32/32 and Studio normally closing. No stable red warning timing or independent fake Remote damage rejection has been proven. The newer PC's actual implementation may already correct this: if so no patch. If not, test the smallest adapter in an isolated copy, not by push to `main`.

## Trusted source-only mapping, no second lifecycle

1. D07 Core's genuine `STOMP_WARNING` has `cmd.windupEnds` in Core's `input.now` clock domain. The server-owned combined runtime owns this command (no client Remote). At emission, sample a reliable server `coreNow` in **the same monotonic time base** and `workspace:GetServerTimeNow()`. Never mix `os.clock()` or `tick()` with `coreNow` without verified conversion. The latter uses Roblox's synchronized epoch-like clock. There must be **one** authoritative impact time, not a new timer.
2. If `config.enabled` and `ownerApproved` are both TRUE after real PC QA, instantiate `GoroganWarningDeadlineServer` once per real event/epoch. Feed only the genuine Core warning; its `roundId`, `eventId`, `attackId`, and `windupEnds` must already have passed server validation. The server `clock.roundLive` callback must recheck current epoch/round and genuine boss identity. If a callback yields, recheck epoch/event/clock/owner afterward; stale means STOP and no send. Do not mint attack IDs in this module.
3. Attach the extra `kind="STOMP_DEADLINE"` value snapshot via an existing, already approved `TRAP_BossVisualEvent` server channel; do not create or subscribe to a second Remote or start another Heartbeat. This snapshot must never authorize combat or client state. The existing D07 single visual listener intercepts it **before** the old `GoroganVisualPolicy.apply`, since old policy does not accept this kind. Feed only existing `VisualPolicy.state.active==true`; the resulting remainingSeconds is for **visual presentation only**.
4. Existing START/STOMP/END authority remains unchanged. When the new contract is enabled, the local STOMP `now+2` must not override or re-enable the display after the stamped deadline; if the real PC code cannot guarantee that single display authority, do **not** enable the helper. Existing damage resolution, attack receipt, server current round and physical hit time remain wholly server owned.
5. For late packets arriving beyond the deadline, return `LATE_EXPIRED`; show no delayed telegraph. This can cause a late-arrival to see no warning at all; record and review game fairness separately. An incident of 0.93 s remaining **could be expected** for a 1.07 s late delivery, while a live round entrant losing 1.07 s due to unexpected sync gap requires repair in the actual PC source.

## Negative tests and metrics

- Two clients both participating before S1 warning: server `coreNow`, `windupEnds`, `sentServerTime`, `warningEndsServerTime`, each client `recvServerTime`, first rendered frame, last rendered frame; identify late join vs delay vs emission bug. Compare max drift to measured synchronization and render tick; avoid assigning a blanket PASS from a single run.
- Both clients must display remaining warning that does **not exceed the authoritative actual hit deadline**; no repeated `now+2` and no duplicate STOMP callbacks. At least one direct compare with actual `STOMP_RESOLVE` receipts, actor HP before/after and distance.
- Test true on-time 2 s warning, delayed 0.93 s projection, late-after-impact suppressed, spoofed/wrong match/event/epoch/attackId/stage, replay, reversed server clock, client clock discontinuity, server cancelled round, visual END/retire, start of new round; no extra client listener nor boss AI.
- Isolate other NPC/tense combat to ensure any HP loss comes only from authoritative actor HP and one true damage receipt. Test safe zone, wall, immunity, dodge, round end, fake Remote and replay independently.
- Landscape iPhone emulator warning ring, FPS/HUD, 2-client real Play/Stop, normal Edit/save and **only owned Studio PID** terminated. Physical mobile remains NOT_TESTED until physical phone QA exists. Preserve new SHA and evidence in #213/#218.

## Strict boundaries

No game release, main/direct push, merge, extra costs, P0-A/B/C CAS/auth/review bypass, other ChatGPT author branch changes, or modification of five existing Automations. If protected GitHub write gating blocks remote game results, keep genuine PC checkpoint local and report `GITHUB_UPLOAD_BLOCKED_PROTECTED_GATE` rather than bypassing controls.

**Source QA does not imply any native Luau or Studio acceptance.**
