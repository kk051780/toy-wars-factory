# GQ8 Realm compact touch HUD — 2026-11-18

Scope: only existing #764 RealmBattleControls LocalScript UI positions and height; no new Game/Combat/Host/Score/Store/Remote/gameplay authority. Original author source pinned by Git blob 058af03e9f43ac9aa45e8833d7bd99534902189d.

## Real defect
Original panel is 218×290 px even if active mode allows only one HYDRO, CANNON, BREATH or GUN button. This covers much of a narrow Android screen, conflicting with FB-001 minimal in-battle HUD. Source-observed, not visual Studio evidence.

## Candidate change
- FIGHTER: preserve pitch/up/down, gun, bomb, weather warning; 218×260.
- SUBSEA/SHIP/SEA_BEAST/SKY_BEAST/AIRSHIP: only already authorized weapon visible at y=34; panel 218×90.
- Re-layout only on mounted-kind transitions; no change to input, damage or server authority.

## Source QA / integration
verify_compact.py rejects original SHA drift and any delta outside one-client UI patch, checks actual 36-source composition (35 others exact), and keeps original31 OFF rollback. GitHub Action runs pinned native Luau and Rojo Source/Class for ON36 and OFF31.

CLAIM=GQ8_REALM_COMPACT_TOUCH_HUD_20261118. Baseline formal RC f77b4d4393d9e9b19b65566413432a7a9f13962b; original author #764. This remains SOURCE_PREP until unique authenticated B writer #220 integrates on latest RC with nonforce expected-SHA CAS and new-HEAD CI. No main merge, Roblox Publish, billing, Studio success, or automatic author ACK requirement. If mobile layout undesirable, OFF restores exact original #764 client. RED on source lock/native/Rojo/session authority drift; YELLOW for pending device UX.

8-domain scope: improve Field+Battle visibility only; Character, Castle, Neutral, Items, Lobby, and Balance preserved without claiming their engine-level acceptance. Studio 2-client/Android15m/ART/FUN/OWNER remain NO_GO.
