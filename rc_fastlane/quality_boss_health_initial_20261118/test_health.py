"""Real-source regression for one existing boss Script. No fabricated source fixtures."""
import os
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import select_health as s

class BossInitialHealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=os.environ.get("GQ8_ORIGINAL_BOSS")
        author=os.environ.get("GQ8_GQ518_PATCH")
        if not original or not author:
            raise RuntimeError("RED: pinned original boss and original GQ518 patch required")
        cls.original=Path(original).read_bytes()
        cls.author=Path(author)
        cls.base=s.base_518(cls.original,cls.author)
        cls.on=s.apply(cls.base)

    def test_original_blob_is_exact(self):
        self.assertEqual(s.blob_sha(self.original),s.ORIGINAL_BLOB)

    def test_initial_hp_exists_before_first_hit(self):
        self.assertEqual(self.on.count(b' model:SetAttribute("EGGRUMBLE_BossHealth",health)'),1)
        self.assertLess(
            self.on.index(b' model:SetAttribute("EGGRUMBLE_BossHealth",health)'),
            self.on.index(b' local function damageFrom('))
        self.assertIn(b" local health=900\n",self.on)

    def test_previously_accepted_boss_wall_occlusion_unchanged(self):
        for anchor in (b"shockwaveClear(c,root)", b"params.RespectCanCollide=true",
                       b"h:TakeDamage(28)", b"MIN_HIT_INTERVAL=.22"):
            self.assertEqual(self.base.count(anchor),self.on.count(anchor))

    def test_old_blob_is_exactly_recovered_when_flag_off(self):
        self.assertEqual(s.undo(self.on),self.base)
        s.verify(self.base,self.on)
        self.assertEqual(len(self.on)-len(self.base),len(s.REPLACEMENT)-len(s.ANCHOR))

    def test_no_extra_gameplay_owners(self):
        for anchor in (b"function Boss.spawn(",b"local function damageFrom(",
                       b"function Boss.new(",b"RemoteEvent",b"DataStoreService"):
            self.assertEqual(self.base.count(anchor),self.on.count(anchor))

    def test_duplicate_apply_is_red(self):
        with self.assertRaisesRegex(ValueError,"anchor changed"):
            s.apply(self.on)

    def test_old_or_tampered_parent_is_red(self):
        with self.assertRaisesRegex(ValueError,"blob drift"):
            s.base_518(self.original+b" ",self.author)
        with self.assertRaisesRegex(ValueError,"anchor changed"):
            s.apply(self.base.replace(s.ANCHOR,b" local health=100\n local active=true\n"))

    def test_bad_off_rollback_is_red(self):
        with self.assertRaisesRegex(ValueError,"cannot reverse"):
            s.undo(self.base)

if __name__=="__main__":
    unittest.main()
