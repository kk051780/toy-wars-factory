# P0D-LOBBY-TRAINING-001 — V4 free-focus-cap training scheduler

**Isolated source only; neither selected for official S1 RC nor Studio-tested.** This has no facility/3D place, no XP writer, DataStore or monetization. Another author has already claimed BEAST+WEAPON station/XP work, so this packet ONLY models the six-way training selection policy.

## Player behavior
- On any auto-training station, a free user can choose a skill for **30 minutes total per Japan-time calendar day (00:00 JST reset)**.
- After this budget is exhausted, continue earning XP without interruption by changing among the six skills **every 10 training minutes**. A deterministic shuffled bag prevents duplicate streaks in each 6-slot cycle; all six become available for free.
- The user's saved selected skill can resume when the focus clock resets on a new day. When offline, no training XP is granted in this module.
- Verified real same-server Roblox friends add proposed +25% XP per friend, capped at four (+100%). Friends can be on other facilities or fighting; zero friends get ordinary XP.
- **Future, unapproved commercial hypothesis only:** purchase unlimited time to select a preferred skill; no increase in base XP/sec, no exclusive max level, no paid RNG, no actual product, receipts or shop.
- Free training never gates match entry. Roblox idle disconnect behavior is not bypassed.

## Integration contract
- Server constructs `newState(userId, trustedServerUnixSeconds, profile.trainingV4)` after an existing profile is loaded. This resets session `lastTick` so reconnecting does not give offline credit.
- Server calls `selectSkill(state, skill)` on a rate-limited legitimate station command (selection may be changed while quota remains).
- Before any station exit, friend arrival/departure, round transition or periodic server tick, call `settle(state, trustedServerTime, actualStationActive, serverVerifiedFriendCount, serverAuthorizedUnlimitedFocus)`.
- This returns an updated state and segments `{skill, seconds, bonusBps, mode}`, where e.g. 12500 basis points means 1.25×. Feed segments through the **original existing XP/skill authority**, with deterministic fractional remainders, PvP normalization and safe reward caps. This module **does not credit XP**.
- Persist `snapshot(state)` inside the original player profile, batched; never create a parallel XP store or save per second. Roblox's current guidance favors in-memory buffering and conflict-safe UpdateAsync for shared user data.
- Friend verification adapter must run **server-side** (e.g. Player:IsFriendsWithAsync(otherUserId) under pcall with bounded caching). Count DISTINCT current same-server players, exclude self and exits; never accept friend count from clients.
- `settle` caps credit for a stalled tick to 120 seconds and never backpays offline idle. Use server-owned time, not client clocks. Day quota and cross-server double credit require the **existing session lock/atomic save** from the game: this pure module alone DOES NOT solve concurrent server sessions.
- Purchase entitlement is a trusted input for future review ONLY. In S1 preview always pass false. A paid product must not be enabled without a separate OWNER decision and purchase QA.

## Test evidence / limitations
An offline Python oracle/static source suite authored alongside this module passes 34/34 locally. This is **not native Luau runtime/Studio/2-client/Android certification**, nor independent QA. The actual current game Source/Game/Remote/XP/Store are untouched. An explicit #250 product selection and #220 sole-integrator acceptance are prerequisites to official RC installation.

Existing official S1 remains **75/100, FUN_NO_GO** as last documented. No main/merge/publish/real payments/extra spending/PC/CAS/P0ABC/automation changes.
