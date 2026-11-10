from pathlib import Path
import unittest
source=(Path(__file__).resolve().parents[1]/'luau/GoroganAttackReceiptWindow.luau').read_text()
class ReceiptSourceTests(unittest.TestCase):
    def test_core_result_only(self):self.assertIn('cmd.kind~="STOMP_RESOLVE"',source)
    def test_round_guard(self):self.assertIn('cmd.roundId~=roundId',source)
    def test_event_guard(self):self.assertIn('cmd.eventId~=eventId',source)
    def test_attack_bounds(self):self.assertIn('cmd.attackId>3',source)
    def test_attest(self):self.assertIn('function Window:attests',source)
    def test_no_network(self):self.assertNotIn('OnServerEvent',source)
    def test_ephemeral_cleanup(self):self.assertIn('self.active=nil',source)
    def test_center_from_core(self):self.assertIn('Vector3.new(cmd.center.x,cmd.center.y,cmd.center.z)',source)
