#!/usr/bin/env python3
"""Real six-module native-Luau regression for PlayerRemoving ordering.

Reproduces a PRE-vs-POST removal GetPlayers() difference in exact official Game.
Reuses pinned full real Game+Map+Trap+roster native QA; candidate ONLY changes
the authoritative team-survivor count at the disconnect decision.
Roblox engine services are external test doubles. Not actual Studio evidence.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

OFFICIAL = "1263a03701211a652b99b91d2339575dc8104eff"
UPSTREAM = "664284d6ec29741060bead3bd0df66e9ea6b1e76"
UPSTREAM_FILE = "handoffs/P0D-S1-V6-ROSTER-ROUND-CYCLES-NATIVE-20261112-01/tools/roster_cycle_native.py"
UPSTREAM_BLOB = "1ec338dcb2946848a34c233cd08e365e7b0f0f02"
GAME_ORIGINAL_BLOB = "7c5229f600f17537bc1bbbb0b96b6a2435875374"
GAME_CANDIDATE_BLOB = "3d7122a340631cdef7232edd21e6817394a48d34"
OWN_ROOT = Path("handoffs/P0D-S1-V6-PLAYERREMOVING-ORDER-20261112-01")
CANDIDATE = OWN_ROOT / "candidate/src/server/Game.server.luau"
OLD = '''    if match.phase == "ACTIVE" and side ~= "NONE" then
        local surviving = Rules.opponent(side)
        if teamCount(side) <= 1 then stopRound(surviving, "OPPONENT_LEFT") end
    end'''
NEW = '''    if match.phase == "ACTIVE" and side ~= "NONE" then
        -- Robust to PlayerRemoving before OR after GetPlayers() drops the leaver.
        -- Count only distinct teammates, never the player being removed.
        local teammates = 0
        for _, other in ipairs(Players:GetPlayers()) do
            if other ~= player and getTeamName(other) == side then
                teammates += 1
            end
        end
        if teammates == 0 then
            stopRound(Rules.opponent(side), "OPPONENT_LEFT")
        end
    end'''
BEFORE = 'eq(last(pRed).bluePlayers,2,"blue_team_after_departure")'
AFTER = 'eq(pReturn.Character.hum.Health,newEnemyHp-24,"fresh_seq_can_attack_after_new_round")'

# Realistic variants:
# A) callback receives player BEFORE GetPlayers excludes him, handled by
# frozen upstream test pThree/pFour; B) callback receives player AFTER
# exclusion, new specific test checks 2v2 teammate survival. Third test
# ensures A's last-member departure still ends and is never ignored.
PRE_ADD = r'''
-- Exact active roster, before Game loses a RED teammate:
-- one RED and two BLUE remain following pThree's legitimate departure.
local pAfter=makePlayer(307)
Players.users={pRed,pBlue,pFour,pAfter}
Players.PlayerAdded:Fire(pAfter)
eq(pAfter.Team.Name,"RED","postremove_second_red_team")
eq(last(pAfter).phase,"ACTIVE","postremove_join_active")
-- THIS is the behavior not previously covered: Roblox Players list has
-- already excluded the leaving player WHEN PlayerRemoving fires.
Players.users={pRed,pBlue,pFour}
Players.PlayerRemoving:Fire(pAfter)
tick(33.12)
eq(last(pRed).phase,"ACTIVE","postremove_teammate_survives")
eq(last(pRed).redPlayers,1,"postremove_one_red_survivor")
eq(last(pRed).bluePlayers,2,"postremove_two_blue_still_present")
'''
POST_ADD = r'''
-- The reverse event ordering: callback fires while the BLUE last-member
-- pReturn still appears in GetPlayers(). Excluding the leaver is mandatory.
Players.PlayerRemoving:Fire(pReturn)
eq(last(pRed).phase,"RESULTS","preremove_last_blue_results")
eq(last(pRed).winner,"RED","preremove_last_blue_winner")
eq(last(pRed).reason,"OPPONENT_LEFT","preremove_last_blue_reason")
Players.users={pRed}
'''
MUTANTS = (
    ("premature_win_with_one_teammate_left",
     "if teammates == 0 then", "if teammates <= 1 then",
     "GAME_S1_ASSERT_departing_red_has_surviving_teammate"),
    ("forget_to_exclude_leaver",
     "if other ~= player and getTeamName(other) == side then",
     "if getTeamName(other) == side then",
     "GAME_S1_ASSERT_preremove_last_blue_results"),
    ("count_opponents_not_teammates",
     "if other ~= player and getTeamName(other) == side then",
     "if other ~= player and getTeamName(other) ~= side then",
     "GAME_S1_ASSERT_disconnect_ends_round"),
    ("ignore_last_member_departure",
     "if teammates == 0 then", "if false then",
     "GAME_S1_ASSERT_disconnect_ends_round"),
)


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()


def exactly(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"UNSAFE_ANCHOR_{label}_count={count}")
    return source.replace(old,new,1)


def pinned_source(repo: Path, sha: str, path: str, blob: str) -> str:
    p=subprocess.run(["git","-C",str(repo),"show",sha+":"+path],
                     capture_output=True,check=False,timeout=25)
    if p.returncode or gitblob(p.stdout)!=blob:
        raise RuntimeError(f"UNREADABLE_OR_WRONG_FROZEN_GIT_SOURCE_{path}")
    return p.stdout.decode("utf-8")


def load(repo: Path):
    upstream=pinned_source(repo,UPSTREAM,UPSTREAM_FILE,UPSTREAM_BLOB)
    env={"__name__":"_p0d_frozen_roster_order_source"}
    exec(compile(upstream,UPSTREAM_FILE,"exec"),env)
    if env["OFFICIAL"]!=OFFICIAL:
        raise RuntimeError("WRONG_UPSTREAM_GAME_VERSION")
    engine,base,sources=env["load"](repo)
    original=sources["Game"]
    if gitblob(original.encode())!=GAME_ORIGINAL_BLOB:
        raise RuntimeError("REAL_GAME_SOURCE_WRONG_BLOB")
    if not CANDIDATE.is_file() or CANDIDATE.is_symlink():
        raise RuntimeError("CANDIDATE_NOT_AN_ORDINARY_FILE")
    candidate=(repo/CANDIDATE).read_bytes()
    if gitblob(candidate)!=GAME_CANDIDATE_BLOB:
        raise RuntimeError("CANDIDATE_GIT_BLOB_WRONG")
    if candidate != exactly(original,OLD,NEW,"sole_source_edit").encode("utf-8"):
        raise RuntimeError("NOT_EXACTLY_ONE_PLAYERREMOVING_SOURCE_REPLACEMENT")
    base["LUAU_TEST"]=exactly(base["LUAU_TEST"],BEFORE,
        BEFORE+"\n"+PRE_ADD,"postremove_added_once")
    base["LUAU_TEST"]=exactly(base["LUAU_TEST"],AFTER,
        AFTER+"\n"+POST_ADD,"last_blue_added_once")
    return engine,base,sources,candidate.decode("utf-8")


def execute(repo: Path, luau: str):
    engine,base,sources,candidate=load(repo)
    with TemporaryDirectory(prefix="p0d_s1_removing_order_") as tmp:
        output=Path(tmp)/"real_six_game_order.luau"
        # Baseline regression requires exact known failure. Do not claim
        # real Studio bug, only conditional GetPlayers() ordering risk.
        original_code,original_log=engine["run"](luau,output,base,sources)
        marker="GAME_S1_ASSERT_postremove_teammate_survives"
        if original_code==0 or marker not in original_log:
            raise RuntimeError("UNEXPECTED_BASELINE_NONREPRODUCTION "+original_log[-950:])
        print("P0D_REAL_S1_ORDER_DEPENDENCY_REPRODUCED_IN_NATIVE "+marker)
        fixed=dict(sources)
        fixed["Game"]=candidate
        status,log=engine["run"](luau,output,base,fixed)
        match=re.search(r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)",log)
        if status!=0 or not match or int(match.group(1))<136:
            raise RuntimeError("CANDIDATE_REAL_SIX_SOURCE_NATIVE_FAILED "+log[-1850:])
        print("P0D_REAL_S1_V6_ORDER_INDEPENDENT_MATCH_LUAU_PASS assertions="+match.group(1))
        for name,old,new,expected in MUTANTS:
            alt=dict(fixed)
            alt["Game"]=exactly(candidate,old,new,name)
            status,log=engine["run"](luau,output,base,alt)
            if status==0 or expected not in log:
                raise RuntimeError("TARGETED_BAD_SOURCE_VARIANT_NOT_REJECTED_"+name+" "+log[-1250:])
            print("P0D_REAL_S1_ORDER_DANGER_MUTATION_REJECTED "+name)
        print("P0D_REAL_S1_PLAYERREMOVING_ALL_ACCEPTANCE_NATIVE_PASS mutants="+str(len(MUTANTS)))


def selftest():
    assert len(OFFICIAL)==len(UPSTREAM)==len(UPSTREAM_BLOB)==len(GAME_CANDIDATE_BLOB)==40
    assert len(MUTANTS)==4 and len({v[0] for v in MUTANTS})==4
    assert gitblob(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert exactly("A OLD B","OLD","NEW","fixture")=="A NEW B"
    for code,anchor in (("A","MISSING"),("A A","A")):
        try:exactly(code,anchor,"B","negative")
        except RuntimeError:pass
        else:raise AssertionError("UNSAFE_NON_UNIQUE_PATCH_ACCEPTED")
    for part in ("postremove_teammate_survives","postremove_one_red_survivor",
                 "preremove_last_blue_results","preremove_last_blue_winner"):
        assert part in PRE_ADD+POST_ADD
    assert "other ~= player" in NEW and "teamCount(side) <= 1" in OLD
    assert all("GAME_S1_ASSERT_" in x[3] for x in MUTANTS)
    print("P0D_PLAYERREMOVING_ORDER_PYTHON_SELFTEST_PASS checks=9")


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    args=p.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.repo or not args.luau:
        p.error("To run native-Luau supply --repo and --luau")
    execute(args.repo.resolve(),args.luau)
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,UnicodeError,OSError,ValueError) as exc:
        print("P0D_PLAYERREMOVING_NATIVE_BLOCKED "+str(exc),file=sys.stderr)
        sys.exit(2)
