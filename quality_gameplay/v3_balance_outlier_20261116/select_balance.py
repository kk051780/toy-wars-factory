#!/usr/bin/env python3
"""Select the original #487 BalanceMetrics with one bounded round-tail fairness fix.

This is NOT a new score/combat authority: the selected source replaces the
existing BalanceMetrics slot in a private candidate build. The original 31-source
RC companion remains unchanged until authenticated #220 intake.
"""
import argparse
import hashlib
from pathlib import Path

ORIGINAL_GIT_BLOB = "1cb9316faa41f646bf2c18e15c6ddc46fc93bc78"
ORIGINAL_HEAD = "438a406ccfda5563053d783d7561797ccd364361"
ORIGINAL_PATH = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BalanceMetrics.luau"
EDITS = (
    (
        " local durations={}\n local maxKo=0\n",
        " local durations={}\n local maxKo=0\n local overlongCount=0\n local longestRoundSeconds=0\n",
    ),
    (
        "  local seconds=integer(match.seconds,0,3600)\n  table.insert(durations,seconds)\n",
        "  local seconds=integer(match.seconds,0,3600)\n"
        "  if seconds>B.MAX_SECONDS then overlongCount+=1 end\n"
        "  longestRoundSeconds=math.max(longestRoundSeconds,seconds)\n"
        "  table.insert(durations,seconds)\n",
    ),
    (
        "  tooLong=median>B.MAX_SECONDS,modeCoverage=wins.TEAM>0 and wins.BATTLE_ROYALE>0,\n"
        "  maxKo=maxKo,releaseReady=median>=B.MIN_SECONDS and median<=B.MAX_SECONDS\n"
        "   and wins.TEAM>0 and wins.BATTLE_ROYALE>0}\n",
        "  tooLong=median>B.MAX_SECONDS or overlongCount>0,\n"
        "  overlongCount=overlongCount,longestRoundSeconds=longestRoundSeconds,\n"
        "  modeCoverage=wins.TEAM>0 and wins.BATTLE_ROYALE>0,\n"
        "  maxKo=maxKo,releaseReady=median>=B.MIN_SECONDS and median<=B.MAX_SECONDS\n"
        "   and wins.TEAM>0 and wins.BATTLE_ROYALE>0 and overlongCount==0}\n",
    ),
)

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def select(original: bytes) -> bytes:
    if git_blob_sha(original) != ORIGINAL_GIT_BLOB:
        raise ValueError("RED: upstream BalanceMetrics blob drift; refuse non-exact patch")
    text = original.decode("utf-8")
    for old, new in EDITS:
        if text.count(old) != 1:
            raise ValueError("RED: patch anchor missing or ambiguous")
        text = text.replace(old, new, 1)
    patch = text.encode("utf-8")
    if not patch.startswith(b"--!strict"):
        raise ValueError("RED: invalid source header")
    return patch

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--off-output", required=True)
    a = parser.parse_args()
    source = Path(a.input).read_bytes()
    selected = select(source)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.off_output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_bytes(selected)
    Path(a.off_output).write_bytes(source)
    if Path(a.off_output).read_bytes() != source:
        raise AssertionError("RED: OFF rollback not byte exact")
    print("BALANCE_OUTLIER_SOURCE_SELECT_PASS original=" + git_blob_sha(source)
          + " selected=" + git_blob_sha(selected)
          + " native_required=true studio=UNKNOWN rc_adopted=false")

if __name__ == "__main__":
    main()
