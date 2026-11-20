#!/usr/bin/env python3
"""GQ470 FB015: REAL69 selected HUD minimap matte/contrast patch, A-only."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
RUN = 44695199140
MARK = "GQ470_FB015_FILTERED_MINIMAP_MATTE_PINS_REAL69_20261121"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
ROLLBACK = "OFF69_MINIMAP_MATTE_ROLLBACK"

# All replacements are limited to the original server-filtered minimap's
# TextLabels and already-pooled fog cells; no camera, controls or authority.
PATCHES = (
    (
        """  v.TextColor3=Color3.fromRGB(255,255,255)
  v.BackgroundColor3=Color3.fromRGB(33,46,61)
  v.BackgroundTransparency=.08""",
        """  -- GQ470_FB015_FILTERED_MINIMAP_MATTE_PINS_REAL69_20261121
  -- Improve the pooled 20px markers; no new GUI instances or input hooks.
  v.TextColor3=Color3.fromRGB(247,250,249)
  v.TextStrokeColor3=Color3.fromRGB(12,23,31)
  v.TextStrokeTransparency=.38
  v.BackgroundColor3=Color3.fromRGB(38,57,69)
  v.BackgroundTransparency=.10""",
    ),
    (
        """ local count=0
 local nx=math.min(12,math.max(7,math.floor(width/12)))""",
        """ local count=0
 -- SEA/SKY/LAND remain distinct even on compact screens; all non-revealed
 -- cells use one dark tone. No extra per-cell gradients/parts/render loops.
 local revealedTint=if activeLayer=="SEA" then Color3.fromRGB(47,94,114)
  elseif activeLayer=="SKY" then Color3.fromRGB(86,101,117)
  else Color3.fromRGB(74,112,88)
 local hiddenTint=Color3.fromRGB(23,39,48)
 local nx=math.min(12,math.max(7,math.floor(width/12)))""",
    ),
    (
        """   f.BackgroundColor3=visited[index]
     and Color3.fromRGB(75,119,88) or Color3.fromRGB(30,49,59)
   f.BackgroundTransparency=visited[index] and .1 or .06""",
        """   f.BackgroundColor3=if visited[index] then revealedTint else hiddenTint
   f.BackgroundTransparency=visited[index] and .12 or .03""",
    ),
    (
        """    pin.BackgroundColor3=if m.kind=="SELF" then Color3.fromRGB(49,154,197)
      elseif m.kind=="ENEMY" then Color3.fromRGB(166,76,89)
      elseif m.precision=="SECTOR" then Color3.fromRGB(132,107,64)
      else Color3.fromRGB(71,105,119)""",
        """    -- Contrast by objective as well as icon; low-glare, matte fills.
    -- Sector-only intel is NOT upgraded to exact positioning here.
    pin.BackgroundColor3=if m.precision=="SECTOR" then Color3.fromRGB(113,90,62)
      elseif m.kind=="SELF" then Color3.fromRGB(43,118,148)
      elseif m.kind=="ALLY" then Color3.fromRGB(44,105,106)
      elseif m.kind=="ENEMY" then Color3.fromRGB(141,63,70)
      elseif m.kind=="CASTLE" and m.team=="RED" then Color3.fromRGB(141,69,75)
      elseif m.kind=="CASTLE" and m.team=="BLUE" then Color3.fromRGB(58,93,151)
      elseif m.kind=="CASTLE_GATE" then Color3.fromRGB(87,87,101)
      elseif m.kind=="EGG" then Color3.fromRGB(136,100,40)
      elseif m.kind=="MAGIC_TREASURE" then Color3.fromRGB(79,105,119)
      elseif m.kind=="RESOURCE" then Color3.fromRGB(74,106,70)
      elseif m.kind=="NEUTRAL" then Color3.fromRGB(93,83,71)
      elseif m.kind=="ENEMY_TRAIL" then Color3.fromRGB(112,78,57)
      else Color3.fromRGB(67,93,109)
    pin.BackgroundTransparency=mapExpanded and .04 or .10""",
    ),
    (
        """    pin.TextSize=mapExpanded and 13 or 10""",
        """    pin.TextSize=mapExpanded and 13 or 11""",
    ),
)

def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_MINIMAP_" + message)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch(src: str) -> str:
    need(MARK not in src, "ALREADY_PATCHED")
    need('EGGRUMBLE_MapIntelUpdate_V1' in src and
         'local function redraw()' in src and
         'local function mapPin(index)' in src and
         'actions.ATTACK.Activated:Connect' in src and
         's.explored or {}' in src and 's.markers or {}' in src,
         "REAL69_HUD_IDENTITY_DRIFT")
    need("GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120" in src,
         "FB019_ATTACK_VISUAL_NOT_PRESERVED")
    for index, (old, new) in enumerate(PATCHES):
        need(src.count(old) == 1, "ANCHOR_DRIFT_" + str(index))
        src = src.replace(old, new, 1)
    need(src.count(MARK) == 1 and src.count('local function redraw()') == 1,
         "PATCH_RESULT_SHAPE")
    return src

def selected(root: Path) -> dict[str, Path]:
    tree = json.loads((root / PROJECT).read_text(encoding="utf-8"))["tree"]
    result: dict[str, Path] = {}
    def visit(node: dict, route: str) -> None:
        if "$path" in node:
            result[route] = root / node["$path"]
        for name, value in node.items():
            if not name.startswith("$") and isinstance(value, dict):
                visit(value, route + "/" + name if route else name)
    visit(tree, "")
    return result

def selftest() -> None:
    body = """EGGRUMBLE_MapIntelUpdate_V1
