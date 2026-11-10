# TRAP RAIDERS — D07 synchronized stomp-warning deadline (keyless optional reference)

`game_id=TRAP_RAIDERS` / `work_id=p0d-siege-v19` / `packet_id=P0D-D07-GOROGAN-SYNCED-WARNING-DEADLINE-20261111-01`

This is NEW standalone, disabled-by-default reference source and is **not** a migration of any old encrypted archive, nor a modification to the actual Windows Studio game. It uses the OWNER-approved `PUBLIC_SOURCE_V1` protocol: raw Luau/Python, tests, QA notes and SHA manifest, on a unique public handoff branch.

## Why this exists

Real PC S1 two-client report #213 comment `6776360480` observed 1.92 s at server, 1.96 s blue and 0.93 s red. The red duration could represent a legitimate late join or measurement start mismatch, not necessarily a rendering defect; the report is **PARTIAL_NOT_READY**. Original exact D07 `GoroganServerAICore` returns STOMP_WARNING containing `windupEnds` in its authoritative server engine time. Original `GoroganCombinedRuntime` drops `windupEnds` when forwarding a visual STOMP packet. Original `GoroganVisualPolicy` then sets local `telegraphUntil=client_os_clock_now+2`. That can visually extend a late warning past the actual server impact if it is used unmodified.

The proposed sidecar transports the absolute **synchronized server-clock deadline** instead of restarting a local two-second countdown. It creates no new game scheduler, event chooser or clock source. The server adapter obtains both `coreNow` and `workspace:GetServerTimeNow()` together at actual Core STOMP_WARNING emission and issues `{sentServerTime,warningEndsServerTime}`. The existing trusted client visual listener uses `workspace:GetServerTimeNow()` to project remaining time; the same value is also logged to distinguish network delay from a missing server warning.

## Deliverables

- `luau/GoroganWarningDeadlineServer.luau`: pure `Server.new(config)`, `.stamp(state, originalWarning, originalServerClock)` and `.close`, validates genuine round/event, integer attackId 1–3, non-regressing clocks, owner opt-in, <=2.05 s deadline and replay.
- `luau/GoroganWarningDeadlineClient.luau`: pure `Client.new(...)`, `.accept(state, approvedPacket, syncedServerNow, originalVisualActive)`, `.remaining`, `.close`. Reuses ONLY the existing server-authenticated visual feed, refuses stale/expired/replayed packets, and never invents another 2s window.
- `tests/oracle.py`, `tests/test_deadline.py`: independent executable Python oracle with 50 tests, including 1,000 deterministic latency variation cases. Static checks ensure no RemoteEvent subscriber, NPC/HP mutation or event chooser.
- `docs/OWNER_PC_QA.md`: fail-closed owner PC integration checklist, metrics, and protection constraints.
- `BUILD_MANIFEST.json`: source byte size/SHA-256.

This candidate **does not** implement a true server-authoritative client heartbeat or UI renderer, or auto-patch original VisualPolicy: the OWNER's actual Windows Codex must preserve the latest PC Place and install only a proven necessary minimal adapter. It must never use a second `TRAP_BossVisualEvent` listener or parallel independent boss AI/chooser.

### Immutable original inputs consulted, never changed

- D07 exact original AI `d65adccef6ce08ec48854ff2cc99f77e69e0765e` (STOMP_WARNING `windupEnds`).
- D07 exact original combined `80a1f0ce15adfb475df0c95677f9966bb760a8ae` (visual STOMP drops engine deadline).
- D07 exact original visual `e9b0a7496a69bda3e0e6527ff4d112d50cf70e80` (client `now+2`).
- Real PC report: https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6776360480.

Status at authoring: offline Python source tests PASS; no native Luau, owner PC intake of this candidate, Studio 2-client, phone testing or normal Studio exit performed by this chat. If the actual PC implementation already has a satisfactory authoritative deadline contract, **NO-OP** and do not deploy this optional sidecar.
