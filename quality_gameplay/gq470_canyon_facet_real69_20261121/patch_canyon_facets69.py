#!/usr/bin/env python3
"""A-only, reversible ART fix for the existing REAL69 LegacyCanyonRoutes.

Seven bridge-side glowing box primitives become seven low-glare faceted
WedgeParts at the two banks. No new Parts, routes, physics, prompts, AI,
gameplay authority or player UI. This is source preparation, NOT an ART pass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FEATURE = "GQ470_FB015_CANYON_FACET_SHORELINE_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_CANYON_FACETS"
AUTHOR_MARK = "GQ8_RC85_RC86_WCS_STARRY_METEOR_REAL67_20261119"

OLD = ''' for i=1,7 do
  local crystal=block("CanyonCrystal_"..i,Vector3.new(2,7+i%3*2,2),
   Vector3.new(-23+i*6,3,-13),violet,Enum.Material.Neon,false,.13)
  crystal.CanQuery=false
 end
'''
NEW = ''' -- GQ470_FB015_CANYON_FACET_SHORELINE_REAL69_20261121
 -- Original 7 neon block crystals sat across X=-17..19 on the short bridge.
 -- EXACTLY 7 angular matte WedgeParts, now on either bank outside X +/-25.
 -- No extra Part instances, collision, touch, query, cast shadows or UI.
 stage:SetAttribute("CanyonFacetVisualBudget",7)
 for i=1,7 do
  local rightBank=(i%2==1)
  local bankX=if rightBank then 32 else -32
  local shoreZ=-29+(i-1)*10
  local h=7+(i%3)*1.5
  local facet=Instance.new("WedgePart")
  facet.Name="CanyonShoreFacet_"..i
  facet.Size=Vector3.new(2.2,h,2)
  facet.CFrame=origin*CFrame.new(bankX,h/2-.25,shoreZ)
   *CFrame.Angles(0,math.rad((i*41)%360),
    math.rad((rightBank and 1 or -1)*7))
  facet.Material=Enum.Material.SmoothPlastic
  facet.Color=if i%3==0 then blue else violet
  facet.Transparency=.04
  facet.Anchored=true
  facet.CanCollide=false
  facet.CanTouch=false
  facet.CanQuery=false
  facet.CastShadow=false
  facet.TopSurface=Enum.SurfaceType.Smooth
  facet.BottomSurface=Enum.SurfaceType.Smooth
  facet.Parent=stage
 end
'''

def demand(ok: bool, name: str) -> None:
    if not ok:
        raise ValueError("RED_CANYON_FACET_" + name)

def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    document = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    out: dict[str, Path] = {}
    base = root.resolve()
    def walk(node: object, route: str = "") -> None:
        if not isinstance(node, dict):
            return
        if "$path" in node:
            raw = node["$path"]
            demand(isinstance(raw, str), "PATH_TYPE")
            found = (base / raw).resolve()
            demand(found.is_relative_to(base) and found.is_file(), "PATH_ESCAPE")
            demand(route not in out, "DUPLICATE_ROUTE")
            out[route] = found
        for key, child in node.items():
            if not key.startswith("$"):
                walk(child, route + "/" + key if route else key)
    walk(document["tree"])
    return out

def verify_visual_contract(fragment: str) -> None:
    """Fail closed if styling changes reintroduce physics or blocked corridors.

    This is a source/geometry upper-bound check, NOT actual camera visibility.
    """
    constructors = re.findall(r'Instance\\.new\\("([^"]+)"\\)', fragment)
    demand(constructors == ["WedgePart"], "ONE_WEDGE_PART_FACTORY")
    demand(fragment.count("for i=1,7 do") == 1 and
           fragment.count('facet.Parent=stage') == 1 and
           fragment.count('stage:SetAttribute("CanyonFacetVisualBudget",7)') == 1,
           "ONLY_SEVEN_DECORATIONS")
    assignments = re.findall(
        r'(?m)^\\s*facet\\.(CanCollide|CanTouch|CanQuery|CastShadow)\\s*=\\s*(\\w+)',
        fragment)
    expected = [(key, "false") for key in
                ("CanCollide", "CanTouch", "CanQuery", "CastShadow")]
    demand(sorted(assignments) == sorted(expected),
           "EXACTLY_ONE_NO_PHYSICS_SETTER_EACH")
    demand(fragment.count("facet.Anchored=true") == 1 and
           fragment.count("facet.Material=Enum.Material.SmoothPlastic") == 1,
           "MATTE_STATIC")
    demand('facet.Transparency=.04' in fragment and
           'facet.Size=Vector3.new(2.2,h,2)' in fragment,
           "VISUAL_SIZE")
    demand('local bankX=if rightBank then 32 else -32' in fragment and
           'local shoreZ=-29+(i-1)*10' in fragment and
           'local h=7+(i%3)*1.5' in fragment,
           "PINNED_GEOMETRY")
    demand("Enum.Material.Neon" not in fragment and
           "BillboardGui" not in fragment and
           "ProximityPrompt" not in fragment,
           "NO_NEON_GUI_PROMPT")
    for i in range(1, 8):
        x = 32 if i % 2 else -32
        z = -29 + (i-1)*10
        height = 7 + (i%3)*1.5
        # Conservatively upper-bound rotation-expanded footprint in X.
        max_half_x = 2.2/2 + math.sin(math.radians(7))*height/2 + 2/2
        demand(abs(x)-max_half_x >= 29, "STUD4_SAFE_CENTER_MARGIN")
        demand(abs(z)+2.5 <= 42.5, "BANK_LONGITUDINAL_BOUNDS")

def transform(source: str) -> str:
    demand(FEATURE not in source, "DOUBLE_APPLY")
    demand(AUTHOR_MARK in source, "ORIGINAL_AUTHOR")
    demand(source.count(OLD) == 1, "EXACT_ORIGINAL_CRYSTALS")
    demand('if not RunService:IsStudio() then return end' in source,
           "STUDIO_FENCE")
    demand('local function setGate(open:boolean)' in source and
           'local function authorized(p:Player,target:BasePart):boolean' in source,
           "GAMEPLAY_OWNERS")
    demand('local safe=block("AlwaysOpenSafeRoute"' in source and
           'local shortcut=block("ShortcutBridge"' in source,
           "SAFE_ROUTES")
    demand('stage:SetAttribute("SafeRouteAlwaysAvailable",true)' in source,
           "SAFE_ROUTE_MARK")
    candidate = source.replace(OLD, NEW, 1)
    demand(candidate.count(FEATURE) == 1 and
           candidate.count('Instance.new("WedgePart")') ==
           source.count('Instance.new("WedgePart")') + 1,
           "ONE_FACET_FACTORY")
    verify_visual_contract(NEW)
    demand(NEW.count("Instance.new(") == 1, "SEVEN_ONLY")
    demand('local bankX=if rightBank then 32 else -32' in NEW and
           'local shoreZ=-29+(i-1)*10' in NEW, "SHORE_NOT_BRIDGE")
    demand('facet.CanCollide=false' in NEW and
           'facet.CanQuery=false' in NEW and
           'facet.CanTouch=false' in NEW and
           'facet.CastShadow=false' in NEW, "MOBILE_NONPHYSICAL")
    demand('Enum.Material.Neon' not in NEW and
           'BillboardGui' not in NEW and 'ProximityPrompt' not in NEW,
           "NO_UI_NEON_PROMPTS")
    # Every byte outside the unique crystal block remains exactly unchanged.
    before, after = source.split(OLD, 1)
    demand(candidate == before + NEW + after, "SOURCE_ONLY_SCOPE")
    return candidate

def self_test() -> None:
    sample = (
        "-- " + AUTHOR_MARK + "\n"
        + 'if not RunService:IsStudio() then return end\n'
        + 'local function setGate(open:boolean)\nend\n'
        + 'local function authorized(p:Player,target:BasePart):boolean\nend\n'
        + 'stage:SetAttribute("SafeRouteAlwaysAvailable",true)\n'
        + 'local safe=block("AlwaysOpenSafeRoute"\n'
        + 'local shortcut=block("ShortcutBridge"\n'
        + OLD)
    changed = transform(sample)
    demand('CanyonShoreFacet_' in changed and
           'CanyonFacetVisualBudget",7' in changed,
           "POSITIVE")
    for bad in (
        NEW.replace('facet.CanCollide=false', 'facet.CanCollide=true'),
        NEW.replace('facet.CanQuery=false', 'facet.CanQuery=false\\n  facet.CanQuery=true'),
        NEW.replace('facet.CastShadow=false', 'facet.CastShadow=true'),
        NEW.replace('Instance.new("WedgePart")', 'Instance.new("Part")'),
        NEW.replace("for i=1,7 do", "for i=1,8 do"),
        NEW.replace('facet.Parent=stage', 'facet.Parent=stage\\n  facet.Parent=stage'),
        NEW.replace('local bankX=if rightBank then 32 else -32',
                    'local bankX=if rightBank then 25 else -25'),
    ):
        try:
            verify_visual_contract(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_CANYON_VISUAL_CONTRACT_MUTANT_ACCEPTED")
    print("GQ470_CANYON_7_ADDITIONAL_VISUAL_SAFETY_NEGATIVES_PASS")
    for mutant in (
        changed,
        sample.replace(OLD, ""),
        sample.replace("RunService:IsStudio()", "RunService:IsServer()"),
        sample.replace('AlwaysOpenSafeRoute', 'UnsafeRoute'),
        sample.replace('local function setGate', 'local function noGate'),
        sample.replace('SafeRouteAlwaysAvailable",true',
                       'SafeRouteAlwaysAvailable",false'),
        sample.replace('CanyonCrystal_', 'CanyonBeacon_'),
    ):
        try:
            transform(mutant)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_CANYON_MUTANT_ACCEPTED")
    demand(NEW.count('facet.Parent=stage') == 1, "SINGLE_PARENT")
    # Synthetic geometry contract: 7 parts, |x|=32 > bridge half-width 25.
    geometry = [(32 if i % 2 else -32, -29+(i-1)*10)
                for i in range(1, 8)]
    demand(len(geometry) == 7 and
           all(abs(x) > 25 and -42.5 < z < 42.5 for x, z in geometry),
           "SEVEN_BANK_FACETS_AND_SAFE_CENTER")
    print("GQ470_CANYON_7_NEGATIVE_MUTATIONS_GEOMETRY_PASS")

def patch(root: Path) -> None:
    root = root.resolve()
    source_map = selected(root)
    demand(len(source_map) == 69 and ROUTE in source_map,
           "SELECTED69_TARGET")
    receipt_file = root / RECEIPT
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    original_hashes = {route: sha(p.read_bytes())
                       for route, p in source_map.items()}
    demand(receipt.get("canonical_build") is True and
           receipt.get("build_head") == BASE and
           receipt.get("selected_source_count") == 69,
           "OFFICIAL_BASE")
    demand(receipt.get("source_hashes") == original_hashes,
           "ALL69_SOURCE_HASH_LOCK")
    original = source_map[ROUTE].read_bytes()
    replacement = transform(original.decode("utf-8")).encode("utf-8")
    demand(replacement != original, "ACTUAL_SOURCE_DELTA")
    off = root / OFF
    demand(not off.exists() and (root / "sources").is_dir() and
           (root / PLACE).is_file(), "ORIGINAL_ARTIFACT")
    off.mkdir()
    shutil.copytree(root / "sources", off / "sources")
    for fn in (PROJECT, RECEIPT, PLACE):
        shutil.copyfile(root / fn, off / fn)
    source_map[ROUTE].write_bytes(replacement)
    after = {route: sha(p.read_bytes()) for route, p in selected(root).items()}
    changed = {route for route in after if
               after[route] != original_hashes[route]}
    demand(changed == {ROUTE} and len(after) == 69,
           "ONE_SOURCE_ONLY_68_BYTE_EXACT")
    demand((off / PROJECT).read_bytes() == (root / PROJECT).read_bytes(),
           "PROJECT_UNCHANGED")
    demand(selected(off)[ROUTE].read_bytes() == original,
           "OFF_EXACT_SOURCE")
    receipt["source_hashes"][ROUTE] = sha(replacement)
    receipt["gq470_canyon_facet_shoreline"] = {
        "feature_id": FEATURE,
        "selected_route": ROUTE,
        "official_parent": BASE,
        "changed_selected_routes": 1,
        "unchanged_selected_routes": 68,
        "decorative_parts_old_new": [7, 7],
        "shore_x_abs_studs": 32,
        "bridge_half_width_studs": 25,
        "nonphysical": True,
        "new_remotes": 0,
        "new_combat_score_egg_authority": False,
        "rollback": OFF,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "human_art": "NOT_TESTED",
        "kid_fun": "NOT_TESTED",
        "owner_accepted": False
    }
    receipt_file.write_text(json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print("GQ470_CANYON_FACET_REAL69_ONE_SOURCE_OFF69_READY",
          sha(replacement))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    options = parser.parse_args()
    if options.self_test:
        self_test()
    else:
        demand(options.base is not None, "NEED_OFFICIAL_PACKAGE")
        patch(options.base)
