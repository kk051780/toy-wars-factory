"""Fail-closed source-level game-art budget and true health-loss provenance.
This does not measure visual quality, Studio playback or Android FPS.
"""
from pathlib import Path
import json
import re
import unittest

SOURCE = Path(__file__).resolve().parent / "EGGRUMBLE_LocalDamageCue.client.luau"


def validate(source: str) -> None:
    code = "\n".join(row.split("--", 1)[0] for row in source.splitlines())
    required = (
        "GQ470_FB015_TRUE_LOCAL_DAMAGE_CUE_REAL69_20261121",
        'Instance.new("ColorCorrectionEffect")',
        'effect.Name = EFFECT_NAME',
        'local COOLDOWN_SECONDS = 0.30',
        'local MAX_CUE_SECONDS = 0.24',
        'local MAX_DAMAGE_TINT = 20',
        'effect.TintColor = Color3.fromRGB(255, 255 - tintStrength, 255 - tintStrength)',
        'math.min(MAX_DAMAGE_TINT, math.floor(9 + fraction * 36))',
        'local lost = previousHealth - currentHealth',
        'previousHealth = currentHealth',
        'if lost > 0.25 then',
        'humanoid.HealthChanged:Connect',
        'humanoid.Died:Connect(disconnectCharacter)',
        'if token ~= generation or humanoid.Health <= 0 or currentHealth <= 0 then',
        'PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true',
        'PLAYER.CharacterRemoving:Connect',
        'PLAYER.CharacterAdded:Connect(bindCharacter)',
        'damageConnection:Disconnect()',
        'diedConnection:Disconnect()',
        'currentTween:Cancel()',
        'effect.Enabled = false',
        'effect.Saturation = -0.06',
        'effect.Brightness = -0.008',
        'task.delay(MAX_CUE_SECONDS + 0.01',
        'if ticket == pulseTicket then',
    )
    for item in required:
        if item not in code:
            raise ValueError("RED_DAMAGE_CUE_MISSING_" + item)
    forbidden = (
        'FireServer', 'InvokeServer', 'RemoteEvent', 'RemoteFunction',
        'DataStoreService', 'MarketplaceService', 'TakeDamage',
        'Humanoid.Health =', 'SetNetworkOwner', 'ReplicatedStorage',
        'RunService', 'RenderStepped', 'Heartbeat', 'Stepped',
        'while true', 'while task.wait', 'ScreenGui', 'BillboardGui',
        'ParticleEmitter', 'PointLight', 'BloomEffect', 'BlurEffect',
        'Enum.Material.Neon', 'Instance.new("Part")',
        'Instance.new("WedgePart")', 'Instance.new("ColorCorrectionEffect",',
    )
    for word in forbidden:
        if word in code:
            raise ValueError("RED_DAMAGE_CUE_FORBIDDEN_" + word)
    if code.count('Instance.new("ColorCorrectionEffect")') != 1:
        raise ValueError("RED_DAMAGE_CUE_MULTIPLE_COLOR_EFFECT_FACTORIES")
    numbers = {
        "COOLDOWN_SECONDS": "0.30",
        "MAX_CUE_SECONDS": "0.24",
        "MAX_DAMAGE_TINT": "20",
    }
    for name, value in numbers.items():
        if not re.search(r"(?m)^local " + name + r" = " + re.escape(value) + r"$", code):
            raise ValueError("RED_DAMAGE_CUE_BUDGET_" + name)
    if len(source.encode()) > 9500:
        raise ValueError("RED_DAMAGE_CUE_OVERSIZED_CLIENT_SCRIPT")


class LocalTrueDamageCueSourceQA(unittest.TestCase):
    def test_real_source_gate(self):
        validate(SOURCE.read_text(encoding="utf8"))

    def test_runtime_studio_matrix_stays_honest_until_actual_evidence(self):
        m = json.loads((SOURCE.parent / "STUDIO_RETEST_MATRIX.json").read_text(encoding="utf8"))
        self.assertEqual(m["base_formal_head"],
                         "e80973c354f14a0d0088577f3cc1a875454f0f8f")
        self.assertEqual(m["comparison_old_new_pc_android_32"], "0/32")
        self.assertEqual(m["art_gate"], "ART_NO_GO")
        self.assertEqual(m["gameplay_gate"], "PRODUCT_NO_GO")
        self.assertFalse(m["owner_accepted"])
        self.assertEqual(m["studio_solo"], "NOT_TESTED")
        self.assertEqual(m["studio_two_client"], "NOT_TESTED")
        self.assertEqual(m["low_end_android_15min"], "NOT_TESTED")
        self.assertEqual(len(m["runtime_scenarios"]), 10)
        self.assertEqual(len({s["id"] for s in m["runtime_scenarios"]}), 10)
        self.assertTrue(all(s["status"] == "NOT_TESTED"
                            for s in m["runtime_scenarios"]))
        self.assertEqual(m["mobile_targets"]["median_fps_min"], 30)
        self.assertEqual(m["mobile_targets"]["p10_fps_min"], 25)
        self.assertEqual(m["human_art_targets"]["pc_score_min"], 4.5)
        self.assertEqual(m["human_art_targets"]["android_score_min"], 4.0)

    def test_mutations_fail_closed(self):
        baseline = SOURCE.read_text(encoding="utf8")
        changes = [
            ('local COOLDOWN_SECONDS = 0.30', 'local COOLDOWN_SECONDS = 0'),
            ('local MAX_CUE_SECONDS = 0.24', 'local MAX_CUE_SECONDS = 3'),
            ('local MAX_DAMAGE_TINT = 20', 'local MAX_DAMAGE_TINT = 100'),
            ('local lost = previousHealth - currentHealth', 'local lost = currentHealth - previousHealth'),
            ('previousHealth = currentHealth', '-- previousHealth = currentHealth'),
            ('if lost > 0.25 then', 'if lost >= 0 then'),
            ('humanoid.HealthChanged:Connect', 'humanoid:GetPropertyChangedSignal("WalkSpeed"):Connect'),
            ('humanoid.Died:Connect(disconnectCharacter)', 'humanoid.Died:Connect(function() end)'),
            ('PLAYER.CharacterRemoving:Connect', 'PLAYER.AncestryChanged:Connect'),
            ('PLAYER.CharacterAdded:Connect(bindCharacter)', 'PLAYER.CharacterAdded:Connect(function() end)'),
            ('damageConnection:Disconnect()', 'damageConnection = nil'),
            ('diedConnection:Disconnect()', 'diedConnection = nil'),
            ('currentTween:Cancel()', 'currentTween = nil'),
            ('effect.Enabled = false', 'effect.Enabled = true'),
            ('effect.Brightness = -0.008', 'effect.Brightness = 1'),
            ('effect.Saturation = -0.06', 'effect.Saturation = 1'),
            ('if lost > 0.25 then', 'if true then'),
            ('PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true', 'false'),
            ('task.delay(MAX_CUE_SECONDS + 0.01', 'task.delay(999'),
            ('if ticket == pulseTicket then', 'if true then'),
        ]
        for before, after in changes:
            self.assertIn(before, baseline)
            with self.subTest(mutant=after), self.assertRaises(ValueError):
                validate(baseline.replace(before, after))
        for injection in ('\nRemoteEvent:FireServer()\n',
                          '\nInstance.new("Part")\n',
                          '\nRunService.Heartbeat:Connect(function() end)\n'):
            with self.assertRaises(ValueError):
                validate(baseline + injection)


if __name__ == "__main__":
    unittest.main()
