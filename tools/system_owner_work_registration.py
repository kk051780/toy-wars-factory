#!/usr/bin/env python3
"""Host-neutral, single-attempt compare-and-swap work-ID registry candidate.

This source has NO GitHub/network client, NOT a trusted host/provider adapter,
not a work authorization grant, and MUST NOT dispatch a worker. Both callbacks
in apply_once() are caller-supplied: a passing test or reported CAS success
cannot authenticate those callbacks. A trusted original GitHub host, legal
existing coordinator owner, audit, and independent protected integration are
prerequisites to deployment.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta
import hashlib
import json
import re
from typing import Any, Callable

from system_owner_intake_dedup import (
    IDEA_ID, KINDS, PROJECT, REPOSITORY, SHA, calculate_work_id, request_fields,
)

REGISTRY_KEY = "work_registrations"
CONTROL_BRANCH = "twf-repair-coordinator"
CONTROL_PATH = "ops/REPAIR_COORDINATOR.json"
ALLOWED_STATUSES = frozenset(("OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"))
UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
MAX_ROWS = 512


class Rejected(ValueError):
    pass


def must(test: bool, reason: str) -> None:
    if not test:
        raise Rejected(reason)


def _is_sha(value: Any) -> bool:
    return type(value) is str and SHA.fullmatch(value) is not None


def _work_record(row: Any) -> tuple[str, str]:
    must(type(row) is dict and set(row) == {
        "project_id", "repository", "idea_id", "kind", "objective",
        "work_id", "status", "owner_id", "epoch", "created_from_main_sha",
    }, "bad registry row shape")
    must(type(row["project_id"]) is str and PROJECT.fullmatch(row["project_id"]) is not None,
         "bad registry project")
    must(type(row["repository"]) is str and REPOSITORY.fullmatch(row["repository"]) is not None,
         "bad registry repository")
    must(all(p not in (".", "..") for p in row["repository"].split("/")) and
         row["repository"] == row["repository"].casefold(),
         "unsafe or noncanonical registry repository")
    must(type(row["idea_id"]) is str and IDEA_ID.fullmatch(row["idea_id"]) is not None,
         "bad registry idea_id")
    must(type(row["kind"]) is str and row["kind"] in KINDS, "bad registry kind")
    must(type(row["owner_id"]) is str and UUID.fullmatch(row["owner_id"]) is not None,
         "bad registry owner")
    must(type(row["epoch"]) is int and row["epoch"] > 0, "bad registry epoch")
    must(type(row["status"]) is str and row["status"] in ALLOWED_STATUSES,
         "bad registry status")
    must(_is_sha(row["created_from_main_sha"]), "bad registry main")
    valid_id = calculate_work_id(row["project_id"], row["repository"],
                                 row["kind"], row["objective"])
    must(type(row["work_id"]) is str and row["work_id"] == valid_id,
         "forged or noncanonical work_id")
    # Owner idea IDs are only unique WITHIN project/repository, not globally.
    return valid_id, row["idea_id"]


def _registry(state: dict) -> list[dict]:
    registry = state.get(REGISTRY_KEY, {"schema": 1, "entries": []})
    must(type(registry) is dict and set(registry) == {"schema", "entries"} and
         type(registry["schema"]) is int and registry["schema"] == 1,
         "invalid registry schema")
    entries = registry["entries"]
    must(type(entries) is list and len(entries) <= MAX_ROWS, "invalid registry size")
    seen_ids, seen_ideas = set(), set()
    for row in entries:
        work_id, idea_id = _work_record(row)
        idea_key = (row["project_id"], row["repository"], idea_id)
        must(work_id not in seen_ids, "duplicate canonical work id")
        must(idea_key not in seen_ideas, "duplicate owner idea key")
        seen_ids.add(work_id)
        seen_ideas.add(idea_key)
    return entries


def _snapshot(snapshot: Any) -> tuple[dict, dict, list[dict]]:
    must(type(snapshot) is dict and set(snapshot) == {
        "repository", "coordination_branch", "ref_sha", "main_sha", "state"
    }, "invalid snapshot shape")
    must(type(snapshot["repository"]) is str and
         REPOSITORY.fullmatch(snapshot["repository"]) is not None and
         all(p not in (".", "..") for p in snapshot["repository"].split("/")) and
         snapshot["repository"] == snapshot["repository"].casefold(),
         "invalid or noncanonical snapshot repo")
    must(snapshot["coordination_branch"] == CONTROL_BRANCH, "wrong coordinator")
    must(_is_sha(snapshot["ref_sha"]), "invalid coordinator ref")
    must(_is_sha(snapshot["main_sha"]), "invalid main ref")
    state = snapshot["state"]
    must(type(state) is dict and type(state.get("schema")) is int and
         state["schema"] == 1 and
         type(state.get("epoch")) is int and state["epoch"] >= 1 and
         "holder" in state, "malformed coordinator state")
    return state, snapshot, _registry(state)


def _request(request: Any, repo: str, main_sha: str) -> str:
    must(type(request) is dict and set(request) == {
        "project_id", "repository", "kind", "objective", "idea_id",
        "owner_id", "epoch", "base_main_sha", "work_branch", "observed_at",
    }, "invalid request shape")
    must(type(request["project_id"]) is str and
         PROJECT.fullmatch(request["project_id"]) is not None, "bad project")
    must(request["repository"] == repo, "request repo != snapshot repo")
    must(request["base_main_sha"] == main_sha, "stale request main")
    must(type(request["owner_id"]) is str and
         UUID.fullmatch(request["owner_id"]) is not None, "invalid run ID")
    must(type(request["epoch"]) is int and request["epoch"] > 0,
         "invalid request epoch")
    must(type(request["observed_at"]) is str, "missing trusted host observed_at")
    must(type(request["work_branch"]) is str and
         request["work_branch"].startswith("controller/") and
         12 <= len(request["work_branch"]) <= 120 and
         ".." not in request["work_branch"] and
         all(ord(c) in range(33, 127) for c in request["work_branch"]),
         "unsafe work branch")
    # Reuse the exact normalized objective and idea identity validator from PR173.
    request_fields({k: request[k] for k in ("kind", "objective", "idea_id")})
    return calculate_work_id(request["project_id"], repo, request["kind"],
                             request["objective"])


def _utc_instant(value: Any) -> datetime:
    must(type(value) is str and len(value) <= 40, "bad timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Rejected("unparseable timestamp") from None
    must(parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0),
         "timestamp must be UTC aware")
    return parsed


def plan(snapshot: dict, request: dict) -> dict:
    """Build a non-authorizing CAS proposal from an untrusted caller snapshot.

    For a missing registry ID, only the live exclusive CONTROLLER owner may
    propose a change. No ownership is granted by a caller-produced owner UUID.
    The trust-root consumer must independently prove the original owner claim.
    """
    state, observation, entries = _snapshot(snapshot)
    work_id = _request(request, observation["repository"], observation["main_sha"])
    for row in entries:
        if (row["project_id"], row["repository"], row["idea_id"]) == (
            request["project_id"], request["repository"], request["idea_id"]
        ) and row["work_id"] != work_id:
            raise Rejected("same owner idea ID changed objective")
    for row in entries:
        if row["work_id"] == work_id:
            return {"decision": "JOIN_EXISTING_UNVERIFIED", "work_id": work_id,
                    "existing_status": row["status"], "existing_owner": row["owner_id"],
                    "expected_sha": observation["ref_sha"], "proposed_state": None,
                    "may_dispatch": False, "github_authenticated": False}
    holder = state["holder"]
    must(type(holder) is dict and holder.get("kind") == "CONTROLLER" and
         holder.get("origin") == "controller" and
         holder.get("owner_id") == request["owner_id"] and
         type(holder.get("epoch")) is int and
         holder["epoch"] == request["epoch"] == state["epoch"] and
         holder.get("task_id") is None and
         holder.get("work_branch") == request["work_branch"] and
         holder.get("base_main_sha") == observation["main_sha"],
         "foreign/mismatched coordinator holder")
    acquired = _utc_instant(holder.get("acquired_at"))
    expires = _utc_instant(holder.get("expires_at"))
    now = _utc_instant(request["observed_at"])
    must(acquired <= now < expires and timedelta(0) < expires - acquired <= timedelta(minutes=30),
         "not inside an unexpired exclusive lease")
    # Source time is caller-provided. Host must independently obtain and bind its clock.
    must(len(entries) < MAX_ROWS, "registry full")
    updated = copy.deepcopy(state)
    new_record = {key: request[key] for key in (
        "project_id", "repository", "idea_id", "kind", "objective", "owner_id", "epoch"
    )}
    new_record.update({"work_id": work_id, "status": "OPEN",
                       "created_from_main_sha": observation["main_sha"]})
    updated[REGISTRY_KEY] = {"schema": 1, "entries": copy.deepcopy(entries) + [new_record]}
    # Updating coordinator must preserve unrelated state exactly.
    must(set(updated) - set(state) == ({REGISTRY_KEY} if REGISTRY_KEY not in state else set()),
         "unexpected coordinator changes")
    return {"decision": "CAS_PROPOSAL_NOT_AUTHORIZED", "work_id": work_id,
            "existing_status": None, "existing_owner": None,
            "expected_sha": observation["ref_sha"], "proposed_state": updated,
            "may_dispatch": False, "github_authenticated": False}


def intake_projection(snapshot: dict) -> list[dict]:
    """Project registry rows to PR173's v2 read-only owner intake shape.

    This is caller-supplied data, NOT authenticated; consumers must not dispatch.
    """
    _, _, entries = _snapshot(snapshot)
    return [{key: row[key] for key in (
        "project_id", "repository", "idea_id", "kind", "objective", "work_id", "status"
    )} for row in entries]


def apply_once(snapshot: dict, request: dict, *, cas: Callable,
               readback: Callable, read_main_ref: Callable,
               fresh_coordinator_snapshot: Callable | None = None,
               trusted_clock: Callable | None = None) -> dict:
    """Single untrusted-callback CAS attempt with fail-closed pre-write fencing.

    All callbacks are supplied by a CALLER, not authenticated by this library.
    fresh_coordinator_snapshot(repo, CONTROL_BRANCH, CONTROL_PATH) must perform
    a new original-source ref/content read, not serve stale caller request data.
    trusted_clock() must obtain a new original-host UTC-aware timestamp.

    These checks only reduce the time-of-check/time-of-use gap. They do NOT
    prove GitHub write-time lease validity: the trustworthy CAS adapter must
    independently enforce the exclusive owner/epoch/expiry at actual write.
    There is no automatic retry, provider identity attestation, work dispatch,
    merge, external inference or Roblox execution in this module.
    """
    outcome = plan(snapshot, request)
    if outcome["decision"] != "CAS_PROPOSAL_NOT_AUTHORIZED":
        return {"status": outcome["decision"], "work_id": outcome["work_id"],
                "cas_attempted": False, "may_dispatch": False,
                "github_authenticated": False}

    old = outcome["expected_sha"]
    new_state = outcome["proposed_state"]
    repo = snapshot["repository"]

    def wait(status: str) -> dict:
        return {"status": status, "work_id": outcome["work_id"],
                "cas_attempted": False, "may_dispatch": False,
                "github_authenticated": False}

    # Missing callbacks are a hard hold. Never fall back to request.observed_at.
    if not callable(fresh_coordinator_snapshot) or not callable(trusted_clock):
        return wait("WAIT_PRECAS_CALLBACK_UNAVAILABLE")

    try:
        original_main = read_main_ref(repo)
    except Exception:
        original_main = None
    if original_main != snapshot["main_sha"]:
        return wait("WAIT_MAIN_DRIFT_UNCONFIRMED")

    # The immutable expected SHA does not change merely because a lease expires.
    # Require two fresh original-source coordinator reads and an exact match
    # to the proposed predecessor, including all existing state and holder.
    try:
        first = fresh_coordinator_snapshot(repo, CONTROL_BRANCH, CONTROL_PATH)
        second = fresh_coordinator_snapshot(repo, CONTROL_BRANCH, CONTROL_PATH)
        _snapshot(first)
        _snapshot(second)
        unchanged = (type(first) is dict and type(second) is dict and
                     first == second == snapshot)
    except Exception:
        unchanged = False
    if not unchanged:
        return wait("WAIT_COORDINATOR_DRIFT_UNCONFIRMED")

    # Main may move during the coordinator reads; reject before time check.
    try:
        last_main = read_main_ref(repo)
    except Exception:
        last_main = None
    if last_main != snapshot["main_sha"]:
        return wait("WAIT_MAIN_DRIFT_UNCONFIRMED")

    # Last injected host callback before CAS: independent UTC clock. The
    # caller's earlier observed_at may be stale and MUST NOT serve as now.
    try:
        actual_now = _utc_instant(trusted_clock())
        previously_observed = _utc_instant(request["observed_at"])
        holder = snapshot["state"]["holder"]
        acquired = _utc_instant(holder["acquired_at"])
        expires = _utc_instant(holder["expires_at"])
        in_lease = (acquired <= previously_observed <= actual_now < expires and
                    timedelta(0) < expires - acquired <= timedelta(minutes=30))
    except Exception:
        return wait("WAIT_PRECAS_CLOCK_UNCONFIRMED")
    if not in_lease:
        return wait("WAIT_PRECAS_CLOCK_UNCONFIRMED")
    # A five-second headroom limits ordinary transport overrun; it is NOT a
    # remotely enforced deadline. Original write adapter remains the trust root.
    if expires - actual_now <= timedelta(seconds=5):
        return wait("WAIT_PRECAS_EXPIRING_UNCONFIRMED")

    try:
        new_sha = cas(repo, CONTROL_BRANCH, CONTROL_PATH,
                      old, copy.deepcopy(new_state))
    except Exception:
        # Ambiguous ACK: no retry. Fresh original read by the owner is required.
        return {"status": "WAIT_CAS_UNCONFIRMED", "work_id": outcome["work_id"],
                "cas_attempted": True, "may_dispatch": False,
                "github_authenticated": False}
    if new_sha is None or not _is_sha(new_sha) or new_sha == old:
        return {"status": "WAIT_CAS_CONFLICT_OR_INVALID_ACK",
                "work_id": outcome["work_id"], "cas_attempted": True,
                "may_dispatch": False, "github_authenticated": False}

    try:
        observed = readback(repo, CONTROL_BRANCH, CONTROL_PATH)
        second = readback(repo, CONTROL_BRANCH, CONTROL_PATH)
        state, details, _ = _snapshot(observed)
        state2, details2, _ = _snapshot(second)
        second_main = read_main_ref(repo)
        valid = (second_main == snapshot["main_sha"] and
                 details["ref_sha"] == details2["ref_sha"] == new_sha and
                 details["main_sha"] == details2["main_sha"] == snapshot["main_sha"] and
                 details["repository"] == details2["repository"] == repo and
                 state == state2 == new_state)
    except Exception:
        valid = False
    return {"status": ("CALLBACK_CAS_CONFIRMED_NOT_GITHUB_AUTHENTICATED" if valid
                       else "WAIT_CAS_UNCONFIRMED"), "work_id": outcome["work_id"],
            "cas_attempted": True, "may_dispatch": False,
            "github_authenticated": False}
