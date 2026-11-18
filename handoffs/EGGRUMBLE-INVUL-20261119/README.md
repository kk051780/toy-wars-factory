# EGGRUMBLE P0｜無敵覚醒 V2（OWNER最新2026-11-19・旧#822 V1上書き）

**AUTHORITATIVE**: issue #822 latest V2. Old fixed-duration immediate invulnerability 0.9–2.2 seconds / total5seconds / global18s is formally **SUPERSEDED**, do not resurrect via other worker.

## Why this wins over generic guard/awakening
The Strongest Battlegrounds and Jujutsu Shenanigans teach two competing patterns (counter moments, character-specific ultimate/arena domination); EGGRUMBLE adds an original cross-linked loop: **announce defense → deliberately attract/catch a hostile attack → completely nullify the first hit → 6–9 sec character-specific awakening with one signature active retaliation → one confirmed neutral hit can extend it once by up to1.5s → choose to save remaining match budget**.

No automatic passive invulnerability and no trigger via self damage, weather, fall, fake/duplicate/unverified events. If an enemy holds attacks and escapes for 3s, the user's stance whiffs **without spending a charge** but with 12s retrial. Consequently the opponent has clear responses.

## V2 single owner initial numbers (candidates, tune using real 2-player 15-min acceptance)
All 7 roles have FREE Lv1 access, available from first life.

