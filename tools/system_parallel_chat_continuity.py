#!/usr/bin/env python3
"""Read-only continuity packets when a ChatGPT chat reaches its context limit.

A context limit is NOT a service terminal signal. These proposals never grant
GitHub write, release, reviewer, dispatch, or takeover authority. A successor
must fetch current immutable GitHub and authentic service evidence separately.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
import unicodedata

from system_parallel_shadow_leases import inspect, instant, uuid
from system_parallel_scope_admission import normalized_path

SHA = re.compile(r"[0-9a-f]{40}\Z")
TASK = re.compile(r"[0-9a-f]{32}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
WORK = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{5,127}\Z")
BRANCH = re.compile(r"(?:controller|auto)/[a-z0-9][a-z0-9._/-]{4,120}\Z")
PROJECT = re.compile(r"[a-z0-9][a-z0-9_-]{2,63}\Z")
REPOSITORY = re.compile(r"[a-z0-9_.-]+/[a-z0-9_.-]+\Z")
STAGES = frozenset(("PLANNED", "EDITING", "DRAFT_PR", "CI_WAIT",
                    "REVIEW_WAIT", "BLOCKED", "DONE"))
ACTIONS = frozenset(("INSPECT", "EDIT", "TEST", "CHECK_CI", "REQUEST_REVIEW",
                     "RECOVER_LEASE", "REBASE", "NONE"))
REQ_KEYS = frozenset(("project_id", "work_id", "branch", "source_head", "seq",
                      "stage", "next_action", "summary", "changed_paths",
                      "pr_number", "ci_run_id", "observed_at"))
PACKET_KEYS = REQ_KEYS - {"observed_at", "seq"} | {
    "schema", "repository", "main_sha", "coord_ref_sha", "lease_epoch",
    "owner_id", "task_id", "origin", "sequence", "acquired_at", "expires_at",
    "created_at", "digest",
}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _summary(value):
    require(type(value) is str and 1 <= len(value) <= 200 and value.strip() == value,
            "summary length")
    require(not any(unicodedata.category(c).startswith("C") for c in value),
            "control in summary")
    require(not re.search(r"(?i)(?:bearer|password|github_pat_|ghp_|gho_|sk-|api[_-]?key|secret)", value),
            "credential-shaped summary")
    return value


def _paths(value):
    require(type(value) is list and len(value) <= 80, "path list")
    paths = [normalized_path(v) for v in value]
    require(len(paths) == len(set(paths)), "duplicate paths")
    return paths


def _id(value):
    require(type(value) is str and SHA.fullmatch(value) is not None, "invalid SHA")


def _positive_or_null(value):
    require(value is None or (type(value) is int and 0 < value <= 999999999999),
            "invalid positive integer")


def verify_packet(packet):
    require(type(packet) is dict and set(packet) == PACKET_KEYS, "packet schema")
    require(type(packet["schema"]) is int and packet["schema"] == 1, "schema")
    require(type(packet["digest"]) is str and HASH.fullmatch(packet["digest"]),
            "digest shape")
    require(_digest({k:v for k,v in packet.items() if k != "digest"}) == packet["digest"],
            "packet digest mismatch")
    for k in ("main_sha", "source_head", "coord_ref_sha"):
        _id(packet[k])
    require(type(packet["project_id"]) is str and PROJECT.fullmatch(packet["project_id"]),
            "project")
    require(type(packet["repository"]) is str and REPOSITORY.fullmatch(packet["repository"]),
            "repository")
    require(type(packet["work_id"]) is str and WORK.fullmatch(packet["work_id"]),
            "work")
    require(type(packet["branch"]) is str and BRANCH.fullmatch(packet["branch"]) and
            all(p not in (".", "..", "") for p in packet["branch"].split("/")),
            "branch")
    uuid(packet["owner_id"])
    require(type(packet["origin"]) is str and packet["origin"] in ("MANUAL", "REGISTERED", "SHADOW"),
            "origin")
    if packet["origin"] == "REGISTERED":
        require(type(packet["task_id"]) is str and
                TASK.fullmatch(packet["task_id"]) is not None,
                "registered task ID")
    else:
        require(packet["task_id"] is None, "manual task spoof")
    require(type(packet["lease_epoch"]) is int and packet["lease_epoch"] > 0,
            "epoch")
    require(type(packet["sequence"]) is int and 0 < packet["sequence"] <= 1000000,
            "sequence")
    require(type(packet["stage"]) is str and packet["stage"] in STAGES, "stage")
    require(type(packet["next_action"]) is str and packet["next_action"] in ACTIONS,
            "next action")
    _summary(packet["summary"])
    _paths(packet["changed_paths"])
    _positive_or_null(packet["pr_number"])
    _positive_or_null(packet["ci_run_id"])
    require(packet["stage"] != "DRAFT_PR" or packet["pr_number"] is not None,
            "draft without PR number")
    a, t, b = instant(packet["acquired_at"]), instant(packet["created_at"]), instant(packet["expires_at"])
    require(a <= t < b and 0 < (b-a).total_seconds() <= 1800, "checkpoint outside lease")
    return packet


def draft_checkpoint(snapshot, request, previous=None):
    """Prepare a checksum-bound packet; caller must separately persist to GitHub."""
    def out(status, packet=None):
        return {"status": status, "packet": packet, "may_write": False,
                "may_recover": False, "github_authenticated": False,
                "persisted_to_github": False}
    try:
        state, rows = inspect(snapshot)
        require(type(request) is dict and set(request) == REQ_KEYS, "request shape")
        require(type(request["project_id"]) is str and PROJECT.fullmatch(request["project_id"]),
                "project")
        require(type(request["work_id"]) is str and WORK.fullmatch(request["work_id"]),
                "work")
        require(type(request["branch"]) is str and BRANCH.fullmatch(request["branch"]),
                "branch")
        _id(request["source_head"])
        t = instant(request["observed_at"])
        require(type(request["seq"]) is int and 0 < request["seq"] <= 1000000,
                "sequence")
        require(type(request["stage"]) is str and request["stage"] in STAGES,
                "stage")
        require(type(request["next_action"]) is str and request["next_action"] in ACTIONS,
                "next")
        _summary(request["summary"])
        _paths(request["changed_paths"])
        _positive_or_null(request["pr_number"])
        _positive_or_null(request["ci_run_id"])
        owner = state["holder"]
        if owner is not None:
            require(type(owner) is dict and owner.get("kind") in
                    ("CONTROLLER", "WORKER", "META", "REVIEWER"), "owner kind")
            require(owner.get("work_branch") == request["branch"] and
                    owner.get("base_main_sha") == snapshot["main_sha"] and
                    owner.get("epoch") == state["epoch"], "owner mismatch")
            origin = "MANUAL" if owner["kind"] == "CONTROLLER" else "REGISTERED"
            task_id = None if origin == "MANUAL" else owner.get("task_id")
            if origin == "REGISTERED":
                require(type(state.get("authorized_tasks")) is dict and
                        state["authorized_tasks"].get(owner["kind"]) == task_id,
                        "registered task authority missing")
        else:
            selected = [e for e in rows
                        if e["scope"]["work_id"] == request["work_id"] and
                           e["scope"]["branch"] == request["branch"]]
            require(len(selected) == 1, "no unique shadow lease")
            e = selected[0]
            owner = {"owner_id": e["owner_id"], "task_id": e["run_id"],
                     "acquired_at": e["acquired_at"], "expires_at": e["expires_at"],
                     "epoch": e["lease_epoch"]}
            task_id = None
            origin = "SHADOW"
        uuid(owner["owner_id"])
        if origin == "REGISTERED":
            require(type(task_id) is str and TASK.fullmatch(task_id),
                    "task ID must be 32 hex")
        packet = {
            "schema":1, "project_id":request["project_id"], "repository":snapshot["repository"],
            "work_id":request["work_id"], "branch":request["branch"],
            "source_head":request["source_head"], "main_sha":snapshot["main_sha"],
            "coord_ref_sha":snapshot["ref_sha"], "lease_epoch":owner["epoch"],
            "owner_id":owner["owner_id"], "task_id":task_id, "origin":origin,
            "sequence":request["seq"], "stage":request["stage"],
            "next_action":request["next_action"], "summary":request["summary"],
            "changed_paths":copy.deepcopy(request["changed_paths"]),
            "pr_number":request["pr_number"], "ci_run_id":request["ci_run_id"],
            "created_at":request["observed_at"],
            "acquired_at":owner["acquired_at"], "expires_at":owner["expires_at"],
        }
        packet["digest"] = _digest(packet)
        verify_packet(packet)
        if previous is not None:
            verify_packet(previous)
            require(packet["sequence"] == previous["sequence"] + 1, "sequence rollback")
            for key in ("repository", "project_id", "work_id", "branch",
                        "lease_epoch", "owner_id", "task_id", "main_sha"):
                require(packet[key] == previous[key], "predecessor drift")
            require(t >= instant(previous["created_at"]), "time reversal")
        return out("CHECKPOINT_DRAFT_UNTRUSTED", packet)
    except (KeyError, TypeError, ValueError):
        return out("WAIT_INVALID_CHECKPOINT")


def successor_preflight(packet, observation, terminal=None):
    """Read-only new-chat routing; never treats context full as owner termination."""
    def out(status):
        return {"status": status, "may_write": False, "may_recover": False,
                "may_release": False, "may_dispatch": False,
                "provider_authenticated": False, "fresh_lease_required": True}
    try:
        verify_packet(packet)
        require(type(observation) is dict and set(observation) ==
                {"snapshot", "branch_head", "pr_head", "observed_at"},
                "observation shape")
        state, rows = inspect(observation["snapshot"])
        now = instant(observation["observed_at"])
        require(observation["snapshot"]["repository"] == packet["repository"] and
                observation["snapshot"]["main_sha"] == packet["main_sha"],
                "repository or main changed")
        _id(observation["branch_head"])
        if packet["pr_number"] is None:
            require(observation["pr_head"] is None, "unexpected PR")
        else:
            _id(observation["pr_head"])
        if observation["branch_head"] != packet["source_head"] or (
                packet["pr_number"] is not None and
                observation["pr_head"] != packet["source_head"]):
            return out("WAIT_EXACT_HEAD_DRIFT")
        holder = state["holder"]
        if holder is not None:
            if holder.get("owner_id") != packet["owner_id"] or (
                    holder.get("epoch") != packet["lease_epoch"]):
                return out("WAIT_OTHER_OWNER_OR_EPOCH")
            if now < instant(holder["expires_at"]):
                return out("JOIN_ACTIVE_OWNER_READ_ONLY")
            if packet["origin"] == "MANUAL":
                return out("WAIT_MANUAL_EXACT_EPOCH_OWNER_REVOCATION")
            if terminal is None:
                return out("WAIT_AUTHENTIC_SERVICE_TERMINAL")
            require(type(terminal) is dict and set(terminal) ==
                    {"task_id", "run_id", "started_at", "completed_at", "recorded_status"},
                    "terminal shape")
            require(terminal["task_id"] == packet["task_id"] and
                    terminal["run_id"] == packet["owner_id"] and
                    type(terminal["recorded_status"]) is str and
                    terminal["recorded_status"] in ("completed", "failed", "no_update"),
                    "foreign or active run")
            require(instant(terminal["started_at"]) <= instant(packet["acquired_at"]) <=
                    instant(terminal["completed_at"]) <= now, "bad terminal chronology")
            return out("TERMINAL_CANDIDATE_REQUIRES_ORIGINAL_PROVIDER_PROOF")
        completed = state.get("last_completed")
        if (type(completed) is dict and
                completed.get("owner_id") == packet["owner_id"] and
                completed.get("epoch") == packet["lease_epoch"] and
                completed.get("released_at") and
                packet["coord_ref_sha"] != observation["snapshot"]["ref_sha"] and
                instant(packet["acquired_at"]) <= instant(completed["released_at"]) <= now):
            return out("HANDOFF_READY_ONLY_AFTER_FRESH_LEASE")
        if packet["origin"] == "REGISTERED" and rows:
            return out("WAIT_SHADOW_LEASE_UNRECONCILED")
        return out("WAIT_ORIGINAL_RELEASE_PROOF")
    except (KeyError, TypeError, ValueError):
        return out("WAIT_UNTRUSTED_EVIDENCE")


def compact_handoff(packet):
    """Safe human note for a PR/Issue comment, not an authenticated receipt."""
    verify_packet(packet)
    fields = ("work_id", "branch", "source_head", "main_sha", "owner_id",
              "lease_epoch", "pr_number", "ci_run_id", "stage", "next_action",
              "sequence", "digest")
    return ("TOY WARS P0 CONTINUITY / read-only handoff.\n"
            "Read Issues 123/182, original GitHub coordinator, PR and CI.\n"
            "Never inherit/release an old lock on chat silence or expiry.\n"
            + json.dumps({key:packet[key] for key in fields}, sort_keys=True))
