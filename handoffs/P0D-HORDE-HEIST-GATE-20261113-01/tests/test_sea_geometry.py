"""Conservative 2-D source-geometry and grid routing for S2 SEA dual-gate overlay.

These checks establish source-level directional utility, not Roblox physics or
Android performance. Avatars represented as disks with 1.7-stud clearance.
"""
from collections import deque
from pathlib import Path
import re
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src/GateRouteOverlay.luau").read_text("utf-8")

def number(key):
    found=re.search(r"^local "+re.escape(key)+r" = (-?\d+(?:\.\d+)?)$",SOURCE,re.M)
    if not found: raise AssertionError("MISSING_OR_CHANGED_ROUTE_SPEC: "+key)
    return float(found.group(1))

X=number("ROUTE_GATE_X")
Z=number("ROUTE_GATE_Z")
WIDTH=number("ROUTE_GATE_WIDTH")
NORTH=number("ROUTE_ARM_NORTH_Z")
NORTH_LENGTH=number("ROUTE_ARM_NORTH_LENGTH")
SOUTH=number("ROUTE_ARM_SOUTH_Z")
SOUTH_LENGTH=number("ROUTE_ARM_SOUTH_LENGTH")
THICKNESS=number("ROUTE_WALL_THICKNESS")
HEIGHT=number("ROUTE_WALL_HEIGHT")
CLEARANCE=1.7

def barriers(x_mag=X,north=NORTH,south=SOUTH,open_doors=False):
    result=[]
    for sign in (-1,1):
        x=sign*x_mag
        result.extend([(x,north,THICKNESS,NORTH_LENGTH),
                       (x,south,THICKNESS,SOUTH_LENGTH)])
        if not open_doors:
            result.append((x,Z,1.2,WIDTH))
    return result

def overlap(a,b):
    ax,az,aw,ad=a
    bx,bz,bw,bd=b
    return abs(ax-bx) < (aw+bw)/2 and abs(az-bz) < (ad+bd)/2

def blocked(x,z,doors_open=False):
    # Existing S1 arena floor and boundaries.
    if not (-117 <= x <=117 and -64 <= z <=64):
        return True
    for ox,oz,w,d in barriers(open_doors=doors_open):
        if abs(x-ox) <= w/2+CLEARANCE and abs(z-oz) <= d/2+CLEARANCE:
            return True
    # Exact frozen S1 MapBuilder five pillars at 20-stud pitch, z alternates +/-32.
    for i in range(-2,3):
        ox,oz=20*i,(32 if i%2==0 else -32)
        if abs(x-ox) <= 3.5+CLEARANCE and abs(z-oz) <= 3.5+CLEARANCE:
            return True
    # Original two castles; conservative solid north/south and rear wall AABBs.
    for sign in (-1,1):
        for zz in (-44,44):
            if abs(x-sign*103)<=20+CLEARANCE and abs(z-zz)<=2.5+CLEARANCE:
                return True
        if abs(x-sign*123)<=2.5+CLEARANCE and abs(z)<=46.5+CLEARANCE:
            return True
    return False

def route(start,end,doors_open):
    if blocked(*start,doors_open) or blocked(*end,doors_open):
        return None
    queue=deque([start])
    lengths={start:0}
    while queue:
        x,z=queue.popleft()
        if (x,z)==end:
            return lengths[end]
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
            new=(x+dx,z+dz)
            if new in lengths or blocked(*new,doors_open):
                continue
            lengths[new]=lengths[(x,z)]+1
            queue.append(new)
    return None

