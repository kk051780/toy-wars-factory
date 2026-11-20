#!/usr/bin/env python3
"""One REAL69 selected TwinBiomes art-only reef/sign transformation, reversible.

Target is the current ONE official V3 private companion's exact selected Lua
source, not historical RC64 or a new/second Game/Host/Combat/HUD authority.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

BASE = "c226c63eeb235503f9292503b61f2173550337ec"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
TARGET = "ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
MARK = "GQ470_ART_REEF_ORGANIC_SIGN_READABLE_REAL69_20261120"
OLD_CORAL = """    for i = 1, 4 do
        local x = spec.x + (i - 2.5) * 4
        local reefStem = part("CoralBranch_" .. i, Vector3.new(1.6, 3.8 + i % 2, 1.6),
            x, 2.1, -29, i % 2 == 0 and coral or aqua, Enum.Material.Neon, false, reef)
        reefStem.Shape = Enum.PartType.Ball
    end
"""
NEW_CORAL = """    -- GQ470_ART_REEF_ORGANIC_SIGN_READABLE_REAL69_20261120
    -- Two sculpted, asymmetric matte limbs instead of a glowing ball per coral.
    -- Eight additional static, noncolliding Parts across BOTH shores combined.
    -- Geometry is decorative and stays off the bridge/egg route.
    reef:SetAttribute("ReefVisual", "MATTE_FORK_CORAL")
    reef:SetAttribute("DecorativeExtraParts", 4)
    for i = 1, 4 do
        local x = spec.x + (i - 2.5) * 4
        local tint = if i % 2 == 0 then coral else aqua
        local lean = if i % 2 == 0 then 1 else -1
        local stem = part("SculptedCoralStem_" .. i,
            Vector3.new(0.88, 3.3 + (i % 2) * 0.6, 0.8),
            x, 1.86, -29, tint, Enum.Material.SmoothPlastic, false, reef)
        stem.CFrame = stem.CFrame * CFrame.Angles(0, 0, math.rad(lean * 9))
        local fork = part("SculptedCoralFork_" .. i,
            Vector3.new(0.64, 2.2 + (i % 2) * 0.36, 0.7),
            x + lean * 0.82, 3.46, -29, tint,
            Enum.Material.SmoothPlastic, false, reef)
        fork.CFrame = fork.CFrame * CFrame.Angles(0, 0, math.rad(-lean * 39))
    end
"""
OLD_SIGN = """    gui.AlwaysOnTop = true
    gui.MaxDistance = 100
    gui.Size = UDim2.fromOffset(200, 62)
"""
NEW_SIGN = """    -- Avoid oversized floating signs obscuring egg/castle action on Android.
    -- Prompt interaction and team/species discovery remain unchanged.
    gui.AlwaysOnTop = false
    gui.MaxDistance = 38
    gui.Size = UDim2.fromOffset(166, 54)
