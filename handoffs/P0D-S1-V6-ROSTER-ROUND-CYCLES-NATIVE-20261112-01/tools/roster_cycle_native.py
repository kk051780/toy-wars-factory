#!/usr/bin/env python3
"""Actual frozen six-original-source Game/Map/Rules/Lobby/Config/TrapRules QA.

Adds real late join, carrier departure, countdown reset, and stale seq after
rematch assertions to the previously source-locked native-Luau full-game fixture.
Only harness test body and test-only Roblox external service fakes change.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

OFFICIAL = "1263a03701211a652b99b91d2339575dc8104eff"
UPSTREAM = "84d061d81ffd28418f6e28e9e85bb684dd0daaf7"
UPSTREAM_PATH = "handoffs/P0D-S1-V6-REAL-MAP-TRAP-COMPOSED-20261112-01/tools/run_v6_game_map_trap.py"
UPSTREAM_SHA = "586aaa9b3498f9b28d283211d6f1b5fcd3af1fbe"
PRE = r'''
-- NEW: real original V6 game handles 3rd and 4th player during ACTIVE;
-- genuinely produced map and trap tests have already passed above.
local pThree=makePlayer(303)
Players.users={pRed,pBlue,pThree}
Players.PlayerAdded:Fire(pThree)
eq(pThree.Team.Name,"RED","late_join_balances_red")
eq(last(pThree).phase,"ACTIVE","late_join_receives_active")
local pFour=makePlayer(304)
Players.users={pRed,pBlue,pThree,pFour}
Players.PlayerAdded:Fire(pFour)
eq(pFour.Team.Name,"BLUE","fourth_join_balances_blue")
eq(last(pFour).phase,"ACTIVE","fourth_join_receives_active")
tick(33.0)
eq(last(pRed).redPlayers,2,"two_red_players")
eq(last(pRed).bluePlayers,2,"two_blue_players")
-- Carry a genuine BLUE egg with midround arriving RED, then leave. The
-- carrier's egg must return, without ending a match that has another RED.
setNear(pThree,arena.teams.BLUE.egg.Position)
promptSteal(pThree,"BLUE")
eq(last(pThree).carrying,"BLUE","late_join_can_carry_enemy_egg")
eq(arena.teams.BLUE.egg.Transparency,1,"late_join_stolen_egg_hidden")
-- Roblox event is fired BEFORE Players list loses the leaving member.
Players.PlayerRemoving:Fire(pThree)
eq(arena.teams.BLUE.egg.Transparency,0,"carrier_departure_restores_egg")
eq(arena.teams.BLUE.eggPrompt.Enabled,true,"carrier_departure_unlocks_egg")
eq(last(pRed).phase,"ACTIVE","departing_red_has_surviving_teammate")
Players.users={pRed,pBlue,pFour}
tick(33.1)
eq(last(pRed).redPlayers,1,"red_team_after_departure")
eq(last(pRed).bluePlayers,2,"blue_team_after_departure")
Players.PlayerRemoving:Fire(pFour)
eq(last(pRed).phase,"ACTIVE","departing_blue_has_surviving_teammate")
Players.users={pRed,pBlue}
tick(33.2)
eq(last(pRed).bluePlayers,1,"blue_team_after_departure")
'''
POST = r'''
-- Re-enter from RESULTS to LOBBY with one player, then abort countdown.
tick(42.3)
eq(last(pRed).phase,"LOBBY","solo_after_results_is_lobby")
tick(42.4)
eq(last(pRed).phase,"LOBBY","solo_cannot_start")
local pShort=makePlayer(305)
Players.users={pRed,pShort}
Players.PlayerAdded:Fire(pShort)
eq(pShort.Team.Name,"BLUE","new_blue_join_lobby")
tick(43.0)
eq(last(pRed).phase,"COUNTDOWN","second_player_starts_countdown")
Players.PlayerRemoving:Fire(pShort)
Players.users={pRed}
tick(43.5)
eq(last(pRed).phase,"LOBBY","countdown_aborted_on_departure")
tick(44.0)
eq(last(pRed).phase,"LOBBY","aborted_countdown_stays_lobby")
local pReturn=makePlayer(306)
Players.users={pRed,pReturn}
Players.PlayerAdded:Fire(pReturn)
eq(pReturn.Team.Name,"BLUE","replacement_blue_arrives")
tick(44.2)
eq(last(pRed).phase,"COUNTDOWN","replacement_starts_fresh_countdown")
tick(50.99)
eq(last(pRed).phase,"COUNTDOWN","countdown_not_early_after_rejoin")
tick(51.2)
eq(last(pRed).phase,"ACTIVE","third_round_started_with_two_players")
eq(last(pRed).serial,3,"third_round_serial_monotonic")
eq(last(pRed).scores.RED,0,"third_round_resets_red_score")
eq(last(pRed).scores.BLUE,0,"third_round_resets_blue_score")
eq(last(pRed).hp.BLUE,300,"third_round_castle_reset")
-- Initial pRed has sent seq1..5 in previous round. Old seq5 must NEVER
-- be accepted after a new round even if attack cooldown has elapsed.
tick(54.0) -- respawn invulnerability 2.5s ended
setNear(pRed,V.new(5,0,0))
setNear(pReturn,V.new(10,0,0))
local newEnemyHp=pReturn.Character.hum.Health
send(pRed,"ATTACK",5,{targetId=306,damage=999})
eq(pReturn.Character.hum.Health,newEnemyHp,"old_seq_cannot_attack_after_new_round")
send(pRed,"ATTACK",6,{targetId=306,damage=999})
eq(pReturn.Character.hum.Health,newEnemyHp-24,"fresh_seq_can_attack_after_new_round")
'''
BEFORE="-- On player disconnect, existing match ends by SERVER authority."
AFTER='if checks<75 then error("GAME_S1_TOO_FEW_ASSERTIONS "..tostring(checks),0) end'
MUTANTS=(
 ("force_all_joiners_blue", "Game",
  'local name = if teamCount("RED") <= teamCount("BLUE") then "RED" else "BLUE"',
  'local name = "BLUE"',
  "GAME_S1_ASSERT_late_join_balances_red"),
 ("fail_to_drop_enemy_egg_on_departure", "Game",
  'local side = getTeamName(player)\n    dropEgg(player)\n    restoreSlow(player)',
  'local side = getTeamName(player)\n    -- dropEgg(player) deliberately omitted\n    restoreSlow(player)',
  "GAME_S1_ASSERT_carrier_departure_restores_egg"),
 ("end_round_while_teammate_remains", "Game",
  'if teamCount(side) <= 1 then stopRound(surviving, "OPPONENT_LEFT") end',
  'if teamCount(side) <= 2 then stopRound(surviving, "OPPONENT_LEFT") end',
  "GAME_S1_ASSERT_departing_red_has_surviving_teammate"),
 ("countdown_not_cancelled_when_second_leaves", "Game",
  'if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then',
  'if false then',
  "GAME_S1_ASSERT_countdown_aborted_on_departure"),
 ("seq_counter_reset_between_rounds", "Game",
  'lastAttack[p] = -math.huge\n        lastTrap[p] = -math.huge',
  'lastAttack[p] = -math.huge\n        lastTrap[p] = -math.huge\n        lastSeq[p] = 0',
  "GAME_S1_ASSERT_old_seq_cannot_attack_after_new_round"),
)


def blob_sha(data: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def exact(text: str, old: str, new: str, scope: str)->str:
    if text.count(old) != 1:
        raise RuntimeError(f"ANCHOR_MISSING_OR_DUPLICATED_{scope}_count={text.count(old)}")
    return text.replace(old,new,1)


def load(repo: Path):
    p=subprocess.run(["git","-C",str(repo),"show",UPSTREAM+":"+UPSTREAM_PATH],
                     check=False,capture_output=True,timeout=20)
    if p.returncode or blob_sha(p.stdout)!=UPSTREAM_SHA:
        raise RuntimeError("FROZEN_REAL_GAME_MAP_QA_SOURCE_NOT_AVAILABLE")
    env={"__name__":"_p0d_v6_real_qa_without_main"}
    exec(compile(p.stdout.decode("utf-8"),UPSTREAM_PATH,"exec"),env)
    if env["OFFICIAL"]!=OFFICIAL or len(env["BLOBS"])!=6:
        raise RuntimeError("UPSTREAM_ORIGINAL_SOURCE_SELECTION_CHANGED")
    base,sources=env["prepare"](repo)
    source=base["LUAU_TEST"]
    source=exact(source,BEFORE,PRE+"\n"+BEFORE,"insert_real_midround_join_and_exit")
    source=exact(source,AFTER,POST+"\n"+AFTER,"insert_second_lobby_and_replay")
    base["LUAU_TEST"]=source
    return env,base,sources


def execute(repo: Path,luau: str):
    env,base,sources=load(repo)
    with TemporaryDirectory(prefix="p0d_s1_roster_") as path:
        file=Path(path)/"actual_game_roster.luau"
        code,log=env["run"](luau,file,base,sources)
        match=re.search(r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)",log)
        if code or not match or int(match.group(1))<115:
            raise RuntimeError("REAL_ORIGINAL_ROSTER_TEST_FAILED "+log[-1750:])
        print("P0D_V6_REAL_ORIGINAL_ROSTER_ROUNDS_NATIVE_PASS assertions="+match.group(1))
        for name,module,needle,mutation,expected in MUTANTS:
            changed=dict(sources)
            changed[module]=exact(changed[module],needle,mutation,name)
            code,log=env["run"](luau,file,base,changed)
            if code==0 or expected not in log:
                raise RuntimeError("ROSTER_UNSAFE_MUTATION_NOT_CAUGHT_"+name+" "+log[-1150:])
            print("P0D_V6_REAL_ROSTER_UNSAFE_MUTATION_REJECTED "+name)
        print("P0D_V6_ROSTER_CYCLE_POSITIVE_AND_MUTANTS_PASS count="+str(len(MUTANTS)))


def selftest():
    assert len(UPSTREAM)==len(OFFICIAL)==len(UPSTREAM_SHA)==40
    assert blob_sha(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert len(MUTANTS)==len({m[0] for m in MUTANTS})==5
    assert exact("a OLD b","OLD","NEW","yes")=="a NEW b"
    for s,key in [("a","unknown"),("a a","a")]:
        try:exact(s,key,"x","neg")
        except RuntimeError:pass
        else:raise AssertionError("bad anchor passed")
    assert all(f"GAME_S1_ASSERT_" in m[4] for m in MUTANTS)
    for label in ("carrier_departure_restores_egg","countdown_aborted_on_departure",
                  "old_seq_cannot_attack_after_new_round","fourth_join_balances_blue"):
        assert label in PRE+POST
    print("P0D_S1_ROSTER_PYTHON_SELFTEST_PASS checks=9")


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.repo or not a.luau:
        p.error("Both --repo and --luau required for actual native Luau")
    execute(a.repo.resolve(),a.luau)
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,ValueError,OSError,UnicodeError) as e:
        print("P0D_S1_REAL_ROSTER_NATIVE_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(2)
