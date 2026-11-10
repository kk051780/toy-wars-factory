# Security and authority boundaries

- GitHub package is encrypted, not executable by itself, and never grants automatic Windows PC or Roblox permission. Decryption key only to OWNER private chat.
- `integrationApproved=true` is an installation guard, not proof of event origin. A genuine trusted RoundCoordinator, source review and executable Luau tests must validate canonical `BOSS/GOROGAN` event and server timer.
- Pathfinding can yield. Recheck identity and event epoch before `Humanoid:MoveTo`. No teleport fallback. Multi-client requests must never control a boss via Remote.
- Humanoid ownership set to server via `SetNetworkOwner(nil)`; failure aborts the rig. Only a PC Studio test can confirm R6 rig actually walks, renders, collides and recovers from path failure.
- Attack window opened only around real Core `STOMP_RESOLVE` emission. Damage gate must recheck server player identity, round, attack receipt, safezone, line of sight, distance, immunity and character immediately before `TakeDamage`.
- No attack permits more than 8 HP per target; attack count max3 and damage ledger max72 participant receipts per event. These are *integration reference limits*, not Roblox-certified guarantees.
- No DataStore, real payments, Robux products, player analytics/PII, main or release behavior.
