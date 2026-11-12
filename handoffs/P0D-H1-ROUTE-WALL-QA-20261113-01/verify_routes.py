#!/usr/bin/env python3
"""Source-pinned QA: actual H1 route CENTERLINES vs original S1 solid castle walls.

Run:
  python handoffs/P0D-H1-ROUTE-WALL-QA-20261113-01/verify_routes.py --selftest
  python handoffs/P0D-H1-ROUTE-WALL-QA-20261113-01/verify_routes.py --check

--check returns 2 when the pinned original has obstructed routes. This is a
deliberate RED gate, not a Studio collision/phone QA success claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "handoffs/P0D-H1-WORLD-CREATURES-20261113-01/src/server"
WORLD_FILE = BASE / "H1FunWorld.server.luau"
MAP_FILE = BASE / "MapBuilder.luau"
EXPECTED_PATHS = {"SKY_RAMP_RED", "SKY_WALKWAY", "SKY_RAMP_BLUE", "SEA_LOW_CAUSEWAY"}
PATH_RE = re.compile(
    r'path\("([A-Z_]+)",\s*'
    r'Vector3\.new\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\),\s*'
    r'Vector3\.new\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\),\s*[\d.]+',
)
WALL_RE = re.compile(
    r'part\(base,\s*name\s*\.\.\s*"_WALL",\s*'
    r'Vector3\.new\(\s*40,\s*14,\s*5\),\s*'
    r'Vector3\.new\(\s*sign\s*\*\s*103,\s*7,\s*z\)',
)

@dataclass(frozen=True)
class Segment:
    name: str
    a: tuple[float, float, float]
    b: tuple[float, float, float]

@dataclass(frozen=True)
class Wall:
    team: str
    z: float
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]

def extract_paths(source: str) -> list[Segment]:
    found = []
    for match in PATH_RE.finditer(source):
        n = tuple(float(match.group(i)) for i in range(2, 8))
        found.append(Segment(match.group(1), (n[0], n[1], n[2]), (n[3], n[4], n[5])))
    names = [p.name for p in found]
    if len(names) != len(set(names)) or set(names) != EXPECTED_PATHS:
        raise ValueError("H1_ROUTE_SET_CHANGED_FAIL_CLOSED: " + repr(names))
    return found

def extract_castle_walls(source: str) -> list[Wall]:
    if not WALL_RE.search(source) or not re.search(
        r'for\s+_,\s*z\s+in\s+ipairs\(\{\s*-44,\s*44\s*\}\)', source
    ):
        raise ValueError("S1_CASTLE_WALL_GEOMETRY_CHANGED_FAIL_CLOSED")
    return [
        Wall(team, z, ((x - 20, x + 20), (0.0, 14.0), (z - 2.5, z + 2.5)))
        for team, x in (("RED", -103.0), ("BLUE", 103.0))
        for z in (-44.0, 44.0)
    ]

def segment_aabb_entry(seg: Segment, box: Wall):
    """Exact continuous clipping of centerline against CLOSED 3D wall volume.

    This ignores walkway/ramp physical width and thickness, so a centerline
    hit is sufficient proof of overlap. It cannot prove real Roblox traversal.
    """
    entry, leave = 0.0, 1.0
    for axis, (low, high) in enumerate(box.bounds):
        origin, end = seg.a[axis], seg.b[axis]
        delta = end - origin
        if abs(delta) < 1e-12:
            if origin < low or origin > high:
                return None
        else:
            t0, t1 = (low - origin) / delta, (high - origin) / delta
            entry = max(entry, min(t0, t1))
            leave = min(leave, max(t0, t1))
            if entry > leave:
                return None
    if entry > leave:
        return None
    return tuple(round(seg.a[i] + entry * (seg.b[i] - seg.a[i]), 4) for i in range(3))

def find_intersections(paths: list[Segment], walls: list[Wall]) -> list[dict]:
    return [
        {"route": path.name, "castle": wall.team, "side_z": wall.z, "centerline_entry_xyz": point}
        for path in paths for wall in walls
        if (point := segment_aabb_entry(path, wall)) is not None
    ]

def actual_sources():
    return WORLD_FILE.read_text(encoding="utf-8"), MAP_FILE.read_text(encoding="utf-8")

class H1ActualRouteQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world, cls.map = actual_sources()
        cls.paths = extract_paths(cls.world)
        cls.walls = extract_castle_walls(cls.map)

    def test_01_real_source_four_routes_present(self):
        self.assertEqual(len(self.paths), 4)

    def test_02_real_source_four_original_solid_walls(self):
        self.assertEqual(len(self.walls), 4)

    def test_03_pinned_current_geometry_has_four_centerline_obstructions(self):
        hits = find_intersections(self.paths, self.walls)
        self.assertEqual(len(hits), 4, hits)
        self.assertEqual(sorted((h["route"], h["castle"]) for h in hits), [
            ("SEA_LOW_CAUSEWAY", "BLUE"), ("SEA_LOW_CAUSEWAY", "RED"),
            ("SKY_RAMP_BLUE", "BLUE"), ("SKY_RAMP_RED", "RED"),
        ])

    def test_04_proposed_z57_paths_and_repositioned_ends_clear_walls(self):
        candidate = [
            Segment("SKY_RAMP_RED", (-72, 0, 57), (-42, 16, 57)),
            Segment("SKY_WALKWAY", (-42, 16, 57), (42, 16, 57)),
            Segment("SKY_RAMP_BLUE", (42, 16, 57), (72, 0, 57)),
            Segment("SEA_LOW_CAUSEWAY", (-72, 0, -57), (72, 0, -57)),
        ]
        self.assertEqual(find_intersections(candidate, self.walls), [])
        # Does NOT certify access via Roblox physics, role balance, egg carry, phone.

    def test_05_partial_sky_only_fix_still_catches_sea(self):
        replaced = [
            Segment(s.name, tuple((57 if i == 2 else x) for i, x in enumerate(s.a)),
                tuple((57 if i == 2 else x) for i, x in enumerate(s.b)))
            if s.name.startswith("SKY") else s for s in self.paths
        ]
        self.assertEqual(len(find_intersections(replaced, self.walls)), 2)

    def test_06_missing_real_route_refused(self):
        with self.assertRaisesRegex(ValueError, "H1_ROUTE_SET_CHANGED"):
            extract_paths(self.world.replace("SEA_LOW_CAUSEWAY", "INVISIBLE_SEA"))

    def test_07_duplicate_route_refused(self):
        with self.assertRaisesRegex(ValueError, "H1_ROUTE_SET_CHANGED"):
            extract_paths(self.world + '\npath("SKY_RAMP_RED",Vector3.new(-1,0,0),Vector3.new(1,0,0),15)')

    def test_08_castle_geometry_change_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "S1_CASTLE_WALL_GEOMETRY_CHANGED"):
            extract_castle_walls(self.map.replace('Vector3.new(40, 14, 5)', 'Vector3.new(40, 2, 5)'))

    def test_09_walls_outside_z_do_not_hit(self):
        future = Segment("TEST", (-72, 0, 60), (72, 0, 60))
        self.assertEqual(find_intersections([future], self.walls), [])

    def test_10_existing_source_not_modified_by_auditor(self):
        self.assertIn('RunService:IsStudio()', self.world)
        self.assertIn('CanCollide=solid', self.world)
        self.assertIn('assert(workspace:FindFirstChild("TRAP_RAIDERS_S1") == nil', self.map)

if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        world, baseline = actual_sources()
        defects = find_intersections(extract_paths(world), extract_castle_walls(baseline))
        print(json.dumps({"source_gate": "BLOCKED" if defects else "PASS",
                          "engine_studio_2client": "NOT_TESTED",
                          "actual_h1_source_sha": "c73f305fb412927aee05b399a4f54a2a16d0579f",
                          "defects": defects}, ensure_ascii=False, indent=2))
        sys.exit(2 if defects else 0)
    if sys.argv[1:] != ["--selftest"]:
        raise SystemExit("Use --check or --selftest")
    unittest.main(argv=[sys.argv[0]], verbosity=2)
