# EGGRUMBLE GQ Objective Compass (independent source-only candidate)

FB-003 / FB-014: new players can lose track of the egg-steal / return goal on the expanded field. This is **real client Luau**, not another game engine, item system or score implementation. The official RC is untouched.

Source: EGGRUMBLE_ObjectiveCompass.client.luau
- The client observes the existing #482 V3 Workspace arena (TEAM or BATTLE_ROYALE) and the existing selected-role Player attribute.
- One concise screen line and one non-AlwaysOnTop world marker point to a valid enemy EggVault; nearby existing field pickups and the neutral Stone Giant take priority.
- TEAM marks a castle as enemy only when it is across the existing battlefield center line, so an ally's castle cannot be marked as hostile by default. If the layout changes, the rule fails closed.
- The UI is invisible in the lobby and auto-collapses after 18 seconds in the battlefield. PC G key and a small touch button reopen it. Refresh no more than once every 0.8 seconds.
- All labels are client-side. There are no new remotes, server scripts, rewards, damage, AI, or castle/item ownership mutations. Distances use Roblox studs.
- The V3 server does NOT expose reliable carried-egg count to the client. Accordingly, guidance explains both steal and deposit, rather than falsely asserting a player is carrying an egg.

Independent Rojo project: EGGRUMBLE_GQ_OBJECTIVE_STUDIO.project.json includes original #482's 21 source paths **directly, without modification**, plus the new LocalScript = 22 source files. Its dedicated CI performs original-source preservation tests, pinned native Luau parse, checksum-locked Rojo build, and embedded source-exact verification. It never publishes to Roblox.

## Cross-area, non-overlapping contribution

| Category | Objective Compass addition | Existing owner |
| --- | --- | --- |
| Characters | Compact selected-role identity | #482 skills, movement and weapons |
| Field | Spatial heading and stud distance | #482 / #485 world |
| Combat | Enemy objective orientation | #482 / #484 combat |
| Castle / eggs | Enemy EggVault and return-home explanation | #482 server egg authority |
| Neutral | Nearby original stone giant marker | #482 boss / #484 AI |
| Item | Actual nearby unconsumed pickup marker | #482 item effects |
| Lobby | Remains hidden before match | #482 lobby |
| Balance | One marker, throttle, auto-hide | #487 scores |

## Integration contract

Base fixed at #482 author commit fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9. Recheck all current #482 / #484 / #485 / #487 HEADs before composition. #218 unique-path CLAIM requested in comment 6906374899; CLAIM_GRANTED is NOT yet verified. Draft PR only; no merge, main change, official RC write, publish, payment or Windows control. Only authenticated #220 writer may source-selectively adopt into official RC with fresh CAS, same-HEAD CI, actual Place byte/SHA and rollback.

Rollback: omit EGGRUMBLE_GQ_ObjectiveCompass from StarterPlayerScripts (other 21 scripts unchanged). Studio, Android, competitor, ART/FUN and OWNER acceptance are NOT_TESTED/NO_GO. Verified source is not verified gameplay.
