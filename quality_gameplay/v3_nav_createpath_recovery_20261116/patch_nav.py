#!/usr/bin/env python3
"""Source-exact, fail-closed single-author V3 AI CreatePath error recovery overlay.

This produces a PRIVATE candidate from immutable original #482; never writes
the original author source, main, or the canonical RC.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_BLOB = "810155857fcd56bd93623e4deb5a4f7de530031b"

BEFORE = '''  local path=PathfindingService:CreatePath({
   AgentRadius=2,AgentHeight=5,AgentCanJump=false,
   WaypointSpacing=8,Costs={Water=15},
  })
  local ok=pcall(function()
   path:ComputeAsync(surfaceAt(at,actors),surfaceAt(expectedTarget,actors))
  end)
  inFlight=math.max(0,inFlight-1)
  if states[id]~=state or not model.Parent then
   path:Destroy();return
  end
'''

AFTER = '''  -- Creation and compute must share one error boundary: a CreatePath
  -- exception must NEVER leak either of the two global navigation permits.
  local path:Path?=nil
  local ok=pcall(function()
   path=PathfindingService:CreatePath({
    AgentRadius=2,AgentHeight=5,AgentCanJump=false,
    WaypointSpacing=8,Costs={Water=15},
   })
   path:ComputeAsync(surfaceAt(at,actors),surfaceAt(expectedTarget,actors))
  end)
  inFlight=math.max(0,inFlight-1)
  if not path then
   -- A failed create is retryable, but only the same still-owned actor may
   -- be unlocked; never resurrect a removed/replaced session's path state.
   if states[id]==state then
    state.inFlight=false
    state.failed=(state.failed or 0)+1
    state.retryAt=os.clock()+RECOMPUTE_SECONDS
   end
   return
  end
  if states[id]~=state or not model.Parent then
   path:Destroy();return
  end
'''


class SourceDrift(RuntimeError):
    pass


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def overlay(raw: bytes, *, locked: bool = True) -> bytes:
    if locked and blob_sha(raw) != ORIGINAL_BLOB:
        raise SourceDrift(f"original #482 BotPathRouter Git blob mismatch: {blob_sha(raw)}")
    src = raw.decode("utf-8")
    if src.count(BEFORE) != 1:
        raise SourceDrift("CreatePath/ComputeAsync/permit-release anchor is missing or duplicated")
    result = src.replace(BEFORE, AFTER, 1)
    if result.count("inFlight=math.max(0,inFlight-1)") != 1:
        raise SourceDrift("navigation permit release count differs from exactly one")
    if result.count("MAX_COMPUTES_IN_FLIGHT=2") != 1 or result.count("function Router.navigate(") != 1:
        raise SourceDrift("existing navigation authority or concurrency constant drifted")
    if "local ok=pcall(function()\n   path=PathfindingService:CreatePath" not in result:
        raise SourceDrift("creation is not protected by the same error boundary")
    return result.encode("utf-8")


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise SourceDrift("original source may not be overwritten")
    patched = overlay(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    print(f"source={ORIGINAL_BLOB} patched_blob={blob_sha(patched)} bytes={len(patched)} AUTHOR_ONLY_OFFICIAL_RC=0")


if __name__ == "__main__":
    main()
