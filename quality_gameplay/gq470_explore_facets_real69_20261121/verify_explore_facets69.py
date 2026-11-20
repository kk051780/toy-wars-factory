#!/usr/bin/env python3
"""A-source REAL69 visual patch: 4 Realm stones + 6 StarShards.

Uses the real edited Luau source from this PR, not a toy-only Lua replacement.
Copies the original 69-script canonical Place into OFF69 and selects one real
visual source for the candidate. SOURCE PASS != Studio/ART/MOBILE/FUN PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FEATURE = "GQ470_FB015_EXPLORATION_FACETS_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_LegacyExplorationBridge"
SOURCE_FILE = REPO_ROOT / "quality_gameplay/gq8_rc85_rc86_exploration_20261119/EGGRUMBLE_LegacyExplorationBridge.server.luau"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_EXPLORATION_FACETS"
REPORT = "EXPLORATION_FACETS_SOURCE_REPORT.json"

def check(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_EXPLORE_" + reason)

def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    root = root.resolve()
    tree = json.loads((root / PROJECT).read_text(encoding="utf-8"))["tree"]
    found: dict[str, Path] = {}
    def visit(value: object, route: str = "") -> None:
        if not isinstance(value, dict):
            return
        if "$path" in value:
            raw = value["$path"]
            check(isinstance(raw, str), "PATH_NOT_STRING")
            path = (root / raw).resolve()
            check(path.is_relative_to(root) and path.is_file(), "PATH_ESCAPE")
            check(route not in found, "DUPLICATE_ROUTE")
            found[route] = path
        for key, node in value.items():
            if not key.startswith("$"):
                visit(node, route + "/" + key if route else key)
    visit(tree)
    return found

def check_visual(new: str) -> None:
    check(new.count(FEATURE) == 1, "FEATURE_MARKER")
    check(new.count('Instance.new("WedgePart")') == 1, "ONE_FACET_FACTORY")
    check(new.count('local function makeFacet(') == 1, "ONE_HELPER")
    check(new.count('local isRealm=kind=="REALM"') == 1, "REALM_SHARD_FAMILY")
    check(new.count('local core=makeFacet(id.."_Artifact",') == 1,
          "EXISTING_CORE_ID")
    check(new.count('makeFacet(id.."_Relief",') == 1, "EXISTING_RELIEF_ID")
    check(new.count('makePart(id.."_Pedestal",') == 1, "EXISTING_PEDESTAL")
    check(new.count('local prompt=Instance.new("ProximityPrompt")') == 1
          and new.count('prompt.Parent=core') == 1, "EXISTING_PROMPT")
    check(new.count('{"REALM_') == 4 and new.count('{"SHARD_') == 6,
          "TEN_DISCOVERABLE_OBJECTIVES")
    check('p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false' in new,
          "NO_COLLISION_TOUCH_QUERY")
    check('p.CastShadow=false' in new, "NO_SHADOW")
    check('p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth' in new,
          "MATTE_SMOOTH_SHAPE")
    check('if isRealm then Enum.Material.Slate else Enum.Material.SmoothPlastic' in new,
          "NO_NEON_CORE")
    check('if isRealm then Color3.fromRGB(223,229,221) else Color3.fromRGB(255,239,188)' in new,
          "TWO_TONE_MATTE")
    check('Vector3.new(2.7,3.25,2.2)' in new
          and 'Vector3.new(1.55,2.5,1.4)' in new
          and 'Vector3.new(1.05,2.15,1.2)' in new
          and 'Vector3.new(.72,1.65,.8)' in new,
          "BOUNDED_2_FACETS_PER_OBJECTIVE")
    check('root.Position-point).Magnitude>10' in new
          and 'workspace:Raycast(rayStart,rayDirection,rayParams)' in new
          and 'arena.Destroying:Connect(function()' in new,
          "AUTHORITATIVE_DISCOVERY_AND_CLEANUP")
    check('if not RunService:IsStudio() then return end' in new,
          "STUDIO_ONLY")
    check('local function makePart(' in new, "EXISTING_PEDESTAL_FACTORY")

def only_visual_change(old: str, new: str) -> None:
    check_visual(new)
    mark = "-- " + FEATURE
    start = new.index(mark)
    end = new.index("local function install(arena:Instance,mode:string)", start)
    check(new[start:end].count('Instance.new("WedgePart")') == 1,
          "ONLY_ONE_WEDGE_CONSTRUCTOR")
    old_start = old.index('  local core=makePart(id.."_Artifact"')
    new_start = new.index('  -- Four big asymmetric matte realm monoliths')
    old_end = old.index('  local prompt=Instance.new("ProximityPrompt")', old_start)
    new_end = new.index('  local prompt=Instance.new("ProximityPrompt")', new_start)
    removed_helper = new[:start] + new[end:]
    rebuilt = removed_helper[:new_start - (end - start)] + old[old_start:old_end] + removed_helper[new_end - (end - start):]
    check(rebuilt == old, "STRICT_RECONSTRUCTION_OUTSIDE_ART")
    check(old[old_end:] == new[new_end:], "EXISTING_GAMEPLAY_AUTHORITY_BYTE_EXACT")
    check(old.count('Instance.new("ProximityPrompt")') == new.count('Instance.new("ProximityPrompt")'),
          "PROMPT_COUNT_UNCHANGED")
    check(old.count('makePart(id.."_Pedestal"') == 1, "ONE_PEDESTAL_FACTORY_CALL")
    check(old[old_start:old_end].count('makePart(') == 2
          and new[new_start:new_end].count('makeFacet(') == 2, "TWO_FOR_TWO_PARTS")
    check(new.count('Instance.new("RemoteEvent")') == old.count('Instance.new("RemoteEvent")') == 0,
          "NO_REMOTES")
    check(new.count('Instance.new("Highlight")') == old.count('Instance.new("Highlight")'),
          "EXISTING_HIGHLIGHT_ONLY")

def self_test() -> None:
    source = SOURCE_FILE.read_text(encoding="utf-8")
    check_visual(source)
    # The known-good source must reject intentional visual/authority regressions.
    mutations = (
        ('p.CanCollide=false', 'p.CanCollide=true'),
        ('p.CanQuery=false', 'p.CanQuery=true'),
        ('p.CastShadow=false', 'p.CastShadow=true'),
        ('Instance.new("WedgePart")', 'Instance.new("Part")'),
        ('makeFacet(id.."_Relief",', 'makePart(id.."_Relief",'),
        ('prompt.Parent=core', 'prompt.Parent=folder'),
        ('{"SHARD_6"', '{"SHARD_SIX"'),
        ('local isRealm=kind=="REALM"', 'local isRealm=true'),
        ('Vector3.new(1.55,2.5,1.4)', 'Vector3.new(20,25,14)'),
        ('if not RunService:IsStudio() then return end', '-- not fenced'),
    )
    # The SHARD naming mutation above changes one specific token while retaining
    # the number of markers. Explicitly reject the missing unique objective too.
    for index, (good, bad) in enumerate(mutations):
        check(good in source, "TEST_ANCHOR_" + str(index))
        mutant = source.replace(good, bad, 1)
        try:
            check_visual(mutant)
            if index == 6:
                check('{"SHARD_6"' in mutant, "SHARD6_ID_PRESERVED")
        except ValueError:
            continue
        raise AssertionError("RED_VISUAL_MUTATION_ACCEPTED_" + str(index))
    print("EXPLORATION_FACETS_10_SOURCE_MUTATIONS_REJECTED")

def build_candidate(root: Path) -> None:
    root = root.resolve()
    manifest = selected(root)
    check(len(manifest) == 69 and ROUTE in manifest, "SELECTED_REAL69")
    original = {k: digest(p.read_bytes()) for k, p in manifest.items()}
    receipt_file = root / RECEIPT
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    check(receipt.get("canonical_build") is True
          and receipt.get("build_head") == BASE
          and receipt.get("selected_source_count") == 69
          and receipt.get("source_hashes") == original,
          "EXACT_OFFICIAL_SOURCE_LOCK")
    candidate_source = SOURCE_FILE.read_bytes()
    original_source = manifest[ROUTE].read_bytes()
    only_visual_change(original_source.decode("utf-8"),
                       candidate_source.decode("utf-8"))
    check(candidate_source != original_source, "NO_ACTUAL_VISUAL_CHANGE")
    off = root / OFF
    check(not off.exists() and (root / PLACE).is_file()
          and (root / "sources").is_dir(), "CLEAN_ARTIFACT")
    off.mkdir()
    shutil.copytree(root / "sources", off / "sources")
    for name in (PROJECT, RECEIPT, PLACE):
        shutil.copyfile(root / name, off / name)
    manifest[ROUTE].write_bytes(candidate_source)
    after = {k: digest(p.read_bytes()) for k, p in selected(root).items()}
    check(len(after) == 69
          and {k for k in original if original[k] != after[k]} == {ROUTE},
          "ONLY_ONE_SELECTED_SOURCE_68_EXACT")
    check(selected(off)[ROUTE].read_bytes() == original_source,
          "OFF_ORIGINAL_SOURCE")
    check((off / PROJECT).read_bytes() == (root / PROJECT).read_bytes(),
          "PROJECT_UNCHANGED")
    report = {
        "feature_id": FEATURE,
        "status": "PASS_SOURCE_ONLY",
        "formal_rc_head_original": BASE,
        "changed_selected_routes": [ROUTE],
        "unchanged_selected_routes": 68,
        "expected_objectives": {"realm": 4, "shard": 6},
        "decorative_parts_per_objective_old_new": [3, 3],
        "all_old_prompt_gameplay_logic_byte_exact": True,
        "real_studio": "NOT_TESTED",
        "android15": "NOT_TESTED",
        "screenshots_received": 0,
        "screenshots_required": 32,
        "human_art": "NOT_TESTED",
        "kid_fun": "NOT_TESTED",
        "owner_accepted": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
        "formal_rc_adopted": False,
        "reversible_off_directory": OFF,
        "old_sha256": digest(original_source),
        "candidate_sha256": digest(candidate_source),
    }
    receipt["source_hashes"][ROUTE] = after[ROUTE]
    receipt["gq470_exploration_facets"] = report
    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    (root / REPORT).write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8")
    check(json.loads(receipt_file.read_text())["source_hashes"] == after,
          "NEW_RECEIPT_HASHES")
    print("EXPLORATION_FACETS_REAL69_A_SOURCE_PREP_PASS_" + after[ROUTE])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        check(args.base is not None, "NEED_REAL_CANONICAL_ARTIFACT")
        build_candidate(args.base)
