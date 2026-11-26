# EGGRUMBLE V3 — boss shockwave wall occlusion (GQ non-overlap)

**Scope/claim:** `GQ_BOSS_SHOCKWAVE_WALL_OCCLUSION_20261116`; #218 SOFT claim comment 6908767688, **not GRANTED**. **Not merged, not the official RC, and not Studio/Android tested.** Original game author #482 / composer #484 / B only authenticated RC writer #220 retain their respective authority.

## Reproduced source defect

Original #482 `EGGRUMBLE_NeutralStoneGiant.luau`, commit `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, Git blob `2670618cba320c51936c750a10e43c194cada0f0`, telegraphs for 2 seconds, checks the human root's horizontal distance <=11 studs and vertical distance <=8 studs, then directly executes `h:TakeDamage(28)` without checking solid walls. A human behind a castle wall can be damaged by a boss strike even if the wall is supposed to provide cover. **This is an observed source logic gap, not a Studio-reproduced bug.**

## Actual implementation

`tools/compose_patch.py` accepts *only* that exact original author blob. It generates a scratch **single original boss module source** and inserts `shockwaveClear` before the original attack prompt. The helper performs a server-side `workspace:Raycast` from boss center to human torso, with `RespectCanCollide=true` and filters for the boss model and the target avatar. The existing horizontal + vertical gate now also requires unblocked LOS before its existing 28 HP attack. Unblocked targets keep the identical 2s warning, 5s interval, 28 HP hit, no change to boss 900 HP, hero 36stud skill reach, castle/win/KO/egg/loot/score or mode state. Invalid source SHA, missing/duplicated anchors or a second patch fails closed.

**Production safety:** no new Game, Store, Remote, boss spawner, damage authority, bot AI, ITEM, HUD or paid asset. No original author file edited. The generated original boss is for selective review by #482 and #484, not a replacement branch/RC. **Rollback:** do not select the generated boss module at intake, or restore exact original blob `2670618...` and remove the optional gate.

## Eight-domain review (reuse, don't duplicate)

| Area | Existing owner / coverage | Effect of this slice |
|---|---|---|
| Character | #482 seven roles, #510 mage, #516 DOT | No class/HP/role edit; hero receives radial damage only if cover ray is clear |
| Field | #482 arena, #485 field art | Castle wall / terrain is now cover, no map edit |
| Battle | #482 real skill combat, #503 FX, #504 audio | 28 HP boss strike retained, block through solid wall |
| Castle/egg | #482 rules, #500 defense, #509 egg ledger | Cover decision only, no castle authority |
| Neutral | #482 original StoneGiant, #494/#501 Swarm, #514 boss KO counter | Only original boss radial attack LOS |
| Items | #489 egg-carrier buffs, #517 fullHP HEAL | No item change |
| Lobby | #482 TEAM/BR and #513 host lease | No lobby/queue change |
| Balance/SCORE | #487 score, #499 900s timeout | Reduces cover-ignoring hits; telemetry and real Studio acceptance required |

## Verification / RC intake

The dedicated read-only workflow checks original full commit + Git blob, ten source tests including source drift, mutation, authority and exact two-hunk isolation, native Luau compilation of the **actual generated authored source**, and artifact of diff/generated source. It does **not** run Roblox Studio, a real collision engine, live 1+15AI/2+14AI games, Android FPS, #420 ART/FUN or OWNER review. Do not record it as effective wall protection until real engine test.

For B intake: #218 exclusive CLAIM_GRANTED decision -> #482 original owner ACK for two-hunk change -> #484 one-boss source-selective composer -> no duplicate Game/Role/Store/Remote/Swarm -> latest official RC HEAD authentication+nonforce CAS by #220 -> same-HEAD official source/native/Rojo/Place/ZIP/rollback ACK -> Studio wall cover test + PC/Android 15-minute performance + OWNER acceptance. Retain YELLOW debt record if nonfatal, block RED, never merge whole DRAFT PR. No main changes, publish, purchases or PC actions.


<!-- CURRENT69_INCOMING_LOS_REGISTRATION_20261123 -->
## Current69 incoming LOS payload registration — 2026-11-23 JST

