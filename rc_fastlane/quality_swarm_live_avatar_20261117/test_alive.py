"""GQ8 dead-avatar target fence: focused regressions and current31 optional binding."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from select_alive import BEFORE, AFTER, SWARM, patch, unpatch, scoped, scan, compare

SAMPLE = """--!strict
 local function aliveTargets():{Vector3}
  local a={}
  for _,p in ipairs(Players:GetPlayers()) do
   local c=session.rules.castles[tostring(p.UserId)]
   if c and c.alive then
    local ch=p.Character
    local root=ch and ch:FindFirstChild("HumanoidRootPart")::BasePart?
    if root then table.insert(a,root.Position) end
   end
  end
  for id,m in pairs(session.botActors or {}) do
   local c=session.rules.castles[id]
   if c and c.alive and m.Parent and m.PrimaryPart then table.insert(a,m.PrimaryPart.Position) end
  end
  return a
 end
-- following code remains unchanged
"""

class TargetSafety(unittest.TestCase):
    def test_source_exact_inverse(self):
        updated=patch(SAMPLE)
        self.assertEqual(unpatch(updated),SAMPLE)
        self.assertEqual(updated.count("humanoid.Health>0"),1)
        self.assertIn("for id,m in pairs(session.botActors or {})",updated)

    def test_dead_avatar_fence_is_not_bot_fence(self):
        updated=patch(SAMPLE)
        self.assertEqual(updated.split("  for id,m in pairs")[1],SAMPLE.split("  for id,m in pairs")[1])
        self.assertIn("if root and humanoid and humanoid.Health>0",scoped(updated))

    def test_double_application_red(self):
        with self.assertRaisesRegex(ValueError,"ALREADY_APPLIED"):
            patch(patch(SAMPLE))

    def test_stale_mutated_anchor_red(self):
        with self.assertRaisesRegex(ValueError,"ANCHOR"):
            patch(SAMPLE.replace(BEFORE,BEFORE.replace("if root then","if root and true then")))

    def test_no_fake_swarm_function_red(self):
        with self.assertRaisesRegex(ValueError,"FUNCTION_DRIFT"):
            patch(SAMPLE.replace("aliveTargets","aliveTargetz"))

    def test_no_castle_membership_red(self):
        with self.assertRaisesRegex(ValueError,"CASTLE_OWNER"):
            patch(SAMPLE.replace("local c=session.rules.castles[tostring(p.UserId)]","local c=true"))

    def test_non31_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"project.json"
            p.write_text(json.dumps({"tree":{"ServerScriptService":{"EGGRUMBLE_SwarmCombat":{"$path":"none.luau"}}}}))
            with self.assertRaisesRegex((ValueError,FileNotFoundError),""):
                scan(p)

    def test_actual_selected31_if_ci_provided(self):
        path=os.environ.get("GQ8_LIVE_BASE31")
        if not path:
            self.skipTest("actual31 is tested by official V3 PR workflow")
        base=Path(path)
        _,files=scan(base)
        orig=files[SWARM].read_text(encoding="utf-8")
        new=patch(orig)
        self.assertEqual(unpatch(new),orig)
        self.assertEqual(orig.count(BEFORE),1)
        self.assertNotEqual(orig,new)
        self.assertNotIn("humanoid.Health>0 then table.insert(a,root.Position)",orig)

if __name__=="__main__":
    unittest.main()
