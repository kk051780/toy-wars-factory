"""Fail-closed tests for the *actual* author source anchor, no game-source overwrite."""
import unittest
from cross_domain_gate.repair_empty_match import OLD, NEW, apply

ORIGINAL = '''  session.closeRound=function()
   if sessions[mode]~=session or session.rules.phase~="FINISHED" then return end
   sessions[mode]=nil
   queues[mode]={}
   queueEpoch[mode]+=1
  end
  local abandoned=RoundReplay.abandonIfEmpty(scene,joined,function()
    scene.closeRound(true)
  end)
'''

class EmptyHumanRecoveryTest(unittest.TestCase):
    def test_exactly_one_source_change(self):
        patched = apply(ORIGINAL)
        self.assertEqual(patched.replace(NEW, OLD), ORIGINAL)
        self.assertIn('abandoned~=true', patched)
        self.assertIn('joined[live.UserId]==mode', patched)
        self.assertIn('session.rules.phase~="ACTIVE"', patched)

    def test_old_callback_is_preserved(self):
        patched = apply(ORIGINAL)
        self.assertIn('scene.closeRound(true)', patched)

    def test_new_synthetic_author_head_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "anchor drift"):
            apply(ORIGINAL.replace(OLD, '  session.closeRound=function()\n'))

    def test_doubled_host_callback_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "anchor drift"):
            apply(ORIGINAL.replace(OLD, OLD * 2))

    def test_missing_original_disconnect_call_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "caller/cleanup changed"):
            apply(ORIGINAL.replace('scene.closeRound(true)', 'scene.closeRound()'))

    def test_cleanup_must_exist(self):
        with self.assertRaisesRegex(ValueError, "caller/cleanup changed"):
            apply(ORIGINAL.replace('queueEpoch[mode]+=1', 'queueEpoch[mode]+=2'))

if __name__ == "__main__":
    unittest.main()
