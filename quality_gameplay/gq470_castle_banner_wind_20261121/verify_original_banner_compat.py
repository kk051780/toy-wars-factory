#!/usr/bin/env python3
"""Compatibility check with immutable official REAL69 FieldArt source.

A source test, not Roblox Studio validation. Requires downloaded actual official
Actions #44695199140 artifact, never a detached source from another branch.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re

FIELD = "sources/ServerScriptService/EGGRUMBLE_FlagshipFieldArt.server.luau"
FIELD_SHA256 = "d77fdaf390506f87dfea3064611898320288690f4ef14b97f4e8416eaef40395"
CANDIDATE = Path(__file__).parent / "EGGRUMBLE_CastleBannerWind.client.luau"

def verify(field_src: str, client_src: str) -> None:
    """Fail when the actual banners, ancestry, material or local detector drift."""
    original_markers = [
        'local function castleAt(arena:Instance,castle:Model)',
        'castle:FindFirstChild("StandardCore")',
        'deco.Name="EGGRUMBLE_CastleArt_VisualOnly"',
        "deco.Parent=castle",
        'p.Name="ART_"..name',
        "p.Parent=parent",
        "p.Anchored=true",
        "p.CanCollide=false",
        'add("FB015Banner"..tostring(x),"Wedge"',
        "Vector3.new(x,13.6,-14.8),teamTrim,Enum.Material.Fabric",
        "if used>=MAX_CASTLE_PARTS then return nil end",
        "if (budgets[arena] or 0)>=MAX_VISUAL_PARTS_PER_ARENA then return nil end",
    ]
    for mark in original_markers:
        assert mark in field_src, f"RED_OFFICIAL_ORIGINAL_MISSING_{mark}"
    assert field_src.count('add("FB015Banner"..tostring(x)') == 1
    assert 'for _,x in ipairs({-20,20}) do' in field_src
    # Geometry must be in the same castle as StandardCore; a sibling decoration
    # folder in the arena would never match our client detector.
    assert re.search(r'deco.Parent=castle.*?add\("FB015Banner"',field_src,re.S)
    assert re.search(r'local function isCastleBanner\(.*?ancestor:FindFirstChild\("StandardCore", true\)',client_src,re.S)
    assert 'string.find(name, "banner", 1, true)' in client_src
    assert "part.Anchored" in client_src and "part.CanCollide" in client_src
    assert "part.Material == Enum.Material.Neon" in client_src
    assert "RunService.Heartbeat:Connect" in client_src
    assert "if UserInputService.TouchEnabled then 0.32 else 0.18" in client_src
    assert "MAX_BANNERS = 20" in client_src
    assert "RANGE_STUDS = 110" in client_src

def main(root: Path) -> None:
    source = root / FIELD
    project = root / "EGGRUMBLE_REAL69.project.json"
    receipt = root / "REAL69_LEGACY_INTAKE_RECEIPT.json"
    assert source.is_file() and project.is_file() and receipt.is_file(), "RED_MISSING_IMMUTABLE_ARTIFACT"
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIELD_SHA256, "RED_REAL69_SOURCE_SHA_DRIFT"
    import json
    meta=json.loads(receipt.read_text(encoding="utf-8"))
    assert meta["build_head"]=="e80973c354f14a0d0088577f3cc1a875454f0f8f"
    assert meta["selected_source_count"] == 69
    assert meta["source_hashes"]["ServerScriptService/EGGRUMBLE_FlagshipFieldArt"] == FIELD_SHA256
    src=raw.decode("utf-8")
    client=CANDIDATE.read_text(encoding="utf-8")
    verify(src,client)
    mutants = [
        src.replace('add("FB015Banner"', 'add("FB015Gone"', 1),
        src.replace("deco.Parent=castle", "deco.Parent=arena", 1),
        src.replace("p.Anchored=true", "p.Anchored=false", 1),
        src.replace("p.CanCollide=false", "p.CanCollide=true", 1),
        src.replace('p.Name="ART_"..name', 'p.Name="OMIT_"..name', 1),
        src.replace('castle:FindFirstChild("StandardCore")','castle:FindFirstChild("FakeCore")',1),
    ]
    for i,altered in enumerate(mutants,1):
        try:
            verify(altered,client)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"RED_ORIGINAL_COMPAT_MUTANT_{i}_SURVIVED")
    for i,changed in enumerate([
        client.replace("string.find(name, \"banner\", 1, true)", "string.find(name, \"fake\", 1, true)",1),
        client.replace('ancestor:FindFirstChild("StandardCore", true)','ancestor:FindFirstChild("Fake", true)',1),
        client.replace("part.Material == Enum.Material.Neon","false",1),
        client.replace("MAX_BANNERS = 20","MAX_BANNERS = 200",1),
    ],1):
        try:
            verify(src,changed)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"RED_CLIENT_COMPAT_MUTANT_{i}_SURVIVED")
    print("GQ470_REAL69_ORIGINAL_BANNER_SOURCE_COMPAT_PASS_10_NEGATIVES")
    print("STUDIO_ANDROID_VISUAL_EVIDENCE_NOT_TESTED_ART_NO_GO")

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--official-dir",type=Path,required=True)
    main(parser.parse_args().official_dir)
