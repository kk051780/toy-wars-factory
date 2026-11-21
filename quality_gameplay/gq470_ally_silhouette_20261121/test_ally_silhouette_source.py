"""GQ470 teammate-only silhouette source gate; NOT a real Studio/Android test."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_AllySilhouette.client.luau"

def validate(source: str) -> None:
    code = "\n".join(line.split("--", 1)[0] for line in source.splitlines())
    if "GQ470_FB015_ALLY_SILHOUETTE_REAL69_20261121" not in source:
        raise ValueError("RED_ALLY_SILHOUETTE_MISSING_FEATURE_MARKER")
    required = (
        'local MAX_ALLIES = 3',
        'local MAX_DISTANCE = 45',
        'local SCAN_INTERVAL = 0.75',
        'local OUTLINE_TRANSPARENCY = 0.68',
        'player.Team ~= localTeam or player.Neutral',
        'player == LOCAL_PLAYER',
        'character:GetAttribute("AssassinCloaked") == true',
        'character:GetAttribute("EGGRUMBLE_Stealthed") == true',
        'head.Transparency >= 0.35',
        'head.LocalTransparencyModifier >= 0.35',
        'character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")',
        'torso.Transparency >= 0.35',
        'torso.LocalTransparencyModifier >= 0.35',
        'humanoid.Health <= 0',
        'distance > MAX_DISTANCE',
        'Instance.new("Highlight")',
        'effect.DepthMode = Enum.HighlightDepthMode.Occluded',
        'effect.FillTransparency = 1',
        'effect.OutlineTransparency = OUTLINE_TRANSPARENCY',
        'effect.Adornee = candidate.character',
        'player.TeamColor.Color:Lerp',
        'LOCAL_PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true',
        'LOCAL_PLAYER:GetAttribute(DISABLE_ATTRIBUTE) == true',
        'Players.PlayerRemoving:Connect(clear)',
        'LOCAL_PLAYER.CharacterRemoving:Connect(clearAll)',
        'effect:Destroy()',
        'task.wait(SCAN_INTERVAL)',
        'math.min(MAX_ALLIES, #candidates)',
        'if not keep[player] then',
        'clearAll()',
    )
    for item in required:
        if item not in code:
            raise ValueError("RED_ALLY_SILHOUETTE_MISSING_" + item)
    forbidden = (
        "FireServer", "InvokeServer", "RemoteEvent", "RemoteFunction",
        "DataStoreService", "MarketplaceService", "TakeDamage",
        "Humanoid.Health =", "SetNetworkOwner", "ReplicatedStorage",
        "RunService", "RenderStepped", "Heartbeat", "BindToRenderStep",
        'Instance.new("Part")', 'Instance.new("ScreenGui")',
        'Instance.new("BillboardGui")', 'Enum.HighlightDepthMode.AlwaysOnTop',
        'Instance.new("ParticleEmitter")', "TweenService",
    )
    for item in forbidden:
        if item in code:
            raise ValueError("RED_ALLY_SILHOUETTE_FORBIDDEN_" + item)
    if code.count('Instance.new("Highlight")') != 1:
        raise ValueError("RED_ALLY_SILHOUETTE_MULTIPLE_FACTORIES")
    for name, value in (("MAX_ALLIES", "3"), ("MAX_DISTANCE", "45"),
                        ("SCAN_INTERVAL", "0.75"),
                        ("OUTLINE_TRANSPARENCY", "0.68")):
        if not re.search(r"(?m)^local " + name + r" = " + re.escape(value) + "$", code):
            raise ValueError("RED_ALLY_SILHOUETTE_BUDGET_" + name)
    if len(source.encode("utf-8")) > 9000:
        raise ValueError("RED_ALLY_SILHOUETTE_SOURCE_SIZE")

class SourceGate(unittest.TestCase):
    def test_author_source(self):
        validate(SOURCE.read_text(encoding="utf-8"))

    def test_exact_feature_and_sole_runtime_route(self):
        from compose_official70 import BASE, FEATURE, ROUTE, B_PACKET, TARGET, COMPETING_CREST_ROUTE
        self.assertEqual(BASE, "e80973c354f14a0d0088577f3cc1a875454f0f8f")
        self.assertEqual(FEATURE, "GQ470_FB015_ALLY_SILHOUETTE_REAL69_20261121")
        self.assertEqual(ROUTE, "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AllySilhouette")
        self.assertEqual(TARGET, "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AllySilhouette.client.luau")
        self.assertEqual(B_PACKET, "B220_ALLY_SILHOUETTE_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL")
        self.assertEqual(COMPETING_CREST_ROUTE, "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerTeamCrest")
        composer = (ROOT / "compose_official70.py").read_text(encoding="utf-8")
        self.assertIn('require(COMPETING_CREST_ROUTE not in original_map, "COMPETING_PR976_AVATAR_CREST_ROUTE")', composer)
        self.assertIn('"exclusive_alternative_route": COMPETING_CREST_ROUTE', composer)
        self.assertIn('"exclusive_alternative_pr": 976', composer)
        self.assertIn('manifest["exclusive_alternative_route"] == COMPETING_CREST_ROUTE', composer)
        self.assertIn('manifest["exclusive_alternative_pr"] == 976', composer)
        self.assertIn(FEATURE, SOURCE.read_text(encoding="utf-8"))
        
    def test_no_faked_runtime_proof(self):
        m = json.loads((ROOT / "STUDIO_RETEST_MATRIX.json").read_text(encoding="utf-8"))
        self.assertEqual(m["base_formal_head"], "e80973c354f14a0d0088577f3cc1a875454f0f8f")
        self.assertEqual(m["comparison_old_new_pc_android_32"], "0/32")
        self.assertEqual(m["studio_solo"], "NOT_TESTED")
        self.assertEqual(m["studio_two_client"], "NOT_TESTED")
        self.assertEqual(m["low_end_android_15min"], "NOT_TESTED")
        self.assertFalse(m["owner_accepted"])
        self.assertEqual(m["art_gate"], "ART_NO_GO")
        alt = m["visual_alternative_selection"]
        self.assertEqual(alt["rule"], "EXCLUSIVE_ONE_OR_NEITHER_AFTER_HUMAN_STUDIO_ANDROID_ART_GATE")
        self.assertEqual(alt["option_975"]["pr"], 975)
        self.assertEqual(alt["option_976"]["pr"], 976)
        self.assertEqual(alt["option_975"]["status"], "NOT_TESTED")
        self.assertEqual(alt["option_976"]["status"], "NOT_TESTED")
        self.assertIsNone(alt["winner"])
        self.assertIsNone(alt["option_975"]["median_fps"])
        self.assertIsNone(alt["option_976"]["median_fps"])
        for variant in ("option_975", "option_976"):
            self.assertIsNone(alt[variant]["pc_human_score"])
            self.assertIsNone(alt[variant]["android_human_score"])
            self.assertIsNone(alt[variant]["artifact"])
        self.assertEqual(len(m["runtime_scenarios"]), 10)
        self.assertTrue(all(s["status"] == "NOT_TESTED" for s in m["runtime_scenarios"]))

    def test_fail_closed_mutations(self):
        source = SOURCE.read_text(encoding="utf-8")
        replacements = [
            ("MAX_ALLIES = 3", "MAX_ALLIES = 15"),
            ("MAX_DISTANCE = 45", "MAX_DISTANCE = 1000"),
            ("SCAN_INTERVAL = 0.75", "SCAN_INTERVAL = 0.001"),
            ("OUTLINE_TRANSPARENCY = 0.68", "OUTLINE_TRANSPARENCY = 0"),
            ("player.Team ~= localTeam or player.Neutral", "player.Team == localTeam or player.Neutral"),
            ("player == LOCAL_PLAYER", "player ~= LOCAL_PLAYER"),
            ('character:GetAttribute("AssassinCloaked") == true', "false"),
            ('character:GetAttribute("EGGRUMBLE_Stealthed") == true', "false"),
            ("head.Transparency >= 0.35", "head.Transparency >= 1.0"),
            ("head.LocalTransparencyModifier >= 0.35", "false"),
            ('character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")', 'character:FindFirstChild("HumanoidRootPart")'),
            ("torso.Transparency >= 0.35", "false"),
            ("torso.LocalTransparencyModifier >= 0.35", "false"),
            ("humanoid.Health <= 0", "humanoid.Health < 0"),
            ("distance > MAX_DISTANCE", "distance < MAX_DISTANCE"),
            ('Instance.new("Highlight")', 'Instance.new("Part")'),
            ("Enum.HighlightDepthMode.Occluded", "Enum.HighlightDepthMode.AlwaysOnTop"),
            ("effect.FillTransparency = 1", "effect.FillTransparency = 0"),
            ("effect.Adornee = candidate.character", "effect.Adornee = workspace"),
            ("effect:Destroy()", "effect.Enabled = false"),
            ("math.min(MAX_ALLIES, #candidates)", "#candidates"),
            ("task.wait(SCAN_INTERVAL)", "task.wait()"),
            ("Players.PlayerRemoving:Connect(clear)", "Players.PlayerRemoving:Connect(function() end)"),
            ("LOCAL_PLAYER.CharacterRemoving:Connect(clearAll)", "LOCAL_PLAYER.CharacterRemoving:Connect(function() end)"),
            ("if not keep[player] then", "if false then"),
            ("clearAll()", "discardAll()"),
        ]
        for before, after in replacements:
            self.assertIn(before, source)
            with self.subTest(mutant=after), self.assertRaises(ValueError):
                validate(source.replace(before, after))
        for extra in ("\nRunService.Heartbeat:Connect(function() end)",
                      "\nRemoteEvent:FireServer()",
                      '\nInstance.new("BillboardGui")'):
            with self.assertRaises(ValueError):
                validate(source + extra)
if __name__ == "__main__":
    unittest.main()
