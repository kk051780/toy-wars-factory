#!/usr/bin/env python3
"""P0D #470 / FB-009: evidence-based static battlefield footprint audit.

Reads two pinned-in-repository REAL Luau sources and reports only source-proven
geometry. This cannot prove Roblox Pathfinding, effective live field, FPS,
fun, public-world rendering or competitor superiority.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

DEFAULT_MAP = "releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau"
DEFAULT_STUDIO = "rc_fastlane/features/owner361_castle/CastleBattlefield.server.luau"

def one(pattern, src, field):
    matches = re.findall(pattern, src, re.MULTILINE | re.DOTALL)
    if len(matches) != 1:
        raise ValueError(f"SOURCE_PATTERN_AMBIGUOUS_OR_MISSING:{field}:matches={len(matches)}")
    return matches[0]

def coords(values):
    return [float(x) for x in values]

def vector_from_part(src, partname):
    # Fail closed if duplicated or missing. Named part's first vector is its size.
    q = re.escape(partname)
    m = one(r'part\(\s*folder\s*,\s*"' + q
            + r'"\s*,\s*Vector3\.new\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
            src, partname)
    return coords(m)

def vector_assignment(src, var):
    return coords(one(r'\b' + re.escape(var) + r'\.Size\s*=\s*Vector3\.new\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
                      src, var + "_Size"))

def named_objective(src, variable, name):
    # A source name, its size, then a position Vector3(sign * X, Y, Z).
    pat = (r'\blocal\s+' + re.escape(variable) + r'\s*=\s*part\(\s*base\s*,\s*name\s*\.\.\s*"' +
           re.escape(name) + r'"\s*,\s*Vector3\.new\([^)]+\)\s*,\s*'
           r'Vector3\.new\(\s*sign\s*\*\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)')
    return coords(one(pat, src, variable + name))

def dist(a, b):
    return round(math.dist(a, b), 3)

def audit(base_path, studio_path):
    mb = Path(base_path).read_text(encoding="utf-8")
    cs = Path(studio_path).read_text(encoding="utf-8")
    arena = vector_from_part(mb, "GrassArena")
    center = vector_from_part(mb, "CenterRoad")
    expanded = vector_assignment(cs, "grass")
    egg = named_objective(mb, "egg", "_EGG")
    pad = named_objective(mb, "pad", "_SCORE_PAD")
    spawn = named_objective(mb, "spawn", "_SPAWN")
    if arena[0] <= 0 or arena[2] <= 0 or expanded[0] <= 0 or expanded[2] <= 0:
        raise ValueError("NONPOSITIVE_FIELD_DIMENSIONS")
    guard = re.search(r'if\s+not\s+RunService:IsStudio\(\)\s+then\s+return\s+end', cs)
    expansion = re.search(r'\bgrass\.Size\s*=', cs)
    if guard is None or expansion is None or guard.start() > expansion.start():
        raise ValueError("STUDIO_ONLY_GUARD_UNKNOWN")
    routes = []
    for name in ("NORTH_WOODLAND_TRAIL", "SOUTH_WETLAND_TRAIL"):
        m = one(r'part\(\s*folder\s*,\s*"' + re.escape(name) +
                r'"\s*,\s*Vector3\.new\([^)]+\)\s*,\s*Vector3\.new\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
                cs, name + "_POSITION")
        route_pos = coords(m)
        routes.append({"name": name, "center_studs": route_pos,
                       "center_outside_base_ground_z": abs(route_pos[2]) > arena[2] / 2})
    base_area = arena[0] * arena[2]
    studio_area = expanded[0] * expanded[2]
    # RED sign=-1 and BLUE sign=+1; do not confuse ground straight-line
    # lower bounds with accessible path lengths or actual walking times.
    red_spawn = [-spawn[0], spawn[2]]
    blue_spawn = [spawn[0], spawn[2]]
    blue_egg = [egg[0], egg[2]]
    red_pad = [-pad[0], pad[2]]
    payload = {
        "schema": "P0D_F009_STATIC_FIELD_AUDIT_V1",
        "quality_issue": "https://github.com/kk051780/toy-wars-factory/issues/470",
        "owner_feedback": "FB-009",
        "source_provenance": {
            "base_path": str(base_path),
            "base_sha256": hashlib.sha256(mb.encode()).hexdigest(),
            "studio_path": str(studio_path),
            "studio_sha256": hashlib.sha256(cs.encode()).hexdigest(),
        },
        "base_map": {
            "ground_studs_xyz": arena,
            "ground_plan_area_studs2": base_area,
            "center_road_studs_xyz": center,
            "one_named_center_road": True,
            "other_effective_traversal_routes": None,
            "live_build_effective_area_studs2": None,
        },
        "studio_only_extension": {
            "studio_guard_source_confirmed": True,
            "ground_studs_xyz": expanded,
            "ground_plan_area_studs2": studio_area,
            "area_multiplier_vs_base": round(studio_area / base_area, 4),
            "area_percent_increase_vs_base": round(100 * (studio_area / base_area - 1), 2),
            "decorative_flank_trails": routes,
            "walkable_routes_engine_verified": None,
            "public_build_expansion_verified": False,
        },
        "objective_geometry_lower_bounds": {
            "red_blue_spawn_straight_line_studs": dist(red_spawn, blue_spawn),
            "red_spawn_to_blue_egg_straight_line_studs": dist(red_spawn, blue_egg),
            "blue_egg_to_red_scoring_pad_straight_line_studs": dist(blue_egg, red_pad),
            "walking_seconds": None,
            "pathfinding_success_by_route": None,
        },
        "external_competitor_map_studs": None,
        "real_roblox_playtest": "NOT_RUN",
        "status": "FIELD_P0_NEEDS_REAL_LIVE_AND_STUDIO_ROUTE_MEASUREMENT",
        "critical_findings": [
            "Base MapBuilder builds 250x142 ground; source-proven Studio-only extension changes it to 370x294.",
            "The two flank route markers are inside a Studio-only script; they cannot demonstrate published-mode routes.",
            "A larger render area is NOT proof of three pathfindable routes, egg-delivery flow, or enjoyable combat.",
            "No automatic competitive win claim until measured on actual target device and external game."
        ]
    }
    return payload

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--map", default=DEFAULT_MAP)
    p.add_argument("--studio", default=DEFAULT_STUDIO)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = audit(args.map, args.studio)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FIELD_P0_NO_GO", result["base_map"]["ground_plan_area_studs2"],
          result["studio_only_extension"]["ground_plan_area_studs2"])
    # Exit 0 only indicates successful source-measurement/report generation.
    # It NEVER makes the actual field or overall product quality GO.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
