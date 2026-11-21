"""Source-only safety contract for capped RED/BLUE shoulder crests.
No Studio/Android/FUN or visual-quality claims.
"""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).with_name("EGGRUMBLE_PlayerTeamCrest.client.luau")

FORBIDDEN = (
    r'Instance\.new\(["\'](?:RemoteEvent|RemoteFunction|BindableEvent|ScreenGui|BillboardGui|PointLight|SpotLight|SurfaceLight|ParticleEmitter|Fire|Smoke|Explosion)["\']\)',
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
    'character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")',
    'HumanoidRootPart',
    'Instance.new("WedgePart")',
    'Instance.new("WeldConstraint")',
    'CanCollide = false',
    'CanTouch = false',
    'CanQuery = false',
    'Massless = true',
    'CastShadow = false',
    'Material.SmoothPlastic',
    'local isRed = player.Team ~= nil and player.Team.Name == "RED"',
    'crest.Size = if isRed then Vector3.new(0.52, 0.20, 0.66)',
    'else Vector3.new(0.35, 0.31, 0.63)',
    'LOD_STUDS = 66',
    'LOD_POLL_SECONDS = 0.75',
    'task.wait(LOD_POLL_SECONDS)',
    'local camera = workspace.CurrentCamera',
    'RED = Color3.fromRGB',
    'BLUE = Color3.fromRGB',
    'MAX_REMOTE_CRESTS = if UserInputService.TouchEnabled then 2 else 3',
    'for index = 1, math.min(MAX_REMOTE_CRESTS, #nearby) do',
    'local distance = cameraDistance(player, character, cameraPosition)',
    'return if distance <= LOD_STUDS then distance else nil',
    'if player == localPlayer or not cameraPosition or not character then return nil end',
    'if not mounted[player] then attach(player, character) end',
    'if not root.Parent or not teamColor(player) or isConcealed(player, character) then return nil end',
    'or isConcealed(player, rec.character)',
    'for _, connection in ipairs(rec.watchers or {}) do connection:Disconnect() end',
    'player:GetAttribute(flag) == true or character:GetAttribute(flag) == true',
    'part.Transparency >= 0.5 or part.LocalTransparencyModifier >= 0.5',
    '["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true,',
    'player:GetAttributeChangedSignal(flag):Connect(rejectConcealment)',
    'character:GetAttributeChangedSignal(flag):Connect(rejectConcealment)',
    'part:GetPropertyChangedSignal("Transparency"):Connect(rejectConcealment)',
    'part:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(rejectConcealment)',
    'Stealthed", "IsInvisible", "AssassinCloaked", "EGGRUMBLE_Stealthed',
    'localPlayer:GetAttribute("ReducedEffects") == true',
    'localPlayer:GetAttribute("EGGRUMBLE_TeamCrestsOff") == true',
    'for _, attr in ipairs({ "ReducedEffects", "EGGRUMBLE_TeamCrestsOff" }) do',
    'if cameraPosition and not visualsDisabled() then',
    'for player in pairs(mounted) do removeMounted(player) end',
    'if token ~= generations[player] or player.Character ~= character then return end',
    'if not color then return end',
    'makeCrest(folder, torso, color, -1, isRed)',
    'makeCrest(folder, torso, color, 1, isRed)',
    'selected[player] ~= rec.character or not rec.folder.Parent',
    'table.sort(nearby, function(a, b)',
)

def source_errors(text):
    errors = []
    # Cautionary source comments must not count as executable unsafe APIs.
    executable = "\n".join(line.split("--", 1)[0] for line in text.splitlines())
    for pattern in FORBIDDEN:
        if re.search(pattern, executable):
            errors.append("prohibited:" + pattern)
    for token in REQUIRED:
        if token not in text:
            errors.append("missing:" + token)
    if text.count('makeCrest(folder, torso, color, -1, isRed)') != 1:
        errors.append("wrong_left_count")
    if text.count('makeCrest(folder, torso, color, 1, isRed)') != 1:
        errors.append("wrong_right_count")
    if text.count('Instance.new("WedgePart")') != 1:
        errors.append("extra_part_constructors")
    if 'piece.Transparency = near and 0.04 or 1' in executable:
        errors.append("transparent_distant_parts_allocated")
    if re.search(r'player\.CharacterAdded:Connect\([^\n]*attach', executable):
        errors.append("unbounded_character_added")
    return errors

class AvatarTeamCrestSourceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_source_only_contract(self):
        self.assertFalse(source_errors(self.text), source_errors(self.text))

    def test_no_spawn_or_server_authority(self):
        for call in ('player:LoadCharacter', 'CharacterAutoLoads', 'SpawnLocation',
                     'PivotTo(', 'FireServer(', 'TakeDamage(', 'DataStoreService'):
            self.assertNotIn(call, self.text)

    def test_two_shapes_and_actual_budget(self):
        self.assertEqual(self.text.count('makeCrest(folder, torso, color, -1, isRed)'), 1)
        self.assertEqual(self.text.count('makeCrest(folder, torso, color, 1, isRed)'), 1)
        self.assertIn('MAX_REMOTE_CRESTS = if UserInputService.TouchEnabled then 2 else 3', self.text)
        self.assertIn('if isRed then 0.22 else -0.22', self.text)
        self.assertIn('return if distance <= LOD_STUDS then distance else nil', self.text)

    def test_stealth_6_15_and_immediate_cleanup(self):
        self.assertIn('GetDescendants()', self.text)
        self.assertIn('GetAttributeChangedSignal', self.text)
        self.assertIn('LocalTransparencyModifier', self.text)
        self.assertIn('removeMounted(player)', self.text)
        self.assertIn('rec.watchers or {}', self.text)

    def test_negative_mutations_fail_closed(self):
        replacements = [
            ('CanCollide = false', 'CanCollide = true'),
            ('CanTouch = false', 'CanTouch = true'),
            ('Material.SmoothPlastic', 'Material.Neon'),
            ('LOD_POLL_SECONDS = 0.75', 'LOD_POLL_SECONDS = 0.016'),
            ('character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")',
             'character:FindFirstChild("UNKNOWN_PART")'),
            ('if not color then return end', 'if color then return end'),
            ('MAX_REMOTE_CRESTS = if UserInputService.TouchEnabled then 2 else 3', 'MAX_REMOTE_CRESTS = 999'),
            ('localPlayer:GetAttribute("ReducedEffects") == true',
             'localPlayer:GetAttribute("ReducedEffects") == false'),
            ('localPlayer:GetAttribute("EGGRUMBLE_TeamCrestsOff") == true',
             'localPlayer:GetAttribute("EGGRUMBLE_TeamCrestsOff") == false'),
            ('if cameraPosition and not visualsDisabled() then',
             'if cameraPosition then'),
            ('for player in pairs(mounted) do removeMounted(player) end',
             '-- no immediate disable cleanup'),
            ('for index = 1, math.min(MAX_REMOTE_CRESTS, #nearby) do',
             'for index = 1, #nearby do'),
            ('player:GetAttribute(flag) == true or character:GetAttribute(flag) == true',
             'player:GetAttribute(flag) == false'),
            ('part.Transparency >= 0.5 or part.LocalTransparencyModifier >= 0.5',
             'part.Transparency > 2'),
            ('["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true,',
             '["LeftArm"] = true,'),
            ('player:GetAttributeChangedSignal(flag):Connect(rejectConcealment)',
             '-- removed player cloak watcher'),
            ('character:GetAttributeChangedSignal(flag):Connect(rejectConcealment)',
             '-- removed character cloak watcher'),
            ('part:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(rejectConcealment)',
             '-- removed body transparency watcher'),
            ('for _, connection in ipairs(rec.watchers or {}) do connection:Disconnect() end',
             '-- leaked concealment watchers'),
            ('if player == localPlayer or not cameraPosition or not character then return nil end',
             'if not cameraPosition then return nil end'),
            ('return if distance <= LOD_STUDS then distance else nil',
             'return distance'),
            ('or isConcealed(player, rec.character)', 'or false'),
            ('if not mounted[player] then attach(player, character) end',
             'if mounted[player] then attach(player, character) end'),
            ('if token ~= generations[player] or player.Character ~= character then return end',
             '-- disabled generation fence'),
            ('table.sort(nearby, function(a, b)', '-- removed nearest ordering'),
            ('makeCrest(folder, torso, color, 1, isRed)',
             'makeCrest(folder, torso, color, -1, isRed)'),
        ]
        for before, after in replacements:
            with self.subTest(before=before[:40]):
                self.assertIn(before, self.text)
                mutated = self.text.replace(before, after, 1)
                self.assertTrue(source_errors(mutated), "escaped mutation: " + before)
        for danger in ('local x = Instance.new("RemoteEvent")',
                       'local x = game:GetService("DataStoreService")',
                       'local x = game:GetService("RunService").Heartbeat',
                       'local x = Instance.new("BillboardGui")'):
            with self.subTest(danger=danger):
                self.assertTrue(source_errors(self.text + "\n" + danger))

if __name__ == "__main__":
    unittest.main()
