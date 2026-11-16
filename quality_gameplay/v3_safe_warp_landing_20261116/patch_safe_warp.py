#!/usr/bin/env python3
"""Fail-closed, one-original-module source overlay for V3 Assassin/Esper move safety."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau"
EXPECTED_GIT_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"

OLD = """local function safeMove(char:Model,root:BasePart,amount:number):boolean
 -- Egg carriers do not get a short-cut across walls or instantly through a siege route.
 local v=root.CFrame.LookVector
 local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={char};ray.RespectCanCollide=true
 local start=root.Position+Vector3.new(0,2,0)
 local collision=workspace:Raycast(start,v*amount,ray)
 local distance=if collision then math.max(0,collision.Distance-3) else amount
 if distance<3 then return false end
 -- Airborne crossing is NOT permitted: land only on physical navigable ground.
 local landing=root.Position+v*distance
 local downward=workspace:Raycast(landing+Vector3.new(0,6,0),Vector3.new(0,-17,0),ray)
 if not downward or not downward.Instance.CanCollide then return false end
 if math.abs(landing.Y-downward.Position.Y)>8 then return false end
 char:PivotTo(CFrame.new(Vector3.new(landing.X,downward.Position.Y+3,landing.Z),landing+v))
 return true
end"""

NEW = """local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean
 -- Private V3 uses one active arena per mode. Never dash/warp outside its floor.
 local arena=session.world and session.world:FindFirstChild("TacticalBattlefield")
 if not arena or not arena:IsA("BasePart") or not arena.Parent or not arena.CanCollide then return false end
 local v=root.CFrame.LookVector
 local right=root.CFrame.RightVector
 local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={char};ray.RespectCanCollide=true
 -- Trace a 3x3 cross-section: the old single center/head ray missed low
 -- barriers, narrow side walls and overhangs. Use the nearest collision.
 local distance=amount
 for _,height in ipairs({-1.1,2,4.6}) do
  for _,side in ipairs({-1.3,0,1.3}) do
   local origin=root.Position+Vector3.new(0,height,0)+right*side
   local hit=workspace:Raycast(origin,v*amount,ray)
   if hit then distance=math.min(distance,math.max(0,hit.Distance-3)) end
  end
 end
 if distance<3 then return false end
 local landing=root.Position+v*distance
 -- Existing Studio arena is unrotated; reject exits, including return into
 -- the other match's field/lobby, with a conservative 4.5-stud margin.
 if math.abs(landing.X-arena.Position.X)>arena.Size.X*.5-4.5
  or math.abs(landing.Z-arena.Position.Z)>arena.Size.Z*.5-4.5 then return false end
 local ground=workspace:Raycast(landing+Vector3.new(0,6,0),Vector3.new(0,-17,0),ray)
 if not ground or not ground.Instance.CanCollide then return false end
 if math.abs(landing.Y-ground.Position.Y)>8 then return false end
 local target=Vector3.new(landing.X,ground.Position.Y+3,landing.Z)
 -- The root cannot be embedded inside a wall, player or low roof even
 -- when a single ray found legal ground. The lower edge stays above floor.
 local overlap=OverlapParams.new()
 overlap.FilterType=Enum.RaycastFilterType.Exclude
 overlap.FilterDescendantsInstances={char}
 overlap.RespectCanCollide=true
 for _,part in ipairs(workspace:GetPartBoundsInBox(CFrame.new(target),Vector3.new(3.2,4.5,3.2),overlap)) do
  if part.CanCollide then return false end
 end
 char:PivotTo(CFrame.new(target,target+v))
 return true
end"""

OLD_NINJA = "owner.heldEggs==0 and safeMove(char,root,25)"
NEW_NINJA = "owner.heldEggs==0 and safeMove(session,char,root,25)"
OLD_ESPER = "if owner.heldEggs==0 then safeMove(char,root,20) end"
NEW_ESPER = "if owner.heldEggs==0 then safeMove(session,char,root,20) end"


def git_blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def patch(original: bytes) -> bytes:
    if git_blob_sha(original) != EXPECTED_GIT_BLOB:
        raise ValueError("ORIGINAL_SOURCE_LOCK_MISMATCH: reject changed Game/Combat source")
    text = original.decode("utf-8")
    for anchor in (OLD, OLD_NINJA, OLD_ESPER):
        if text.count(anchor) != 1:
            raise ValueError("UNIQUE_SOURCE_ANCHOR_MISMATCH: refuse partial edit")
    patched = text.replace(OLD, NEW, 1).replace(OLD_NINJA, NEW_NINJA, 1).replace(OLD_ESPER, NEW_ESPER, 1)
    if patched.count("local function safeMove(") != 1:
        raise ValueError("DUPLICATE_WARP_AUTHORITY")
    return patched.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ORIGINAL)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.source.resolve() == args.out.resolve():
        raise SystemExit("REFUSE_ORIGINAL_SOURCE_OVERWRITE")
    source = args.source.read_bytes()
    result = patch(source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(result)
    print("GQ_V3_SAFE_WARP_SOURCE_LOCK_PASS", git_blob_sha(source), hashlib.sha256(result).hexdigest())


if __name__ == "__main__":
    main()
