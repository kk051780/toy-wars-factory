"""P0 ART: fail-closed source contract; NOT a Roblox runtime or visual PASS."""
from pathlib import Path
import re
import unittest

SRC = Path(__file__).with_name("EGGRUMBLE_NeutralContactShadows.client.luau")
MARKERS = [
 "GQ470_FB015_NEUTRAL_CONTACT_SHADOWS_REAL69_20261121",
 'local MAX_SHADOWS = if TOUCH then 6 else 10',
 'local MAX_DISTANCE = if TOUCH then 55 else 72',
 'local UPDATE_SECONDS = if TOUCH then 0.95 else 0.75',
 'local RESCAN_SECONDS = 3.8',
 'local MIN_GROUND_NORMAL = 0.72',
 'local SHADOW_TRANSPARENCY = 0.73',
 'EGGRUMBLE_NeutralSpecies',
 'EGGRUMBLE_NeutralContactShadowsOff',
 'EGGRUMBLE_ReducedEffects',
 'Workspace:GetDescendants()',
 'typeof(species) == "string"',
 'humanoid.Health > 0',
 'table.sort(nearby',
 'math.min(MAX_SHADOWS, #nearby)',
 'Workspace:Raycast',
 'ray.IgnoreWater = false',
 'ray.RespectCanCollide = true',
 'hit.Normal.Y < MIN_GROUND_NORMAL',
 'local tangent = Vector3.new(0, 0, 1):Cross(groundNormal).Unit',
 'disc.CFrame = CFrame.fromMatrix(',
 'entry.hit.Position + groundNormal * 0.035, groundNormal, tangent)',
 'hit.Material == Enum.Material.Water',
 'disc.Shape = Enum.PartType.Cylinder',
 'disc.Material = Enum.Material.SmoothPlastic',
 'disc.CanCollide = false',
 'disc.CanTouch = false',
 'disc.CanQuery = false',
 'disc.CastShadow = false',
 'disc.Transparency = SHADOW_TRANSPARENCY',
 'disc.Parent = folder',
 'disc:Destroy()',
 'script.Destroying:Connect',
 'task.delay(UPDATE_SECONDS, tick)',
 'task.defer(tick)',
 'PLAYER:GetAttributeChangedSignal(FEATURE_OFF)',
 'PLAYER:GetAttributeChangedSignal(REDUCED_EFFECTS)',
 'local featureOffConnection: RBXScriptConnection? = nil',
 'local reducedEffectsConnection: RBXScriptConnection? = nil',
 'featureOffConnection:Disconnect()',
 'reducedEffectsConnection:Disconnect()',
 'script.Destroying:Connect(function()',
]
BANNED = [
 "FireServer", "InvokeServer", "RemoteEvent", "RemoteFunction",
 "TakeDamage", "DataStoreService", "MarketplaceService", "RunService",
 "RenderStepped", "Heartbeat", "Enum.Material.Neon", "ParticleEmitter",
 "PointLight", "while true", "while task.wait",
 "disc.CanCollide = true", "disc.CanTouch = true", "disc.CanQuery = true",
]
def validate(source: str):
    for token in MARKERS:
        if token not in source:
            raise ValueError("RED_NEUTRAL_MISSING_" + token)
    for token in BANNED:
        if token in source:
            raise ValueError("RED_NEUTRAL_FORBIDDEN_" + token)
    if len(source.encode("utf8")) > 9500:
        raise ValueError("RED_NEUTRAL_SOURCE_SIZE")
    if source.count('Instance.new("Part")') != 1:
        raise ValueError("RED_NEUTRAL_PART_FACTORY")
    # Reject the transient Android Part-budget spike: retiring the old
    # selected set MUST happen before any next selected Part allocation.
    if source.count("GQ470_CONTACT_SHADOW_HARD_PART_BUDGET_V2") != 1:
        raise ValueError("RED_NEUTRAL_HARD_BUDGET_MARKER")
    scope = source.split("GQ470_CONTACT_SHADOW_HARD_PART_BUDGET_V2", 1)[1]
    retire = scope.find("for model, disc in pairs(active) do")
    allocate = scope.find("for _, entry in ipairs(chosen) do")
    factory = scope.find("disc = newDisc()")
    if not (0 <= retire < allocate < factory):
        raise ValueError("RED_NEUTRAL_PEAK_ALLOCATION_OVER_CAP")
    if source.count("disc = newDisc()") != 1 or (
        "if not selected[model] then" not in scope
        or "table.insert(chosen, {model = entry.model, root = entry.root, hit = hit})" not in scope
        or "local limit = math.min(MAX_SHADOWS, #nearby)" not in scope
    ):
        raise ValueError("RED_NEUTRAL_SELECTION_RECLAIM_CONTRACT")
    if source.count('task.delay(UPDATE_SECONDS, tick)') != 3:
        raise ValueError("RED_NEUTRAL_TASK_CHAIN")
    if source.count("clearAll()") < 5:
        raise ValueError("RED_NEUTRAL_CLEANUP")
    # Prevent stale Player attribute signals after LocalScript is destroyed.
    if source.count("featureOffConnection:Disconnect()") != 1 or (
        source.count("reducedEffectsConnection:Disconnect()") != 1
        or "featureOffConnection = nil" not in source
        or "reducedEffectsConnection = nil" not in source
        or source.index("featureOffConnection:Disconnect()") < source.index("script.Destroying:Connect")
        or source.index("reducedEffectsConnection:Disconnect()") < source.index("script.Destroying:Connect")
    ):
        raise ValueError("RED_NEUTRAL_PLAYER_SIGNAL_LIFECYCLE")

