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
import math
import re
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
CALL_ANCHOR = " for _,child in ipairs(arena:GetChildren()) do\n  if child:IsA(\"Model\") and child.Name:sub(1,7)==\"Castle_\" then castleAt(arena,child) end\n end\n"

RIDGE = '''-- GQ470_FB015_RIDGE_HORIZON_P0_20261120
-- Visual-only horizon cliffs are strictly lower priority than all baseline
-- terrain/ruin visuals and every current or future castle ornament.
-- At most twelve noncolliding wedges; castles may reclaim them on budget hit.
local function drawHorizonRidges(arena:Instance,art:Instance,ground:(number,number)->Vector3)
 local bucket=ridgeVisuals[arena]
 -- A scene may be repainted; keep one bounded ridge set per arena, never 12 more.
 if bucket then return end
 bucket={}
 ridgeVisuals[arena]=bucket
 -- The arena teardown releases both its reference and decorative-Part list.
 arena.Destroying:Once(function()
  ridgeVisuals[arena]=nil
 end)
 -- Three unequal stepped profiles, mirrored by shore without repeating
 -- identical silhouettes. Each side has six matte, nonphysical Wedges.
 local ridgeContours = {
  {height=14,yaw=-19,drift=-16,depth=27,lean=-7,notch=3},
  {height=23,yaw=13,drift=8,depth=35,lean=6,notch=1},
  {height=17,yaw=27,drift=19,depth=25,lean=-4,notch=4},
 }
 for _,side in ipairs({-1,1}) do
  for index=1,3 do
   local contour=ridgeContours[index]
   local x=side*410
   local z=(index-2)*270+side*contour.drift
   local at=ground(x,z)
   local h=contour.height+(if side>0 then 3 else 0)
   local turn=side*contour.yaw
   local lean=side*contour.lean
   -- Use existing matte stone palette for subtle depth and directional
   -- contrast. These Color3 blends run once when an arena is built, not
   -- during combat frames; zero new instances or texture fetches.
   local baseTint=darkStone:Lerp(limestone,.07*(index-1))
   local crownTint=limestone:Lerp(darkStone,.08*(3-index))
   -- Reserve both pieces before sculpting a complete profile. If the 320
   -- scene cap is almost full, skip this pair rather than leave a bare wedge.
   if (budgets[arena] or 0)+2<=MAX_VISUAL_PARTS_PER_ARENA then
    local basePart=createVisual(arena,art,"HorizonCliffBase_"..side.."_"..index,"Wedge",
     Vector3.new(18,h,contour.depth),
     CFrame.new(at+Vector3.new(side*contour.notch,h/2,0))
      *CFrame.Angles(math.rad((index-2)*3),math.rad(turn),math.rad(lean)),
     baseTint,Enum.Material.Slate)
    if basePart then
     -- Matched limestone cap penetrates the base: no detached floating crown.
     local crownPart=createVisual(arena,art,"HorizonCliffCrown_"..side.."_"..index,"Wedge",
      Vector3.new(11,4,contour.depth-6),
      CFrame.new(at+Vector3.new(-side*(2+contour.notch*.25),h+.75,side*2))
       *CFrame.Angles(math.rad(-lean),math.rad(-turn*.7),math.rad(-lean*1.4)),
      crownTint,Enum.Material.Limestone)
     if crownPart then
      table.insert(bucket,basePart)
      table.insert(bucket,crownPart)
     else
      -- Defensive rollback for a failed crown allocation; no half cliff.
      basePart:Destroy()
      budgets[arena]=math.max(0,(budgets[arena] or 0)-1)
     end
    end
   end
  end
 end
end

'''

CALL = ''' -- GQ470_FB015_RIDGE_HORIZON_P0_20261120: add only after baseline and present castles.
 drawHorizonRidges(arena,art,onGround)
'''

