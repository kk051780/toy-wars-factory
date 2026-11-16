#!/usr/bin/env python3
"""Generate a real native Luau VM test by embedding the exact shipped module."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "EGGRUMBLE_BotSiegePacing.luau"
CASES = r"""
local n=0
local function check(value, label)
 n+=1
 assert(value, label)
end
local function session(mode)
 local alpha={id="AI_A",team=if mode=="TEAM" then "RED" else nil,alive=true,isAI=true}
 local beta={id="AI_B",team=if mode=="TEAM" then "RED" else nil,alive=true,isAI=true}
 local enemy={id="TARGET",team=if mode=="TEAM" then "BLUE" else nil,alive=true,isAI=false}
 local other={id="TARGET2",team=if mode=="TEAM" then "BLUE" else nil,alive=true,isAI=false}
 local friend={id="FRIEND",team=if mode=="TEAM" then "RED" else nil,alive=true,isAI=false}
 return {mode=mode,rules={mode=mode,phase="ACTIVE",winner=nil,castles={
  AI_A=alpha,AI_B=beta,TARGET=enemy,TARGET2=other,FRIEND=friend
 }}}
end

local team=session("TEAM")
check(Pace.allow(team,"TARGET","AI_A",100),"first bot claim")
check(not Pace.allow(team,"TARGET","AI_B",100),"no same-time bot swarm")
check(not Pace.allow(team,"TARGET","AI_A",101.6),"per-bot original 1.6s insufficient")
check(not Pace.allow(team,"TARGET","AI_B",106.99),"sub-seven rejected")
check(Pace.allow(team,"TARGET","AI_B",107),"new seven-second target claim")
check(not Pace.allow(team,"TARGET","AI_A",107.1),"others cannot pile on")
check(Pace.allow(team,"TARGET2","AI_A",107.1),"different castle separate budget")
-- Regression: a failed authoritative Rules.damageCastle pcall must not consume
-- a seven-second team siege slot. Only the exact bot/timestamp can roll back.
local fault=session("TEAM")
check(Pace.allow(fault,"TARGET","AI_A",50),"reserve before damage")
check(not Pace.cancelFailed(fault,"TARGET","AI_B",50),"wrong bot cannot cancel")
check(not Pace.allow(fault,"TARGET","AI_B",50.5),"failure reservation still locked")
check(not Pace.cancelFailed(fault,"TARGET","AI_A",49.9),"stale timestamp cannot cancel")
check(Pace.cancelFailed(fault,"TARGET","AI_A",50),"failed damage released slot")
check(not Pace.cancelFailed(fault,"TARGET","AI_A",50),"failure cannot release twice")
check(Pace.allow(fault,"TARGET","AI_B",50.5),"next bot may retry after failure")
check(not Pace.cancelFailed(fault,"TARGET","AI_A",50.5),"earlier bot cannot cancel new owner")
check(not Pace.allow(fault,"TARGET","AI_A",51),"successful later reservation held")
check(Pace.allow(fault,"TARGET2","AI_A",51),"failed target leaves other castle free")
check(not Pace.cancelFailed(nil,"TARGET","AI_A",51),"nil session cannot cancel")
check(not Pace.cancelFailed(fault,"TARGET","AI_B",0/0),"NaN cannot cancel")
check(not Pace.cancelFailed(fault,"TARGET","AI_B",math.huge),"Inf cannot cancel")
check(not Pace.allow(team,"FRIEND","AI_A",200),"no friendly fire")
check(not Pace.allow(team,"TARGET","FRIEND",200),"humans never impersonate bots")
check(not Pace.allow(team,"TARGET","INVALID",200),"unknown bot rejected")
team.rules.castles.AI_A.alive=false
check(not Pace.allow(team,"TARGET","AI_A",200),"eliminated bot rejected")
team.rules.castles.AI_A.alive=true
team.rules.castles.TARGET.alive=false
check(not Pace.allow(team,"TARGET","AI_A",200),"fallen castle rejected")
team.rules.castles.TARGET.alive=true
team.rules.phase="FINISHED";team.rules.winner="RED"
check(not Pace.allow(team,"TARGET","AI_A",200),"after result rejected")
team.rules.phase="ACTIVE";team.rules.winner=nil
check(not Pace.allow(team,"TARGET","AI_A",99),"clock rollback rejected")
team.gqBotSiegePacingEnabled=false
check(Pace.allow(team,"TARGET","AI_A",100.1),"flag-OFF restores original bot pace")
check(Pace.allow(team,"TARGET","AI_B",100.2),"flag-OFF restores parallel bot attacks")
local br=session("BATTLE_ROYALE")
check(Pace.allow(br,"TARGET","AI_A",100),"BR first claim")
check(not Pace.allow(br,"TARGET","AI_B",100),"BR shared target budget")
check(Pace.allow(br,"TARGET","AI_B",107),"BR new interval")
local fresh=session("TEAM")
check(Pace.allow(fresh,"TARGET","AI_A",100),"new match fresh budget")
br.mode="TEAM"
check(not Pace.allow(br,"TARGET","AI_A",200),"no cross-mode corruption")
br.mode="BATTLE_ROYALE"
check(not Pace.allow(br,"TARGET","AI_A",0/0),"NaN rejected")
check(not Pace.allow(br,"TARGET","AI_A",math.huge),"Infinity rejected")
check(not Pace.allow(nil,"TARGET","AI_A",200),"nil session rejected")
print("GQ_BOT_SIEGE_PACING_NATIVE_PASS",n)
"""


def generate(out: Path):
    source = MODULE.read_text(encoding="utf-8")
    if source.count("return Pace") != 1:
        raise ValueError("module return anchor drift")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("local Pace=(function()\n" + source + "\nend)()\n" + CASES + "\n",
                   encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    generate(Path(args.out))