class NeutralShadowsTests(unittest.TestCase):
    def test_contract(self):
        validate(SRC.read_text(encoding="utf8"))
    def test_mutants(self):
        src = SRC.read_text(encoding="utf8")
        changes = [
            ('if TOUCH then 6 else 10', 'if TOUCH then 60 else 100'),
            ('if TOUCH then 55 else 72', 'if TOUCH then 550 else 720'),
            ('if TOUCH then 0.95 else 0.75', 'if TOUCH then 0.01 else 0.01'),
            ('RESCAN_SECONDS = 3.8','RESCAN_SECONDS = 0'),
            ('MIN_GROUND_NORMAL = 0.72','MIN_GROUND_NORMAL = -1'),
            ('SHADOW_TRANSPARENCY = 0.73','SHADOW_TRANSPARENCY = 0'),
            ('typeof(species) == "string"', 'true'),
            ('humanoid.Health > 0','humanoid.Health >= 0'),
            ('math.min(MAX_SHADOWS, #nearby)', '#nearby'),
            ('ray.IgnoreWater = false','ray.IgnoreWater = true'),
            ('ray.RespectCanCollide = true','ray.RespectCanCollide = false'),
            ('CFrame.fromMatrix(', 'CFrame.new('),
            ('Vector3.new(0, 0, 1):Cross(groundNormal).Unit', 'Vector3.new(1,0,0)'),
            ('groundNormal * 0.035', 'Vector3.new(0, 1, 0) * 0.035'),
            ('hit.Material == Enum.Material.Water','hit.Material == Enum.Material.Neon'),
            ('disc.CanCollide = false','disc.CanCollide = true'),
            ('disc.CanQuery = false','disc.CanQuery = true'),
            ('disc.Transparency = SHADOW_TRANSPARENCY','disc.Transparency = 0'),
            ('script.Destroying:Connect','script.Changed:Connect'),
            ('task.delay(UPDATE_SECONDS, tick)','tick()'),
            ('PLAYER:GetAttributeChangedSignal(REDUCED_EFFECTS)', 'PLAYER:GetAttributeChangedSignal("Bad")'),
            ('if not selected[model] then', 'if selected[model] then'),
            ('for _, entry in ipairs(chosen) do', 'for _, entry in ipairs(discovered) do'),
            ('table.insert(chosen, {model = entry.model, root = entry.root, hit = hit})', 'selected[entry.model] = false'),
            ('GQ470_CONTACT_SHADOW_HARD_PART_BUDGET_V2', 'GQ470_BROKEN_BUDGET'),
            ('featureOffConnection:Disconnect()', 'featureOffConnection = nil'),
            ('reducedEffectsConnection:Disconnect()', 'reducedEffectsConnection = nil'),
        ]
        for old, new in changes:
            self.assertIn(old, src)
            with self.subTest(new=new), self.assertRaises(ValueError):
                validate(src.replace(old, new))
        for added in ("RemoteEvent:FireServer()", "RunService.Heartbeat:Connect(function() end)"):
            with self.assertRaises(ValueError):
                validate(src+"\n"+added+"\n")

if __name__ == "__main__":
    unittest.main()
