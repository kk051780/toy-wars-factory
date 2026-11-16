#!/usr/bin/env python3
"""Compose pre-existing source, live-runtime, and original-composer receipts.

Do not reimplement the #484 composer, #490 runtime source inspection, or #488
real Studio/Android evidence evaluation. Source admission != product acceptance.
Never write official RC or infer a player test from GitHub CI.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DOMAINS = ("character", "field", "battle", "castle_egg", "neutral",
           "item", "lobby", "balance")
HEXSHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
SOURCE_SCHEMA = "EGGRUMBLE_V3_RC_LINEAGE_V1"
LIVE_SCHEMA = "P0D_EGGRUMBLE_LIVE_RC_INTAKE_DRIFT_V2"


def valid_shas(mapping: dict, length_pattern: re.Pattern) -> bool:
    return isinstance(mapping, dict) and bool(mapping) and all(
        isinstance(n, str) and isinstance(v, str) and
        length_pattern.fullmatch(v) for n, v in mapping.items()
    )


def evaluate(source: dict, build: dict, live: dict) -> dict:
    """A single evidence receipt for #220 intake, not an authorization token.

    Fail on mismatch; keep the original #490 source/runtime decision visible.
    #488 is the sole owner of real device evidence. Absence remains NOT_TESTED.
    """
    errors: list[str] = []
    if source.get("schema") != SOURCE_SCHEMA or source.get("status") != "SOURCE_GATE_PASS":
        errors.append("SOURCE_LINEAGE_NOT_GREEN")
    if source.get("full_26_owner_byte_identity") is not True:
        errors.append("ORIGINAL_OWNER_BYTES_UNVERIFIED")
    if source.get("source_count_author") != 21 or source.get("source_count_candidate") != 26:
        errors.append("SINGLE_GAME_21_TO_26_COUNT_MISMATCH")
    if source.get("quality_source_equivalent_to_live_head") is not True:
        errors.append("LATEST_QUALITY_SOURCE_NOT_IDENTICAL")
    inventory = source.get("domain_inventory")
    if not isinstance(inventory, dict) or set(inventory) != set(DOMAINS):
        errors.append("INCOMPLETE_EIGHT_DOMAIN_INVENTORY")
        inventory = {}
    elif any(inventory.get(n) is not True for n in DOMAINS):
        errors.append("MISSING_GAME_SOURCE_DOMAIN")
    original_shas = source.get("owner_heads")
    live_shas = live.get("heads")
    if not isinstance(original_shas, dict) or not isinstance(live_shas, dict):
        errors.append("MISSING_ACTUAL_AUTHOR_HEADS")
        original_shas, live_shas = {}, {}
    for role, number in (("author", "#482"), ("art", "#485"), ("score", "#487")):
        if not HEXSHA.fullmatch(str(original_shas.get(number, ""))) or \
           original_shas[number] != live_shas.get(role):
            errors.append("AUTHOR_HEAD_MISMATCH_" + role.upper())
    if not HEXSHA.fullmatch(str(source.get("quality_live_head", ""))) or \
       source.get("quality_live_head") != live_shas.get("quality"):
        errors.append("LIVE_QUALITY_HEAD_MISMATCH")
    official = source.get("latest_rc_sha")
    if not HEXSHA.fullmatch(str(official or "")) or official != live.get("official_rc_head"):
        errors.append("OFFICIAL_RC_HEAD_MISMATCH")

    candidate_hashes = source.get("candidate_source_sha256")
    receipt_hashes = build.get("source_sha256")
    if not valid_shas(candidate_hashes, DIGEST) or not valid_shas(receipt_hashes, DIGEST):
        errors.append("SOURCE_DIGEST_MANIFEST_MISSING")
    elif (len(candidate_hashes) != 26 or len(receipt_hashes) != 26
          or candidate_hashes != receipt_hashes):
        errors.append("COMPOSER_SOURCE_BYTES_DISAGREE")
    if build.get("script_count") != 26 or build.get("server_count") != 23 or \
       build.get("client_count") != 3:
        errors.append("COMPOSER_SERVICE_OR_COUNT_MISMATCH")
    if build.get("status") != "SOURCE_ONLY_NOT_OFFICIAL_RC":
        errors.append("UNEXPECTED_AUTHOR_COMPOSER_RELEASE_STATE")

    if live.get("schema") != LIVE_SCHEMA or \
       live.get("decision") != "SOURCE_REVIEW_READY_ONLY" or live.get("blockers"):
        errors.append("LIVE_26_SOURCE_DRIFT_OR_CI_BLOCKED")
    if live.get("target_candidate_script_count") != 26:
        errors.append("LIVE_26_SCRIPT_TOTAL_UNVERIFIED")
    if live.get("composite_ci", {}).get("head") != live_shas.get("quality") or \
       live.get("composite_ci", {}).get("conclusion") != "success" or \
       live.get("composite_ci", {}).get("status") != "completed":
        errors.append("LATEST_COMPOSITE_CI_NOT_GREEN")

    # The production-source gate belongs solely to #490. Do not independently
    # parse Studio-only guards, and do not erase its explicit blockers.
    activation = live.get("runtime_activation")
    if not isinstance(activation, dict) or \
       activation.get("schema") != "EGGRUMBLE_RUNTIME_ACTIVATION_V1" or \
       activation.get("source_guard_inspection") != "COMPLETE":
        errors.append("PRODUCTION_ACTIVATION_INSPECTION_UNAVAILABLE")
        activation = {}
    production = activation.get("production_runtime")
    blocked_domains = activation.get("eight_domain_production_impact")
    if production == "BLOCKED_STUDIO_ONLY_GAME_HOST":
        if not isinstance(blocked_domains, list) or set(blocked_domains) != set(DOMAINS):
            errors.append("PRODUCTION_BLOCKER_EIGHT_DOMAIN_SCOPE_UNKNOWN")
    elif production != "NOT_VERIFIED_FAIL_CLOSED":
        errors.append("UNRECOGNIZED_PRODUCTION_RUNTIME_VERDICT")
    if source.get("official_rc_integrated") is not False or \
       build.get("owner_accepted") is not False or \
       live.get("product_go") is not False:
        errors.append("PREMATURE_RC_OR_OWNER_ACCEPTANCE_CLAIM")

    status = "SOURCE_NO_GO" if errors else (
        "SOURCE_READY_PRODUCTION_BLOCKED" if production == "BLOCKED_STUDIO_ONLY_GAME_HOST"
        else "SOURCE_READY_PRODUCTION_NOT_VERIFIED"
    )
    return {
        "schema": "P0D_GQ_491_CROSS_OWNER_RC_INTAKE_RECEIPT_V1",
        "status": status,
        "source_provenance_pass": not errors,
        "candidate_source_scripts": 26 if not errors else "UNVERIFIED",
        "source_author_heads": original_shas,
        "source_quality_live_head": source.get("quality_live_head"),
        "private_composite_ci": live.get("composite_ci"),
        "official_rc_head_read_only": official,
        "official_rc_integration": "NOT_INTEGRATED_OR_UNVERIFIED",
        "source_admission": "REVIEW_BY_220_ONLY" if not errors else "BLOCKED",
        "production_runtime": production or "UNKNOWN_FAIL_CLOSED",
        "production_blocked_domains": blocked_domains if production == "BLOCKED_STUDIO_ONLY_GAME_HOST" else [],
        "domain_stage": {
            name: {
                "source_present": inventory.get(name) is True,
                "private_source_review": "PASS" if not errors else "NO_GO",
                "studio_runtime": "NOT_TESTED",
                "android_15min": "NOT_TESTED",
                "product_go": False,
            } for name in DOMAINS
        },
        "studio_1p15ai": "NOT_TESTED",
        "studio_2p14ai": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "art_fun_owner": "NO_GO_UNVERIFIED",
        "owner_accepted": False,
        "next_owners": [
            "#482: original game runtime policy and single-host production adapter (source review)",
            "#484: exact 26-source candidate fixes only",
            "#220: authenticated official RC nonforce CAS and same-HEAD receipt only",
            "#488/#420: independent Studio, Android, visual, FUN evidence",
        ],
        "errors": errors,
        "rollback": "Do not adopt candidate; retain pinned official RC HEAD and remove only approved overlays",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--composer", type=Path, required=True)
    p.add_argument("--live", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        result = evaluate(*[
            json.loads(path.read_text(encoding="utf-8"))
            for path in (a.source, a.composer, a.live)
        ])
    except (ValueError, OSError) as error:
        result = {
            "schema": "P0D_GQ_491_CROSS_OWNER_RC_INTAKE_RECEIPT_V1",
            "status": "SOURCE_NO_GO",
            "errors": [type(error).__name__ + ": " + str(error)],
            "official_rc_integration": "NOT_INTEGRATED_OR_UNVERIFIED",
            "owner_accepted": False,
        }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if result["status"] == "SOURCE_NO_GO" else 0


if __name__ == "__main__":
    raise SystemExit(main())
