"""Finite stylized sky geometry gate: source-derived clearance / budget only.

Never infer actual in-game camera visibility or Android FPS from this model.
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path

SOURCE = Path(__file__).with_name("EGGRUMBLE_FarSkyFacets.client.luau")

def required_int(text: str, pattern: str, label: str) -> int:
    found = re.search(pattern, text)
    if found is None:
        raise ValueError("RED_FARSKY_GEOMETRY_MISSING_" + label)
    return int(found.group(1))

def measure(text: str) -> dict:
    desk = required_int(text, r"local MAX_DESKTOP_BANKS = (\d+)\b", "DESK_BANKS")
    touch = required_int(text, r"local MAX_TOUCH_BANKS = (\d+)\b", "TOUCH_BANKS")
    per = required_int(text, r"local FACETS_PER_BANK = (\d+)\b", "FACET_COUNT")
    dist = required_int(text, r"local distance = (\d+) \+ \(i % 3\) \* 55\b", "DISTANCE")
    altitude = required_int(text, r"local altitude = (\d+) \+ \(i % 3\) \* 12\b", "ALTITUDE")
    require = lambda p,m: None if p else (_ for _ in ()).throw(ValueError("RED_FARSKY_GEOMETRY_"+m))
    require((desk,touch,per)==(6,4,3), "BUDGET_CHANGES")
    require("local theta = ((i - 1) / bankCount) * math.pi * 2 + math.rad(-18)" in text,
            "ORBIT_FORMULA_DRIFT")
    require("local origin = Vector3.new(math.cos(theta) * distance, altitude, math.sin(theta) * distance)" in text,
            "HORIZON_POSITION_DRIFT")
    require("local tangent = Vector3.new(-math.sin(theta), 0, math.cos(theta))" in text,
            "BANK_TANGENT_DRIFT")
    shapes=[
        ("Base", 146,16,20,0,0),
        ("CrestA", 100,25,14,-39,12),
        ("CrestB",91,19,14,43,9),
    ]
    require('Vector3.new(146, 16, 20)' in text and 'Vector3.new(100, 25, 14)' in text
            and 'Vector3.new(91, 19, 14)' in text, "FACET_DIMENSIONS")
    require('origin - tangent * 39 + Vector3.new(0, 12, 0)' in text and
            'origin + tangent * 43 + Vector3.new(0, 9, 0)' in text,
            "FACET_ANCHORS")
    closest = float("inf")
    lowest = float("inf")
    for banks in (touch,desk):
        for i in range(1,banks+1):
            r=dist+(i%3)*55
            cy=altitude+(i%3)*12
            for _,w,h,z,tangent_offset,raise_y in shapes:
                # Worst-case rotated horizontal footprint of shallow wedge.
                conservative_min_radius = r - abs(tangent_offset) - math.hypot(w,z)*.5
                conservative_low_y = cy+raise_y-h*.5
                closest=min(closest,conservative_min_radius)
                lowest=min(lowest,conservative_low_y)
    require(closest>=490,"CASTLE_AND_3_PATH_GROUND_CLEARANCE")
    require(lowest>=145,"PLAYER_AND_CASTLE_OVERHEAD_CLEARANCE")
    require(desk*per<=18 and touch*per<=12, "MOBILE_PART_BUDGET")
    require("CanCollide = false" in text and "CanQuery = false" in text and
            "CanTouch = false" in text and "CastShadow = false" in text,
            "PHYSICS_OR_SHADOW_COST")
    return {
        "source_gate":"GEOMETRY_MODEL_PASS_NOT_STUDIO",
        "keyboard_banks":desk,
        "touch_banks":touch,
        "parts_per_bank":per,
        "max_desktop_parts":desk*per,
        "max_touch_parts":touch*per,
        "conservative_min_ground_radius_studs":round(closest,2),
        "conservative_lowest_cloud_y_studs":round(lowest,2),
        "castle_path_collision":"MODEL_NONE_NOT_ENGINE",
        "camera_visibility":"NOT_TESTED",
        "mobile_fps":"NOT_TESTED",
        "art_owner":"NO_GO"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=measure(SOURCE.read_text(encoding="utf-8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