local function mapPin(index)
GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120
actions.ATTACK.Activated:Connect
s.explored or {}
s.markers or {}
local function redraw()
""" + "\n".join(old for old, _ in PATCHES)
    good = patch(body)
    need(good.count(MARK) == 1 and
         'm.kind=="CASTLE" and m.team=="BLUE"' in good and
         'mapExpanded and 13 or 11' in good and
         'local revealedTint=' in good, "SELFTEST_PATCH_NOT_PRESENT")
    mutants = [
        good,
        body.replace(PATCHES[0][0], PATCHES[0][0].replace(".08", ".09")),
        body.replace(PATCHES[2][0], PATCHES[2][0].replace(".1 or .06", ".1 or .07")),
        body.replace(PATCHES[3][0], PATCHES[3][0].replace("166,76,89", "166,76,90")),
        body.replace(PATCHES[4][0], "    pin.TextSize=mapExpanded and 13 or 12"),
        body.replace("GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120", "MISSING_ATTACK"),
        body.replace("s.explored or {}", "no_fog"),
        body.replace("EGGRUMBLE_MapIntelUpdate_V1", "MISSING_REMOTE"),
    ]
    for i, mutant in enumerate(mutants):
        try:
            patch(mutant)
        except ValueError:
            continue
        raise AssertionError("RED_MUTATION_WAS_ACCEPTED_" + str(i))
    print("GQ470_MINIMAP_PATCH_8_NEGATIVE_MUTATIONS_PASS")

def apply(root: Path) -> None:
    routes = selected(root)
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    need(len(routes) == 69 and ROUTE in routes, "SELECTED_REAL69_MISSING")
    need(receipt.get("build_head") == BASE and
         len(receipt.get("source_hashes", {})) == 69,
         "IMMUTABLE_ORIGINAL_RECEIPT")
    original_hashes = {k: sha(p.read_bytes()) for k, p in routes.items()}
    need(original_hashes == receipt["source_hashes"], "ORIGINAL_SOURCE_LOCK")
    need(receipt["source_classes"].get(ROUTE) == "LocalScript",
         "ORIGINAL_CLASS")
    need(not (root / ROLLBACK).exists(), "ROLLBACK_COLLISION")
    target = routes[ROUTE]
    original = target.read_text(encoding="utf-8")
    need(original.encode("utf-8") == target.read_bytes(), "REAL_UTF8")
    modified = patch(original)
    for token in ('Instance.new(', 'FireServer(', ':Activate()', 'OnClientEvent',
                  'marketplace', 'TakeDamage', 'actions.ATTACK.Activated:Connect',
                  's.explored or {}', 's.markers or {}'):
        need(modified.count(token) == original.count(token),
             "AUTHORITY_OR_UI_INSTANCE_DELTA_" + token)
    shutil.copytree(root / "sources", root / ROLLBACK / "sources")
    shutil.copy2(root / PROJECT, root / ROLLBACK / PROJECT)
    target.write_text(modified, encoding="utf-8", newline="")
    after = {k: sha(p.read_bytes()) for k, p in routes.items()}
    need({k for k in routes if original_hashes[k] != after[k]} == {ROUTE},
         "ONLY_ONE_SELECTED_HUD_CHANGE")
    receipt["source_hashes"][ROUTE] = after[ROUTE]
    receipt["build_head"] = "A_PREP_NOT_CANONICAL_FROM_" + BASE
    receipt["gq470_minimap_matte"] = {
        "feature_id": MARK, "original_official_head": BASE,
        "parent_official_run": RUN, "selected_route": ROUTE,
        "class": "LocalScript", "selected_sources": 69,
        "unchanged_other_source_count": 68,
        "original_sha256": original_hashes[ROUTE],
        "candidate_sha256": after[ROUTE],
        "original_marker_instances": original.count('Instance.new('),
        "candidate_marker_instances": modified.count('Instance.new('),
        "new_3d_parts": 0, "new_gui_instances": 0, "new_remotes": 0,
        "new_runtime_scripts": 0,
        "preserved_fog_projection": True, "preserved_fb019_swing": True,
        "native_rojo": "NOT_TESTED", "engine": "NOT_TESTED",
        "android": "NOT_TESTED", "human_art": "NOT_TESTED",
        "real_before_after_png": 0, "formal_rc_adopted": False,
        "owner_accepted": False, "rollback": ROLLBACK,
    }
    (root / RECEIPT).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print("GQ470_MINIMAP_REAL69_1_SELECTED_HUD_68_OTHER_EXACT_PREP_PASS")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        selftest()
    else:
        need(args.base is not None, "NO_ORIGINAL_ARTIFACT")
        apply(args.base)

if __name__ == "__main__":
    main()
