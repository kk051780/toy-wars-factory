#!/usr/bin/env python3
"""GQ8 first-join lobby void fix: one already-authorized Host source, no second Game.

This is a PRIVATE source admission candidate. It never writes canonical RC.
The input must be the original same-HEAD official 31-script Place artifact.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

PINNED_OFFICIAL_HEAD = "2291154fd07c8d8af086f76199bf585ff2c725c4"
PINNED_PLACE_SHA256 = "87ca0135a1b3ec6fcc8b35f55856f58a200ca9cd9b89050da6e30ed2524eb082"
PINNED_HOST_SHA256 = "9fd1f9211ff8f99cecc1dff1c09ff66e61ea4575a19e6c7f440b6932f00ddc37"
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
FEATURE = "GQ8_LOBBY_VOID_SPAWN_FLOOR_20261117"
ANCHOR = "local function board(at:BasePart,label:string)"
# Strictly one new, passive, Studio-only lobby floor and SpawnLocation.
# The existing session/queue/Game/Combat/AI/Item/Store code is untouched.
INSERT = """-- GQ8_LOBBY_VOID_SPAWN_FLOOR_20261117: original official Place has zero
-- Workspace Parts/SpawnLocations. First join otherwise falls into void before
-- the seven role stands or TEAM/BR portals are usable.
local lobbySafetyFloor=block(folder,"EGGRUMBLE_LobbySafetyFloor",
 root+Vector3.new(0,-5,37),Vector3.new(210,6,220),Color3.fromRGB(100,141,104))
lobbySafetyFloor.Material=Enum.Material.Grass
lobbySafetyFloor.CanCollide=true
if not spawn then
 local lobbySpawn=Instance.new("SpawnLocation")
 lobbySpawn.Name="EGGRUMBLE_LobbySpawn"
 lobbySpawn.Size=Vector3.new(10,1,10)
 lobbySpawn.Position=root+Vector3.new(0,0.5,0)
 lobbySpawn.Anchored=true
 lobbySpawn.Neutral=true
 lobbySpawn.Enabled=true
 lobbySpawn.AllowTeamChangeOnTouch=false
 lobbySpawn.CanCollide=true
 lobbySpawn.Transparency=1
 lobbySpawn.Parent=folder
end
-- CharacterAdded may beat the dynamically installed SpawnLocation in Studio.
-- Recover only idle/queued avatars outside the safe floor: never teleport an
-- ACTIVE/RESULTS castle participant or alter their inventory, HP, or team.
local function recoverIdleSpawn(player:Player,character:Model)
 task.delay(0.25,function()
  if player.Parent~=Players or player.Character~=character then return end
  local mode=joined[player.UserId]
  if mode and sessions[mode] then return end
  local hum=character:FindFirstChildOfClass("Humanoid")
  local pivot=character:FindFirstChild("HumanoidRootPart")
  if not hum or hum.Health<=0 or not pivot or not pivot:IsA("BasePart") then return end
  local delta=pivot.Position-root
  if math.abs(delta.X)>85 or delta.Z < -65 or delta.Z>136 or delta.Y < -7 then
   pivot.AssemblyLinearVelocity=Vector3.zero
   pivot.AssemblyAngularVelocity=Vector3.zero
   pivot.CFrame=CFrame.new(root+Vector3.new(0,4,0))
  end
 end)
end
local function watchLobbyArrival(player:Player)
 player.CharacterAdded:Connect(function(character)
  recoverIdleSpawn(player,character)
 end)
 if player.Character then recoverIdleSpawn(player,player.Character) end
end
Players.PlayerAdded:Connect(watchLobbyArrival)
for _,player in ipairs(Players:GetPlayers()) do watchLobbyArrival(player) end

