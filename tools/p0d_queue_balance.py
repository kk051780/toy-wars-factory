#!/usr/bin/env python3
"""P0D two-lane READY supply balancer. Pure, read-only planning; no GitHub writes."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

_SHA = re.compile(r"^[0-9a-f]{40}$")
_FEATURE = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
_STATES = ("QUEUE_RED", "QUEUE_LOW", "QUEUE_BALANCED", "QUEUE_STOCKED")
_RATIOS = ((70, 30), (60, 40), (50, 50), (30, 70))
# Prioritise a meaningful player action, not catalogue row count or speculative assets.
_PREFERRED_SOURCE = (
    "P0D-018",  # capture / restraint
    "P0D-017",  # elite neutral enemies
    "P0D-040",  # XP/level-up
    "P0D-038",  # beast equipment / scout
    "P0D-027",  # cosmic zero gravity
    "P0D-044",  # evolution index
)
_GROUP_RANK = {
    "戦闘": 0, "育成・戦闘": 1, "収集育成": 2,
    "世界": 3, "世界・収集": 4, "基本": 5, "ロビー収益": 6,
}


class InvalidSnapshot(ValueError):
    pass


def _id_list(values: Any, field: str) -> set[str]:
    if not isinstance(values, list) or not all(isinstance(v, str) and _FEATURE.fullmatch(v) for v in values):
        raise InvalidSnapshot(f"INVALID_{field}")
    return set(values)


def balance(queue: dict[str, Any], catalog: dict[str, Any],
            claimed_feature_ids: list[str] | None = None) -> dict[str, Any]:
    """Plan A/B work from one verified queue snapshot; never mark a PR READY.

    'claimed_feature_ids' are externally verified active work IDs, not assumed leases.
    A recommendation is not a lock, authorisation, PR approval, or RC adoption.
    """
    if not isinstance(queue, dict) or queue.get("schema") != "P0D_TWO_LANES_V1":
        raise InvalidSnapshot("UNTRUSTED_QUEUE_SCHEMA")
    sha = queue.get("official_head")
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise InvalidSnapshot("UNTRUSTED_OFFICIAL_RC_SHA")
    selected = queue.get("selected")
    n = queue.get("ready_count")
    if (not isinstance(selected, list) or not isinstance(n, int)
            or isinstance(n, bool) or n < 0 or len(selected) != n):
        raise InvalidSnapshot("READY_COUNT_OR_SELECTION_MISMATCH")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("rows"), list):
        raise InvalidSnapshot("UNTRUSTED_CATALOG")
    rows = catalog["rows"]
    if any(not isinstance(r, dict) or not isinstance(r.get("id"), str)
           or not isinstance(r.get("stage"), str) for r in rows):
        raise InvalidSnapshot("INVALID_CATALOG_ROW")
    if len(set(r["id"] for r in rows)) != len(rows):
        raise InvalidSnapshot("DUPLICATE_CATALOG_ID")
    if any(r["stage"] not in ("IDEA", "SOURCE", "RC", "STUDIO", "FUN") for r in rows):
        raise InvalidSnapshot("UNKNOWN_CATALOG_STAGE")

    if queue.get("claims_scan_complete") is not True:
        raise InvalidSnapshot("OPEN_PR_CLAIMS_SCAN_INCOMPLETE")
    active_claims = queue.get("open_pr_title_claims")
    if not isinstance(active_claims, list):
        raise InvalidSnapshot("OPEN_PR_CLAIMS_MISSING")
    active_by_id: dict[str, set[int]] = {}
    for item in active_claims:
        if (not isinstance(item, dict)
                or not isinstance(item.get("feature_id"), str)
                or not _FEATURE.fullmatch(item["feature_id"])
                or not isinstance(item.get("pr"), int) or isinstance(item["pr"], bool)
                or item["pr"] < 1
                or not isinstance(item.get("head"), str)
                or not _SHA.fullmatch(item["head"])
                or not isinstance(item.get("draft"), bool)):
            raise InvalidSnapshot("INVALID_OPEN_PR_CLAIM")
        active_by_id.setdefault(item["feature_id"], set()).add(item["pr"])
    occupied = _id_list(claimed_feature_ids or [], "CLAIMS")
    occupied.update(active_by_id)
    seen_ready = set()
    for item in selected:
        if (not isinstance(item, dict)
                or item.get("status") != "READY_FOR_SOLE_WRITER_REVIEW"
                or not isinstance(item.get("pr"), int)
                or not isinstance(item.get("head"), str)
                or not _SHA.fullmatch(item["head"])):
            raise InvalidSnapshot("UNVERIFIED_READY_ENTRY")
        ids = _id_list(item.get("features"), "READY_FEATURE_IDS")
        if not ids or ids & seen_ready:
            raise InvalidSnapshot("DUPLICATE_OR_EMPTY_READY_FEATURES")
        seen_ready.update(ids)
    occupied.update(seen_ready)
    catalog_by_id = {r["id"]: r["stage"] for r in rows}
    eligible_ready = []
    excluded_adopted = []
    for item in selected:
        adopted_ids = [fid for fid in item["features"]
                       if catalog_by_id.get(fid) in ("RC", "STUDIO", "FUN")]
        if adopted_ids:
            excluded_adopted.append({"pr": item["pr"], "already_adopted": sorted(adopted_ids)})
        else:
            eligible_ready.append(item)
    eligible_count = len(eligible_ready)

    level = 0 if eligible_count == 0 else 1 if eligible_count == 1 else 2 if eligible_count <= 3 else 3
    state = _STATES[level]
    prep_pct, integrate_pct = _RATIOS[level]
    # SOURCE-backed gameplay before IDEA-only ideation. Never duplicate active/READY IDs.
    source = [r for r in rows if r["stage"] == "SOURCE" and r["id"] not in occupied]
    idea = [r for r in rows if r["stage"] == "IDEA" and r["id"] not in occupied]
    def rank(r: dict) -> tuple:
        ident = r["id"]
        preferred = _PREFERRED_SOURCE.index(ident) if ident in _PREFERRED_SOURCE else 999
        return (
            0 if r.get("release") == "S1" else 1,
            preferred,
            _GROUP_RANK.get(r.get("group", ""), 9),
            ident,
        )

    source.sort(key=rank)
    idea.sort(key=rank)
    slots = 2 if eligible_count <= 1 else 1
    has_source_backlog = any(r["stage"] == "SOURCE" for r in rows)
    # An already-owned SOURCE item must be finished, not replaced by speculative IDEA.
    targets = (source if source else [] if has_source_backlog else idea)[:slots]
    target_stage = ("SOURCE_TO_READY" if source else
                    "ASSIST_CLAIMED_SOURCE" if has_source_backlog else
                    "IDEA_TO_REAL_SOURCE" if idea else "NO_UNCLAIMED_BACKLOG")
    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row["stage"]] = statuses.get(row["stage"], 0) + 1
    result = {
        "schema": "P0D_AUTO_QUEUE_BALANCE_V1",
        "official_head": sha,
        "queue_state": state,
        "ready_count": eligible_count,
        "raw_selected_ready_count": n,
        "excluded_already_adopted_prs": excluded_adopted,
        "target_work_split_pct": {"A_PREP": prep_pct, "B_INTEGRATOR": integrate_pct},
        "a_target_stage": target_stage,
        "a_suggested_feature_ids": [r["id"] for r in targets],
        "a_suggested_features": [{"id": r["id"], "name": r.get("name", ""),
                                  "from_stage": r["stage"], "group": r.get("group", "")}
                                 for r in targets],
        "b_ready_prs": [{"pr": x["pr"], "head": x["head"], "features": x["features"]}
                        for x in eligible_ready],
        "a_assist_existing_prep_prs": [
            {"feature_id": fid, "prs": sorted(active_by_id[fid])}
            for fid in sorted(active_by_id)
            if catalog_by_id.get(fid) == "SOURCE"
        ][:2],
        "catalog_total": len(rows),
        "catalog_stages": statuses,
        "blocked_by_external_claims": sorted(_id_list(claimed_feature_ids or [], "CLAIMS")),
        "blocked_by_open_pr_claims": [
            {"feature_id": fid, "prs": sorted(nums)} for fid, nums in sorted(active_by_id.items())
        ],
        "priority_fun_validation": ["#340 HUD real Studio/Android", "#341 solo launch real Studio"],
        "writer": "ONLY_AUTHENTICATED_ISSUE_220_CAS",
        "human_studio_fun": "NOT_INFERRED",
        "no_auto_merge": True,
        "no_branch_writes": True,
        "note": ("Suggestions are not work leases or CI evidence. A must obtain a "
                 "non-overlapping author claim; B rechecks latest live official HEAD "
                 "and Sourcery before any licensed RC CAS write."),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--queue", required=True, help="Existing read-only P0D_PREP_INBOX.json")
    p.add_argument("--catalog", required=True, help="FEATURE_CATALOG.json at same official snapshot")
    p.add_argument("--catalog-head", required=True, help="git rev-parse HEAD of trusted catalog checkout")
    p.add_argument("--claims", help="Optional JSON array of currently claimed feature IDs")
    p.add_argument("--out", default="-")
    opts = p.parse_args(argv)
    q = json.loads(Path(opts.queue).read_text(encoding="utf-8"))
    c = json.loads(Path(opts.catalog).read_text(encoding="utf-8"))
    claims = json.loads(Path(opts.claims).read_text(encoding="utf-8")) if opts.claims else None
    if not _SHA.fullmatch(opts.catalog_head) or q.get("official_head") != opts.catalog_head:
        raise InvalidSnapshot("QUEUE_AND_TRUSTED_CATALOG_HEAD_MISMATCH")
    result = balance(q, c, claims)
    result["trusted_catalog_checkout_head"] = opts.catalog_head
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if opts.out == "-":
        print(output, end="")
    else:
        Path(opts.out).write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
