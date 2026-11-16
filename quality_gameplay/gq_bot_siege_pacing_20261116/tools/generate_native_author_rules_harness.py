#!/usr/bin/env python3
"""Native Luau integration of EXACT #482 CastleMatchRules + real staged BotActors clause.

No simulated Rules.damageCastle; this fixture embeds the actual 21-source author
gameplay rules and exercises siege, shields, earned tokens, eggs and mode winners.
Not a Roblox Studio or Android test. No official RC writes.
"""
import argparse
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
MODULE = HERE / "EGGRUMBLE_BotSiegePacing.luau"
EXPECTED_RULES_BLOB = "27da5ca1e9e6d9a7afe0674030e387f094ee7492"

CASES = r"""
local Rules=(function()
--EXACT_CASTLE_RULES--
end)()
local SiegePacing=(function()
--EXACT_SIEGE_PACING--
end)()
local SIEGE_INTERVAL=1.6
local n=0
local function check(v,what)
 n+=1
 assert(v,what)
end
local function action(session,id,enemy,now,lastSiege)
 local enemyLoc=nil
 --EXACT_BOT_SIEGE_BRANCH--
end

local function make(mode,secondBlue)
 local roster={}
 for i=1,4 do
  table.insert(roster,{id="AI_"..i,isAI=true,team=if mode=="TEAM" then "RED" else nil})
 end
 table.insert(roster,{id="TARGET",isAI=false,team=if mode=="TEAM" then "BLUE" else nil})
 if secondBlue then
  table.insert(roster,{id="BLUE2",isAI=false,team=if mode=="TEAM" then "BLUE" else nil})
 end
 local rules=Rules.new(mode,roster,24)
 local events={}
 local session={mode=mode,rules=rules,releaseEggs=function(id,pos,ids)
  table.insert(events,{id=id,ids=ids})
 end}
 Rules.start(rules)
 return session,events
end
local function run4(s,now,cooldowns)
 for i=1,4 do
  action(s,"AI_"..i,s.rules.castles.TARGET,now,cooldowns)
 end
end

local team=make("TEAM",true)
local t=team.rules.castles.TARGET
-- Real pre-match defense API is separate, so use another canonical match here.
local shield=make("TEAM",false)
-- Load defense requires LOBBY: validate via independent true author API.
local defRoster={
 {id="AI_1",team="RED",isAI=true},
 {id="TARGET",team="BLUE",isAI=false}
}
local def=Rules.new("TEAM",defRoster,24)
check(Rules.loadDefense(def,"TARGET",{"HARDENED"})==5,"original defense cost")
check(def.castles.TARGET.shield==50,"original shield 50")
Rules.start(def)
local ds={mode="TEAM",rules=def}
local dc={}
action(ds,"AI_1",def.castles.TARGET,10,dc)
check(def.castles.TARGET.hp==1000 and def.castles.TARGET.shield==24,"first hit absorbed by shield")
action(ds,"AI_1",def.castles.TARGET,17,dc)
check(def.castles.TARGET.hp==998 and def.castles.TARGET.shield==0,"remaining shield then real HP")
check(Rules.auditEggConservation(def).valid,"shield does not lose eggs")

local cd={}
run4(team,10,cd)
check(t.hp==974,"four RED bots share one original 26HP attack")
check(team.rules.phase=="ACTIVE","TEAM still active with both sides")
run4(team,11,cd)
check(t.hp==974,"squad can not bypass seven seconds")
run4(team,17,cd)
check(t.hp==948,"second attack exactly after 7s")

check(Rules.auditEggConservation(team.rules).valid,"actual egg ledger starts conserved")
check(Rules.takeEggs(team.rules,"AI_1",1,"TARGET")==1,"original enemy egg capture")
check(Rules.depositEggs(team.rules,"AI_1",1)==1,"original egg deposit")
check(team.rules.teamSiegeTokens.RED==1,"earned TEAM siege bonus")
check(Rules.auditEggConservation(team.rules).valid,"steal and deposit conserve eggs")
run4(team,24,cd)
check(t.hp==920,"one bonus siege hit applies floor(26*1.1)=28 once")
check(team.rules.teamSiegeTokens.RED==0,"one earned token consumed once")
run4(team,25,cd)
check(t.hp==920 and team.rules.teamSiegeTokens.RED==0,"rejected attacks spend no token")
check(Rules.auditEggConservation(team.rules).valid,"AI pacing leaves eggs conserved")

local br=make("BATTLE_ROYALE",true)
local bcd={}
run4(br,10,bcd)
check(br.rules.castles.TARGET.hp==974,"true original BR rules apply 26HP once")
run4(br,17,bcd)
check(br.rules.castles.TARGET.hp==948,"BR seven-second shared target limit")
check(team.rules.castles.TARGET.hp==920,"simultaneous TEAM and BR isolated")
check(Rules.auditEggConservation(br.rules).valid,"BR egg conservation")

local failed=make("TEAM",false)
local fcd={}
-- Genuine author Rules.damageCastle errors before writing HP when team token
-- ledger is invalid. Restore ledger before another bot retries same timestamp.
failed.rules.teamSiegeTokens.RED=nil
action(failed,"AI_1",failed.rules.castles.TARGET,10,fcd)
check(failed.rules.castles.TARGET.hp==1000,"author Rules exception handled without HP mutation")
check(failed._gqLastBotSiegeByCastle.TARGET==nil,"failed reservation canceled")
failed.rules.teamSiegeTokens.RED=0
action(failed,"AI_2",failed.rules.castles.TARGET,10,fcd)
check(failed.rules.castles.TARGET.hp==974,"another bot succeeds immediately after author fault")
check(failed._gqLastBotSiegeByCastle.TARGET==10,"new successful reservation held")
action(failed,"AI_3",failed.rules.castles.TARGET,11,fcd)
check(failed.rules.castles.TARGET.hp==974,"successful retry cannot be bypassed")
check(Rules.auditEggConservation(failed.rules).valid,"author fault does not duplicate eggs")

local winner, releases=make("TEAM",false)
winner.rules.castles.TARGET.hp=15 -- deterministic pre-existing low-HP scenario
run4(winner,10,{})
check(winner.rules.castles.TARGET.hp==0 and not winner.rules.castles.TARGET.alive,"real castle falls once")
check(winner.rules.phase=="FINISHED" and winner.rules.winner=="RED","original TEAM all-opponent-castles-fallen victory")
check(#releases==1 and #releases[1].ids==3,"original egg release exact three IDs")
check(Rules.auditEggConservation(winner.rules).valid,"victory preserves all original egg IDs")
run4(winner,20,{})
check(#releases==1 and winner.rules.phase=="FINISHED","no post-win double egg release")
check(Rules.auditEggConservation(winner.rules).valid,"round termination conservation")

local brfall, brreleases=make("BATTLE_ROYALE",true)
brfall.rules.castles.TARGET.hp=15
run4(brfall,10,{})
check(brfall.rules.castles.TARGET.hp==0,"BR original castle fall")
check(brfall.rules.phase=="ACTIVE" and brfall.rules.winner==nil,"BR not declared winner while other castles live")
check(#brreleases==1 and #brreleases[1].ids==3,"BR release once")
check(Rules.auditEggConservation(brfall.rules).valid,"BR original egg stock preserved")

local off=make("TEAM",false)
off.gqBotSiegePacingEnabled=false
run4(off,10,{})
check(off.rules.castles.TARGET.hp==896,"feature OFF has all four real 26HP author hits")
check(Rules.auditEggConservation(off.rules).valid,"OFF rollback preserves egg ledger")

local separate=make("TEAM",false)
run4(separate,10,{})
check(separate.rules.castles.TARGET.hp==974,"new original session independent throttle")
print("GQ_ORIGINAL_RULES_PLUS_REAL_BOT_BRANCH_NATIVE_PASS",n)
"""


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def main(actor: Path, rules: Path, out: Path):
    orig = rules.read_bytes()
    assert git_blob(orig) == EXPECTED_RULES_BLOB, "original CastleMatchRules source SHA drift"
    rule_source = orig.decode("utf-8")
    assert rule_source.count("function M.damageCastle(") == 1
    assert rule_source.count("function M.auditEggConservation(") == 1

    stage = actor.read_text(encoding="utf-8")
    start = "elseif now-(lastSiege[id] or 0)>=SIEGE_INTERVAL and SiegePacing.allow(session,enemy.id,id,now) then"
    end = "\n          if session.refresh then session.refresh() end"
    assert stage.count(start) == 1 and stage.count(end) >= 1, "BotActors source changed"
    i = stage.index(start)
    j = stage.index(end, i)
    clause = stage[i:j]
    assert clause.count("Rules.damageCastle(session.rules,enemy.id,id,26)") == 1
    assert clause.count("SiegePacing.cancelFailed(session,enemy.id,id,now)") == 1
    assert clause.strip().endswith("end")
    clause = clause.replace("elseif", "if", 1)

    pace = MODULE.read_text(encoding="utf-8")
    assert pace.count("return Pace") == 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        CASES.replace("--EXACT_CASTLE_RULES--", rule_source)
             .replace("--EXACT_SIEGE_PACING--", pace)
             .replace("--EXACT_BOT_SIEGE_BRANCH--", clause),
        encoding="utf-8",
    )
    print("EXACT_AUTHOR_RULES_GIT_BLOB", git_blob(orig))
    print("EXACT_STAGED_BOT_BRANCH_SHA256", hashlib.sha256(clause.encode()).hexdigest())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--actor", required=True, type=Path)
    ap.add_argument("--rules", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    main(args.actor, args.rules, args.out)
