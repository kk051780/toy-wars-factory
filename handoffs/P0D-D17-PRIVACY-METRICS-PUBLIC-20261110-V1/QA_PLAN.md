# QA gates (Windows/Roblox NOT_TESTED)

1. Verify existing PC CHECKPOINT/PLACE source SHA and v37 final QA before integrating. v39 first. Do not alter main/PR/protected auth gate.
2. In isolated local Studio, record server-confirmed session/round IDs (rotating per session), and server-attested round start/end and UI clicks; no player names, raw account IDs, IPs, chat or cross-day tracking.
3. Confirm Studio sessions do not influence real players' metrics; run rematch, noncompleted round, duplicate/replayed client requests, round cancel, disconnect and repeated joins.
4. Export only aggregate counts/ratios with sample sizes and explicit UNKNOWN for D1/D7 retention/sales until reliable first-party production data exist. No real purchases, paywall, Robux transactions or new external telemetry service.
5. Profile mobile and 2client; record UI and performance. Validate actual Roblox official AnalyticsService availability only in appropriate authorized environment; NOT_TESTED otherwise. Stop/Edit/Save/Quit own Studio PID only.
