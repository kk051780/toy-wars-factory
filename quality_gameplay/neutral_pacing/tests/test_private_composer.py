import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"tools/compose_private_v3.py"
SPEC=importlib.util.spec_from_file_location("p0d_compose",MODULE)
COMPOSE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPOSE)

class TestPrivateComposer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author_checkout=Path(os.environ["P0D_V3_AUTHOR_CHECKOUT"]).resolve(strict=True)
        cls.author_dir=Path(os.environ["P0D_V3_AUTHOR_ROOT"]).resolve(strict=True)
        cls.swarm=(cls.author_dir/"EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")

    def test_patch_is_one_existing_swarm_no_second_engine(self):
        before=self.swarm
        after=COMPOSE.patch_swarm(before)
        self.assertEqual(after.count("local function credit("),1)
        self.assertEqual(after.count("h.Died:Connect("),1)
        self.assertEqual(after.count("SpawnPacing.step("),1)
        self.assertEqual(after.count("local function addEnemy("),1)
        self.assertIn('session.swarm=api',after)
        self.assertIn('Damage',after)
        self.assertIn('math.max(0,(elapsed-SPAWN_TICK)*1000)',after)
        self.assertNotIn('math.min(SPAWN_BATCH,LIMIT-n)',after)
        self.assertNotEqual(after,before)

    def test_neutral_death_credit_excludes_finished_round_or_fallen_owner(self):
        after=COMPOSE.patch_swarm(self.swarm)
        lines=after.splitlines()
        guarded='   if type(id)=="string" and session.rules.phase=="ACTIVE"'
        owner='    and session.rules.castles[id] and session.rules.castles[id].alive then'
        self.assertEqual(lines.count(guarded),1)
        self.assertEqual(lines.count(owner),1)
        self.assertEqual(lines[lines.index(guarded)+1],owner)
        self.assertEqual(after.count("h.Died:Connect("),1)
        self.assertEqual(after.count("ImpactFeedback.ko("),1)
        self.assertEqual(lines.count("    credit(id)"),1)
        self.assertLess(lines.index(owner),lines.index("    credit(id)"))
        # Source-only negative eligibility matrix; real Studio is separate.
        for phase,alive,expected in (
            ("ACTIVE",True,True),("ACTIVE",False,False),
            ("FINISHED",True,False),("ABANDONED",True,False)):
            self.assertEqual(phase=="ACTIVE" and alive,expected)

    def test_mismatched_author_source_fails_closed(self):
        corrupt=self.swarm.replace('local SPAWN_BATCH=5','local SPAWN_BATCH=6')
        with self.assertRaises(AssertionError):
            COMPOSE.patch_swarm(corrupt)
        corrupt=self.swarm.replace("session.swarm=api","session.swarm=nil")
        with self.assertRaises(AssertionError):
            COMPOSE.patch_swarm(corrupt)

    def test_end_to_end_21_input_22_output_with_original_sha(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp)/"private_22"
            receipt=COMPOSE.compose(self.author_dir,self.author_checkout,stage)
            self.assertEqual(receipt["author_head"],COMPOSE.AUTHOR_HEAD)
            self.assertEqual(receipt["previous_author_sources"],21)
            self.assertEqual(receipt["new_total_sources"],22)
            self.assertEqual(receipt["original_sources_byte_exact"],20)
            self.assertEqual(sum(1 for v in receipt["originals"].values() if v["changed"]),1)
            project=json.loads((stage/"EGGRUMBLE_V3_NEUTRAL_PACING.project.json").read_text(encoding="utf-8"))
            m=COMPOSE.entries(project)
            self.assertEqual(len(m),22)
            original=json.loads((self.author_dir/"EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))
            old=COMPOSE.entries(original)
            self.assertEqual(set(old)|{("ServerScriptService","EGGRUMBLE_NeutralSpawnPacing")},set(m))
            for key,source_path in old.items():
                existing=(self.author_dir/source_path).read_bytes()
                new=(stage/m[key]).read_bytes()
                if key[-1]!="EGGRUMBLE_SwarmCombat":
                    self.assertEqual(new,existing,key)
            self.assertIn(b'Pacing.MAX_ALIVE = 110',(stage/"source/EGGRUMBLE_NeutralSpawnPacing.luau").read_bytes())
            with self.assertRaises(AssertionError):
                COMPOSE.compose(self.author_dir,self.author_checkout,stage)

if __name__=="__main__":
    unittest.main()
