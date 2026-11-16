# GQ-V3-BOSS-STOMP-WALL-LOS-20261116

## Root-cause, not a duplicate neutral boss
Original #482 `EGGRUMBLE_NeutralStoneGiant.luau`, immutable author HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, original blob `2670618cba320c51936c750a10e43c194cada0f0` checks LOS when players ATTACK its eye, but outgoing 28-HP stomp only checks radius 11 and vertical difference 8. Thus a player physically behind a collidable castle wall and inside the radius can take damage. Intended fix: one server-side ray from stomp origin to player root, exclude attacker model and target character, respect collidable walls, no damage through wall. Visual windup 2 seconds, radius, damage, active match, authorized player, one boss model all remain original.

## Ownership
Own ONLY `quality_gameplay/v3_boss_stomp_los_20261116/**` and dedicated workflow. The original #482 game, #484 AI/composition, #485 art, #487 score, #500 defense, #501 neutral quotas, #510 mage heal, #516 status and #517 items are NOT rewritten. No new Game, boss, HP/score/store/remote authority. #220 alone may source-select the resulting single patched boss module into the protected official RC after source lock, independent review, non-force CAS and same-HEAD official CI. Until then the resulting Place is **private / unpublished**, and official RC adoption = 0.

## Executable QA
1. `apply_stomp_los.py` pins exact original Git blob; rejects changed anchor, duplicate patch, or shadow-source mutation.
2. Python regression includes negative mutants and preservation of match/telegraph/attack contract.
3. `make_native_los_test.py` extracts ACTUAL modified Luau function and evaluates clear, solid-wall blocked, and zero-distance native cases using pinned Luau CLI.
4. `pack_private21.py` retains 20/21 original modules byte for byte, only source-selects `EGGRUMBLE_NeutralStoneGiant`; validates all 8 domains, builds real Rojo .rbxlx, and compares 21 embedded Script Source bodies exactly.
5. Original #482 author Python regressions run. These are source/native checks, NOT an actual Studio 1+15AI, 2+14AI, Android 15-minute test or kid FUN evidence.

## RC-gate remaining
- Author #482 reviews and ACKs change; independent Reviewer checks source/performance/security.
- #220 checks current official HEAD, existing competing overlays, only one true Game and no boss/HP duplication; then commits via authenticated non-force CAS to its protected RC branch and records same-HEAD Actions run, real official Place/ZIP bytes, rollback.
- Studio behind-wall boss stomp, TEAM+BR, 2-client and Android FPS/ART and first-three-minutes FUN all require real owner verification. NO ART/FUN/MOBILE GO until evidence. Roll back by reverting ONLY selected boss overlay, leaving all author baseline sources untouched.
