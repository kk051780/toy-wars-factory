#!/usr/bin/env python3
"""GQ470 FB-015: source-exact, reversible 8-NPC silhouette art for REAL69.

This edits *only* the existing LegacyTwinBiomes makeGuide visual slice.
It does not create or authorize another Game/Remote/HP/score/Store owner.
Native/Rojo/Studio/Android/FUN evidence must be separately obtained by B220.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FEATURE = "GQ470_FB015_TWIN_CREATURE_SILHOUETTES_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
FORMAL_BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
# After the already-adopted reef sculpt; never substitute the historical REAL68.
FORMAL_SOURCE_SHA256 = "c8a78277b74669caebfb7ac6e1dc18f065c537f2da00cf22d8fd7fbca0bf5a00"

OLD_BODY = '''    local body = part("Body", Vector3.new(3.5, 3.5, 3.5), x, info.y,
        info.localZ, info.tint, Enum.Material.SmoothPlastic, false, npc)
    body.Shape = Enum.PartType.Ball
'''
NEW_BODY = '''    -- GQ470_FB015_TWIN_CREATURE_SILHOUETTES_REAL69_20261121
    -- Distinct species massing, not four recolored luminous spheres.
    -- Same one noncolliding Body per NPC, no extra object/physics budget.
    local bodySize = if info.id=="AWARIN" then Vector3.new(3.25,3.0,3.25)
        elseif info.id=="SANGORU" then Vector3.new(2.9,4.15,2.9)
        elseif info.id=="RAIKO" then Vector3.new(3.0,3.8,2.75)
        else Vector3.new(4.2,2.8,3.4)
    local body = part("Body", bodySize, x, info.y,
        info.localZ, info.tint, Enum.Material.SmoothPlastic, false, npc)
    body.Shape = Enum.PartType.Ball
    body.Reflectance = 0
    body:SetAttribute("ArtSilhouette",info.id)
'''
OLD_EYE = '''            x + d, info.y + 0.4, info.localZ - 1.65, dark,
            Enum.Material.Neon, false, npc)
'''
NEW_EYE = '''            x + d, info.y + 0.4, info.localZ - 1.65, dark,
            Enum.Material.SmoothPlastic, false, npc)
'''
OLD_CREST = '''    local crest = part("Crest", Vector3.new(1.1, 1.3, 1.1), x,
        info.y + 2, info.localZ, info.tint, Enum.Material.Neon, false, npc)
    crest.Shape = Enum.PartType.Ball
'''
NEW_CREST = '''    local crest = part("Crest", Vector3.new(1.1, 1.3, 1.1), x,
        info.y + 2, info.localZ, info.tint, Enum.Material.SmoothPlastic, false, npc)
    crest.Shape = Enum.PartType.Ball
'''
OLD_DECOR = '''        local p = part(name,size,x+dx,info.y+dy,info.localZ+dz,
            tint,Enum.Material.Neon,false,npc)
        if shape=="Ball" then p.Shape=Enum.PartType.Ball end
'''
NEW_DECOR = '''        -- Matte ornamentation retains the authored 8-NPC silhouette count.
        -- No persistent glow overdraw or extra mobile lights.
        local p = part(name,size,x+dx,info.y+dy,info.localZ+dz,
            tint,Enum.Material.SmoothPlastic,false,npc)
        if shape=="Ball" then p.Shape=Enum.PartType.Ball end
'''
OLD_ANTLERS = '''        for side=-1,1,2 do
            decor("CoralAntler_"..side,Vector3.new(0.85,3.3,0.85),
                side*1.15,2.65,0,coral,nil,0)
            decor("CoralFork_"..side,Vector3.new(1.7,0.75,0.85),
                side*1.85,3.75,0,pearl,nil,0)
        end
'''
NEW_ANTLERS = '''        for side=-1,1,2 do
            local stem=decor("CoralAntler_"..side,Vector3.new(0.85,3.3,0.85),
                side*1.15,2.65,0,coral,nil,0)
            stem.CFrame=stem.CFrame*CFrame.Angles(0,0,math.rad(-side*12))
            local fork=decor("CoralFork_"..side,Vector3.new(1.7,0.75,0.85),
                side*1.85,3.75,0,pearl,nil,0)
            fork.CFrame=fork.CFrame*CFrame.Angles(0,0,math.rad(side*30))
        end
'''
OLD_HORNS = '''        for side=-1,1,2 do
            decor("ThunderHorn_"..side,Vector3.new(0.8,3.1,0.75),
                side*1.1,2.6,0,gold,nil,0)
            decor("ThunderBolt_"..side,Vector3.new(1.85,0.65,0.75),
                side*1.65,3.9,0,aqua,nil,0)
        end
'''
NEW_HORNS = '''        for side=-1,1,2 do
            local horn=decor("ThunderHorn_"..side,Vector3.new(0.8,3.1,0.75),
                side*1.1,2.6,0,gold,nil,0)
            horn.CFrame=horn.CFrame*CFrame.Angles(0,0,math.rad(side*17))
            local flash=decor("ThunderBolt_"..side,Vector3.new(1.85,0.65,0.75),
                side*1.65,3.9,0,aqua,nil,0)
            flash.CFrame=flash.CFrame*CFrame.Angles(0,0,math.rad(-side*24))
        end
'''

PAIRS = (
    ("BODY", OLD_BODY, NEW_BODY),
    ("EYES", OLD_EYE, NEW_EYE),
    ("CREST", OLD_CREST, NEW_CREST),
    ("DECOR", OLD_DECOR, NEW_DECOR),
    ("CORAL_ANTLERS", OLD_ANTLERS, NEW_ANTLERS),
    ("THUNDER_HORNS", OLD_HORNS, NEW_HORNS),
)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fail(condition: bool, key: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_TWIN_NPC_" + key)

def patch(source: str) -> str:
    fail(FEATURE not in source, "ALREADY_APPLIED")
    fail("GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119" in source, "ORIGIN_MARKER")
    fail('local function makeGuide(info, side)' in source, "NPC_OWNER")
    fail('local function summonBoundCompanion(player, info, level)' in source, "BOND_OWNER")
    fail('npc.PrimaryPart=body' in source and 'table.insert(animate,{model=npc' in source,
         "MODEL_PIVOT")
    fail('prompt.Parent = body' in source and 'prompt.Triggered:Connect(function(player)' in source,
         "REAL_NPC_PROMPT")
    fail('local coral = Color3.fromRGB' in source, "BIOME_PALETTE")
    out = source
    for name, old, new in PAIRS:
        fail(out.count(old) == 1, "ANCHOR_" + name)
        out = out.replace(old, new, 1)
    fail(out.count(FEATURE) == 1, "MARKER_COUNT")
    # No new Script/Part/Remote/GUI, no changes in prompt, save, or authority.
    fail(out.count('Instance.new("Part")') == source.count('Instance.new("Part")'),
         "PART_ALLOCATOR_DRIFT")
    fail(out.count("ProximityPrompt") == source.count("ProximityPrompt"),
         "PROMPT_DRIFT")
    fail(out.count("RemoteEvent") == source.count("RemoteEvent"),
         "REMOTE_DRIFT")
    fail(out.count("DataStore") == source.count("DataStore"), "STORE_DRIFT")
    fail(out.count("TakeDamage") == source.count("TakeDamage"), "DAMAGE_DRIFT")
    fail(out.count('local function summonBoundCompanion') ==
         source.count('local function summonBoundCompanion'), "BOND_DRIFT")
    return out

def verify_selftest(source: str) -> dict:
    candidate = patch(source)
    fail(candidate != source and len(candidate) > len(source), "POSITIVE_PATCH")
    negatives = {
        "duplicate": candidate,
        "missing_body": source.replace(OLD_BODY, "", 1),
        "missing_eye": source.replace(OLD_EYE, "", 1),
        "missing_crest": source.replace(OLD_CREST, "", 1),
        "missing_antlers": source.replace(OLD_ANTLERS, "", 1),
        "missing_horns": source.replace(OLD_HORNS, "", 1),
        "missing_prompt": source.replace("prompt.Parent = body", "prompt.Parent = nil", 1),
        "missing_pivot": source.replace("npc.PrimaryPart=body", "npc.PrimaryPart=nil", 1),
        "missing_origin": source.replace("GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119",
                                         "WRONG_PROFILE", 1),
    }
    for name, corrupted in negatives.items():
        try:
            patch(corrupted)
        except ValueError:
            continue
        raise AssertionError("NEGATIVE_NOT_REJECTED_" + name)
    return {
        "feature_id": FEATURE, "scope": "ONE_SELECTED_REAL69_NPC_VISUAL_SLICE",
        "mutations_rejected": len(negatives),
        "base_source_bytes": len(source.encode("utf-8")),
        "candidate_source_bytes": len(candidate.encode("utf-8")),
        "source_sha256": digest(source.encode("utf-8")),
        "candidate_sha256": digest(candidate.encode("utf-8")),
        "source_gate": "PATCH_AND_STATIC_NEGATIVE_ONLY",
        "native_rojo_off69": "NOT_TESTED",
        "studio_android_human_art_owner": "NOT_TESTED",
    }

def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--fixture", type=Path, help="historical authored file, tests only")
    cli.add_argument("--source", type=Path, help="extracted official selected REAL69 Luau file")
    cli.add_argument("--output", type=Path)
    cli.add_argument("--report", type=Path)
    args = cli.parse_args()
    fail(bool(args.fixture) != bool(args.source), "CHOOSE_SINGLE_INPUT")
    source_path = args.fixture or args.source
    fail(source_path.is_file(), "INPUT_MISSING")
    source_bytes = source_path.read_bytes()
    source = source_bytes.decode("utf-8")
    if args.source:
        fail(digest(source_bytes) == FORMAL_SOURCE_SHA256, "FORMAL_SHA_NOT_CURRENT")
        fail(args.output is not None and args.report is not None, "OUTPUTS_REQUIRED")
    info = verify_selftest(source)
    info["formal_rc_head_at_authoring"] = FORMAL_BASE
    info["formal_source_gate"] = "EXACT_FORMAL_SOURCE" if args.source else "FIXTURE_ONLY_NOT_FORMAL"
    info["route"] = ROUTE
    if args.output:
        fail(args.output.resolve() != source_path.resolve(), "NO_INPLACE_WRITE")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(patch(source).encode("utf-8"))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))

if __name__ == "__main__":
    main()