class OriginalGeometryContract(unittest.TestCase):
    def test_exact_symmetric_spec(self):
        self.assertEqual((X,Z,WIDTH), (36,-22,10))
        self.assertEqual((NORTH,NORTH_LENGTH,SOUTH,SOUTH_LENGTH),
                         (-3.5,27,-34.5,15))

    def test_road_and_gate_are_real_colliders(self):
        self.assertIn("part.CanCollide = true",SOURCE)
        self.assertIn("gateVisual.create(model,",SOURCE)
        self.assertIn('CFrame.Angles(0,math.pi/2,0)',SOURCE)

    def test_source_guard_requires_actual_sea(self):
        for s in ("H1_FUN_WORLD","SEA_LOW_CAUSEWAY",
                  "SEA_ENTRY_RED","SEA_ENTRY_BLUE",
                  "H1_SEA_SOURCE_NOT_READY_OR_CHANGED"):
            self.assertIn(s,SOURCE)

    def test_not_second_round_server(self):
        for bad in ("FireServer(","RemoteEvent.new","DataStore",
                    "TakeDamage(","OnServerEvent:Connect"):
            self.assertNotIn(bad,SOURCE)

    def test_one_snapshot_two_doors(self):
        self.assertIn('for _,teamSign in ipairs({-1,1})',SOURCE)
        self.assertIn("gateVisual.render(door,snapshot)",SOURCE)
        self.assertIn('DUPLICATE_S2_GATE_REJECTED',SOURCE)

    def test_physical_minion_origins_clear(self):
        # Original eight NPCs: x=-24,-8,8,24; z +/-18. One elite at (0,0).
        for b in barriers(open_doors=False):
            for x in (-24,-8,8,24):
                for z in (-18,18):
                    self.assertFalse(overlap(b,(x,z,3.4,3.4)))
            self.assertFalse(overlap(b,(0,0,4,5)))

    def test_original_pillars_clear(self):
        for i in range(-2,3):
            for b in barriers(open_doors=False):
                self.assertFalse(overlap(b,(i*20,32 if i%2==0 else -32,7,7)))

    def test_original_castle_walls_clear(self):
        for sign in (-1,1):
            for wall in [(sign*103,-44,40,5),(sign*103,44,40,5),
                         (sign*123,0,5,93)]:
                for b in barriers(open_doors=False):
                    self.assertFalse(overlap(b,wall))

    def test_inside_original_world_limits(self):
        for x,z,w,d in barriers(open_doors=False):
            self.assertLessEqual(abs(x)+w/2,76)
            self.assertLessEqual(abs(z)+d/2,64)
        self.assertLessEqual(HEIGHT,10)

    def test_english_source_admits_free_detour(self):
        self.assertIn("z>=12",SOURCE)
        self.assertLess(NORTH+NORTH_LENGTH/2,12)
        self.assertGreater(SOUTH-SOUTH_LENGTH/2,-64)

    def test_red_blue_symmetric_parts(self):
        self.assertEqual(sorted(x for x,_,_,_ in barriers(open_doors=False)),
                         [-X]*3 + [X]*3)

class RoundTripGeometry(unittest.TestCase):
    def test_original_sea_route_open_vs_closed(self):
        self.assertEqual(route((-72,-22),(72,-22),True),144)
        closed=route((-72,-22),(72,-22),False)
        self.assertIsNotNone(closed)
        self.assertGreaterEqual(closed,174)

    def test_red_to_enemy_egg_open_improves(self):
        opened=route((-68,0),(98,-20),True)
        closed=route((-68,0),(98,-20),False)
        self.assertEqual(opened,186)
        self.assertGreaterEqual(closed-opened,20)

    def test_blue_to_enemy_egg_is_fair(self):
        self.assertEqual(route((68,0),(-98,-20),True),
                         route((-68,0),(98,-20),True))
        self.assertEqual(route((68,0),(-98,-20),False),
                         route((-68,0),(98,-20),False))

    def test_closed_gates_do_not_trap_both_teams(self):
        for a,b in (((-68,0),(98,-20)),((68,0),(-98,-20)),
                    ((-72,-22),(72,-22)),((72,-22),(-72,-22)),
                    ((-98,-20),(82,20)),((98,-20),(-82,20))):
            self.assertIsNotNone(route(a,b,False))

    def test_egg_return_routes_exist(self):
        self.assertIsNotNone(route((98,-20),(-82,20),False))
        self.assertIsNotNone(route((-98,-20),(82,20),False))

    def test_bad_mirrored_design_may_overlap_elite(self):
        # Mutation guard: central copy at x=0 would be in elite's combat area.
        self.assertTrue(any(overlap(b,(0,0,4,5))
                            for b in barriers(x_mag=0,open_doors=False)
                            if b[1] < 10 and b[1] > -20) is False)
        self.assertNotEqual(X,0)

    def test_fall_back_grass_route_is_public(self):
        for z in (14,18,48,-49):
            self.assertFalse(blocked(36,z,False))
            self.assertFalse(blocked(-36,z,False))

if __name__=="__main__":
    unittest.main()
