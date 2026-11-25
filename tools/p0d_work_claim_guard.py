#!/usr/bin/env python3
"""Offline P0D claim collision gate. Fail closed; no network/writes/merge.

Registry must be read from an authorized coordination ref with pinned blob
SHA. Candidate and changed paths must come from live same-HEAD GitHub API.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fnmatch
import json
from pathlib import PurePosixPath
import re
import sys
from typing import Any

SHA = re.compile(r"[0-9a-f]{40}\Z")
TOKEN = re.compile(r"[A-Z][A-Z0-9_-]{2,79}\Z")
BUSY = {"GRANTED", "SOURCE_WIP", "PREP_READY", "HANDOFF_PENDING", "BLOCKED"}


def fail(reason: str) -> None:
    raise ValueError(reason)


def valid_paths(paths: Any) -> set[str]:
    if not isinstance(paths, list) or not paths:
        fail("MISSING_CHANGED_PATHS")
    result: set[str] = set()
    for p in paths:
        if not isinstance(p, str) or len(p) > 250 or not p or "\\" in p or p.startswith("/") or ".." in PurePosixPath(p).parts:
            fail("INVALID_TARGET_PATH")
        result.add(p.casefold())
    return result


def pat_overlap(a: str, b: str) -> bool:
    if fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a):
        return True
    wild = "*?["
    pa = a[:min([a.find(c) for c in wild if c in a], default=len(a))]
    pb = b[:min([b.find(c) for c in wild if c in b], default=len(b))]
    return (any(x in a for x in wild) and any(x in b for x in wild) and
            (pa.startswith(pb) or pb.startswith(pa)))


def canonical(s: Any, aliases: dict[str, str]) -> str:
    if not isinstance(s, str):
        fail("INVALID_FEATURE_OR_RESOURCE")
    key = s.upper().replace("-", "_")
    if not TOKEN.fullmatch(key):
        fail("INVALID_FEATURE_OR_RESOURCE")
    seen = set()
    while key in aliases:
        if key in seen:
            fail("ALIAS_CYCLE")
        seen.add(key)
        key = aliases[key]
    return key


def iso(s: Any) -> datetime:
    if not isinstance(s, str):
        fail("INVALID_LEASE_TIME")
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        fail("INVALID_LEASE_TIME")
    if t.tzinfo is None:
        fail("MISSING_LEASE_TIMEZONE")
    return t


def check(registry: dict[str, Any], candidate: dict[str, Any], actual_paths: list[str], official_head: str,
          now: datetime) -> dict[str, Any]:
    if registry.get("schema") != "P0D_EXCLUSIVE_CLAIMS_V1":
        fail("UNTRUSTED_REGISTRY_SCHEMA")
    if not SHA.fullmatch(official_head):
        fail("INVALID_OFFICIAL_HEAD")
    if now.tzinfo is None:
        fail("INVALID_NOW_TIMEZONE")
    raw_aliases = registry.get("aliases", {})
    if not isinstance(raw_aliases, dict):
        fail("INVALID_ALIAS_TABLE")
    aliases: dict[str, str] = {}
    for k, v in raw_aliases.items():
        ka = str(k).upper().replace("-", "_")
        va = str(v).upper().replace("-", "_")
        if not TOKEN.fullmatch(ka) or not TOKEN.fullmatch(va):
            fail("INVALID_ALIAS_TABLE")
        aliases[ka] = va
    claims = registry.get("claims")
    if not isinstance(claims, list):
        fail("INVALID_CLAIMS")
    active = []
    claim_ids = set()
    for c in claims:
        if not isinstance(c, dict):
            fail("INVALID_CLAIM_ROW")
        cid = c.get("claim_id")
        if not isinstance(cid, str) or not cid or cid in claim_ids:
            fail("DUPLICATE_CLAIM_ID")
        claim_ids.add(cid)
        state = c.get("state")
        if state not in BUSY and state not in {"RELEASED", "RC_INTEGRATED", "REVOKED"}:
            fail("INVALID_CLAIM_STATE")
        if state not in BUSY:
            continue
        if not isinstance(c.get("owner"), str) or not c["owner"]:
            fail("INVALID_CLAIM_OWNER")
        c = dict(c)
        c["feature_id"] = canonical(c.get("feature_id"), aliases)
        resources = c.get("resources")
        if not isinstance(resources, list) or not resources:
            fail("MISSING_CLAIM_RESOURCES")
        c["resources"] = {canonical(r, aliases) for r in resources}
        c["target_paths"] = valid_paths(c.get("target_paths"))
        c["expires_at"] = iso(c.get("expires_at"))
        active.append(c)
    for i, a in enumerate(active):
        for b in active[i+1:]:
            if (a["feature_id"] == b["feature_id"] or a["resources"] & b["resources"] or
                any(pat_overlap(p, q) for p in a["target_paths"] for q in b["target_paths"])):
                fail("REGISTRY_CONFLICT_ACTIVE_CLAIMS")
    if not isinstance(candidate, dict):
        fail("INVALID_CANDIDATE")
    for k in ("source_head", "base_rc"):
        if not isinstance(candidate.get(k), str) or not SHA.fullmatch(candidate[k]):
            fail("INVALID_CANDIDATE_SHA")
    if candidate["base_rc"] != official_head:
        fail("STALE_RC_BASE_RECHECK_REQUIRED")
    f = canonical(candidate.get("feature_id"), aliases)
    cr = candidate.get("resources")
    if not isinstance(cr, list) or not cr:
        fail("MISSING_CANDIDATE_RESOURCES")
    resources = {canonical(x, aliases) for x in cr}
    paths = valid_paths(actual_paths)
    claim_id = candidate.get("claim_id")
    owner = candidate.get("owner")
    matching = [c for c in active if c["claim_id"] == claim_id and c["feature_id"] == f and c["owner"] == owner]
    if len(matching) != 1:
        fail("CLAIM_NOT_GRANTED_OR_OWNER_MISMATCH")
    grant = matching[0]
    if grant["expires_at"] <= now.astimezone(timezone.utc):
        fail("STALE_CLAIM_REQUIRES_COORDINATED_HANDOFF")
    if not resources.issubset(grant["resources"]):
        fail("RESOURCE_SCOPE_EXCEEDS_GRANT")
    if any(not any(fnmatch.fnmatchcase(p, allowed) for allowed in grant["target_paths"]) for p in paths):
        fail("CHANGED_FILES_EXCEED_GRANT")
    return {"schema": "P0D_CLAIM_GATE_V1", "result": "CLAIM_SCOPE_PASS_NOT_RC_ADOPTION", "claim_id": claim_id,
            "feature_id": f, "owner": owner, "source_head": candidate["source_head"], "official_head": official_head,
            "changed_files": len(paths), "no_merge": True, "art_mobile_fun_verified": False}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for x in ("registry", "candidate", "changed-files", "official-head"):
        p.add_argument("--" + x, required=True)
    p.add_argument("--now", help="Test override, otherwise system UTC")
    a = p.parse_args()
    try:
        with open(a.registry, encoding="utf-8") as f:
            r = json.load(f)
        with open(a.candidate, encoding="utf-8") as f:
            c = json.load(f)
        with open(a.changed_files, encoding="utf-8") as f:
            files = json.load(f)
        ans = check(r, c, files, a.official_head, iso(a.now) if a.now else datetime.now(timezone.utc))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"schema": "P0D_CLAIM_GATE_V1", "result": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(ans, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
