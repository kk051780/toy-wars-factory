import unittest
from cross_domain_gate.compose_observed import (
    patch,REQUIRE_ANCHOR,REQUIRE_INJECT,START_ANCHOR,START_INJECT
)
HOST = '''local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))
  SwarmCombat.start(session)
  scene.closeRound(true)
  if session.rules.phase=="ACTIVE" then return end
'''
class ShadowAttachTest(unittest.TestCase):
    def test_two_insertions_only(self):
        result=patch(HOST)
        self.assertEqual(result.replace(REQUIRE_INJECT,"").replace(START_INJECT,""),HOST)
        self.assertIn("IntegrityObserver.inspect",result)
        self.assertIn('task.wait(5)',result)
        self.assertIn('scene.closeRound(true)',result)
    def test_double_apply_rejected(self):
        with self.assertRaisesRegex(ValueError,"already integrated"):
            patch(patch(HOST))
    def test_missing_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError,"source drift"):
            patch(HOST.replace(START_ANCHOR,""))
    def test_lifecycle_removal_rejected(self):
        with self.assertRaisesRegex(ValueError,"lifecycle"):
            patch(HOST.replace("scene.closeRound(true)","scene.closeRound()"))
if __name__=="__main__":
    unittest.main()
