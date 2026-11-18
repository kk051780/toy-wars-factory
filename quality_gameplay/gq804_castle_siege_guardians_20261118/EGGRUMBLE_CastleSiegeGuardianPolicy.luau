--!strict
-- GQ804: PURE siege authorization/guardian spawn proposals for original CastleMatchRules.
-- No Humanoid, damage, Remote, DataStore, score, wallet or NPC owner. Single Host/Rules apply all results.
local M={}
local GUARDIANS={
 WARRIOR={basic="SHIELD_KNIGHT",advanced="WAR_BANNER",tactic="FRONTAL_BLOCK",cue="SHIELD_BELL"},
 MAGE={basic="ICE_MAGE",advanced="STAR_HEALER",tactic="ICE_SLOW",cue="CRYSTAL_CHIME"},
 NINJA={basic="SHADOW_SCOUT",advanced="PHANTOM_DUELIST",tactic="AMBUSH",cue="SHADOW_WHIP"},
 TRAPPER={basic="PSY_PUPPET",advanced="GRAVITY_KEEPER",tactic="PUSH_BACK",cue="ORBIT_POP"},
 BUILDER={basic="CLOCK_GOLEM",advanced="SPRING_ARTILLERY",tactic="SIEGE_DEFLECT",cue="GEAR_BONK"},
 BEAST={basic="GUARD_WOLF",advanced="ARMORED_BEAST",tactic="PACK_CHARGE",cue="GUARD_HOWL"},
 ZOMBIE={basic="CURSE_SOLDIER",advanced="WRAITH_BEARER",tactic="SHORT_CURSE",cue="CURSE_CHIME"},
}
local THRESHOLDS={700,400,200}
local GATE_MAX=180
local GATE_ATTACKER_COOLDOWN=1
local GATE_WINDOW_SECONDS=5
local GATE_MAX_DAMAGE_WINDOW=72
local HP_MAX=1000
local MAX_CASTLE_DAMAGE_WINDOW=150
local WINDOW_SECONDS=5
local ATTACKER_COOLDOWN=1
local SUMMON_COOLDOWN=40
local MAX_ACTIVE=2
local MAX_TOTAL=3
function M.new(matchId:string,castleId:string):any
 assert(type(matchId)=="string" and #matchId>3)
 assert(type(castleId)=="string" and castleId~="")
 return {matchId=matchId,castleId=castleId,gateHP=GATE_MAX,castleHP=HP_MAX,stage="GATE",
  alive=true,gateLastAttacks={},gateHitHistory={},gateClock=-math.huge,
  lastAttacks={},windowAt=-math.huge,windowDamage=0,guardianThresholdUsed={},
  guardianTotal=0,guardianActive={},lastSummon=-math.huge}
end
local function ctx(s:any,r:any):boolean
 return s.alive and type(r)=="table" and r.verifiedByServer==true
  and r.matchId==s.matchId and r.targetCastleId==s.castleId
  and r.phase=="ACTIVE" and r.ownerCastleAlive==true
end
local function legalAttack(s:any,r:any):boolean
 return ctx(s,r) and type(r.attackerId)=="string" and r.attackerId~=""
  and r.attackerId~=s.castleId and r.attackerCastleAlive==true
  and r.isEnemy==true and r.matchMember==true
  and r.losClear==true and r.reachable==true and r.withinRange==true
end
local function validAmount(v:any):boolean
 return type(v)=="number" and v==v and v>0 and v<math.huge
end
function M.gateHit(s:any,r:any):any
 if not legalAttack(s,r) or s.stage~="GATE" or not validAmount(r.damage)
  or type(r.now)~="number" or r.now~=r.now or math.abs(r.now)==math.huge then return nil end
 -- Server time, not client time. Rolling (not bucketed) 5s total
 -- prevents boundary exploits where several allies double-burst a castle.
 if r.now<s.gateClock then return nil end
 if r.now-(s.gateLastAttacks[r.attackerId] or -math.huge)<GATE_ATTACKER_COOLDOWN then return nil end
 local used=0
 for i=#s.gateHitHistory,1,-1 do
  local hit=s.gateHitHistory[i]
  if r.now-hit.at>=GATE_WINDOW_SECONDS then
   table.remove(s.gateHitHistory,i)
  else
   used+=hit.amount
  end
 end
 local amount=math.min(36,math.floor(r.damage),GATE_MAX_DAMAGE_WINDOW-used)
 if amount<1 then return nil end
 table.insert(s.gateHitHistory,{at=r.now,amount=amount})
 s.gateClock=r.now
 s.gateLastAttacks[r.attackerId]=r.now
 s.gateHP=math.max(0,s.gateHP-amount)
 if s.gateHP==0 then s.stage="CORE" end
 return {kind=if s.gateHP==0 then "BREACH_READY" else "GATE_HIT",
  gateRemaining=s.gateHP,damageToGate=amount,serverAnimationOnly=true}
end
local function isQualified(r:any):boolean
 local weapon=tonumber(r.weaponSiegeRating) or 0
 local skill=tonumber(r.skillSiegeRating) or 0
 local mastery=tonumber(r.masteryLevel) or 0
 return weapon>=2 or skill>=2
  or (mastery>=10 and r.earnedSiegeSkillVerified==true)
  or (type(r.coordinatedHumanCount)=="number" and r.coordinatedHumanCount>=2)
  or r.freeSiegeToolVerified==true
  or r.friendlyAIHelperVerified==true
end
function M.corePermit(s:any,r:any):any
 if not legalAttack(s,r) or s.stage=="GATE" or s.stage=="FALLEN" or not isQualified(r)
  or not validAmount(r.damage) or type(r.now)~="number" or r.now~=r.now then return nil end
 if r.now-(s.lastAttacks[r.attackerId] or -math.huge)<ATTACKER_COOLDOWN then return nil end
 local used=if r.now-s.windowAt>=WINDOW_SECONDS then 0 else s.windowDamage
 local remaining=MAX_CASTLE_DAMAGE_WINDOW-used
 if remaining<=0 then return nil end
 local damage=math.min(math.floor(r.damage),60,remaining)
 if damage<1 then return nil end
 -- Caller must immediately pass damage to one original Rules.damageCastle;
 -- it MUST only call commitCorePermit after that original source returns success.
 return {kind="ORIGINAL_CASTLE_DAMAGE_PERMIT",damage=damage,attackerId=r.attackerId,
  matchId=s.matchId,castleId=s.castleId,issuedAt=r.now,
  requiresSameServerCall=true,requiresOriginalRules=true}
end
function M.commitCorePermit(s:any,permit:any,confirmed:any):boolean
 if type(permit)~="table" or permit.kind~="ORIGINAL_CASTLE_DAMAGE_PERMIT"
  or permit.matchId~=s.matchId or permit.castleId~=s.castleId
  or type(confirmed)~="table" or confirmed.originalRulesAccepted~=true
  or confirmed.matchId~=s.matchId or confirmed.castleId~=s.castleId
  or not validAmount(confirmed.actualDamage) or confirmed.actualDamage>permit.damage then return false end
 local at=permit.issuedAt
 if type(at)~="number" then return false end
 if at-(s.lastAttacks[permit.attackerId] or -math.huge)<ATTACKER_COOLDOWN then return false end
 if at-s.windowAt>=WINDOW_SECONDS then s.windowAt=at;s.windowDamage=0 end
 if s.windowDamage+confirmed.actualDamage>MAX_CASTLE_DAMAGE_WINDOW then return false end
 s.lastAttacks[permit.attackerId]=at
 s.windowDamage+=confirmed.actualDamage
 return true
end
function M.recordOriginalCastleHp(s:any,r:any):any
 if not ctx(s,r) or type(r.hp)~="number" or r.hp~=r.hp or r.hp<0 or r.hp>HP_MAX
  or r.originalRulesAccepted~=true then return nil end
 s.castleHP=r.hp
 if r.hp==0 then s.alive=false;s.stage="FALLEN";return {kind="TRUE_CASTLE_FALL"} end
 if s.stage=="GATE" then return {kind="GATE_PROTECTED",hp=r.hp} end
 if r.hp<=200 then s.stage="FINAL"
 elseif r.hp<=700 then s.stage="INNER"
 else s.stage="CORE" end
 return {kind="CASTLE_HP_UPDATE",stage=s.stage,hp=r.hp,
  worldGauge=true,serverConfirmedOnly=true}
end
local function activeCount(s:any):number local n=0 for _ in pairs(s.guardianActive) do n+=1 end return n end
function M.guardianProposal(s:any,r:any):any
 if not ctx(s,r) or s.stage=="GATE" or s.guardianTotal>=MAX_TOTAL
  or activeCount(s)>=MAX_ACTIVE or type(r.now)~="number"
  or r.now-s.lastSummon<SUMMON_COOLDOWN then return nil end
 if not r.equippedGuardianOwnedByCastle or type(r.role)~="string" then return nil end
 local spec=GUARDIANS[r.role]
 if not spec or type(r.guardianMasteryLevel)~="number" or r.guardianMasteryLevel<1 then return nil end
 local roleName=if r.guardianMasteryLevel>=10 then spec.advanced else spec.basic
 if r.equippedGuardianType~=roleName and r.equippedGuardianType~=spec.basic then return nil end
 for _,threshold in ipairs(THRESHOLDS) do
  if s.castleHP<=threshold and not s.guardianThresholdUsed[threshold] then
   local tier=if r.guardianMasteryLevel>=25 then 3 elseif r.guardianMasteryLevel>=10 then 2 else 1
   return {kind="ORIGINAL_CASTLE_GUARDIAN_SPAWN_PROPOSAL",threshold=threshold,
    typeId=r.equippedGuardianType,role=r.role,tier=tier,tactic=spec.tactic,cue=spec.cue,
    maxLifetimeSeconds=45,requiresOriginalAIAndDamageOwner=true}
  end
 end
 return nil
end
function M.confirmGuardianSpawn(s:any,p:any,r:any):boolean
 if not p or p.kind~="ORIGINAL_CASTLE_GUARDIAN_SPAWN_PROPOSAL"
  or not ctx(s,r) or r.serverSpawnAccepted~=true
  or type(r.actorId)~="string" or r.actorId=="" or s.guardianActive[r.actorId]
  or type(r.now)~="number" or r.now-s.lastSummon<SUMMON_COOLDOWN
  or s.guardianTotal>=MAX_TOTAL or activeCount(s)>=MAX_ACTIVE
  or s.guardianThresholdUsed[p.threshold] or s.castleHP>p.threshold then return false end
 s.guardianThresholdUsed[p.threshold]=true
 s.guardianActive[r.actorId]={at=r.now,expires=r.now+45}
 s.guardianTotal+=1;s.lastSummon=r.now
 return true
end
function M.releaseGuardian(s:any,actorId:string,serverConfirmed:boolean):boolean
 if serverConfirmed~=true or not s.guardianActive[actorId] then return false end
 s.guardianActive[actorId]=nil;return true
end
M.CASTLE_HP=HP_MAX
M.GATE_HP=GATE_MAX
M.MAX_ACTIVE=MAX_ACTIVE
M.MAX_TOTAL=MAX_TOTAL
M.GUARDIAN_ROLES=7
return M
