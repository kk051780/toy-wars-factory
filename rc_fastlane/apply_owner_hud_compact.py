#!/usr/bin/env python3
"""OWNER #340 isolated compact HUD overlay on the *final* RC65 source.

No Game, Remote, Store, score, HP, egg, XP, saved state or other Luau changes.
--enabled off is genuinely byte-identical, including all locks/project files.
Not evidence of Studio/Android testing. Only #220 may adopt into official RC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FEATURE = "P0D_OWNER_COMPACT_HUD_V1"
HUD = "client/HUD.client.luau"
PARENT_COUNT = 65
START = "-- OWNER_COMPACT_HUD_BEGIN"
END = "-- OWNER_COMPACT_HUD_END"

HUD_INSERT = """-- OWNER_COMPACT_HUD_BEGIN
-- The full instructions remain accessible, but are not permanently laid over
-- the camera / thumbstick. Avoid intercepting movement or combat touches.
top.Size = UDim2.new(.70, 0, 0, 46)
top.Position = UDim2.new(.15, 0, 0, 4)
top.BackgroundTransparency = .36
top.TextSize = 14
status.Size = UDim2.new(.66, 0, 0, 30)
status.Position = UDim2.new(.17, 0, 0, 52)
status.BackgroundTransparency = .36
status.TextSize = 13
status.TextWrapped = false
status.TextTruncate = Enum.TextTruncate.AtEnd
instructions.Size = UDim2.new(.68, 0, 0, 54)
instructions.Position = UDim2.new(.16, 0, 0, 87)
instructions.Visible = false
local compactHelp = Instance.new("TextButton")
compactHelp.Name = "CompactHUDHelp"
compactHelp.AnchorPoint = Vector2.new(1, 0)
compactHelp.Position = UDim2.new(1, -8, 0, 8)
compactHelp.Size = UDim2.fromOffset(30, 30)
compactHelp.Text = "?"
compactHelp.TextSize = 20
compactHelp.Font = Enum.Font.GothamBold
compactHelp.TextColor3 = Color3.new(1, 1, 1)
compactHelp.BackgroundColor3 = Color3.fromRGB(31, 49, 68)
compactHelp.BackgroundTransparency = .18
compactHelp.BorderSizePixel = 0
compactHelp.Parent = gui
compactHelp.MouseButton1Click:Connect(function()
    instructions.Visible = not instructions.Visible
end)
-- OWNER_COMPACT_HUD_END"""

SNAPSHOT_INSERT = """if s.kind ~= "SNAPSHOT" then return end
    -- Compact help is for onboarding only, never overlays combat.
    compactHelp.Visible = s.phase ~= "ACTIVE"
    if s.phase == "ACTIVE" then instructions.Visible = false end"""


def gitblob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def inventory(dist: Path) -> dict[str, bytes]:
    return {p.relative_to(dist / "src").as_posix(): p.read_bytes()
            for p in sorted((dist / "src").rglob("*.luau"))}


def transform(source: str) -> str:
    assert START not in source and END not in source, "ALREADY_APPLIED"
    assert source.count('local top = label(gui, "Score"') == 1, "SCORE_ANCHOR_DRIFT"
    assert source.count('local status = label(gui, "Status"') == 1, "STATUS_ANCHOR_DRIFT"
    assert source.count('local instructions = label(gui, "Instructions"') == 1, "HELP_ANCHOR_DRIFT"
    assert source.count('if s.kind ~= "SNAPSHOT" then return end') == 1, "SNAPSHOT_ANCHOR_DRIFT"
    # This line is authored once and followed by other HUD widget definitions.
    anchor = re.compile(r"(?m)^instructions\.Text\s*=\s*[^\n]+$")
    matches = list(anchor.finditer(source))
    assert len(matches) == 1, ("INSTRUCTIONS_TEXT_DRIFT", len(matches))
    m = matches[0]
    result = source[:m.end()] + "\n" + HUD_INSERT + source[m.end():]
    result = result.replace('if s.kind ~= "SNAPSHOT" then return end',
                            SNAPSHOT_INSERT, 1)
    assert result.count(START) == 1 and result.count(END) == 1
    assert result.count("compactHelp.MouseButton1Click:Connect(") == 1
    assert result.count('remote.OnServerEvent:Connect(') == source.count('remote.OnServerEvent:Connect(')
    assert result.count('remote:FireServer(') == source.count('remote:FireServer(')
    return result


def run(dist: Path, enabled: bool) -> bool:
    before = inventory(dist)
    assert len(before) == PARENT_COUNT, ("NEED_FINAL_OFFICIAL_65_SOURCES", len(before))
    assert HUD in before and "server/Game.server.luau" in before
    lockpath = dist / "SOURCE_LOCK.json"
    featurepath = dist / "RC_FEATURE_LOCK.json"
    projectpath = dist / "default.project.json"
    lock = json.loads(lockpath.read_text("utf8"))
    feature = json.loads(featurepath.read_text("utf8"))
    pins = {k: gitblob(v) for k, v in sorted(before.items())}
    assert lock["total_scripts"] == 65 and lock["blobs"] == pins, "RC65_LOCK_DRIFT"
    assert feature["total_sources"] == 65 and feature["source_gitblobs"] == pins, "RC65_FEATURE_LOCK_DRIFT"
    game = before["server/Game.server.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(') == 1, "REMOTE_AUTHORITY_DRIFT"
    assert game.count('remote.Name = "TrapRaidersS1Remote"') == 1
    assert FEATURE not in lock and FEATURE not in feature.get("feature_flags", {})
    assert projectpath.exists()
    if not enabled:
        print("P0D_OWNER_HUD_OFF_PREVIOUS_65_AND_ALL_PROJECT_FILES_UNCHANGED_PASS")
        return False

    updated = transform(before[HUD].decode("utf8")).encode("utf8")
    after = dict(before)
    after[HUD] = updated
    newpins = {k: gitblob(v) for k, v in sorted(after.items())}
    assert set(after) == set(before) and len(after) == 65
    assert all(after[k] == before[k] for k in before if k != HUD)
    assert after["server/Game.server.luau"] == before["server/Game.server.luau"]
    assert after["server/PersistentHatchStore.luau"] == before["server/PersistentHatchStore.luau"]

    lock["blobs"] = newpins
    lock[FEATURE] = {
        "changed": [HUD], "source_count": 65, "other64_byte_exact": True,
        "prior_hud_blob": pins[HUD], "modified_hud_blob": newpins[HUD],
        "rollback": "Omit apply_owner_hud_compact.py --enabled on; rebuild exact parent RC65",
        "studio_2client": "NOT_TESTED", "android": "NOT_TESTED", "owner_fun": "NOT_TESTED",
        "official_rc_adopted": False,
    }
    feature["source_gitblobs"] = newpins
    feature.setdefault("feature_flags", {})[FEATURE] = True
    # No writes above this line. Do not rewrite the project definition.
    (dist / "src" / HUD).write_bytes(updated)
    lockpath.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", "utf8")
    featurepath.write_text(json.dumps(feature, ensure_ascii=False, indent=2) + "\n", "utf8")
    assert inventory(dist) == after
    assert json.loads(lockpath.read_text("utf8"))["blobs"] == newpins
    print("P0D_OWNER_COMPACT_HUD_65_SOURCES_ONLY_ONE_HUD_CHANGED_SOURCE_LOCK_PASS")
    return True


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dist", type=Path, required=True)
    cli.add_argument("--enabled", choices=("on", "off"), required=True)
    args = cli.parse_args()
    run(args.dist, args.enabled == "on")
