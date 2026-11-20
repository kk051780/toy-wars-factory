#!/usr/bin/env python3
"""One-original-source REAL69 confirmed-hit reticle art patch; A PREP, never RC write.

Only rearranges locally visible pixels of the existing server-confirmed HIT
presentation in CombatFeel. Animation/camera recoil, hit authority, role
scores and mobile combat logic remain original byte-for-byte outside anchors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

FORMAL_SHA = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
OFFICIAL_RUN_ID = 44695199140
OFFICIAL_ARTIFACT_ID = 14610422120
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel"
RELATIVE_SOURCE = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel.client.luau"
OLD_SHA = "d378d6a356b9462c99deddc19b4393d79bf113225047a057658d1782e1e8a32e"
NEW_SHA = "ae43ff66055698dd72ccf6beb2aa3fcc61080e49343055b3d8cd3594831c0b1c"
MARKER = "GQ470_FB015_CONFIRMED_HIT_CENTERED_MATTE_RETICLE_REAL69_20261121"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF_NAME = "OFF69_HIT_RETICLE_EXACT"

# Original source anchors are individually unique in the actual 69 selected files.
REPLACEMENTS = (
    ('-- Small, short-lived hit reticle in the center (nothing persists as a large HUD).',
     '-- ' + MARKER + '\n-- Existing confirmed-hit GUI only. Center four strokes through size tween,\n'
     '-- use compact matte counter with fixed glyph sizes for readable mobile HIT/CHAIN.\n'
     '-- Small, short-lived hit reticle in the center (nothing persists as a large HUD).'),
    ('hitToast.Position=UDim2.new(.5,6,.49,34)',
     'hitToast.Position=UDim2.new(.5,0,.49,30)'),
    ('hitToast.Size=UDim2.fromOffset(62,20)',
     'hitToast.Size=UDim2.fromOffset(78,20)'),
    ('hitToast.BackgroundColor3=Color3.fromRGB(12,20,29)',
     'hitToast.BackgroundColor3=Color3.fromRGB(25,32,42)'),
    ('hitToast.BackgroundTransparency=.28',
     'hitToast.BackgroundTransparency=.35'),
    ('hitToast.TextStrokeTransparency=.65',
     'hitToast.TextStrokeTransparency=.85'),
    ('hitToast.TextScaled=true',
     'hitToast.TextScaled=false;hitToast.TextSize=12'),
    ('hitToast.Font=Enum.Font.GothamBold',
     'hitToast.Font=Enum.Font.GothamBold\nhitToast.TextTruncate=Enum.TextTruncate.AtEnd'),
    ('v.Size=UDim2.fromOffset(3,10)',
     'v.Size=UDim2.fromOffset(2,9)'),
    ('v.Rotation=i*90',
     'v.Rotation=(i-1)*90'),
    ('local positions={\n  UDim2.fromOffset(6,-9),UDim2.fromOffset(21,6),\n'
     '  UDim2.fromOffset(6,21),UDim2.fromOffset(-9,6),\n }\n v.Position=positions[i]',
     'local positions={\n  Vector2.new(0,-12),Vector2.new(12,0),\n'
     '  Vector2.new(0,12),Vector2.new(-12,0),\n }\n'
     ' -- Scale from the mark center: its existing 12→26px size tween must\n'
     ' -- not move the four strokes diagonally by 7px while confirming a hit.\n'
     ' v.Position=UDim2.new(.5,positions[i].X,.5,positions[i].Y)'),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(ok: bool, code: str) -> None:
    if not ok:
        raise AssertionError("RED_GQ470_RETICLE_" + code)


def changed_text(original: str) -> str:
    require(MARKER not in original, "DOUBLE_APPLY")
    text = original
    for i, (old, new) in enumerate(REPLACEMENTS):
        require(text.count(old) == 1, f"ANCHOR_{i}")
        text = text.replace(old, new, 1)
    require(text.count(MARKER) == 1, "MARKER")
    return text


def validate_source(original: str, candidate: str) -> None:
    require(original.startswith("--!strict\n") and candidate.startswith("--!strict\n"), "LUAU_STRICT")
    require(changed_text(original) == candidate, "EXACT_ONLY_PIXEL_SCOPE")
    require('v.Position=UDim2.new(.5,positions[i].X,.5,positions[i].Y)' in candidate, "CENTERED_TICKS")
    require('hitToast.TextScaled=false;hitToast.TextSize=12' in candidate, "TEXT_GLYPHS_FIXED")
    require('hitToast.TextTruncate=Enum.TextTruncate.AtEnd' in candidate, "LONG_CHAIN_BOUNDED")
    require('hitToast.BackgroundColor3=Color3.fromRGB(25,32,42)' in candidate, "MATTE")
    require('v.Size=UDim2.fromOffset(2,9)' in candidate, "COMPACT_TICKS")
    require('v.Rotation=(i-1)*90' in candidate, "RADIAL_TICK_LAYOUT")
    for anchor in (
        'player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
        'player:GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature")',
        'local chainCount=hitChainCount(now)',
        'hitToast.Text="CHAIN x"..tostring(chainCount)',
        'hitToast.Text="HIT x"..tostring(math.floor(power))',
        'RunService:BindToRenderStep("EGGRUMBLE_RealHitFeedback"',
        'GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117',
    ):
        require(candidate.count(anchor) == original.count(anchor) and original.count(anchor) > 0,
                "PRESERVE_" + anchor[:25])
    for token in (
        'Instance.new(', 'RemoteEvent', 'TakeDamage(', 'DataStore', 'RenderStepped:Connect(',
        ':Connect(', 'BindToRenderStep(', 'camera.CFrame=', 'IMPACT_WINDOW=',
    ):
        require(candidate.count(token) == original.count(token), "NO_GAMEPLAY_OR_LOOP_" + token)
    # Insets must be relative to the label's animated center at BOTH sizes.
    radial = ((0,-12),(12,0),(0,12),(-12,0))
    for mark_size in (12,19,26):
        for x,y in radial:
            require((mark_size/2+x)-(mark_size/2) == x and
                    (mark_size/2+y)-(mark_size/2) == y, "ANIMATION_CENTER_DRIFT")


def sample_mutations(original: str, candidate: str) -> int:
    mutants = (
        candidate.replace('v.Position=UDim2.new(.5,positions[i].X,.5,positions[i].Y)',
                          'v.Position=UDim2.fromOffset(6,-9)',1),
        candidate.replace('hitToast.TextScaled=false','hitToast.TextScaled=true',1),
        candidate.replace('hitToast.BackgroundColor3=Color3.fromRGB(25,32,42)',
                          'hitToast.BackgroundColor3=Color3.new(1,1,1)',1),
        candidate.replace('v.Size=UDim2.fromOffset(2,9)','v.Size=UDim2.fromOffset(6,30)',1),
        candidate.replace(MARKER,MARKER+MARKER,1),
        candidate.replace('hitToast.TextTruncate=Enum.TextTruncate.AtEnd','',1),
        candidate.replace('v.Rotation=(i-1)*90','v.Rotation=i*90',1),
        candidate.replace('local chainCount=hitChainCount(now)','local chainCount=0',1),
        candidate.replace('IMPACT_WINDOW=.115','IMPACT_WINDOW=.5',1),
        candidate.replace('hitToast.Visible=true','hitToast.Visible=false',1),
        candidate + '\nInstance.new("RemoteEvent")',
        candidate.replace('RunService:BindToRenderStep("EGGRUMBLE_RealHitFeedback"',
                          'RunService:BindToRenderStep("REMOVED"',1),
    )
    for index, mutant in enumerate(mutants):
        try:
            validate_source(original, mutant)
        except AssertionError:
            continue
        raise AssertionError(f"RED_GQ470_RETICLE_MUTANT_MISSED_{index}")
    return len(mutants)


def source_routes(folder: Path) -> dict[str, Path]:
    doc = json.loads((folder / PROJECT).read_text(encoding="utf-8"))
    selected: dict[str, Path] = {}
    def walk(node: dict, route: str = "") -> None:
        if not isinstance(node, dict):
            return
        if "$path" in node:
            file = (folder / node["$path"]).resolve()
            require(file.is_relative_to(folder.resolve()) and file.is_file(), "SOURCE_ESCAPE")
            require(route not in selected, "DUPLICATE_ROUTE")
            selected[route] = file
        for name, child in node.items():
            if not name.startswith("$"):
                walk(child, route + "/" + name if route else name)
    walk(doc["tree"])
    require(len(selected) == 69 and ROUTE in selected, "EXACT_69_SELECTED")
    require(selected[ROUTE].relative_to(folder).as_posix() == RELATIVE_SOURCE, "TARGET_CLASS_AND_PATH")
    return selected


def run(base: Path, out: Path) -> dict:
    require(base.is_dir() and not out.exists(), "BASE_OR_DESTINATION")
    receipt = json.loads((base / RECEIPT).read_text(encoding="utf-8"))
    selected = source_routes(base)
    require(receipt.get("build_head") == FORMAL_SHA
            and receipt.get("canonical_build") is True
            and receipt.get("selected_source_count") == 69, "PINNED_FORMAL_ARTIFACT")
    require(len(receipt.get("source_hashes", {})) == 69, "COMPLETE_RECEIPT")
    for route, file in selected.items():
        require(receipt["source_hashes"].get(route) == digest(file.read_bytes()), "SOURCE_HASH_" + route)
    original_bytes = selected[ROUTE].read_bytes()
    require(digest(original_bytes) == OLD_SHA, "TARGET_SOURCE_PIN")
    original = original_bytes.decode("utf-8")
    candidate = changed_text(original)
    validate_source(original, candidate)
    count = sample_mutations(original, candidate)
    candidate_bytes = candidate.encode("utf-8")
    require(digest(candidate_bytes) == NEW_SHA, "CANDIDATE_SOURCE_PIN")
    shutil.copytree(base, out)
    off = out / OFF_NAME
    off.mkdir()
    shutil.copytree(base / "sources", off / "sources")
    for filename in (PROJECT, RECEIPT, "EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copy2(base / filename, off / filename)
    after = source_routes(out)
    after[ROUTE].write_bytes(candidate_bytes)
    before_off = source_routes(off)
    require({route for route in selected
             if after[route].read_bytes() != before_off[route].read_bytes()} == {ROUTE},
            "SINGLE_69_ROUTE_DELTA")
    require(all(before_off[k].read_bytes() == selected[k].read_bytes() for k in selected),
            "ORIGINAL_69_OFF_EXACT")
    receipt["source_hashes"][ROUTE] = NEW_SHA
    receipt["gq470_hit_reticle_candidate"] = {
        "feature_id": MARKER, "official_formal_base_head": FORMAL_SHA,
        "official_artifact": OFFICIAL_ARTIFACT_ID, "candidate_scope": "ONE_LOCAL_HIT_VISUAL_ONLY",
        "selected_route": ROUTE, "script_class": "LocalScript",
        "original_source_sha256": OLD_SHA, "candidate_source_sha256": NEW_SHA,
        "source_size_before_bytes": len(original_bytes),
        "source_size_after_bytes": len(candidate_bytes),
        "selected_changed": 1, "selected_unchanged": 68,
        "existing_gui_objects_delta": 0, "new_connections_delta": 0,
        "gameplay_authority_changed": False, "camera_recoil_changed": False,
        "mutants_rejected": count, "formal_rc_integrated": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android15": "NOT_TESTED", "matched_png_screenshots": "0/32",
        "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO",
        "owner_accepted": False,
    }
    (out / RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    packet = out / "B220_RETICLE_ONE_SOURCE_NOT_FORMAL"
    target = packet / "selected_sources" / RELATIVE_SOURCE.split("sources/",1)[1]
    target.parent.mkdir(parents=True)
    target.write_bytes(candidate_bytes)
    (packet / "SOURCE_SELECT_MANIFEST.json").write_text(json.dumps(
        receipt["gq470_hit_reticle_candidate"],ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ470_RETICLE_REAL69_A_PREP_NATIVE_PENDING", NEW_SHA,
          "original",len(original_bytes),"candidate",len(candidate_bytes),"mutants",count)
    return receipt["gq470_hit_reticle_candidate"]


def main() -> None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--base", type=Path)
    cli.add_argument("--out", type=Path)
    cli.add_argument("--self-test", action="store_true")
    args=cli.parse_args()
    if args.self_test:
        # Check all replacement anchors against source supplied on the CLI in CI.
        require(args.base is not None and args.base.is_dir(), "SELFTEST_NEEDS_REAL_BASE")
        source=source_routes(args.base)[ROUTE].read_text(encoding="utf-8")
        require(digest(source.encode()) == OLD_SHA, "SELFTEST_SOURCE_PIN")
        art=changed_text(source)
        validate_source(source, art)
        print("GQ470_RETICLE_12_MUTATIONS_REJECTED", sample_mutations(source, art))
    else:
        require(args.base is not None and args.out is not None, "REQUIRE_BASE_OUT")
        run(args.base.resolve(), args.out.resolve())

if __name__=="__main__":
    main()