| Role ID | Action | Reactive full invul | Skill triggers/match | Skill CD | Reactive finisher |
|---|---|---:|---:|---:|---|
| WARRIOR 武神 | 神威迎撃 | **7s** | 2 | 75s | First attacker single target divine recoil, normal neutral one-shot; PvP execute only ≤25% HP after .65s telegraph+second dodge/LOS check, else max40% maxHP heavy burst. Boss capped15% |
| NINJA 暗殺者 | 影殺返し | **6s** | 3 | 60s | First attacker single target backline counter, normal neutral one-shot; PvP execute only ≤20% HP after .65s tell+second dodge/LOS check, else max35% maxHP burst. No wall teleport |
| MAGE 魔法使い | 万象絶対結界 | **9s** | 2 | 85s | All attacks from every direction zero, first3 distinct valid hostile hits arm arcane null pulse AoE14 studs, PvP hit cap16% target maxHP; old heal+revive kept separate |
| TRAPPER 超能力者 | 鏡面反射領域 | **7.5s** | 2 | 80s | Store up to 3 verified attacks, mirror-reflect at attackers once, PvP per-target reflected cap18% HP; no arbitrary infinite reflects |
| BUILDER マッドサイエンティスト | 超防護実験装置 | **9s** | 2 | 90s | Self true immune; after 2 hits activate 10-stud ally barrier **50% reduction for 3s** (allies not full immune), base/castle NOT immune |
| BEAST 魔獣使い | 獣王反攻 | **7.5s** | 2 | 80s | Self true immune, tamed beast charge/push and neutral herd domino attack; PvP up to25% maxHP, no long stun loops |
| ZOMBIE 呪術師 | 冥府反転 | **8s** | 2 | 85s | After3 stopped hits one real original neutral may turn to ally if HP≤35% (existing #800/#821 Swarm owner); other targets curse-mark, boss never converted |

The game has a **single reactive damage owner**: incoming first hit zero when valid. Repeated hits zero until expiry, including PvP, elite, boss, DoT, storm/fire/sea/fall. Existing new CC and knockback blocked for immune wearer; existing status effects must not deal HP damage during mode (they can remain timed and resume afterwards). Match-loss/despawn/anti-cheat is NOT prevented.

### Activation sources
- Free SKILL: 3s visible defensive ready stance. Only **real first server-confirmed hostile PLAYER/NEUTRAL/BOSS hit** wakes role-specific window, consuming **one match charge**. Missed bait window consumes no use, retrial lock12s.
- Free ITEM Aegis Shard: 5s window to catch a real enemy hit; after hit 3.5s full immune, one item/match and existing item owner's actual pickup; no Store/Robux gates.
- Real weapon PERFECT GUARD: verified successful real intercept and valid weapon owner from old Combat/Item; .45s readiness, after hit 2.2s full immune, one perfect guard/match. The damage owner may create stance and trigger it in its one hit transaction; do not use client-success boolean.

All sources share an **aggregate 24s full-immune match budget** and **40s global minimum gap between successful triggers**. Max 1 concurrent mode; source CD, match charge, source id and token checked server-side. Source switch cannot bypass. On actual counter success vs a real neutral, once per awakening at most **+1.5s**, charged against 24s shared budget; never from PvP farming, no infinite combo.

### Counter fairness, design source distinctions
- Ordinary attacks during invulnerability remain allowed but **80% damage**; **the one genuine signature counter** exempt from this multiplier. Ordinary FINISHER and SIEGE damage 0 while immune, no egg pickups/deposits or carrier activation, no invulnerability stacking with normal SHIELD.
- The exciting one-hit KO applies to normal single-target neutral grunts only. PvP finish is **never unconditional against fresh HP**: strict first-attacker target lock for WARRIOR/NINJA, confirmed counter, visible .65s warning, second authoritative LOS+evade recheck, execute only when ≤25% / 20% respectively. Other PvP damage capped; boss cap15%. No ghost finisher effects unsupported by actual damage.
- MAGE is **multi-attacker** defense rather than a single-character parry, and its 9s field does not erase opponent player HP. TRAPPER/BUI/BEAST/ZOMBIE support distinctive team/mob counterplay.
- All action outputs are **instructions**, not direct kill/heal/HP/score writes; they must be accepted and applied by existing single source owners after live match/attacker/target/LOS/CC verification. This PR does not bypass original authority.

### Data and API
Server-only Luau `InvulnerabilityPolicy.luau`:
`newRound(epoch)` creates match-owned state.
`arm(s,context,source)` sets ready state with no use charge.
`onIncomingDamage(s,context,event)` is the **sole pre-damage hook** and returns `blocked=true,multiplier=0` on valid triggering or active invulnerability. The DamageOwner must use this result before any HP/DoT/Realm PVP damage application, not reactively heal after death.
`claimCounter(...)` returns ONE role-specific decision only after verified block count and target proof; no damage performed. `rewardConfirmedCounter(...)` extends up to1.5s once after verified hit on neutral only. `damageMultiplier`, `allowNewStatus`, `attackMultiplier`, `allowObjectiveAction`, `snapshot`, `cancelAvatar`, `cancelOnObjectivePickup` are read/guard/cancel adapters.

Input to all calls must originate from server-held match epoch, player+avatar epoch, verified role, castle state, real health/hit, item/weapon success flags. Attack IDs must be immutable server unique IDs. No client sends damage, timestamp, free item, isInvulnerable or counter outcome. Rejoin/respawn cannot refill charges. No passive HP regeneration while Combat owner is unaware of stopped damage; crosslane integration must coordinate #775/777.

### Tests and ownership
Native real source VM suite: 7 roles, 3 source channels, 6–9s exact, first hostile hit absorbed, no pre-hit immunity, weather does not trigger but is immune mid-awakening, shield/egg/CC, 40s shared gap, 12s miss, 24s aggregate, per-match charges and respawn no reset, PvP/neutral single counter, uniqueness and one neutral chain, invalid client/round/NaN. Deliberate 3 mutations: 240sec aggregate, damage allowed during invulnerability, unlimited charge rejected as RED.

**NOT GAMEPLAY DONE**: Existing Core36/Realm/Combat/Swarm/Item/Weapon/Weather/CC and VFX are not yet connected; original #823 policy changed, must use latest source hash, rebuild same-HEAD Native/Rojo/OFF before formal RC. #220 only authorized formal RC nonforce CAS writer, no main or publish/paid. Studio2client/Android15min/FUN remains NOT_TESTED.
