#!/usr/bin/env python3
"""P0D GQ safe lobby: add a physical floor and first-respawn protection to ONE V3 Host.

Source-derived defect: original #482 V3 Studio project has no Workspace
SpawnLocation, while its Host builds prompts, gates and role stands but no
lobby foundation. Keep all other source, existing session/AI and authorities.
This is an isolated PREP candidate, NOT the official RC writer.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

TARGET = "EGGRUMBLE_LobbyCastleModesPreview"
ANCHOR = "local function board(at:BasePart,label:string)"
MARKER = "-- GQ_SAFE_LOBBY_SPAWN_20261117_BEGIN"
END_MARKER = "-- GQ_SAFE_LOBBY_SPAWN_20261117_END"
PATCH = """-- GQ_SAFE_LOBBY_SPAWN_20261117_BEGIN
-- Always provide real ground under all seven role stands and both mode gates.
-- Never add another match/remote or change current TEAM/BR session ownership.
local safeLobbyGround=block(folder,"EGGRUMBLE_LobbySafeGround",
 root+Vector3.new(0,-5,40),Vector3.new(122,8,148),Color3.fromRGB(81,144,105))
safeLobbyGround.Material=Enum.Material.Grass
safeLobbyGround.CanCollide=true
if spawn==nil then
 local safeLobbySpawn=Instance.new("SpawnLocation")
 safeLobbySpawn.Name="EGGRUMBLE_LobbySafeSpawn"
 safeLobbySpawn.Anchored=true
 safeLobbySpawn.Neutral=true
 safeLobbySpawn.AllowTeamChangeOnTouch=false
 safeLobbySpawn.Duration=0
 safeLobbySpawn.Size=Vector3.new(12,1,12)
 safeLobbySpawn.Position=root+Vector3.new(0,2,0)
 safeLobbySpawn.Color=Color3.fromRGB(106,183,133)
 safeLobbySpawn.Parent=folder
end
-- Avatar loading may precede map creation in Studio. Correct only unqueued,
-- current avatars; never teleport current-match humans back into the lobby.
local function placeUnqueuedAvatar(player:Player,character:Model)
 task.defer(function()
  local rootPart=character:FindFirstChild("HumanoidRootPart")
   or character:WaitForChild("HumanoidRootPart",8)
  if player.Parent~=Players or player.Character~=character
   or joined[player.UserId]~=nil then return end
  local humanoid=character:FindFirstChildOfClass("Humanoid")
  if not rootPart or not rootPart:IsA("BasePart")
   or not humanoid or humanoid.Health<=0 then return end
  rootPart.CFrame=CFrame.new(root+Vector3.new(0,8,-10))
 end)
end
local function bindLobbyRespawn(player:Player)
 player.CharacterAdded:Connect(function(character)
  placeUnqueuedAvatar(player,character)
 end)
 if player.Character then placeUnqueuedAvatar(player,player.Character) end
end
Players.PlayerAdded:Connect(bindLobbyRespawn)
for _,p in ipairs(Players:GetPlayers()) do bindLobbyRespawn(p) end
-- GQ_SAFE_LOBBY_SPAWN_20261117_END
"""
BLOCK = PATCH + "\n"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def apply(before: str) -> str:
    if MARKER in before or END_MARKER in before:
        raise ValueError("RED_ALREADY_APPLIED")
    if before.count(ANCHOR) != 1:
        raise ValueError("RED_UNIQUE_BOARD_ANCHOR")
    if before.count('local folder=Instance.new("Folder")') != 1:
        raise ValueError("RED_ORIGINAL_HOST_DRIFT")
    after = before.replace(ANCHOR, BLOCK + ANCHOR, 1)
    if rollback(after) != before:
        raise ValueError("RED_ROLLBACK_NOT_EXACT")
    return after

def rollback(after: str) -> str:
    if after.count(BLOCK) != 1:
        raise ValueError("RED_MARKER_OR_PATCH_DRIFT")
    return after.replace(BLOCK, "", 1)

def mapping(project: Path):
    project = project.resolve(strict=True)
    obj = json.loads(project.read_text(encoding="utf-8"))
    found = {}
    def walk(node, route=()):
        for name, child in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(child, dict):
                raise ValueError("RED_BAD_PROJECT")
            path = route + (name,)
            if "$path" in child:
                if set(child) != {"$path"} or path in found:
                    raise ValueError("RED_BAD_SOURCE_MAPPING")
                found[path] = (project.parent / child["$path"]).resolve(strict=True)
            else:
                walk(child, path)
    walk(obj["tree"])
    if len(found) != 31 or len({p[-1] for p in found}) != 31:
        raise ValueError("RED_NOT_CURRENT31")
    targets = [p for p in found if p[-1] == TARGET]
    if len(targets) != 1:
        raise ValueError("RED_NO_SINGLE_HOST")
    return obj, found, targets[0]

def prepare(base: Path, out: Path):
    base = base.resolve(strict=True)
    out = out.resolve()
    if out.parent != base.parent or out.exists():
        raise ValueError("RED_REQUIRE_NEW_SIBLING_PROJECT")
    obj, old, target = mapping(base)
    original = old[target].read_text(encoding="utf-8")
    updated = apply(original)
    src = out.parent / "GQ_SAFE_LOBBY_HOST.server.luau"
    if src.exists():
        raise ValueError("RED_OUTPUT_SOURCE_EXISTS")
    src.write_text(updated, encoding="utf-8")
    next_project = copy.deepcopy(obj)
    node = next_project["tree"]
    for key in target:
        node = node[key]
    node["$path"] = src.name
    out.write_text(json.dumps(next_project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, selected, selected_target = mapping(out)
    changed = [p for p in old if old[p].read_bytes() != selected[p].read_bytes()]
    if set(old) != set(selected) or selected_target != target or changed != [target]:
        raise ValueError("RED_NOT_SINGLE_HOST_ONLY")
    if rollback(src.read_text(encoding="utf-8")) != original:
        raise ValueError("RED_OFF_NOT_IDENTICAL")
    receipt = {
        "feature_id": "GQ_SAFE_LOBBY_SPAWN_20261117",
        "source_count": 31,
        "changed_existing_source": TARGET,
        "other_30_source_exact": True,
        "rollback_host_exact": True,
        "before_sha256": sha(old[target].read_bytes()),
        "after_sha256": sha(src.read_bytes()),
        "studio_2client": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner_accepted": False,
        "formal_rc_adopted": False,
    }
    (out.parent / "GQ_SAFE_LOBBY_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("GQ_SAFE_LOBBY_ONE_HOST_OTHER30_EXACT_ROLLBACK_PASS")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-source", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.source and args.out_source and not args.base and not args.out:
        args.out_source.write_text(apply(args.source.read_text(encoding="utf-8")), encoding="utf-8")
        print("GQ_SAFE_LOBBY_NATIVE_HOST_CANDIDATE_PREPARED")
    elif args.base and args.out and not args.source and not args.out_source:
        prepare(args.base, args.out)
    else:
        parser.error("provide either --source/--out-source or --base/--out")

if __name__ == "__main__":
    main()