BUDGET_ANCHOR = "local budgets:{[Instance]:number}={}\n"
CREATE_VISUAL_GUARD = " if (budgets[arena] or 0)>=MAX_VISUAL_PARTS_PER_ARENA then return nil end"
PRIORITY_BUDGET = '''local ridgeVisuals:{[Instance]:{BasePart}}={}
local function reclaimRidgeForCastle(arena:Instance):boolean
 local bucket=ridgeVisuals[arena]
 if not bucket then return false end
 while #bucket>0 do
  local p=table.remove(bucket)
  if p and p.Parent then
   p:Destroy()
   budgets[arena]=math.max(0,(budgets[arena] or 0)-1)
   return true
  end
 end
 return false
end
'''
PRIORITY_GUARD = ''' if (budgets[arena] or 0)>=MAX_VISUAL_PARTS_PER_ARENA then
  if parent.Name~="EGGRUMBLE_CastleArt_VisualOnly" or not reclaimRidgeForCastle(arena) then return nil end
 end'''

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def need(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_RIDGE_" + code)

def verify_contour_geometry(spec: str) -> None:
    """Fail closed on cliffs that crowd the routes or blow mobile visual bounds."""
    rows = re.findall(
        r"\{height=(\d+),yaw=(-?\d+),drift=(-?\d+),depth=(\d+),lean=(-?\d+),notch=(\d+)\}",
        spec)
    need(len(rows) == 3, "THREE_DISTINCT_CONTOURS")
    need("local x=side*410" in spec and
         "local z=(index-2)*270+side*contour.drift" in spec and
         "for _,side in ipairs({-1,1}) do" in spec, "FIXED_HORIZON_COORDINATES")
    seen = set()
    for index, values in enumerate(rows, 1):
        h, yaw, drift, depth, lean, notch = map(int, values)
        need(12 <= h <= 28 and 24 <= depth <= 38, "SILHOUETTE_SCALE")
        need(abs(yaw) <= 32 and abs(drift) <= 24 and abs(lean) <= 9
             and 0 <= notch <= 4, "SILHOUETTE_SKEW")
        yaw_r = math.radians(abs(yaw))
        half_base_x = 9 * math.cos(yaw_r) + depth / 2 * math.sin(yaw_r)
        cap_yaw_r = math.radians(abs(yaw * .7))
        half_cap_x = 5.5 * math.cos(cap_yaw_r) + (depth - 6) / 2 * math.sin(cap_yaw_r)
        # Conservative skew margin for the 3D tilted wedge bounding box.
        base_inner_x = 410 + notch - half_base_x - 2
        cap_inner_x = 410 - (2 + notch * .25) - half_cap_x - 2
        need(min(base_inner_x, cap_inner_x) >= 388,
             "HORIZON_FULL_WEDGE_FOOTPRINT")
        for side in (-1, 1):
            x, z = side * 410, (index - 2) * 270 + side * drift
            need(abs(x) >= 405 and abs(z) <= 310, "ROUTE_CLEARANCE")
            need((x, z) not in seen, "DUPLICATE_RIDGE_ANCHOR")
            seen.add((x, z))
    need(len(seen) == 6, "SIX_GEOMETRY_ANCHORS")


def verify_stylized_low_cost_art(spec: str) -> None:
    """P0 #420 source-level material guard, not a rendered beauty verdict."""
    forbidden = (
        "Enum.Material.Neon",
        "Enum.Material.Glass",
        "BillboardGui",
        "SurfaceGui",
        "ParticleEmitter",
        "PointLight",
        "SurfaceLight",
        "SpotLight",
        "Instance.new(",
    )
    need(not any(token in spec for token in forbidden),
         "NO_GLARE_HUD_OR_EXTRA_INSTANCES")
    need(spec.count("createVisual(arena,art,") == 2 and
         spec.count("Enum.Material.Slate") == 1 and
         spec.count("Enum.Material.Limestone") == 1,
         "TWO_MATTE_STONE_SURFACES_ONLY")
    need("local baseTint=darkStone:Lerp(limestone,.07*(index-1))" in spec and
         "local crownTint=limestone:Lerp(darkStone,.08*(3-index))" in spec,
         "PALETTE_VARIATION_NOT_IN_PER_FRAME_LOOP")


def verify_atomic_source_contract(source: str) -> None:
    """Test actual inserted source tokens, not merely a test model's booleans."""
    start = source.find("local function drawHorizonRidges(arena:Instance,art:Instance,ground:(number,number)->Vector3)")
    end = source.find("local function paintArena(arena:Instance)", start)
    need(start >= 0 and end > start, "RIDGE_ATOMIC_BODY_SCOPE")
    block = source[start:end]
    markers = (
        "(budgets[arena] or 0)+2<=MAX_VISUAL_PARTS_PER_ARENA",
        "if basePart then",
        "if crownPart then",
        "table.insert(bucket,basePart)",
        "table.insert(bucket,crownPart)",
        "basePart:Destroy()",
        "budgets[arena]=math.max(0,(budgets[arena] or 0)-1)",
    )
    need(all(block.count(x) == 1 for x in markers),
         "RUNTIME_PAIR_BUDGET_OR_REFUND_CONTRACT")
    # Pair is reserved before either allocation; bucket is committed only
    # after both allocations succeeded, with a refund on second failure.
    indices = [block.index(x) for x in markers]
    need(indices[0] < indices[1] < indices[2] < indices[3] <
         indices[4] < indices[5] < indices[6],
         "RUNTIME_PAIR_ORDER_AND_ATOMICITY")
    need(block.count("createVisual(arena,art,") == 2,
         "EXACTLY_TWO_RIDGE_VISUAL_ALLOCATIONS")
    need("if bucket then return end" in block and
         "ridgeVisuals[arena]=nil" in block,
         "RIDGE_REPAINT_AND_TEARDOWN")


def patch(source: str) -> str:
    verify_contour_geometry(RIDGE)
    verify_stylized_low_cost_art(RIDGE)
    need(MARK not in source, "DUPLICATE")
    need(source.count(PRIOR) == 1, "FORTRESS_904_ANCESTRY")
    need(source.count("local MAX_CASTLE_PARTS = 19") == 1, "CASTLE_BUDGET_DRIFT")
    need(source.count("local MAX_VISUAL_PARTS_PER_ARENA = 320") == 1, "MOBILE_BUDGET_DRIFT")
    need(source.count(FUNCTION_ANCHOR) == 1, "PAINT_ANCHOR_DRIFT")
    need(source.count(CALL_ANCHOR) == 1, "SCENE_ANCHOR_DRIFT")
    need("p.CanCollide=false" in source and "p.CanQuery=false" in source and
         "p.CastShadow=false" in source, "NONPHYSICAL_ART_GUARD")
    need(source.count(BUDGET_ANCHOR) == 1, "BUDGET_TABLE_ANCHOR")
    need(source.count(CREATE_VISUAL_GUARD) == 1, "VISUAL_GUARD_ANCHOR")
    out = source.replace(BUDGET_ANCHOR, BUDGET_ANCHOR + PRIORITY_BUDGET)
    out = out.replace(CREATE_VISUAL_GUARD, PRIORITY_GUARD)
    out = out.replace(FUNCTION_ANCHOR, RIDGE + FUNCTION_ANCHOR)
    out = out.replace(CALL_ANCHOR, CALL_ANCHOR + CALL)
    need(out.count("reclaimRidgeForCastle(arena)") == 1 and
         out.count("table.insert(bucket,") == 2 and
         out.count("arena.Destroying:Once(function()") == 1 and
         out.count("if bucket then return end") == 1, "CASTLE_PRIORITY_AND_SCENE_CLEANUP")
    need(out.count(MARK) == 2 and out.count("drawHorizonRidges(arena,art,onGround)") == 1,
         "SOURCE_INSERT_COUNT")
    need("RemoteEvent" not in RIDGE and "Tool" not in RIDGE and "DataStore" not in RIDGE,
         "NO_AUTHORITY")
    verify_atomic_source_contract(out)
    return out

def selftest() -> None:
    minimal = ("local MAX_CASTLE_PARTS = 19\n"
               "local MAX_VISUAL_PARTS_PER_ARENA = 320\n"
               + BUDGET_ANCHOR + CREATE_VISUAL_GUARD + "\n"
               "-- " + PRIOR + "\n"
               "p.CanCollide=false;p.CanQuery=false;p.CastShadow=false\n"
               + FUNCTION_ANCHOR + "\n"
               + CALL_ANCHOR)
    result = patch(minimal)
    verify_contour_geometry(RIDGE)
    verify_stylized_low_cost_art(RIDGE)
    for style_mutant in (
        RIDGE.replace("Enum.Material.Slate", "Enum.Material.Neon", 1),
        RIDGE.replace("Enum.Material.Limestone", "Enum.Material.Glass", 1),
        RIDGE + "Instance.new(\\\"BillboardGui\\\")",
        RIDGE.replace("local baseTint=darkStone:Lerp(limestone,.07*(index-1))",
                      "local baseTint=darkStone", 1),
    ):
        try:
            verify_stylized_low_cost_art(style_mutant)
        except ValueError:
            pass
        else:
            raise AssertionError("STYLIZED_ART_NEGATIVE_MUTANT_ACCEPTED")
    ridge_start = result.index("local function drawHorizonRidges(")
    ridge_end = result.index(FUNCTION_ANCHOR, ridge_start)
    ridge_block = result[ridge_start:ridge_end]
    for guard, altered in (
        ("(budgets[arena] or 0)+2<=MAX_VISUAL_PARTS_PER_ARENA",
         "(budgets[arena] or 0)+1<=MAX_VISUAL_PARTS_PER_ARENA"),
        ("if crownPart then", "if true then"),
        ("table.insert(bucket,crownPart)", "table.insert(bucket,basePart)"),
        ("basePart:Destroy()", "basePart:ClearAllChildren()"),
        ("budgets[arena]=math.max(0,(budgets[arena] or 0)-1)",
         "budgets[arena]=math.max(0,(budgets[arena] or 0)+1)"),
    ):
        need(ridge_block.count(guard) == 1, "ATOMIC_MUTANT_TEST_ANCHOR")
        mutant_source = (result[:ridge_start] +
                         ridge_block.replace(guard, altered, 1) +
                         result[ridge_end:])
        try:
            verify_atomic_source_contract(mutant_source)
        except ValueError:
            pass
        else:
            raise AssertionError("ATOMIC_RIDGE_SOURCE_MUTANT_ACCEPTED")
    for mutant in (
        RIDGE.replace("height=14", "height=2", 1),
        RIDGE.replace("depth=27", "depth=230", 1),
        RIDGE.replace("lean=-7", "lean=-27", 1),
        RIDGE.replace("drift=-16", "drift=-316", 1),
        RIDGE.replace("yaw=-19", "yaw=-119", 1),
        RIDGE.replace("notch=3", "notch=33", 1),
        RIDGE.replace("local x=side*410", "local x=side*300", 1),
        RIDGE.replace("local z=(index-2)*270", "local z=(index-2)*120", 1),
    ):
        try:
            verify_contour_geometry(mutant)
        except ValueError:
            pass
        else:
            raise AssertionError("RIDGE_GEOMETRY_MUTANT_ACCEPTED")
    need("local baseTint=darkStone:Lerp(limestone,.07*(index-1))" in result and
         "local crownTint=limestone:Lerp(darkStone,.08*(3-index))" in result,
         "MATTE_COLOR_DEPTH_NO_ADDED_PARTS")
    need("contour.depth-6" in result and "math.rad(-lean*1.4)" in result
         and "CFrame.new(at+Vector3.new(-side*(2+contour.notch*.25),h+.75,side*2))" in result,
         "SCULPTED_CAP_AND_BASE_MISSING")
    need("(budgets[arena] or 0)+2<=MAX_VISUAL_PARTS_PER_ARENA" in result
         and "if basePart then" in result and "if crownPart then" in result
         and "basePart:Destroy()" in result
         and "budgets[arena]=math.max(0,(budgets[arena] or 0)-1)" in result,
         "ATOMIC_TWOPART_RIDGE_AND_REFUND")
    need("for index=1,3 do" in result and "drawHorizonRidges" in result
         and "local ridgeContours" in result and "local contour=ridgeContours[index]" in result
         and "arena.Destroying:Once(function()" in result
         and "if bucket then return end" in result,
         "HAPPY_PATH_IRREGULAR_CONTOURS")
    for broken in (minimal.replace(PRIOR, "missing"),
                   minimal.replace("= 320", "= 600"),
                   minimal.replace(CALL_ANCHOR, ""),
                   minimal.replace(BUDGET_ANCHOR, ""),
                   minimal.replace(CREATE_VISUAL_GUARD, ""),
                   result):
        try:
            patch(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("NEGATIVE_MUTANT_WAS_ACCEPTED")
    print("GQ470_RIDGE_SCULPTED_6_ANCHORS_12_WEDGES_8_GEOMETRY_MUTANTS_PASS")
    print("GQ470_RIDGE_ATOMIC_TWO_PART_BUDGET_AND_REFUND_GUARD_PASS")
    print("GQ470_RIDGE_5_ATOMIC_SOURCE_MUTATIONS_REJECTED")
    print("GQ470_RIDGE_4_MATTE_STYLE_AND_MOBILE_NEGATIVES_PASS")
    print("GQ470_RIDGE_PATCH_AND_6_SOURCE_NEGATIVES_PASS")

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
        "arena_destroy_cleanup": "Destroying:Once clears ridgeVisuals key and part references",
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
