#!/usr/bin/env python3
"""Fail-closed source-only negative checks for optional castle banner animation.
No Roblox Studio, Android or visual quality conclusion is made by these tests.
"""
from pathlib import Path
import re
import unittest

SRC = (Path(__file__).parent / "EGGRUMBLE_CastleBannerWind.client.luau")
MARKER = "GQ470_FB015_CASTLE_BANNER_WIND_20261121"

def validate(code: str) -> None:
    expected = [
        r"MAX_BANNERS\s*=\s*20",
        r"RANGE_STUDS\s*=\s*110",
        r"MAX_SWAY_RADIANS\s*=\s*math.rad\(3\.5\)",
        r"if UserInputService.TouchEnabled then 0.32 else 0.18",
        r"not part.Anchored or part.CanCollide",
        r"part.Material == Enum.Material.Neon",
        r'ancestor:FindFirstChild\("StandardCore", true\)',
        r"for _ = 1, 3 do",
        r"Workspace.DescendantRemoving:Connect",
        r"Workspace.DescendantAdded:Connect",
        r"RunService.Heartbeat:Connect",
        r"if accumulator < TICK_SECONDS then return end",
        r"reduced or not camPos",
        r"\(part.Position - camPos\).Magnitude > RANGE_STUDS",
        r"local hinge = part.Size.Y \* 0.5",
        r"state.base \* CFrame.new",
        r"trackedCount = math.max\(0, trackedCount - 1\)",
    ]
    assert code.count(MARKER) == 1, "missing/duplicate feature ID"
    for pat in expected:
        assert re.search(pat, code), f"missing guard: {pat}"
    forbidden = [
        "Instance.new", "RemoteEvent", "RemoteFunction", "DataStoreService",
        ":TakeDamage(", ":LoadCharacter(", "CameraSubject =", "CharacterAutoLoads",
        "PlayerGui", "SetAttribute(", "MarketplaceService", "TweenService",
    ]
    for marker in forbidden:
        assert marker not in code, f"forbidden authority, HUD or spawn API: {marker}"
    assert code.count("Workspace:GetDescendants()") == 1, "map scan must be one-shot"
    assert code.count("part.CFrame =") == 2, "animation and one rollback only"

class Gate(unittest.TestCase):
    def test_actual_candidate(self):
        self.assertGreater(len(SRC.read_bytes()), 3500)
        validate(SRC.read_text(encoding="utf-8"))
    def test_mutants_rejected(self):
        original = SRC.read_text(encoding="utf-8")
        cases = [
            ("MAX_BANNERS = 20", "MAX_BANNERS = 2000"),
            ("RANGE_STUDS = 110", "RANGE_STUDS = 5000"),
            ("math.rad(3.5)", "math.rad(70)"),
            ("then 0.32 else 0.18", "then 0.01 else 0.01"),
            ("not part.Anchored or part.CanCollide", "not part.Anchored"),
            ('ancestor:FindFirstChild("StandardCore", true)', 'ancestor:FindFirstChild("Fake", true)'),
            ("Workspace.DescendantRemoving:Connect", "Workspace.NeverRemove:Connect"),
            ("if accumulator < TICK_SECONDS then return end", "if false then return end"),
            ("trackedCount = math.max(0, trackedCount - 1)", "trackedCount = trackedCount + 1"),
            ("local hinge = part.Size.Y * 0.5", "local hinge = 100"),
        ]
        for old, new in cases:
            self.assertIn(old, original)
            with self.subTest(old=old), self.assertRaises(AssertionError):
                validate(original.replace(old, new, 1))
    def test_forbidden_gameplay_mutants(self):
        original = SRC.read_text(encoding="utf-8")
        for bad in ("Instance.new", "RemoteEvent", "DataStoreService", "CharacterAutoLoads",
                    "CameraSubject =", ":TakeDamage(", "PlayerGui"):
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                validate(original + "\n-- " + bad)
if __name__ == "__main__":
    unittest.main()
