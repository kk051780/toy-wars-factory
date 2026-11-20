#!/usr/bin/env python3
"""Fail-closed static/source policy gate for the FB015 REAL69 art-only A candidate.

This cannot demonstrate Roblox Studio, Android FPS, or visual acceptance.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("EGGRUMBLE_LowCostSceneGrade.luau")
MARKER = "GQ470_FB015_LOW_COST_SCENE_GRADE_REAL69_20261121"
MOODS = ("CLEAR", "GOLDEN", "OVERCAST", "STORM")
LIMITS = {
    "contrast": (-0.02, 0.12),
    "saturation": (-0.12, 0.12),
    "brightness": (-0.035, 0.035),
    "density": (0.10, 0.34),
    "haze": (0.20, 1.40),
    "glare": (0.0, 0.12),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("RED_FB015_GRADE_" + message)


def verify(source: str) -> dict[str, int]:
    require(source.count(MARKER) == 1, "MARKER")
    require(source.startswith("--!strict"), "STRICT")
    require('if not RunService:IsStudio() then' in source, "STUDIO_FENCE")
    require('return nil, "STUDIO_ONLY"' in source, "STUDIO_REJECTION")
    require(source.count('game:GetService("RunService")') == 1, "SERVICE_SCOPE")
    require(len(re.findall(r'game:GetService\(', source)) == 1, "EXTRA_SERVICES")
    classes = re.findall(r'Instance\.new\("([^"]+)"\)', source)
    require(sorted(classes) == ["Atmosphere", "ColorCorrectionEffect"], "INSTANCE_BUDGET")
    require('lighting:FindFirstChild(GRADE_NAME)' in source, "DUPLICATE_FENCE")
    require('return nil, "ALREADY_INSTALLED"' in source, "DUPLICATE_REJECTION")
    require(source.count("if ownsAtmosphere and atmosphere ~= nil then") == 2,
            "OTHER_LANE_ATMOSPHERE")
    require("grade:Destroy()" in source and "atmosphere:Destroy()" in source,
            "REVERSIBLE_DESTROY")
    require('setMood("CLEAR")' in source, "DEFAULT")
    require('return false, "UNKNOWN_MOOD"' in source, "MOOD_WHITELIST")
    require('return false, "DISPOSED"' in source, "DEAD_CONTROLLER")
    banned = (
        "Heartbeat", "RenderStepped", "Stepped:Connect", "while true",
        "task.spawn", "task.delay", "TweenService", "ReplicatedStorage",
        "RemoteEvent", "RemoteFunction", "DataStore", "MarketplaceService",
        "ProximityPrompt", "ClickDetector", "Humanoid", "TakeDamage",
        "GetPlayers(", "Lighting.ClockTime", "Lighting.Brightness",
        "Terrain:", "workspace:", "CanCollide",
    )
    for token in banned:
        require(token not in source, "FORBIDDEN_" + re.sub(r"\W+", "_", token))

    found = {}
    matches = list(re.finditer(
        r'(?ms)^    ([A-Z]+) = \{\n(.*?)^    \},?$', source
    ))
    require(len(matches) == 4, "MOOD_COUNT")
    for match in matches:
        name, body = match.group(1), match.group(2)
        require(name in MOODS and name not in found, "MOOD_UNIQUE")
        numbers = {
            key: float(value)
            for key, value in re.findall(
                r'\b([a-z]+) = (-?\d+(?:\.\d+)?)', body
            )
        }
        require(set(numbers) == set(LIMITS), "PARAMETER_SET_" + name)
        for key, value in numbers.items():
            low, high = LIMITS[key]
            require(low <= value <= high, "RANGE_" + name + "_" + key)
        colors = re.findall(
            r'Color3\.fromRGB\((\d+), (\d+), (\d+)\)', body
        )
        require(len(colors) == 3, "COLOR_COUNT_" + name)
        require(all(0 <= int(channel) <= 255 for color in colors
                    for channel in color), "RGB_RANGE_" + name)
        found[name] = True
    require(set(found) == set(MOODS), "MOOD_MISSING")
    return {"moods": len(found), "created_instances": len(classes),
            "parts": 0, "per_frame_loops": 0}


class GradeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_full_source_policy(self) -> None:
        self.assertEqual(verify(self.source), {
            "moods": 4, "created_instances": 2,
            "parts": 0, "per_frame_loops": 0
        })

    def test_reject_adversarial_source_mutations(self) -> None:
        edits = {
            "studio_fence": (
                'if not RunService:IsStudio() then', 'if false then'),
            "part_growth": (
                'local grade = Instance.new("ColorCorrectionEffect")',
                'local unexpected = Instance.new("Part")\n'
                '    local grade = Instance.new("ColorCorrectionEffect")'),
            "android_overcontrast": (
                'contrast = 0.09', 'contrast = 0.40'),
            "android_oversaturation": (
                'saturation = 0.08', 'saturation = 0.40'),
            "missing_destroy": (
                'grade:Destroy()', '-- REMOVED_DESTROY'),
            "atmosphere_takeover": (
                'if ownsAtmosphere and atmosphere ~= nil then',
                'if atmosphere ~= nil then'),
            "continuous_render_loop": (
                'local active = true',
                'local _tick = RunService.Heartbeat:Connect(function() end)\n'
                '    local active = true'),
            "unknown_mood": (
                '    STORM = {', '    HAZARD = {'),
            "remote_authority": (
                'local SceneGrade = {}',
                'local SceneGrade = {}\nlocal leak = RemoteEvent'),
        }
        for label, (old, new) in edits.items():
            with self.subTest(label=label):
                self.assertIn(old, self.source)
                with self.assertRaisesRegex(ValueError, "RED_FB015_GRADE_"):
                    verify(self.source.replace(old, new, 1))


if __name__ == "__main__":
    unittest.main()
