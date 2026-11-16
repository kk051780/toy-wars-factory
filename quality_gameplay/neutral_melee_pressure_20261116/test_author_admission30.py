"""Review-gated original #528/#531 cross-owner admission, no duplicate runtime."""
import json,os,tempfile,unittest
from pathlib import Path
from compose_author_admission30 import compose,flatten,HOST,BOT,ORIGINAL,BUDGET

class Admission30SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        needed=["GQ_BASE29_PROJECT","GQ_AUTHOR528_COMPOSER",
                "GQ_AUTHOR531_COMPOSER","GQ_AUTHOR528_POLICY"]
        if not all(os.environ.get(k) for k in needed):
            raise unittest.SkipTest("Requires SHA pinned exact original author 29 private stage")
        cls.base=Path(os.environ[needed[0]])
        cls.mod528=Path(os.environ[needed[1]])
        cls.mod531=Path(os.environ[needed[2]])
        cls.policy=Path(os.environ[needed[3]])

    def test_original_writer_source_exact_and_shared_callbacks(self):
        old,mapped=flatten(self.base)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ADMISSION30.project.json"
            receipt=compose(self.base,self.mod528,self.mod531,self.policy,p)
            new,files=flatten(p)
            self.assertEqual(len(mapped),29)
            self.assertEqual(len(files),30)
            self.assertEqual(set(files)-set(mapped),{BUDGET})
            self.assertEqual(receipt["previous_byte_exact_count"],26)
            self.assertEqual(receipt["source_count"],30)
            for key in set(mapped)-{HOST,BOT,ORIGINAL}:
                self.assertEqual(mapped[key].read_bytes(),files[key].read_bytes(),key)
            host=files[HOST].read_text()
            bot=files[BOT].read_text()
            swarm=files[ORIGINAL].read_text()
            self.assertEqual(host.count("session.isCurrentHuman=function"),1)
            self.assertEqual(bot.count("session.isCurrentHuman(player)"),1)
            self.assertEqual(bot.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)"),1)
            self.assertEqual(swarm.count("session.isCurrentHuman(p)"),2)
            self.assertEqual(swarm.count("EncounterFair.chooseIndex("),1)
            self.assertEqual(swarm.count("SpawnPacing.step("),1)
            self.assertEqual(swarm.count("candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"),1)
            self.assertEqual(swarm.count("session.neutralBudget:acquire("),1)
            self.assertIn('lastMeleeSwing[m]=nil',swarm)
            self.assertIn('setmetatable({}, {__mode="k"}) :: any',swarm)
            self.assertEqual(host.count("gqDualBudget=GQDualBudget.new("),1)
            self.assertFalse(receipt["rc_adopted"])
            self.assertFalse(receipt["studio_tested"])
            self.assertFalse(receipt["owner_accepted"])
            with self.assertRaises(AssertionError):
                compose(self.base,self.mod528,self.mod531,self.policy,p)

    def test_fail_closed_mutant_missing_original_author_hook(self):
        from compose_author_admission30 import load_file,once
        mod=load_file(self.mod531,"admission30_true_owner")
        self.assertRaises(ValueError,mod.replace_exact,"session=nil",mod.HOST_BEFORE,mod.HOST_AFTER,"host")
        self.assertRaises(ValueError,once,"local a=1","local b=2","x","drift")
        # Mutant removes the real original #531 server callback, rejection is mandatory.
        with self.assertRaises(ValueError):
            once("if p.Parent then end",'session.isCurrentHuman~=nil and session.isCurrentHuman(p)',"true","human_guard")
if __name__=="__main__":unittest.main()
