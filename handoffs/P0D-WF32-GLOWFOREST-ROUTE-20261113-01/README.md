# WF32 ひかる胞子樹海 — isolated original gameplay field prototype

EGG RAID RUMBLE / TRAP_RAIDERS / p0d-siege-v19
**Status:** SOURCE_CREATED; unpublished Studio-only *standalone* playable geometric route; NOT existing H1 Game adoption, NOT dual-client/Android/human FUN verified.
**Claim:** #219 comment 6846857141; design #219 comment 6846802690; #250 selection and sole #220 RC pending.
**Root:** handoffs/P0D-WF32-GLOWFOREST-ROUTE-20261113-01

## Real prototype behavior
- Real collidable ground at z=0 always passable, symmetric north passage at z=42 with equal left/right approach.
- Both sides can use a nearby glowing E/tap ProximityPrompt to open a real collidable root-gate for 7s; server checks own HRP distance <=12 studs, living Humanoid and 11s cooldown.
- Ten mushrooms, six moving low-part ポコスポ minions, moving elite ツタハンター with 1.5s periodic **purely visual** warning, crowned floating 樹冠王モリノス. All three archetypes are noncombat silhouettes, NOT actual existing Game enemies.
- No second egg/score/HP/XP/reward/save authority, no third egg mode. Own game code stays untouched. No purchased access.
- Only executes inside Roblox Studio (RunService:IsStudio()) to prevent accidental public gameplay mutation.

## Testing
python -m unittest discover -s tests
rojo build default.project.json -o WF32-private.rbxlx
Do not overwrite OWNER's source/Place. Open as private test only. Verify both approaches, physical gate, always-open road, mobile prompts, collisions, Output, and correct Studio close.
Current authored Python checks are **static**; neither they nor native Luau/Rojo/Studio have been proved executed by this package yet.

## H0→H1 and downstream contract
H0: immutable #288 v5 original H1 full Game and MapBuilder unchanged.
H1: when #250 and #220 select S2+ version, integrate just one optional forest area, retaining original one Game/Remote and existing MapBuilder geometry authority. Reconcile field name with #222 atlas and existing WF02 root path. Do NOT copy this full standalone world into existing map unreviewed: castle walls/route lengths and egg-carrier emergency exits need actual geometry QA.
Visible elite tell needs future server combat director hookup; this preview does not damage players, bind, award XP or grant an obtainable beast. Future minion/elite/boss combat must extend original #288 server-authoritative Horde module, not run separate damage.
Safety gate: per-round reset; door must not entrap egg carriers; symmetrical routes/no paywall; low-part streaming/mobile performance benchmark; fail-open or safe carrier evacuation if adopting door; independent source tests, actual 2client and Android human FUN are mandatory.
Rollback: leave source unmounted (H0).
