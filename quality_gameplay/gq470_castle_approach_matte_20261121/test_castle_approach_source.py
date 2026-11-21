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
    'core.Size.X > 126 or core.Size.Z > 126 or core.Size.Y > 150',
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
    'math.clamp(core.Size.X * .5 + 9, 12, 72)',
    'math.clamp(core.Size.Z * .5 + 9, 12, 72)',
    'math.sin(angle) * offsetX, 0, math.cos(angle) * offsetZ',
    'assert(#pieces == PIECES_PER_CASTLE)',
    'Workspace:Raycast(pose.Position + Vector3.new(0, 6, 0)',
    'Vector3.new(0, -14, 0), filter)',
    'hit.Normal.Y < .7',
    'math.abs(hit.Position.Y - pose.Position.Y) > 2.75',
    'piece.Transparency = 1',
    'piece.Transparency = 0',
    'filter.IgnoreWater = true',
    'local ignore: {Instance} = {core}',
    'filter.FilterDescendantsInstances = ignore',
    'placeOnGround(decor.pieces[first]',
    'placeOnGround(decor.pieces[first + 1]',
    'player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
    'player:GetAttribute("EGGRUMBLE_CastleApproachOff") ~= true',
    'Workspace.DescendantAdded:Connect',
    'Workspace.DescendantRemoving:Connect',
    'player.CharacterAdded:Connect',
    'player.CharacterRemoving:Connect',
    'for core in active do clear(core) end',
    'task.wait(REFRESH_SECONDS)',
    'local disposed = false',
    'local trackedConnections: {RBXScriptConnection} = {}',
    'if disposed then return end',
    'while not disposed and script.Parent do',
    'script.Destroying:Connect(function()',
    'disposed = true',
    'for _, connection in ipairs(trackedConnections) do',
    'connection:Disconnect()',
    'table.clear(trackedConnections)',
    'table.clear(candidates)',
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
            present = re.search(r"(?m)^[ \t]*" + re.escape(term) + r"[ \t]*$", s) is not None
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
    if s.count('keep(') != 7:  # Six event listeners plus the helper definition.
        raise ValueError("RED_UNTRACKED_EVENT_LISTENER")
    if s.count('for core in active do') != 3:  # pruning, respawn and destroy
        raise ValueError("RED_STALE_CASTLE_DECOR")
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
            ('core.Size.X > 126 or core.Size.Z > 126 or core.Size.Y > 150', 'false'),
            ('ancestor.Name == "TacticalBattlefield"', 'ancestor.Name == "FakeWorld"'),
            ('humanoid.Health <= 0', 'humanoid.Health < -100'),
            ('for side = 1, 4 do', 'for side = 1, 40 do'),
            ('math.clamp(core.Size.X * .5 + 9, 12, 72)', 'math.clamp(core.Size.X * .5 + 9, 12, 3)'),
            ('math.clamp(core.Size.Z * .5 + 9, 12, 72)', 'math.clamp(core.Size.Z * .5 + 9, 12, 3)'),
            ('math.sin(angle) * offsetX, 0, math.cos(angle) * offsetZ',
             'math.sin(angle) * offsetZ, 0, math.cos(angle) * offsetX'),
            ('assert(#pieces == PIECES_PER_CASTLE)', 'assert(true)'),
            ('hit.Normal.Y < .7', 'false'),
            ('math.abs(hit.Position.Y - pose.Position.Y) > 2.75', 'false'),
            ('filter.IgnoreWater = true', 'filter.IgnoreWater = false'),
            ('local ignore: {Instance} = {core}', 'local ignore: {Instance} = {core.Parent}'),
            ('Vector3.new(0, -14, 0), filter)', 'Vector3.new(0, 14, 0), filter)'),
            ('piece.Transparency = 1', 'piece.Transparency = 0'),
            ('p.CanCollide = false', 'p.CanCollide = true'),
            ('p.CanTouch = false', 'p.CanTouch = true'),
            ('p.CanQuery = false', 'p.CanQuery = true'),
            ('p.CastShadow = false', 'p.CastShadow = true'),
            ('Enum.Material.Slate', 'Enum.Material.Neon'),
            ('GetAttribute("EGGRUMBLE_ReducedEffects") ~= true', 'GetAttribute("EGGRUMBLE_ReducedEffects") == true'),
            ('GetAttribute("EGGRUMBLE_CastleApproachOff") ~= true', 'GetAttribute("EGGRUMBLE_CastleApproachOff") == true'),
            ('for core in active do clear(core) end', 'task.defer(refresh)'),
            ('task.wait(REFRESH_SECONDS)', 'task.wait(.01)'),
            ('assert(actual * PIECES_PER_CASTLE <= MAX_PARTS)', 'assert(true)'),
        )
        for before, after in mutations:
            with self.subTest(before=before):
                self.assertIn(before, s)
                with self.assertRaises(ValueError):
                    validate(s.replace(before, after, 1))

    def test_teardown_mutants_fail_closed(self):
        s = SRC.read_text(encoding="utf-8")
        mutants = (
            ('script.Destroying:Connect(function()', 'script:WaitForChild("Destroyed")'),
            ('disposed = true', 'disposed = false'),
            ('connection:Disconnect()', 'connection:Connect()'),
            ('table.clear(trackedConnections)', '-- listener connections leaked'),
            ('table.clear(candidates)', '-- candidate registry leaked'),
            ('while not disposed and script.Parent do', 'while script.Parent do'),
            ('if disposed then return end', '-- no disposed guard'),
            ('keep(player.CharacterAdded:Connect', 'player.CharacterAdded:Connect'),
        )
        for before, after in mutants:
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
