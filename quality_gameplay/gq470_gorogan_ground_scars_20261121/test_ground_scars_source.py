#!/usr/bin/env python3
"""Fail-closed static/negative checks for client-only Gorogan ground art.

A source check is NOT Roblox execution, screenshot evidence or Android FPS.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "EGGRUMBLE_GoroganGroundScars.client.luau"
MARK = "GQ470_FB015_GOROGAN_GROUND_SCARS_REAL69_20261121"

REQUIRED = (
    "if not RunService:IsStudio() then return end",
    'MODEL_NAME = "Gorogan_ServerRig"',
    "MAX_PARTS = if LOW_TOUCH then 4 else 6",
    "MAX_DISTANCE = if LOW_TOUCH then 100 else 140",
    "UPDATE_SECONDS = 0.40",
    'piece = Instance.new("WedgePart")',
    "piece.Anchored = true",
    "piece.CanCollide = false",
    "piece.CanTouch = false",
    "piece.CanQuery = false",
    "piece.CastShadow = false",
    "piece.Material = Enum.Material.Slate",
    'player:GetAttribute("EGGRUMBLE_ReducedEffects") == true',
    "Workspace:Raycast(",
    "ray.IgnoreWater = true",
    "hit.Normal.Y < 0.82",
    "humanoid.Died:Connect(",
    "model.Destroying:Connect(",
    "script.Destroying:Connect(",
    "addedConnection:Disconnect()",
    "folder:Destroy()",
    "clearParts(entry)",
    "local character = player.Character",
)
FORBIDDEN = (
    "FireServer(", "InvokeServer(", "OnServerEvent", "GetDataStore(",
    "TakeDamage(", "ApplyImpulse(", "PivotTo(", "MoveTo(",
    "UserInputService.InputBegan", "RunService.RenderStepped",
    "Enum.Material.Neon", 'Instance.new("RemoteEvent")',
    'Instance.new("ScreenGui")', 'Instance.new("ParticleEmitter")',
    'Instance.new("PointLight")', "piece.CanCollide = true",
    "piece.CanQuery = true", "piece.Anchored = false",
)


def verify(source: str) -> None:
    assert source.startswith("--!strict\n"), "RED_STRICT_SCRIPT"
    assert source.count(MARK) == 1, "RED_FEATURE_MARKER"
    assert source.count('Instance.new("WedgePart")') == 1, "RED_PART_CONSTRUCTOR"
    assert source.count("task.spawn(function()") == 1, "RED_ONE_THROTTLED_LOOP"
    assert source.count("Workspace:GetDescendants()") == 1, "RED_ONE_BOOT_SCAN"
    for token in REQUIRED:
        assert token in source, "RED_REQUIRED_" + token
    for token in FORBIDDEN:
        assert token not in source, "RED_FORBIDDEN_" + token


def run() -> int:
    base = SOURCE.read_text(encoding="utf-8")
    verify(base)
    mutations = [
        base.replace("then 4 else 6", "then 40 else 60"),
        base.replace("then 100 else 140", "then 1000 else 1400"),
        base.replace("UPDATE_SECONDS = 0.40", "UPDATE_SECONDS = 0"),
        base.replace("piece.CanCollide = false", "piece.CanCollide = true"),
        base.replace("piece.CanQuery = false", "piece.CanQuery = true"),
        base.replace("piece.CastShadow = false", "piece.CastShadow = true"),
        base.replace("Enum.Material.Slate", "Enum.Material.Neon"),
        base.replace("humanoid.Died:Connect(", "humanoid.HealthChanged:Connect("),
        base.replace("model.Destroying:Connect(", "model.ChildAdded:Connect("),
        base.replace("hit.Normal.Y < 0.82", "hit.Normal.Y < 0"),
        base.replace('player:GetAttribute("EGGRUMBLE_ReducedEffects") == true', "false"),
        base + "\nWorkspace:FindFirstChild('Fake'):PivotTo(CFrame.new())\n",
        base.replace("folder:Destroy()", 'Instance.new("RemoteEvent").Parent = Workspace'),
        base.replace("if not RunService:IsStudio() then return end", "-- unrestricted runtime"),
        base.replace("local character = player.Character", "local character = nil"),
        base.replace("clearParts(entry)", "-- leak parts"),
    ]
    for i, altered in enumerate(mutations):
        assert altered != base, f"RED_NO_OP_MUTATION_{i}"
        try:
            verify(altered)
        except AssertionError:
            continue
        raise AssertionError(f"RED_ACCEPTED_MUTATION_{i}")
    print(f"GQ470_GOROGAN_GROUND_SCARS_STATIC_16_MUTANTS_PASS; ENGINE_NOT_TESTED; ART_NO_GO")
    return len(mutations)


if __name__ == "__main__":
    run()
