#!/usr/bin/env python3
"""Read-only source geometry checks; NOT Roblox Studio or native Luau."""
import hashlib, math, re, unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "src/H1FunWorld_SKY_CASTLE_TEST.server.luau"
EXPECTED = "1955d51a1fb4d1d59639e93aa8d72b909acfe64d790ea8e81ea2f41161f17768"
PAT = re.compile(r'path\("(SKY_FORT_[A-Z_]+)",Vector3.new\(([^)]*)\),Vector3.new\(([^)]*)\),(\d+),')

def collect(src):
    return {n:(tuple(float(z) for z in a.split(",")),
               tuple(float(z) for z in b.split(",")),float(w))
            for n,a,b,w in PAT.findall(src)}

class SkySource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=FILE.read_bytes()
        cls.src=cls.raw.decode("utf-8")
        cls.paths=collect(cls.src)

    def test_exact_frozen_source(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),EXPECTED)
    def test_studio_only(self):
        self.assertIn("if not RunService:IsStudio() then",self.src)
    def test_one_world(self):
        self.assertEqual(self.src.count('local world=Instance.new("Folder")'),1)
        self.assertIn('assert(not arena:FindFirstChild("H1_FUN_WORLD")',self.src)
    def test_four_paths(self):
        self.assertEqual(set(self.paths),{"SKY_FORT_ENTRY_RED","SKY_FORT_ENTRY_BLUE",
                                         "SKY_FORT_ESCAPE_RED","SKY_FORT_ESCAPE_BLUE"})
    def test_no_second_authority(self):
        for s in ("OnServerEvent","DataStoreService","FireServer","TeleportService"):
            self.assertNotIn(s,self.src)
    def test_all_free(self):
        self.assertIn('p:SetAttribute("FreeToAllRoles",true)',self.src)
    def test_island_collidable(self):
        self.assertIn('local fort=box("FLOATING_SKY_ISLAND",Vector3.new(50,8,20)',self.src)
        self.assertIn("Vector3.new(0,28,49),rgb(103,194,151),true",self.src)
    def test_all_slopes_bounded(self):
        for n,(a,b,w) in self.paths.items():
            length=math.hypot(b[0]-a[0],b[2]-a[2])
            self.assertLessEqual(abs(b[1]-a[1])/length,.55,n)
    def test_symmetry(self):
        for typ in ("ENTRY","ESCAPE"):
            a,b,_=self.paths["SKY_FORT_"+typ+"_RED"]
            c,d,_=self.paths["SKY_FORT_"+typ+"_BLUE"]
            self.assertEqual(a[0],-c[0]); self.assertEqual(b[0],-d[0])
            self.assertEqual(a[1:],c[1:]);self.assertEqual(b[1:],d[1:])
    def test_entrances_join_old_route(self):
        self.assertEqual(self.paths["SKY_FORT_ENTRY_RED"][0],(-30,16,18))
        self.assertEqual(self.paths["SKY_FORT_ENTRY_BLUE"][0],(30,16,18))
        self.assertIn('path("SKY_WALKWAY",Vector3.new(-30,16,18)',self.src)
    def test_castle_deck_landings(self):
        for side in ("RED","BLUE"):
            self.assertEqual(self.paths["SKY_FORT_ENTRY_"+side][1][1:],(32,39))
            self.assertEqual(self.paths["SKY_FORT_ESCAPE_"+side][0][1:],(32,49))
    def test_returns_to_real_scorepad_vicinity(self):
        for side in ("RED","BLUE"):
            x,y,z=self.paths["SKY_FORT_ESCAPE_"+side][1]
            self.assertEqual((abs(x),y,z),(82,0,22))
    def test_no_sidewall_sample_intrusion(self):
        for name,(a,b,w) in self.paths.items():
            for i in range(201):
                t=i/200; x=a[0]+t*(b[0]-a[0]);z=a[2]+t*(b[2]-a[2])
                bad=83-w/2-2<=abs(x)<=123+w/2+2 and (abs(z-44)<=w/2+2.5 or abs(z+44)<=w/2+2.5)
                self.assertFalse(bad,(name,t))
    def test_no_out_of_map_endpoints(self):
        for a,b,w in self.paths.values():
            for x,y,z in (a,b):
                self.assertLess(abs(x)+w/2,125)
                self.assertLess(abs(z)+w/2,69)
    def test_preview_creatures_not_monetized(self):
        self.assertIn('NoRewardNoD18Ownership',self.src)
        self.assertIn('Models.create("SPACE",creatures)',self.src)
    def test_negative_steep_route_rejected(self):
        a,b,w=self.paths["SKY_FORT_ENTRY_RED"]
        self.assertGreater(abs(48-a[1])/math.hypot(-6-a[0],39-a[2]),.55)

if __name__=="__main__":unittest.main()
