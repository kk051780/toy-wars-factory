"""GQ470 castle banner source-only guard: no gameplay ownership, exact art budget, fail-closed mutations."""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name("EGGRUMBLE_CastleBannerMatte.client.luau")


def validate(s: str) -> None:
    markers = (
        "local MAX_PER_TEAM = if UserInputService.TouchEnabled then 2 else 3",
        "local MAX_PARTS_PER_TOWER = 4",
        "local MAX_NEUTRAL_CASTLES = 2",
        "local NEARER_MARGIN_STUDS = 8",
        "local MAX_TOTAL_EXTRA_PARTS = (MAX_PER_TEAM * 2 + MAX_NEUTRAL_CASTLES) * MAX_PARTS_PER_TOWER",
        'name == "RED_TOWER"', 'name == "BLUE_TOWER"',
        'ancestor.Name == team .. "_CASTLE"',
        'if counts[team] >= limit then return end',
        'local limit = if team == "NEUTRAL" then MAX_NEUTRAL_CASTLES else MAX_PER_TEAM',
        'name == "StandardCore"',
        'parent.Name == "TacticalBattlefield"',
        'local function cameraDistance(tower: BasePart): number',
        'if team == "NEUTRAL" and counts[team] >= limit then',
        'farthest and cameraDistance(tower) + NEARER_MARGIN_STUDS < farthestDistance',
        'if descendant.Name == "StandardCore" then attach(descendant) end',
        'p.Material = if name == "MatteFlagstaff" then Enum.Material.SmoothPlastic else Enum.Material.Fabric',
        'p.CanCollide = false', 'p.CanTouch = false',
        'p.CanQuery = false', 'p.CastShadow = false',
        'table.insert(entry.connections, tower.Destroying:Connect',
        'tower:IsDescendantOf(Workspace) or castleTeam(tower) ~= team',
        'local function refillVacantSlots()',
        'refillVacantSlots()',
        'local restingPose: {[BasePart]: CFrame} = {}',
        'for _, panel in fly do restingPose[panel] = panel.CFrame end',
        'local base = restingPose[panel]',
        'panel.CFrame = base',
        'player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
        'TweenInfo.new(2.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)',
        'Workspace.DescendantAdded:Connect(attach)',
        'player.CharacterAdded:Connect(function()',
        'part(folder, "TeamClothBody",',
    )
    for marker in markers:
        # Numeric budget declarations need whole-line matching: 4 must not accept 400.
        count = (len(re.findall(r"(?m)^" + re.escape(marker) + r"\s*$", s))
                 if marker.startswith(("local MAX_", "local NEARER_")) else s.count(marker))
        if count != 1:
            raise ValueError("RED_BANNER_CONTRACT_" + marker)
    # PR #979 only targets BasePart names containing banner/pennant/castleflag.
    # This new candidate has its own TweenService owner: never double-animate it.
    for visual_part in ("MatteFlagstaff", "TeamClothBody", "SplitTailUpper",
                        "SplitTailLower", "SinglePointTail"):
        if any(token in visual_part.lower() for token in
               ("banner", "pennant", "castleflag")):
            raise ValueError("RED_BANNER_PR979_DOUBLE_SWAY")
    if 'part(folder, "TeamBannerBody",' in s:
        raise ValueError("RED_BANNER_PR979_DOUBLE_SWAY_PARTNAME")
    if s.count('Workspace:GetDescendants()') != 3:
        raise ValueError("RED_BANNER_INITIAL_RESPAWN_AND_SLOT_RECOVERY_RESCAN")
    stripped = "\n".join(line.split("--", 1)[0] for line in s.splitlines())
    forbidden = (
        "RemoteEvent", "RemoteFunction", "FireServer", "InvokeServer", "DataStore",
        "TakeDamage", "Humanoid.Health =", "SetPrimaryPartCFrame",
        "RenderStepped", "Heartbeat", "Stepped", "while true",
        "Enum.Material.Neon", "BillboardGui", "ScreenGui", "Highlight",
        "LoadCharacter", "LoadCharacterAsync", "SpawnLocation",
        "game:GetService(\"ServerStorage\")", "workspace.Gravity =",
        "TweenService:Create(tower",
    )
    for token in forbidden:
        if token in stripped:
            raise ValueError("RED_BANNER_AUTHORITY_OR_ART_" + token)
    if len(s.encode("utf-8")) > 11000:
        raise ValueError("RED_BANNER_SOURCE_BUDGET")
    if len(re.findall(r'Instance.new\("(?:Part|WedgePart)"\)', stripped)) != 2:
        raise ValueError("RED_BANNER_FACTORY_COUNT")
    if not re.search(r"if not team or not tower:IsA\(\"BasePart\"\) or tracked\[tower\] then return end", s):
        raise ValueError("RED_BANNER_IDEMPOTENCE")


