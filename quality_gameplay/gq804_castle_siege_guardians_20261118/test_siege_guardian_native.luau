--!strict
local P=require("./EGGRUMBLE_CastleSiegeGuardianPolicy")
local function req()
 return {verifiedByServer=true,matchId="TEAM:2026",targetCastleId="castle-blue",
  phase="ACTIVE",ownerCastleAlive=true,attackerId="hero-red",attackerCastleAlive=true,
  isEnemy=true,matchMember=true,losClear=true,reachable=true,withinRange=true,
  damage=26,now=0,weaponSiegeRating=0,skillSiegeRating=0,masteryLevel=1,
  coordinatedHumanCount=1,freeSiegeToolVerified=false,friendlyAIHelperVerified=false}
end
local s=P.new("TEAM:2026","castle-blue")
assert(P.CASTLE_HP==1000 and P.GATE_HP==180)
local a=req()
assert(P.corePermit(s,a)==nil)
a.losClear=false;assert(P.gateHit(s,a)==nil)
a.losClear=true;a.isEnemy=false;assert(P.gateHit(s,a)==nil)
a.isEnemy=true;a.damage=100
-- A gate cannot vanish in five zero-time spam hits, even for one valid server attacker.
a.now=0
local first=P.gateHit(s,a)
assert(first and first.gateRemaining==144)
assert(P.gateHit(s,a)==nil and s.gateHP==144)
a.now=1.1
local second=P.gateHit(s,a)
assert(second and second.gateRemaining==108)
a.now=2.2
assert(P.gateHit(s,a)==nil and s.gateHP==108)
local ally=req()
ally.attackerId="hero-red-ally";ally.damage=100;ally.now=3.3
assert(P.gateHit(s,ally)==nil and s.gateHP==108) -- global team damage cap
a.now=5.1
assert(P.gateHit(s,a).gateRemaining==72)
a.now=6.2
assert(P.gateHit(s,a).gateRemaining==36)
a.now=6.3
assert(P.gateHit(s,a)==nil)
a.now=10.2
assert(P.gateHit(s,a).gateRemaining==0)
assert(s.stage=="CORE")
assert(P.gateHit(s,a)==nil)
local invalidTime=P.new("TEAM:2026","castle-blue")
local badClock=req();badClock.now=math.huge
assert(P.gateHit(invalidTime,badClock)==nil)
badClock.now=0/0
assert(P.gateHit(invalidTime,badClock)==nil)
-- The fixed-bucket implementation used to allow 144 HP near a 5s boundary.
local boundary=P.new("TEAM:2026","castle-blue")
local rush=req();rush.damage=100;rush.now=4.90
assert(P.gateHit(boundary,rush).gateRemaining==144)
rush.attackerId="hero-ally";rush.now=4.99
assert(P.gateHit(boundary,rush).gateRemaining==108)
rush.attackerId="hero-third";rush.now=5.01
assert(P.gateHit(boundary,rush)==nil and boundary.gateHP==108)
rush.now=4.98
assert(P.gateHit(boundary,rush)==nil and boundary.gateHP==108) -- stale server time
rush.now=9.91
assert(P.gateHit(boundary,rush).gateRemaining==72)
a.damage=100;a.weaponSiegeRating=1
assert(P.corePermit(s,a)==nil)
a.freeSiegeToolVerified=true
local permit=P.corePermit(s,a)
assert(permit and permit.damage==60)
assert(not P.commitCorePermit(s,permit,{originalRulesAccepted=false,matchId="TEAM:2026",castleId="castle-blue",actualDamage=60}))
assert(P.commitCorePermit(s,permit,{originalRulesAccepted=true,matchId="TEAM:2026",castleId="castle-blue",actualDamage=60}))
assert(P.corePermit(s,a)==nil)
a.now=11.3
assert(P.corePermit(s,a).damage==60)
local b=P.corePermit(s,a)
assert(P.commitCorePermit(s,b,{originalRulesAccepted=true,matchId="TEAM:2026",castleId="castle-blue",actualDamage=60}))
a.now=12.4;assert(P.corePermit(s,a).damage==30)
local c=P.corePermit(s,a);assert(P.commitCorePermit(s,c,{originalRulesAccepted=true,matchId="TEAM:2026",castleId="castle-blue",actualDamage=30}))
a.now=13.5;assert(P.corePermit(s,a)==nil)
a.now=15.4;assert(P.corePermit(s,a).damage==60)
local low=req();low.now=16;low.weaponSiegeRating=0;low.coordinatedHumanCount=2
assert(P.corePermit(s,low)~=nil)
low.coordinatedHumanCount=1;low.masteryLevel=10;low.earnedSiegeSkillVerified=true
assert(P.corePermit(s,low)~=nil)
low.earnedSiegeSkillVerified=false;low.friendlyAIHelperVerified=true
assert(P.corePermit(s,low)~=nil)
low.friendlyAIHelperVerified=false;assert(P.corePermit(s,low)==nil)
local hp=req();hp.originalRulesAccepted=true;hp.hp=690
assert(P.recordOriginalCastleHp(s,hp).stage=="INNER")
local guard={verifiedByServer=true,matchId="TEAM:2026",targetCastleId="castle-blue",
 phase="ACTIVE",ownerCastleAlive=true,now=20,role="WARRIOR",guardianMasteryLevel=25,
 equippedGuardianOwnedByCastle=true,equippedGuardianType="WAR_BANNER"}
local proposal=P.guardianProposal(s,guard)
assert(proposal and proposal.threshold==700 and proposal.tier==3)
guard.actorId="guard1";guard.serverSpawnAccepted=true
assert(P.confirmGuardianSpawn(s,proposal,guard))
assert(not P.confirmGuardianSpawn(s,proposal,guard))
guard.now=21;assert(P.guardianProposal(s,guard)==nil)
guard.now=61;hp.hp=390;assert(P.recordOriginalCastleHp(s,hp).stage=="INNER")
local p2=P.guardianProposal(s,guard);assert(p2 and p2.threshold==400)
guard.actorId="guard2";assert(P.confirmGuardianSpawn(s,p2,guard))
guard.now=105;hp.hp=190;assert(P.recordOriginalCastleHp(s,hp).stage=="FINAL")
assert(P.guardianProposal(s,guard)==nil)
assert(P.releaseGuardian(s,"guard1",true))
local p3=P.guardianProposal(s,guard);assert(p3 and p3.threshold==200)
guard.actorId="guard3";assert(P.confirmGuardianSpawn(s,p3,guard))
guard.now=160;assert(P.guardianProposal(s,guard)==nil)
hp.hp=0;assert(P.recordOriginalCastleHp(s,hp).kind=="TRUE_CASTLE_FALL")
assert(P.guardianProposal(s,guard)==nil)
local invalid=P.new("BR:2026","castle-blue")
local bad=req();bad.matchId="TEAM:2026"
assert(P.gateHit(invalid,bad)==nil)
print("GQ804_SIEGE_GATE_CORE_BUDGET_GUARDIAN_7ROLE_NATIVE_PASS")
