from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from compose_melee_candidate import GAME, HERE, SOURCE_BLOB, git_blob, main, patch

class NeutralMeleeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=(GAME/"EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")

    def test_original_blob_is_immutable(self):
        assert git_blob(self.original.encode("utf-8"))==SOURCE_BLOB

    def test_one_owner_one_damage_path_and_no_new_game(self):
        candidate=patch(self.original)
        assert candidate.count("function Swarm.start(session:any)")==1
        assert candidate.count("nearest.humanoid:TakeDamage(Melee.DAMAGE)")==1
        assert candidate.count("local Melee=require(")==1
        assert "lastMeleeSwing" in candidate and "lastVictimHit" in candidate
        # Lifetime contract: no strong-key references to destroyed soldiers or old avatars.
        assert candidate.count('setmetatable({}, {__mode="k"}) :: any')==2
        assert "   live[m]=nil\n   lastMeleeSwing[m]=nil\n" in candidate
        assert candidate.count("lastMeleeSwing[m]=nil")==1
        assert "local lastMeleeSwing:{[Model]:number}={}" not in candidate
        assert "local lastVictimHit:{[Humanoid]:number}={}" not in candidate
        assert "Melee.MAX_RAYS_PER_TICK" in candidate
        assert "session.rules.phase==\"ACTIVE\"" in candidate
        assert "RespectCanCollide=true" in candidate
        assert "workspace:Raycast(from,delta,params)==nil" in candidate
        assert "for id,actor in pairs(session.botActors or {})" in candidate
        assert "Players:GetPlayers()" in candidate
        assert 'p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode' in candidate
        assert "if castle and castle.alive" in candidate

    def test_original_body_untouched_before_on_the_fly_patch(self):
        before=(GAME/"EGGRUMBLE_SwarmCombat.luau").read_bytes()
        patch(before.decode())
        self.assertEqual(before,(GAME/"EGGRUMBLE_SwarmCombat.luau").read_bytes())

    def test_source_drift_fail_closed(self):
        self.assertRaises(ValueError,patch,self.original.replace(
            "local lastBotHit:{[string]:number}={}",
            "local lastBotHit={}",1))
        self.assertRaises(ValueError,patch,self.original.replace(
            "local ImpactFeedback=require(script.Parent:WaitForChild(\"EGGRUMBLE_ImpactFeedback\"))",
            "local ImpactFeedback=nil",1))

    def test_project_and_rollback_source_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            main(out)
            receipt=json.loads((out/"SOURCE_LOCK.json").read_text())
            project=json.loads((out/"EGGRUMBLE_GQ_NEUTRAL_MELEE.project.json").read_text())
            service=project["tree"]["ServerScriptService"]
            self.assertFalse(receipt["official_RC_integrated"])
            self.assertFalse(receipt["studio_tested"])
            self.assertEqual(receipt["source_parent"], SOURCE_BLOB)
            self.assertEqual(receipt["scripts"],22)
            self.assertEqual(service["EGGRUMBLE_SwarmCombat"]["$path"],"EGGRUMBLE_SwarmCombat.luau")
            self.assertEqual(service["EGGRUMBLE_NeutralMeleePolicy"]["$path"],"EGGRUMBLE_NeutralMeleePolicy.luau")
            self.assertEqual((out/"EGGRUMBLE_NeutralMeleePolicy.luau").read_bytes(),
                (HERE/"EGGRUMBLE_NeutralMeleePolicy.luau").read_bytes())
            self.assertEqual(len(service),21)  # includes $className; 20 real server scripts
            self.assertTrue((out/"EGGRUMBLE_SwarmCombat.luau").is_file())

if __name__=="__main__":
    unittest.main()
