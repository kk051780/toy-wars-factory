#!/usr/bin/env python3
"""Source-locked single-script overlay: no new server authority or script."""
import argparse
import hashlib
from pathlib import Path

ORIGINAL_BLOB = "1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1"
SOURCE_PATH = "handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleCore.server.luau"

OLD = """     elseif root and now-data.lastHit>=2 then
      data.lastHit=now
      local h=nearest.Character:FindFirstChildOfClass("Humanoid")
      if h then h:TakeDamage(6) end -- new underwater neutral only, no KO/score
"""
NEW = """     elseif root and now-data.lastHit>=2 then
      -- Preserve the original two-second neutral attack cadence even behind cover.
      data.lastHit=now
      -- Authoritative wall check. Exclude the creature and this target avatar,
      -- but keep solid coral, reef, and level geometry as blockers.
      local params=RaycastParams.new()
      params.FilterType=Enum.RaycastFilterType.Exclude
      params.FilterDescendantsInstances={creature,nearest.Character}
      params.RespectCanCollide=true
      local origin=creature:GetPivot().Position
      local obstacle=Workspace:Raycast(origin,root.Position-origin,params)
      if not obstacle then
       local h=nearest.Character:FindFirstChildOfClass("Humanoid")
       if h and h.Health>0 then h:TakeDamage(6) end -- existing neutral, no KO/score
      end
"""

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def patch(original: str) -> str:
    if git_blob(original.encode("utf-8")) != ORIGINAL_BLOB:
        raise ValueError("RED original #764 author blob drift")
    if original.count(OLD) != 1 or original.count(NEW):
        raise ValueError("RED non-unique melee source anchor")
    updated = original.replace(OLD, NEW, 1)
    if updated.replace(NEW, OLD, 1) != original:
        raise ValueError("RED inverse source mismatch")
    return updated

def restore(updated: str) -> str:
    if updated.count(NEW) != 1 or updated.count(OLD):
        raise ValueError("RED non-unique rollback anchor")
    original = updated.replace(NEW, OLD, 1)
    if git_blob(original.encode("utf-8")) != ORIGINAL_BLOB:
        raise ValueError("RED rollback differs from immutable #764 original")
    return original

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = args.source.read_bytes().decode("utf-8")
    updated = patch(original)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(updated.encode("utf-8"))
    assert restore(updated) == original
    print("GQ8_LEVIATHAN_LOS_SOURCE_PATCH_AND_EXACT_OFF_PASS",
          ORIGINAL_BLOB, len(updated.encode("utf-8")))

if __name__ == "__main__":
    main()
