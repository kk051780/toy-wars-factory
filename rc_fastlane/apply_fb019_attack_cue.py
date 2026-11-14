#!/usr/bin/env python3
"""FB-019 P0: source-locked attack INPUT cue on actual RC80 HUD only.

This is an attempted-swing visual, not a server hit receipt. It deliberately
does not claim to fix neutral mob damage or Studio gameplay; do not score
FB-019 OWNER_ACCEPTED until real combat tests pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

TARGET = "client/HUD.client.luau"
FEATURE = "FB019_ATTACK_INPUT_SWING_CUE_V1"
ACTION_START = "local function action(kind: string, role: string?)\n"
ATTACK_CONNECT = 'attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)'
FIRE_SERVER = 'remote:FireServer({action = kind, role = role, seq = seq})'
SWING_START = "-- FB019_ATTACK_INPUT_SWING_CUE_START"
SWING_END = "-- FB019_ATTACK_INPUT_SWING_CUE_END"

# Client-only, transient, in-world attempted-attack cue. No ScreenGui.
# The authoritative Game/Combat code decides whether any target was hit.
SWING = r'''-- FB019_ATTACK_INPUT_SWING_CUE_START
local FB019TweenService = game:GetService("TweenService")
local FB019Debris = game:GetService("Debris")
local fb019LastSwing = -math.huge
local function fb019ShowAttemptedSwing()
    if not attack.Visible then return end
    local char = player.Character
    local root = if char then char:FindFirstChild("HumanoidRootPart") else nil
    local hum = if char then char:FindFirstChildOfClass("Humanoid") else nil
    if not root or not hum or hum.Health <= 0 then return end
    local now = os.clock()
    if now - fb019LastSwing < 0.2 then return end
    fb019LastSwing = now
    local slash = Instance.new("Part")
    slash.Name = "FB019_AttackInput_CosmeticOnly"
    slash.Size = Vector3.new(3.3, 0.16, 0.16)
    slash.Material = Enum.Material.Neon
    slash.Color = Color3.fromRGB(255, 215, 136)
    slash.Transparency = 0.18
    slash.Anchored = true
    slash.CanCollide = false
    slash.CanTouch = false
    slash.CanQuery = false
    slash.CastShadow = false
    local center = root.CFrame * CFrame.new(0, 0, -3)
    slash.CFrame = center * CFrame.Angles(0, 0, math.rad(-32))
    slash.Parent = workspace
    FB019TweenService:Create(slash, TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Transparency = 1,
        CFrame = center * CFrame.Angles(0, 0, math.rad(35))
    }):Play()
    FB019Debris:AddItem(slash, 0.22)
end
-- FB019_ATTACK_INPUT_SWING_CUE_END
'''

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def source_map(root: Path) -> dict[str, bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()), ("UNSAFE_SOURCE_TREE", p)
    src = root / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def patch(raw: bytes) -> bytes:
    text = raw.decode("utf8")
    assert text.count(ACTION_START) == 1, "ACTION_HELPER_DRIFT"
    assert text.count(ATTACK_CONNECT) == 1, "BUTTON_EVENT_DRIFT"
    assert text.count(FIRE_SERVER) == 1, "AUTHORITATIVE_REMOTE_DRIFT"
    assert text.count("local player = Players.LocalPlayer") == 1, "PLAYER_REFERENCE_DRIFT"
    assert SWING_START not in text and SWING_END not in text, "DUPLICATE_SWING"
    assert "    b.Text = text\n" in text, "FB018_BUTTON_LABEL_REGRESSION"
    replacement = SWING + ACTION_START + '    if kind == "ATTACK" then fb019ShowAttemptedSwing() end\n'
    updated = text.replace(ACTION_START, replacement, 1)
    assert updated.count(FIRE_SERVER) == 1 and updated.count(ATTACK_CONNECT) == 1
    assert updated.count('if kind == "ATTACK" then fb019ShowAttemptedSwing() end') == 1
    assert updated.count(SWING_START) == updated.count(SWING_END) == 1
    assert "TakeDamage(" not in SWING and "FireServer(" not in SWING
    assert "RemoteEvent" not in SWING and "ScreenGui" not in SWING
    return updated.encode("utf8")

def apply(base: Path, out: Path, enabled: bool) -> bool:
    if not enabled:
        assert not out.exists(), "OFF_ZERO_WRITE_REQUIRED"
        print("FB019_OFF_ZERO_WRITES_PASS")
        return False
    base = base.resolve()
    out = out.absolute()
    assert out.parent.is_dir() and not out.exists() and not out.is_relative_to(base)
    before = source_map(base)
    assert len(before) == 80 and TARGET in before, "RC80_REQUIRED"
    sl = json.loads((base / "SOURCE_LOCK.json").read_text("utf8"))
    fl = json.loads((base / "RC_FEATURE_LOCK.json").read_text("utf8"))
    pins = {p: blob(raw) for p, raw in sorted(before.items())}
    assert sl["total_scripts"] == fl["total_sources"] == 80
    assert sl["blobs"] == fl["source_gitblobs"] == pins, "SOURCE_LOCK_DRIFT"
    assert fl["feature_flags"]["FB018_ACTION_BUTTON_TEXT_INIT"] is True
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert FEATURE not in fl["feature_flags"], "FEATURE_DUPLICATE"
    after = dict(before)
    after[TARGET] = patch(before[TARGET])
    assert len(after) == 80
    assert {p for p in before if before[p] != after[p]} == {TARGET}
    newpins = {p: blob(raw) for p, raw in sorted(after.items())}
    receipt = {
        "feature": FEATURE, "feedback": "FB-019",
        "status": "SOURCE_WIP_ONLY",
        "scope": "PC+touch attack input shows short attempted swing, never a fake hit",
        "source_count": 80, "changed": [TARGET],
        "old_blob": pins[TARGET], "new_blob": newpins[TARGET],
        "other79_byte_exact": True,
        "new_remote": False, "new_damage_owner": False,
        "game_store_hp_egg_reward_unchanged": True,
        "hit_damage_confirmed": False, "neutral_mob_damage_confirmed": False,
        "studio_retest": "NOT_TESTED", "owner_fun": "FUN_NO_GO",
        "rollback": "omit FB019 overlay; previous official FB018 HUD restored",
        "canonical_rc_adopted": False
    }
    sl["blobs"] = newpins
    sl["fb019_attack_input"] = receipt
    fl["source_gitblobs"] = newpins
    fl["feature_flags"][FEATURE] = True
    fl["fb019_attack_input"] = receipt
    temp = Path(tempfile.mkdtemp(prefix=".fb019_", dir=str(out.parent)))
    staged = temp / "dist"
    try:
        shutil.copytree(base, staged, symlinks=False)
        (staged / "src" / TARGET).write_bytes(after[TARGET])
        (staged / "SOURCE_LOCK.json").write_text(json.dumps(sl, ensure_ascii=False, indent=2) + "\n", "utf8")
        (staged / "RC_FEATURE_LOCK.json").write_text(json.dumps(fl, ensure_ascii=False, indent=2) + "\n", "utf8")
        assert source_map(staged) == after and source_map(base) == before
        os.replace(staged, out)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("FB019_RC80_LOCAL_SWING_OTHER79_BYTE_EXACT_PASS")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args()
    apply(args.base, args.out, args.enabled == "true")
