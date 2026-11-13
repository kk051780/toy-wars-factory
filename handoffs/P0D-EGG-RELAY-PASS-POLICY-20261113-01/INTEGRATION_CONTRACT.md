# P0D S2 proposal: EGG RELAY / 卵の味方パス

Scope: **isolated original Luau policy only**. NOT wired into the Roblox Game; NOT official #220 RC; NOT Studio-played. #219 is Product DRI and #250 decides selection. Do not block the S1 release or overwrite other egg/source owners (#273, #279, #288).

## The child-visible action
One player steals an egg; a defender approaches; a nearby teammate becomes the escape runner. Once a teammate is within range the carrier sees a single contextual "🤝 パス" action. After a verified handoff both teammates see "ナイスパス！"; the original egg and server score system remain unchanged. The carrier no longer holds the egg and the receiver has exactly that one egg. The receiver's existing waypoint should follow the egg. This moment is a hypothesis for stronger cooperative replay and shareable clips, NOT user-tested.

First proposal: 8-stud horizontal range, <=4-stud vertical separation, no walls, per-egg pass cooldown of 12 seconds, no pass while stunned or restrained. The opponent can intercept using existing movement, class actions, traps and NPC pressure. A pass confers no added HP, XP, damage, score, money, paid protection or loot advantage. No enforced tutorial or real-money button.

## Code now shipped
The original `src/EggRelayPolicy.luau` is pure Luau with `Relay.evaluate(world,request)`. It returns `false,reason` or `true,receipt`. It does **not** change the world, create RemoteEvents, spawn a second game, mutate a score, or transfer an egg. The only permissible future caller is the **sole existing server Game**, and the actual transfer must be carried out by that authoritative owner atomically without yield. Native Luau compilation and engine execution remain NOT_TESTED.

Trusted world fields (constructed afresh exclusively on the server):
- `phase="PLAYING"`, integer `roundEpoch`, monotonic `nowSec`
- `players[userId]`: alive, stunned, restrained, team, carriedEggId, serverPosition as {x,y,z} from HumanoidRootPart
- `eggs[eggId]`: id, phase="CARRIED", carrierUserId, relayEligible explicitly determined by the canonical 1-egg / 5-egg mode, transferSeq, optional lastRelayAtSec
- `lastAcceptedSeqByUser[userId]` (server-owned)
- `serverLineOfSightClear=true` ONLY when a fresh server-side raycast has confirmed the actual unobstructed player-to-player path.

Request fields: eggId, targetUserId, roundEpoch, expectedTransferSeq, seq; **actorUserId must be overwritten by the server from the actual Player.UserId**. Never trust a client-provided actor/team/position/range/LOS/carry state/timestamp. The client-supplied seq is compared to server state and requests are rate-limited by the existing Game handler separately.

Validation: exact epoch; active round; valid, distinct same-team alive players; sender owns exactly the authoritative carried egg; receiver holds no egg; both are unstunned/unrestrained; horizontal/vertical proximity; fresh LOS; per-egg 12s cooldown; expected transfer version still current; per-sender request sequence strictly increasing. Unrecognized or stale states fail closed. The result receipt contains egg ID, sender, receiver, round epoch, previous/new transferSeq, accepted seq and server time.

## #220 atomic integration recipe (not executed)
1. Obtain explicit #250 `PRODUCT_SELECTED_FOR_OFFICIAL_RC` *before* official admission. Freeze source SHA and official H0 rollback SHA. Consider S2/private preview first.
2. Add ONE new command to the canonical Game's **existing Remote** after rate limiting; player identity is the server's Player instance. No standalone event authority. Reconstruct world from existing current Game state, so legacy classic and five-egg modes use their actual canonical egg IDs.
3. Perform fresh server raycast using actual character positions and world geometry; if this cannot be verified, deny. Call the pure policy and immediately confirm the same egg still exists, its carrier/transferSeq/round match the receipt, and the receiver remains free.
4. Under the **same no-yield transaction**, update exactly one egg's carrierUserId, sender carriedEggId=nil, receiver carriedEggId=egg ID, transferSeq+1, lastRelayAtSec=server now, accepted seq. Do not invoke DataStore or async code during the mutation. Reuse existing egg drop/deposit/score/snapshot flows, never double-award anything.
5. Reconnect the existing server snapshots, Game HUD and mobile contextual action only after independent authority review. Show success only on the authoritative ack. Do not override forced drop, death/disconnect, score or replay rules.
6. Generate isolated complete private Place with actual canonical Game + manifest/source lock. Require #220 independent RC receipt and OWNER privately performed 2-client Studio and Android checks before any adoption statement.

## Necessary negative engine cases
Simultaneous passes, self-pass, cross-team pass, target already holding a different egg, target dead/stunned/behind wall/above caster, stale request seq or egg version, duplicate Remote, clock reset, death while pending, disconnect, round end, egg lost/swapped between request and commit, 1-egg and 5-egg modes, scorer's one-egg-one-owner invariant, HUD overlap on Android. Confirm that no legitimate egg can be duplicated or removed without normal drop handling.

## Product selection experiment
Once the private build exists, compare relay OFF/ON in same map with real human pairs and log: first-pass discovery, successful handoff, original player-to-score time, interceptions, fun 0–5, rematch desire, softlocks and server errors. Proposed human pass threshold average >=4/5 with no hard security/physics fails. Neither real FUN nor monetization is currently measured. Reject or revise if the action is confusing, prolongs matches, or trivializes roles.

## Delivery boundary and progress
- GitHub author branch: `feature/p0d-egg-relay-pass-policy-20261113-01`, unique root `handoffs/P0D-EGG-RELAY-PASS-POLICY-20261113-01/**`.
- Only isolated pure Luau policy / Python reference / Python tests / docs; no RC/main, no other branch, no Roblox Studio, publishing, paid switch, purchases or PC Codex work.
- Python reference tests are **not native Luau or Studio proof**. This source cannot be described as "a playable new game feature" until the sole #220 integration and actual human Studio acceptance.
- Current #220 S1 official progress stays last published 75/100 with FUN_NO_GO; S2 concept must not inflate it.
