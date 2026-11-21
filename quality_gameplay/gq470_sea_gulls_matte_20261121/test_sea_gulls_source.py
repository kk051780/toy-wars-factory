"""GQ470 FB-015: fail-closed static tests of the actual coastal bird Luau.

Static tests are NOT Roblox Studio rendering or device performance evidence.
"""
import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).parent / "EGGRUMBLE_SeaGullsMatte.client.luau").read_text(encoding="utf-8")

def gate(s: str) -> None:
    required = (
        'FEATURE_ID = "GQ470_FB015_SEA_GULLS_MATTE_20261121"',
        'return obj:IsA("BasePart") and obj.Name == "PublicSeaDock" and', "obj.Anchored",
        'parent:IsA("Folder")',
        'parent.Name == "EGGRUMBLE_LAND_SEA_SKY_20261117"',
        'obj:IsDescendantOf(Workspace)', 'localPlayer.Character',
        'humanoid.Health > 0', 'HumanoidRootPart',
        'localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") == true',
        'BIRD_LIMIT = if UserInputService.TouchEnabled then 2 else 3',
        'PARTS_PER_BIRD = 3',
        'TOTAL_PART_BUDGET = BIRD_LIMIT * PARTS_PER_BIRD',
        'assert(created <= TOTAL_PART_BUDGET',
        'part.Anchored = true', 'part.CanCollide = false',
        'part.CanTouch = false', 'part.CanQuery = false',
        'part.CastShadow = false', 'Enum.Material.SmoothPlastic',
        'Instance.new("WedgePart")', 'TweenService:Create(part, style',
        'tween:Cancel()', 'localFolder:Destroy()',
        'Workspace.DescendantAdded:Connect',
        'Workspace.DescendantRemoving:Connect',
        'localPlayer.CharacterRemoving:Connect(clear)',
        'GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects")',
        'task.wait(UPDATE_SECONDS)',
    )
    for mark in required:
        if mark not in s:
            raise AssertionError("RED_SEA_GULLS_MISSING_" + mark)
    forbidden = (
        "RemoteEvent", "RemoteFunction", ":FireServer(", ":InvokeServer(",
        "DataStore", "SetAsync(", "UpdateAsync(", "RunService.RenderStepped",
        "RunService.Heartbeat", "BillboardGui", "ScreenGui", "Highlight",
        "Enum.Material.Neon", "Instance.new(\"PointLight\")",
        "TakeDamage(", ".Health =", "CameraSubject =", "CameraType =",
        ":LoadCharacter(", "LoadCharacterAsync(", "Players.PlayerAdded",
        "ServerScriptService", "TweenService:Create(root",
    )
    for mark in forbidden:
        if mark in s:
            raise AssertionError("RED_SEA_GULLS_FORBIDDEN_" + mark)
    if not re.search(r"(?m)^local PARTS_PER_BIRD = 3$", s):
        raise AssertionError("RED_SEA_GULLS_EXACT_PARTS_PER_BIRD_LIMIT")
    if s.count("tween:Cancel()") != 2:
        raise AssertionError("RED_SEA_GULLS_BOTH_TWEEN_CLEANUP_POINTS")
    if s.count("newPiece(folder,") != 3:
        raise AssertionError("RED_SEA_GULLS_NOT_THREE_PARTS")
    if len(re.findall(r"while\s+script\.Parent", s)) != 1:
        raise AssertionError("RED_SEA_GULLS_UNBOUNDED_TICK")
    if "if dock == nil then clear(); return end" not in s:
        raise AssertionError("RED_SEA_GULLS_NEEDS_RANGE_CLEANUP")

class SeagullSourceTests(unittest.TestCase):
    def test_source_passes(self):
        gate(SOURCE)

    def test_official_is_not_rewritten(self):
        self.assertNotIn("git push", SOURCE)
        self.assertNotIn("rc/p0d-s1-kids-rc01", SOURCE)
        self.assertNotIn("game:GetService(\"ReplicatedStorage\")", SOURCE)

    def test_negative_mutations(self):
        mutants = [
            SOURCE.replace('obj.Name == "PublicSeaDock"', 'obj.Name == "AnyPart"', 1),
            SOURCE.replace("obj.Anchored", "true", 1),
            SOURCE.replace('humanoid.Health > 0', "true", 1),
            SOURCE.replace('then 2 else 3', 'then 25 else 30', 1),
            SOURCE.replace("PARTS_PER_BIRD = 3", "PARTS_PER_BIRD = 30", 1),
            SOURCE.replace("CanCollide = false", "CanCollide = true", 1),
            SOURCE.replace("CanQuery = false", "CanQuery = true", 1),
            SOURCE.replace("CastShadow = false", "CastShadow = true", 1),
            SOURCE.replace("Enum.Material.SmoothPlastic", "Enum.Material.Neon", 1),
            SOURCE.replace("TweenService:Create(part, style", "TweenService:Create(root, style", 1),
            SOURCE.replace("tween:Cancel()", "tween:Play()", 1),
            SOURCE.replace("localFolder:Destroy()", "print(localFolder)", 1),
            SOURCE.replace('task.wait(UPDATE_SECONDS)', 'task.wait(0)', 1),
            SOURCE + '\nlocal ev = Instance.new("RemoteEvent")\n',
            SOURCE + '\nRunService.RenderStepped:Connect(function() end)\n',
            SOURCE.replace('if dock == nil then clear(); return end', 'if dock == nil then return end', 1),
            SOURCE.replace('obj:IsDescendantOf(Workspace)', 'true', 1),
            SOURCE.replace('parent.Name == "EGGRUMBLE_LAND_SEA_SKY_20261117"',
                           'parent.Name == "UnrelatedWorld"', 1),
            SOURCE.replace('parent:IsA("Folder")', 'true', 1),
            SOURCE.replace('GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects")',
                           'GetAttributeChangedSignal("CosmeticValue")', 1),
        ]
        self.assertEqual(len(mutants), 20)
        for i, variant in enumerate(mutants):
            with self.subTest(mutation=i):
                with self.assertRaises(AssertionError):
                    gate(variant)

if __name__ == "__main__":
    unittest.main()
