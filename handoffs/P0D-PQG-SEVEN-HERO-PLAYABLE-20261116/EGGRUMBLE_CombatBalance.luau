--!strict
-- EGGRUMBLE V3 seven-role combat balance / authoritative skill numbers (preview).
-- Damage is for a connected hit. All cooldowns are server-owned seconds.
-- Each skill has a capped affected area and category-defining secondary effect.
-- No paid module changes these limits. Tuning is subject to PvP / 15-min mobile QA.
local Balance={}
Balance.HERO_BASE_HP=100
Balance.MAX_SKILL_RANGE=32
Balance.MAX_AREA_RADIUS=22
Balance.MAX_CROWD_HITS_PER_PULSE=24
Balance.MAX_HERO_HITS_PER_PULSE=5
Balance.NEUTRAL_BASE_HP=32
Balance.KAMI_DUEL_MULTIPLIER=1.25
Balance.SKILLS={
 WARRIOR={
  A={damage=44,reach=20,radius=8,cooldown=.72,shape="BLADE",effect="CUT",notes="single-target strongest with war-god boost"},
  B={damage=26,reach=21,radius=9,cooldown=6.0,shape="LANCE",effect="TRIPLE",notes="three forward spear thrusts"},
  C={damage=46,reach=14,radius=15,cooldown=16,shape="GOD",effect="KAMI_6S",notes="six-second self empowerment, 1v1 strength"},
 },
 MAGE={
  A={damage=30,reach=25,radius=10,cooldown=.86,shape="CRYSTAL",effect="CHILL_2S",notes="precise long-range ice slow"},
  B={damage=52,reach=21,radius=21,cooldown=7.2,shape="INFERNO",effect="BURN_3S",notes="largest sustainable horde-clearing circle"},
  C={damage=42,reach=14,radius=18,cooldown=17,shape="LIGHTNING",effect="HEAL_25",notes="team heal and lightning impact"},
 },
 NINJA={
  A={damage=46,reach=8,radius=7,cooldown=.68,shape="SHADOW",effect="CRITICAL_CLOSE",notes="close-range ambush skill"},
  B={damage=26,reach=10,radius=9,cooldown=7,shape="WIND",effect="DASH_STEALTH_3S",notes="safe dash, no egg shortcuts"},
  C={damage=31,reach=12,radius=13,cooldown=14,shape="SHURIKEN",effect="TRIPLE",notes="three fan-shaped cuts"},
 },
 TRAPPER={
  A={damage=31,reach=16,radius=11,cooldown=.95,shape="PSI",effect="PUSH",notes="telekinetic burst"},
  B={damage=24,reach=15,radius=18,cooldown=7,shape="GRAVITY",effect="SLOW_3S",notes="crowd locking instead of raw damage"},
  C={damage=35,reach=12,radius=12,cooldown=16,shape="WARP",effect="SAFE_WARP",notes="controlled displacement without egg carrying"},
 },
 BUILDER={
  A={damage=27,reach=28,radius=8,cooldown=.62,shape="RAIL",effect="PIERCE",notes="long-range electric ray"},
  B={damage=28,reach=23,radius=10,cooldown=6,shape="ROCKET",effect="TRIPLE",notes="multiple separated salvos"},
  C={damage=24,reach=17,radius=12,cooldown=17,shape="TURRET",effect="FOUR_PULSES",notes="area cover turret proxy, can counter siege"},
 },
 BEAST={
  A={damage=40,reach=10,radius=12,cooldown=.92,shape="FANG",effect="PREDATOR",notes="strong front-line companion strike"},
  B={damage=48,reach=14,radius=18,cooldown=9,shape="GIANT",effect="GIANT_FEED",notes="short-lived giant form impact"},
  C={damage=27,reach=14,radius=11,cooldown=17,shape="SPLIT",effect="THREE_SPLITS",notes="three smaller beasts attack different spots"},
 },
 ZOMBIE={
  A={damage=34,reach=14,radius=12,cooldown=.9,shape="CURSE",effect="MARK",notes="mid-range curse branding"},
  B={damage=24,reach=14,radius=18,cooldown=8,shape="PLAGUE",effect="SLOW_3S",notes="crowd denial and anti-rush"},
  C={damage=26,reach=17,radius=12,cooldown=17,shape="UNDEAD",effect="THREE_PULSES",notes="multi-unit area pressure"},
 },
}
function Balance.skill(role:string,slot:string):any
 local row=Balance.SKILLS[role]
 assert(row~=nil,"invalid combat class")
 local spec=row[slot]
 assert(spec~=nil,"invalid skill slot")
 return spec
end
function Balance.validate():number
 local count=0
 for role,row in pairs(Balance.SKILLS) do
  local ordered={"A","B","C"}
  for _,slot in ipairs(ordered) do
   local s=row[slot]
   assert(s and type(s.damage)=="number" and s.damage>=20 and s.damage<=60,role.." damage out of bounds")
   assert(s.reach>=0 and s.reach<=Balance.MAX_SKILL_RANGE,role.." range out of bounds")
   assert(s.radius>=4 and s.radius<=Balance.MAX_AREA_RADIUS,role.." area too large")
   assert(s.cooldown>=.60 and s.cooldown<=18,role.." cooldown out of bounds")
   assert(type(s.effect)=="string" and #s.effect>1,"missing secondary effect")
   count+=1
  end
 end
 assert(count==21,"7 roles x 3 actions required")
 return count
end
return Balance
