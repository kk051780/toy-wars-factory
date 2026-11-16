# GQ vertical hit fairness — unique isolated source repair

ORIGINAL owner: #482, exact original HEAD `fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9`, original Git blob `a47b1d803ed9bb80c27a8ac86e6bad74a337aa79`.

**Actual code defect:** `EGGRUMBLE_AttackGeometry.allowed` measures only world X/Z, not Y. A mage circle, sword fan or builder rail can qualify a neutral/enemy on an upper/lower floor even 50 studs above or below if X/Z overlaps and ray LOS is open. This is a **source-derived vulnerability, not Studio-reproduced**. With sky routes and castle interiors, the vertical false hit harms fairness/clarity.

**Unique owner slice:** one 2-line finite vertical guard in existing original shared attack geometry; no changed SevenRoleCombat, Swarm, Castle, Bot, Item, Lobby, Score or active RC. Preserve every other existing geometry shape and range. Vertical allowance is `min(skill radius,14)` studs, which avoids accidental hits between elevated levels while preserving nearby sloped terrain. 14-stud value is a source trial, **must be tuned with Studio gameplay evidence**.

**Differential tests:** eight Python mutation/source lock/byte-exact reversal checks and native actual Luau 14-before / 14-after scenarios including CIRCLE/FAN/LANE elevated 50 studs, -22 studs, 14.1 threshold, horizontal miss, same-floor and radius. The old source must admit those elevated false hits; selected source must reject them.

**Do not double up:** Other current chat lanes own #580 takeover (already formally selected), #520 ridge+forest, #583 roster, #571 boss, #582 zombie command and #518 shockwave wall LOS. This slice does not change any of those methods. Original author personal approval is not a stopping condition; immutable source and code safety are.

**RC handoff:** SOURCE_ONLY until a current exact-head true canonical31 composer substitutes only existing `EGGRUMBLE_AttackGeometry` with this selected source; 30/31 other Luau byte-identical; native31 and Rojo31 Source/Class exact + inverse OFF; authenticated #220 sole nonforce expected-SHA CAS; new same-head V3+legacy CI, true Place and provider ZIP bytes. On drift, rebase the source-select only; never force or overwrite other authors. Do not count as official adopted or as Studio/Android/FUN/OWNER GO until genuinely verified.

No main/publish/paid/Windows mutations.
