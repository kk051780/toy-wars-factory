#!/usr/bin/env python3
"""Read-only EGGRUMBLE latest-source/RC intake freshness audit.

Unlike Studio evidence checking or author-specific tests, this compares the
actual live PR heads, Rojo module maps, Git blob identities, and fixed ART/SCORE
composer pins. It does NOT merge, write the official RC, or certify gameplay.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import posixpath
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote

REPO = "kk051780/toy-wars-factory"
PROJECT = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_V3_STUDIO.project.json"
COMPOSER = ".github/workflows/p0d-eggrumble-gq-art-score-composite.yml"
OFFICIAL = "rc/p0d-s1-kids-rc01"
PRS = {"author": 482, "quality": 484, "art": 485, "score": 487}
DOMAINS = {
    "character": ("SevenRoleCombat", "WeaponSilhouettes", "ProceduralSkills"),
    "field": ("BotPathRouter", "BotActors", "LobbyCastleModesPreview"),
    "battle": ("SevenRoleCombat", "AttackGeometry", "CombatFeel", "ImpactFeedback"),
    "castle_egg": ("CastleMatchRules", "InteractionGuard", "LobbyCastleModesPreview"),
    "neutral": ("SwarmCombat", "NeutralStoneGiant", "BossSessionFence"),
    "item": ("FieldItemPickups", "RaidItemIntake"),
    "lobby": ("LobbyCastleModesPreview", "RoundReplay"),
    "balance": ("CombatBalance", "MatchResultService"),
}
# These are #484-owned source adaptations; their exact diff needs human review.
QUALITY_OVERRIDES = frozenset({"BotActors", "BotPathRouter", "LobbyCastleModesPreview"})
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def api(path: str) -> dict:
    url = "https://api.github.com/repos/" + REPO + "/" + path
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "p0d-live-source-drift-gate"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as result:
        return json.load(result)


def github_file(path: str, ref: str) -> str:
    assert HEX40.fullmatch(ref), "source ref must be full immutable commit SHA"
    response = api("contents/" + quote(path, safe="/") + "?ref=" + ref)
    if response.get("encoding") != "base64" or response.get("type") != "file":
        raise ValueError("Not an individually pinned source file: " + path)
    return base64.b64decode(response["content"]).decode("utf-8")


def project_nodes(project: dict) -> dict:
    """Resolve Rojo service paths to one unambiguous executable source per node."""
    nodes = {}
    def walk(branch: dict, parts: tuple[str, ...] = ()) -> None:
        for name, value in branch.items():
            if name.startswith("$") or not isinstance(value, dict):
                continue
            at = parts + (name,)
            if "$path" not in value:
                walk(value, at)
                continue
            filename = value["$path"]
            if not isinstance(filename, str) or not filename.endswith(".luau"):
                raise ValueError("non-Luau executable mapping: " + repr(filename))
            if name in nodes:
                raise ValueError("duplicate executable name: " + name)
            fullpath = posixpath.normpath(posixpath.join(posixpath.dirname(PROJECT), filename))
            if fullpath.startswith("../") or fullpath.startswith("/"):
                raise ValueError("source escaped repository: " + fullpath)
            kind = ("LocalScript" if filename.endswith(".client.luau") else
                    "Script" if filename.endswith(".server.luau") else "ModuleScript")
            nodes[name] = {"path": fullpath, "class": kind, "service": "/".join(at[:-1])}
    walk(project["tree"])
    return nodes


def tree_blobs(tree: dict) -> dict[str, str]:
    if tree.get("truncated"):
        raise ValueError("Git tree truncated, refusing partial source identity audit")
    return {e["path"]: e["sha"] for e in tree.get("tree", [])
            if e.get("type") == "blob" and isinstance(e.get("sha"), str)}


def evaluate(prs: dict, author_project: dict, quality_project: dict,
             composer_text: str, author_blobs: dict, quality_blobs: dict,
             official_sha: str) -> dict:
    author = project_nodes(author_project)
    quality = project_nodes(quality_project)
    defects: list[str] = []
    overrides: list[str] = []
    drifts: list[str] = []
    extra = sorted(set(quality) - set(author))
    if extra:
        defects.append("unowned_added_modules:" + ",".join(extra))

    domains = {}
    for domain, required in DOMAINS.items():
        absent_author = sorted("EGGRUMBLE_" + x for x in required
                               if "EGGRUMBLE_" + x not in author)
        absent_quality = sorted("EGGRUMBLE_" + x for x in required
                                if "EGGRUMBLE_" + x not in quality)
        domains[domain] = {"original_missing": absent_author,
                           "quality_missing": absent_quality,
                           "candidate_ready": not absent_author and not absent_quality}
        if absent_author:
            defects.append("author_contract_missing:" + domain + ":" + ",".join(absent_author))
        if absent_quality:
            defects.append("quality_candidate_missing:" + domain + ":" + ",".join(absent_quality))

    for name in sorted(set(author) & set(quality)):
        a, q = author[name], quality[name]
        if a["class"] != q["class"] or a["service"] != q["service"]:
            defects.append("class_or_service_mismatch:" + name)
        ablob, qblob = author_blobs.get(a["path"]), quality_blobs.get(q["path"])
        if not ablob or not qblob:
            defects.append("source_blob_unknown:" + name)
        elif ablob != qblob:
            if name.removeprefix("EGGRUMBLE_") in QUALITY_OVERRIDES:
                overrides.append(name)
            else:
                drifts.append(name)
    if drifts:
        defects.append("original_source_identity_drift:" + ",".join(drifts))
    if prs["quality"]["base"]["sha"] != prs["author"]["head"]["sha"]:
        defects.append("quality_base_not_latest_author_head")

    pins = re.findall(r"(?m)^\s*ref:\s*([0-9a-f]{40})\s*$", composer_text)
    for role, idx in (("art", 0), ("score", 1)):
        if len(pins) <= idx or pins[idx] != prs[role]["head"]["sha"]:
            defects.append(role + "_composer_pin_not_latest_head")
    # HEAD-only source comparison cannot prove any source was admitted to official RC.
    if not HEX40.fullmatch(official_sha):
        defects.append("official_rc_head_unknown")
    report = {
        "schema": "P0D_EGGRUMBLE_LIVE_RC_INTAKE_DRIFT_V1",
        "decision": "SOURCE_RECONCILIATION_REQUIRED" if defects else "SOURCE_REVIEW_READY_ONLY",
        "official_rc_head": official_sha,
        "official_rc_adopted": "UNVERIFIED_REQUIRES_220_CAS_RECEIPT",
        "studio_android_fun_owner": "NOT_VERIFIED_BY_THIS_GATE",
        "heads": {key: value["head"]["sha"] for key, value in prs.items()},
        "quality_base_sha": prs["quality"]["base"]["sha"],
        "module_count": {"latest_author": len(author), "quality_game_core": len(quality)},
        "domains": domains, "quality_owned_overrides_needing_diff_review": overrides,
        "unowned_identity_drifts": drifts,
        "art_score_composer_pins": pins[:2],
        "blockers": defects,
        "next_owner": "#484 for composer/source reconciliation; #220 ONLY for official RC CAS",
    }
    return report


def live_audit() -> dict:
    prs = {name: api("pulls/" + str(number)) for name, number in PRS.items()}
    author_sha = prs["author"]["head"]["sha"]
    quality_sha = prs["quality"]["head"]["sha"]
    author_project = json.loads(github_file(PROJECT, author_sha))
    quality_project = json.loads(github_file(PROJECT, quality_sha))
    composer_text = github_file(COMPOSER, quality_sha)
    author_blobs = tree_blobs(api("git/trees/" + author_sha + "?recursive=1"))
    quality_blobs = tree_blobs(api("git/trees/" + quality_sha + "?recursive=1"))
    official = api("git/ref/heads/" + OFFICIAL)["object"]["sha"]
    return evaluate(prs, author_project, quality_project, composer_text,
                    author_blobs, quality_blobs, official)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("P0D_LIVE_RC_SOURCE_DRIFT.json"))
    parser.add_argument("--strict", action="store_true",
                        help="Nonzero when latest source reconciliation is blocked")
    args = parser.parse_args()
    try:
        report = live_audit()
    except Exception as exc:
        report = {"schema": "P0D_EGGRUMBLE_LIVE_RC_INTAKE_DRIFT_V1",
                  "decision": "AUDIT_UNAVAILABLE_FAIL_CLOSED",
                  "blockers": [type(exc).__name__ + ": " + str(exc)],
                  "official_rc_adopted": "UNVERIFIED"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report["decision"] != "SOURCE_REVIEW_READY_ONLY":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
