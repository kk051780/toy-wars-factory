import pathlib
import runpy
import unittest
from difflib import unified_diff

ROOT=pathlib.Path(__file__).resolve().parents[1]
COMPOSE=ROOT/"tools/compose_private27.py"
SWARM=pathlib.Path("_v3_original/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SwarmCombat.luau")

class PrivateOverlay(unittest.TestCase):
    def setUp(self):
        self.function=runpy.run_path(str(COMPOSE))["patch_swarm"]

    def test_original_swarm_preserved_except_explicit_hook(self):
        if not SWARM.exists():self.skipTest("pinned original author checkout needed")
        original=SWARM.read_text(encoding="utf-8")
        patched=self.function(original)
        self.assertEqual(original.count("local LIMIT=110"),1)
        for token in ("local LIMIT=110","local SPAWN_TICK=.18","local SPAWN_BATCH=5",
            "MAX_LOS_RAYS_PER_ATTACK=48","ImpactFeedback.ko(","ImpactFeedback.hit(",
            'p:SetAttribute("EGGRUMBLE_NeutralKOs",n)',
            'task.wait(.38)'):
            self.assertEqual(original.count(token),patched.count(token),token)
        for owner in ("function Swarm.start(session:any)","local function addEnemy(at:Vector3)",
                      "local function strike("):
            self.assertEqual(original.count(owner),patched.count(owner))
        self.assertEqual(patched.count("EncounterFair.chooseIndex"),1)
        self.assertEqual(patched.count('table.insert(kinds,"HUMAN")'),1)
        self.assertEqual(patched.count('table.insert(kinds,"BOT")'),1)
        self.assertIn("return a,kinds",patched)
        self.assertIn('if selected==nil then break end',patched)
        self.assertIn('EncounterFair.clear(encounterFairState)',patched)
        delta=list(unified_diff(original.splitlines(),patched.splitlines()))
        self.assertLess(len(delta),95,"overbroad implementation drift")
        self.assertNotIn("SetAsync",patched)
        self.assertNotIn("DataStore",patched)

    def test_stale_author_fails_closed(self):
        if not SWARM.exists():self.skipTest("pinned author needed")
        original=SWARM.read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            self.function(original.replace("local SPAWN_TICK=.18","local SPAWN_TICK=.17").replace(
                'local target=candidates[math.random(1,#candidates)]',
                'local target=candidates[1]'))
        with self.assertRaises(AssertionError):
            self.function(original.replace(
                "-- EGGRUMBLE V3: standalone lightweight neutral-horde combat controller.",
                "-- UNKNOWN HOST"))

    def test_strict_source_span_only(self):
        source=COMPOSE.read_text(encoding="utf-8")
        self.assertIn('"original_scripts_exact_unchanged":25',source)
        self.assertIn('assert len(new)==27',source)
        self.assertIn('NONOWNER_MUTATION',source)
        self.assertIn('"BASE_26_HASH_DRIFT"',source)
        self.assertIn('author.read_bytes()',source)
        self.assertIn('"NOT_MERGED"',source)

if __name__=="__main__":unittest.main()
