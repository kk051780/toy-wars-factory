# WORLD-G9｜三階層の卵争奪・逃走と救出
2026-11-13 JST. Independent original game-design+CONTENT-FEATURE slice G9 from G8 original private 3-tier transport, **S2+ standalone prototype**, not TRAP RAIDERS H1 main or official #220 RC.

## New field feature cards
### WF-19: 海底ガラス城の卵争奪
- **3秒で分かること**: 赤か青、相手色の光る卵をE/タップで取り、自分の色の台へ。先に3点取ると勝利、6秒後に自動再戦
- **Actual authored source**: server-owned RED/BLUE alternating assignment, both real egg world Parts and nested prompt, physically separate home colored score pads; pure rules lock enemy-only steal and own-egg-home condition before score, genuine in-world source-authoritative egg carried by one real UserId, first-to-3 score. Both egg nests laid out symmetric from central SEA entry: RED x-22, BLUE x+22, same y=-28, own score pads at z136 vs eggs z168, independent of all paid or class abilities
- **Counterplay**: both sides may steal simultaneously, but if your own egg is stolen you cannot score until it is returned. No pay-to-win, no damage, no projectile. Defender always knows which egg was stolen from shared sea scoreboard
- **Rescue**: theft expires automatically after 45s to prevent indefinite hiding; on disconnect/character death the egg returns to its home
- **Marketing 7s**: blue child steals red egg; red child runs toward sky rather than waiting at home; both can recover their real objectives
- **Evaluation**: first30s understands objective, 2-team win fairness, single-color visual clarity, real physical collision, mobile touch and fun NOT_TESTED

### WF-20: 追いついて救出のタッチ
- **3秒で分かること**: 卵を持つ相手の頭上には「たまご運搬中」。追いついてE/タップで救出。相手を傷つけない
- **Actual authored source**: each carrier real HumanoidRootPart gets only one server-side ProximityPrompt for recovery. Actor must be real owning-team defender; server independently verifies actual character health and <=12 studs distance²<=144, 0.45sec actor cooldown, carry UserId and egg ownership before recovery
- **Counterplay**: carrier may choose original G8 private PORT/SEA/SKY five real server-verified portals to evade; defender can follow same publicly available free routes. No invisible speed buffs, no hiding item paid
- **Failsafe**: death/leave/45sec expiry automatically resets egg; expired callbacks are not trusted. Any attempt to rescue an egg of the other color, wrong actor, remotely or from self is rejected
- **Marketing 7s**: defender chases colored egg carrier to a portal and tags a second before the goal

### WF-21: 天空みはり台（守るための情報）
- **3秒で分かること**: 高い空城の光る台座でE/タップ。「卵を持つ人がどの階層にいるか」が全員に7秒間表示
- **Actual authored source**: SKY located (0,49,313), real server ProximityPrompt with <=12 studs physical range, 10sec global cooldown, truthful layer inferred from real server avatar Position.Z, uses no gameplay rewards/HP/Remote
- **Counterplay/fairness**: same information displayed to both teams, lookout is publicly accessible from SEA; no wall hacks, identity revelation only high-level tier labels PORT/SEA/SKY and egg color
- **Failsafe**: if player leaves/health invalid, no fake location returned; no tracking after 7s, no always-on telemetry or pay-to-know advantage
- **Marketing 7s**: defender taps the sky lookout, sees blue egg on the sea level and rushes down with the same free portal
- **Performance**: low-poly static 3D existing G8 retained, 3 more colored egg props, score pads, small prompts and billboards; actual FPS/memory unmeasured

## Actual, proposed, and release boundaries
ACTUAL SOURCE: G8 immutable original 2 Luau (world three physical SEA/PORT/SKY and 5 safe teleport routes) copied unmodified exact; 2 additional original server Luau (pure egg rules and Game controller); full standalone 4-script private Rojo Play place. Studio RunService guard. Supports solo exploratory test and 2 simultaneous Studio players, no live release or actual gameplay test by agent.

NOT IMPLEMENTED: S1 existing actual Game.server/eggs/first-90s core, H1 roles (RAIDER/GUARDIAN) or Wind/traps, native swimming, low gravity, NPC boss, currency, paid item/real collectible inventory, persistence. Deliberately no Network Remote; original S1 authority must not be replaced/combined without #220 sole writer's approval.

Observation/source: Roblox official docs [ProximityPrompt security](https://create.roblox.com/docs/scripting/security/client-server-boundary) say even visible prompts need independent server validation, and [ProximityPrompt reference](https://create.roblox.com/docs/reference/engine/classes/ProximityPrompt) supports mobile UI. Our original strategy hypothesis needs real human trial and is NOT substantiated by player metrics.

## Stage gates
K1 unique source author claim/provenance & previous G8 pinned; K2 2 exact old G8 and 2 new egg/server scripts plus original child-centered action/counterplay/safe expiry; K3 real native Luau policy 50+ assertions, adversarial Python source and negative mutation tests; K4 genuine Rojo whole private .rbxlx exact4/4 and real compiler4/4; K5 immutable fixed commit and QA receipt in #222/#219/#218/#220 informational intake; K6 actual Roblox engine two-player/physical phone and human joy NOT_TESTED. Only one main H1 official release decision, last #220 75/100 and #222 field master50% remain unchanged.
