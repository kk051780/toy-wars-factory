"""Exercise rich51's actual bot kickoff and single-Game egg ownership."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from apply_active_solo_bots import BOT, GAME, PACKAGE
from integrate import gitblob
from test_p0_ready_composed_native import unique_function


def exactly_between(body, first, last):
    assert body.count(first) == 1 and last in body.split(first, 1)[1]
    return body.split(first, 1)[1].split(last, 1)[0]


def game_program(dist):
    source = (dist / "src" / GAME).read_text("utf-8")
    eligibility = unique_function(source, "local function eligibleSoloPlayers(): {Player}")
    authority = exactly_between(source, "-- Standard S1 classic egg transaction rules remain authoritative for humans.\n",
                                "local function resetRound()")
    startup = exactly_between(source, "    -- Deferral prevents spawn/reset and captures from overlapping this callback.\n",
                              "    -- This private H1 has")
    epoch = exactly_between(source, "        p:LoadCharacter()\n    end\n",
                            "    -- All previous epoch egg carriers were cleaned above")
    rules = (dist / "src/server/S1Rules.luau").read_text("utf-8")
    return "\n".join((SETUP, "local Rules=(function()", rules, "end)()", eligibility, authority,
                      "local function scheduleSolo(startupSerial)", startup, "end",
                      "local function finishKickoff(startupSerial)", epoch,
                      "    return true\nend", CASES))


SETUP = r'''
local match={phase="ACTIVE",serial=1,eggOwners={},scores={RED=0,BLUE=0},hp={RED=100,BLUE=100}}
local Config={InteractDistance=9,CapturesToWin=2}
local EXPERIMENTAL_FIVE_EGG_MODE=false
local studioSoloRoundStarted=true
local studio=true
local Players={online={}}
function Players:GetPlayers() return self.online end
local RunService={}
function RunService:IsStudio() return studio end
local function getTeamName(p) return p.Team and p.Team.Name or "NONE" end
local function player(name,side,spectator)
    local p={Name=name,Team=side and {Name=side}}
    function p:GetAttribute(k) return k=="P0D_LateJoinSpectator" and spectator end
    return p
end
local human=player("Human","RED",false)
local opponent=player("Opponent","BLUE",false)
local observer=player("Observer",nil,true)
local function point(x)
    return setmetatable({x=x},{__sub=function(a,b) return {Magnitude=math.abs(a.x-b.x)} end})
end
local function team()
    return {egg={Position=point(0),Transparency=0},eggPrompt={Enabled=true},scorePad={Position=point(0)}}
end
local map={teams={RED=team(),BLUE=team()}}
local botEggOwners={}
local restores=0
local function resetEgg(side)
    restores+=1
    botEggOwners[side]=nil
    map.teams[side].egg.Transparency=0
    map.teams[side].eggPrompt.Enabled=true
end
local updates=0
local function broadcast() updates+=1 end
local function stopRound(winner,reason)
    match.phase="RESULTS"
    match.winner=winner
    match.reason=reason
end
local tasks={}
local task={defer=function(callback) table.insert(tasks,callback) end}
local starts,stops=0,0
local healthyStart=true
local function warn(message)
    assert(message=="FB005_SOLO_START_FAIL_CLOSED","BOT_UNEXPECTED_WARNING")
end
local expectedAuthority
local SoloTeamBots={
    start=function(world,side,callbacks)
        assert(world==map and side=="RED" and callbacks==expectedAuthority,"BOT_GAME_WRONG_AUTHORITY")
        starts+=1
        return healthyStart
    end,
    stop=function() stops+=1 end,
}
local function flush()
    local dequeued=tasks
    tasks={}
    for _, callback in ipairs(dequeued) do callback() end
end
'''

CASES = r'''
expectedAuthority=botAuthority
Players.online={human,observer}
scheduleSolo(1);flush()
assert(starts==1 and match.phase=="ACTIVE","BOT_SOLO_AND_SPECTATOR")
scheduleSolo(1)
match.serial=2
flush()
assert(starts==1,"BOT_STALE_EPOCH")
assert(finishKickoff(1)==nil and finishKickoff(2)==true,"BOT_STALE_PLAYER_LOAD_CONTINUATION")
Players.online={human,opponent,observer}
scheduleSolo(2);flush()
assert(starts==1,"BOT_TWO_PLAYERS")
Players.online={human,observer}
EXPERIMENTAL_FIVE_EGG_MODE=true
scheduleSolo(2);flush()
assert(starts==1,"BOT_FIVE_EGG_FORBIDDEN")
EXPERIMENTAL_FIVE_EGG_MODE=false
studio=false
scheduleSolo(2);flush()
assert(starts==1,"BOT_ONLY_STUDIO")
studio=true
healthyStart=false
scheduleSolo(2);flush()
assert(starts==2 and stops==1 and match.reason=="SOLO_BOTS_NOT_READY","BOT_START_FAILURE_ENDS_MATCH")
print("ACTIVE_RICH51_BOT_ROSTER_EPOCH_AND_FAIL_CLOSED_PASS")

match.phase="ACTIVE"
local carrier={id="B1",team="RED",root={Position=point(0)}}
local second={id="B2",team="RED",root={Position=point(0)}}
assert(not botAuthority.steal(carrier,"RED"),"BOT_OWN_EGG")
carrier.root.Position=point(10)
assert(not botAuthority.steal(carrier,"BLUE"),"BOT_FAR_STEAL")
carrier.root.Position=point(0)
match.eggOwners.BLUE=opponent
assert(not botAuthority.steal(carrier,"BLUE"),"BOT_COULD_STEAL_HUMAN_EGG")
match.eggOwners.BLUE=nil
assert(botAuthority.steal(carrier,"BLUE") and botEggOwners.BLUE=="B1","BOT_STEAL")
assert(not botAuthority.steal(second,"BLUE"),"BOT_DOUBLE_STEAL")
match.eggOwners.RED=opponent
assert(not botAuthority.deposit(carrier,"RED","BLUE") and match.scores.RED==0,"BOT_OWN_EGG_NOT_HOME")
match.eggOwners.RED=nil
assert(not botAuthority.deposit(second,"RED","BLUE"),"BOT_WRONG_CARRIER")
assert(botAuthority.deposit(carrier,"RED","BLUE") and match.scores.RED==1 and restores==1,"BOT_DEPOSIT")
assert(not botAuthority.deposit(carrier,"RED","BLUE") and match.scores.RED==1,"BOT_DOUBLE_SCORE")
assert(botAuthority.steal(carrier,"BLUE") and botAuthority.deposit(carrier,"RED","BLUE"),"BOT_SECOND_DEPOSIT")
assert(match.phase=="RESULTS" and match.winner=="RED" and match.reason=="STUDIO_BOT_EGG_CAPTURE","BOT_AUTHORITY_RESULT")
assert(not botAuthority.steal(carrier,"BLUE"),"BOT_RESULT_STEAL")
print("ACTIVE_RICH51_BOT_SINGLE_GAME_EGG_SCORE_AND_WINNER_PASS")
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((PACKAGE / "source_lock.json").read_bytes())
    assert gitblob((args.dist / "src" / BOT).read_bytes()) == lock["bot_blob"]
    args.out.mkdir()
    (args.out / "game.luau").write_bytes(game_program(args.dist).encode())
    for name, identity in lock["native_author_fixtures"].items():
        fixture = PACKAGE / "native" / name
        assert gitblob(fixture.read_bytes()) == identity
        subprocess.run([sys.executable, "-B", str(fixture), "--dist", str(args.dist),
                        "--out", str(args.out / (fixture.stem + ".luau"))], check=True)
