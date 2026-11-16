#!/usr/bin/env python3
"""Source-locked one-line V3 #484 AI wall-raycast full-step overlay (private only)."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ORIGINAL_AUTHOR_PR = 484
ORIGINAL_AUTHOR_HEAD = "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
ORIGINAL_BLOB = "d9841bb874659129cae6c930bce302ff6936ac4a"
BEFORE = "local ray=workspace:Raycast(at,diff.Unit*math.min(8,diff.Magnitude),p)"
AFTER = "local ray=workspace:Raycast(at,diff.Unit*diff.Magnitude,p)"


class SourceDrift(RuntimeError):
    pass


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def overlay(raw: bytes, *, locked: bool = True) -> bytes:
    if locked and git_blob_sha(raw) != ORIGINAL_BLOB:
        raise SourceDrift(f"current #484 author Router Git blob changed: {git_blob_sha(raw)}")
    text = raw.decode("utf-8")
    if text.count(BEFORE) != 1:
        raise SourceDrift("single original routeClear raycast anchor absent or duplicated")
    for anchor in (
        "local PATH_TRAVEL_SPEED=30", "math.clamp(dt,.05,.3)",
        "routeClear(here,here+direction*step,actors)",
        "local function routeClear(", "params.RespectCanCollide=true",
        "function Router.navigate(", "local MAX_COMPUTES_IN_FLIGHT=2",
    ):
        if anchor not in text:
            raise SourceDrift(f"original navigation source changed at {anchor}")
    updated = text.replace(BEFORE, AFTER, 1)
    if updated.count(AFTER) != 1 or updated.replace(AFTER, BEFORE, 1) != text:
        raise SourceDrift("not a reversible single source hunk")
    return updated.encode("utf-8")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise SourceDrift("refuse in-place change of author source")
    raw = overlay(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(f"GQ_ROUTE_FULLSTEP_PRIVATE_PATCHED_BLOB={git_blob_sha(raw)} bytes={len(raw)} official_rc_adopted=0")


if __name__ == "__main__":
    main()
