# CHECKPOINT / RESUME — S1 Chat integrator

RELEASE_ID: `P0D-S1-KIDS-RC01`
BRANCH: `rc/p0d-s1-kids-rc01`
WORK_ID: `p0d-siege-v19`
SCOPE: chat-assembled, source-first standalone S1 playable vertical slice, not final RC and not owner PC latest Place.
CURRENT SOURCE: new LuaU project under `releases/P0D_S1_KIDS_RC01/` with its own `default.project.json`.
LATEST STATE: initial complete source path for S1 eggs/castle combat/match/roles/HUD/2-player map authored. Pure Python and static tests executed; true Studio/native Luau not run. Team and round authorities owned by `Game.server.luau` exactly once.

## Next phase for same Chat or successor

1. Read #218 (top/latest), #220 (including comments), #217, #213 latest actual PC evidence. Only ONE Chat integrator may write RC branch. If claim belongs to this lane, resume or explicitly hand off; otherwise work in separate feature branches.
2. Retrieve this RC's final fixed Git commit and verify `BUILD_MANIFEST.json` entire source. Do not cherry-pick another original/CLEANROOM pair without reviewed signatures.
3. Critically evaluate game playability: D07 authentic Gorogan boss rig/AI/visual, shared D08 event authority singleton, D11 neutral capture, seven-job game choice, S1 castle geometry, death/timeout/reconnect, mobile HUD and quest tutorials. Integrate accepted originals with real Luau imports/source mapping and targeted offline QA. Do not add duplicate round/event/reward owners.
4. Run independent CHAT_QA on final S1 source, not just individual pure-unit oracles. Register issues and fix within chat. Only after playable full composite RC and independent QA, mark CHAT_RC_READY and request final owner Windows Codex Studio check once.
5. If latest real Windows PC source differs or is newer, do not overwrite. Current branch is not an exact or complete derivative of owner's stored v43-A Place.

## Explicit outstanding

`GAP-D07=ORIGINAL_BOSS_NOT_INTEGRATED`
`GAP-D08=ORIGINAL_CANONICAL_EVENT_NOT_INTEGRATED`
`GAP-D11=ORIGINAL_NEUTRAL_NPC_NOT_INTEGRATED`
`GAP-PERSISTENCE=S1_ROUND_TRANSIENT_ONLY`
`GAP-PC-LATEST=UNKNOWN`
`GAP-LUAU-NATIVE=NOT_TESTED`
`GAP-STUDIO-2CLIENT=NOT_TESTED`
`GAP-MOBILE=NOT_TESTED`
`GAP-INDEPENDENT-CHAT-QA=NOT_TESTED`
`GAP-LIVE-PUBLISH=NOT_APPROVED`
