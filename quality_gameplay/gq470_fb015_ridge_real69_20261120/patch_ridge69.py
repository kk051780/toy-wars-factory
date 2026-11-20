#!/usr/bin/env python3
"""Source-locked P0 flagship ridgeline visual slice; no added runtime owner.

Input: immutable current official REAL69 Studio artifact, not the old RC85/86
game. Output modifies one existing FlagshipFieldArt Script. This is an
isolated PREP candidate only; source success != Studio/Android/ART acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

PARENT = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET = "ServerScriptService/EGGRUMBLE_FlagshipFieldArt"
MARK = "GQ470_FB015_RIDGE_HORIZON_P0_20261120"
PRIOR = "GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL69_20261120"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
FUNCTION_ANCHOR = "local function paintArena(arena:Instance)"
CALL_ANCHOR = " -- Broken long-distance ruin silhouette at the central axis; not a new wall.\n"

RIDGE = '''-- GQ470_FB015_RIDGE_HORIZON_P0_20261120
-- Six coastal-looking stepped ridgelines at +/-410 studs, far outside all
-- three 23-stud assault roads; never create physics walls or distracting UI.
-- Exactly twelve noncolliding wedge silhouettes per arena, mobile budget
-- remains original 320 total. No transparency cards, particles or lights.
local function drawHorizonRidges(arena:Instance,art:Instance,ground:(number,number)->Vector3)
 -- Irregular but deterministic silhouettes: three contours, mirrored lanes
 -- staggered in height/angle/depth. Exactly twelve original nonphysics parts.
 local ridgeContours = {
  {height=14,yaw=-19,drift=-16},
  {height=23,yaw=13,drift=8},
  {height=17,yaw=27,drift=19},
 }
 for _,side in ipairs({-1,1}) do
  for index=1,3 do
   local contour=ridgeContours[index]
   local x=side*410
   local z=(index-2)*270+side*contour.drift
   local at=ground(x,z)
   local h=contour.height+(if side>0 then 3 else 0)
   local turn=side*contour.yaw
   createVisual(arena,art,"HorizonCliffBase_"..side.."_"..index,"Wedge",
    Vector3.new(18,h,31),CFrame.new(at+Vector3.new(0,h/2,0))
     *CFrame.Angles(0,math.rad(turn),0),darkStone,Enum.Material.Slate)
   createVisual(arena,art,"HorizonCliffCrown_"..side.."_"..index,"Wedge",
    Vector3.new(11,4,24),CFrame.new(at+Vector3.new(-side*2,h+1,0))
     *CFrame.Angles(0,math.rad(-turn),0),limestone,Enum.Material.Limestone)
  end
 end
end

'''

CALL = ''' -- GQ470_FB015_RIDGE_HORIZON_P0_20261120: silhouette-only side ridges.
 drawHorizonRidges(arena,art,onGround)
'''

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def need(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_RIDGE_" + code)

def patch(source: str) -> str:
    need(MARK not in source, "DUPLICATE")
    need(source.count(PRIOR) == 1, "FORTRESS_904_ANCESTRY")
    need(source.count("local MAX_CASTLE_PARTS = 19") == 1, "CASTLE_BUDGET_DRIFT")
    need(source.count("local MAX_VISUAL_PARTS_PER_ARENA = 320") == 1, "MOBILE_BUDGET_DRIFT")
    need(source.count(FUNCTION_ANCHOR) == 1, "PAINT_ANCHOR_DRIFT")
    need(source.count(CALL_ANCHOR) == 1, "SCENE_ANCHOR_DRIFT")
    need("p.CanCollide=false" in source and "p.CanQuery=false" in source and
         "p.CastShadow=false" in source, "NONPHYSICAL_ART_GUARD")
    out = source.replace(FUNCTION_ANCHOR, RIDGE + FUNCTION_ANCHOR)
    out = out.replace(CALL_ANCHOR, CALL + CALL_ANCHOR)
    need(out.count(MARK) == 2 and out.count("drawHorizonRidges(arena,art,onGround)") == 1,
         "SOURCE_INSERT_COUNT")
    need("RemoteEvent" not in RIDGE and "Tool" not in RIDGE and "DataStore" not in RIDGE,
         "NO_AUTHORITY")
    return out

def selftest() -> None:
    minimal = ("local MAX_CASTLE_PARTS = 19\n"
               "local MAX_VISUAL_PARTS_PER_ARENA = 320\n"
               "-- " + PRIOR + "\n"
               "p.CanCollide=false;p.CanQuery=false;p.CastShadow=false\n"
               + FUNCTION_ANCHOR + "\n"
               + CALL_ANCHOR)
    result = patch(minimal)
    need("for index=1,3 do" in result and "drawHorizonRidges" in result
         and "local ridgeContours" in result and "local contour=ridgeContours[index]" in result,
         "HAPPY_PATH_IRREGULAR_CONTOURS")
    for broken in (minimal.replace(PRIOR, "missing"),
                   minimal.replace("= 320", "= 600"),
                   minimal.replace(CALL_ANCHOR, ""),
                   result):
        try:
            patch(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("NEGATIVE_MUTANT_WAS_ACCEPTED")
    print("GQ470_RIDGE_PATCH_AND_4_NEGATIVES_PASS")

def apply(root: Path) -> None:
    original = project_scan(root, PROJECT)
    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    need(len(original) == 69 and TARGET in original, "REAL69_69_ROUTES")
    need(receipt.get("build_head") == PARENT and
         receipt.get("selected_source_count") == 69 and
         len(receipt.get("source_hashes", {})) == 69,
         "PINNED_PARENT_RECEIPT")
    need(all(receipt["source_hashes"].get(k) == v["sha256"]
             for k,v in original.items()), "FULL_RECEIPT_SOURCE_DRIFT")
    need(not (root / "off69_ridge").exists(), "ROLLBACK_COLLISION")
    file = root / original[TARGET]["path"]
    old = file.read_bytes()
    need(original[TARGET]["class"] == "Script", "EXISTING_ART_SCRIPT_OWNER")
    result = patch(old.decode("utf-8")).encode("utf-8")
    save = root / "off69_ridge"
    shutil.copytree(root / "sources", save / "sources")
    for name in (PROJECT, RECEIPT, "EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copy2(root / name, save / name)
    file.write_bytes(result)
    after = project_scan(root, PROJECT)
    need(set(after) == set(original) and len(after) == 69, "ROUTE_COUNT")
    changed = {k for k in after if after[k]["sha256"] != original[k]["sha256"]}
    need(changed == {TARGET}, "EXACTLY_ONE_ART_SOURCE")
    need(all(after[k]["class"] == original[k]["class"] for k in after),
         "CLASS_NONLOSS")
    need(all(after[k]["sha256"] == original[k]["sha256"]
             for k in after if k != TARGET), "OTHER_68_EXACT")
    need((save / original[TARGET]["path"]).read_bytes() == old, "EXACT_INVERSE")
    receipt["source_hashes"][TARGET] = sha(result)
    receipt["build_head"] = "PREP_RIDGE_FROM_" + PARENT
    receipt["gq470_fb015_ridge_visual"] = {
        "feature_id": MARK,
        "original_formal_sha": PARENT,
        "modified_existing_route": TARGET,
        "original_source_sha256": sha(old),
        "new_source_sha256": sha(result),
        "other_selected_routes_byte_exact": 68,
        "new_selected_scripts": 0,
        "new_visual_parts_per_arena_max": 12,
        "total_arena_visual_budget_unchanged": 320,
        "collision_or_gameplay_authority_changed": False,
        "rollback": "off69_ridge",
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "human_art_accepted": False
    }
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                            encoding="utf-8")
    print("GQ470_FLAGSHIP_RIDGE_ONE_SOURCE_68_NONLOSS_OFF69_PASS")

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()
    if args.self_test:
        selftest()
    else:
        need(args.base is not None,"MISSING_ARTIFACT")
        apply(args.base)
