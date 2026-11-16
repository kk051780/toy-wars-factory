import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/"EGGRUMBLE_NeutralEncounterFairness.luau"
class NonOverlapContract(unittest.TestCase):
 def test_real_policy_not_memo(self):
  s=SOURCE.read_text(encoding="utf-8")
  for clause in ["function Fair.chooseIndex(", "Fair.MIN_HUMAN_SHARE = 0.40",
   "state.epoch ~= epoch", 'return nil, "NO_LIVE_HUMAN"', "state.humanCursor", "state.botCursor", "return Fair"]:
   self.assertIn(clause,s)
 def test_no_competing_game_authority(self):
  s=SOURCE.read_text(encoding="utf-8")
  for forbidden in ["Instance.new(", "TakeDamage(", "SetAttribute(", "SetAsync(", "RemoteEvent", "DataStore", "task.spawn(", "workspace", "Players:GetPlayers", "SWARM_RANGE"]:
   self.assertNotIn(forbidden,s)
 def test_scope_is_unique(self):
  names=sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file())
  self.assertEqual(names,["EGGRUMBLE_NeutralEncounterFairness.luau","README.md","tests/native_cases.luau","tests/test_contract.py","tools/build_native_harness.py"])
 def test_native_cases_cover_real_targets_and_epoch(self):
  s=(ROOT/"tests/native_cases.luau").read_text(encoding="utf-8")
  for evidence in ["sample(1,15,100)","sample(8,8,100)","sample(16,0,100)","ROUND_2","Fair.clear(s)"]:
   self.assertIn(evidence,s)
if __name__=="__main__": unittest.main()
