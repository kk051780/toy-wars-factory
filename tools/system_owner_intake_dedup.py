#!/usr/bin/env python3
"""Pure, non-authorizing owner-idea duplicate intake proposal.

This code cannot attest GitHub, user identity or provider runs, does not perform
shared coordination CAS, and must NEVER be used as an admission/write gate.
A later trusted host has to fetch original records, validate work scope, and
atomically register a work ID before enabling any writer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

SHA = re.compile(r"[a-f0-9]{40}\Z")
PROJECT = re.compile(r"[a-z0-9][a-z0-9_-]{2,63}\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
IDEA_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:\-]{0,99}\Z")
KINDS = frozenset(("gameplay", "system", "qa", "design", "asset"))
STATUSES = frozenset(("OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"))
MAX_BYTES = 128 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def objective_key(value):
    require(type(value) is str, "objective type")
    require(8 <= len(value) <= 500, "objective length")
    # Bidi overrides, zero-width format controls, surrogates and invisible
    # categorical controls can disguise a duplicate; reject rather than strip.
    require(not any(unicodedata.category(c).startswith("C") for c in value),
            "unsafe Unicode control")
    norm = unicodedata.normalize("NFKC", value).casefold()
    key = " ".join(norm.split())
    require(8 <= len(key) <= 500, "normalized objective length")
    require(any(c.isalnum() for c in key), "objective without content")
    return key


def request_fields(value, *, record=False, project_id=None, repository=None):
    require(type(value) is dict, "invalid work record")
    required = {"idea_id", "kind", "objective"}
    if record:
        # Do not silently import records from another game or repository.
        # Scope is asserted by the caller; this function does not authenticate it.
        required |= {"work_id", "status", "project_id", "repository"}
    require(set(value) == required, "unknown or missing work record field")
    require(type(value["idea_id"]) is str and IDEA_ID.fullmatch(value["idea_id"]),
            "invalid idea ID")
    require(type(value["kind"]) is str and value["kind"] in KINDS,
            "invalid work kind")
    normalized = objective_key(value["objective"])
    if record:
        require(type(value["project_id"]) is str and value["project_id"] == project_id,
                "foreign or missing record project_id")
        require(type(value["repository"]) is str and value["repository"] == repository,
                "foreign or missing record repository")
        require(type(value["status"]) is str and value["status"] in STATUSES,
                "invalid work status")
    return normalized


def calculate_work_id(project_id, repository, kind, objective):
    normalized = objective_key(objective)
    # GitHub repository names are case-insensitive; canonicalize before hashing.
    # The trusted host must still authenticate the actual repository identity.
    stable = json.dumps([project_id, repository.casefold(), kind, normalized],
                        ensure_ascii=False, separators=(",", ":"))
    return "work-" + hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]


def classify(snapshot):
    require(type(snapshot) is dict and set(snapshot) == {
        "schema", "project_id", "repository", "main_sha", "collection_complete",
        "incoming", "records"}, "invalid intake envelope")
    require(type(snapshot["schema"]) is int and snapshot["schema"] == 2,
            "wrong schema")
    project, repo = snapshot["project_id"], snapshot["repository"]
    require(type(project) is str and PROJECT.fullmatch(project), "invalid project")
    require(type(repo) is str and REPOSITORY.fullmatch(repo) and
            all(part not in (".", "..") for part in repo.split("/")) and
            repo == repo.casefold(),
            "invalid repository")
    require(type(snapshot["main_sha"]) is str and SHA.fullmatch(snapshot["main_sha"]),
            "invalid main SHA")
    require(snapshot["collection_complete"] is True, "incomplete work inventory")
    incoming = snapshot["incoming"]
    norm = request_fields(incoming)
    require(type(snapshot["records"]) is list and len(snapshot["records"]) <= 1000,
            "invalid or too many work records")
    wanted_id = calculate_work_id(project, repo, incoming["kind"], incoming["objective"])
    idea_seen = {}
    work_seen = set()
    exact = None
    for item in snapshot["records"]:
        key = request_fields(item, record=True, project_id=project,
                             repository=repo)
        canonical = calculate_work_id(project, repo, item["kind"], item["objective"])
        require(item["work_id"] == canonical, "record work ID not canonical")
        require(canonical not in work_seen, "duplicate canonical work record")
        work_seen.add(canonical)
        idea_id = item["idea_id"]
        signature = (item["kind"], key)
        require(idea_id not in idea_seen or idea_seen[idea_id] == signature,
                "conflicting historic owner idea identity")
        idea_seen[idea_id] = signature
        if canonical == wanted_id:
            exact = item
    incoming_signature = (incoming["kind"], norm)
    if incoming["idea_id"] in idea_seen and idea_seen[incoming["idea_id"]] != incoming_signature:
        decision = "WAIT_OWNER_ID_DRIFT"
        existing_id = None
        status = None
    elif exact is not None:
        decision = "JOIN_EXISTING_ADVISORY"
        existing_id = exact["work_id"]
        status = exact["status"]
    else:
        decision = "NEW_ID_CANDIDATE_ONLY"
        existing_id = None
        status = None
    return {
        "schema": 2,
        "decision": decision,
        "project_id": project,
        "repository": repo,
        "proposed_work_id": wanted_id,
        "existing_work_id": existing_id,
        "existing_status": status,
        "checked_records": len(snapshot["records"]),
        "github_authenticated": False,
        "provider_run_authenticated": False,
        "may_claim": False,
        "may_write": False,
        "may_dispatch": False,
        "may_merge": False,
        "cas_performed": False,
        "warning": "Caller-supplied, non-atomic snapshot; paraphrases and semantic duplicates remain unverified. A trusted original GitHub read + atomic coordinator CAS are required before work admission."
    }


def strict_json(data):
    def no_dup(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate JSON key")
            obj[key] = value
        return obj

    def no_const(_):
        raise ValueError("nonfinite JSON literal")

    return json.loads(data, object_pairs_hook=no_dup, parse_constant=no_const)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        raw = Path(args.input).read_bytes()
        require(0 < len(raw) <= MAX_BYTES, "bad input size")
        result = classify(strict_json(raw.decode("utf-8")))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        # This is an offline tool. Never output supplied objective or content.
        print(json.dumps({"decision": "WAIT_INVALID_INPUT", "may_write": False,
                          "reason": str(exc)[:110]}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if result["decision"] == "WAIT_OWNER_ID_DRIFT" else 0


if __name__ == "__main__":
    sys.exit(main())
