#!/usr/bin/env python3
"""Exact-source private ON/OFF compose. Does not edit original author files."""
import argparse
import hashlib
from pathlib import Path

AUTHOR_PATH = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_FieldItemPickups.luau"
AUTHOR_BLOB = "24a35a2e6004c635456cc6f2288cf13f8365ba27"
REQUIRE_ANCHOR = 'local Items={}\n'
DASH_ANCHOR = '''   elseif kind=="DASH" then
    local previous=hum.WalkSpeed
    hum.WalkSpeed=math.max(previous,27)
    task.delay(5,function()
     if hum.Parent and hum.Health>0 and hum.WalkSpeed==math.max(previous,27) then
      hum.WalkSpeed=previous
     end
    end)'''
DASH_PATCH = '''   elseif kind=="DASH" then
    DashLease.apply(hum,session,task.delay,function()
     return canUse(player,session) and player.Character==hum.Parent
    end)'''


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def compose(data: bytes, enabled: bool) -> bytes:
    if git_blob_sha(data) != AUTHOR_BLOB:
        raise ValueError("source lock mismatch: original ITEM author blob changed")
    text = data.decode("utf-8")
    if not enabled:
        return data
    if text.count(REQUIRE_ANCHOR) != 1 or text.count(DASH_ANCHOR) != 1:
        raise ValueError("ambiguous or stale original DASH author hunk")
    text = text.replace(REQUIRE_ANCHOR,
                        REQUIRE_ANCHOR + 'local DashLease=require(script.Parent:WaitForChild("EGGRUMBLE_DashLease"))\n')
    return text.replace(DASH_ANCHOR, DASH_PATCH).encode("utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default=AUTHOR_PATH)
    p.add_argument("--out", required=True)
    p.add_argument("--enabled", action="store_true")
    args = p.parse_args()
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    original = Path(args.source).read_bytes()
    target.write_bytes(compose(original, args.enabled))
    print(f"GQ_DASH_SOURCE_LOCK_PASS enabled={args.enabled} output_bytes={target.stat().st_size}")


if __name__ == "__main__":
    main()
