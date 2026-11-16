#!/usr/bin/env python3
"""Single-callback reversible source patch for the existing EGGRUMBLE V3 Host."""
import argparse
import hashlib
from pathlib import Path

OWNER_HEAD = "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
OWNER_HOST_BLOB = "c1ff23cd2883401d44d6fc47311bebcfd53eb1c6"
OWNER_PATH = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
BEFORE = """  if mode and not sessions[mode] then
   local q=queues[mode]
   local idx=table.find(q,p)
   if idx then table.remove(q,idx) end
  end"""
AFTER = """  if mode and not sessions[mode] then
   local q=queues[mode]
   local idx=table.find(q,p)
   if idx then
    table.remove(q,idx)
    -- Cancel the abandoned first-player timer only when nobody remains.
    -- A subsequent first entrant receives the full COUNTDOWN seconds.
    if #q==0 then queueEpoch[mode]+=1 end
   end
  end"""
MARKER = "if #q==0 then queueEpoch[mode]+=1 end"

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()

def compose(original: bytes, enabled: bool = True, verify: bool = True) -> bytes:
    if verify and blob_sha(original) != OWNER_HOST_BLOB:
        raise ValueError("RED: original owner Host blob drift; do not patch")
    if not enabled:
        return original
    text = original.decode("utf-8")
    if text.count(BEFORE) != 1 or MARKER in text:
        raise ValueError("RED: expected unique PlayerRemoving source anchor missing/duplicated")
    result = text.replace(BEFORE, AFTER, 1).encode("utf-8")
    if result == original or result.count(MARKER.encode()) != 1:
        raise AssertionError("RED: overlay not unique")
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--off", action="store_true")
    args = ap.parse_args()
    input_bytes = Path(args.input).read_bytes()
    result = compose(input_bytes, enabled=not args.off)
    target = Path(args.output)
    if target.resolve() == Path(args.input).resolve():
        raise ValueError("RED: cannot modify original author source in place")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    print("QUEUE_TIMER_PATCH", "OFF_ROLLBACK_BYTE_EXACT" if args.off else "ON_ONE_HOST_CALLBACK",
          blob_sha(input_bytes), len(result))

if __name__ == "__main__":
    main()
