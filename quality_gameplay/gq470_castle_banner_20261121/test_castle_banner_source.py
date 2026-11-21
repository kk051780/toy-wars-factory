"""GQ470 castle banner source-only guard: no gameplay ownership, exact art budget, fail-closed mutations."""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name("EGGRUMBLE_CastleBannerMatte.client.luau")


def validate(s: str) -> None:
    markers = (
        "local MAX_PER_TEAM = if UserInputService.TouchEnabled then 2 else 3",
        "local MAX_PARTS_PER_TOWER = 4",
        "local MAX_TOTAL_EXTRA_PARTS = MAX_PER_TEAM * 2 * MAX_PARTS_PER_TOWER",
        'name == "RED_TOWER"', 'name == "BLUE_TOWER"',
        'ancestor.Name == team .. "_CASTLE"',
        'counts[team] >= MAX_PER_TEAM',
        'p.Material = Enum.Material.SmoothPlastic',
        'p.CanCollide = false', 'p.CanTouch = false',
        'p.CanQuery = false', 'p.CastShadow = false',
        'table.insert(entry.connections, tower.Destroying:Connect',
        'tower:IsDescendantOf(Workspace)',
        'player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
        'TweenInfo.new(2.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)',
        'Workspace.DescendantAdded:Connect(attach)',
        'Workspace:GetDescendants()',
    )
    for marker in markers:
        if s.count(marker) != 1:
            raise ValueError("RED_BANNER_CONTRACT_" + marker)
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
    if len(s.encode("utf-8")) > 7800:
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
            ('p.CanCollide = false', 'p.CanCollide = true'),
            ('p.CanTouch = false', 'p.CanTouch = true'),
            ('p.CanQuery = false', 'p.CanQuery = true'),
            ('p.CastShadow = false', 'p.CastShadow = true'),
            ("Enum.Material.SmoothPlastic", "Enum.Material.Neon"),
            ("counts[team] >= MAX_PER_TEAM", "counts[team] > 9000"),
            ("tower.Destroying:Connect", "tower.X:Connect"),
            ("Workspace.DescendantAdded:Connect(attach)", "Workspace.DescendantAdded:Connect(function() end)"),
            ('tower:IsDescendantOf(Workspace)', 'true'),
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
