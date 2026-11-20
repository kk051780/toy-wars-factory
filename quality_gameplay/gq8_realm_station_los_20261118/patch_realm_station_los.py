#!/usr/bin/env python3
"""GQ8: reversible, *original-author pinned* Realm station prompt LOS overlay.

Scope is ONLY the three prompts created by RealmBattleCore.prompt:
dive, surface and public fighter boarding. It never changes LSS prompts,
Host, Game, Combat, AI, score, Store, or the public default profile.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

FEATURE_ID = "GQ8_REALM_STATION_SERVER_LOS_20261118"
UPSTREAM_PR = 764
UPSTREAM_HEAD = "c51de1ed4feb7a7500ada95d21282402053ef988"
UPSTREAM_BLOB = "1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1"
UPSTREAM_PATH = ("handoffs/EGGRUMBLE-REALM-CORE-20261118/"
                 "EGGRUMBLE_RealmBattleCore.server.luau")
OLD = """  if not r or not h or h.Health<=0 or (r.Position-p.Position).Magnitude>16 then return end
  callback(player,h)
"""
NEW = """  if not r or not h or h.Health<=0 or (r.Position-p.Position).Magnitude>16 then return end
  -- A client-side RequiresLineOfSight prompt is not a server authorization.
  -- Raycast to the top of the same station pad, excluding only this avatar.
  local sightTarget=p.Position+Vector3.new(0,p.Size.Y*.5+.25,0)
  local sightParams=RaycastParams.new()
  sightParams.FilterType=Enum.RaycastFilterType.Exclude
  sightParams.FilterDescendantsInstances={c}
  sightParams.RespectCanCollide=true
  local sightHit=Workspace:Raycast(r.Position,sightTarget-r.Position,sightParams)
  if sightHit and sightHit.Instance~=p then return end
  callback(player,h)
"""


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def apply(original: bytes) -> bytes:
    if git_blob_sha(original) != UPSTREAM_BLOB:
        raise ValueError("RED_REALM_LOS_PINNED_SOURCE_DRIFT")
    text = original.decode("utf-8")
    if text.count(OLD) != 1 or NEW in text:
        raise ValueError("RED_REALM_LOS_ANCHOR_OR_DOUBLE_PATCH")
    selected = text.replace(OLD, NEW, 1).encode("utf-8")
    if rollback(selected) != original:
        raise ValueError("RED_REALM_LOS_INVERSE")
    return selected


def rollback(selected: bytes) -> bytes:
    text = selected.decode("utf-8")
    if text.count(NEW) != 1 or OLD in text:
        raise ValueError("RED_REALM_LOS_SELECTED_SOURCE_DRIFT")
    restored = text.replace(NEW, OLD, 1).encode("utf-8")
    if git_blob_sha(restored) != UPSTREAM_BLOB:
        raise ValueError("RED_REALM_LOS_NONORIGINAL_ROLLBACK")
    return restored


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--rollback", action="store_true")
    a = p.parse_args()
    content = a.source.read_bytes()
    value = rollback(content) if a.rollback else apply(content)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(value)
    print(FEATURE_ID, "OFF31" if a.rollback else "SOURCE_PREP",
          "upstream", UPSTREAM_HEAD, "blob", git_blob_sha(value),
          "sha256", hashlib.sha256(value).hexdigest(), "bytes", len(value))


if __name__ == "__main__":
    main()
