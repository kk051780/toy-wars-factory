"""Regression QA for a single shared Swarm: #494 owns pacing, #501 owns fairness."""
import importlib.util
import os
import pathlib
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
MODULE=ROOT/"tools/compose_dual28.py"
SPEC=importlib.util.spec_from_file_location("dual28",MODULE)
DUAL=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DUAL)

class DualOverlayContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pacing=pathlib.Path(os.environ["P0D_GQ494_COMPOSER"]).resolve(strict=True)
        cls.author=pathlib.Path(os.environ["P0D_V3_ORIGINAL_SWARM"]).resolve(strict=True)
        spec=importlib.util.spec_from_file_location("gq494",cls.pacing)
        cls.parent=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.parent)
        cls.src=cls.author.read_text(encoding="utf-8")

    def test_exact_original_494_patch_not_rewritten(self):
        p=self.parent.patch_swarm(self.src)
        both=DUAL.patch_fair_on_paced(p)
        self.assertNotEqual(self.src,p)
        self.assertNotEqual(p,both)
        for token in ("SpawnPacing.step(","SpawnPacing.new(","local function credit(",
                      "h.Died:Connect(","ImpactFeedback.ko(","local function addEnemy(",
                      "local function strike(","session.rules.phase=="):
            self.assertEqual(p.count(token),both.count(token),token)
        self.assertIn('and session.rules.castles[id].alive then',both)
        self.assertNotIn('local SPAWN_BATCH=5',both)
        self.assertIn("MAX_LOS_RAYS_PER_ATTACK=48",both)
        self.assertEqual(both.count("EncounterFair.chooseIndex("),1)
        self.assertEqual(both.count("table.insert(kinds,\"HUMAN\")"),1)
        self.assertEqual(both.count("table.insert(kinds,\"BOT\")"),1)
        self.assertEqual(both.count("EncounterFair.clear("),1)
        self.assertIn('local candidates,kinds=aliveTargets()',both)
        self.assertIn("return a,kinds",both)

    def test_private_overlay_refuses_stale_pacer_or_duplicate_authority(self):
        p=self.parent.patch_swarm(self.src)
        with self.assertRaises(AssertionError):
            DUAL.patch_fair_on_paced(p.replace('SpawnPacing.step(','SpawnPacing.noLongerSupported(',1))
        with self.assertRaises(AssertionError):
            DUAL.patch_fair_on_paced(p.replace('local candidates=aliveTargets()', 'local candidates={}',1))
        with self.assertRaises(AssertionError):
            DUAL.patch_fair_on_paced(p.replace('and session.rules.castles[id].alive then','and true then'))
        with self.assertRaises(AssertionError):
            DUAL.patch_fair_on_paced(p.replace('local SPAWN_BATCH=5', 'local SPAWN_BATCH=5\n',1) + '\nlocal SPAWN_BATCH=5')

    def test_dual_manifest_real_original26_remains_untouched(self):
        base=pathlib.Path(os.environ["P0D_GQ_ORIGINAL26_PROJECT"]).resolve(strict=True)
        pace_policy=pathlib.Path(os.environ["P0D_GQ494_POLICY"]).resolve(strict=True)
        fair=ROOT/"EGGRUMBLE_NeutralEncounterFairness.luau"
        with tempfile.TemporaryDirectory() as td:
            out=pathlib.Path(td)/"GQ_NEUTRAL28.project.json"
            proof=DUAL.compose(base,self.author,self.pacing,pace_policy,fair,out)
            self.assertEqual(proof["total_mapped"],28)
            self.assertEqual(proof["unchanged_original26"],25)
            self.assertEqual(proof["overlaid_original26"],1)
            self.assertEqual(proof["originals"],26)
            self.assertEqual(len(proof["mapped_sha256"]),28)
            a=DUAL.flat(base)[1];b=DUAL.flat(out)[1]
            self.assertEqual(set(b)-set(a),{("ServerScriptService","EGGRUMBLE_NeutralSpawnPacing"),
                                            ("ServerScriptService","EGGRUMBLE_NeutralEncounterFairness")})
            for key in set(a)-{("ServerScriptService","EGGRUMBLE_SwarmCombat")}:
                self.assertEqual(a[key].read_bytes(),b[key].read_bytes())
            with self.assertRaises(AssertionError):
                DUAL.compose(base,self.author,self.pacing,pace_policy,fair,out)

if __name__=="__main__":
    unittest.main()
