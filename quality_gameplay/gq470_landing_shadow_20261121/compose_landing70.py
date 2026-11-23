#!/usr/bin/env python3
"""Isolated GQ470 matte landing marker intake; never edits official RC.

A REAL69 artifact must be supplied by the sole B writer or a source-locking CI job.
Creates reproducible ON70 and exact-byte OFF69 candidates in a temporary folder.
This script intentionally does not fetch GitHub content or write any branch ref.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

SOURCE_ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LandingShadow"
SOURCE_FILE = "EGGRUMBLE_LandingShadow.client.luau"
PROJECT = "EGGRUMBLE_REAL69.project.json"
OUTPUT_PROJECT = "EGGRUMBLE_LANDING70.project.json"


def demand(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("GQ470_LANDING_RED_" + reason)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_map(project_root: Path, project_name: str = PROJECT) -> dict[str, Path]:
    obj = json.loads((project_root / project_name).read_text(encoding="utf-8"))
    selected: dict[str, Path] = {}

    def walk(node: dict, route: tuple[str, ...]) -> None:
        demand(isinstance(node, dict), "BAD_PROJECT_TREE")
        if "$path" in node:
            path = (project_root / node["$path"]).resolve()
            demand(path.is_relative_to(project_root.resolve()), "OUTSIDE_SOURCE")
            demand(path.is_file(), "SOURCE_MISSING")
            key = "/".join(route)
            demand(key not in selected, "DUPLICATE_ROUTE")
            selected[key] = path
        for key, item in node.items():
            if not key.startswith("$"):
                walk(item, (*route, key))
    demand("tree" in obj, "TREE_MISSING")
    walk(obj["tree"], ())
    return selected


def check_art_source(source: str) -> None:
    required = (
        "EGGRUMBLE_LandingShadow_LocalOnly", "MAX_VISUAL_PARTS = 3",
        "SAMPLE_INTERVAL = 0.12", "Enum.Material.SmoothPlastic",
        "CanCollide = false", "CanTouch = false", "CanQuery = false",
        "CastShadow = false", "Enum.Material.Water", "CameraSubject",
        "Enum.HumanoidStateType.Freefall", "MIN_FALL_SPEED",
        "FilterDescendantsInstances = {character, effects}", "hide()",
        "EGGRUMBLE_ReducedEffects", "ReducedEffects",
        "EGGRUMBLE_LandingShadowOff", "visualDisabled(character)",
        "GetAttributeChangedSignal(flag)", "clearCharacterConnections()",
        "script.Destroying:Connect", "effects:Destroy()",
        "not hit.Instance.CanCollide",
        "hit.Instance.Transparency >= 0.95",
        "hit.Instance.Material == Enum.Material.Glass",
        "hit.Instance.LocalTransparencyModifier >= 0.95",
        'ancestor:FindFirstChildOfClass("Humanoid")',
    )
    for text in required:
        demand(text in source, "MISSING_GUARD_" + text.split()[0])
    prohibited = (
        "RemoteEvent", "RemoteFunction", "FireServer", "InvokeServer",
        "DataStoreService", "MarketplaceService", "HttpService",
        "Lighting", "ParticleEmitter", "PointLight", "SpotLight", "SurfaceLight",
        "Enum.Material.Neon", "TweenService", "BodyVelocity", "Instance.new(\"LinearVelocity\")",
        "AssemblyLinearVelocity =", "Humanoid:MoveTo", "TakeDamage",
    )
    for text in prohibited:
        demand(text not in source, "PROHIBITED_SIDE_EFFECT_" + text)
    demand(re.search(r"(?m)^local MAX_VISUAL_PARTS = 3$", source) is not None, "STRICT_PART_BUDGET")
    demand(re.search(r"(?m)^local SAMPLE_INTERVAL = 0\.12$", source) is not None, "STRICT_SAMPLE_PERIOD")
    demand(source.count('visualPart("') == 3, "PART_BUDGET")
    demand(source.count("Workspace:Raycast(") == 1, "RAYCAST_BUDGET")
    demand(source.count("RunService.Heartbeat:Connect") == 1, "SINGLE_LOOP")
    # Protect the same real grounded material/collision semantics if this
    # source is subsequently revised by other A authors.
    demand(re.search(
        r"if not hit\.Instance\.CanCollide\s+or hit\.Instance\.Transparency >= 0\.95"
        r"\s+or hit\.Instance\.LocalTransparencyModifier >= 0\.95"
        r"\s+or \(hit\.Instance\.Material == Enum\.Material\.Glass"
        r" and hit\.Instance\.Transparency >= 0\.35\)", source) is not None,
        "SOLID_GROUND_AND_SYNTHETIC_SEA_GUARD")


def compose(base: Path, source: Path, output: Path) -> dict:
    demand(base.resolve() != output.resolve() and not output.resolve().is_relative_to(base.resolve()), "OUTPUT_OVERLAPS_BASE")
    demand(source.is_file(), "CANDIDATE_SOURCE_MISSING")
    source_text = source.read_text(encoding="utf-8")
    check_art_source(source_text)
    originals = selected_map(base)
    demand(len(originals) == 69, "BASE_MUST_BE_REAL69")
    demand(SOURCE_ROUTE not in originals, "DUPLICATE_EXISTING_FEATURE")
    demand(not output.exists(), "OUTPUT_MUST_BE_NEW")
    output.mkdir(parents=True)
    shutil.copytree(base, output / "on70")
    shutil.copytree(base, output / "off69")
    on_root = output / "on70"
    new_path = on_root / "sources/StarterPlayer/StarterPlayerScripts" / SOURCE_FILE
    demand(not new_path.exists(), "SOURCE_EXISTS")
    new_path.parent.mkdir(parents=True, exist_ok=True)
    new_path.write_text(source_text, encoding="utf-8")

    obj = json.loads((on_root / PROJECT).read_text(encoding="utf-8"))
    root_tree = obj["tree"]
    starter = root_tree.get("StarterPlayer")
    demand(isinstance(starter, dict), "STARTERPLAYER_MISSING")
    starter_scripts = starter.get("StarterPlayerScripts")
    demand(isinstance(starter_scripts, dict), "STARTERPLAYERSCRIPTS_MISSING")
    demand("$path" not in starter_scripts, "STARTERPLAYERSCRIPTS_IS_DIRECTORY_MOUNT")
    demand("EGGRUMBLE_LandingShadow" not in starter_scripts, "SCRIPT_NAME_COLLISION")
    starter_scripts["EGGRUMBLE_LandingShadow"] = {
        "$path": "sources/StarterPlayer/StarterPlayerScripts/" + SOURCE_FILE
    }
    (on_root / OUTPUT_PROJECT).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Original project remains available unmodified for immediate rollback.
    shutil.copy2((output / "off69") / PROJECT, (output / "off69") / OUTPUT_PROJECT)
    selected_on = selected_map(on_root, OUTPUT_PROJECT)
    selected_off = selected_map(output / "off69", OUTPUT_PROJECT)
    demand(len(selected_on) == 70, "NEW_COUNT_MUST_BE_70")
    demand(len(selected_off) == 69, "OFF_COUNT_MUST_BE_69")
    demand(SOURCE_ROUTE in selected_on and SOURCE_ROUTE not in selected_off, "ONLY_NEW_ROUTE")
    unchanged = all(
        key in selected_on and digest(older) == digest(selected_on[key])
        for key, older in selected_off.items()
    )
    demand(unchanged, "ORIGINAL_69_BYTE_DIFFERENCE")
    receipt = {
        "schema": "GQ470_LANDING_SHADOW_A_SOURCE_ONLY_V1",
        "base_expected": "REAL69_SOURCE_CANDIDATE_NOT_OFFICIAL_HEAD",
        "feature": "GQ470_FB015_LANDING_MATTE_LOCAL_ONLY_20261121",
        "source_route": SOURCE_ROUTE,
        "new_luau_sha256": digest(new_path),
        "source_count_on": len(selected_on),
        "source_count_off": len(selected_off),
        "original_scripts_unchanged_sha256": len(selected_off),
        "new_source_routes": sorted(set(selected_on) - set(selected_off)),
        "single_local_visual_part_budget": 3,
        "raycast_hz_max": 8.34,
        "new_game_remote_store_host": 0,
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner_art": "NO_GO",
        "official_rc_adopted": False,
        "rollback": "Use off69/EGGRUMBLE_LANDING70.project.json (69 source unchanged)"
    }
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def self_test(source: Path) -> None:
    good = source.read_text(encoding="utf-8")
    check_art_source(good)
    # Dangerous mutations must fail closed without false source-GREEN receipts.
    mutants = [
        good.replace("MAX_VISUAL_PARTS = 3", "MAX_VISUAL_PARTS = 300"),
        good.replace("CanCollide = false", "CanCollide = true"),
        good.replace("CanTouch = false", "CanTouch = true"),
        good.replace("CanQuery = false", "CanQuery = true"),
        good.replace("CastShadow = false", "CastShadow = true"),
        good.replace("SAMPLE_INTERVAL = 0.12", "SAMPLE_INTERVAL = 0"),
        good.replace("Enum.Material.SmoothPlastic", "Enum.Material.Neon"),
        good + "\nInstance.new(\"ParticleEmitter\")\n",
        good + "\ngame:GetService(\"MarketplaceService\")\n",
        good + "\nrem:FireServer(10)\n",
        good + "\nhumanoid:TakeDamage(10)\n",
        good + "\nlocal extra = Workspace:Raycast(Vector3.zero, Vector3.yAxis)\n",
        good.replace("Enum.HumanoidStateType.Freefall", "Enum.HumanoidStateType.Running"),
        good.replace("CameraSubject", "CameraTarget"),
        good.replace('"EGGRUMBLE_LandingShadowOff",', '"EGGRUMBLE_LandingShadowDisabled",'),
        good.replace('"EGGRUMBLE_ReducedEffects",', '"EGGRUMBLE_ReducedFXX",'),
        good.replace('visualDisabled(character)', 'false'),
        good.replace('script.Destroying:Connect', 'script.Removing:Connect'),
        good.replace('effects:Destroy()', 'effects:ClearAllChildren()'),
        good.replace('clearCharacterConnections()', 'clearCharacterSignals()'),
        good.replace("not hit.Instance.CanCollide", "hit.Instance.CanCollide"),
        good.replace("hit.Instance.Transparency >= 0.95", "hit.Instance.Transparency >= 1"),
        good.replace("hit.Instance.Material == Enum.Material.Glass", "hit.Instance.Material == Enum.Material.Slate"),
        good.replace("hit.Instance.LocalTransparencyModifier >= 0.95", "hit.Instance.LocalTransparencyModifier >= 1"),
        good.replace('ancestor:FindFirstChildOfClass("Humanoid")', 'ancestor:FindFirstChildOfClass("Animator")'),
    ]
    for i, mutant in enumerate(mutants, start=1):
        try:
            check_art_source(mutant)
        except ValueError:
            continue
        raise AssertionError(f"unsafe mutation unexpectedly passed: {i}")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        base = root / "base"
        src_dir = base / "sources/StarterPlayer/StarterPlayerScripts"
        src_dir.mkdir(parents=True)
        manifest = {"name": "fixture69", "tree": {"$className": "DataModel", "StarterPlayer": {
            "$className": "StarterPlayer", "StarterPlayerScripts": {
                "$className": "StarterPlayerScripts"}}}}
        for i in range(69):
            name = f"Original_{i:02d}"
            loc = src_dir / (name + ".client.luau")
            loc.write_text("-- original selected source\nprint('safe')\n", encoding="utf-8")
            manifest["tree"]["StarterPlayer"]["StarterPlayerScripts"][name] = {
                "$path": str(loc.relative_to(base)).replace("\\", "/")}
        (base / PROJECT).write_text(json.dumps(manifest), encoding="utf-8")
        output = root / "candidate"
        receipt = compose(base, source, output)
        assert receipt["original_scripts_unchanged_sha256"] == 69
        assert receipt["source_count_on"] == 70
        assert receipt["source_count_off"] == 69
        # A duplicate new visual or an already-broken profile must fail closed.
        for bad in (output / "on70", root / "missing"):
            try:
                compose(bad, source, root / ("reject_" + bad.name))
            except (ValueError, FileNotFoundError):
                continue
            raise AssertionError(f"bad baseline accepted: {bad}")
    print("GQ470_LANDING_SOURCE_SELFTEST_GREEN: 25 mutations RED, 69 originals exact, 70 ON / 69 OFF")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--source", type=Path, default=Path(__file__).with_name(SOURCE_FILE))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(args.source)
        return
    demand(args.base is not None and args.out is not None, "BASE_AND_OUT_REQUIRED")
    receipt = compose(args.base, args.source, args.out)
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == "__main__":
    main()
