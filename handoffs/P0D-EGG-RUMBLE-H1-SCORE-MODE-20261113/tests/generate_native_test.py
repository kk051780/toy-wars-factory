#!/usr/bin/env python3
"""Embed EXACT original H2 pure Luau module in actually executed upstream native test."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument("--write",required=True)
a=p.parse_args()
src=(ROOT/"inputs/H2FiveEggRules.luau").read_text(encoding="utf8")
test=r'''
local Rules=(function()
''' + src + r'''
end)()
local asserts=0
local function ck(cond,label)
    if not cond then error("H2_MULTI_EGG_POLICY_FAIL:"..label) end
    asserts+=1
end
local function equal(actual,expected,label)
    ck(actual==expected,label.." ACTUAL="..tostring(actual).." EXPECTED="..tostring(expected))
end
local function tick(m,n)
    for i=1,n do
        local valid=Rules.advance(m,1)
        ck(valid,"tick_valid")
        ck(Rules.assertConserved(m),"all5_egg_conservation_tick")
    end
end
local function result(ok,reason,expectedOk,expectedReason,tag)
    equal(ok,expectedOk,tag.." ok")
    equal(reason,expectedReason,tag.." reason")
end

local m=Rules.new()
ck(Rules.assertConserved(m),"initial5_eggs")
equal(m.now,0,"start clock")
equal(m.scores.RED,0,"red0")
equal(m.scores.BLUE,0,"blue0")
equal(m.eggs.R1.owner,"RED","R1 owner")
equal(m.eggs.R2.owner,"RED","R2 owner")
equal(m.eggs.B1.owner,"BLUE","B1 owner")
equal(m.eggs.B2.owner,"BLUE","B2 owner")
equal(m.eggs.N1.owner,"NEUTRAL","N1 owner")
equal(m.eggs.N1.state,"NEUTRAL","neutral spawn")

-- Enemy egg: only one carrier, one egg per carrier, real carrying pts,
-- first only legitimate foreign deposit bonus, real vault income.
local ok,reason=Rules.pickup(m,"B1",101,"RED")
result(ok,reason,true,"PICKUP","enemy pickup")
ck(Rules.assertConserved(m),"after enemy pickup")
ok,reason=Rules.pickup(m,"B1",102,"BLUE")
result(ok,reason,false,"ALREADY_CARRIED","reject double pickup")
ok,reason=Rules.pickup(m,"N1",101,"RED")
result(ok,reason,false,"FULL_HANDS","reject duplicate carrier")
ok,reason=Rules.pickup(m,"B2",102,"BLUE")
result(ok,reason,true,"PICKUP","own carry")
tick(m,10)
equal(m.scores.RED,1,"red holding enemy 10s")
equal(m.scores.BLUE,0,"blue own defensive carry not 10s")
local deposited,dr,bonus=Rules.deposit(m,101,"RED")
ck(deposited and dr=="DEPOSIT" and bonus==12,"first enemy deposit +12")
equal(m.scores.RED,13,"red credited 1+12")
ck(Rules.assertConserved(m),"after deposit conservation")
tick(m,10)
equal(m.scores.RED,18,"enemy egg vault +3/10 plus two RED home egg ticks")
ok,reason=Rules.pickup(m,"B1",101,"RED")
result(ok,reason,true,"PICKUP","red retrieves same egg")
deposited,dr,bonus=Rules.deposit(m,101,"RED")
ck(deposited and bonus==0,"farm same egg deposit rejected")
equal(m.scores.RED,18,"red no deposit farm")
equal(m.eggs.B1.transferSeq,4,"consistent transferSeq exact")
ok,reason=Rules.drop(m,999)
result(ok,reason,false,"NO_EGG","no fake drop")
ok,reason=Rules.deposit(m,999,"RED")
result(ok,reason,false,"NO_EGG","no fake deposit")
ok,reason=Rules.pickup(m,"NOT_AN_EGG",202,"RED")
result(ok,reason,false,"INVALID","invalid ID")
ok,reason=Rules.pickup(m,"R1",-1,"RED")
result(ok,reason,false,"INVALID","fake negative userId")
ok,reason=Rules.pickup(m,"R1",202,"GREEN")
result(ok,reason,false,"INVALID","fake team")
ok,reason=Rules.pickup(m,"R1",math.huge,"RED")
result(ok,reason,false,"INVALID","nan infinite player")
ok,reason=Rules.advance(m,2)
result(ok,reason,false,"TICK_MUST_BE_ONE_SECOND","no skipped time farming")
equal(m.now,20,"no invalid tick")

-- Genuine owner recovery of an egg once stolen.
ok,reason=Rules.pickup(m,"B1",303,"BLUE")
result(ok,reason,true,"PICKUP","blue real retrieval")
deposited,dr,bonus=Rules.deposit(m,303,"BLUE")
ck(deposited and bonus==2,"real single rescue +2")
ok,reason=Rules.pickup(m,"B1",303,"BLUE")
result(ok,reason,true,"PICKUP","blue takes own again")
deposited,dr,bonus=Rules.deposit(m,303,"BLUE")
ck(deposited and bonus==0,"repeated rescue farm 0")

-- Neutral: both sides may legitimately claim it once each.
local neutral=Rules.new()
ok,reason=Rules.pickup(neutral,"N1",111,"RED")
result(ok,reason,true,"PICKUP","neutral pickup red")
tick(neutral,10)
equal(neutral.scores.RED,1,"neutral carried +1/10")
deposited,dr,bonus=Rules.deposit(neutral,111,"RED")
ck(deposited and bonus==10,"neutral first deposit +10")
tick(neutral,10)
equal(neutral.scores.RED,15,"neutral vault +2/10 plus RED home passive ticks")
ok,reason=Rules.pickup(neutral,"N1",222,"BLUE")
result(ok,reason,true,"PICKUP","neutral stolen by blue")
deposited,dr,bonus=Rules.deposit(neutral,222,"BLUE")
ck(deposited and bonus==10,"neutral blue first deposit +10")
ok,reason=Rules.pickup(neutral,"N1",222,"BLUE")
result(ok,reason,true,"PICKUP","neutral blue repeated claim")
deposited,dr,bonus=Rules.deposit(neutral,222,"BLUE")
ck(deposited and bonus==0,"neutral blue bonus single claim")

-- Own egg defence: carrying one egg for 30s gives +1 not +1/20s.
local own=Rules.new()
ok,reason=Rules.pickup(own,"R1",1001,"RED")
result(ok,reason,true,"PICKUP","own defensive carry")
tick(own,30)
equal(own.scores.RED,2,"own R1 carry1 and R2 home1")
deposited,dr,bonus=Rules.deposit(own,1001,"RED")
ck(deposited and bonus==0,"own re-deposit no rescue bonus")
ck(Rules.assertConserved(own),"own post deposit conserved")

-- Death/disconnect drop one egg, no points while dropped.
local fallen=Rules.new()
ok,reason=Rules.pickup(fallen,"N1",1,"RED")
ck(ok,"fall pickup neutral")
ok,reason=Rules.drop(fallen,1)
result(ok,reason,true,"DROP","disconnect/death drop")
ck(Rules.assertConserved(fallen),"no missing dropped egg")
tick(fallen,10)
equal(fallen.scores.RED,0,"dropped neutral no score")
ok,reason=Rules.pickup(fallen,"N1",2,"BLUE")
result(ok,reason,true,"PICKUP","enemy can pick dropped")
ck(Rules.assertConserved(fallen),"pickup dropped no duplicate")

-- Idle four-minute finish is DRAW, no late rewards or 241st tick.
local timed=Rules.new()
tick(timed,240)
equal(timed.now,240,"4min finish")
equal(timed.winner,"DRAW","symmetric passive score ties")
ck(not timed.active,"round ended")
local scoreRed=timed.scores.RED
ok,reason=Rules.advance(timed,1)
result(ok,reason,false,"INACTIVE","no post-finish scoring")
equal(timed.scores.RED,scoreRed,"no extra pts")
ok,reason=Rules.pickup(timed,"B1",1,"RED")
result(ok,reason,false,"INACTIVE","no post-finish theft")
ck(Rules.assertConserved(timed),"time end conserved")

-- End while carried: release state and carrier mapping consistently.
local withCarry=Rules.new()
ok,reason=Rules.pickup(withCarry,"N1",123,"RED")
ck(ok,"carry before deadline")
tick(withCarry,240)
equal(withCarry.eggs.N1.state,"DROPPED","timeout carrier safely released")
ck(Rules.assertConserved(withCarry),"timeout full 5 conserved")
equal(withCarry.carryByPlayer[123],nil,"timeout player free")

-- Symmetric RED and BLUE opponent-carry/deposit decisions.
local mirror=Rules.new()
ok,reason=Rules.pickup(mirror,"R1",8,"BLUE")
ck(ok,"blue steals red")
deposited,dr,bonus=Rules.deposit(mirror,8,"BLUE")
ck(deposited and bonus==12,"blue capture same 12")
equal(mirror.scores.BLUE,12,"blue equals red capture")
ck(Rules.assertConserved(mirror),"mirror five eggs conserved")

print("P0D_H2_MULTI_EGG_NATIVE_POLICY_PASS_"..tostring(asserts))
'''
Path(a.write).write_text(test,encoding="utf8")
print("NATIVE_SOURCES",len(src),"TEST_BYTES",len(test))
