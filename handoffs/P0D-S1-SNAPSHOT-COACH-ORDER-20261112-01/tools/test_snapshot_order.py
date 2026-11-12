#!/usr/bin/env python3
"""Exact six official Game/map/etc + vetted original Coach, two surgical candidates.

The real original source bodies execute in genuine upstream native Luau, with
only Roblox engine-boundary test doubles. This is not actual Roblox Studio.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC = "1263a03701211a652b99b91d2339575dc8104eff"
UPSTREAM = "24061fd7fc165c506f9a862ba48ceaf80b6345bb"
UPSTREAM_PATH = "handoffs/P0D-S1-V6-REAL-SERVER-COACH-20261112-01/tools/test_server_snapshots_with_coach.py"
UPSTREAM_BLOB = "e1758cff9ad8facece8f03e1206dd52564bc3c7c"
ROOT = Path("handoffs/P0D-S1-SNAPSHOT-COACH-ORDER-20261112-01")
GAME_PATH = ROOT / "candidate/src/server/Game.server.luau"
GAME_SHA = "36d1f90005fef0315011b600b07a6d13b89d2a72"
GAME_ORIGINAL_SHA = "7c5229f600f17537bc1bbbb0b96b6a2435875374"
COACH_PATH = ROOT / "candidate/src/shared/FirstMinuteModel.luau"
COACH_SHA = "d8dda6b1781375612c123f8c83b6f23fe45d09f1"
COACH_ORIGINAL_SHA = "967ea52df79884e6c73e3e0952d5a97de0d1796e"
GAME_PATCHES = [
    ("local function snapshotFor(player: Player)\n    local now = serverNow()",
     "-- Server-only monotonic replication ordinal, never reset on match changes.\n"
     "local snapshotUpdateId = 0\n"
     "local function snapshotFor(player: Player)\n"
     "    snapshotUpdateId += 1\n    local now = serverNow()"),
    ('kind = "SNAPSHOT", serial = match.serial, phase = match.phase,',
     'kind = "SNAPSHOT", serial = match.serial, phase = match.phase,\n'
     '        updateId = snapshotUpdateId, -- view ordering only, not gameplay authority')
]
COACH_PATCHES = [
    ("    serial: number,\n    activeAt: number?,",
     "    serial: number,\n    lastUpdateId: number,\n    activeAt: number?,"),
    ("        serial = -1, activeAt = nil, initialScore = 0,",
     "        serial = -1, lastUpdateId = -1, activeAt = nil, initialScore = 0,"),
    ('    if type(localNow) ~= "number" or localNow ~= localNow or math.abs(localNow) > 1000000000 then return false end\n'
     '\n    if packet.serial > state.serial then',
     '    if type(localNow) ~= "number" or localNow ~= localNow or math.abs(localNow) > 1000000000 then return false end\n'
     '    -- A server-monotonic SNAPSHOT ordinal protects same-round GUI ordering.\n'
     '    -- Legacy unversioned snapshots are accepted only until a versioned one.\n'
     '    local id = packet.updateId\n'
     '    if id ~= nil then\n'
     '        if not wholeNumber(id) or id <= state.lastUpdateId then return false end\n'
     '    elseif state.lastUpdateId >= 0 then\n'
     '        return false\n'
     '    end\n'
     '\n    if packet.serial > state.serial then'),
    ("    state.latest = packet\n    return true",
     "    state.latest = packet\n    if id ~= nil then state.lastUpdateId = id end\n    return true"),
]
MUTANTS = [
    ("no_server_ordinal_advance","Game",
     "updateId = snapshotUpdateId, -- view ordering only, not gameplay authority",
     "updateId = 1, -- deliberately freeze ordinal",
     "GAME_S1_ASSERT_real_guardian_role_snapshot_consumes"),
    ("no_ordinal_recorded","Coach",
     "if id ~= nil then state.lastUpdateId = id end",
     "if false then state.lastUpdateId = id end",
     "GAME_S1_ASSERT_real_coach_tracks_first_update_id"),
    ("out_of_order_guard_defeated","Coach",
     "id <= state.lastUpdateId then return false",
     "id < -1 then return false",
     "GAME_S1_ASSERT_real_same_serial_old_lobby_rejected"),
    ("invalid_fractional_id_accepted","Coach",
     "not wholeNumber(id) or id <= state.lastUpdateId",
     'type(id) ~= "number" or id <= state.lastUpdateId',
     "GAME_S1_ASSERT_real_fractional_id_rejected"),
    ("legacy_after_version_rolls_back","Coach",
     "elseif state.lastUpdateId >= 0 then\n        return false",
     "elseif false then\n        return false",
     "GAME_S1_ASSERT_real_unversioned_after_version_rejected"),
    ("id_read_disabled","Coach",
     "local id = packet.updateId",
     "local id = nil -- intentionally discard the new server field",
     "GAME_S1_ASSERT_real_coach_tracks_first_update_id"),
]

EXTRA_BY_ANCHOR = {
    'eq(__real_Coach.view(redCoach,0).title,"まず役職をえらぼう","real_lobby_coach_title")':r'''
local firstBlueLobby=last(pBlue)
eq(type(firstBlueLobby.updateId),"number","real_server_provides_update_id")
eq(blueCoach.lastUpdateId,firstBlueLobby.updateId,"real_coach_tracks_first_update_id")
''',
    'eq(blueCoach.latest.role,"GUARDIAN","real_guardian_role_reflected")':r'''
eq(last(pBlue).updateId>firstBlueLobby.updateId,true,
   "real_sequenced_role_update_monotonic")
eq(__real_Coach.consume(blueCoach,firstBlueLobby,.2),false,
   "real_same_serial_old_lobby_rejected")
eq(blueCoach.latest.role,"GUARDIAN","real_delayed_lobby_cannot_rollback_role")
''',
    'eq(redCoach.carried,true,"real_coach_notes_egg_carry")':r'''
local priorCarrier=last(pRed)
eq(type(priorCarrier.updateId),"number","real_carrier_packet_versioned")
''',
    'eq(__real_Coach.view(redCoach,12).title,"得点できたね！","real_red_scoring_title")':r'''
local newestScore=last(pRed)
eq(newestScore.updateId>priorCarrier.updateId,true,
   "real_same_round_update_monotonic")
eq(__real_Coach.consume(redCoach,priorCarrier,12.1),false,
   "real_same_serial_late_carrier_rejected")
eq(redCoach.latest,newestScore,"real_late_carrier_cannot_rollback_score")
''',
    'eq(redCoach.serial,2,"real_round2_coach_serial")':r'''
eq(redCoach.lastUpdateId>newestScore.updateId,true,
   "real_update_sequence_never_reset_at_rematch")
local finalS=last(pRed)
local malformed={}
for k,v in pairs(finalS) do malformed[k]=v end
malformed.updateId=redCoach.lastUpdateId+.5
eq(__real_Coach.consume(redCoach,malformed,24),false,
   "real_fractional_id_rejected")
malformed.updateId="spoofed"
eq(__real_Coach.consume(redCoach,malformed,24),false,
   "real_string_id_rejected")
malformed.updateId=nil
eq(__real_Coach.consume(redCoach,malformed,24),false,
   "real_unversioned_after_version_rejected")
local legacyCoach=__real_Coach.new()
eq(__real_Coach.consume(legacyCoach,malformed,24),true,
   "real_fresh_legacy_unversioned_accepted")
eq(__real_Coach.consume(legacyCoach,finalS,24.1),true,
   "real_legacy_upgrade_to_sequenced")
eq(__real_Coach.consume(legacyCoach,malformed,24.2),false,
   "real_legacy_replay_after_upgrade_rejected")
eq(legacyCoach.latest,finalS,"real_legacy_latest_not_replaced")
''',
}


def blob_sha(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\x00" + payload).hexdigest()


def exact(text: str, needle: str, replacement: str, label: str) -> str:
    n = text.count(needle)
    if n != 1:
        raise RuntimeError(f"NON_UNIQUE_SOURCE_POSITION_{label}_{n}")
    return text.replace(needle, replacement, 1)


def git_read(repo: Path, commit: str, path: str, expected_blob: str) -> str:
    p = subprocess.run(["git","-C",str(repo),"show",commit+":"+path],
                       capture_output=True,timeout=25,check=False)
    if p.returncode or blob_sha(p.stdout)!=expected_blob:
        raise RuntimeError("FROZEN_SOURCE_READ_FAILED_"+path)
    return p.stdout.decode("utf8")


def candidate(repo: Path, path: Path, expected_blob: str,
              official: str, patches: list[tuple[str,str]]) -> str:
    f=repo/path
    if not f.is_file() or f.is_symlink():
        raise RuntimeError("CANDIDATE_FILE_MISSING_OR_SYMLINK_"+str(path))
    payload=f.read_bytes()
    if blob_sha(payload)!=expected_blob:
        raise RuntimeError("CANDIDATE_GIT_BLOB_TAMPERED_"+str(path))
    selected=official
    for i,(old,new) in enumerate(patches):
        selected=exact(selected,old,new,"candidate_exact_change_"+str(i))
    if payload != selected.encode("utf8"):
        raise RuntimeError("UNAUTHORIZED_CANDIDATE_SOURCE_DIFF_"+str(path))
    return payload.decode("utf8")


def prepare(repo: Path):
    upstream=git_read(repo,UPSTREAM,UPSTREAM_PATH,UPSTREAM_BLOB)
    namespace={"__name__":"_upstream_actual_server_and_coach_native"}
    exec(compile(upstream,UPSTREAM_PATH,"exec"),namespace)
    if namespace["OFFICIAL"]!=RC or namespace["COACH_BLOB"]!=COACH_ORIGINAL_SHA:
        raise RuntimeError("UPSTREAM_REAL_SOURCE_SELECTION_CHANGED")
    env,base,sources,coach=namespace["prepare"](repo)
    if env["BLOBS"]["src/server/Game.server.luau"][1]!=GAME_ORIGINAL_SHA:
        raise RuntimeError("ACTUAL_OFFICIAL_SERVER_BLOB_CHANGED")
    server_candidate=candidate(repo,GAME_PATH,GAME_SHA,sources["Game"],GAME_PATCHES)
    coach_candidate=candidate(repo,COACH_PATH,COACH_SHA,coach,COACH_PATCHES)
    for anchor,extra in EXTRA_BY_ANCHOR.items():
        base["LUAU_TEST"]=exact(base["LUAU_TEST"],anchor,anchor+"\n"+extra,
                               "original_real_snapshot_assertion")
    selected_sources=dict(sources)
    selected_sources["Game"]=server_candidate
    return namespace,env,base,selected_sources,coach_candidate,game_anchor_check(server_candidate)


def game_anchor_check(s: str)->str:
    if s.count("snapshotUpdateId += 1")!=1 or s.count(
        "updateId = snapshotUpdateId")!=1:
        raise RuntimeError("SERVER_SNAPSHOT_VERSION_AMBIGUOUS")
    return "server_monotonic_versioned"


def run(luau: str, file: Path, namespace, env, base, sources, coach):
    return namespace["run"](luau,file,env,base,sources,coach)


def execute(repo: Path, luau: str):
    namespace,env,base,sources,coach,_ = prepare(repo)
    with TemporaryDirectory(prefix="p0d_s1_monotonic_snapshot_") as p:
        out=Path(p)/"real_game_and_coach_candidate.luau"
        status,log=run(luau,out,namespace,env,base,sources,coach)
        found=re.search(r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)",log)
        if status!=0 or not found or int(found.group(1))<154:
            raise RuntimeError("REAL_SNAPSHOT_MONOTONIC_POSITIVE_FAILED "+log[-1800:])
        print("P0D_S1_V6_REAL_SERVER_VERSIONED_COACH_NATIVE_PASS checks="+found.group(1))
        for label,module,old,bad,expected in MUTANTS:
            s=dict(sources)
            modified_coach=coach
            if module=="Game":
                s["Game"]=exact(s["Game"],old,bad,label)
            else:
                modified_coach=exact(coach,old,bad,label)
            rc,log=run(luau,out,namespace,env,base,s,modified_coach)
            if rc==0 or expected not in log:
                raise RuntimeError("UNDETECTED_VERSION_PROTOCOL_MUTATION_"+label+" "+log[-1100:])
            print("P0D_S1_SNAPSHOT_ORDER_MUTANT_REJECTED "+label)
        print("P0D_S1_REAL_SNAPSHOT_MONOTONIC_FINAL_SUCCESS mutants="+str(len(MUTANTS)))


def selftest():
    assert len(RC)==len(UPSTREAM)==len(UPSTREAM_BLOB)==40
    assert len(GAME_SHA)==len(COACH_SHA)==40
    assert blob_sha(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert len(GAME_PATCHES)==2 and len(COACH_PATCHES)==4
    assert len(EXTRA_BY_ANCHOR)==5 and len(MUTANTS)==6
    assert len({m[0] for m in MUTANTS})==len(MUTANTS)
    assert exact("a@b","@","#","positive")=="a#b"
    for text,needle in (("a","not_found"),("double double","double")):
        try:exact(text,needle,"bad","negative")
        except RuntimeError:pass
        else:raise AssertionError("BAD_SOURCE_ANCHOR_ACCEPTED")
    print("P0D_S1_SNAPSHOT_ORDER_SELFTEST_PASS checks=9")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.repo or not args.luau:
        p.error("provide --repo and --luau for genuine native Luau")
    execute(args.repo.resolve(),args.luau)
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError,ValueError,OSError,UnicodeError) as e:
        print("P0D_S1_SNAPSHOT_ORDER_FAIL_CLOSED "+str(e),file=sys.stderr)
        sys.exit(2)
