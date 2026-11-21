"""Conservative SOURCE-only gate for 2-Part player team shoulder crests.
Does not simulate Studio or claim Luau Native / Rojo / Android / user acceptance.
"""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name("EGGRUMBLE_PlayerTeamCrest.client.luau")

PROHIBITED_RUNTIME_APIS = (
    r'Instance\.new\(["\'](?:RemoteEvent|RemoteFunction|BindableEvent|ScreenGui|BillboardGui|'
    r'PointLight|SpotLight|SurfaceLight|ParticleEmitter|Fire|Smoke|Explosion)["\']\)',
    r'\b(?:FireServer|FireAllClients|InvokeServer|TakeDamage|LoadCharacter|Kick)\s*\(',
    r'\b(?:DataStoreService|MarketplaceService|TeleportService|HttpService|RunService)\b',
    r'\b(?:RenderStepped|Heartbeat|Stepped)\b',
    r'\bEnum\.Material\.Neon\b',
    r'\bHumanoid\.Health\s*=',
)

REQUIRED = (
    'local localPlayer = Players.LocalPlayer',
    'PlayerAdded:Connect(register)',
    'PlayerRemoving:Connect(unregister)',
    'CharacterAdded:Connect',
    'CharacterRemoving:Connect',
    'GetPropertyChangedSignal("Team")',
    'humanoid.Died:Connect',
    'generation',
    'UpperTorso',
    'Torso',
    'HumanoidRootPart',
    'WedgePart',
    'WeldConstraint',
    'CanCollide = false',
    'CanTouch = false',
    'CanQuery = false',
    'Massless = true',
    'CastShadow = false',
    'Material.SmoothPlastic',
    'LOD_STUDS = 66',
    'LOD_POLL_SECONDS = 0.75',
    'task.wait(LOD_POLL_SECONDS)',
    'local camera = workspace.CurrentCamera',
    'RED = Color3.fromRGB',
    'BLUE = Color3.fromRGB',
)

def source_errors(text):
    errors = []
    for pattern in PROHIBITED_RUNTIME_APIS:
        if re.search(pattern, text):
            errors.append("prohibited:" + pattern)
    for token in REQUIRED:
        if token not in text:
            errors.append("missing:" + token)
    if text.count('makeCrest(folder, torso, color, -1)') != 1:
        errors.append("not_one_left_crest")
    if text.count('makeCrest(folder, torso, color, 1)') != 1:
        errors.append("not_one_right_crest")
    if text.count('Instance.new("WedgePart")') != 1:
        errors.append("extra_part_constructors")
    if not re.search(r'if token ~= generations\[player\] or player\.Character ~= character then return end', text):
        errors.append("missing_async_character_fence")
    if not re.search(r'if not color then return end', text):
        errors.append("wrong_unassigned_team")
    if not re.search(r'if not near and cameraPosition and rec\.root\.Parent then', text):
        errors.append("missing_camera_lod")
    if not re.search(r'piece\.Transparency = near and 0\.04 or 1', text):
        errors.append("missing_full_distance_hide")
    if not re.search(r'if rec\.died then rec\.died:Disconnect\(\) end', text):
        errors.append("missing_humanoid_died_disconnect")
    return errors

class AvatarTeamCrestSourceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_source_only_contract(self):
        self.assertFalse(source_errors(self.text), source_errors(self.text))

    def test_local_character_not_spawn_manipulation(self):
        self.assertNotIn("player:LoadCharacter", self.text)
        self.assertNotIn("CharacterAutoLoads", self.text)
        self.assertNotIn("SpawnLocation", self.text)
        self.assertNotIn("PivotTo(", self.text)

    def test_two_crests_each_and_lod(self):
        self.assertEqual(self.text.count('makeCrest(folder, torso, color, -1)'), 1)
        self.assertEqual(self.text.count('makeCrest(folder, torso, color, 1)'), 1)
        self.assertIn('LOD_POLL_SECONDS = 0.75', self.text)

    def test_team_and_respawn_lifetime(self):
        self.assertIn('player:GetPropertyChangedSignal("Team")', self.text)
        self.assertIn('token ~= generations[player]', self.text)
        self.assertIn('removeMounted(player)', self.text)

    def test_negative_regressions_fail_closed(self):
        mutants = [
            self.text.replace("CanCollide = false", "CanCollide = true", 1),
            self.text.replace("CanTouch = false", "CanTouch = true", 1),
            self.text.replace("Material.SmoothPlastic", "Material.Neon", 1),
            self.text.replace("LOD_POLL_SECONDS = 0.75", "LOD_POLL_SECONDS = 0.016", 1),
            self.text.replace("UpperTorso", "Head", 1),
            self.text.replace("if not color then return end", "if color then return end", 1),
            self.text.replace("piece.Transparency = near and 0.04 or 1", "piece.Transparency = 0", 1),
            self.text.replace("if rec.died then rec.died:Disconnect() end", "-- lost cleanup", 1),
            self.text.replace('makeCrest(folder, torso, color, 1)', 'makeCrest(folder, torso, color, -1)', 1),
            self.text.replace("if token ~= generations[player] or player.Character ~= character then return end",
                              "-- late character race", 1),
            self.text + '\nlocal x = Instance.new("RemoteEvent")',
            self.text + '\nlocal x = game:GetService("DataStoreService")',
            self.text + '\nlocal x = game:GetService("RunService").Heartbeat',
            self.text + '\nlocal y = Instance.new("BillboardGui")',
        ]
        for i, mutant in enumerate(mutants):
            with self.subTest(mutation=i):
                self.assertTrue(source_errors(mutant), f"mutation {i} escaped")

if __name__ == "__main__":
    unittest.main()
