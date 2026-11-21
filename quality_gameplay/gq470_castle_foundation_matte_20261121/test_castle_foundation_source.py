"""GQ470 castle-foundation source gate. Static/source-only, NOT Studio or ART approval."""
from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name("EGGRUMBLE_CastleFoundationMatte.client.luau")


def validate(source: str):
    required = [
        "local MAX_CASTLES = if UserInputService.TouchEnabled then 2 else 3",
        "local PARTS_PER_CASTLE = 8",
        "local MAX_TOTAL_EXTRA_PARTS = MAX_CASTLES * PARTS_PER_CASTLE",
        "local MAX_DISTANCE_STUDS = 190",
        "local REFRESH_INTERVAL = 2.5",
        'obj.Name ~= "StandardCore"',
        'ancestor.Name == "TacticalBattlefield"',
        'Instance.new("WedgePart")',
        "for side = 1, 4 do",
        "assert(#stones == PARTS_PER_CASTLE)",
        "if dist <= MAX_DISTANCE_STUDS then",
        'if obj:IsA("BasePart") and obj.Name == "StandardCore" then',
        'Enum.Material.Slate', 'Enum.Material.SmoothPlastic',
        "stone.Anchored = true",
        "stone.CanCollide = false",
        "stone.CanTouch = false",
        "stone.CanQuery = false",
        "stone.CastShadow = false",
        'player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
        "decoration.parts[first].CFrame = outward",
        "if not wanted[core] or not validCore(core) then clear(core) end",
        "Workspace.DescendantAdded:Connect",
        "Workspace.DescendantRemoving:Connect",
        "while script.Parent do",
        "task.wait(REFRESH_INTERVAL)",
        "assert(count * PARTS_PER_CASTLE <= MAX_TOTAL_EXTRA_PARTS)",
        "local FEATURE_ID = \"GQ470_FB015_CASTLE_FOUNDATION_MATTE_20261121\"",
    ]
    for text in required:
        if text.startswith("local "):
            matches = re.findall(r"(?m)^" + re.escape(text) + r"\s*$", source)
            count = len(matches)
        else:
            count = source.count(text)
        expected = 2 if text == 'if obj:IsA("BasePart") and obj.Name == "StandardCore" then' else 1
        if count != expected:
            raise ValueError("RED_FOUNDATION_REQUIRED_" + text)
    for declaration in ("MAX_CASTLES", "PARTS_PER_CASTLE", "MAX_TOTAL_EXTRA_PARTS",
                        "MAX_DISTANCE_STUDS", "REFRESH_INTERVAL"):
        if not re.search(r"(?m)^local " + declaration + r" = .+$", source):
            raise ValueError("RED_FOUNDATION_BAD_BUDGET_DECLARATION")
    stripped = "\n".join(x.split("--", 1)[0] for x in source.splitlines())
    forbidden = ("RemoteEvent", "RemoteFunction", "FireServer", "InvokeServer",
                 "DataStore", "TakeDamage", "Humanoid.Health =", "BillboardGui",
                 "ScreenGui", "Highlight", "Enum.Material.Neon", "RenderStepped",
                 "Heartbeat", "Stepped", "LoadCharacter", "SpawnLocation",
                 "workspace.Gravity", "SetAttribute(\"Team\"", "TweenService")
    for marker in forbidden:
        if marker in stripped:
            raise ValueError("RED_FOUNDATION_FORBIDDEN_" + marker)
    if stripped.count('Instance.new("WedgePart")') != 1:
        raise ValueError("RED_FOUNDATION_UNBOUNDED_PART_CREATORS")
    if stripped.count("table.insert(stones, makeStone(") != 2:
        raise ValueError("RED_FOUNDATION_STONE_SLOT_OVERFLOW")
    if stripped.count('if obj:IsA("BasePart") and obj.Name == "StandardCore" then') != 2:
        raise ValueError("RED_FOUNDATION_UNSTABLE_LATE_STREAMING_DISCOVERY")
    if not (len(source.encode("utf-8")) < 11000):
        raise ValueError("RED_FOUNDATION_SOURCE_TOO_LARGE")
    if not re.search(r"for i = 1, math.min\(MAX_CASTLES, #ranked\) do", source):
        raise ValueError("RED_FOUNDATION_LOD_UNBOUNDED")


class FoundationTests(unittest.TestCase):
    def test_contract(self):
        validate(SRC.read_text(encoding="utf-8"))

    def test_negative_mutations(self):
        s = SRC.read_text(encoding="utf-8")
        mutations = [
            ("then 2 else 3", "then 200 else 300"),
            ("PARTS_PER_CASTLE = 8", "PARTS_PER_CASTLE = 80"),
            ("for side = 1, 4 do", "for side = 1, 40 do"),
            ("assert(#stones == PARTS_PER_CASTLE)", "assert(true)"),
            ("if dist <= MAX_DISTANCE_STUDS then", "if true then"),
            ("MAX_DISTANCE_STUDS = 190", "MAX_DISTANCE_STUDS = 19000"),
            ("REFRESH_INTERVAL = 2.5", "REFRESH_INTERVAL = 0.01"),
            ('obj.Name ~= "StandardCore"', 'obj.Name ~= "NoSuchCore"'),
            ('ancestor.Name == "TacticalBattlefield"', 'ancestor.Name == "OtherWorld"'),
            ("stone.CanCollide = false", "stone.CanCollide = true"),
            ("stone.CanTouch = false", "stone.CanTouch = true"),
            ("stone.CanQuery = false", "stone.CanQuery = true"),
            ("stone.CastShadow = false", "stone.CastShadow = true"),
            ("Enum.Material.Slate", "Enum.Material.Neon"),
            ("Instance.new(\"WedgePart\")", "Instance.new(\"Part\")"),
            ("GetAttribute(\"EGGRUMBLE_ReducedEffects\") ~= true",
             "GetAttribute(\"EGGRUMBLE_ReducedEffects\") == true"),
            ("if not wanted[core] or not validCore(core) then clear(core) end",
             "if false then clear(core) end"),
            ("task.wait(REFRESH_INTERVAL)", "task.wait(0.01)"),
            ("assert(count * PARTS_PER_CASTLE <= MAX_TOTAL_EXTRA_PARTS)",
             "assert(true)"),
        ]
        for old, new in mutations:
            self.assertIn(old, s)
            with self.subTest(mutant=old), self.assertRaises(ValueError):
                validate(s.replace(old, new, 1))
        for injection in ("FireServer(", 'Instance.new("BillboardGui")',
                          'Enum.Material.Neon', "RenderStepped:Connect",
                          "Humanoid.Health = 0"):
            with self.subTest(injection=injection), self.assertRaises(ValueError):
                validate(s + "\n" + injection)


if __name__ == "__main__":
    unittest.main()