**SOURCE_EVIDENCE_REGISTRATION_ONLY; PREP_READY=false; official RC adoption not performed.** The unchanged sections above are the historical original21/outgoing record, including old SOFT-claim and prior-author-ACK wording. Current [#1011/v1.2](https://github.com/kk051780/toy-wars-factory/issues/1011) requires genuine scope, original-candidate reuse and independent review; a separate prior-author ACK is not required. This update preserves the old producer and does not turn its tests into current69 incoming evidence.

### Existing one-line repair

The current Boss incoming `damageFrom` ray can stop on a queryable noncollidable decoration and miss a solid wall behind it. The existing repair adds exactly `params.RespectCanCollide=true` after the character/Boss exclusion filter. It preserves the current `InvulRuntime.boundAttackMultiplier(player,"NORMAL")` expression and the entire outgoing `shockwaveClear` tail.

- Payload baseline: `fb5d9b693c48d4ffcce05c3f89d490593e0cecfd`.
- Route/class: `ServerScriptService/EGGRUMBLE_NeutralStoneGiant`, ModuleScript.
- Before: 7,075 B / SHA256 `ddd22fae146fa7a6cc15d3193a29a723e98dfc5dd3cce931e4387ef17a5688be`.
- Existing candidate: 7,107 B / SHA256 `0e81e4487877c014612125e8ccde422023c7a13d46bf65aa6a241318dd1b3615`.
- One 32-byte insertion / one hunk; exact inverse restores the fixed before bytes.

[current69/incoming_los.patch](current69/incoming_los.patch) is the unchanged original557 B patch: SHA256 `bf4415aa0859d28e3e2a96b5bc8588d92347a3a8c33b4812bbb56db32d223490`, Git blob `21247525134069a6de225fcbdc109ba0193bcb6c`.

[current69/INCOMING_LOS_EVIDENCE.json](current69/INCOMING_LOS_EVIDENCE.json) is the unchanged original19,024 B independent REVIEW_RECEIPT.json: SHA256 `fb1ff4700a0f44a93207f461266cb009c7f43ae4253340aaf557d6bdab2355db`, Git blob `b2554196c2391ec3ff893617b12177d2c6455f1b`. Original review time20:24:28 UTC, `registered_approval=false` and `rc_adoption=false` remain intact. Its absolute local paths record historical provenance; the original files/logs remain in the linked evidence package.

Source/patch author lineage is **CODEX_ROOT_0043C64DE7ED and its separate reviewer context**. CODEX_ROOT_7B6B25AEAA29 only registers the existing bytes and this explanation, and does not claim original repair/test authorship or reruns.

- [Original fb5 revalidation](https://github.com/kk051780/toy-wars-factory/pull/518#issuecomment-7085605574).
- [Original payload handoff](https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-7085611873).
- [Existing source, programs, logs and independent review package](https://chatgpt.com/library?file_id=libfile_5711f7ee9e5c8191a6ff55e267c640d2&account_id=personal): `boss_fb5d9_revalidation/` and `boss_fb5d9_independent/`.

The historical independent receipt binds seven full modules and eight exact Host/Combat/constructor excerpts. It is not complete Host execution. It separates author geometry24, historical independent18 and fresh independent6. The six fresh cases changed from2/6 to6/6 in the declared Native AABB/API fixture, covering wall rejection, same-tick valid retry, cooldown, NORMAL multiplier, membership/phase and old-session fences. These are reused historical results, not new current-HEAD incoming CI from this registration.

### Genuine limited scope and next gate

Existing PR518 / `feature/gq-boss-wave-occlusion-20261116-01` retains pre-registration HEAD `f31081d5cb2bea86d01c76c53bb60cd2f9a8355d` as ancestry. GitHub's historical PR base `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34` differs from the payload baseline fb5; no rebase or whole-PR merge is claimed.

Actual [request7086835669](https://github.com/kk051780/toy-wars-factory/pull/518#issuecomment-7086835669), [CLAIM_GRANTED](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7086934249), registry [baa9e4c1b3b494ce24c406716e76047f22072c2c](https://github.com/kk051780/toy-wars-factory/commit/baa9e4c1b3b494ce24c406716e76047f22072c2c), claim `P0D-GQ518-INCOMING-LOS-20261123-7B6B25AE`. Eight cumulative PR paths are registered; only this README and the two added files may change. Five historical code/test/workflow blobs stay exact. Separate source lease epoch617, acquisition [c073cd20ce35ffd07d8378fb7885d0a5fe109bd5](https://github.com/kk051780/toy-wars-factory/commit/c073cd20ce35ffd07d8378fb7885d0a5fe109bd5). Actual new-HEAD registration review is required from `/root/current_rules`; it is not predeclared here.

The original private21 workflow remains unchanged. Any result on this new commit still covers historical outgoing21, not this current69 incoming patch. Canonical UNION22 composer/profile/native files and shared workflow are excluded. Later integration requires the preceding owner's completed intake or explicit handoff, a new scoped claim, fixed candidate checks and independent review, and a separate RC writer.

Registration rollback removes only these two added files and this appended section, preserving the original six-file PR and intervening work. Gameplay rollback is the original one-line inverse. No new gameplay producer, authority, feature, test, workflow or PR. Studio Solo/2-client, Android, ART, FUN and owner acceptance remain untested; main, publishing and payments are outside scope.
<!-- END_CURRENT69_INCOMING_LOS_REGISTRATION_20261123 -->
