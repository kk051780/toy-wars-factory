"""Source-level contract sanity tests, not Roblox Studio gameplay proof."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
bridge=(ROOT/"src/EliteKOBridge.luau").read_text(encoding="utf-8")
rule=(ROOT/"src/GateRules.luau").read_text(encoding="utf-8")
README=(ROOT/"README.md").read_text(encoding="utf-8")
class SourceContract(unittest.TestCase):
    def test_read_only_adapter(self):
        self.assertIn("function EliteKOBridge.capture(horde)",bridge)
        self.assertIn("function EliteKOBridge.didConfirmEliteKO(horde, receipt)",bridge)
        self.assertNotIn("FireServer(",bridge)
        self.assertNotIn("RemoteEvent.new",bridge)
    def test_match_epoch_guard(self):
        self.assertIn("horde.round ~= receipt.round",bridge)
        self.assertIn("mob == receipt.elite",bridge)
        self.assertIn("mob.hp ~= 0",bridge)
    def test_single_elite_and_liveness(self):
        self.assertIn("if elite ~= nil",bridge)
        self.assertIn("elite.hp <= 0",bridge)
        self.assertIn("mob.deadUntil <= 0",bridge)
    def test_visual_not_damage(self):
        v=(ROOT/"src/GateVisual.luau").read_text(encoding="utf-8")
        self.assertIn("door.CanCollide = not open",v)
        self.assertNotIn("TakeDamage",v)
    def test_gate_idempotence(self):
        self.assertIn("self.triggered or self.phase",rule)
        self.assertIn('"WAIT_CLEAR"',rule)
    def test_no_false_claim_of_playable_shortcut(self):
        self.assertIn("does **not** build or validate the bypass",README)
if __name__ == "__main__":
    unittest.main()
