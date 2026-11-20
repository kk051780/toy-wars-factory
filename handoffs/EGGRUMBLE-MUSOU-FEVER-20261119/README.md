# EGGRUMBLE P0 #824 — MUSOU / RUSH / KAKUHEN

FEATURE_ID = GQ8_MUSOU_FEVER_CHAIN_20261119
OWNER directive = 2026-11-19 JST; predecessor = #285 level awakening; adjacent but independent #822 / #823 damage-zero invulnerability; reuse #800/#801 KO finisher. Follow #810 successor DRI, #220 authentic B writer.

## Unique source inventory
- MusouFeverPolicy.luau: real pure server Luau state machine. No new damage/KO/scoring/storage/remote authority.
- MusouAuraClient.luau: cosmetic-only Roblox client observer ModuleScript (7 role distinct nameplate, highlight, affordable particles). **Not wired** to the existing server snapshot channel, so no actual in-game aura yet.
- make_native_musou.py: source-derived native Luau VM tests and adversarial mutants.
- Dedicated pinned native CI workflow. **Source candidate, not formal RC behavior.**

## 7 roles: official display names and stable IDs
WARRIOR 武神; MAGE 魔法使い; NINJA 暗殺者 (retain legacy ID); TRAPPER 超能力者; BUILDER マッドサイエンティスト; BEAST 魔獣使い; ZOMBIE 呪術師.

## Gameplay tuning candidate
- Lv1, free/time charge; first ready 70s; no-paid-use permission.
- MUSOU 8s, recharge 105s after true ending. KO confirmed by original server owner only, weighted streak within 3s; RUSH chain>=3, KAKUHEN chain>=7.
- Neutral +0.5s, human/boss +1.0s, combined KO-extension cap +6s; KAKUHEN one-time +6s, maximum 20s from start and no endlessly cycling state. Fever recharge 90s from extended end.
- Role-specific neutral multiplier 3.4–4.0x, fever only neutral +25%, players 1.20–1.35x (including fever), bosses 1.25–1.40x, castles 0.60–0.70x. Rebalance after real playtests.
- Read-only snapshot exposes role phase, sigil, label, seconds for other players to see. Server state never inferred from visuals; exact server-KO receipt IDs cannot be replayed across activations in same match (512 fixed max per player per match, 24 per activation).
- No invul/shield/egg carrier/defeated/castle-dead activation; a conflict removes effective damage boost and the owning Combat must call cancel. Respawn cancels active but not time-recharge, rounds are isolated.
- Unknown actor, fake enemy, client-provided KO, converted/summoned farm, old round, old avatar, mismatched player, NaN time all fail closed. Existing Combat owner must apply multipliers ONCE pre-damage, not independently scale DOT/terrain or duplicate KO credit.
- Player strategy: defend/interrupt visible enemy burst, force its 8s timer to lapse; save for neutral wave/boss/egg-defense; KAKUHEN extends fun but can't auto win PvP or deliver carried egg.

