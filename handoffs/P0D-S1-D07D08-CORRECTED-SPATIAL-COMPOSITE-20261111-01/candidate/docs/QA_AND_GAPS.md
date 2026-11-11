# S1 Chat-first source integration QA / outstanding gaps

## What may be asserted

- Luau source and project file exist, with a server match authority, server map, client HUD, a shared configuration module, server objective/combat validation and canonical one-event sequence.
- Python standard-library reference model and static source checks pass if local test report says so.
- This does **NOT** attest Rojo sync, Luau native compile, Roblox Studio multiplayer or mobile, actual data persistence, or approved Roblox game launch.

## Unresolved before `CHAT_RC_READY`

1. Reconcile this standalone source-built S1 implementation with latest actual Windows owner game Place and original D01/D06/D08/D11 source. This is not yet an original-source package merge. Choose one round/event/damage authority. Preserve saved v43-A and D07 integrated source as historical immutable baseline.
2. Original D07 Gorogan is missing: true boss rig movement, client mesh, the 2-second warning clock issue reported in earlier PC QA, one authentic attack damage receipt and cleanup. Current `WARNING/SIGNAL` is an unrelated cosmetic alarm, not a pass for D07.
3. User-facing richer lobby, music/sound, team change, match objectives tutorial, more content, accessible reduced-motion settings, death HUD, physical mobile QA and network disconnect recovery need independent Chat/source implementation or final Studio testing.
4. No DataStore/write semantics are implemented in this S1 demo. Round state and scores reset after match; no paid items. If persistent progress is added later, offline failure/replay tests are mandatory.
5. Chat-independent QA needs to read immutable final build commit, verify source/module wiring and feature completeness, then issue its own receipt on a separate branch.

## S1 offline regression targets

- Prevent a third client from dictating arbitrary damage/position, repeating a stale seq, attack spamming or scoring from afar.
- Stealing own egg, stealing a held egg, scoring the wrong egg, scoring while own egg is stolen, multiple egg carriers, death/quit cleanup, cross-team attack, spawn invulnerability.
- Role-change heal exploit while active, spectator/non-team intents, stale match result/restart, no minimum players, falling into void without permanent soft-lock.
- Single match/event/damage owner. Only one `OnServerEvent` entry. No duplicated boss or second event chooser.

## Windows final QA (only after whole RC ready + direct OWNER request)

Native Luau load and Rojo source path, Studio Play/Stop, owned client/server PID normal exit, 2+ clients touch & desktop, real ProximityPrompt and melee hit geometry, coin/reward if added, fake remote and excessive event replay, join/leave and egg carry cleanup, 2 capture vs castle destruction, timer draw, no accidental experience publish. Preserve newest owner PC Place/HEAD/checkpoint before any import. `StudioStatus=NOT_TESTED` until actual logs.
