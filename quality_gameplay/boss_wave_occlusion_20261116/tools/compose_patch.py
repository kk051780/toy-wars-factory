#!/usr/bin/env python3
"""Source-locked, generated-only wall-occlusion patch for #482 boss shockwave."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ORIGINAL_BLOB = "2670618cba320c51936c750a10e43c194cada0f0"
ORIGINAL_COMMIT = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
FUNCTION_ANCHOR = ' local hitPrompt=Instance.new("ProximityPrompt")'
FUNCTION_ADD = ''' -- Server-authoritative castle-wall occlusion for the telegraphed boss wave.
 local function shockwaveClear(character:Model?,root:BasePart):boolean
  if not character then return false end
  local params=RaycastParams.new()
  params.FilterType=Enum.RaycastFilterType.Exclude
  params.FilterDescendantsInstances={model,character}
  params.RespectCanCollide=true
  -- Use torso height to avoid rejecting targets on flat Terrain.
  local origin=at+Vector3.new(0,2.5,0)
  local direction=(root.Position+Vector3.new(0,2.5,0))-origin
  if direction.Magnitude<=0.01 then return true end
  return workspace:Raycast(origin,direction,params)==nil
 end
'''
DAMAGE_ANCHOR = '''     if d<=11 and math.abs(root.Position.Y-at.Y)<=8 then
      -- Server-side radial attack only, no client-trusted damage remotes.
      h:TakeDamage(28)'''
DAMAGE_REPLACEMENT = '''     if d<=11 and math.abs(root.Position.Y-at.Y)<=8
      and shockwaveClear(c,root) then
      -- Server-side radial attack only; solid walls block the shockwave.
      h:TakeDamage(28)'''


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw).hexdigest()


def patch_bytes(original: bytes) -> bytes:
    actual = git_blob_sha(original)
    if actual != ORIGINAL_BLOB:
        raise ValueError(f"Original boss Git blob drift: {actual} != {ORIGINAL_BLOB}")
    source = original.decode("utf-8")
    for name, anchor in (("helper", FUNCTION_ANCHOR), ("damage", DAMAGE_ANCHOR)):
        if source.count(anchor) != 1:
            raise ValueError(f"Unsafe {name} anchor count: {source.count(anchor)}")
    amended = source.replace(FUNCTION_ANCHOR, FUNCTION_ADD + FUNCTION_ANCHOR, 1)
    amended = amended.replace(DAMAGE_ANCHOR, DAMAGE_REPLACEMENT, 1)
    if amended.count("h:TakeDamage(28)") != 1:
        raise ValueError("Unexpected boss damage authority")
    return amended.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = patch_bytes(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print("GQ_BOSS_WAVE_PATCHED SHA256=" + hashlib.sha256(result).hexdigest())
    print("Original author file unchanged; optional generated boss only; official RC adoption=0")


if __name__ == "__main__":
    main()