## Integration contract — CURRENTLY UNFULFILLED
1. Read latest #818/#796/#815 source lineage and #823; adapt original Combat/Swarm/Host singleton sources ONLY. Do not copy these whole modules into another authority; existing #801 finisher remains sole KO visuals.
2. Add the policy as one server ModuleScript. At start/round end/new avatar, instantiate or cancel match state; drive recharge from verified server monotonic time, not client clock. Read-only snapshot replicated to **all** observing clients via existing HUD/channel with remote ownership preserved.
3. The existing server KO credit callback calls onConfirmedKO exactly once, with immutable receiptId unique across match, server-confirmed enemy/team/source and score credit; no client-claimed hits.
4. Existing Combat queries attackMultiplier by target classification in one place. Defense policy (#823) must reject same-time activation, regardless of call order; egg owner cancels during pickup and blocks delivery during active surge. Confirm normal damage on expiration. Use #765 elemental VFX as subordinate to role aura, not substitute for verified server damage.
5. Mount existing client LocalScript to call MusouAuraClient.update for all nearby combatants on phase changes. On Roblox death/removal call MusouAuraClient.stop. Current optional module has never been tested in Studio; color and text aren't a final cinematic quality pass. Add high-impact but Android-safe role-specific shockwave/animations from existing #381 FX owner, without new damage/score.
6. Same-source compile + real Rojo complete game source/class, OFF exact rollback, same-HEAD proof, true private Place/ZIP artifact readback, source SHA, and authenticated #220 nonforce CAS into **rc/p0d-s1-kids-rc01** only. Do not touch main/publish/Robux.
7. Studio solo/2client/Android15min, 7-role distinct perceptible effect, low-end FPS, PvP guard/LOS/fairness, chain satisfaction, retention. Neither native-only policy tests nor aura unit compile count as Roblox behavioral verification.

## Current status ledger
SPEC=COMPLETE; SOURCE_POLICY=ADDED; OBSERVER_VFX_MODULE=ADDED; NATIVE_CI=AWAIT_LIVE_EVIDENCE; SINGLETON_COMBAT_WIRING=NOT_DONE; FORMAL_RC_ADOPTION=0/1; STUDIO_2CLIENT=NOT_TESTED; ANDROID_15MIN=NOT_TESTED; FUN_ART=NO_GO; MAIN/PUBLISH/ROBLOX_PAYMENTS=UNTOUCHED.

Non-overlap feature paths: handoffs/EGGRUMBLE-MUSOU-FEVER-20261119/** and .github/workflows/p0d-gq8-musou-fever-native.yml. Rollback: omit optional two modules; original official Core36 and the latest selected #818 game source unchanged. No original author personal ACK is required. Next successor Chat reGET issue #824 + exact PR HEAD + #810/#220 + official HEAD and keep responsibility through legitimate RC adoption.


## 2026-11-19 latest: Real44 original gameplay -> Real47 single-owner candidate

Supersedes the earlier `SINGLETON_COMBAT_WIRING=NOT_DONE` statement **for the private selectable Real47 candidate only**. Formal RC remains unmodified. Exact immutable selected upstream is PR #815 HEAD `d5c13082d4987a8c89588a12b81edc73adc945ce`, its verified Real44 artifact from run `44385257005`, original formal Core36 branch `f77b4d4393d9e9b19b65566413432a7a9f13962b`.

### Actual integration source and verifiable result
- `compose_real47.py` source-selects 44 real existing original scripts and adds 3 modules, changing **only the original singleton EGGRUMBLE_SwarmCombat and EGGRUMBLE_SevenRoleCombat** (42 other originals byte exact). New 47 are: existing server-owned MusouFeverPolicy ModuleScript, StarterPlayerScripts MusouAuraClient ModuleScript, StarterPlayerScripts MusouAuraController LocalScript.
- Existing server-side SevenRoleCombat equipment now adds a fourth genuine selectable Tool `EGGRUMBLE_MUSOU_AWAKEN`; `Activated` validates role/match/player on server and calls existing Swarm API, never a new client damage Remote. Original Tool cleanup removes it at round end.
- Existing Swarm player neutral-hit path applies the `NEUTRAL` multiplier exactly once before its **one** original `Humanoid:TakeDamage`; existing KoFence->credit path emits actual unique per-match neutral KO receipts and refreshes MUSOU/RUSH/KAKUHEN state. Existing human PvP damage and real boss damage pass through role-specific policy multipliers without a new damage owner. Existing neutral charm source is retained.
- Replicated server Player attributes expose phase/role/remaining; the read-only StarterPlayerScripts LocalScript observes all players, rendering 7 distinct cosmetic auras. One bounded scheduled expiry callback per state update and no extra AI/KO loop.
- Original game policy untouched: server roster/actual heldEggs, active mode, old avatar, downed, castle alive, no ForceField, and explicit server invul indicator gate in context. Direct egg objective/guard and defensive #823 integration still needs composite testing, **do not infer complete all-source defense/egg/CC security** from this candidate.
- Same exact HEAD `9065372c385bad1f228450a74fa052503d02b7b3` Native+Rojo result **COMPLETED SUCCESS**: https://github.com/kk051780/toy-wars-factory/actions/runs/44387396403
  - Original44 **44/44** and candidate47 **47/47** true Native Luau compile; exact policy VM and all 3 malicious mutations gated.
  - Real47 Rojo Source/Class+Portable47 byte equality; OFF44 Rojo Place **byte exact** to certified upstream Real44.
  - Candidate Real47 Place **532,452 bytes**, SHA256 `5965e9ef2bc313df5d3e427c774200990e79351672eb59f23896bee978fed1f4`.
  - Private artifact `GQ8-MUSOU-REAL47-PORTABLE-NOT-OFFICIAL` (workflow run artifact ID 14466482902; compressed archive 503,996 bytes) contains all 47 sources, project, Place, receipts and OFF44. This is **not** a published Roblox game.
- Future integration MUST reconcile latest parallel #823 V2 counter-awakening and its actual Real46 private source (run #44386320845) into one author-owned Combat and Swarm. The isolated Real47 **does not include** all #823 original all-damage prehit guard source and must not displace it. Original #815 latest source is immutable for this receipt and must be re-fetched at future official RC selection.
- Formal `rc/p0d-s1-kids-rc01` **adoption 0/1**; only #220 authenticated CAS writer may update with new fresh expected SHA plus same-HEAD Rojo/Native/OFF/Place readback. Current Chat does not claim its B writer authentication. Studio 2 clients / Android15 min / ART / fun **not tested; NO_GO**. Main/Publish/pay untouched. No original author approval required for successor DRI.
