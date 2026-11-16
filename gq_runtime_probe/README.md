# EGGRUMBLE #470 — Studio live observer (isolated candidate)

This module **does not change or create game systems**. It observes existing #482 V3 gameplay in a private Studio session and collects supporting measurements for independent product-quality review. It cannot grant product PASS.

## Strict non-overlap
- #482 owns seven classes, field, castle/eggs, battle, neutral, items and lobby.
- #484 owns source-composition work.
- #485 owns ART and its mobile LOD.
- #487 owns scoreboard and results.
- #488 owns the external GQ01–06 evidence validator.
- #220 is the only authenticated official RC integration writer.

Only the new gq_runtime_probe/ path belongs to this candidate. No original source file is replaced.

## Private Studio use
1. Open the source-locked private Studio V3 Place based on the current #482 original game; do not add any alternative game host.
2. Add EGGRUMBLE_StudioLiveObserver.server.luau as ONE Script inside ServerScriptService.
3. Press Play and exercise both TEAM and BATTLE_ROYALE. Use the seven roles, real attacks, castle/egg actions, live neutral units, item pickups and the lobby. The observer attaches to live TEAM_Arena and BATTLE_ROYALE_Arena.
4. From **server-side Studio Command Bar**, read:
   game:GetService("ServerStorage"):WaitForChild("EGGRUMBLE_StudioLiveObserver_JSON").Value
   It updates every five seconds. Preserve it together with an actual video, the original Source SHA, the Place SHA256, device, test date and observer identity for later independent evidence review.
5. Remove only the observer Script/JSON StringValue when done. No production game scripts, Remote, stores, assets, balancing or Publish permissions are altered.

## Metrics and evidence limitations
- Server-observed neutral/bot Humanoid HealthChanged and Died events, consumable item part CanQuery true-to-false transitions, castles, physical routes, visible item parts, egg parts, neutral models, bot models, stone giant and ART Part counts.
- Server player attribute aggregation: selected/equipped role, queued mode and credited neutral KO. These **must not be mistaken** for authenticated score awards or the source of every damage event.
- Not measured by this code: authoritative castle HP, actual deposited-egg score, causal item benefit, 7-role skill effectiveness, visual aesthetics, actual Android FPS/thermal, child first-3-minute fun, OWNER acceptance, or certified RC inclusion.
- Part counts do not certify that a path is traversable or a castle door works. Actual Studio play and video still required.
- Always returns OBSERVATION_ONLY_PRODUCT_NO_GO. This is an instrument, not automatic gameplay acceptance.

## Tests and handoff
Execute: python -m unittest discover -s gq_runtime_probe/tests -v

These tests only validate the observer's source structure and prohibited mutation patterns; they do not run Roblox Studio or the native Luau VM. #220 may selectively include the observer in a test-only RC build after path claim, latest-source SHA, provenance, rollback, and authority checks. The official RC is not changed by this candidate.

Rollback: remove one Script from ServerScriptService; its ServerStorage JSON StringValue disappears with the test Place. No live game paths are changed.
