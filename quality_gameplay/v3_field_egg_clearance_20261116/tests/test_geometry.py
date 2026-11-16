import importlib.util
import math
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
SRC=BASE/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
MOD=pathlib.Path(__file__).resolve().parents[1]/"patch_field_eggs.py"
spec=importlib.util.spec_from_file_location("egg_clearance",MOD)
fix=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)

def castles(mode):
    result=[]
    for index in range(1,17):
        if mode=="TEAM":
            red=index%2==1
            local=(index-1)//2
            col=local%2
            row=local//2
            x=(-885+col*124) if red else (-475+col*124)
            z=260+row*146
        else:
            col=(index-1)%4
            row=(index-1)//4
            x=620+(col-1.5)*122
            z=280+row*112
        result.append((x,z))
    return result

def eggs(mode, rows):
    center=-620 if mode=="TEAM" else 620
    return [(center+((i-1)%8-3.5)*93, rows[(i-1)//8]) for i in range(1,25)]

def count_overlaps(mode,positions):
    collisions=[]
    for i,(x,z) in enumerate(positions,1):
        for idx,(cx,cz) in enumerate(castles(mode),1):
            if abs(x-cx)<36+1.3 and abs(z-cz)<36+1.65:
                collisions.append((i,idx))
    return collisions

def item_sites(mode):
    center=-620 if mode=="TEAM" else 620
    return [(center+x,z) for x,z in [
        (-140,300),(0,300),(140,300),(140,470),(-140,470),(0,470),
        (0,640),(140,640),(-140,640)]]

class FieldEggSourceAndGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=SRC.read_bytes()
        cls.author=cls.original.decode("utf-8")
        cls.patched=fix.patch(cls.author)

    def test_source_hash_locked(self):
        self.assertEqual(fix.blob_sha(self.original),fix.ORIGINAL_HOST_BLOB)

    def test_original_geometry_is_actual_source_not_invented(self):
        for token in [
            "MODE_SEATS=16",
            "if isRed then -885+col*124 else -475+col*124",
            "260+row*146",
            "local base=root+Vector3.new(620,2,0)",
            "(col-1.5)*122,0,280+row*112",
            'Vector3.new(72,3,72)',
            "worldX+(col-3.5)*93,3,290+row*200",
            "for i=1,24 do",
            'local eggId="FIELD_"..i',
        ]:
            self.assertIn(token,self.author)

    def test_original_castle_overlap_is_reproduced_not_guessed(self):
        self.assertEqual(len(count_overlaps("TEAM",eggs("TEAM",[290,490,690]))),8)
        self.assertEqual(len(count_overlaps("BATTLE_ROYALE",eggs("BATTLE_ROYALE",[290,490,690]))),4)

    def test_new_rows_have_no_castle_foundation_overlap_in_both_modes(self):
        for mode,rows in [("TEAM",[338,506,610]),("BATTLE_ROYALE",[338,448,676])]:
            with self.subTest(mode=mode):
                self.assertEqual(count_overlaps(mode,eggs(mode,rows)),[])
                self.assertEqual(len(set(eggs(mode,rows))),24)

    def test_each_row_and_every_egg_within_real_floor(self):
        for mode,rows in [("TEAM",[338,506,610]),("BATTLE_ROYALE",[338,448,676])]:
            center=-620 if mode=="TEAM" else 620
            for x,z in eggs(mode,rows):
                self.assertLess(abs(x-center)+1.3,445)
                self.assertLess(abs(z-465)+1.65,525)
            self.assertEqual(len(set(rows)),3)

    def test_original_item_stations_not_collocated_or_prompt_overlap(self):
        for mode,rows in [("TEAM",[338,506,610]),("BATTLE_ROYALE",[338,448,676])]:
            dist=min(math.hypot(ex-ix,ez-iz)
                     for ex,ez in eggs(mode,rows) for ix,iz in item_sites(mode))
            self.assertGreater(dist,22.0,mode)

    def test_team_ridge_tree_and_valley_no_egg_intersection(self):
        spots=eggs("TEAM",[338,506,610])
        # Center ridge actual x=-620 +/-27, z=475 +/-95, plus egg half-width.
        for x,z in spots:
            self.assertFalse(abs(x+620)<27+1.3 and abs(z-475)<95+1.65)
            self.assertFalse(abs(x+610)<42.5+1.3 and abs(z-695)<15+1.65)
        for idx in range(1,8):
            tx=-800+(idx%4)*38
            tz=470+(idx//4)*110
            for x,z in spots:
                self.assertFalse(abs(x-tx)<3.5+1.3 and abs(z-tz)<3.5+1.65)

    def test_only_one_original_game_host_diff_two_small_hunks(self):
        self.assertEqual(self.patched.replace(fix.ROWS_LINE,"",1).replace(fix.REPLACEMENT_LINE,fix.ORIGINAL_LINE,1),self.author)
        self.assertEqual(self.patched.count("for i=1,24 do"),1)
        self.assertEqual(self.patched.count('local eggId="FIELD_"..i'),1)
        self.assertEqual(self.patched.count("Rules.takeFieldEgg("),self.author.count("Rules.takeFieldEgg("))
        self.assertIn(fix.ROWS_LINE,self.patched)
        self.assertIn(fix.REPLACEMENT_LINE,self.patched)

    def test_double_patch_denied(self):
        with self.assertRaisesRegex(AssertionError,"already patched"):
            fix.patch(self.patched)

    def test_moved_author_anchor_denied(self):
        with self.assertRaises(AssertionError):
            fix.patch(self.author.replace("290+row*200","291+row*200",1))

    def test_negative_original_overlap_if_unsafe_rows_reintroduced(self):
        for mode in ["TEAM","BATTLE_ROYALE"]:
            rows=[290,490,690]
            self.assertGreater(len(count_overlaps(mode,eggs(mode,rows))),0)

    def test_eggs_not_owned_by_other_system(self):
        # Both the FIELD egg token authority and the field/item spawn authority remain original.
        originalRules=(BASE/"EGGRUMBLE_CastleMatchRules.luau").read_text()
        originalItem=(BASE/"EGGRUMBLE_FieldItemPickups.luau").read_text()
        self.assertIn("M.DEFAULT_FIELD_EGGS=24",originalRules)
        self.assertIn('m.fieldEggTokens["FIELD_"..i]=true',originalRules)
        self.assertIn('function Items.start',originalItem)
        self.assertNotIn("RemoteEvent",fix.ROWS_LINE)

if __name__=="__main__":
    unittest.main()
