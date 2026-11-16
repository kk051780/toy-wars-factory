"""New #533 isolated tests applied to #494+#501 AUTHOR source, never copy their code."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from compose_melee_candidate import patch
from compose_triple29 import compose, flatten, ORIGINAL, POLICY

class Triple29Contract(unittest.TestCase):
    def test_reject_missing_fairness_or_pacing(self):
        # Original #482 has no #494/#501 combined hook. Must RED fail if used
        # instead of the original 28-author composer.
        p=Path(__file__).resolve().parents[2]/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SwarmCombat.luau"
        original=p.read_text(encoding="utf-8")
        self.assertNotIn("SpawnPacing.step(",original)
        self.assertNotIn("EncounterFair.chooseIndex(",original)

    @unittest.skipUnless(os.environ.get("GQ_TRIPLE28_BASE"),"Needs exact upstream private28 fixture")
    def test_real_upstream_28_to_29_and_mutant(self):
        base=Path(os.environ["GQ_TRIPLE28_BASE"])
        author=Path(os.environ["GQ_TRIPLE_ORIGINAL_SWARM"])
        policy=Path(__file__).resolve().parent/"EGGRUMBLE_NeutralMeleePolicy.luau"
        data,paths=flatten(base)
        self.assertEqual(len(paths),28)
        source=paths[ORIGINAL].read_text(encoding="utf-8")
        mutant=source.replace("EncounterFair.chooseIndex(","EncounterFair.disabled(",1)
        self.assertNotIn("EncounterFair.chooseIndex(",mutant)
        with tempfile.TemporaryDirectory() as td:
            project=Path(td)/"triple29.project.json"
            receipt=compose(base,author,project,policy)
            self.assertEqual(receipt["preserved28_sources_exact"],27)
            self.assertEqual(receipt["total_count"],29)
            after, new=flatten(project)
            self.assertEqual(set(new)-set(paths),{POLICY})
            self.assertEqual(new[ORIGINAL].read_text().count("SpawnPacing.step("),1)
            self.assertEqual(new[ORIGINAL].read_text().count("EncounterFair.chooseIndex("),1)
            self.assertEqual(new[ORIGINAL].read_text().count("candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"),1)
            self.assertIn('p:GetAttribute("EGGRUMBLE_QueuedMode")==session.mode',new[ORIGINAL].read_text())
            self.assertFalse(receipt["official_rc_adopted"])
            self.assertFalse(receipt["owner_accepted"])
            with self.assertRaises(AssertionError):
                compose(base,author,project,policy) # never overwrite
            for k in set(paths)-{ORIGINAL}:
                self.assertEqual(new[k].read_bytes(),paths[k].read_bytes())
            self.assertEqual(new[POLICY].read_bytes(),policy.read_bytes())

if __name__=="__main__":unittest.main()
