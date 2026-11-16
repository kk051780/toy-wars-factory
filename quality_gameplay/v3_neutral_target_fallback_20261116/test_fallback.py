"""Source-exact and negative tests for #533's nearest-target fallback only."""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from compose_fallback import OLD, NEW, apply, emit, sha256

ROOT = Path(__file__).resolve().parents[2]
OWNER_COMPOSER = ROOT / "quality_gameplay/neutral_melee_pressure_20261116/compose_melee_candidate.py"
OWNER_COMPOSER_BLOB = "032c4de1560a4f5396b06905fcdc3bcd0b764975"
ORIGINAL_SWARM = ROOT / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SwarmCombat.luau"
ORIGINAL_SWARM_BLOB = "fea147ac51411e626b410d172aad5cd72615bd45"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def original_composed() -> str:
    assert git_blob(OWNER_COMPOSER.read_bytes()) == OWNER_COMPOSER_BLOB, "RED #533 composer drift"
    assert git_blob(ORIGINAL_SWARM.read_bytes()) == ORIGINAL_SWARM_BLOB, "RED #482 author drift"
    spec = importlib.util.spec_from_file_location("gq533_owner", OWNER_COMPOSER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.patch(ORIGINAL_SWARM.read_text(encoding="utf-8"))

def choose_model(rows: list[tuple[float,bool,bool]], budget: int) -> tuple[int | None,int]:
    """Pure negative model: (distance, ready, unblocked); returns selected index, rays."""
    rays = 0
    for original_id, (dist, ready, unblocked) in sorted(enumerate(rows), key=lambda p:p[1][0]):
        if rays >= budget:
            break
        if dist > 4.25 or not ready:
            continue
        rays += 1
        if unblocked:
            return original_id, rays
    return None, rays

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = original_composed()

    def test_full_existing_author_real_source_one_hunk(self):
        fixed = apply(self.owner)
        self.assertEqual(self.owner.count(OLD), 1)
        self.assertEqual(fixed.count(OLD), 0)
        self.assertEqual(fixed.count(NEW), 1)
        self.assertEqual(fixed.replace(NEW, OLD, 1), self.owner)
        self.assertEqual(fixed.count("local Melee=require("), 1)
        self.assertEqual(fixed.count("victim.humanoid:TakeDamage(Melee.DAMAGE)"), 1)
        self.assertIn("lastMeleeSwing[m]=nil", fixed)

    def test_second_unblocked_target_after_first_cooldown(self):
        self.assertEqual(choose_model([(1.0,False,True),(2.0,True,True)], 24), (1,1))

    def test_second_unblocked_target_after_first_wall(self):
        self.assertEqual(choose_model([(1.0,True,False),(2.0,True,True)], 24), (1,2))

    def test_per_tick_global_ray_budget(self):
        self.assertEqual(choose_model([(1.0,True,False),(2.0,True,True)], 1), (None,1))
        self.assertEqual(choose_model([(1.0,True,False),(2.0,True,True)], 2), (1,2))
        self.assertEqual(choose_model([(1.0,False,True),(2.0,False,True)], 24), (None,0))

    def test_out_of_range_never_hits(self):
        self.assertEqual(choose_model([(5.0,True,True)], 24), (None,0))

    def test_author_drift_rejected(self):
        with self.assertRaises(ValueError):
            apply(self.owner.replace("nearest.humanoid:TakeDamage(Melee.DAMAGE)", "nearest.humanoid.Health-=4"))
        with self.assertRaises(ValueError):
            apply(self.owner.replace("lastMeleeSwing[m]=nil", "-- deleted", 1))
        with self.assertRaises(ValueError):
            apply(apply(self.owner))

    def test_emit_exact_input_lock_and_rollback(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d)/"original.luau"
            out = Path(d)/"candidate.luau"
            inp.write_text(self.owner, encoding="utf-8")
            before = inp.read_bytes()
            with self.assertRaises(ValueError):
                emit(inp,"0"*64,out)
            self.assertFalse(out.exists())
            receipt = emit(inp,sha256(before),out)
            self.assertEqual(inp.read_bytes(),before)
            self.assertEqual(out.read_text(encoding="utf-8"),apply(self.owner))
            self.assertFalse(receipt["formal_rc_adopted"])
            with self.assertRaises(ValueError):
                emit(inp,sha256(before),out)
            with self.assertRaises(ValueError):
                emit(inp,sha256(before),inp)

if __name__=="__main__":
    unittest.main()
