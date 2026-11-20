# GQ470 REAL69｜7職スキル動作 ART 改修（A候補のみ）

- Parent: #470 / #420 / #218 soft claim 7051834048
- Official source: `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f`; real artifact #14610422120, Run #44695199140
- Unique selected route: `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills` LocalScript
- Source OLD SHA256: `95e5dba544a759547ea41e8ecec1984317fc61b35281f4533b2323df1951491f`
- Source NEW SHA256: `bcc83fd61c4cac1e54f4fb5b2564e3bbb04fc74f0d645b989891b163e87adf7b`

## Actual player-visible change

One source-locked patch changes **existing** 7-role / A,B,C skill gestures only: 18% anticipation, 24% fast strike, 12% readable impact silhouette, 46% eased recovery. It also adds B/C role-specific body/hand accents for WARRIOR/MAGE/NINJA/TRAPPER/BUILDER/BEAST/ZOMBIE (NINJA is the stable internal ID; display remains Assassin/暗殺者), disconnects per-player CharacterRemoving observers on exit, and clears residual procedural poses on leaving the 130-stud visible budget.

No Parts, particles, new loop, Roblox assets, duplicate client, RemoteEvents, gameplay attack timing, damage/HP, score, Store, skill authority or publication. Existing max 16 animated avatars and `DURATION={A=.26,B=.48,C=.82}` retained. Studio-only source remains intentionally Studio-only.

## Provenance and rollback

`ROLE_MOTION_REAL69.patch` applies with zero fuzz exclusively to original selected 6764-byte Luau; a changed base hash causes RED, never blind reapplication. `gate.py` fetches genuine 69 route/class/hash proofs, checks one changed route/68 byte-exact, creates `OFF69_SOURCE_EXACT`, and rejects 4 mutation negatives. CI runs original + candidate Native Luau 69/69, pinned Rojo ON/OFF and exact OFF Place. B receives **one selected source + route/SHA manifest**, not a PR-merge request.

Local original REAL69 source verification: **PASS**. A candidate source 8282 bytes; original 6764 bytes. XML candidate Place formed from the real 798390B official Place for independent non-engine static sanity only: 802178B. These numbers do **not** establish Studio or Android performance.

## Official adoption conditions

This branch/PR is a proposal, not the formal RC. #910 P0 one playable match and #931 ART6 review have priority. Only #220 authorized writer may adopt the single verified source after #250 value decision, a fresh formal RC HEAD, exact source lock, nonforce expected-SHA CAS, same HEAD full CI and rollback. Do not merge this entire PR into RC/main. Check motion against server skills in actual Studio Solo + 2 clients, 8 fixed scenes old/new x PC/Android = 32 real images, Android 15m and OWNER acceptance. Until then `ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / OWNER_ACCEPTED=0`.