"""Mutation-style coverage for static tracing; results are NOT an engine diagnosis."""
import unittest
from p0_spawn_visibility_trace import audit_script, strip_comment, PATTERNS, EXPECTED_BASE

class SpawnSourceTraceContract(unittest.TestCase):
    def test_real66_protocol_base_pin(self):
        self.assertEqual(len(EXPECTED_BASE), 40)
        self.assertEqual(len(PATTERNS), 13)

    def test_comments_never_trigger_spawn_diagnosis(self):
        self.assertEqual(audit_script("-- CharacterAutoLoads = false\n-- LoadCharacter()"), [])
        self.assertEqual(strip_comment("local x = 1 -- PlayerAdded:Connect"), "local x = 1 ")

    def test_actual_spawn_tokens_are_safely_counted(self):
        cases = {
            "game.Players.CharacterAutoLoads = false": "character_auto_loads",
            "player:LoadCharacter()": "explicit_load_character",
            "player.CharacterAdded:Connect(function(c) end)": "character_added",
            "workspace.CurrentCamera.CameraSubject = humanoid": "camera_subject",
            "workspace.CurrentCamera.CameraType = Enum.CameraType.Scriptable": "camera_type",
            "part.LocalTransparencyModifier = 1": "transparency_modifier",
            "mySpawn.PivotTo(CFrame.new())": "manual_spawn_teleport",
        }
        for text, category in cases.items():
            with self.subTest(category=category):
                self.assertIn(category, [r["category"] for r in audit_script(text)])

    def test_do_not_confuse_health_trajectories_with_visibility(self):
        self.assertEqual(audit_script("humanoid.Health = 0"), [])
        self.assertEqual(audit_script("player.Character = nil"), [])
        self.assertEqual(audit_script("return nil"), [])

    def test_line_number_is_real_and_sanitized(self):
        actual=audit_script("local a=1\nplayer:LoadCharacter()\n-- player:LoadCharacter()")
        self.assertEqual(actual, [{"line":2,"category":"explicit_load_character"}])
        self.assertNotIn("text", actual[0])

if __name__=="__main__":
    unittest.main()
