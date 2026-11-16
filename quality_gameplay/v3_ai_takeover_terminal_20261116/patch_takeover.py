#!/usr/bin/env python3
"""One-function additive EGGRUMBLE V3 BotActors takeover lifecycle guard.

Source input must be the currently selected singleton BotActors (e.g. the
original #484/#555 selected actor). No new actor, Game, Remote, Store or loop.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ANCHOR = (
    ' session.takeover=function(id:string):boolean\n'
    '  local state=session.rules.castles[id]\n'
)
REPLACEMENT = (
    ' session.takeover=function(id:string):boolean\n'
    '  -- Never create a disconnected-player replacement after the match ends\n'
    '  -- or while its world is being removed. No new actor authority is added.\n'
    '  if session.rules.phase~="ACTIVE" or not folder.Parent then return false end\n'
    '  local state=session.rules.castles[id]\n'
)
PREEXISTING_GUARD = '  if not state or not state.alive or bots[id] then return false end\n'

def patch(src: str) -> str:
    if src.count(ANCHOR) != 1:
        raise ValueError("RED: singleton takeover anchor missing or duplicated")
    if src.count(PREEXISTING_GUARD) != 1:
        raise ValueError("RED: existing alive/duplicate-actor gate was changed")
    if REPLACEMENT in src:
        raise ValueError("RED: terminal fence already selected; do not double-apply")
    out = src.replace(ANCHOR, REPLACEMENT, 1)
    if out.replace(REPLACEMENT, ANCHOR, 1) != src:
        raise AssertionError("RED: byte-exact source rollback failed")
    return out

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_text(encoding="utf-8")
    output = patch(raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8")
    print(f"GQ_AI_TAKEOVER_TERMINAL_FENCE: original={len(raw.encode())}B "
          f"selected={len(output.encode())}B; inverse-byte-exact=PASS")

if __name__ == "__main__":
    main()
