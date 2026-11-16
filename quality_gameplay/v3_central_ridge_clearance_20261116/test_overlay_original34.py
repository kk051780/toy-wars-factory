"""34-source original author's one-hunk-only overlay behavior; no other writer edits."""
import unittest
from patch_ridge import HOST, ITEMS, OLD, NEW
from overlay_original34 import patch34

class RidgeOnExisting34Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=HOST.read_text(encoding="utf-8")
        cls.item=ITEMS.read_text(encoding="utf-8")
        cls.host=(cls.author+"\n -- CastleAccessRamp original #484\n"
         +" -- CastleDefense.start(session) original #500\n"
         +" -- session.castleDefenseStop() original #500\n")

    def test_01_one_block_only_retains_every_original_hunk(self):
        actual=patch34(self.host,self.author,self.item)
        self.assertEqual(actual.count(NEW),1)
        self.assertEqual(actual.count(OLD),0)
        self.assertEqual(actual.replace(NEW,OLD),self.host)
        for text in ("CastleAccessRamp","CastleDefense.start(session)",
          "session.castleDefenseStop()","EGGRUMBLE_NeutralStoneGiant",
          "EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_RaidItemIntake"):
            self.assertEqual(actual.count(text),self.host.count(text))

    def test_02_refuse_missing_castle_owner_hook(self):
        with self.assertRaisesRegex(ValueError,"CastleDefense.start"):
            patch34(self.author,self.author,self.item)

    def test_03_refuse_second_application(self):
        once=patch34(self.host,self.author,self.item)
        with self.assertRaisesRegex(ValueError,"already patched"):
            patch34(once,self.author,self.item)

    def test_04_refuse_wrong_original_host(self):
        with self.assertRaises((ValueError,AssertionError)):
            patch34(self.host,self.author+" ",self.item)

    def test_05_refuse_moved_item(self):
        with self.assertRaises((ValueError,AssertionError)):
            patch34(self.host,self.author,self.item.replace(
              'x=0,z=470,kind="SHIELD"','x=30,z=470,kind="SHIELD"'))

    def test_06_preserves_all_other_gameplay_source_bytes(self):
        actual=patch34(self.host,self.author,self.item)
        self.assertEqual(self.host[:self.host.index(OLD)],actual[:actual.index(NEW)])
        self.assertEqual(self.host[self.host.index(OLD)+len(OLD):],
          actual[actual.index(NEW)+len(NEW):])

if __name__=="__main__":unittest.main()
