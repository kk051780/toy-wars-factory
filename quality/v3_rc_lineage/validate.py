#!/usr/bin/env python3
"""EGGRUMBLE V3 author-to-candidate SOURCE identity gate.

This checks disk bytes and Rojo mappings; it does not establish Roblox engine QA,
official RC adoption, player enjoyment, Android performance or OWNER approval.
No network, write-side GitHub operations, or Roblox authentication are needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "EGGRUMBLE_V3_RC_LINEAGE_V1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
SERVER = ("ServerScriptService",)
CLIENT = ("StarterPlayer", "StarterPlayerScripts")
MANDATORY = frozenset(
    """
    EGGRUMBLE_CastleMatchRules EGGRUMBLE_BotPathRouter EGGRUMBLE_BotActors
    EGGRUMBLE_SwarmCombat EGGRUMBLE_LobbyCastleModesPreview
    EGGRUMBLE_InteractionGuard EGGRUMBLE_SevenRoleCombat EGGRUMBLE_MatchResultService
    EGGRUMBLE_CombatBalance EGGRUMBLE_SkillFX EGGRUMBLE_RoundReplay
    EGGRUMBLE_AttackGeometry EGGRUMBLE_ImpactFeedback EGGRUMBLE_WeaponSilhouettes
    EGGRUMBLE_DivineMantle EGGRUMBLE_FieldItemPickups EGGRUMBLE_RaidItemIntake
    EGGRUMBLE_NeutralStoneGiant EGGRUMBLE_BossSessionFence
    EGGRUMBLE_CombatFeel EGGRUMBLE_ProceduralSkills
    """.split()
)
DOMAIN_NAMES = {
    "character": "EGGRUMBLE_SevenRoleCombat",
    "field": "EGGRUMBLE_BotPathRouter",
    "battle": "EGGRUMBLE_AttackGeometry",
    "castle_egg": "EGGRUMBLE_CastleMatchRules",
    "neutral": "EGGRUMBLE_SwarmCombat",
    "item": "EGGRUMBLE_FieldItemPickups",
    "lobby": "EGGRUMBLE_LobbyCastleModesPreview",
    "balance": "EGGRUMBLE_CombatBalance",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path, project: Path, errors: list[str], label: str) -> dict:
    """Collect real source file bytes in Rojo positions, fail closed on ambiguity."""
    try:
        tree = json.loads(project.read_text(encoding="utf-8"))["tree"]
    except (ValueError, OSError, KeyError) as exc:
        errors.append(f"{label}: invalid project: {exc}")
        return {}
    if tree.get("$className") != "DataModel":
        errors.append(f"{label}: project is not DataModel")
    found = {}
    paths = set()

    def walk(node, location):
        if not isinstance(node, dict):
            errors.append(f"{label}: invalid node {location}")
            return
        if "$path" in node:
            name = location[-1]
            placement = location[:-1]
            path = node["$path"]
            if not isinstance(path, str) or not path.endswith(".luau"):
                errors.append(f"{label}: bad Luau source path {name}")
                return
            actual = (root / path).resolve()
            if not actual.is_relative_to(root.resolve()) or not actual.is_file():
                errors.append(f"{label}: missing or escaping source {name} -> {path}")
                return
            if name in found or actual in paths:
                errors.append(f"{label}: duplicate source name/path {name}")
                return
            paths.add(actual)
            if placement not in (SERVER, CLIENT):
                errors.append(f"{label}: disallowed runtime placement {name} / {placement}")
            if placement == SERVER and path.endswith(".client.luau"):
                errors.append(f"{label}: client script is on server {name}")
            if placement == CLIENT and not path.endswith(".client.luau"):
                errors.append(f"{label}: non-client script is in player scripts {name}")
            if placement == SERVER and name == "EGGRUMBLE_LobbyCastleModesPreview":
                if not path.endswith(".server.luau"):
                    errors.append(f"{label}: match host not server Script")
            found[name] = {"path": path, "place": "/".join(placement), "sha256": digest(actual)}
            return
        for key, child in node.items():
            if key.startswith("$"):
                continue
            walk(child, location + (key,))

    walk(tree, ())
    for name in sorted(MANDATORY - found.keys()):
        errors.append(f"{label}: mandatory V3 source missing: {name}")
    if len([n for n in found if n == "EGGRUMBLE_LobbyCastleModesPreview"]) != 1:
        errors.append(f"{label}: one canonical match host required")
    if any(n in found for n in ("Game", "SevenHeroArena", "EGGRUMBLE_MassBattleCastlePreview")):
        errors.append(f"{label}: multiple match owners")
    return found


def check(author_dir: Path, candidate_dir: Path, author_project: Path,
          candidate_project: Path, provenance: dict,
          latest_author_head: str, latest_rc_head: str) -> dict:
    errors = []
    for key in ("author_sha", "candidate_sha", "rc_sha"):
        if not isinstance(provenance.get(key), str) or not SHA40.fullmatch(provenance[key]):
            errors.append(f"provenance: invalid {key}")
    if provenance.get("schema") != SCHEMA:
        errors.append("provenance: unsupported schema")
    if not SHA40.fullmatch(latest_author_head) or not SHA40.fullmatch(latest_rc_head):
        errors.append("provenance: latest HEAD inputs must be verified 40-digit SHAs")
    if provenance.get("author_sha") != latest_author_head:
        errors.append("STALE_AUTHOR: candidate compiled against an older #482 HEAD")
    if provenance.get("rc_sha") != latest_rc_head:
        errors.append("STALE_RC: official #220 RC moved; re-review before CAS")
    original = inventory(author_dir, author_project, errors, "author")
    candidate = inventory(candidate_dir, candidate_project, errors, "candidate")
    overlays = provenance.get("overlays", {})
    if not isinstance(overlays, dict):
        errors.append("provenance: overlays must be a name-indexed object")
        overlays = {}
    for name in sorted(original.keys() - candidate.keys()):
        errors.append(f"candidate: deleted author source {name}")
    for name in sorted(candidate.keys()):
        current = candidate[name]
        prior = original.get(name)
        overlay = overlays.get(name)
        if prior and current == prior:
            if overlay is not None:
                errors.append(f"{name}: declared overlay without actual change")
            continue
        if not isinstance(overlay, dict):
            errors.append(f"{name}: changed/added source lacks owner-scoped overlay")
            continue
        for field in ("owner", "feature_id", "reason", "rollback"):
            if not isinstance(overlay.get(field), str) or not overlay[field].strip():
                errors.append(f"{name}: overlay requires {field}")
        if overlay.get("sha256") != current["sha256"]:
            errors.append(f"{name}: source hash differs from approved overlay")
        if prior:
            if overlay.get("original_sha256") != prior["sha256"]:
                errors.append(f"{name}: source predecessor was not pinned")
            if prior["place"] != current["place"]:
                errors.append(f"{name}: source moved between server/client without review")
        elif overlay.get("original_sha256") is not None:
            errors.append(f"{name}: new source must not invent an original digest")
    for name in sorted(overlays.keys() - candidate.keys()):
        errors.append(f"provenance: orphaned overlay {name}")
    if len(candidate) != len(set(candidate)):
        errors.append("candidate: duplicate runtime names")
    status = "SOURCE_GATE_PASS" if not errors else "SOURCE_NO_GO"
    return {
        "schema": SCHEMA,
        "status": status,
        "latest_author_sha": latest_author_head,
        "latest_rc_sha": latest_rc_head,
        "candidate_sha": provenance.get("candidate_sha"),
        "source_count_author": len(original),
        "source_count_candidate": len(candidate),
        "domain_inventory": {domain: name in candidate for domain, name in DOMAIN_NAMES.items()},
        "changed_sources": sorted(
            n for n in candidate if candidate[n] != original.get(n)
        ),
        "errors": errors,
        "official_rc_integrated": False,
        "studio_test": "NOT_TESTED",
        "android_test": "NOT_TESTED",
        "owner_accepted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("author-dir", "candidate-dir", "author-project", "candidate-project",
                "provenance", "latest-author-head", "latest-rc-head"):
        parser.add_argument("--" + key, required=True)
    args = parser.parse_args(argv)
    try:
        result = check(
            Path(args.author_dir), Path(args.candidate_dir),
            Path(args.author_project), Path(args.candidate_project),
            json.loads(Path(args.provenance).read_text(encoding="utf-8")),
            args.latest_author_head, args.latest_rc_head
        )
    except (OSError, ValueError) as exc:
        result = {"schema": SCHEMA, "status": "SOURCE_NO_GO", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "SOURCE_GATE_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
