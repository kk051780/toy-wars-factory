# P0D D17 — Privacy-first local metrics reference

Game TRAP_RAIDERS, work_id p0d-siege-v19, packet_id P0D-D17-PRIVACY-METRICS-20261110-A.

Purpose: enable truthful session-only KPIs for game iteration (first match completion, rematch intent, cosmetic preview), without collecting personal information or inventing D1/D7, users or revenue. NEVER assume Studio test sessions are real players. No Roblox AnalyticsService calls, networking, monetization activation or persistent identity. For production Codex must build a secure server-origin adapter, verify consent/retention/privacy controls and choose legitimate Roblox official analytics separately.

Trusted fields: event_id (random), session_id (ephemeral), round_id, timestamp, origin=studio/live, event allowlist. Client-supplied events must be rejected before entering this pure reference oracle. Start+end for same round and session constitutes completed round. Match metrics should be compared to a no-change baseline; observed zeros/unknowns are not profits.
