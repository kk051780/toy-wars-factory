#!/usr/bin/env python3
"""P0D genuine seven-safe Game + Coach live-source native Luau independent QA.

Read frozen assembled preview 7-safe Game+Coach from git itself, verify every
one of its 37 release files and exact diff against 6-safe preview + prior #237
original one-line insertions, then run actual Game+Map+Rules+Lobby+Trap+Coach
in genuine pinned native Luau. Only Roblox engine services are test doubles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

SEVEN = "d319b56d1552713da482189048473f266c7b3fdc"
SIX = "65785c2e3b9bc37a6962f9ace128fbfcbb670901"
OFFICIAL = "1263a03701211a652b99b91d2339575dc8104eff"
NATIVE = "24061fd7fc165c506f9a862ba48ceaf80b6345bb"
NATIVE_PATH = "handoffs/P0D-S1-V6-REAL-SERVER-COACH-20261112-01/tools/test_server_snapshots_with_coach.py"
NATIVE_BLOB = "e1758cff9ad8facece8f03e1206dd52564bc3c7c"
ORDER = "6ed1e7e3585e26aff153c7c0c2be2fe68b459ff3"
ORDER_PATH = "handoffs/P0D-S1-SNAPSHOT-COACH-ORDER-20261112-01/tools/test_snapshot_order.py"
ORDER_BLOB = "1d017417f922594baabbc86906a1e8ac112e1f2a"
PREFIX = "releases/P0D_S1_KIDS_RC01/"
GAME_FILE = "src/server/Game.server.luau"
COACH_FILE = "src/shared/FirstMinuteModel.luau"
GAME_SEVEN_BLOB = "e684ca79b8f5ed279bcdf033f4118bf77d552abb"
GAME_SIX_BLOB = "a575ef5175ace5aab59f1dbe3ad8dc74d3d1860d"
COACH_SEVEN_BLOB = "d8dda6b1781375612c123f8c83b6f23fe45d09f1"
COACH_SIX_BLOB = "967ea52df79884e6c73e3e0952d5a97de0d1796e"
MANIFEST_BLOB = "24d36159e91f927fdfbf38a74048072ab31387a7"
MUTANT_EXPECTED = (
    "real_guardian_role_snapshot_consumes",
    "real_coach_tracks_first_update_id",
    "real_same_serial_old_lobby_rejected",
    "real_fractional_id_rejected",
    "real_unversioned_after_version_rejected",
    "real_coach_tracks_first_update_id",
)
ADDED_PRE_EXIT = r'''
local sevenSafePreExitSnapshot=last(pRed)
eq(sevenSafePreExitSnapshot.phase,"ACTIVE","seven_safe_pre_exit_active")
eq(type(sevenSafePreExitSnapshot.updateId),"number","seven_safe_pre_exit_id")
'''
ADDED_POST_EXIT = r'''
local sevenSafeResultSnapshot=last(pRed)
eq(sevenSafeResultSnapshot.updateId>sevenSafePreExitSnapshot.updateId,true,
   "seven_safe_departure_result_has_newer_id")
eq(__real_Coach.consume(redCoach,sevenSafeResultSnapshot,29.1),true,
   "seven_safe_departure_results_snapshot_consumed")
eq(__real_Coach.view(redCoach,29.1).title,"つぎの対戦も挑戦しよう！",
   "seven_safe_departure_results_title")
eq(__real_Coach.consume(redCoach,sevenSafePreExitSnapshot,29.2),false,
   "seven_safe_stale_active_after_departure_rejected")
eq(redCoach.latest,sevenSafeResultSnapshot,
   "seven_safe_latest_result_survives_old_active")
'''

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def exact(source: str, needle: str, replacement: str, label: str) -> str:
    if source.count(needle) != 1:
        raise RuntimeError(f"NON_UNIQUE_{label}_count_{source.count(needle)}")
    return source.replace(needle,replacement,1)

def read(repo: Path, ref: str, path: str, expected: str | None = None) -> bytes:
    p=subprocess.run(["git","-C",str(repo),"show",ref+":"+path],
                     check=False,capture_output=True,timeout=30)
    if p.returncode: raise RuntimeError("GIT_SOURCE_UNAVAILABLE "+ref+" "+path)
    if expected is not None and blob(p.stdout)!=expected:
        raise RuntimeError("GIT_IMMUTABLE_BLOB_MISMATCH "+path)
    return p.stdout

def namespace_of(raw: bytes, origin: str):
    env={"__name__":"_p0d_source_inspection"}
    exec(compile(raw.decode("utf8"),origin,"exec"),env)
    return env

def provenance(repo: Path):
    original=read(repo,SIX,PREFIX+GAME_FILE,GAME_SIX_BLOB).decode("utf8")
    combined=read(repo,SEVEN,PREFIX+GAME_FILE,GAME_SEVEN_BLOB).decode("utf8")
    original_coach=read(repo,SIX,PREFIX+COACH_FILE,COACH_SIX_BLOB).decode("utf8")
    combined_coach=read(repo,SEVEN,PREFIX+COACH_FILE,COACH_SEVEN_BLOB).decode("utf8")
    order=namespace_of(read(repo,ORDER,ORDER_PATH,ORDER_BLOB),ORDER_PATH)
    assert len(order["GAME_PATCHES"])==2 and len(order["COACH_PATCHES"])==4
    for i,(needle,replacement) in enumerate(order["GAME_PATCHES"]):
        original=exact(original,needle,replacement,"GAME_ORDINAL_PATCH_"+str(i))
    for i,(needle,replacement) in enumerate(order["COACH_PATCHES"]):
        original_coach=exact(original_coach,needle,replacement,"COACH_ORDINAL_PATCH_"+str(i))
    if combined!=original or combined_coach!=original_coach:
        raise RuntimeError("SEVEN_SAFE_NOT_EXACTLY_SIX_PLUS_ORDER_FIXED_PATCHES")
    for requirement in (
        "local teammates = 0", "other ~= player", "snapshotUpdateId += 1",
        "updateId = snapshotUpdateId", "root.AssemblyLinearVelocity",
    ):
        if requirement not in combined:
            raise RuntimeError("PREEXISTING_SIX_SAFE_GAME_LOST_"+requirement)
    if "lastUpdateId" not in combined_coach or "罠ボタン" not in combined_coach:
        raise RuntimeError("COACH_GUARDIAN_SOURCE_LOST")
    if "D07_D08_RELEASE_REVIEW_APPROVED = false" not in combined:
        raise RuntimeError("S1_OPTIONAL_BOSS_MUST_REMAIN_OFF")
    print("P0D_SEVEN_SAFE_2_SOURCE_EXACT_6_PATCH_DIFF_PASS")

    base=json.loads(read(repo,SIX,PREFIX+"BUILD_MANIFEST.json"))
    newer=read(repo,SEVEN,PREFIX+"BUILD_MANIFEST.json",MANIFEST_BLOB)
    seven=json.loads(newer)
    files0={row["path"]:row for row in base["files"]}
    files1={row["path"]:row for row in seven["files"]}
    if len(files0)!=37 or len(files1)!=37 or set(files0)!=set(files1):
        raise RuntimeError("FULL_SOURCE_37_ENTRY_MANIFEST_CHANGED")
    changes={x for x in files1 if files1[x]!=files0[x]}
    if changes!={GAME_FILE,COACH_FILE}:
        raise RuntimeError("UNEXPECTED_MANIFEST_CHANGE_"+repr(changes))
    for key,row in files1.items():
        data=read(repo,SEVEN,PREFIX+key)
        if hashlib.sha256(data).hexdigest()!=row["sha256"] or len(data)!=row["size"]:
            raise RuntimeError("SEVEN_SAFE_SOURCE_SHA256_BAD_"+key)
    print("P0D_SEVEN_SAFE_FULL_MANIFEST_SHA256_37_OF_37_PASS")
    return combined,combined_coach,order

def prepare_native(repo: Path):
    server,coach,order=provenance(repo)
    previous=namespace_of(read(repo,NATIVE,NATIVE_PATH,NATIVE_BLOB),NATIVE_PATH)
    engine,base,sources,old_coach=previous["prepare"](repo)
    if previous["OFFICIAL"]!=OFFICIAL or len(engine["BLOBS"])!=6:
        raise RuntimeError("REAL_ENGINE_SOURCE_PIN_CHANGED")
    for label,extra in order["EXTRA_BY_ANCHOR"].items():
        base["LUAU_TEST"]=exact(base["LUAU_TEST"],label,label+"\n"+extra,
                                "SNAPSHOT_REGRESSION_INSERT")
    # Pre-exit state is from an actual server SNAPSHOT, not a fabricated one.
    anchor="-- On player disconnect, existing match ends by SERVER authority."
    base["LUAU_TEST"]=exact(base["LUAU_TEST"],anchor,
                            ADDED_PRE_EXIT+"\n"+anchor,"RESULT_BEFORE_DEPARTURE")
    end='eq(last(pRed).reason,"OPPONENT_LEFT","disconnect_reason")'
    base["LUAU_TEST"]=exact(base["LUAU_TEST"],end,end+"\n"+ADDED_POST_EXIT,
                            "RESULT_AFTER_DEPARTURE")
    s=dict(sources)
    s["Game"]=server
    return previous,engine,base,s,coach,order

def execute(repo: Path, luau: str):
    previous,engine,base,sources,coach,order=prepare_native(repo)
    with TemporaryDirectory(prefix="p0d-seven-safe-native") as d:
        path=Path(d)/"seven_safe_actual_game_and_coach.luau"
        rc,log=previous["run"](luau,path,engine,base,sources,coach)
        match=re.search(r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)",log)
        if rc or not match or int(match.group(1)) < 160:
            raise RuntimeError("SEVEN_SAFE_LIVE_SOURCE_TEST_FAILED "+log[-1800:])
        print("P0D_SEVEN_SAFE_GENUINE_NATIVE_FULL_GAME_CLIENT_PASS checks="+match.group(1))
        if len(order["MUTANTS"])!=6:
            raise RuntimeError("UNEXPECTED_MUTANT_COUNT")
        for (title,kind,needle,unsafe,expected),expected_part in zip(
                order["MUTANTS"],MUTANT_EXPECTED):
            if expected_part not in expected:
                raise RuntimeError("MUTANT_NEGATIVE_ASSERTION_CHANGED_"+title)
            selected=dict(sources)
            view=coach
            if kind=="Game":
                selected["Game"]=exact(selected["Game"],needle,unsafe,title)
            elif kind=="Coach":
                view=exact(coach,needle,unsafe,title)
            else: raise RuntimeError("UNEXPECTED_MODULE_TO_MUTATE")
            rc,log=previous["run"](luau,path,engine,base,selected,view)
            if rc==0 or expected not in log:
                raise RuntimeError("DANGEROUS_SOURCE_MUTANT_NOT_REJECTED_"+title+" "+log[-900:])
            print("P0D_SEVEN_SAFE_REAL_SOURCE_MUTANT_REJECTED "+title)
        print("P0D_SEVEN_SAFE_REAL_NATIVE_AND_MUTANTS_SUCCESS total=6")

def selftest():
    assert len(SEVEN)==len(SIX)==len(NATIVE)==len(OFFICIAL)==40
    assert blob(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert exact("a@b","@","-","yes")=="a-b"
    for text,needle in (("missing","notfound"),("x x","x")):
        try:exact(text,needle,"wrong","negative")
        except RuntimeError:pass
        else:raise AssertionError("UNSAFE_ANCHOR_ACCEPTED")
    assert "seven_safe_departure_results_snapshot_consumed" in ADDED_POST_EXIT
    assert "seven_safe_pre_exit_active" in ADDED_PRE_EXIT
    assert len(MUTANT_EXPECTED)==6
    print("P0D_SEVEN_SAFE_NATIVE_QA_PYTHON_SELFTEST_PASS tests=8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--provenance-only",action="store_true")
    args=p.parse_args()
    if args.selftest:
        selftest();return 0
    if not args.repo:
        p.error("--repo required")
    if args.provenance_only:
        provenance(args.repo.resolve());return 0
    if not args.luau:
        p.error("--luau required for genuine native source execution")
    execute(args.repo.resolve(),args.luau)
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,AssertionError,ValueError,OSError,UnicodeError) as ex:
        print("P0D_SEVEN_SAFE_NATIVE_SOURCE_QA_BLOCKED "+str(ex),file=sys.stderr)
        sys.exit(2)
