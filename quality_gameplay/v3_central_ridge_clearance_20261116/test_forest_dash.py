"""Original-author source-only TEAM Forest/DASH clearance negative/provenance tests."""
from pathlib import Path
import tempfile
import unittest
from patch_ridge import HOST,ITEMS,OLD as RIDGE_OLD,NEW as RIDGE_NEW
from forest_dash_overlay import OLD_FOREST,NEW_FOREST,forest_report,patch_forest
from forest_dash_native import inspect,extract_forest,extract_item_list,write_vm

class ForestDashSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=HOST.read_text(encoding="utf-8")
        cls.item=ITEMS.read_text(encoding="utf-8")
        cls.ridge=cls.author.replace(RIDGE_OLD,RIDGE_NEW)+"\n-- CastleDefense.start(session)\n"
        cls.forest=patch_forest(cls.ridge,cls.author,cls.item)

    def test_01_reproduces_only_tree_1_original_collision(self):
        report=forest_report()
        self.assertEqual(report["before_embedded_tree_ids"],[1])
        self.assertEqual(report["after_embedded_tree_ids"],[])
        self.assertEqual(report["tree_1_before"],(-762,470))
        self.assertEqual(report["tree_1_after"],(-762,488))
        self.assertTrue(report["other_tree_positions_preserved"])
        self.assertFalse(report["roblox_studio_verified"])

    def test_02_exactly_one_immutable_author_hunk(self):
        self.assertEqual(self.author.count(OLD_FOREST),1)
        self.assertEqual(self.ridge.count(OLD_FOREST),1)
        self.assertEqual(self.forest.count(NEW_FOREST),1)
        self.assertEqual(self.forest.replace(NEW_FOREST,OLD_FOREST),self.ridge)
        self.assertEqual(self.forest.count(RIDGE_NEW),1)

    def test_03_reject_repeat_application(self):
        with self.assertRaisesRegex(ValueError,"already patched"):
            patch_forest(self.forest,self.author,self.item)

    def test_04_refuse_mutated_author_blob(self):
        with self.assertRaisesRegex(ValueError,"author blob changed"):
            patch_forest(self.ridge,self.author+" ",self.item)

    def test_05_refuse_missing_existing_ridge(self):
        with self.assertRaisesRegex(ValueError,"ridge"):
            patch_forest(self.author+"\n-- CastleDefense.start(session)",self.author,self.item)

    def test_06_refuse_missing_original_castle_hook(self):
        with self.assertRaisesRegex(ValueError,"castle hook"):
            patch_forest(self.author.replace(RIDGE_OLD,RIDGE_NEW),self.author,self.item)

    def test_07_refuse_moved_original_DASH_item(self):
        with self.assertRaisesRegex(ValueError,"pickup site"):
            patch_forest(self.ridge,self.author,
                self.item.replace('x=-140,z=470,kind="DASH"','x=-130,z=470,kind="DASH"'))

    def test_08_reject_different_tree_position_source(self):
        with self.assertRaisesRegex(ValueError,"TREE scope drift"):
            patch_forest(self.ridge.replace(OLD_FOREST,
                "   local z=465+math.floor(n/4)*110"),self.author,self.item)

    def test_09_real_forest_loop_and_site_table_extracted(self):
        old,new,itemlist,itempos=inspect(self.author,self.ridge,self.forest,self.item)
        self.assertIn("ForestAmbushCover_",old)
        self.assertIn(OLD_FOREST,old)
        self.assertIn(NEW_FOREST,new)
        self.assertIn('{x=-140,z=470,kind="DASH"}',itemlist)
        self.assertIn("table.insert(points,origin+Vector3.new",itempos)

    def test_10_generate_native_luau_using_exact_original_sources(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            files=[d/s for s in ("original.luau","ridge.luau","forest.luau",
                                  "raid.luau","real_native.luau")]
            for f,src in zip(files[:4],(self.author,self.ridge,self.forest,self.item)):
                f.write_text(src,encoding="utf-8")
            write_vm(*files)
            body=files[4].read_text(encoding="utf-8")
            self.assertEqual(body.count(OLD_FOREST),1)
            self.assertEqual(body.count(NEW_FOREST),1)
            self.assertIn("GQ520_FOREST_DASH_COLLISION_NEGATIVE_PASS",body)
            self.assertIn("before_TEAM_2 ridge_only_1 ridge_forest_0",body)

    def test_11_refuse_unrelated_author_script_mutation(self):
        with self.assertRaisesRegex(ValueError,"another source hunk"):
            inspect(self.author,self.ridge,self.forest+"\n-- changed unrelated battle",self.item)

    def test_12_full_7_tree_count_and_latin_square_unchanged(self):
        old,new,table,_=inspect(self.author,self.ridge,self.forest,self.item)
        self.assertEqual(old.count("for n=1,7 do"),1)
        self.assertEqual(new.count("for n=1,7 do"),1)
        self.assertEqual(table.count('kind="'),9)
        self.assertEqual(table.count('kind="DASH"'),3)
        self.assertEqual(table.count('kind="SHIELD"'),3)
        self.assertEqual(table.count('kind="HEAL"'),3)

if __name__=="__main__":unittest.main()
