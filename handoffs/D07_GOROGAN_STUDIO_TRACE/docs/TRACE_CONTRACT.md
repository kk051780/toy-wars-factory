# D07 Gorogan — sanitized Studio server trace contract v1

This tool is **not an engine test** and does not modify `GoroganServerRuntime`, `GoroganRigDriver`, the v40 event chooser, the local PC build or Roblox Studio. The validator only checks supplied event JSON for logical consistency. Any values in a JSON file can be forged, so a PASS **never constitutes real Studio QA**. OWNER Windows Codex must independently establish the source log and actual saved Place hashes.

## Scope and source

The source of normalized events must be the **server** in the owner's unpublished Studio game. Record a single S1 match and one Gorogan, with >=2 clients. Do not log or publish actual user IDs, names, account identifiers, place files, game scripts, private configuration, private keys or unredacted Output. Tokenize player identities consistently (`ANON_P1`, `ANON_P2`), and choose anonymous round/boss/attack IDs. Keep the original local raw server Output/private evidence on the PC. The sanitized JSON alone cannot prove identities or server origin.

Top-level keys:

| Field | Value |
|---|---|
| `schema` | `P0D_GOROGAN_STUDIO_TRACE_V1` |
| `game_id` / `work_id` / `feature_id` | `TRAP_RAIDERS` / `p0d-siege-v19` / `D07` |
| `stage` / `environment` / `trigger_mode` | `S1` / `UNPUBLISHED_STUDIO` / `SERVER_QA_ONLY` |
| `round_id` / `run_id` | Stable anonymous `[A-Za-z0-9_-]` IDs, max64 |
| `trace_origin` | `SYNTHETIC` or `STUDIO_SERVER_OUTPUT` (self-claimed, not authenticated) |
| `clients` | 2, 3, or 4 |
| `place_sha256`, `source_sha256`, `output_sha256` | Lowercase 64-hex digests of the actual **local saved Place**, source set and separate retained raw server Output log |
| `evidence` | `saved_place_sha256`, `local_source_sha256`, `log_sha256` matching the top-level values; `stop_edit_save: true`, `owned_studio_pid_exited: true` — these claims must be checked against actual Windows evidence separately |
| `events` | 5 to 1,000 ordered events; `seq` consecutive from 1; `ms` monotone relative time, nonnegative integers; `authority: SERVER`; `round_id` matches root |

## Accepted event sequence

- `ROUND_START` then `TRIGGER` with `mode=SERVER_QA_ONLY`, `source=SERVER_TEST_COMMAND`; this is **an isolated server-only debug signal**, never a normal client Remote or production event scheduler.
- Exactly one `SPAWN`: `boss_id` token, `server_owned: true`, 3D numeric `pos`. Boss identity is carried on every subsequent boss event.
- `NAV_REQUEST`: `mechanism=PATHFINDING_MOVETO`, at most 20, >=750ms between requests; at least one must occur. No other pathfinding hooks are authored by this tool.
- `MOVE_SAMPLE`: actual server-observed HumanoidRootPart `pos`, `source=SERVER_HUMANOID_ROOT`, `server_owned: true`, `grounded: true`, `root_anchored: false`. At least 0.5 studs of observed movement, peak sampled speed <=16 studs/s (plus small observation tolerance). **MoveTo *intent* alone cannot pass.** The verifier cannot detect short-distance physics glitches between samples.
- `TELEGRAPH`: new `attack_id`, both `visible_blue` and `visible_red` true. Up to 3 attack IDs. Values report what the game instrumented, not actual human perception.
- `ATTACK_RESOLVE`: matching `attack_id`, 2,000–5,000ms after its telegraph, `receipt=CORE_STOMP_RESOLVE`, `fresh_server_snapshot:true`. This string must only be emitted by authentic existing Core dispatch, not a QA stub that lies about an event.
- `HIT`: immediately after matching resolve (0–150ms); target alias unique **per attack**, integer `damage` from 1 to 8; server LOS true, `safezone:false`, `invulnerable:false`, `target_alive:true`, `server_roster_verified:true`; 0 <= `distance_studs` <= `max_range_studs` <=12. Must capture actual post-authorized Humanoid damage, **not only an intention to hit**.
- `HIT_DENIED`: actual blocked attack after matching resolve, `reason` from `LOS`, `SAFEZONE`, `IMMUNE`, `STALE_ROUND`, `DEAD`. Include at least one negative case.
- `REMOTE_REJECTED`: reject an actual unauthorized client request; `reason` from `CLIENT_DAMAGE`, `CLIENT_BOSS_SPAWN`, `CLIENT_CFRAME`. Include at least one.
- `ROUND_END`, then `CLEANUP`: final boss instance count exactly 0, <=14,000ms after spawn, with no later gameplay events.

Boss events `NAV_REQUEST`, `MOVE_SAMPLE`, `TELEGRAPH`, `ATTACK_RESOLVE`, `HIT`, `HIT_DENIED`, `CLEANUP` all need the original `boss_id`.

## Verdicts and limits

- `SYNTHETIC_PASS_NOT_STUDIO_QA`: simulator example only. No Windows or Studio assertions.
- `TRACE_CONTRACT_PASS_NOT_STUDIO_QA`: supplied self-labelled Studio trace is schema/chronology/authorization consistent. **This alone is not trustworthy evidence** of actual NPC movement, visual perception, physics, damage, PC files, PID closure, network role or successful source merge.
- `TRACE_CONTRACT_FAIL_OR_BLOCKED`: reject or hold. CLI exits nonzero.

For human Studio acceptance, additionally inspect real private Output/video/client windows and PC file hashes. The game remains `PARTIAL_NOT_READY`; no release, merge, payments or P0-A/B/C bypass.
