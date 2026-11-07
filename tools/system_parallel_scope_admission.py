#!/usr/bin/env python3
"""Advisory, fail-closed work-scope comparison for the Issue #123 parallel pilot.

This module only compares untrusted *proposals*. It does NOT acquire a lease,
authenticate a task, grant GitHub writes, dispatch a worker, or allow merging.
The existing exclusive coordinator remains authoritative until a reviewed v2
adapter can atomically admit scoped leases against original provider state.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

SHA = re.compile(r"[0-9a-f]{40}\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{5,127}\Z")
PROJECT = re.compile(r"[a-z0-9][a-z0-9_-]{2,63}\Z")
REPO = re.compile(r"[a-z0-9_.-]+/[a-z0-9_.-]+\Z")
BRANCH = re.compile(r"(?:controller|auto)/[a-z0-9][a-z0-9._/-]{4,120}\Z")
RESOURCE = re.compile(r"[a-z0-9][a-z0-9:._/-]{0,79}\Z")
FIELDS = frozenset((
    "project_id", "repository", "work_id", "branch", "base_sha",
    "write_paths", "read_paths", "generated_paths", "shared_resources", "status",
))
# A design/source dependency collision need not have an identical file path.
# These are intentionally conservative for the first two-writer pilot.
INTERFACE_PATHS = frozenset((
    "src/toywarsbalance.lua", "src/toywarsserver.server.lua",
    "src/toywarshud.client.lua", "config/characters.json",
    "tools/system_character_pipeline.py",
))
EXCLUSIVE_PREFIXES = (
    ".github", "ops/repair_coordinator.json", "agents.md",
    "project_state.json", "config/quality_policy.json",
    "config/autonomous_repair.json", "tools/repair_control.py",
    "tools/repair_integration.py",
)


class InvalidScope(ValueError):
    pass


def _check(ok: bool, message: str) -> None:
    if not ok:
        raise InvalidScope(message)


def normalized_path(path: Any) -> str:
    """Conservative repository path normalization, without FS access.

    Avoid ambiguous traversal/escapes, Windows case aliases, Unicode confusables,
    broad glob patterns, and git metadata. Keep prefix collisions detectable.
    """
    _check(type(path) is str and 1 <= len(path) <= 240, "invalid path")
    _check(unicodedata.normalize("NFKC", path) == path, "noncanonical Unicode path")
    _check(not any(unicodedata.category(c).startswith("C") for c in path),
           "control character in path")
    _check(not path.startswith(("/", "./")) and not path.endswith("/"),
           "noncanonical path boundary")
    _check("\\" not in path and "%" not in path and ":" not in path,
           "path escape or drive alias")
    _check(not any(c in path for c in "*?[]{}~"), "glob or alias path")
    parts = path.split("/")
    _check(all(x not in ("", ".", "..") for x in parts), "traversal or empty path")
    _check(all(x.strip() == x and x[-1] not in (".", " ") for x in parts),
           "Windows path alias")
    _check(".git" not in [x.casefold() for x in parts], "git control path")
    folded = path.casefold()
    _check(len(folded) <= 240, "oversized folded path")
    return folded


def _paths(value: Any, name: str) -> frozenset[str]:
    _check(type(value) is list and len(value) <= 128, "invalid " + name)
    items = [normalized_path(p) for p in value]
    _check(len(set(items)) == len(items), "duplicate normalized " + name)
    return frozenset(items)


def _resources(value: Any) -> frozenset[str]:
    _check(type(value) is list and len(value) <= 64, "invalid shared resources")
    _check(all(type(s) is str and RESOURCE.fullmatch(s) for s in value),
           "invalid shared resource")
    _check(len(value) == len(set(value)), "duplicate resource")
    return frozenset(value)


def _scope(value: Any) -> dict:
    _check(type(value) is dict and set(value) == FIELDS, "invalid scope schema")
    _check(type(value["project_id"]) is str and
           PROJECT.fullmatch(value["project_id"]) is not None, "project id")
    _check(type(value["repository"]) is str and
           REPO.fullmatch(value["repository"]) is not None and
           all(segment not in (".", "..") for segment in value["repository"].split("/")),
           "repository id")
    _check(type(value["work_id"]) is str and
           ID.fullmatch(value["work_id"]) is not None, "work id")
    _check(type(value["branch"]) is str and
           BRANCH.fullmatch(value["branch"]) is not None and
           all(segment not in (".", "..") for segment in value["branch"].split("/")),
           "branch name")
    _check(type(value["base_sha"]) is str and
           SHA.fullmatch(value["base_sha"]) is not None, "base SHA")
    _check(value["status"] in ("ACTIVE", "CLOSED") and
           type(value["status"]) is str, "scope status")
    writes = _paths(value["write_paths"], "writes")
    reads = _paths(value["read_paths"], "reads")
    generated = _paths(value["generated_paths"], "generated")
    resources = _resources(value["shared_resources"])
    _check(len(writes) > 0, "empty write set")
    _check(generated <= writes, "generated file missing from full write set")
    _check(writes.isdisjoint(reads), "same file marked read and write")
    inferred = set(resources)
    if INTERFACE_PATHS & writes:
        inferred.add("toy-game-shared-interface")
    return {
        "project": value["project_id"], "repo": value["repository"],
        "id": value["work_id"], "branch": value["branch"],
        "base": value["base_sha"], "status": value["status"],
        "write": writes, "read": reads, "generated": generated,
        "resources": frozenset(inferred),
        "exclusive": any(_overlap(path, item)
                         for path in writes for item in EXCLUSIVE_PREFIXES),
    }


def _overlap(first: str, second: str) -> bool:
    return (first == second or first.startswith(second + "/") or
            second.startswith(first + "/"))


def _path_clash(a: frozenset[str], b: frozenset[str]) -> bool:
    return any(_overlap(left, right) for left in a for right in b)


def compare_claims(active: Any, proposal: Any) -> dict:
    """Return a non-authorizing recommendation for <=2 candidate writers.

    All input is untrusted. Even PROPOSE_DISJOINT cannot grant a real write:
    an independently authenticated service identity, original GitHub state,
    host-enforced CAS and a reviewed integration path are still required.
    """
    def result(decision: str, reason: str = "") -> dict:
        return {
            "decision": decision, "reason": reason,
            "may_write": False, "may_dispatch": False,
            "github_authenticated": False, "real_parallel_verified": False,
        }

    try:
        _check(type(active) is list and len(active) <= 2, "active set capacity")
        new = _scope(proposal)
        _check(new["status"] == "ACTIVE", "new claim must be active")
        seen = set()
        rows = []
        for value in active:
            row = _scope(value)
            _check(row["id"] not in seen, "duplicate active work IDs")
            seen.add(row["id"])
            rows.append(row)
        for row in rows:
            if (new["project"], new["repo"]) != (row["project"], row["repo"]):
                return result("WAIT_FOREIGN_PROJECT", row["id"])
            if new["id"] == row["id"]:
                return result("JOIN_EXISTING" if new["branch"] == row["branch"]
                              else "WAIT_WORK_ID_DRIFT", row["id"])
            if new["branch"] == row["branch"]:
                return result("WAIT_BRANCH_COLLISION", row["id"])
        rows = [row for row in rows if row["status"] == "ACTIVE"]
        if len(rows) >= 2:
            return result("WAIT_CAPACITY", "two existing writers")
        for row in rows:
            if new["base"] != row["base"]:
                return result("WAIT_BASE_DRIFT", row["id"])
            if new["exclusive"] or row["exclusive"]:
                return result("WAIT_EXCLUSIVE_SCOPE", row["id"])
            if _path_clash(new["write"], row["write"]):
                return result("WAIT_WRITE_COLLISION", row["id"])
            if (_path_clash(new["write"], row["read"]) or
                    _path_clash(new["read"], row["write"])):
                return result("WAIT_READ_WRITE_COLLISION", row["id"])
            if new["resources"] & row["resources"]:
                return result("WAIT_SEMANTIC_COLLISION", row["id"])
        return result("PROPOSE_DISJOINT", "advisory only; trusted CAS not present")
    except (InvalidScope, TypeError, KeyError, ValueError) as error:
        return result("WAIT_INVALID_SCOPE", str(error)[:120])
