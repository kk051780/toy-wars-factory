"""Fail-closed static QA for OPTIONAL shoulder crests. Studio/Android/ART not measured."""
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
    'local MAX_REMOTE_CRESTS = if UserInputService.TouchEnabled then 2 else 3',
    'STEALTH_FLAGS = { "Stealthed", "IsInvisible", "AssassinCloaked", "EGGRUMBLE_Stealthed" }',
    'PART_TRANSPARENCY_LIMIT = 0.35',
    'player:GetAttribute(flag) == true or character:GetAttribute(flag) == true',
    'child:IsA("BasePart") and child.Name ~= "HumanoidRootPart"',
    'child.Transparency >= PART_TRANSPARENCY_LIMIT',
    'child.LocalTransparencyModifier >= PART_TRANSPARENCY_LIMIT',
    'return bodyCount == 0',
    'for _, conn in ipairs(rec.watchers) do conn:Disconnect() end',
    'if rec.folder then rec.folder:Destroy() end',
    'rec.pieces = nil',
    'watchActiveVisibility(player, rec)',
    'owner:GetAttributeChangedSignal(flag):Connect(dropIfHidden)',
    'limb:GetPropertyChangedSignal("Transparency"):Connect(dropIfHidden)',
    'limb:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(dropIfHidden)',
    'rec.character.ChildAdded:Connect(function(child)',
    'rec.character.ChildRemoved:Connect(function(child)',
    'dropIfHidden()',
    'GetPropertyChangedSignal("Team")',
    'humanoid.Died:Connect',
    'CharacterAdded:Connect',
    'CharacterRemoving:Connect',
    'Players.PlayerAdded:Connect(register)',
    'Players.PlayerRemoving:Connect(unregister)',
    'token ~= generations[player] or player.Character ~= character',
    'rec.character ~= player.Character or not rec.character.Parent',
    'not rec.root.Parent or not rec.torso.Parent',
    'localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
    'localPlayer:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects")',
    'distance <= LOD_STUDS',
    'if valid then valid = not hiddenAvatar(player, rec.character) end',
    'table.sort(candidates, function(a, b)',
    'elseif remotesDrawn < MAX_REMOTE_CRESTS then',
    'if rec.pieces then remotesDrawn += 1 end',
    'clearPieces(rec)',
    'showPieces(player, rec)',
    'task.wait(LOD_POLL_SECONDS)',
    'LOD_STUDS = 66',
    'LOD_POLL_SECONDS = 0.75',
    'Instance.new("WedgePart")',
    'Instance.new("WeldConstraint")',
    'CanCollide = false',
    'CanTouch = false',
    'CanQuery = false',
    'Massless = true',
    'CastShadow = false',
    'Material.SmoothPlastic',
    'crest.Size = if isRed then Vector3.new(0.52, 0.20, 0.66)',
    'else Vector3.new(0.35, 0.31, 0.63)',
    'makeCrest(folder, rec.torso, color, -1, isRed)',
    'makeCrest(folder, rec.torso, color, 1, isRed)',
)

def source_errors(text):
    errors = []
    executable = "\n".join(line.split("--", 1)[0] for line in text.splitlines())
    for pattern in PROHIBITED_RUNTIME_APIS:
        if re.search(pattern, executable):
            errors.append("prohibited:" + pattern)
    for token in REQUIRED:
        if token not in text:
            errors.append("missing:" + token)
    if text.count('Instance.new("WedgePart")') != 1:
        errors.append("extra_wedge_constructor")
    if text.count('makeCrest(folder, rec.torso, color, -1, isRed)') != 1 or \
       text.count('makeCrest(folder, rec.torso, color, 1, isRed)') != 1:
        errors.append("not_exact_two_crests")
    if 'piece.Transparency = near and 0.04 or 1' in executable:
        errors.append("invisible_parts_retained_at_distance")
    if 'local folder = Instance.new("Folder")' not in text.split(
            'local function showPieces(')[1].split('local function register(')[0]:
        errors.append("parts_created_before_lod_selection")
    if not re.search(r'if hiddenAvatar\(player, rec.character\) then return end', text):
        errors.append("draw_without_stealth_check")
    if not re.search(r'local remotesDrawn = 0[\s\S]*?remotesDrawn < MAX_REMOTE_CRESTS', text):
        errors.append("unbounded_remote_creation")
    if text.count('Players.PlayerAdded:Connect(register)') != 1:
        errors.append("duplicate_player_registration")
    return errors

class TeamCrestBoundedVisualGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_source_only_visual_and_gameplay_separation(self):
        self.assertFalse(source_errors(self.text), source_errors(self.text))
        for forbidden in ("CharacterAutoLoads", "SpawnLocation", "PivotTo(",
                          "game:GetService(\"ReplicatedStorage\")", "MarketplaceService"):
            self.assertNotIn(forbidden, self.text)

    def test_r6_r15_shape_accessibility(self):
        self.assertIn('FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")', self.text)
        self.assertIn('if isRed then 0.22 else -0.22', self.text)
        self.assertIn('RED = Color3.fromRGB', self.text)
        self.assertIn('BLUE = Color3.fromRGB', self.text)

    def test_no_idle_hidden_parts_and_hard_budget(self):
        self.assertIn("Merely register the rig. No WedgePart exists", self.text)
        self.assertIn("TouchEnabled then 2 else 3", self.text)
        self.assertIn("clearPieces(rec)", self.text)

    def test_stealth_and_lifecycle_watchers(self):
        self.assertIn('Player', self.text)
        self.assertIn('Character', self.text)
        self.assertIn('hiddenAvatar(player, rec.character)', self.text)
        self.assertIn('watchActiveVisibility(player, rec)', self.text)
        self.assertIn('localPlayer:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects")', self.text)

    def test_20_fail_closed_source_mutants(self):
        old_new = [
            ('UserInputService.TouchEnabled then 2 else 3', 'UserInputService.TouchEnabled then 99 else 99'),
            ('"Stealthed", "IsInvisible"', '"Visible", "IsInvisible"'),
            ('"AssassinCloaked", "EGGRUMBLE_Stealthed"', '"AssassinCloaked", "Other"'),
            ('player:GetAttribute(flag) == true or character:GetAttribute(flag) == true',
             'player:GetAttribute(flag) == true'),
            ('child.Transparency >= PART_TRANSPARENCY_LIMIT',
             'child.Transparency > 10'),
            ('child.LocalTransparencyModifier >= PART_TRANSPARENCY_LIMIT',
             'child.LocalTransparencyModifier > 10'),
            ('return bodyCount == 0', 'return false'),
            ('owner:GetAttributeChangedSignal(flag):Connect(dropIfHidden)',
             'owner:GetAttributeChangedSignal(flag)'),
            ('limb:GetPropertyChangedSignal("Transparency"):Connect(dropIfHidden)',
             'limb:GetPropertyChangedSignal("Transparency")'),
            ('limb:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(dropIfHidden)',
             'limb:GetPropertyChangedSignal("LocalTransparencyModifier")'),
            ('if rec.folder then rec.folder:Destroy() end', '-- no cleanup'),
            ('rec.pieces = nil', 'rec.pieces = {}'),
            ('remotesDrawn < MAX_REMOTE_CRESTS', 'remotesDrawn < 999'),
            ('distance <= LOD_STUDS', 'distance <= 99999'),
            ('if hiddenAvatar(player, rec.character) then return end', '-- no cloak pretest'),
            ('if valid then valid = not hiddenAvatar(player, rec.character) end',
             '-- no cloak sweep'),
            ('localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
             'true'),
            ('rec.character.ChildAdded:Connect(function(child)', 'rec.character.ChildAdded:Connect(function(x)'),
            ('rec.character.ChildRemoved:Connect(function(child)', 'rec.character.ChildRemoved:Connect(function(x)'),
            ('CanCollide = false', 'CanCollide = true'),
        ]
        for index, (old, new) in enumerate(old_new):
            with self.subTest(index=index):
                self.assertIn(old, self.text)
                mutant = self.text.replace(old, new, 1)
                self.assertTrue(source_errors(mutant), f"mutant {index} escaped")

    def test_4_forbidden_api_mutants(self):
        for addition in (
            '\nlocal x = Instance.new("RemoteEvent")',
            '\nlocal x = game:GetService("DataStoreService")',
            '\nlocal x = game:GetService("RunService").Heartbeat',
            '\nlocal x = Instance.new("BillboardGui")',
        ):
            self.assertTrue(source_errors(self.text + addition))

if __name__ == "__main__":
    unittest.main()
