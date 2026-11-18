#!/usr/bin/env python3
"""Actual source-derived Luau good/mutant harness for #765 lane8; no mock implementation."""
from pathlib import Path
import argparse

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "EGGRUMBLE_MageRescuePolicy.luau"
MUTANT_MARKER = "ctx.now - record.startedAt < P.REVIVE_CHANNEL_SECONDS"

TESTS = r'''
local P = policy
local function clone(t)
 local c = {}
 for k,v in pairs(t) do c[k] = v end
 return c
end
local c = {
 epoch="TEAM:77", mode="TEAM", now=100, distance=12, lineClear=true,
 casterRole="MAGE", casterActive=true, targetActive=true,
 casterAlive=true, casterCastleAlive=true, targetCastleAlive=true,
 casterId=101, targetId=102, casterCharacterKey="101:a", targetCharacterKey="102:b",
 casterTeam="RED", targetTeam="RED", targetHP=100, targetMaxHP=200,
 targetDowned=false, downedAt=0,
}
local s = P.newState("TEAM:77")
local amount, reason = P.heal(s,c)
assert(amount==60 and reason=="HEAL","RED_HEAL_30_PERCENT")
amount,reason=P.heal(s,c)
assert(amount==0 and reason=="HEAL_COOLDOWN","RED_HEAL_18_COOLDOWN")
c.now=118
c.targetHP=195
amount,reason=P.heal(s,c)
assert(amount==5 and reason=="HEAL","RED_HEAL_CAP")
c.now=137
c.targetHP=200
amount,reason=P.heal(s,c)
assert(amount==0 and reason=="NO_WASTED_HEAL","RED_NO_WASTED_COOLDOWN")
c.targetHP=100
amount,reason=P.heal(s,c)
assert(amount==60 and reason=="HEAL","RED_NO_WASTED_HEAL_DID_NOT_CONSUME")

local bad=clone(c)
bad.casterRole="WARRIOR"
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="INACTIVE_OR_WRONG_ROLE","RED_WRONG_ROLE")
bad=clone(c);bad.targetTeam="BLUE"
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="ENEMY_TEAM","RED_ENEMY_HEAL")
bad=clone(c);bad.lineClear=false
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="BLOCKED_WALL","RED_WALL_HEAL")
bad=clone(c);bad.distance=23
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="INVALID_RANGE_TIME","RED_RANGE")
bad=clone(c);bad.epoch="TEAM:OLD"
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="STALE_SESSION","RED_STALE_MATCH")
bad=clone(c);bad.casterActive=false
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="INACTIVE_OR_WRONG_ROLE","RED_STALE_CASTER")
bad=clone(c);bad.targetHP=0
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="DOWNED_OR_DEAD","RED_DEAD_HEAL")
bad=clone(c);bad.targetHP=0/0
amount,reason=P.heal(s,bad)
assert(amount==0 and reason=="BAD_HP","RED_NAN")

-- BR permits Mage self-heal but never remote other-player healing.
local br=clone(c);br.mode="BR";br.casterId=102;br.casterCharacterKey=br.targetCharacterKey
local bs=P.newState("TEAM:77")
amount,reason=P.heal(bs,br)
assert(amount==60 and reason=="HEAL","RED_BR_SELF_HEAL")
br.casterId=103;br.casterCharacterKey="103:new"
amount,reason=P.heal(bs,br)
assert(amount==0 and reason=="BR_SELF_ONLY","RED_BR_OTHER_HEAL")

-- Protected downed=1HP is a caller-owned Host state. No dead Humanoid resurrection.
local v=clone(c)
v.now=200;v.targetHP=1;v.targetDowned=true;v.downedAt=199
local t,why=P.beginRevive(s,v)
assert(type(t)=="number" and why=="CHANNEL_STARTED","RED_CHANNEL_START")
local denied,why2=P.beginRevive(s,v)
assert(denied==nil and why2=="TARGET_ALREADY_RESERVED","RED_DOUBLE_REVIVE_RACE")
local second=clone(v);second.casterId=103;second.casterCharacterKey="103:new"
denied,why2=P.beginRevive(s,second)
assert(denied==nil and why2=="TARGET_ALREADY_RESERVED","RED_OTHER_MAGE_RACE")
local third=clone(v);third.targetId=104;third.targetCharacterKey="104:fresh"
denied,why2=P.beginRevive(s,third)
assert(denied==nil and why2=="CASTER_ALREADY_CHANNELING","RED_SAME_MAGE_PARALLEL_CHANNEL")
v.now=202.999
amount,reason=P.completeRevive(s,v,t)
assert(amount==0 and reason=="CHANNEL_INCOMPLETE","RED_EARLY_CHANNEL")
v.now=203
amount,reason=P.completeRevive(s,v,t)
assert(amount==70 and reason=="REVIVE","RED_35_PERCENT_REVIVE")
amount,reason=P.completeRevive(s,v,t)
assert(amount==0 and reason=="NO_MATCHING_TICKET","RED_DUPLICATE_COMPLETION")
v.now=204;v.downedAt=204
denied,why2=P.beginRevive(s,v)
assert(denied==nil and why2=="REVIVE_COOLDOWN","RED_REVIVE_40_COOLDOWN")

-- One failed stale-character completion cannot revive a replaced avatar.
local s2=P.newState("TEAM:77")
v.now=300;v.downedAt=299
local t2=P.beginRevive(s2,v)
assert(type(t2)=="number","RED_SECOND_CHANNEL")
local old=clone(v);old.targetCharacterKey="102:respawn";old.now=303
amount,reason=P.completeRevive(s2,old,t2)
assert(amount==0 and reason=="STALE_AVATAR_OR_CASTER","RED_STALE_AVATAR")
assert(P.cancelRevive(s2,102,t2)==true,"RED_CANCEL")
assert(P.cancelRevive(s2,102,t2)==false,"RED_DOUBLE_CANCEL")

local s3=P.newState("TEAM:77")
local expired=clone(v);expired.now=400;expired.downedAt=340
denied,why2=P.beginRevive(s3,expired)
assert(denied==nil and why2=="DOWNED_WINDOW_EXPIRED","RED_60SEC_WINDOW")
expired=clone(v);expired.now=400;expired.downedAt=399;expired.targetHP=0
denied,why2=P.beginRevive(s3,expired)
assert(denied==nil and why2=="NOT_PROTECTED_DOWNED","RED_REAL_DEATH")
expired=clone(v);expired.now=400;expired.downedAt=399;expired.mode="BR"
denied,why2=P.beginRevive(s3,expired)
assert(denied==nil and why2=="BR_SELF_ONLY","RED_BR_CROSS_PLAYER")
expired=clone(v);expired.now=400;expired.downedAt=399;expired.casterTeam="BLUE"
denied,why2=P.beginRevive(s3,expired)
assert(denied==nil and why2=="ENEMY_TEAM","RED_PVP_REVIVE")
print("GQ8_MAGE_SOURCE_DERIVED_LUAU_HEAL_CHANNEL_REVIVE_PASS")
'''

def emit(out: Path) -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.rstrip().endswith("return P"), "RED_SOURCE_EXPORT"
    assert source.count(MUTANT_MARKER) == 1, "RED_CHANNEL_TEST_MARKER"
    body = source.rstrip()[:-len("return P")]
    out.mkdir(parents=True, exist_ok=True)
    (out / "good.luau").write_text(body + "\nlocal policy=P\n" + TESTS, encoding="utf-8")
    mutant = body.replace(MUTANT_MARKER, "ctx.now - record.startedAt < 0", 1)
    (out / "mutant.luau").write_text(mutant + "\nlocal policy=P\n" + TESTS, encoding="utf-8")
    print("GQ8_MAGE_ACTUAL_SOURCE_DERIVED_GOOD_MUTANT_READY")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    emit(parser.parse_args().out)
