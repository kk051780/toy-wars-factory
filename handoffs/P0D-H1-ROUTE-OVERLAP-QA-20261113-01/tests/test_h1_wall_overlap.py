"""H1 original wall-route overlap proof and isolated correction candidate QA.
Never claim fake-engine math as genuine Roblox Studio physics.
"""
import hashlib
import math
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[3]
H1_ROOT = REPO / "handoffs/P0D-H1-WORLD-CREATURES-20261113-01"
ORIGINAL = H1_ROOT / "src/server/H1FunWorld.server.luau"
CANDIDATE = ROOT / "candidate/H1FunWorld_wall_clearance_REVIEW_ONLY.server.luau"
MAP = H1_ROOT / "src/server/MapBuilder.luau"

def git_blob_hash(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()

def get_paths(source):
    exp = r'path\("([^"]+)",Vector3\.new\(([^)]+)\),Vector3\.new\(([^)]+)\),\s*([0-9]+)\s*,'
    records={}
    for name, a, b, width in re.findall(exp,source):
        assert name not in records, ("duplicate route",name)
        to_xyz=lambda st:tuple(float(v.strip()) for v in st.split(","))
        records[name]=(to_xyz(a),to_xyz(b),float(width))
    return records

def walls_from_canonical(map_source):
    assert 'Vector3.new(40, 14, 5)' in map_source
    assert 'Vector3.new(sign * 103, 7, z)' in map_source
    assert 'for _, z in ipairs({-44, 44})' in map_source
    # Original wall axis-aligned parts, centered y=7 (range 0..14).
    return [
        (team,label,(-123,-83) if team=="RED" else (83,123),(0,14),(z-2.5,z+2.5))
        for team in ("RED","BLUE") for label,z in (("N",44),("S",-44))
    ]

def wide_segment_bbox(record):
    a,b,width=record
    # Conservative x/z extent; exact Roblox rotated oriented-box physics still needs Studio.
    return (
        (min(a[0],b[0])-width/2,max(a[0],b[0])+width/2),
        (min(a[1],b[1])-2,max(a[1],b[1])+2),
        (min(a[2],b[2])-width/2,max(a[2],b[2])+width/2)
    )

def overlaps(interval1,interval2):
    return min(interval1[1],interval2[1])>max(interval1[0],interval2[0])

def potential_overlaps(paths,walls):
    hits=set()
    for name,record in paths.items():
        boxes=wide_segment_bbox(record)
        for team,label,x,y,z in walls:
            if all(overlaps(a,b) for a,b in zip(boxes,(x,y,z))):
                hits.add((name,team,label))
    return hits

def certain_centerline_intrusions(paths,walls):
    # Path CENTER'S WALKABLE DECK (sample 0.5 stud above center) enters solid wall.
    hits=set()
    for name,(a,b,width) in paths.items():
        for team,label,x,y,z in walls:
            for i in range(1,100):
                t=i/100
                p=tuple(a[k]+(b[k]-a[k])*t for k in range(3))
                if x[0]<p[0]<x[1] and y[0]<p[1]+0.5<y[1] and z[0]<p[2]<z[1]:
                    hits.add((name,team,label))
                    break
    return hits

def validate_corrected(original,corrected):
    op=get_paths(original)
    cp=get_paths(corrected)
    walls=walls_from_canonical(MAP.read_text(encoding="utf-8"))
    assert potential_overlaps(cp,walls)==set(),potential_overlaps(cp,walls)
    assert certain_centerline_intrusions(cp,walls)==set()
    expected={"SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE",
              "SEA_LOW_CAUSEWAY","SEA_ENTRY_RED","SEA_ENTRY_BLUE"}
    assert set(cp)==expected
    # Sky three parts join at their actual origin/end; sea connector endpoints join causeway.
    for a,b in (("SKY_RAMP_RED","SKY_WALKWAY"),("SKY_WALKWAY","SKY_RAMP_BLUE")):
        assert cp[a][1]==cp[b][0]
    assert cp["SEA_LOW_CAUSEWAY"][0]==cp["SEA_ENTRY_RED"][0]
    assert cp["SEA_LOW_CAUSEWAY"][1]==cp["SEA_ENTRY_BLUE"][0]
    for name,(a,b,width) in cp.items():
        d=math.dist(a,b)
        horizontal=math.hypot(b[0]-a[0],b[2]-a[2])
        assert 12<=d<220, (name,"length")
        assert horizontal>0 and abs(a[1]-b[1])<=0.55*horizontal,(name,"slope")
        assert width>=10 and width<=18
        for p in (a,b):
            assert abs(p[0])<=125 and abs(p[2])<=69 and p[1]>=-30,(name,p)
    # Both original field return routes usable by either team with no role check, gates or new remote.
    for needle in ('p:SetAttribute("FreeToAllRoles",true)','p:SetAttribute("TacticalAlternativeRoute",true)',
                   'p.CanCollide=solid','if not RunService:IsStudio() then'):
        assert needle in corrected,needle
    for bad in ("RemoteEvent", "DataStore", "MarketplaceService", "Humanoid.WalkSpeed ="):
        assert bad not in corrected
    # No authority changes or altered star whale/political source; bounded exact block replacement.
    prefix="-- TWO REAL PHYSICAL ALTERNATIVE ROUTES plus original center ground route."
    suffix="for i=-2,2 do"
    assert original.split(prefix,1)[0]==corrected.split(prefix,1)[0]
    assert original.split(suffix,1)[1]==corrected.split(suffix,1)[1]
    assert "H1 private Studio source only; refused live execution" in corrected
    assert 'Models.create("SPACE",creatures)' in corrected
    assert 'Models.create("CELESTIAL",creatures)' in corrected
    # Low sea road remains clear of actual ±71 border (−69 is inward top).
    _,_,sea_width=cp["SEA_LOW_CAUSEWAY"]
    sea_z=cp["SEA_LOW_CAUSEWAY"][0][2]
    assert sea_z-sea_width/2 > -69
    # Sky ramp approach avoids original noncolliding score pads z=14..26 as well as walls.
    for name in ("SKY_RAMP_RED","SKY_RAMP_BLUE"):
        a,b,width=cp[name]
        assert min(a[2],b[2])-width/2 > 26, ("score pad approach occlusion",name)
    # Side connectors x=±72 +/-width/2 do NOT intersect inner edge of castle side wall at |x|=83.
    for name in ("SEA_ENTRY_RED","SEA_ENTRY_BLUE"):
        xs=[cp[name][0][0],cp[name][1][0]]
        assert max(abs(x) for x in xs)+cp[name][2]/2 <83
    # Sea rails leave both full side connector entrances clear.
    assert 'Vector3.new(120,3,1),Vector3.new(0,2,-48)' in corrected
    assert 'Vector3.new(120,3,1),Vector3.new(0,2,-62)' in corrected
    return True

class H1WallOverlapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_bytes=ORIGINAL.read_bytes()
        cls.orig=cls.orig_bytes.decode("utf-8")
        cls.fixed_bytes=CANDIDATE.read_bytes()
        cls.fixed=cls.fixed_bytes.decode("utf-8")
        cls.walls=walls_from_canonical(MAP.read_text(encoding="utf-8"))
    def test_exact_original_h1_blob(self):
        self.assertEqual(git_blob_hash(self.orig_bytes),"6de8a8b4f17afd4e11c4be8eb1db556506d9c8df")
    def test_exact_original_map_blob(self):
        self.assertEqual(git_blob_hash(MAP.read_bytes()),"94655d019fdf9798fa24a350ebf49f8290465ac0")
    def test_exact_qa_candidate_blob(self):
        self.assertEqual(git_blob_hash(self.fixed_bytes),"cc764b9caaa293ff747489e02e607af4502ddca4")
    def test_original_has_four_obvious_route_wall_overlaps(self):
        expected={
            ("SKY_RAMP_RED","RED","N"),
            ("SKY_RAMP_BLUE","BLUE","N"),
            ("SEA_LOW_CAUSEWAY","RED","S"),
            ("SEA_LOW_CAUSEWAY","BLUE","S")
        }
        self.assertEqual(potential_overlaps(get_paths(self.orig),self.walls),expected)
    def test_original_centerline_actually_inside_walls(self):
        direct=certain_centerline_intrusions(get_paths(self.orig),self.walls)
        self.assertEqual(len(direct),4, direct)
    def test_candidate_clear_of_all_castle_walls(self):
        self.assertTrue(validate_corrected(self.orig,self.fixed))
    def test_candidate_sea_has_three_connected_sections(self):
        x=get_paths(self.fixed)
        self.assertEqual(x["SEA_LOW_CAUSEWAY"][0],x["SEA_ENTRY_RED"][0])
        self.assertEqual(x["SEA_LOW_CAUSEWAY"][1],x["SEA_ENTRY_BLUE"][0])
    def test_candidate_sky_has_three_connected_sections(self):
        x=get_paths(self.fixed)
        self.assertEqual(x["SKY_RAMP_RED"][1],x["SKY_WALKWAY"][0])
        self.assertEqual(x["SKY_WALKWAY"][1],x["SKY_RAMP_BLUE"][0])
    def test_mutant_revert_sea_into_castle_wall_is_rejected(self):
        bad=self.fixed.replace('Vector3.new(-72,0,-55),Vector3.new(72,0,-55)',
                               'Vector3.new(-99,0,-45),Vector3.new(99,0,-45)')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_revert_sky_ramp_into_wall_is_rejected(self):
        bad=self.fixed.replace('Vector3.new(-86,0,32.5),Vector3.new(-46,16,32.5)',
                               'Vector3.new(-91,0,43),Vector3.new(-52,16,43)')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_drop_one_sea_connector_is_rejected(self):
        bad=self.fixed.replace('path("SEA_ENTRY_RED"','path("DISABLED_RED_SEA_ENTRY"')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_forged_free_role_attribute_is_rejected(self):
        bad=self.fixed.replace('p:SetAttribute("FreeToAllRoles",true)',
                               'p:SetAttribute("FreeToAllRoles",false)')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_sky_climb_too_steep_is_rejected(self):
        bad=self.fixed.replace('Vector3.new(-86,0,28),Vector3.new(-46,16,28)',
                               'Vector3.new(-66,0,28),Vector3.new(-46,16,28)')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_sky_approach_occludes_score_pad_rejected(self):
        bad=self.fixed.replace('Vector3.new(-86,0,32.5),Vector3.new(-46,16,32.5)',
                               'Vector3.new(-86,0,28),Vector3.new(-46,16,28)')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_out_of_bounds_sea_is_rejected(self):
        bad=self.fixed.replace('Vector3.new(-72,0,-55),Vector3.new(72,0,-55)',
                               'Vector3.new(-72,0,-73),Vector3.new(72,0,-73)')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
    def test_mutant_change_game_authority_rejected(self):
        bad=self.fixed.replace('local elapsed=0','local fake=Instance.new("RemoteEvent")\nlocal elapsed=0')
        with self.assertRaises(AssertionError):validate_corrected(self.orig,bad)
if __name__=="__main__":
    unittest.main()
