#!/usr/bin/env python3
"""P0D #340: isolated, reversible compact-HUD overlay on the FINAL assembled RC65.
No new GUI authority, Remote, Game, DataStore or payment. Does not write canonical RC.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

HUD = "client/HUD.client.luau"
FEATURE = "P0D_UX_HUD_COMPACT_V1"
START = "-- P0D_UX_HUD_COMPACT_V1_BEGIN"
END = "-- P0D_UX_HUD_COMPACT_V1_END"
PATCH = r'''
-- P0D_UX_HUD_COMPACT_V1_BEGIN
-- The one existing Game/HUD/Remote remains the sole owner of match information.
-- The temporary help panel starts hidden; touch camera and jump areas stay clear.
top.Size = UDim2.new(.65, 0, 0, 42)
top.Position = UDim2.new(.175, 0, 0, 3)
top.TextSize = 13
status.Size = UDim2.new(.65, 0, 0, 23)
status.Position = UDim2.new(.175, 0, 0, 47)
status.TextSize = 12
instructions.Visible = false
instructions.AnchorPoint = Vector2.new(1, 0)
instructions.Position = UDim2.new(1, -8, 0, 75)
instructions.Size = UDim2.new(0, 254, 0, 50)
instructions.Text = "相手の卵を取って自陣へ！　2人対戦・1人では開始できません"
instructions.TextSize = 12
instructions.ZIndex = 22
local compactHelp = Instance.new("TextButton")
compactHelp.Name = "P0DCompactHelp"
compactHelp.Size = UDim2.fromOffset(32, 28)
compactHelp.AnchorPoint = Vector2.new(1, 0)
compactHelp.Position = UDim2.new(1, -8, 0, 7)
compactHelp.BackgroundColor3 = Color3.fromRGB(25, 39, 58)
compactHelp.BackgroundTransparency = .17
compactHelp.Text = "?"
compactHelp.TextSize = 18
compactHelp.TextColor3 = Color3.fromRGB(255, 255, 255)
compactHelp.Font = Enum.Font.GothamBold
compactHelp.BorderSizePixel = 0
compactHelp.ZIndex = 22
compactHelp.Parent = gui
local helpCorner = Instance.new("UICorner")
helpCorner.CornerRadius = UDim.new(0, 8)
helpCorner.Parent = compactHelp
local helpGeneration = 0
compactHelp.MouseButton1Click:Connect(function()
    helpGeneration += 1
    local generation = helpGeneration
    instructions.Visible = not instructions.Visible
    if instructions.Visible then
        task.delay(5, function()
            if helpGeneration == generation then instructions.Visible = false end
        end)
    end
end)
-- P0D_UX_HUD_COMPACT_V1_END
'''

def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def inventory(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist: Path, enabled: bool) -> bool:
    before = inventory(dist)
    if len(before) != 65 or HUD not in before or "server/Game.server.luau" not in before:
        raise ValueError("REQUIRE_EXACT_FINAL_OFFICIAL65_SOURCE")
    locks = [dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"]
    slock, flock = [json.loads(p.read_text("utf8")) for p in locks]
    pin = {p: gitblob(raw) for p, raw in before.items()}
    if slock.get("total_scripts") != 65 or slock.get("blobs") != pin:
        raise ValueError("SOURCE_LOCK_DRIFT")
    if flock.get("total_sources") != 65 or flock.get("source_gitblobs") != pin:
        raise ValueError("FEATURE_LOCK_DRIFT")
    if not enabled:
        print("P0D_COMPACT_HUD_OFF_BYTE_IDENTICAL_65_PASS")
        return False
    source = before[HUD].decode("utf8")
    for required in (
        'gui.Name = "TrapRaidersS1HUD"',
        'local instructions = label(', 'local top = label(',
        'local status = label(', 'local function layoutRelayTouch()',
        'relayButton.MouseButton1Click:Connect(fireClassicEggRelay)',
        'remote.OnClientEvent:Connect(function(s)',
    ):
        if source.count(required) != 1:
            raise ValueError("MISSING_OR_DUPLICATE_REQUIRED_HUD_ANCHOR:" + required)
    if START in source or END in source:
        raise ValueError("DUPLICATE_COMPACT_HUD_PATCH")
    # Exclude any whole-author modifications. Single prepared source body changes.
    after = dict(before)
    after[HUD] = (source.rstrip("\n") + "\n" + PATCH.lstrip("\n")).encode("utf8")
    assert len(after) == len(before)
    assert all(before[p] == after[p] for p in before if p != HUD)
    assert after["server/Game.server.luau"] == before["server/Game.server.luau"]
    post_pin = {p: gitblob(raw) for p, raw in after.items()}
    slock["blobs"] = post_pin
    slock["prep_compact_hud"] = {
        "feature": FEATURE, "original_hud_blob": pin[HUD],
        "modified_hud_blob": post_pin[HUD],
        "other_64_scripts_identical": True,
        "rollback": "Disable overlay; rebuild exact original 65 scripts",
        "studio_2client_android_fun": "NOT_TESTED",
        "official_rc_adopted": False,
    }
    flock["source_gitblobs"] = post_pin
    flock["prep_compact_hud"] = {
        "feature": FEATURE, "candidate_only": True,
        "changes": [HUD], "single_game_remote_store": True,
    }
    (dist / "src" / HUD).write_bytes(after[HUD])
    for path, data in zip(locks, (slock, flock)):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf8")
    if inventory(dist) != after:
        raise ValueError("FINAL_SOURCE_READBACK_MISMATCH")
    print("P0D_COMPACT_HUD_ON_OFFICIAL65_TO_PRIVATE65_ONLY_HUD_PATCH_PASS")
    return True

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", type=Path, required=True)
    p.add_argument("--enabled", choices=["on", "off"], required=True)
    a = p.parse_args()
    apply(a.dist, a.enabled == "on")
