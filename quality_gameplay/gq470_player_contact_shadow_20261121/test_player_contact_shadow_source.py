"""GQ470 FB-015 local grounded avatar shadow: source/negative ART gate, not engine proof."""
from pathlib import Path
import unittest

SOURCE_PATH = Path(__file__).with_name("EGGRUMBLE_PlayerContactShadow.client.luau")
REQUIRED = [
    "GQ470_FB015_PLAYER_CONTACT_SHADOW_REAL69_20261121",
    'local INTERVAL = if UserInputService.TouchEnabled then 0.16 else 0.10',
    'local MAX_CAMERA_DISTANCE = if UserInputService.TouchEnabled then 55 else 75',
    'local MIN_GROUND_NORMAL = 0.78',
    'local SHADOW_ALPHA = 0.76',
    'local FEATURE_OFF = "EGGRUMBLE_PlayerContactShadowOff"',
    'local REDUCED_EFFECTS = "EGGRUMBLE_ReducedEffects"',
    'local PLAYER = Players.LocalPlayer',
    'characterVisible(character, humanoid)',
    'humanoid.FloorMaterial == Enum.Material.Air',
    'humanoid.Health <= 0',
    'Enum.HumanoidStateType.Swimming',
    'Enum.HumanoidStateType.Freefall',
    'head.LocalTransparencyModifier >= 0.95',
    'character:GetAttribute("StealthActive") == true',
    'camera.CameraSubject',
    'subject:IsDescendantOf(character)',
    'params.FilterType = Enum.RaycastFilterType.Exclude',
    'params.FilterDescendantsInstances = {character, folder}',
    'params.IgnoreWater = false',
    'params.RespectCanCollide = true',
    'Workspace:Raycast(',
    'hit.Normal.Y < MIN_GROUND_NORMAL',
    'hit.Material == Enum.Material.Water',
    'not hit.Instance.CanCollide',
    'ancestor:FindFirstChildOfClass("Humanoid")',
    'part.Shape = Enum.PartType.Cylinder',
    'part.Material = Enum.Material.SmoothPlastic',
    'part.Transparency = SHADOW_ALPHA',
    'part.CanCollide = false',
    'part.CanTouch = false',
    'part.CanQuery = false',
    'part.CastShadow = false',
    'CFrame.fromMatrix(hit.Position + normal * 0.045, normal, tangent)',
    'PLAYER.CharacterRemoving:Connect(clearDisc)',
    'script.Destroying:Connect(function()',
    'disabledConnection:Disconnect()',
    'reducedConnection:Disconnect()',
    'removingConnection:Disconnect()',
    'folder:Destroy()',
]
BANNED = [
    "FireServer", "InvokeServer", "RemoteEvent", "RemoteFunction",
    "TakeDamage", "DataStoreService", "MarketplaceService", "ParticleEmitter",
    "BillboardGui", "ScreenGui", "RenderStepped", "Heartbeat", "while true",
    'Enum.Material.Neon', 'part.CanCollide = true', 'part.CanTouch = true',
    'part.CanQuery = true'
]

def validate(raw):
    body = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("--"))
    if len(raw.encode("utf-8")) > 8000:
        raise ValueError("RED_SOURCE_SIZE")
    for marker in REQUIRED:
        if marker not in raw:
            raise ValueError("RED_MISSING_" + marker)
    for word in BANNED:
        if word in body:
            raise ValueError("RED_FORBIDDEN_" + word)
    if body.count('Instance.new("Part")') != 1:
        raise ValueError("RED_MORE_THAN_ONE_PART_FACTORY")
    if body.count('task.delay(INTERVAL, update)') != 6:
        raise ValueError("RED_LOOP_RATE_OR_UNBOUNDED_RECURSION")
    if body.count('Workspace:Raycast(') != 1:
        raise ValueError("RED_RAYCAST_BUDGET")
    if body.count('part.CanCollide = false') != 1:
        raise ValueError("RED_COLLISION_SOURCE")
    if body.count('part.CanQuery = false') != 1:
        raise ValueError("RED_QUERY_SOURCE")
    if not body.index('script.Destroying:Connect') < body.index('folder:Destroy()'):
        raise ValueError("RED_DESTROY_LIFETIME")

class LocalAvatarContactShadow(unittest.TestCase):
    def test_safe_source(self):
        validate(SOURCE_PATH.read_text(encoding="utf-8"))

    def test_negative_mutations(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        mutations = [
            ('then 0.16 else 0.10', 'then 0.001 else 0.001'),
            ('then 55 else 75', 'then 999 else 999'),
            ('MIN_GROUND_NORMAL = 0.78', 'MIN_GROUND_NORMAL = -1'),
            ('SHADOW_ALPHA = 0.76', 'SHADOW_ALPHA = 0'),
            ('humanoid.Health <= 0', 'humanoid.Health < 0'),
            ('humanoid.FloorMaterial == Enum.Material.Air', 'false'),
            ('head.LocalTransparencyModifier >= 0.95', 'false'),
            ('character:GetAttribute("StealthActive") == true', 'false'),
            ('camera.CameraSubject', 'nil'),
            ('subject:IsDescendantOf(character)', 'true'),
            ('params.IgnoreWater = false', 'params.IgnoreWater = true'),
            ('params.RespectCanCollide = true', 'params.RespectCanCollide = false'),
            ('hit.Material == Enum.Material.Water', 'hit.Material == Enum.Material.Grass'),
            ('part.CanCollide = false', 'part.CanCollide = true'),
            ('part.CanQuery = false', 'part.CanQuery = true'),
            ('part.Shape = Enum.PartType.Cylinder', 'part.Shape = Enum.PartType.Ball'),
            ('CFrame.fromMatrix(hit.Position + normal * 0.045, normal, tangent)', 'CFrame.new(hit.Position)'),
            ('PLAYER.CharacterRemoving:Connect(clearDisc)', 'PLAYER.CharacterRemoving:Connect(function() end)'),
            ('script.Destroying:Connect(function()', 'script.Changed:Connect(function()'),
            ('task.delay(INTERVAL, update)', 'update()'),
            ('local function ensureDisc(): Part', 'local function ensureDisc(): Part\n    local hack = Instance.new("Part")'),
            ('-- A-only optional visual:', 'local FakeRemote = game:GetService("ReplicatedStorage"):FindFirstChild("Fake")\n-- A-only optional visual:'),
        ]
        for old, new in mutations:
            with self.subTest(old=old):
                self.assertIn(old, source)
                mutated = source.replace(old, new, 1)
                with self.assertRaises(ValueError):
                    validate(mutated)

if __name__ == "__main__":
    unittest.main()
