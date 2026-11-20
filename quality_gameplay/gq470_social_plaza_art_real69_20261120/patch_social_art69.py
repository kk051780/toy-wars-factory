#!/usr/bin/env python3
"""GQ470 REAL69: bounded social-plaza world labels and pitched photo roof.

A-only source PREP from immutable official REAL69. No actual Studio beauty/FPS
claim, no new economy authority or gameplay loop, exact 69-source OFF rollback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET = "ServerScriptService/GQ8_LobbySocialPlaza"
MARK = "GQ470_FB015_SOCIAL_PLAZA_READABILITY_REAL69_20261120"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "off69_social_plaza_art"
OLD_ROOF = 'part("PhotoRoof",Vector3.new(0,8.8,0),Vector3.new(18,1.5,12),Color3.fromRGB(78,128,166),Enum.Material.Slate,false)'
NEW_ROOF = '''-- GQ470_FB015_SOCIAL_PLAZA_READABILITY_REAL69_20261120
-- One extra static Part only; angled roof silhouette, no physics or query.
local roofLeft=part("PhotoRoof_Left",Vector3.new(-4.4,9.2,0),Vector3.new(9.4,1.0,12),Color3.fromRGB(78,128,166),Enum.Material.Slate,false)
roofLeft.CFrame=CFrame.new(center+Vector3.new(-4.4,9.2,0))*CFrame.Angles(0,0,math.rad(13))
roofLeft.CastShadow=false
local roofRight=part("PhotoRoof_Right",Vector3.new(4.4,9.2,0),Vector3.new(9.4,1.0,12),Color3.fromRGB(78,128,166),Enum.Material.Slate,false)
roofRight.CFrame=CFrame.new(center+Vector3.new(4.4,9.2,0))*CFrame.Angles(0,0,math.rad(-13))
roofRight.CastShadow=false'''
EDITS = (
    ("b.Size=UDim2.fromOffset(180,50)", "b.Size=UDim2.fromOffset(136,38)"),
    ("b.MaxDistance=42;b.AlwaysOnTop=false;b.Parent=at",
     "b.MaxDistance=25;b.AlwaysOnTop=false;b.Parent=at"),
    ("t.BackgroundColor3=Color3.fromRGB(22,35,50);t.BackgroundTransparency=.18",
     "t.BackgroundColor3=Color3.fromRGB(22,35,50);t.BackgroundTransparency=.36"),
    (OLD_ROOF, NEW_ROOF),
)

def need(value: bool, code: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_SOCIAL_PLAZA_" + code)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    project = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    found: dict[str, Path] = {}
    def visit(node: object, route: str = "") -> None:
        if not isinstance(node, dict):
            return
        if "$path" in node:
            p = (root / node["$path"]).resolve()
            need(p.is_relative_to(root.resolve()) and p.is_file(), "INVALID_SELECTED_PATH")
            need(route not in found, "DUPLICATE_SELECTED_ROUTE")
            found[route] = p
        for key, value in node.items():
            if not key.startswith("$"):
                visit(value, route + "/" + key if route else key)
    visit(project["tree"])
    return found

def transform(source: str) -> str:
    need(MARK not in source, "DUPLICATE")
    need('if not RunService:IsStudio() then return end' in source, "STUDIO_FENCE")
    need('plaza:SetAttribute("GQ8_TradeSettlementDisabled",true)' in source, "TRADE_DISABLED")
    need('pr.Triggered:Connect(function(player:Player)' in source, "TRADE_PROMPT_PRESERVED")
    need('prompt.Triggered:Connect(function(player:Player)' in source, "PHOTO_PROMPT_PRESERVED")
    for old, new in EDITS:
        need(source.count(old) == 1, "ANCHOR_DRIFT")
        source = source.replace(old, new, 1)
    need(source.count(MARK) == 1, "PATCH_MARK")
    need('b.Size=UDim2.fromOffset(136,38)' in source and
         'b.MaxDistance=25' in source, "LABEL_BOUNDS")
    need('roofLeft.CastShadow=false' in source and
         'roofRight.CastShadow=false' in source, "ROOF_GPU")
    need('CanQuery=solid' in source and
         'partCount+=1' in source, "EXISTING_PART_POLICY")
    need("RemoteEvent" not in NEW_ROOF and
         "DataStore" not in NEW_ROOF and
         "ProximityPrompt" not in NEW_ROOF, "NO_NEW_AUTHORITY")
    return source

def self_test() -> None:
    original = (
        'if not RunService:IsStudio() then return end\n'
        'plaza:SetAttribute("GQ8_TradeSettlementDisabled",true)\n'
        'pr.Triggered:Connect(function(player:Player)\n'
        'prompt.Triggered:Connect(function(player:Player)\n'
        'CanQuery=solid\npartCount+=1\n'
        + "\n".join(old for old, _ in EDITS) + "\n"
    )
    updated = transform(original)
    need(updated.count("PhotoRoof_") == 2, "TWO_PITCHED_ROOFS")
    need('GQ8_TradeSettlementDisabled' in updated, "TRADE_GUARD")
    mutants = [
        updated,
        original.replace(EDITS[0][0], ""),
        original.replace(EDITS[-1][0], ""),
        original.replace('if not RunService:IsStudio() then return end', ""),
        original.replace("GQ8_TradeSettlementDisabled", "GQ8_TradeAllowed"),
        original.replace("CanQuery=solid", "CanQuery=true"),
    ]
    for bad in mutants:
        try:
            transform(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_MUTANT_ACCEPTED")
    print("GQ470_SOCIAL_PLAZA_6_NEGATIVES_PASS")

def apply(root: Path) -> None:
    paths = selected(root)
    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    need(len(paths) == 69 and TARGET in paths, "SELECTED69_TARGET")
    need(receipt.get("build_head") == BASE and
         len(receipt.get("source_hashes", {})) == 69, "IMMUTABLE_OFFICIAL_BASE")
    before = {route: sha(p.read_bytes()) for route, p in paths.items()}
    need(before == receipt["source_hashes"], "EXACT_69_SOURCE_RECEIPT")
    need(not (root / OFF).exists(), "OFF_ALREADY_EXISTS")
    off = root / OFF
    off.mkdir()
    shutil.copytree(root / "sources", off / "sources")
    for name in (PROJECT, RECEIPT, PLACE):
        shutil.copy2(root / name, off / name)
    patch = transform(paths[TARGET].read_text(encoding="utf-8")).encode("utf-8")
    paths[TARGET].write_bytes(patch)
    after = {route: sha(p.read_bytes()) for route, p in paths.items()}
    need({route for route in before if before[route] != after[route]} == {TARGET},
         "ONE_SELECTED_SOURCE_CHANGED")
    need(sha(selected(off)[TARGET].read_bytes()) == before[TARGET], "OFF69_EXACT")
    receipt["source_hashes"][TARGET] = sha(patch)
    receipt["build_head"] = "PREP_SOCIAL_PLAZA_FROM_" + BASE
    receipt["gq470_social_plaza_art"] = {
        "feature_id": MARK, "formal_parent": BASE, "selected_route": TARGET,
        "original_source_sha256": before[TARGET], "new_source_sha256": sha(patch),
        "exact_untouched_selected_sources": 68, "script_count": 69,
        "world_label_pixels_before": [180, 50], "world_label_pixels_after": [136, 38],
        "world_label_distance_before": 42, "world_label_distance_after": 25,
        "photo_roof_parts_before": 1, "photo_roof_parts_after": 2,
        "net_new_visual_parts": 1, "new_ui_instances": 0, "new_authority": False,
        "rollback": OFF, "studio_visual": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "kid_fun": "NOT_TESTED",
        "owner_accepted": False
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print("GQ470_SOCIAL_PLAZA_SOURCE69_NONLOSS_OFF69_PASS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        need(args.base is not None, "NEED_OFFICIAL_ARTIFACT")
        apply(args.base)