class BannerSourceTests(unittest.TestCase):
    def test_source_contract(self):
        validate(SOURCE.read_text(encoding="utf-8"))

    def test_fail_closed_mutations(self):
        s = SOURCE.read_text(encoding="utf-8")
        mutations = [
            ("then 2 else 3", "then 40 else 50"),
            ("MAX_PARTS_PER_TOWER = 4", "MAX_PARTS_PER_TOWER = 400"),
            ("MAX_NEUTRAL_CASTLES = 2", "MAX_NEUTRAL_CASTLES = 200"),
            ("NEARER_MARGIN_STUDS = 8", "NEARER_MARGIN_STUDS = 800"),
            ('p.CanCollide = false', 'p.CanCollide = true'),
            ('p.CanTouch = false', 'p.CanTouch = true'),
            ('p.CanQuery = false', 'p.CanQuery = true'),
            ('p.CastShadow = false', 'p.CastShadow = true'),
            ("Enum.Material.SmoothPlastic", "Enum.Material.Neon"),
            ("Enum.Material.Fabric", "Enum.Material.Neon"),
            ("counts[team] >= limit", "counts[team] > 9000"),
            ('parent.Name == "TacticalBattlefield"', 'parent.Name == "OtherWorld"'),
            ('name == "StandardCore"', 'name == "OtherCore"'),
            ('if team == "NEUTRAL" and counts[team] >= limit then', 'if false then'),
            ('farthest and cameraDistance(tower) + NEARER_MARGIN_STUDS < farthestDistance', 'farthest and true'),
            ("tower.Destroying:Connect", "tower.X:Connect"),
            ("Workspace.DescendantAdded:Connect(attach)", "Workspace.DescendantAdded:Connect(function() end)"),
            ('tower:IsDescendantOf(Workspace) or castleTeam(tower) ~= team', 'tower:IsDescendantOf(Workspace)'), 
            ('local base = restingPose[panel]', 'local base = panel.CFrame'),
            ('local function refillVacantSlots()', 'local function noRefill()'),
            ('panel.CFrame = base', 'panel.CFrame = CFrame.new()'),
            ('part(folder, "TeamClothBody",', 'part(folder, "TeamBannerBody",'),
            ('ancestor.Name == team .. "_CASTLE"', 'true'),
            ('name == "RED_TOWER"', 'name == "OTHER_TOWER"'),
            ("GetAttribute(\"EGGRUMBLE_ReducedEffects\") ~= true", "GetAttribute(\"EGGRUMBLE_ReducedEffects\") == true"),
            ("TweenInfo.new(2.6", "TweenInfo.new(0.01"),
        ]
        for old, new in mutations:
            self.assertIn(old, s)
            with self.subTest(old=old), self.assertRaises(ValueError):
                validate(s.replace(old, new))
        for forbidden in ('RemoteEvent', 'FireServer()', 'RenderStepped:Connect',
                          'Instance.new("Highlight")', 'Enum.Material.Neon',
                          'Humanoid.Health = 0'):
            with self.subTest(forbidden=forbidden), self.assertRaises(ValueError):
                validate(s + "\n" + forbidden)


if __name__ == "__main__":
    unittest.main()
