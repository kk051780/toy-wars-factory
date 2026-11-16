#!/usr/bin/env python3
"""Fail-closed, author-preserving PRIVATE EGGRUMBLE stale-avatar carrier death fence.

ONLY generated Host is changed. Original V3 21-script project sources are untouched.
Never merges, publishes, or writes official RC.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AUTHOR = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
SOURCE = AUTHOR / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
PROJECT = AUTHOR / "EGGRUMBLE_V3_STUDIO.project.json"
AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
HOST_NODE = "EGGRUMBLE_LobbyCastleModesPreview"

def git_blob(source: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(source)).encode("ascii") + b"\0" + source).hexdigest()

def patch(original: str) -> str:
    if git_blob(original.encode("utf-8")) != ORIGINAL_BLOB:
        raise ValueError("SOURCE_LOCK: original #482 Host blob drift")
    needle = '      if joined[player.UserId]~=mode then return end'
    replacement = (
        '      -- Reject old Humanoid.Died after respawn; only the current avatar owns these eggs.\n'
        '      if joined[player.UserId]~=mode or sessions[mode]~=session\n'
        '       or player.Character~=character or session.rules.phase~="ACTIVE" then return end'
    )
    if original.count(needle) != 1:
        raise ValueError("SOURCE_LOCK: original carrier callback guard not unique")
    if original.count('humanoid.Died:Connect(function()') != 1:
        raise ValueError("SOURCE_LOCK: Died callback changed")
    updated = original.replace(needle, replacement, 1)
    if updated.count("session.dropCarrierEggs(tostring(player.UserId),") != 1:
        raise ValueError("SOURCE_LOCK: carrier egg authority drift")
    return updated

def native_cases(patched: str) -> str:
    """Extract and run the actual Host Died callback rather than an invented mirror."""
    start='humanoid.Died:Connect(function()\n'
    stop='\n     end))'
    if patched.count(start)!=1:
        raise ValueError("SOURCE_LOCK: callback extraction start mismatch")
    body=patched.split(start,1)[1]
    if body.count(stop)<1:
        raise ValueError("SOURCE_LOCK: callback extraction end missing")
    body=body.split(stop,1)[0]
    if 'session.dropCarrierEggs(tostring(player.UserId),' not in body:
        raise ValueError("SOURCE_LOCK: callback mutation not permitted")
    return """-- Exact callback extracted from pinned author original, patched single-Host overlay
local root={X=0,Y=0,Z=0}
local old={FindFirstChild=function(self,name)
 if name=="HumanoidRootPart" then return {Position={X=7,Y=2,Z=9}} end
end}
local current={FindFirstChild=old.FindFirstChild}
local player={UserId=42,Character=old}
local mode="TEAM"
local calls=0
local lastOwner=nil
local session={rules={phase="ACTIVE"},castleLocations={["42"]={X=3,Y=4,Z=5}}}
session.dropCarrierEggs=function(owner,pos)
 calls+=1
 lastOwner=owner
 assert(pos.X==7 or pos.X==3)
end
local joined={[42]="TEAM"}
local sessions={TEAM=session}
local character=old
local function actualDiedCallback()
""" + body + """
end
actualDiedCallback()
assert(calls==1 and lastOwner=="42","live avatar death must drop eggs")
player.Character=current
actualDiedCallback()
assert(calls==1,"stale avatar death may not drop new avatar eggs")
player.Character=old
sessions.TEAM={}
actualDiedCallback()
assert(calls==1,"old session cannot drop new session eggs")
sessions.TEAM=session
joined[42]="BATTLE_ROYALE"
actualDiedCallback()
assert(calls==1,"cross-mode death callback must be blocked")
joined[42]="TEAM"
session.rules.phase="FINISHED"
actualDiedCallback()
assert(calls==1,"finished match death callback must be blocked")
session.rules.phase="ACTIVE"
character=current
player.Character=current
actualDiedCallback()
assert(calls==2,"same-session new avatar must drop its own eggs")
character={FindFirstChild=function() return nil end}
player.Character=character
actualDiedCallback()
assert(calls==3,"current avatar without root uses castle location")
print("GQ_STALE_AVATAR_CARRIER_REAL_CALLBACK_NATIVE=PASS 7 CASES")
"""


def walk_project(tree: dict, out: Path) -> tuple[dict, int]:
    copied = copy.deepcopy(tree)
    scripts = 0

    def visit(node: dict, path: tuple[str, ...] = ()) -> None:
        nonlocal scripts
        for key, value in node.items():
            if key == "$path":
                scripts += 1
                if path[-1] == HOST_NODE:
                    node[key] = "HostOverlay.server.luau"
                else:
                    target = (AUTHOR / value).resolve()
                    if not target.is_file() or not target.is_relative_to(AUTHOR.resolve()):
                        raise ValueError(f"Missing / escaped original source: {target}")
                    node[key] = os.path.relpath(target, out).replace("\\", "/")
            elif isinstance(value, dict):
                visit(value, path + (key,))
    visit(copied)
    if scripts != 21:
        raise ValueError(f"Unexpected original source count: {scripts} != 21")
    return copied, scripts

def compose(out: Path) -> dict:
    original_bytes = SOURCE.read_bytes()
    if git_blob(original_bytes) != ORIGINAL_BLOB:
        raise ValueError("Pinned original source SHA mismatch")
    original = original_bytes.decode("utf-8")
    patched = patch(original)
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    mapped, count = walk_project(project, out)
    mapped["name"] = "EGGRUMBLE_V3_CARRIER_STALE_AVATAR_PRIVATE_NOT_RC"
    (out / "HostOverlay.server.luau").write_text(patched, encoding="utf-8", newline="")
    (out / "native_cases.luau").write_text(native_cases(patched), encoding="utf-8", newline="")
    (out / "private.project.json").write_text(
        json.dumps(mapped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    receipt = {
        "feature": "GQ_V3_CARRIER_STALE_AVATAR_DIED_FENCE_20261116",
        "author_head": AUTHOR_HEAD,
        "original_host_blob": ORIGINAL_BLOB,
        "patched_host_blob": git_blob(patched.encode("utf-8")),
        "source_count": count,
        "modified_original_script_count": 1,
        "mode": "PRIVATE_SOURCE_ONLY",
        "formal_rc": "NOT_INTEGRATED",
        "studio_android": "NOT_TESTED",
        "rollback": "Select original Host blob and remove HostOverlay (other20 unchanged)",
    }
    (out / "receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compose(args.out.resolve()), ensure_ascii=False, indent=2))
