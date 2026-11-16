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
from runtime_activation import REQUIRED_RUNTIME_SOURCES, evaluate_runtime_activation
from urllib.parse import quote

REPO = "kk051780/toy-wars-factory"
PROJECT = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_V3_STUDIO.project.json"
COMPOSER = ".github/workflows/p0d-eggrumble-gq-art-score-composite.yml"
OFFICIAL = "rc/p0d-s1-kids-rc01"
PRS = {"author": 482, "quality": 484, "art": 485, "score": 487}
DOMAINS = {
    "character": ("SevenRoleCombat", "WeaponSilhouettes", "ProceduralSkills", "DivineMantle"),
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



# Source-of-truth for the current 26-source composer. The older ART/SCORE21
# workflow is intentionally retained by the original author as a historical
# comparison and MUST NOT be used to judge the active 26-source integration.
CURRENT26_WORKFLOW = ".github/workflows/p0d-eggrumble-gq-current26-private.yml"
CURRENT26_COMPOSER = "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/compose.py"
CURRENT26_RUN_NAME = "P0D GQ current V3 author plus ART SCORE 26-source private build"
CURRENT26_BRANCH = "quality/eggrumble-v3-spatial-bot-intake-20261116"
CURRENT26_ART = frozenset({
    "EGGRUMBLE_HeroSilhouetteArt", "EGGRUMBLE_FlagshipFieldArt",
    "EGGRUMBLE_EncounterReadabilityArt", "EGGRUMBLE_ArtDistanceLOD",
})
CURRENT26_SCORES = frozenset({"EGGRUMBLE_ScoreBalance", "EGGRUMBLE_MatchResultService"})


def current26_pins(workflow_text: str) -> list[str]:
    """Get only the three live original-author checkouts, not the Luau tool ref."""
    start = workflow_text.find("Read fixed latest game SOURCE from original author PR482")
    end = workflow_text.find("Build fixed Luau native compiler and test runner")
    if start < 0 or end <= start:
        raise ValueError("current 26-source checkout section missing")
    return re.findall(r"(?m)^\s*ref:\s*([0-9a-f]{40})\s*$",
                      workflow_text[start:end])


def evaluate_active26(prs: dict, author_project: dict, author_blobs: dict,
                      quality_blobs: dict, workflow_text: str, composer_text: str,
                      workflow_runs: list, official_sha: str) -> dict:
    """Evaluate the *active* 26-source build, not the retired game-core manifest.

    The generator's source-exact output is attested only by its own exact-HEAD
    Action run; no assertion here asserts Studio operation or official adoption.
    """
    author = project_nodes(author_project)
    defects = []
    domains = {}
    for domain, required in DOMAINS.items():
        missing = sorted("EGGRUMBLE_" + stem for stem in required
                         if "EGGRUMBLE_" + stem not in author)
        domains[domain] = {"author_source_present": not missing,
                           "missing": missing,
                           "current26_coverage": "AUTHOR_21_PLUS_4ART_1SCORE_BUILD_CI_REQUIRED"}
        if missing:
            defects.append("author_contract_missing:" + domain + ":" + ",".join(missing))
    if len(author) != 21:
        defects.append("author_expected_21_game_scripts_actual_" + str(len(author)))
    services = {name: node["service"] for name,node in author.items()}
    if sum(v == "ServerScriptService" for v in services.values()) != 19:
        defects.append("author_server_count_not_19")
    if sum(v == "StarterPlayer/StarterPlayerScripts" for v in services.values()) != 2:
        defects.append("author_client_count_not_2")
    for name,entry in author.items():
        if not author_blobs.get(entry["path"]):
            defects.append("author_blob_unknown:" + name)

    pins = current26_pins(workflow_text)
    if len(pins) != 3:
        defects.append("current26_workflow_expected_three_author_pins")
    for idx, role in enumerate(("author", "art", "score")):
        if len(pins) <= idx or pins[idx] != prs[role]["head"]["sha"]:
            defects.append("current26_" + role + "_pin_stale")

    # Require actual source-composer and its claimed selection algorithm from
    # the quality author; do not mistake the old 16-source test project as output.
    required_contract = [
        "def apply_ramp(", "EGGRUMBLE_BotActors", "EGGRUMBLE_BotPathRouter",
        "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_ProceduralSkills",
        "EGGRUMBLE_RaidItemIntake", "EGGRUMBLE_NeutralStoneGiant",
        "EGGRUMBLE_BossSessionFence", "EGGRUMBLE_ScoreBalance",
        "EGGRUMBLE_ArtDistanceLOD", "assert len(server)-1==23 and len(client)-1==3",
        'assert len(mapped)==26', '\"source_sha256\"',
    ]
    for contract in required_contract:
        if contract not in composer_text:
            defects.append("current26_composer_contract_missing:" + contract)
    for part in (CURRENT26_WORKFLOW, CURRENT26_COMPOSER):
        if part not in quality_blobs:
            defects.append("current26_quality_file_missing:" + part)
    if not HEX40.fullmatch(official_sha):
        defects.append("official_rc_head_unknown")

    current_head = prs["quality"]["head"]["sha"]
    qualified_runs = [run for run in workflow_runs
                      if run.get("name") == CURRENT26_RUN_NAME
                      and run.get("head_sha") == current_head]
    latest_run = qualified_runs[0] if qualified_runs else {}
    if latest_run.get("status") != "completed" or latest_run.get("conclusion") != "success":
        defects.append("current26_samehead_CI_not_success")
    # The workflow source is reviewed read-only, the real Rojo native pass
    # remains the job's actual conclusion, not a fabricated runtime claim.
    report = {
        "schema": "P0D_EGGRUMBLE_LIVE_RC_INTAKE_DRIFT_V2",
        "decision": "SOURCE_RECONCILIATION_REQUIRED" if defects else "SOURCE_REVIEW_READY_ONLY",
        "source_candidate": "CURRENT26_21_GAME_4_ART_1_SCORE",
        "heads": {role: pr["head"]["sha"] for role,pr in prs.items()},
        "official_rc_head": official_sha,
        "official_rc_adopted": "NOT_VERIFIED_REQUIRES_220_CAS_RECEIPT",
        "studio_android_art_fun_owner": "NOT_VERIFIED",
        "author_script_count": len(author),
        "target_candidate_script_count": 26,
        "expected_server_scripts": 23,
        "expected_client_scripts": 3,
        "domains": domains,
        "pinned_source_heads": dict(zip(("author", "art", "score"),pins)),
        "composite_ci": {
            "head": current_head,
            "run_id": latest_run.get("id"),
            "status": latest_run.get("status", "NOT_FOUND"),
            "conclusion": latest_run.get("conclusion", "NOT_FOUND"),
            "run_url": latest_run.get("html_url"),
        },
        "obsolete_21_source_workflow_not_used_as_latest_proof": True,
        "blockers": defects,
        "next_owner": "#484 for current26 composite; #220 ONLY for official RC integration",
    }
    return report

def live_audit() -> dict:
    prs = {name: api("pulls/" + str(number)) for name,number in PRS.items()}
    author_sha = prs["author"]["head"]["sha"]
    quality_sha = prs["quality"]["head"]["sha"]
    author_project = json.loads(github_file(PROJECT, author_sha))
    workflow = github_file(CURRENT26_WORKFLOW, quality_sha)
    composer = github_file(CURRENT26_COMPOSER, quality_sha)
    author_blobs = tree_blobs(api("git/trees/" + author_sha + "?recursive=1"))
    quality_blobs = tree_blobs(api("git/trees/" + quality_sha + "?recursive=1"))
    official = api("git/ref/heads/" + OFFICIAL)["object"]["sha"]
    from urllib.parse import urlencode
    runs = api("actions/runs?" + urlencode(
        {"branch": CURRENT26_BRANCH, "per_page": 60})).get("workflow_runs", [])
    report = evaluate_active26(prs, author_project, author_blobs, quality_blobs,
                               workflow, composer, runs, official)
    # Independent, non-invasive runtime boundary for all 8 domains. A native
    # source/Place PASS cannot prove the Studio-only preview works in a normal
    # Roblox server or Android client.
    nodes = project_nodes(author_project)
    runtime_sources = {name: github_file(nodes[name]["path"], author_sha)
                       for name in REQUIRED_RUNTIME_SOURCES if name in nodes}
    report["runtime_activation"] = evaluate_runtime_activation(runtime_sources)
    report["product_go"] = False
    return report

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("P0D_LIVE_RC_SOURCE_DRIFT.json"))
    parser.add_argument("--strict", action="store_true",
                        help="Nonzero when latest SOURCE reconciliation is blocked")
    parser.add_argument("--require-no-studio-only-guards", action="store_true",
                        help="Separate product-preflight code 3 for Studio-only source guards; "
                             "even when this passes, real device evidence remains required")
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
    if args.require_no_studio_only_guards:
        activation = report.get("runtime_activation", {})
        if activation.get("production_runtime") != "NOT_VERIFIED_FAIL_CLOSED" or \
           activation.get("source_guard_inspection") != "COMPLETE":
            raise SystemExit(3)


if __name__ == "__main__":
    main()
