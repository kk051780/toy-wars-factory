# P0D-BATTLE-DOJO-BRIDGE-001 — 戦闘→修行→再戦の導線

**Status:** isolated source prototype; NOT SELECTED for official RC; Roblox Studio/Android/OWNER FUN NOT_TESTED. Native Luau/Rojo NOT_TESTED. Official RC remains unchanged.

## Player-visible change
After a match, show a dismissible 7-second result preview with server-observed eggs scored, PvE enemies defeated, rescues and one suggested next action: evolution if ready → hatch if ready → training if a currently deployed skill pad can level → rematch. Never block rematch, force a minigame, or require another click.

## Interface
`NextStepAdvisor.build(matchSnapshot, progressSnapshot, options)` is pure, read-only and has no service, network, DataStore or reward calls. Snapshot fields: `matchSnapshot = {won, eggsScored, neutralDefeats, rescues}`; `progressSnapshot = {canEvolve, canHatch, skillLevels}`; `options = {availableSkills, sameServerFriendBonus}`. Returns UI-only result+action+suggested skill. **Adapter and UI are not included**: sole RC integrator #220 owns eventual HUD connection.

## Compatibility and ownership
H1 only has BEAST/WEAPON pads; default availableSkills is exactly those two. Six skills are only shown if #220 supplies a verified list from the separately owned V4 six-skill scheduler. No extra game mode. Existing B42 eggs, Musou V7, Game/Remote/round/HP/score/XP/store and same-server 1.5x friend/<=20% PvE skill bonus are untouched. PvP effect unchanged. No paid purchase UI or random outcome.

## Private A/B acceptance (proposed, not real measured)
H0 = current results; H1 = optional read-only card. In >=10 private-play sessions, seek >=8 users understanding their earnings and able to replay immediately. Inspect actual 1st-round rematches, training choices, first-90s egg touch, 2client, Android clipping, stale round display and no duplicate XP. This is a design hypothesis, not a platform benchmark or a claim of measured retention.

## Gates/rollback
`IDEA=written; SOURCE=isolation branch; PYTHON_STATIC_QA=9/9 locally; NATIVE_LUAU=NOT_TESTED; ROJO=NOT_TESTED; official_product_selected=NO; RC_ADOPTED=NO; STUDIO=NOT_TESTED; OWNER_FUN=NO_GO_PENDING`. To adopt: #250 selection → #220 source/contract/authority review → real RC build/QA → OWNER private Studio play/FUN. Remove optional advisor mount for rollback; original Game unchanged. No main, merge, Roblox publish, payments or spending.
