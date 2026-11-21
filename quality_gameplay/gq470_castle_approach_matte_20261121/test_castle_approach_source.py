"""Source-only negative gate for GQ470 castle-approach ART; never an engine pass."""
import re
import unittest
from pathlib import Path

SRC = Path(__file__).with_name("EGGRUMBLE_CastleApproachMatte.client.luau")
REQUIRED = (
    'GQ470_FB015_CASTLE_APPROACH_MATTE_20261121',
    'local MAX_CASTLES = if UserInputService.TouchEnabled then 2 else 3',
    'local PIECES_PER_CASTLE = 8',
    'local MAX_PARTS = MAX_CASTLES * PIECES_PER_CASTLE',
    'local MAX_DISTANCE = 155',
    'local REFRESH_SECONDS = 2.5',
    'core.Name ~= "StandardCore"',
    'ancestor.Name == "TacticalBattlefield"',
    'playerPosition(): Vector3?',
    'humanoid.Health <= 0',
    'Instance.new("WedgePart")',
    'Enum.Material.Slate',
    'p.Anchored = true',
    'p.CanCollide = false',
    'p.CanTouch = false',
    'p.CanQuery = false',
    'p.CastShadow = false',
    'for side = 1, 4 do',
    'math.clamp(faceRadius + 9, 12, 72)',
    'assert(#pieces == PIECES_PER_CASTLE)',
    'decor.lastPose = core.CFrame',
    'decor.lastSize = core.Size',
    'decor.lastPose ~= core.CFrame',
    'decor.lastSize ~= core.Size',
    'player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
    'player:GetAttribute("EGGRUMBLE_CastleApproachOff") ~= true',
    'Workspace.DescendantAdded:Connect',
    'Workspace.DescendantRemoving:Connect',
    'player.CharacterAdded:Connect',
    'player.CharacterRemoving:Connect',
    'task.wait(REFRESH_SECONDS)',
    'assert(actual * PIECES_PER_CASTLE <= MAX_PARTS)',
)
FORBIDDEN = (
    'FireServer', 'InvokeServer', 'RemoteEvent', 'RemoteFunction',
    'DataStoreService', 'LoadCharacter', 'SpawnLocation', 'TakeDamage',
    'Humanoid.Health =', 'SetAttribute("Team"', 'Instance.new("ScreenGui")',
    'Instance.new("BillboardGui")', 'Instance.new("Highlight")',
    'Enum.Material.Neon', 'RenderStepped', 'Heartbeat:Connect',
    'RunService.Stepped', 'workspace.Gravity', 'TweenService',
    'Lighting.', 'Terrain:Fill', 'Humanoid:MoveTo', 'ProximityPrompt',
    'GetMouse', 'CurrentCamera',
)

def validate(s):
    for term in REQUIRED:
        # Prefix substrings such as "155" within "15500" must fail closed.
        if term.startswith("local "):
            present = re.search(r"(?m)^" + re.escape(term) + r"\s*$", s) is not None
        else:
            present = s.count(term) >= 1
        if not present:
            raise ValueError("RED_REQUIRED_" + term)
    stripped = "\n".join(line.split("--", 1)[0] for line in s.splitlines())
    for term in FORBIDDEN:
        if term in stripped:
            raise ValueError("RED_FORBIDDEN_" + term)
    if stripped.count('Instance.new("WedgePart")') != 1:
        raise ValueError("RED_UNBOUNDED_PART_CONSTRUCTION")
    if stripped.count('table.insert(pieces, makePiece(') != 2:
        raise ValueError("RED_PARTS_PER_APPROACH")
    if not re.search(r'for i = 1, math.min\(MAX_CASTLES, #ranked\) do', s):
        raise ValueError("RED_UNBOUNDED_CASTLE_LOD")
    if len(s.encode()) > 9500:
        raise ValueError("RED_OVERSIZED_SOURCE")
    return True

class TestApproachSource(unittest.TestCase):
    def test_contract(self):
        self.assertTrue(validate(SRC.read_text(encoding="utf-8")))

    def test_24_guard_mutants(self):
        s = SRC.read_text(encoding="utf-8")
        mutations = (
            ('then 2 else 3', 'then 200 else 300'),
            ('PIECES_PER_CASTLE = 8', 'PIECES_PER_CASTLE = 80'),
            ('MAX_PARTS = MAX_CASTLES * PIECES_PER_CASTLE', 'MAX_PARTS = 99999'),
            ('MAX_DISTANCE = 155', 'MAX_DISTANCE = 15500'),
            ('REFRESH_SECONDS = 2.5', 'REFRESH_SECONDS = .01'),
            ('core.Name ~= "StandardCore"', 'core.Name ~= "OtherCore"'),
            ('ancestor.Name == "TacticalBattlefield"', 'ancestor.Name == "FakeWorld"'),
            ('humanoid.Health <= 0', 'humanoid.Health < -100'),
            ('for side = 1, 4 do', 'for side = 1, 40 do'),
            ('math.clamp(faceRadius + 9, 12, 72)', 'math.clamp(faceRadius + 9, 12, 3)'),
            ('assert(#pieces == PIECES_PER_CASTLE)', 'assert(true)'),
            ('decor.lastPose = core.CFrame', 'decor.lastPose = CFrame.new()'),
            ('decor.lastSize = core.Size', 'decor.lastSize = Vector3.new()'),
            ('decor.lastPose ~= core.CFrame', 'false'),
            ('decor.lastSize ~= core.Size', 'false'),
            ('p.CanCollide = false', 'p.CanCollide = true'),
            ('p.CanTouch = false', 'p.CanTouch = true'),
            ('p.CanQuery = false', 'p.CanQuery = true'),
            ('p.CastShadow = false', 'p.CastShadow = true'),
            ('Enum.Material.Slate', 'Enum.Material.Neon'),
            ('GetAttribute("EGGRUMBLE_ReducedEffects") ~= true', 'GetAttribute("EGGRUMBLE_ReducedEffects") == true'),
            ('GetAttribute("EGGRUMBLE_CastleApproachOff") ~= true', 'GetAttribute("EGGRUMBLE_CastleApproachOff") == true'),
            ('task.wait(REFRESH_SECONDS)', 'task.wait(.01)'),
            ('assert(actual * PIECES_PER_CASTLE <= MAX_PARTS)', 'assert(true)'),
        )
        for before, after in mutations:
            with self.subTest(before=before):
                self.assertIn(before, s)
                with self.assertRaises(ValueError):
                    validate(s.replace(before, after, 1))

    def test_injected_authority_and_gui(self):
        s = SRC.read_text(encoding="utf-8")
        for api in ('FireServer(', 'Instance.new("ScreenGui")', 'Enum.Material.Neon',
                    'RenderStepped:Connect', 'Humanoid.Health = 0', 'DataStoreService',
                    'CurrentCamera', 'Terrain:FillBlock'):
            with self.subTest(api=api), self.assertRaises(ValueError):
                validate(s + "\n" + api)

if __name__ == "__main__":
    unittest.main()