"""

def require(condition: bool, key: str) -> None:
    if not condition:
        raise ValueError("RED_REEF_VISUAL_" + key)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    pr = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    out: dict[str, Path] = {}
    def walk(node, route=""):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            p = (root / node["$path"]).resolve()
            require(p.is_relative_to(root.resolve()) and p.is_file(), "SELECTED_PATH")
            require(route not in out, "DUPLICATE_SELECTED")
            out[route] = p
        for k, child in node.items():
            if not k.startswith("$"):
                walk(child, route + "/" + k if route else k)
    walk(pr["tree"])
    return out

def transform(source: str) -> str:
    require(MARK not in source, "DOUBLE_APPLY")
    require("GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119" in source, "ORIGINAL_AUTHOR")
    require(source.count(OLD_CORAL) == 1 and source.count(OLD_SIGN) == 1, "OLD_ART_ANCHOR")
    require("p.CanCollide = collide == true" in source and "p.CanQuery = collide == true" in source, "PHYSICS_HELPER")
    require('local function awardPractice(player, info, npc, crest)' in source, "PRACTICE_OWNER")
    new = source.replace(OLD_CORAL, NEW_CORAL, 1).replace(OLD_SIGN, NEW_SIGN, 1)
    require(new.count(MARK) == 1 and "reefStem.Shape = Enum.PartType.Ball" not in new, "BALL_NEON_REMOVED")
    require(new.count("SculptedCoralFork_") == 1 and new.count("gui.MaxDistance = 38") == 1, "NEW_GEOMETRY_SIGN")
    return new

def selftest() -> None:
    original = ('-- GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119\n'
        'p.CanCollide = collide == true; p.CanQuery = collide == true\n'
        'local function awardPractice(player, info, npc, crest) end\n'
        + OLD_CORAL + OLD_SIGN)
    out = transform(original)
    require("MATTE_FORK_CORAL" in out and "gui.AlwaysOnTop = false" in out, "POSITIVE")
    mutants = (out, original.replace(OLD_CORAL, ""),
               original.replace(OLD_SIGN, ""),
               original.replace("p.CanQuery = collide == true", "p.CanQuery = true"),
               original.replace("awardPractice", "fakePractice"))
    for mutant in mutants:
        try:
            transform(mutant)
        except ValueError:
            continue
        raise AssertionError("RED_REEF_MUTATION_NOT_BLOCKED")
    print("GQ470_REEF_SCULPT_SIGN_SELFTEST_5_NEGATIVES_PASS")

def apply(root: Path, current_head: str|None = None) -> None:
    original = selected(root)
    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(len(original) == 69 and TARGET in original, "REAL69_SELECTED_69")
    require(receipt.get("build_head") == (current_head or BASE) and receipt.get("selected_source_count") == 69, "BASE_HEAD")
    require(set(original) == set(receipt.get("source_hashes", {})), "RECEIPT_ROUTE_SET")
    for route, path in original.items():
        require(sha(path.read_bytes()) == receipt["source_hashes"][route], "INPUT_DIGEST_" + route)
    off = root / "off69_reef"
    require(not off.exists(), "OFF_ALREADY_EXISTS")
    off.mkdir()
    for path in original.values():
        dest = off / path.relative_to(root.resolve())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    shutil.copyfile(root / PROJECT, off / PROJECT)
    shutil.copyfile(root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx", off / "EGGRUMBLE_REAL69_PRIVATE.rbxlx")
    old = original[TARGET].read_bytes()
    changed = transform(old.decode("utf-8")).encode("utf-8")
    original[TARGET].write_bytes(changed)
    current = selected(root)
    previous = selected(off)
    require(len(current) == len(previous) == 69 and set(current) == set(previous), "OFF_ROUTES")
    for route in current:
        require(previous[route].read_bytes() == (old if route == TARGET else current[route].read_bytes()),
                "OTHER_68_EXACT_" + route)
    require((off / PROJECT).read_bytes() == (root / PROJECT).read_bytes(), "PROJECT_CLASS_PATH")
    receipt["source_hashes"][TARGET] = sha(changed)
    receipt["gq470_reef_sculpt_visual"] = {
        "feature_id": MARK, "formal_parent": BASE, "selected_source": TARGET,
        "other_selected_routes_byte_exact": 68, "original_source_sha256": sha(old),
        "new_source_sha256": sha(changed), "new_part_count_across_2_reefs": 8,
        "old_sign_range_studs": 100, "new_sign_range_studs": 38,
        "collision_changed": False, "new_game_authority": False,
        "visual_evidence": "NOT_TESTED", "android_15min": "NOT_TESTED",
        "owner_accepted": False, "rollback": "off69_reef",
    }
    if current_head:
        receipt["build_head"] = current_head
        receipt["gq470_reef_sculpt_visual"]["source_adoption_base"] = current_head
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print("REEF_REAL69_EXISTING_OWNER_ONE_SOURCE_PATCH_OFF69_READY", sha(changed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--head", type=str, default=None)
    args = parser.parse_args()
    if args.self_test:
        selftest()
    else:
        require(args.base is not None, "NEED_BASE")
        apply(args.base, args.head)
