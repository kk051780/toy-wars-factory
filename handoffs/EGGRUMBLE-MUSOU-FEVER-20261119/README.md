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