"""

def require(ok: bool, why: str):
    if not ok:
        raise ValueError("RED_GQ8_LOBBY_VOID_" + why)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def scripts(root: ET.Element):
    results = {}
    for item in root.iter("Item"):
        klass = item.get("class")
        if klass not in ("Script", "LocalScript", "ModuleScript"):
            continue
        p = item.find("Properties")
        require(p is not None, "NO_SCRIPT_PROPERTIES")
        name = p.findtext("string[@name='Name']")
        node = p.find("string[@name='Source']")
        if node is None:
            node = p.find("ProtectedString[@name='Source']")
        require(name is not None and node is not None, "MISSING_SCRIPT_SOURCE")
        require(name not in results, "DUPLICATE_SCRIPT_NAME")
        results[name] = (klass, node, node.text or "")
    return results

def patch(src: str) -> str:
    require(sha(src.encode("utf-8")) == PINNED_HOST_SHA256, "SOURCE_HEAD_DRIFT")
    require(src.count(ANCHOR) == 1, "BOARD_ANCHOR_DRIFT")
    require(FEATURE not in src, "DUPLICATE_BOOTSTRAP")
    require(src.count('local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)') == 1,
            "SPAWN_SOURCE_DRIFT")
    require(src.count('if not RunService:IsStudio() then return end') == 1,
            "STUDIO_ONLY_GUARD_DRIFT")
    require(src.count("local function block(") == 1 and
            src.count('remote.OnServerEvent:Connect(') <= 1, "AUTHORITIES_DRIFT")
    return src.replace(ANCHOR, INSERT + ANCHOR, 1)

def prove(before, after):
    old = scripts(before)
    new = scripts(after)
    require(len(old) == len(new) == 31, "SCRIPT_COUNT")
    require(set(old) == set(new), "SCRIPT_IDENTITY")
    require(HOST in old and old[HOST][0] == new[HOST][0] == "Script", "HOST_CLASS")
    require(set(k for k in old if old[k][2] != new[k][2]) == {HOST},
            "OTHER_30_SOURCES_CHANGED")
    for key in old:
        require(old[key][0] == new[key][0], "CLASS_CHANGED")
    old_host, new_host = old[HOST][2], new[HOST][2]
    require(new_host.replace(INSERT, "", 1) == old_host, "OFF_NOT_BYTE_EXACT")
    require(new_host.count(FEATURE) == 1, "BOOTSTRAP_MULTIPLICITY")
    require(new_host.count('Instance.new("SpawnLocation")') == 1, "SPAWN_MULTIPLICITY")
    require(new_host.count('EGGRUMBLE_LobbySafetyFloor') == 1, "FLOOR_MULTIPLICITY")
    require('lobbySafetyFloor.CanCollide=true' in new_host, "FLOOR_NONCOLLISION")
    require('if mode and sessions[mode] then return end' in new_host,
            "ROUND_TELEPORT_FENCE_MISSING")
    require('player.Character~=character' in new_host, "STALE_AVATAR_FENCE_MISSING")
    require(new_host.count('Players.PlayerAdded:Connect(watchLobbyArrival)') == 1,
            "SPAWN_WATCH_MISSING")
    # These are authored-at-runtime Parts; before boot the Rojo Place is script-only.
    fixed_world = [i.get("class") for i in before.iter("Item")
                   if i.get("class") in ("Part", "SpawnLocation")]
    require(not fixed_world, "INPUT_WORLD_DRIFT")
    return {"source_count": 31, "modified": [HOST],
            "unchanged_source_count": 30, "rollback_exact": True,
            "host_old_sha256": sha(old_host.encode()),
            "host_new_sha256": sha(new_host.encode()),
            "first_join_floor": True, "first_join_spawn": True,
            "idle_avatar_fence": True, "actual_studio": "NOT_TESTED",
            "android": "NOT_TESTED", "owner_fun": "NO_GO",
            "formal_rc": "NOT_ADOPTED"}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--input", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    a.add_argument("--receipt", type=Path, required=True)
    args = a.parse_args()
    before_raw = args.input.read_bytes()
    require(sha(before_raw) == PINNED_PLACE_SHA256, "PLACE_HEAD_DRIFT")
    before = ET.fromstring(before_raw)
    after = ET.fromstring(before_raw)
    s = scripts(after)
    require(HOST in s, "MISSING_HOST")
    s[HOST][1].text = patch(s[HOST][2])
    receipt = prove(before, after)
    receipt.update({"feature": FEATURE, "pinned_official_head": PINNED_OFFICIAL_HEAD,
                    "original_place_sha256": PINNED_PLACE_SHA256})
    require(args.output.resolve() != args.input.resolve(), "OVERWRITE_ORIGINAL")
    require(not args.output.exists(), "OUTPUT_EXISTS")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(ET.tostring(after, encoding="utf-8"))
    receipt["private_candidate_sha256"] = sha(args.output.read_bytes())
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print("GQ8_LOBBY_VOID_ACTUAL_RC31_31_SOURCE_EXACT_OFF_PASS")
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == "__main__":
    main()
