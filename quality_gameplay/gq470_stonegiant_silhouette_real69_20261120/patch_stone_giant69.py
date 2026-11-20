#!/usr/bin/env python3
"""GQ470 FB015: low-part stone-giant 3D silhouette from existing REAL69 boss owner.

A-only verified source PREP; no new boss, AI, combat, HP, Remote or score.
Studio/Android/ART/FUN/OWNER remain NOT_TESTED / NO_GO.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE = "ServerScriptService/EGGRUMBLE_NeutralStoneGiant"
OLD_SHA = "c6a30beeeb2c9484870624ddc8f56a5437146c168cc6044ad8e942c1136b0240"
FEATURE = "GQ470_FB015_STONE_GIANT_SILHOUETTE_REAL69_20261120"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF = "OFF69_STONE_GIANT_SILHOUETTE"

OLD = " local eye=block(model,\"CoreWeakpoint\",at+Vector3.new(0,10,-2.7),Vector3.new(2.5,2.5,0.5),Color3.fromRGB(93,220,245),false)\n eye.Material=Enum.Material.Neon\n"
NEW = " local eye=block(model,\"CoreWeakpoint\",at+Vector3.new(0,10,-2.7),Vector3.new(2.5,2.5,0.5),Color3.fromRGB(93,220,245),false)\n eye.Material=Enum.Material.Neon\n -- GQ470_FB015_STONE_GIANT_SILHOUETTE_REAL69_20261120\n -- Four anchored matte rock wedges on existing model: broad shoulder caps and\n -- split crown prongs. Pure silhouette; leave core hitbox, boss LOS/HP/ring intact.\n -- Zero physics/collision/query/touch/shadows, no new animation listeners.\n for side=-1,1,2 do\n  local shoulder=Instance.new(\"WedgePart\")\n  shoulder.Name=\"BasaltShoulder_\"..tostring(side)\n  shoulder.Size=Vector3.new(4.6,2.6,3.8)\n  shoulder.CFrame=CFrame.new(at+Vector3.new(side*5.1,15.0,0))\n   *CFrame.Angles(0,0,math.rad(-side*21))\n  shoulder.Color=Color3.fromRGB(78,88,104)\n  shoulder.Material=Enum.Material.Slate\n  shoulder.Anchored=true\n  shoulder.CanCollide=false;shoulder.CanTouch=false;shoulder.CanQuery=false\n  shoulder.CastShadow=false\n  shoulder.Parent=model\n  local crown=Instance.new(\"WedgePart\")\n  crown.Name=\"BasaltCrown_\"..tostring(side)\n  crown.Size=Vector3.new(2.0,3.7,2.9)\n  crown.CFrame=CFrame.new(at+Vector3.new(side*1.9,20.4,.4))\n   *CFrame.Angles(0,0,math.rad(side*15))\n  crown.Color=Color3.fromRGB(126,140,158)\n  crown.Material=Enum.Material.Slate\n  crown.Anchored=true\n  crown.CanCollide=false;crown.CanTouch=false;crown.CanQuery=false\n  crown.CastShadow=false\n  crown.Parent=model\n end\n"

def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def must(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("RED_KO_SLASH_" + reason)

def selected(root: Path) -> dict[str, Path]:
    project = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    paths: dict[str, Path] = {}
    def walk(node: dict, prefix: str = ""):
        for key, child in node.items():
            if key == "$path":
                path = (root / child).resolve()
                must(path.is_relative_to(root.resolve()) and path.is_file(), "BAD_PATH")
                must(prefix not in paths, "DUPLICATE_ROUTE")
                paths[prefix] = path
            elif not key.startswith("$") and isinstance(child, dict):
                walk(child, f"{prefix}/{key}" if prefix else key)
    walk(project["tree"])
    return paths

def transform(source: str) -> str:
    must(source.count(OLD) == 1, "BOSS_VISUAL_ANCHOR_DRIFT")
    must(FEATURE not in source, "ALREADY_PATCHED")
    for lock in ("function Boss.spawn(", 'assert(RunService:IsStudio()', 
                 'eye.Material=Enum.Material.Neon',
                 'model:SetAttribute("EGGRUMBLE_BossHealth",health)',
                 'h:TakeDamage(InvulRuntime.filterDamage(',
                 'local function shockwaveClear(',
                 'local hitPrompt=Instance.new("ProximityPrompt")',
                 'return {model=model,weakpoint=eye,damageFrom=damageFrom,'):
        must(lock in source, "BOSS_ORIGINAL_AUTHORITY_CONTRACT")
    must(NEW.count('Instance.new("WedgePart")') == 2 and
         "TakeDamage" not in NEW and "RemoteEvent" not in NEW and
         "DataStore" not in NEW and 'CanCollide=false' in NEW and
         'CanQuery=false' in NEW and 'CastShadow=false' in NEW,
         "SCULPT_MOBILE_OR_AUTHORITY")
    after = source.replace(OLD, NEW, 1)
    fence = " -- GQ8_STONE_GIANT_TRUE_HP_LABEL_20261118"
    must(source.count(fence) == after.count(fence) == 1, "BOSS_HP_FENCE")
    must(source.split(fence, 1)[1] == after.split(fence, 1)[1],
         "BOSS_HP_LOS_DAMAGE_PROMPT_TAIL_CHANGED")
    must(after.count(FEATURE) == 1 and 
         after.count("BasaltShoulder_") == 1 and 
         after.count("BasaltCrown_") == 1, "SCULPT_DUPLICATE")
    return after

def self_test():
    fixture = ('local InvulRuntime=require(script.Parent:WaitForChild("EGGRUMBLE_InvulRuntime"))\n'
               'assert(RunService:IsStudio(),"private neutral boss preview only")\n'
               'function Boss.spawn(parent:Instance,at:Vector3,options:any?)\n'
               + OLD + 
               ' -- GQ8_STONE_GIANT_TRUE_HP_LABEL_20261118\n'
               'model:SetAttribute("EGGRUMBLE_BossHealth",health)\n'
               'local function shockwaveClear(character,root)\n'
               'local hitPrompt=Instance.new("ProximityPrompt")\n'
               'h:TakeDamage(InvulRuntime.filterDamage(h,28,"BOSS","STONE_GIANT"))\n'
               'return {model=model,weakpoint=eye,damageFrom=damageFrom,\n')
    patched = transform(fixture)
    must("BasaltShoulder_" in patched and
         "BasaltCrown_" in patched and
         'for side=-1,1,2 do' in patched and
         'CanQuery=false' in patched, "SCULPT_NOT_GENERATED")
    mutants = (
        patched, fixture.replace(OLD, ""),
        fixture.replace("function Boss.spawn(", "function Evil.spawn("),
        fixture.replace("shockwaveClear(", "wrongLOS("),
        fixture.replace("CoreWeakpoint", "WeakpointMoved"),
        fixture.replace("GQ8_STONE_GIANT_TRUE_HP_LABEL", "BAD_LABEL"),
        fixture.replace("filterDamage(", "rawDamage("),
    )
    for mutant in mutants:
        try:
            transform(mutant)
        except ValueError:
            continue
        raise AssertionError("RED_STONE_GIANT_MUTANT_ACCEPTED")
    print("GQ470_STONE_GIANT_7_NEGATIVE_MUTANTS_PASS")

def apply(root: Path, head: str):
    paths = selected(root)
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    must(head == BASE and receipt.get("build_head") == BASE, "STALE_OFFICIAL")
    must(receipt.get("official_branch") == "rc/p0d-s1-kids-rc01", "NOT_SINGLE_RC")
    must(receipt.get("selected_source_count") == len(paths) == 69, "NOT_REAL69")
    must(set(paths) == set(receipt["source_hashes"]), "SOURCE_ROUTE_SET")
    must(receipt["source_classes"].get(ROUTE) == "ModuleScript", "WRONG_CLASS")
    must(receipt["source_hashes"].get(ROUTE) == OLD_SHA, "STALE_SOURCE_HASH")
    for route, path in paths.items():
        must(sha(path.read_bytes()) == receipt["source_hashes"][route], "INPUT_SOURCE_" + route)
    backup = root / OFF
    must(not backup.exists(), "DUPLICATE_OFF")
    backup.mkdir()
    shutil.copytree(root / "sources", backup / "sources")
    for name in (PROJECT, RECEIPT, "EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copyfile(root / name, backup / name)
    original = paths[ROUTE].read_bytes()
    changed = transform(original.decode("utf-8")).encode("utf-8")
    paths[ROUTE].write_bytes(changed)
    before = selected(backup)
    must({route for route, path in paths.items()
          if path.read_bytes() != before[route].read_bytes()} == {ROUTE}, "OTHER68_CHANGED")
    must((root / PROJECT).read_bytes() == (backup / PROJECT).read_bytes(), "PROJECT_CHANGED")
    receipt["source_hashes"][ROUTE] = sha(changed)
    receipt["gq470_stone_giant_silhouette"] = {
        "feature_id": FEATURE,
        "target": ROUTE,
        "before_sha256": sha(original),
        "after_sha256": sha(changed),
        "other_sources_unchanged": 68,
        "previous_boss_decorative_wedges": 0,
        "new_static_decorative_wedges_per_boss": 4,
        "new_remotes": 0,
        "new_gameplay_authority": False,
        "collision_or_targeting_changed": False,
        "rollback": OFF,
        "source_only": True,
        "android_15min": "NOT_TESTED",
        "pc_android_beauty": "NOT_TESTED",
        "first3min_fun": "NOT_TESTED",
        "owner_accepted": False,
    }
    (root / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False,
                                            sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ470_STONE_GIANT_REAL69_SOURCE_PATCH_PASS", sha(changed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--head", default=BASE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        must(args.base is not None, "MISSING_ARTIFACT")
        apply(args.base, args.head)
