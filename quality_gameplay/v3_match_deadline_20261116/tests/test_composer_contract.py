"""Negative source tests for the existing-author 26->27 integration adapter."""
from pathlib import Path
import importlib.util
import unittest

MOD_PATH = Path(__file__).resolve().parents[1] / "tools/compose_private_27.py"
spec = importlib.util.spec_from_file_location("deadline_composer", MOD_PATH)
comp = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(comp)

HOST_STUB = '''
local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))
local function startSession(mode:string)
 session.closeRound=function() end
 session.refresh=function()
  ResultService.showIfFinished(session,queue,mode)
  RoundReplay.schedule(session,session.closeRound)
 end
 Rules.start(session.rules)
end
'''

SCORE_STUB = '''
local ranking=ScoreBalance.build(session.rules,session.swarm and session.swarm.kills or {})
if session.resultsDelivered then return false end
local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"
'''

class SourceSelectiveAdapterTest(unittest.TestCase):
    def test_host_uses_existing_result_replay_after_expire(self):
        patched = comp.patch_host(HOST_STUB)
        self.assertEqual(patched.count("DeadlinePolicy.expire("), 1)
        self.assertEqual(patched.count("session.refresh()"), 1)
        self.assertIn('sessions[mode]==session', patched)
        self.assertIn('session.rules.phase=="ACTIVE"', patched)
        self.assertIn('DeadlinePolicy.new(os.clock(),deadlineId)', patched)

    def test_host_rejects_wrong_author_base(self):
        with self.assertRaises(AssertionError):
            comp.patch_host(HOST_STUB.replace(' Rules.start(session.rules)', ' Rules.start(other.rules)'))

    def test_host_rejects_duplicate_timer_injection(self):
        modified = comp.patch_host(HOST_STUB)
        with self.assertRaises(AssertionError):
            comp.patch_host(modified)

    def test_score_keeps_real_score_and_draw_non_winner(self):
        patched = comp.patch_result(SCORE_STUB)
        self.assertIn('local ranking=ScoreBalance.build(', patched)
        self.assertIn('session.rules.winner=="DRAW" then "引き分け"', patched)
        self.assertEqual(patched.count('local status='), 1)

    def test_score_rejects_wrong_owner_script(self):
        with self.assertRaises(AssertionError):
            comp.patch_result(SCORE_STUB.replace("ScoreBalance.build", "AnotherScore.build"))

    def test_regression_future_start_semantics(self):
        with self.assertRaises(AssertionError):
            comp.patch_host(HOST_STUB.replace("session.refresh=function()", "session.someOtherRefresh=function()"))

if __name__=="__main__":
    unittest.main()
