#!/usr/bin/env python3
"""Compose an ISOLATED current-author EGGRUMBLE V3 art Studio manifest.

No copies of game logic, branch merges, Roblox publishing, or actual Studio execution.
Read-only original creator project + three additive art Scripts -> new private project.
Usage:
 python3 compose_current_v3_art.py --author-project ../author/.../EGGRUMBLE_V3_STUDIO.project.json --out /tmp/private_v3_art.project.json
"""
from __future__ import annotations

import argparse
import copy
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
ART_BY_TARGET = {
    "v3": ART_NAMES,
    "boss": ("EGGRUMBLE_EncounterReadabilityArt",),
    "castle": ("EGGRUMBLE_EncounterReadabilityArt",),
    "lobby": ("EGGRUMBLE_HeroSilhouetteArt", "EGGRUMBLE_EncounterReadabilityArt"),
    "item": ("EGGRUMBLE_EncounterReadabilityArt",),
}
MANDATORY_BY_TARGET = {
    "v3": MANDATORY_GAME_NAMES,
    "boss": ("EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_NeutralBossPreview"),
    "castle": ("EGGRUMBLE_EnterableCastleInterior", "EGGRUMBLE_CastleWalkthrough"),
    "lobby": ("EGGRUMBLE_LobbyUXPreview", "EGGRUMBLE_LobbyUXStandalone"),
    "item": ("EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_FieldItemPreview"),
}
ART_DIR = Path(__file__).resolve().parents[1]


def rebase_tree_paths(node: dict, author_dir: Path, output_dir: Path) -> None:
    """Rebase ALL original Rojo source paths, including client StarterPlayerScripts.

    Keeping the original author tree is mandatory. The latest author includes
    mobile combat feedback LocalScripts that must not vanish from the art preview.
    """
    for key, value in node.items():
        if key == "$path":
            if not isinstance(value, str):
                raise ValueError("Expected a literal Rojo source $path string")
            real = (author_dir / value).resolve(strict=True)
            if not real.is_file():
                raise ValueError(f"Author source path is not a file: {value}")
            node[key] = os.path.relpath(real, output_dir).replace(os.sep, "/")
        elif isinstance(value, dict):
            rebase_tree_paths(value, author_dir, output_dir)


def compose(author_project: Path, output: Path, art_dir: Path = ART_DIR, target: str = "v3") -> dict:
    if target not in ART_BY_TARGET:
        raise ValueError(f"Unknown isolated preview target: {target}")
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
    for name in MANDATORY_BY_TARGET[target]:
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
    for name in ART_BY_TARGET[target]:
        real = (art_dir / (name + ".server.luau")).resolve(strict=True)
        if not real.is_file():
            raise ValueError(f"Not a script: {name}")
        combined[name] = {"$path": os.path.relpath(real, output.parent).replace(os.sep, "/")}

    # Author may add a require before registering its new module in the original
    # Rojo manifest. Only in this NEW isolated art manifest, include an actual
    # existing same-directory EGGRUMBLE_*.luau from the original author's checkout.
    # Never create/copy/edit the author's module, never mask the author gap in logs.
    pending = list(reference_paths.items())
    visited: set[str] = set()
    while pending:
        name, real = pending.pop()
        if name in visited or real.suffix != ".luau":
            continue
        visited.add(name)
        source = real.read_text(encoding="utf-8")
        for sibling in re.findall(r'require\s*\(\s*script\.Parent:WaitForChild\("([^"]+)"\)\s*\)', source):
            if sibling in combined:
                continue
            if not re.fullmatch(r"EGGRUMBLE_[A-Za-z0-9_]+", sibling):
                raise ValueError(f"Unexpected author sibling module import {name} -> {sibling}")
            fallback = (author_project.parent / f"{sibling}.luau").resolve()
            if fallback.parent != author_project.parent or not fallback.is_file():
                raise ValueError(f"Missing real author sibling module {name} -> {sibling}")
            reference_paths[sibling] = fallback
            combined[sibling] = {
                "$path": os.path.relpath(fallback, output.parent).replace(os.sep, "/")
            }
            pending.append((sibling, fallback))

    # Preserve the entire original Rojo tree: especially StarterPlayerScripts,
    # mobile LocalScripts and any future authored nodes outside ServerScriptService.
    assembled = copy.deepcopy(document)
    assembled["name"] = "EGGRUMBLE_" + target.upper() + "_CURRENT_AUTHOR_ART_PRIVATE_SOURCE_ONLY"
    rebase_tree_paths(assembled["tree"], author_project.parent, output.parent)
    assembled["tree"]["ServerScriptService"] = combined
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
    parser.add_argument("--target", choices=tuple(ART_BY_TARGET), default="v3")
    args = parser.parse_args()
    author_original = json.loads(args.author_project.read_text(encoding="utf-8"))
    result = compose(args.author_project, args.out, target=args.target)
    print("ART_COMPOSITION_SOURCE_ONLY=PASS")
    original_nodes = author_original["tree"]["ServerScriptService"]
    composed_nodes = result["tree"]["ServerScriptService"]
    art_names = ART_BY_TARGET[args.target]
    missing = sorted(set(composed_nodes) - set(original_nodes) - set(art_names))
    print(f"AUTHOR_MODULE_COUNT={len(composed_nodes) - 1 - len(art_names)}")
    print(f"ART_SCRIPT_COUNT={len(art_names)}")
    print(f"ADDITIONAL_AUTHOR_MODULES_FOUND_NOT_IN_ROJO={','.join(missing) if missing else 'NONE'}")
    if missing:
        print("AUTHOR_DIRECT_ROJO_MANIFEST=RED (ask source owner to register missing modules)")
    else:
        print("AUTHOR_DIRECT_ROJO_MANIFEST_IMPORTS=PASS")
    print(f"OUTPUT={args.out}")
    print("NATIVE_LUAU_ROJO_STUDIO_ANDROID=NOT_RUN")


if __name__ == "__main__":
    main()
