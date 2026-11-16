# EGGRUMBLE V3 — 卵運搬者の小型ワールド表示（独立GQ候補）

**Scope**: \`quality_gameplay/carrier_world_tell_20261116/**\` only. Original author 21 scripts (PR #482), AI #502, score #487, art #485, item #489, HUD compass #496, hit effects #503/#504, sole RC writer #220 **unchanged**. Source parent is fixed to PR #482 \`fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9\`. This is **not official RC or public deployment**.

## Playable change (not a new HUD)
Server's **real** V3 \`session.rules.castles[id].heldEggs\` drives one world-space Billboard per human or AI carrier (1–3 eggs), at most 70 studs away, behind solid geometry, in TEAM/BR arenas. Updates every 0.3 sec, only when actual carrier quantity changes. Does **not** write to damage, rewards, scores, inventory, egg IDs, NPC actions, shop or session state. No new Parts, RemoteEvents, paid assets or constantly visible HUD. Displays even for an egg-carrying Assassin: existing stealth remains for movement, but cannot conceal the objective completely. For phones, 16 carriers max: 16 compact labels, no per-frame rendering listeners.

**Safety**: dead player, destroyed castle, zero eggs, empty actor, other match, match end, replay lobby or destroyed arena => no label. AI character replacement and human respawn delete stale labels; cleanup handles replay. Never infer egg possession from client attributes.

## Build against the original
\`python3 quality_gameplay/carrier_world_tell_20261116/compose.py --out /tmp/eggrumble-carrier-private\`

Outputs a separate **23-source** Rojo project plus exact-source SHA-256 receipt and one generated copy of the original lobby server. The original Game file's Git blob SHA is checked and refuses drift. Exactly 2 injection statements in generated copy, no edits to the author source: require this optional module and call \`CarrierTell.start(session)\` after the original \`BotActors.start\`. Both authored new ModuleScripts are sibling scripts in ServerScriptService. Reuse base gameplay for characters, field, combat, castle, neutral, items and lobby; this slice adds only visibility/fairness.

## Verification and intake status
- Python source-exact and negative contracts; Native Luau compilation of both scripts and actual Luau VM tests of the **same** policy source.
- GitHub Actions emits private *source-only* Rojo config+receipt; not a real Studio-tested .rbxlx. A compiled Place, Studio with 1 human+15 AI, simultaneous TEAM/BR, real line-of-sight with walls, low-end Android FPS/ART, 15-min endurance, OWNER fun test remain **NOT RUN** until measured.
- RC merge requires sole writer #220 CLAIM, current HEAD, source-lock, CAS, same-HEAD Rojo/Place, rollback, #420/#470/OWNER. **Never auto-merge, push official RC/main, publish or spend money.**
- Rollback in private preview: remove only \`EGGRUMBLE_CarrierWorldTell\` and \`EGGRUMBLE_CarrierTellPolicy\` plus two generated host hook lines.

**Implementation progress**: original module + pure policy + private source composer + regression QA committed to isolated branch; RC adopted 0 until #220 proves otherwise. No false Studio or product GO claim.
