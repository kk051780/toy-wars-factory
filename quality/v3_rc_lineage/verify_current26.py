#!/usr/bin/env python3
"""Bind the EXISTING #484 26-source composer to its exact original authors.

This is an intake provenance checker, not a second composer, a Roblox Studio
runner, or an official RC writer. It never changes any authored Luau source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from validate import OWNERS, SCHEMA, SHA40, check, inventory

GAME = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
ART = "handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116"
QUALITY_MODULES = ("EGGRUMBLE_BotActors", "EGGRUMBLE_BotPathRouter")
ART_MODULES = (
    "EGGRUMBLE_HeroSilhouetteArt",
    "EGGRUMBLE_FlagshipFieldArt",
    "EGGRUMBLE_EncounterReadabilityArt",
    "EGGRUMBLE_ArtDistanceLOD",
)
SCORE_MODULES = ("EGGRUMBLE_ScoreBalance", "EGGRUMBLE_MatchResultService")
LOBBY = "EGGRUMBLE_LobbyCastleModesPreview"


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def quality_gameplay_drift(paths: list[str]) -> list[str]:
    """Only byte-changing game sources and the original composer invalidate SOURCE."""
    composer = "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/compose.py"
    return [p for p in paths
            if (p.startswith(GAME + "/") and
                (p.endswith(".luau") or p.endswith(".project.json")))
            or p == composer]


def original_owner_bytes(name: str, quality: Path, art: Path, score: Path) -> bytes:
    if name in QUALITY_MODULES:
        return (quality / GAME / (name + ".luau")).read_bytes()
    if name in ART_MODULES:
        suffix = ".client.luau" if name == "EGGRUMBLE_ArtDistanceLOD" else ".server.luau"
        return (art / ART / (name + suffix)).read_bytes()
    if name in SCORE_MODULES:
        return (score / GAME / (name + ".luau")).read_bytes()
    raise ValueError("Unclaimed source owner: " + name)


def verify(args) -> dict:
    roots = (args.author, args.quality, args.art, args.score)
    quality_metadata_advance = []

    for key, root in zip(("author", "quality", "art", "score"), roots):
        if not SHA40.fullmatch(getattr(args, key + "_head")):
            raise ValueError(key + " pin is not a commit SHA")
        if not SHA40.fullmatch(getattr(args, "live_" + key)):
            raise ValueError(key + " current HEAD unknown")
        if getattr(args, key + "_head") != getattr(args, "live_" + key):
            if key != "quality":
                raise ValueError("STALE_" + key.upper() + "_HEAD: owner changed during composition")
            # #484 frequently adds CI/test-only commits. Compare actual Git
            # trees, not commit timestamps: no stale game source may enter RC.
            try:
                changed = subprocess.check_output(
                    ["git", "-C", str(root), "diff", "--name-only",
                     args.quality_head, args.live_quality],
                    text=True, stderr=subprocess.STDOUT,
                ).splitlines()
            except subprocess.CalledProcessError as exc:
                raise ValueError("Cannot prove #484 source-equivalent latest HEAD: " + exc.output)
            source_changes = quality_gameplay_drift(changed)
            if source_changes:
                raise ValueError(
                    "STALE_QUALITY_GAME_SOURCE: recompose latest #484, changed "
                    + ", ".join(source_changes)
                )
            quality_metadata_advance = changed

        if not root.is_dir() or not root.resolve().is_relative_to(args.workspace.resolve()):
            raise ValueError("Unsafe or missing original owner tree: " + key)
    if not SHA40.fullmatch(args.rc_head) or args.rc_head != args.live_rc:
        raise ValueError("STALE_OFFICIAL_RC_HEAD: re-review latest official RC")
    author_project = args.author / GAME / "EGGRUMBLE_V3_STUDIO.project.json"
    candidate_project = args.candidate_project
    errs = []
    orig = inventory(args.workspace, author_project, errs, "original")
    combined = inventory(args.workspace, candidate_project, errs, "combined")
    if errs:
        raise ValueError("Invalid real Rojo map: " + "; ".join(errs))
    if len(orig) != 21 or len(combined) != 26:
        raise ValueError(f"Expected 21 original and 26 composite scripts, got {len(orig)}+{len(combined)}")

    original_host = (args.author / GAME / (LOBBY + ".server.luau")).read_text(encoding="utf-8")
    quality_host = (args.quality / GAME / (LOBBY + ".server.luau")).read_text(encoding="utf-8")
    # Reuse #484's ONLY implementation of the physical castle access ramp,
    # do not duplicate its algorithm or replace the latest author's host.
    composer = args.quality / "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/compose.py"
    spec = importlib.util.spec_from_file_location("existing_quality_composer", composer)
    if spec is None or spec.loader is None:
        raise ValueError("Original #484 composer missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected_host = module.apply_ramp(original_host, quality_host).encode("utf-8")

    overlays = {}
    for name, candidate in combined.items():
        source_path = (candidate_project.parent / candidate["path"]).resolve(strict=True)
        present = source_path.read_bytes()
        if sha(present) != candidate["sha256"]:
            raise ValueError(name + ": manifest raced between read and verification")
        author = orig.get(name)
        if author and (author["sha256"] == candidate["sha256"] and
                       author["place"] == candidate["place"]):
            continue
        if name not in OWNERS:
            raise ValueError(name + ": unauthorized author-owned source replacement")
        if name == LOBBY:
            expected_bytes = expected_host
        else:
            expected_bytes = original_owner_bytes(name, args.quality, args.art, args.score)
        if present != expected_bytes:
            raise ValueError(name + ": composed source is not EXACT original owner bytes")
        overlay = {
            "owner": OWNERS[name],
            "feature_id": "GQ-SPATIAL" if OWNERS[name] == "#484"
                          else "ART-A01" if OWNERS[name] == "#485" else "SCORE-LANE",
            "reason": "Exact author source; quality castle ramp via original composer",
            "rollback": "Restore prior #482 source" if author else "Omit added source module",
            "sha256": sha(present),
        }
        if author:
            overlay["original_sha256"] = author["sha256"]
        overlays[name] = overlay

    provenance = {
        "schema": SCHEMA,
        "author_sha": args.author_head,
        "candidate_sha": args.quality_head,
        "rc_sha": args.rc_head,
        "expected_candidate_sources": 26,
        "original_owner_heads": {
            "#482": args.author_head, "#484": args.quality_head,
            "#485": args.art_head, "#487": args.score_head,
        },
        "overlays": overlays,
    }
    report = check(args.workspace, args.workspace, author_project,
                   candidate_project, provenance, args.live_author, args.live_rc)
    report["owner_heads"] = provenance["original_owner_heads"]
    report["quality_live_head"] = args.live_quality
    report["quality_source_equivalent_to_live_head"] = True
    report["quality_metadata_only_changes_since_pinned"] = quality_metadata_advance
    report["quality_latest_CI_required_for_RC"] = bool(quality_metadata_advance)

    report["composer"] = "REUSED_ORIGINAL_484"
    report["actual_candidate_project"] = str(candidate_project)
    report["candidate_project_sha256"] = sha(candidate_project.read_bytes())
    report["full_26_owner_byte_identity"] = report["status"] == "SOURCE_GATE_PASS"
    report["overlays"] = overlays
    report["candidate_source_sha256"] = {n: d["sha256"] for n, d in sorted(combined.items())}
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("workspace", "author", "quality", "art", "score",
                "candidate-project", "out"):
        p.add_argument("--" + key, required=True, type=Path)
    for key in ("author", "quality", "art", "score"):
        p.add_argument("--" + key + "-head", required=True)
        p.add_argument("--live-" + key, required=True)
    p.add_argument("--rc-head", required=True)
    p.add_argument("--live-rc", required=True)
    a = p.parse_args(argv)
    try:
        result = verify(a)
    except (OSError, ValueError, RuntimeError, AssertionError) as exc:
        result = {
            "schema": SCHEMA, "status": "SOURCE_NO_GO",
            "errors": [type(exc).__name__ + ": " + str(exc)],
            "official_rc_integrated": False, "studio_test": "NOT_TESTED",
            "android_test": "NOT_TESTED", "owner_accepted": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    if a.out.parent.is_dir():
        a.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                         encoding="utf-8")
    return 0 if result["status"] == "SOURCE_GATE_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
