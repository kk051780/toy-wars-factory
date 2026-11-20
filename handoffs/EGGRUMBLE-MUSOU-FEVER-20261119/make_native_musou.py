#!/usr/bin/env python3
"""Exact policy source executed by pinned native Luau VM; no logic mirrored in Python."""
from pathlib import Path
import argparse

SOURCE=Path(__file__).with_name("MusouFeverPolicy.luau")
CONTRACT=r'''
__EXACT_POLICY_SOURCE__
local p=M
local function close(a,b) return math.abs(a-b)<.00001 end
local function ctx(role,now,epoch,mode)
 return {epoch=epoch or "matchA",playerId="p1",avatarEpoch="avatar1",
  role=role,now=now,mode=mode or "TEAM",phase="ACTIVE",
  serverCurrent=true,roleVerified=true,characterAlive=true,castleAlive=true,
  downed=false,eliminated=false,carryingEgg=false,shieldActive=false,
  invulnerable=false}
end
local function ko(n,kind)
 return {serverConfirmed=true,enemyConfirmed=true,creditVerified=true,
  scoreEligible=true,creditedPlayerId="p1",victimId="victim"..n,
  receiptId="receipt"..n,targetKind=kind or "NEUTRAL",
  isSummoned=false,isConverted=false}
end
local specs={
 WARRIOR={3.8,1.30,1.35,.70},
 MAGE={3.6,1.25,1.35,.65},
 NINJA={3.5,1.35,1.25,.60},
 TRAPPER={3.6,1.22,1.30,.65},
 BUILDER={3.7,1.22,1.35,.70},
 BEAST={4.0,1.28,1.40,.70},
 ZOMBIE={3.4,1.20,1.30,.60}
}
local count=0
for role,a in pairs(specs) do
 local s=p.newRound("matchA",0)
 local c=ctx(role,69)
 local ok,why=p.activate(s,c)
 assert(not ok and why=="RECHARGING","RED_EARLY_FREE_CHARGE")
 c.now=70
 local success,receipt=p.activate(s,c)
 assert(success and receipt.phase=="MUSOU","RED_ROLE_NOT_PLAYABLE")
 assert(p.snapshot(s,c).visibleToEnemies==true,"RED_NO_VISIBLE_TELL")
 assert(p.snapshot(s,c).sigil~=nil,"RED_ROLE_VISUAL_MISSING")
 assert(close(p.attackMultiplier(s,c,"NEUTRAL"),a[1]),"RED_PVE_POWER")
 assert(close(p.attackMultiplier(s,c,"HUMAN"),a[2]),"RED_PVP_BALANCE")
 assert(p.attackMultiplier(s,c,"HUMAN")<=1.35,"RED_PVP_INSTANT_KILL")
 assert(close(p.attackMultiplier(s,c,"BOSS"),a[3]),"RED_BOSS_BALANCE")
 assert(close(p.attackMultiplier(s,c,"CASTLE"),a[4]),"RED_SIEGE_BYPASS")
 assert(p.attackMultiplier(s,c,"UNKNOWN")==1,"RED_UNKNOWN_TARGET")
 assert(not p.allowEggObjective(s,c),"RED_EGG_OBJECTIVE_DURING_MUSOU")
 local again,reason=p.activate(s,c)
 assert(not again and reason=="ALREADY_ACTIVE","RED_STACKED_MUSOU")
 c.now=78
 assert(not p.snapshot(s,c).active,"RED_PERMANENT_MUSOU")
 assert(p.attackMultiplier(s,c,"NEUTRAL")==1,"RED_POWER_PERSISTS")
 assert(p.allowEggObjective(s,c),"RED_EGG_PERMANENT_BLOCK")
 c.now=182
 ok,why=p.activate(s,c)
 assert(not ok and why=="RECHARGING","RED_NO_RECHARGE_COOLDOWN")
 c.now=183
 assert(p.activate(s,c),"RED_TIME_RECHARGE_FAILED")
 assert(s.entries.p1.used==2,"RED_TIME_CHARGE_ACCOUNTING")
 count+=1
end
assert(count==7,"RED_MISSING_ROLE")

local s=p.newRound("matchA",0)
local c=ctx("WARRIOR",70)
assert(p.activate(s,c),"RED_FEV_START")
-- A real KO is needed: never accept arbitrary client, team or duplicate event.
local fake=ko(1)
fake.serverConfirmed=false
assert(not p.onConfirmedKO(s,c,fake),"RED_CLIENT_FORGED_KO")
fake=ko(1);fake.enemyConfirmed=false
assert(not p.onConfirmedKO(s,c,fake),"RED_TEAM_KO_ABUSE")
fake=ko(1);fake.creditVerified=false
assert(not p.onConfirmedKO(s,c,fake),"RED_CREDIT_KO_ABUSE")
fake=ko(1);fake.scoreEligible=false
assert(not p.onConfirmedKO(s,c,fake),"RED_NON_SCORE_KO_ABUSE")
fake=ko(1);fake.creditedPlayerId="p2"
assert(not p.onConfirmedKO(s,c,fake),"RED_STEAL_KO_ABUSE")
fake=ko(1);fake.isSummoned=true
assert(not p.onConfirmedKO(s,c,fake),"RED_SUMMON_FARM")
fake=ko(1);fake.isConverted=true
assert(not p.onConfirmedKO(s,c,fake),"RED_CONVERT_FARM")
fake=ko(1);fake.isSummoned=nil
assert(not p.onConfirmedKO(s,c,fake),"RED_MISSING_SUMMON_PROOF")
fake=ko(1);fake.isConverted=nil
assert(not p.onConfirmedKO(s,c,fake),"RED_MISSING_CONVERT_PROOF")
fake=ko(1);fake.targetKind="CASTLE"
assert(not p.onConfirmedKO(s,c,fake),"RED_CASTLE_FARM")
for i=1,7 do
 c.now=70+.2*i
 local ok,reply=p.onConfirmedKO(s,c,ko(i))
 assert(ok and reply.chain==i,"RED_REAL_KO_CHAIN")
 if i==3 then assert(reply.phase=="RUSH","RED_RUSH_THRESHOLD") end
 if i==7 then
  assert(reply.phase=="KAKUHEN" and reply.fever,"RED_FEVER_THRESHOLD")
  assert(close(reply.endAt,87.5),"RED_FEVER_DURATION")
  assert(close(p.attackMultiplier(s,c,"NEUTRAL"),3.8*1.25),"RED_FEVER_PVE")
  assert(p.attackMultiplier(s,c,"HUMAN")<=1.35,"RED_FEVER_PVP_POWER")
 end
end
local accepted,reason=p.onConfirmedKO(s,c,ko(1))
assert(not accepted and reason=="REPLAYED_KO","RED_REPLAY_KO")
for i=8,24 do
 c.now=70+.2*i
 local good=p.onConfirmedKO(s,c,ko(i))
 assert(good,"RED_VALID_KO_REJECTED")
 assert(s.entries.p1.endsAt<=90,"RED_BURST_OVER_20_SEC")
end
assert(close(s.entries.p1.endsAt,90),"RED_EXPECT_HARD_CAP")
c.now=75
accepted,reason=p.onConfirmedKO(s,c,ko(25))
assert(not accepted and reason=="KO_BUDGET","RED_UNBOUNDED_KO_CREDIT")
c.now=90
assert(not p.snapshot(s,c).active,"RED_HARD_CAP_EXPIRY")
c.now=179
accepted,reason=p.activate(s,c)
assert(not accepted and reason=="RECHARGING","RED_KAKUHEN_FAST_RECHARGE_ABUSE")
c.now=180
assert(p.activate(s,c),"RED_FEVER_RECHARGE_TIME")
assert(s.entries.p1.used==2,"RED_FEVER_CHARGE")
-- Old KO receipts must not be reused in a later activation.
accepted,reason=p.onConfirmedKO(s,c,ko(1))
assert(not accepted and reason=="REPLAYED_KO","RED_CROSS_ACTIVATION_REPLAY")
c.now=180.1
assert(p.onConfirmedKO(s,c,ko(25)),"RED_NEW_REAL_KO_NOT_ACCEPTED")
c.now=181
c.invulnerable=true
assert(p.attackMultiplier(s,c,"NEUTRAL")==1,"RED_INVUL_MUSOU_OVERLAP")
assert(p.cancel(s,c),"RED_INVUL_CANCEL")
c.invulnerable=false
assert(p.attackMultiplier(s,c,"NEUTRAL")==1,"RED_CANCEL_REENABLE")
-- Respawn cannot inherit active status or regenerate charge.
local sr=p.newRound("matchA",0)
local r=ctx("BEAST",70)
assert(p.activate(sr,r),"RED_RESPAWN_SETUP")
r.avatarEpoch="avatar2";r.now=71
assert(not p.snapshot(sr,r).active,"RED_OLD_AVATAR_IMMORTAL")
assert(not p.activate(sr,r),"RED_RESPAWN_EARLY_CHARGE")
r.now=183
assert(p.activate(sr,r),"RED_RESPAWN_RECHARGE_NOT_AVAILABLE")
assert(sr.entries.p1.used==2,"RED_RESPAWN_RESET_CHARGES")
-- Conflicts and late KO cannot bypass objective/round fences.
local sc=p.newRound("matchA",0)
local d=ctx("MAGE",70)
d.carryingEgg=true
assert(not p.activate(sc,d),"RED_EGG_CARRIER_MUSOU")
d.carryingEgg=false;d.shieldActive=true
assert(not p.activate(sc,d),"RED_SHIELD_MUSOU")
d.shieldActive=false;d.invulnerable=true
assert(not p.activate(sc,d),"RED_INVUL_ACTIVATION")
d.invulnerable=false;d.downed=true
assert(not p.activate(sc,d),"RED_DOWNED_ACTIVATION")
d.downed=false;d.serverCurrent=false
assert(not p.activate(sc,d),"RED_UNVERIFIED_CLIENT")
d.serverCurrent=true;d.mode="BATTLE_ROYALE"
assert(p.activate(sc,d),"RED_BR_MODE_BLOCKED")
d.now=71;d.carryingEgg=true
assert(p.attackMultiplier(sc,d,"NEUTRAL")==1,"RED_EGG_WITH_POWER")
assert(not p.allowEggObjective(sc,d),"RED_EGG_PAYOUT_BEFORE_CANCEL")
d.carryingEgg=false
assert(p.cancel(sc,d),"RED_EGG_PICKUP_MUST_CANCEL")
d.now=72
assert(p.attackMultiplier(sc,d,"NEUTRAL")==1,"RED_REACTIVATION_AFTER_CANCEL")
d.epoch="matchB"
assert(p.attackMultiplier(sc,d,"HUMAN")==1,"RED_WRONG_ROUND_ATTACK")
local st=p.newRound("matchB",0)
d.now=70;d.epoch="matchB";d.mode="TEAM"
assert(p.activate(st,d),"RED_NEXT_MATCH_FREE_RECHARGE")
d.now=0/0
assert(p.attackMultiplier(st,d,"NEUTRAL")==1,"RED_NAN_CLOCK")
assert(not p.activate(st,d),"RED_NAN_TRIGGER")
print("GQ8_MUSOU_NATIVE_7ROLE_RECHARGE_RUSH_KAKUHEN_PVP_ROLLBACK_PASS")
'''
def generate(out):
 src=SOURCE.read_text(encoding="utf-8")
 if not src.rstrip().endswith("return M"):raise ValueError("RED_NO_POLICY_MODULE_END")
 body=src.rstrip()[:-len("return M")]
 required=["M.FEVER_BONUS_SECONDS = 6", 'if e.seen[ident(ko.receiptId)] then return false,"REPLAYED_KO" end',
           'elseif targetKind=="HUMAN" then return role.player']
 if any(t not in body for t in required):raise ValueError("RED_UNEXPECTED_MUSOU_SOURCE")
 out.mkdir(parents=True,exist_ok=True)
 (out/"good.luau").write_text(CONTRACT.replace("__EXACT_POLICY_SOURCE__",body),encoding="utf-8")
 mutants={
  "replay_mutant.luau":body.replace('if e.seen[ident(ko.receiptId)] then return false,"REPLAYED_KO" end',
                                  'if false then return false,"REPLAYED_KO" end'),
  "pvp_mutant.luau":body.replace('elseif targetKind=="HUMAN" then return role.player',
                               'elseif targetKind=="HUMAN" then return role.player*4'),
  "fever_mutant.luau":body.replace("M.FEVER_BONUS_SECONDS = 6",
                                 "M.FEVER_BONUS_SECONDS = 60"),
 }
 for name,mutant in mutants.items():
  if mutant==body:raise ValueError("RED_MUTANT_NOT_INSERTED_"+name)
  (out/name).write_text(CONTRACT.replace("__EXACT_POLICY_SOURCE__",mutant),encoding="utf-8")
 print("GQ8_MUSOU_NATIVE_REAL_SOURCE_AND_3_MUTANTS_GENERATED")

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--out",type=Path,required=True)
 generate(parser.parse_args().out)
