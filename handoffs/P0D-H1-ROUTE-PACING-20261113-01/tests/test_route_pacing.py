"""Source-pinned P0D H1 play-value geometry and fail-closed tests.
The route distances are geometric lower-bound proxies, NOT Roblox Studio traversal.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import math
from pathlib import Path
import re
import unittest

THIS=Path(__file__).resolve()
ROOT=THIS.parents[1]
REPO=THIS.parents[3]
OLD=REPO/"handoffs/P0D-H1-ROUTE-OVERLAP-QA-20261113-01/candidate/H1FunWorld_wall_clearance_REVIEW_ONLY.server.luau"
NEW=ROOT/"candidate/H1FunWorld_short_routes_REVIEW_ONLY.server.luau"
ORIGINAL_MAP=REPO/"handoffs/P0D-H1-WORLD-CREATURES-20261113-01/src/server/MapBuilder.luau"
CONFIG=REPO/"handoffs/P0D-H1-WORLD-CREATURES-20261113-01/src/shared/Config.luau"
EXPECTED_OLD="cc764b9caaa293ff747489e02e607af4502ddca4"
EXPECTED_NEW="7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea"
EXPECTED_MAP="94655d019fdf9798fa24a350ebf49f8290465ac0"
EXPECTED_CONFIG="62023303118454fa395f6bfce4c3a50552f840da"
NAMES={"SEA_LOW_CAUSEWAY","SEA_ENTRY_RED","SEA_ENTRY_BLUE",
       "SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE"}
ROUTE_RE=re.compile(
    r'path\("([^"]+)",Vector3\.new\(([^)]+)\),Vector3\.new\(([^)]+)\),\s*(\d+)\s*,'
)

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def geometry_source_text(path:Path,sha:str)->str:
    data=path.read_bytes()
    assert gitblob(data)==sha, (str(path),gitblob(data),sha)
    return data.decode("utf-8")
def vector(src:str)->tuple[float,float,float]:
    xyz=tuple(float(t.strip()) for t in src.split(","))
    assert len(xyz)==3 and all(math.isfinite(v) for v in xyz)
    return xyz
def parse_paths(source:str):
    parsed={}
    for name,a,b,width in ROUTE_RE.findall(source):
        assert name not in parsed, ("duplicate route",name)
        parsed[name]={"a":vector(a),"b":vector(b),"width":float(width)}
    return parsed
def euclidean(a,b):
    return math.dist(a,b)
def centerline_chain(paths,kind,team):
    # Both sea and sky are THREE free, physical connected segments with two ends.
    links={k:v for k,v in paths.items() if k.startswith(kind)}
    assert len(links)==3 and set(links)==({k for k in NAMES if k.startswith(kind)})
    graph=collections.defaultdict(list)
    for name,x in links.items():
        a,b=x["a"],x["b"]
        assert a!=b
        graph[a].append((b,name,euclidean(a,b)))
        graph[b].append((a,name,euclidean(a,b)))
    ends=[p for p,adj in graph.items() if len(adj)==1]
    assert len(ends)==2,("not a single path",kind,ends)
    start=next((p for p in ends if (p[0]<0 if team=="RED" else p[0]>0)),None)
    assert start is not None
    seen=set()
    current=start
    distance=0.0
    while True:
        options=[edge for edge in graph[current] if edge[1] not in seen]
        if not options:break
        assert len(options)==1,("branch",kind,current)
        other,name,step=options[0]
        seen.add(name);distance+=step;current=other
    assert len(seen)==3 and current!=start
    assert current[0]>0 if team=="RED" else current[0]<0
    return start,current,distance

def roundtrip(paths,kind,team):
    sign=-1 if team=="RED" else 1
    spawn=(sign*68.0,0.0,0.0)
    egg=(-sign*98.0,0.0,-20.0)
    score=(sign*82.0,0.0,20.0)
    first,last,length=centerline_chain(paths,kind,team)
    outbound=euclidean(spawn,first)+length+euclidean(last,egg)
    inbound=euclidean(egg,last)+length+euclidean(first,score)
    direct=euclidean(spawn,egg)+euclidean(egg,score)
    assert direct>0
    return {"team":team,"kind":kind,"outbound":outbound,"return":inbound,
            "total":outbound+inbound,"direct":direct,
            "extra_ratio":(outbound+inbound)/direct-1,
            "raider_min_seconds":(outbound+inbound)/19,
            "guardian_min_seconds":(outbound+inbound)/15}

def aabb_on_horizontal(path):
    a,b,w=path["a"],path["b"],path["width"]
    return ((min(a[0],b[0])-w/2,max(a[0],b[0])+w/2),
            (min(a[2],b[2])-w/2,max(a[2],b[2])+w/2))
def positive_intersection(a,b):
    return min(a[1],b[1])>max(a[0],b[0])
def footprints_overlap(a,b):
    return positive_intersection(a[0],b[0]) and positive_intersection(a[1],b[1])
def original_collidable_footprints(map_source):
    assert 'p.CanCollide = collide ~= false' in map_source
    assert 'Vector3.new(sign * 103, 7, z)' in map_source
    assert 'Vector3.new(40, 14, 5)' in map_source
    assert 'for _, z in ipairs({-44, 44})' in map_source
    assert 'Vector3.new(i * 20, 3, if i % 2 == 0 then 32 else -32)' in map_source
    solids={}
    for team,x in (("RED",-103),("BLUE",103)):
        for z in (-44,44):
            solids[f"{team}_SIDE_{z}"]=((x-20,x+20),(z-2.5,z+2.5))
    # Original five 7×7×7 center rocks, math exact to MapBuilder code.
    for i in range(-2,3):
        x=i*20;z=32 if i%2==0 else -32
        solids[f"CENTER_ROCK_{i}"]=((x-3.5,x+3.5),(z-3.5,z+3.5))
    return solids
def passable_without_major_solids(paths,map_source):
    solid=original_collidable_footprints(map_source)
    for name,x in paths.items():
        p=aabb_on_horizontal(x)
        for obstacle,rect in solid.items():
            assert not footprints_overlap(p,rect),(name,obstacle,p,rect)
    # Do not occlude original *noncolliding* score pad top-view and E prompt:
    # team pad center x±82,z20 size12. SKY starts x±62 and SEA is at z-22.
    pads={"RED_SCORE":((-88,-76),(14,26)),"BLUE_SCORE":((76,88),(14,26))}
    for name,x in paths.items():
        for p_name,rect in pads.items():
            assert not footprints_overlap(aabb_on_horizontal(x),rect), (name,p_name)
    return True

def verify_new(source,old,map_source):
    p=parse_paths(source)
    oldp=parse_paths(old)
    assert set(p)==NAMES
    assert set(oldp)==NAMES
    assert "if not RunService:IsStudio() then" in source
    assert 'Models.create("SPACE",creatures)' in source
    assert 'Models.create("CELESTIAL",creatures)' in source
    assert 'p:SetAttribute("FreeToAllRoles",true)' in source
    assert 'p:SetAttribute("TacticalAlternativeRoute",true)' in source
    assert 'p.CanCollide=solid' in source
    for bad in ("RemoteEvent","DataStore","MarketplaceService","FireServer","Humanoid.WalkSpeed ="):
        assert bad not in source,bad
    # Name+source code outside local sea/sky geometry is the exact original H1.
    marker="-- QA geometry candidate (not integrated):"
    stop="for i=-2,2 do"
    assert old.split(marker,1)[0]==source.split(marker,1)[0]
    assert old.split(stop,1)[1]==source.split(stop,1)[1]
    for name,seg in p.items():
        a,b,width=seg["a"],seg["b"],seg["width"]
        d=euclidean(a,b);horizontal=math.hypot(b[0]-a[0],b[2]-a[2])
        assert 12<=d<220,(name,"zero or invalid path segment",d)
        assert 8<=width<=18,(name,"narrow/oversized",width)
        assert horizontal>0 and abs(a[1]-b[1])<=0.55*horizontal,(name,"slope")
        for x,y,z in (a,b):
            assert abs(x)<=125 and abs(z)<=69 and y>=-30,(name,"play bounds",(x,y,z))
    assert passable_without_major_solids(p,map_source)
    for team in ("RED","BLUE"):
        oldsea=roundtrip(oldp,"SEA",team)
        oldsky=roundtrip(oldp,"SKY",team)
        assert oldsea["extra_ratio"]>0.50
        assert oldsky["extra_ratio"]>0.40
        for kind in ("SEA","SKY"):
            d=roundtrip(p,kind,team)
            assert d["extra_ratio"]<=0.25,(team,kind,"not a meaningful alternate",d)
            assert d["extra_ratio"]>=0.05,(team,kind,"no real tradeoff",d)
            assert d["total"]<roundtrip(oldp,kind,team)["total"]
            # The new loop is a modest detour, not an unmotivated long tour.
            assert d["raider_min_seconds"]<23.0
            assert d["guardian_min_seconds"]<29.0
    # Stable child readable two-sided signs, original side walls never rewritten.
    for key in ("SKY_SIGN_RED","SKY_SIGN_BLUE","SEA_SIGN_RED","SEA_SIGN_BLUE"):
        assert key in source
    return True

class TestH1KidPlayableRoutePacing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=geometry_source_text(OLD,EXPECTED_OLD)
        cls.source=geometry_source_text(NEW,EXPECTED_NEW)
        cls.map=geometry_source_text(ORIGINAL_MAP,EXPECTED_MAP)
        cls.config=geometry_source_text(CONFIG,EXPECTED_CONFIG)
    def test_pinned_real_original_source(self):self.assertIn("GrassArena",self.map)
    def test_real_s1_uses_exactly_two_roles(self):
        self.assertRegex(self.config,r'RoleHealth = \{RAIDER = 100, GUARDIAN = 135\}')
        self.assertRegex(self.config,r'RoleWalkSpeed = \{RAIDER = 19, GUARDIAN = 15\}')
    def test_new_six_reachable_segments(self):self.assertEqual(set(parse_paths(self.source)),NAMES)
    def test_new_source_play_value_gate(self):self.assertTrue(verify_new(self.source,self.old,self.map))
    def test_mirrored_both_team_detours(self):
        p=parse_paths(self.source)
        for kind in ("SEA","SKY"):
            red=roundtrip(p,kind,"RED");blue=roundtrip(p,kind,"BLUE")
            self.assertAlmostEqual(red["total"],blue["total"],places=7)
    def test_both_team_raider_guardian_roundtrip_carry_states(self):
        p=parse_paths(self.source)
        for team in ("RED","BLUE"):
            for role in ("RAIDER","GUARDIAN"):
                for carrying in (False,True):
                    for blocked in ("NONE","SEA","SKY"):
                        alternatives=[kind for kind in ("SEA","SKY") if blocked!=kind]
                        self.assertTrue(alternatives,(team,role,carrying,blocked))
                        self.assertTrue(all(roundtrip(p,kind,team)["extra_ratio"]<=.25 for kind in alternatives))
    def test_original_detours_really_large(self):
        p=parse_paths(self.old)
        self.assertGreater(roundtrip(p,"SEA","RED")["extra_ratio"],.50)
        self.assertGreater(roundtrip(p,"SKY","BLUE")["extra_ratio"],.40)
    def test_prevent_castle_wall_crossings(self):self.assertTrue(passable_without_major_solids(parse_paths(self.source),self.map))
    def test_negative_mutant_sea_blocked_by_center_rock(self):
        bad=self.source.replace('Vector3.new(-60,0,-22),Vector3.new(60,0,-22)',
                                'Vector3.new(-60,0,-32),Vector3.new(60,0,-32)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_long_dull_sea_detour(self):
        bad=self.source.replace('Vector3.new(-60,0,-22),Vector3.new(60,0,-22)',
                                'Vector3.new(-60,0,-60),Vector3.new(60,0,-60)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_sky_entrance_hits_score_pad(self):
        bad=self.source.replace('Vector3.new(-62,0,18),Vector3.new(-30,16,18)',
                                'Vector3.new(-82,0,20),Vector3.new(-30,16,18)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_skyscraper_unreachable(self):
        bad=self.source.replace('Vector3.new(-62,0,18),Vector3.new(-30,16,18)',
                                'Vector3.new(-62,0,18),Vector3.new(-30,60,18)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_teleport_gap_sky(self):
        bad=self.source.replace('Vector3.new(-30,16,18),Vector3.new(30,16,18)',
                                'Vector3.new(-17,16,18),Vector3.new(30,16,18)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_missing_sea_entrance(self):
        bad=self.source.replace('path("SEA_ENTRY_BLUE"','path("SEA_ENTRY_DELETED"')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_parkour_width_unfair(self):
        bad=self.source.replace('Vector3.new(-30,16,18),Vector3.new(30,16,18),16',
                                'Vector3.new(-30,16,18),Vector3.new(30,16,18),2')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_new_authoritative_remote(self):
        bad=self.source.replace('local elapsed=0','local remote=Instance.new("RemoteEvent")\nlocal elapsed=0')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_exceeds_s1_recovery_bounds(self):
        bad=self.source.replace('Vector3.new(-72,0,-22),Vector3.new(-60,0,-22)',
                                'Vector3.new(-150,0,-22),Vector3.new(-60,0,-22)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
    def test_negative_mutant_costly_long_sky(self):
        bad=self.source.replace('Vector3.new(-30,16,18),Vector3.new(30,16,18)',
                                'Vector3.new(-70,16,18),Vector3.new(70,16,18)')
        with self.assertRaises(AssertionError):verify_new(bad,self.old,self.map)
if __name__=="__main__":unittest.main()
