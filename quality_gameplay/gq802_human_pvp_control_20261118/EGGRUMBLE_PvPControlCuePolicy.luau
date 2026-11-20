--!strict
-- GQ802: Human-versus-human elemental control & presentation POLICY ONLY.
-- Gameplay damage, health, PVP legality, physics and result credit still belong
-- to the existing Combat owner. Only a server-verified receipt can be presented.
local M={}
M.ROLE_COUNT=7
M.ELEMENT_COUNT=8

local ROLES={
 WARRIOR={shape="FAN_SLASH",sound="SHING_IMPACT",motion="POWER_SWEEP"},
 MAGE={shape="GLYPH_SPIRAL",sound="MAGIC_POP",motion="ARCANE_PULSE"},
 NINJA={shape="SHADOW_LINES",sound="WHIP_CUT",motion="SHADOW_DASH"},
 TRAPPER={shape="PSYCHIC_RING",sound="SPACE_WHOOSH",motion="LIFT_AND_RELEASE"},
 BUILDER={shape="GEAR_PRESS",sound="BOING_IMPACT",motion="CARTOON_SQUASH"},
 BEAST={shape="BEAST_PAW",sound="ROAR_IMPACT",motion="TAIL_SWEEP"},
 ZOMBIE={shape="CURSE_SEAL",sound="LOW_CHIME",motion="SHADOW_CHAINS"},
}
local ELEMENT={
 FIRE={status="BURN_MARK",duration=2.5,hard=false,impulse=0,icon="FLAME",vfx="EMBER_TRAIL"},
 ICE={status="FREEZE",duration=0.9,hard=true,impulse=0,icon="SNOW_CRYSTAL",vfx="FROZEN_CRACK"},
 LIGHTNING={status="SHOCK",duration=0.55,hard=true,impulse=0,icon="ZIGZAG",vfx="SPARK_CAGE"},
 WATER={status="WET_SLOW",duration=1.8,hard=false,impulse=0,icon="BUBBLE",vfx="BUBBLE_SHELL"},
 WIND={status="KNOCKBACK",duration=0.35,hard=true,impulse=14,icon="SPIRAL",vfx="SAFE_AIR_ROLL"},
 EARTH={status="STAGGER",duration=0.4,hard=true,impulse=4,icon="ROCK",vfx="COMIC_COMPRESS"},
 DIVINE={status="RADIANT_MARK",duration=2,hard=false,impulse=0,icon="HALO",vfx="SUNBEAM_BURST"},
 CURSE={status="CURSE_MARK",duration=2.5,hard=false,impulse=0,icon="CHAIN",vfx="DARK_PUPPET_PULSE"},
}
local function finiteNumber(v:any):boolean
 return type(v)=="number" and v==v and v>-math.huge and v<math.huge
end
local function bounded(v:any, minimum:number, maximum:number):number?
 if not finiteNumber(v) or v<minimum or v>maximum then return nil end
 return v
end
function M.select(receipt:any):any
 -- Avoid interpreting a client cue or a non-damaging hit as real PVP impact.
 if type(receipt)~="table" or receipt.serverConfirmedHit~=true
  or receipt.matchActive~=true or receipt.epochCurrent~=true
  or receipt.victimIsHuman~=true or receipt.attackerIsHuman~=true
  or receipt.sameTeam==true or receipt.spawnProtected==true
  or receipt.targetAlive~=true or receipt.attackerAlive~=true
  or type(receipt.uniqueHitId)~="string" or receipt.uniqueHitId=="" then return nil end
 local role=ROLES[receipt.role]
 local element=ELEMENT[receipt.element]
 if not role or not element then return nil end
 local distance=bounded(receipt.distanceStuds,0,100)
 local now=bounded(receipt.serverTimeSeconds,0,1e10)
 local recentControls=bounded(receipt.targetHardCCCount8s,0,99)
 local recentCCDuration=bounded(receipt.targetHardCCSeconds8s,0,8)
 local immuneUntil=bounded(receipt.targetControlImmunityUntil,0,1e10)
 if not distance or not now or not recentControls or not recentCCDuration or not immuneUntil then return nil end
 if distance>80 and receipt.visible~=true then return nil end
 local low=receipt.deviceTier=="LOW"
 local hard=element.hard
 local duration=element.duration
 local status=element.status
 local knockStuds=element.impulse
 -- A single player cannot repeatedly lose all control. Hard controls total
 -- < 1.8s per rolling 8s, 2 events max; bypass uses non-stacking soft slow.
 if hard and (now<immuneUntil or recentControls>=2
     or recentCCDuration+duration>1.8) then
   hard=false
   duration=0.6
   status="BRIEF_SLOW"
   knockStuds=0
 end
 return {
   receiptId=receipt.uniqueHitId, role=receipt.role, element=receipt.element,
   status=status, durationSeconds=duration, hardControl=hard,
   -- Vector and authority resolved ONLY by existing server Combat physics.
   maxHorizontalImpulseStuds=knockStuds,
   fallRescueRequired=knockStuds>0,
   existingDamageReceiptOnly=true, applyDamageHere=false,
   cannotSetHealth=true, newRemoteOwner=false,
   stackPolicy="ONE_SOFT_STATUS_PER_ELEMENT",
   glyph=element.icon, vfx=element.vfx, roleShape=role.shape,
   roleMotion=role.motion, sound=role.sound,
   particleBudget=if low then 4 else 12,
   lifetimeSeconds=if low then 0.32 else 0.6,
   noGore=true, colorIndependent=true,
 }
end
return M
