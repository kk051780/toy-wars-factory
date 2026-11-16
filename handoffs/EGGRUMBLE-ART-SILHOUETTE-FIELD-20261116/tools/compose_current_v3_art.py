#!/usr/bin/env python3
"""Compose an ISOLATED current-author EGGRUMBLE V3 art Studio manifest.

No copies of game logic, branch merges, Roblox publishing, or actual Studio execution.
Read-only original creator project + three additive art Scripts -> new private project.
Usage:
 python3 compose_current_v3_art.py --author-project ../author/.../EGGRUMBLE_V3_STUDIO.project.json --out /tmp/private_v3_art.project.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re

ART_NAMES = (
    "EGGRUMBLE_HeroSilhouetteArt",
    "EGGRUMBLE_FlagshipFieldArt",
    "EGGRUMBLE_EncounterReadabilityArt",
)
MANDATORY_GAME_NAMES = (
    "EGGRUMBLE_CastleMatchRules",
    "EGGRUMBLE_BotActors",
    "EGGRUMBLE_BotPathRouter",
    "EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_InteractionGuard",
    "EGGRUMBLE_SevenRoleCombat",
    "EGGRUMBLE_MatchResultService",
    "EGGRUMBLE_LobbyCastleModesPreview",
)
ART_DIR = Path(__file__).resolve().parents[1]


def compose(author_project: Path, output: Path, art_dir: Path = ART_DIR) -> dict:
    author_project = author_project.resolve(strict=True)
    output = output.resolve()
    if output == author_project or output.parent == art_dir.resolve() and output.name in (
        "EGGRUMBLE_V3_ART_STUDIO.project.json",
        "EGGRUMBLE_SEVEN_HERO_ART_STUDIO.project.json",
    ):
        raise ValueError("Refusing to overwrite either author's or original art project")
    document = json.loads(author_project.read_text(encoding="utf-8"))
    src = document["tree"]["ServerScriptService"]
    if src.get("$className") != "ServerScriptService":
        raise ValueError("Expected a current Rojo ServerScriptService mapping")
    for name in MANDATORY_GAME_NAMES:
        if name not in src:
            raise ValueError(f"Missing latest author V3 module {name}")
    if any(name in src for name in ART_NAMES):
        raise ValueError("Author project already contains art overlay; refusing duplicate overlay")

    combined = {"$className": "ServerScriptService"}
    reference_paths: dict[str, Path] = {}
    for name, spec in src.items():
        if name == "$className":
            continue
        if not isinstance(spec, dict) or set(spec) != {"$path"}:
            raise ValueError(f"Unexpected author ServerScriptService object: {name}")
        raw_path = Path(spec["$path"])
        real = (author_project.parent / raw_path).resolve(strict=True)
        if not real.is_file():
            raise ValueError(f"Not a file: {name}")
        reference_paths[name] = real
        combined[name] = {"$path": os.path.relpath(real, output.parent).replace(os.sep, "/")}
    for name in ART_NAMES:
        real = (art_dir / (name + ".server.luau")).resolve(strict=True)
        if not real.is_file():
            raise ValueError(f"Not a script: {name}")
        combined[name] = {"$path": os.path.relpath(real, output.parent).replace(os.sep, "/")}

    # Source-level interface guard: each sibling script.Parent:WaitForChild module
    # must exist in the composed manifest. Full Luau runtime still requires Studio.
    for name, real in reference_paths.items():
        if real.suffix != ".luau":
            continue
        source = real.read_text(encoding="utf-8")
        for sibling in re.findall(r'require\s*\(\s*script\.Parent:WaitForChild\("([^"]+)"\)\s*\)', source):
            if sibling not in combined:
                raise ValueError(f"Broken author sibling module import {name} -> {sibling}")

    assembled = {
        "name": "EGGRUMBLE_V3_CURRENT_AUTHOR_ART_STUDIO_PRIVATE_SOURCE_ONLY",
        "tree": {
            "$className": "DataModel",
            "ServerScriptService": combined,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(assembled, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, spec in combined.items():
        if name == "$className":
            continue
        if not (output.parent / spec["$path"]).resolve().is_file():
            raise RuntimeError(f"Bad emitted path: {name}")
    return assembled


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = compose(args.author_project, args.out)
    print("ART_COMPOSITION_SOURCE_ONLY=PASS")
    print(f"AUTHOR_MODULE_COUNT={len(result['tree']['ServerScriptService']) - 1 - len(ART_NAMES)}")
    print(f"ART_SCRIPT_COUNT={len(ART_NAMES)}")
    print(f"OUTPUT={args.out}")
    print("NATIVE_LUAU_ROJO_STUDIO_ANDROID=NOT_RUN")


if __name__ == "__main__":
    main()
