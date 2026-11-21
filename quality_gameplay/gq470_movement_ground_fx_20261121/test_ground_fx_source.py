"""Static fail-closed ART source gate for ground motion A-candidate.

PASS is not Roblox runtime performance, a visual score or formal RC adoption.
"""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parent / "EGGRUMBLE_GroundMotionFX.client.luau"


def validate(source: str) -> None:
    code = "\n".join(line.split("--", 1)[0] for line in source.splitlines())
    markers = [
        "GQ470_FB015_GROUND_MOTION_MATTE_20261121",
        "local MAX_LIVE_PARTS = 6",
        "local MAX_PARTS_PER_STEP = 2",
        "local MOBILE_PARTS_PER_STEP = 1",
        "local STEP_SECONDS = 0.32",
        "local CAMERA_FX_DISTANCE = 78",
        "(camera.CFrame.Position - root.Position).Magnitude > CAMERA_FX_DISTANCE",
        "local LIFE_SECONDS = 0.38",
        "local TOUCH = UserInputService.TouchEnabled",
        "Workspace:Raycast",
        "hit.Normal.Y < 0.70",
        "humanoid.FloorMaterial ~= Enum.Material.Air",
        "swimmingConnection = humanoid.Swimming:Connect",
        "humanoid:GetState() == Enum.HumanoidStateType.Swimming",
        "waterSpeed >= 6",
        "rayParams.IgnoreWater = false",
        "rayParams.RespectCanCollide = not waterOnly",
        "hit.Material ~= Enum.Material.Water",
        "not waterOnly and hit.Material == Enum.Material.Water",
        "math.min(",
        "MAX_LIVE_PARTS - liveParts",
        "Instance.new(\"WedgePart\")",
        "part.Material = Enum.Material.SmoothPlastic",
        "part.Transparency = 0.42",
        "part.Anchored = true",
        "part.CanCollide = false",
        "part.CanTouch = false",
        "part.CanQuery = false",
        "part.CastShadow = false",
        "part.Parent = folder",
        "Debris:AddItem(part, LIFE_SECONDS + 0.08)",
        "task.delay(LIFE_SECONDS + 0.10",
        "task.delay(STEP_SECONDS, pulse)",
        "PLAYER.CharacterRemoving:Connect",
        "PLAYER.CharacterAdded:Connect",
        "humanoid.Died:Connect",
        "generation ~= token",
        "generation += 1",
    ]
    for marker in markers:
        if marker not in code:
            raise ValueError("RED_GROUND_FX_MISSING:" + marker)
    numeric_contract = {
        "MAX_LIVE_PARTS": "6",
        "MAX_PARTS_PER_STEP": "2",
        "MOBILE_PARTS_PER_STEP": "1",
        "STEP_SECONDS": "0.32",
        "LIFE_SECONDS": "0.38",
        "CAMERA_FX_DISTANCE": "78",
    }
    for name, value in numeric_contract.items():
        if not re.search(r"(?m)^\s*local " + name + r"\s*=\s*" +
                         re.escape(value) + r"\s*$", code):
            raise ValueError("RED_GROUND_FX_NUMERIC_BUDGET:" + name)
    forbidden = (
        "RemoteEvent", "RemoteFunction", "FireServer", "InvokeServer",
        "TakeDamage", "DataStore", "MarketplaceService", "ReplicatedStorage",
        "RenderStepped", "Heartbeat", "while true", "while task.wait",
        "Enum.Material.Neon", "PointLight", "ParticleEmitter",
        "AssemblyLinearVelocity", "SetNetworkOwner", "part.CanCollide = true",
    )
    for word in forbidden:
        if word in code:
            raise ValueError("RED_GROUND_FX_FORBIDDEN:" + word)
    if re.search(r"RunService\s*:", code):
        raise ValueError("RED_GROUND_FX_PER_FRAME")
    if len(code.encode()) > 10500:
        raise ValueError("RED_GROUND_FX_UNBOUNDED_CODE")
    if source.count('Instance.new("WedgePart")') != 1:
        raise ValueError("RED_GROUND_FX_MULTIPLE_FACTORY_SITES")
    if code.count("if swimmingConnection then swimmingConnection:Disconnect() end") != 3:
        raise ValueError("RED_GROUND_FX_SWIM_RESPAWN_CONNECTION_LEAK")


class GroundMotionSourceGate(unittest.TestCase):
    def test_source_safety_contract(self):
        validate(SOURCE.read_text(encoding="utf-8"))

    def test_negative_mutations_are_rejected(self):
        original = SOURCE.read_text(encoding="utf-8")
        changes = [
            ("local MAX_LIVE_PARTS = 6", "local MAX_LIVE_PARTS = 600"),
            ("local MOBILE_PARTS_PER_STEP = 1", "local MOBILE_PARTS_PER_STEP = 9"),
            ("local STEP_SECONDS = 0.32", "local STEP_SECONDS = 0"),
            ("local CAMERA_FX_DISTANCE = 78", "local CAMERA_FX_DISTANCE = 1000"),
            ("(camera.CFrame.Position - root.Position).Magnitude > CAMERA_FX_DISTANCE",
             "(camera.CFrame.Position - root.Position).Magnitude > 99999"),
            ("part.CanCollide = false", "part.CanCollide = true"),
            ("part.CanQuery = false", "part.CanQuery = true"),
            ("part.CastShadow = false", "part.CastShadow = true"),
            ("part.Material = Enum.Material.SmoothPlastic",
             "part.Material = Enum.Material.Neon"),
            ('Instance.new("WedgePart")', 'Instance.new("Part")'),
            ("humanoid.FloorMaterial ~= Enum.Material.Air", "true"),
            ("hit.Normal.Y < 0.70", "hit.Normal.Y < -1.0"),
            ("rayParams.IgnoreWater = false", "rayParams.IgnoreWater = true"),
            ("rayParams.RespectCanCollide = not waterOnly",
             "rayParams.RespectCanCollide = true"),
            ("swimmingConnection = humanoid.Swimming:Connect",
             "swimmingConnection = humanoid.Running:Connect"),
            ("waterSpeed >= 6", "waterSpeed >= 0"),
            ("hit.Material ~= Enum.Material.Water",
             "hit.Material == Enum.Material.Water"),
            ("if swimmingConnection then swimmingConnection:Disconnect() end",
             "if swimmingConnection then swimmingConnection = nil end"),
            ("task.delay(STEP_SECONDS, pulse)", "pulse()"),
            ("generation ~= token", "false"),
        ]
        for before, after in changes:
            self.assertIn(before, original)
            with self.subTest(change=after), self.assertRaises(ValueError):
                validate(original.replace(before, after))
        with self.assertRaises(ValueError):
            validate(original + "\nRunService.Heartbeat:Connect(function() end)\n")
        with self.assertRaises(ValueError):
            validate(original + "\nRemoteEvent:FireServer()\n")


if __name__ == "__main__":
    unittest.main()
