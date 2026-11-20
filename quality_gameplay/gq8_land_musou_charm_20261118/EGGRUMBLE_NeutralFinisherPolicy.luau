--!strict
-- GQ800: presentation policy ONLY. A server-confirmed neutral hit/KO receipt is mandatory.
-- No Humanoid, RemoteEvent, Score, PVP, Store or damage authority.
local M = {}

local SPECIES = {
  BANNER_KNIGHT = { label="旗持ち騎士", personality="PROUD", motion="BOW_STUMBLE", friendRole="DEFENDER" },
  TINY_SHIELD = { label="ちび盾兵", personality="SHY", motion="SHIELD_TUMBLE", friendRole="SHIELD" },
  SPIKE_BOAR = { label="トゲ猪", personality="BRAVE", motion="ROLLING_BOAR", friendRole="CHARGER" },
  ACORN_IMP = { label="ドングリ兵", personality="CURIOUS", motion="JUMP_SPIN", friendRole="SCOUT" },
  SHY_WRAITH = { label="おばけ", personality="TIMID", motion="PUFF_SMOKE", friendRole="AMBUSH" },
  ICE_SLIME = { label="氷ぷに", personality="BOUNCY", motion="JELLY_WOBBLE", friendRole="SLOW" },
  SPARK_GOBLIN = { label="火花小鬼", personality="MISCHIEVOUS", motion="SPARK_SPRINT", friendRole="SPARK" },
  BABY_GOLEM = { label="ゴーレム幼体", personality="STOIC", motion="FLAT_THEN_POP", friendRole="TANK" },
}
local ROLE = {
  WARRIOR = { hit="SWEEP_CHAIN", ko="RAGDOLL_FAN", shape="SWORD_ARC", cue="SHING_BOOM" },
  MAGE = { hit="SPELL_SPIRAL", ko="ARCANE_BURST", shape="SPELL_RING", cue="MAGIC_POP" },
  NINJA = { hit="SHADOW_STAGGER", ko="DELAYED_SILHOUETTE", shape="SHADOW_SLASH", cue="TIK_SHING" },
  TRAPPER = { hit="LIFT_SPIN", ko="SAFE_DROP_ROLL", shape="PSYCHIC_ORBIT", cue="WHUP_POP" },
  BUILDER = { hit="SPRING_BOUNCE", ko="CARTOON_COMPRESS", shape="GEAR_PRESS", cue="BOING_BONK" },
  BEAST = { hit="TAIL_TUMBLE", ko="STAMPEDE_DOMINO", shape="PAW_WAVE", cue="ROAR_THUMP" },
  ZOMBIE = { hit="CURSE_TWITCH", ko="SHADOW_UNRAVEL", shape="CURSE_SIGIL", cue="CURSE_CHIME" },
}
local ELEMENT_KO = { FIRE="FLAME_WHIRL", ICE="ICE_CRYSTAL_POP", WATER="BUBBLE_SPLASH",
 LIGHTNING="SPARK_FAN", WIND="CYCLONE_TUMBLE", EARTH="ROCK_BOUNCE",
 DIVINE="HALO_SPARKLES", CURSE="CURSE_SMOKE" }
local ELEMENT_SHAPE = { FIRE="FLAME_TAIL", ICE="CRYSTAL", WATER="WAVE",
 LIGHTNING="ZIGZAG", WIND="SWIRL", EARTH="ROCK", DIVINE="HALO", CURSE="CHAIN" }

function M.species(id:string):any
 local entry = SPECIES[id]
 if not entry then return nil end
 return table.clone(entry)
end
function M.listSpecies():{string}
 local ids={}
 for id in pairs(SPECIES) do table.insert(ids,id) end
 table.sort(ids)
 return ids
end
function M.select(receipt:any):any
 -- Treat all client-originated/nil cues as invalid; consumers must use server-only receipt.
 if type(receipt)~="table" or receipt.serverConfirmed~=true
  or type(receipt.uniqueHitId)~="string" or receipt.uniqueHitId=="" then return nil end
 if receipt.targetIsNeutral~=true or receipt.isFriendly==true then return nil end
 local role=ROLE[receipt.role]
 local species=SPECIES[receipt.species]
 if not role or not species then return nil end
 if receipt.matchActive~=true or receipt.epochCurrent~=true then return nil end
 local isKO=receipt.ko==true
 local effect=if isKO then role.ko else role.hit
 local shape=role.shape
 if ELEMENT_SHAPE[receipt.element] then shape=ELEMENT_SHAPE[receipt.element] end
 if isKO and ELEMENT_KO[receipt.element] then effect=ELEMENT_KO[receipt.element] end
 -- A hit that did not produce an actual KO MUST NOT play a kill/despawn animation.
 local tier=if receipt.deviceTier=="LOW" then "LOW" else "NORMAL"
 local range=math.max(0, tonumber(receipt.distanceStuds) or 0)
 if range>100 then return nil end
 local visible=receipt.visible==true
 if not visible and range>24 then return nil end
 local particleCap=if tier=="LOW" then 4 else 12
 if range>45 then particleCap=math.min(2,particleCap) end
 local maxTargets=if tier=="LOW" then 5 else 12
 local combo=math.max(0,tonumber(receipt.combo) or 0)
 local startOffset=math.min(0.1,math.max(0,tonumber(receipt.ordinal) or 0)*0.013)
 return {
  kind=if isKO then "KO" else "HIT", targetId=receipt.targetId, eventId=receipt.uniqueHitId,
  species=receipt.species, role=receipt.role, personality=species.personality,
  expression=species.motion, finisher=effect, shape=shape, sound=role.cue,
  colorIndependentGlyph=shape, particles=particleCap, maxSimultaneousTargets=maxTargets,
  staggerSeconds=startOffset, lifetime=if tier=="LOW" then 0.32 else 0.65,
  comboAccent=combo>=12, noGore=true, cosmeticOnly=true,
 }
end
M.ROLE_COUNT=7
M.SPECIES_COUNT=8
return M
