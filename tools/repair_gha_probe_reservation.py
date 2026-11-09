"""PR210 protected candidate: OWNER manual GitHub Actions probe reservation.

Pure, non-authorizing state proposal. The same coordinator key
pending_source_action is used as PR203; no second lock namespace.
No GitHub client, token, CAS, source write, reconciliation or grant is here.
"""
from copy import deepcopy
import re

from repair_control import (canonical_id, instant, validate,
                            scoped_lease_migration_block)

REPOSITORY = "kk051780/toy-wars-factory"
WORK = "P0_ISSUE57_PR163_OWNER_GHA_BRANCH_ONLY_PROBE"
SNAPSHOT_KEYS = {"repository", "coordinator_ref", "main_head", "state"}
REQUEST_KEYS = {"operation_id", "owner_id", "owner_epoch", "run_id",
                "run_attempt", "mode"}
SHA = re.compile(r"[0-9a-f]{40}\Z")


def reply(action, **extra):
    return {"action": action, "may_write": False, "may_merge": False,
            "may_dispatch": False, "may_release": False,
            "provider_authenticated": False, "real_parallel": False, **extra}


def propose_branch_reservation(snapshot, request, now):
    """Propose one atomic coordinator CAS write; never perform it."""
    try:
        if (type(snapshot) is not dict or set(snapshot) != SNAPSHOT_KEYS or
                type(request) is not dict or set(request) != REQUEST_KEYS or
                snapshot["repository"] != REPOSITORY or
                type(snapshot["coordinator_ref"]) is not str or
                not SHA.fullmatch(snapshot["coordinator_ref"]) or
                type(snapshot["main_head"]) is not str or
                not SHA.fullmatch(snapshot["main_head"])):
            raise ValueError("invalid live binding snapshot")
        canonical_id(request["operation_id"])
        canonical_id(request["owner_id"])
        run, attempt = request["run_id"], request["run_attempt"]
        if (type(run) is not int or run <= 0 or run > 9223372036854775807 or
                type(attempt) is not int or attempt != 1 or
                type(request["owner_epoch"]) is not int or
                request["mode"] != "BRANCH_ONLY"):
            raise ValueError("wrong strictly manual probe identity")
        state = validate(snapshot["state"])
        if scoped_lease_migration_block(state):
            return reply("WAIT_PENDING_ACTION_OR_MIGRATION")
        when = instant(now)
        holder = state.get("holder")
        branch = f"controller/gha-write-probe-{run}-a{attempt}"
        if (type(holder) is not dict or holder.get("kind") != "CONTROLLER" or
                holder.get("owner_id") != request["owner_id"] or
                holder.get("epoch") != request["owner_epoch"] or
                holder.get("task_id") is not None or
                holder.get("work_branch") != branch or
                holder.get("base_main_sha") != snapshot["main_head"] or
                when < instant(holder["acquired_at"]) or
                when >= instant(holder["expires_at"])):
            return reply("WAIT_AUTHENTIC_OWNER_LEASE")
        staged = deepcopy(state)
        staged["pending_source_action"] = {
            "schema": 1, "operation_id": request["operation_id"],
            "kind": "OWNER_GHA_BRANCH_PROBE",
            "repository": REPOSITORY, "work_branch": branch,
            "work_id": WORK,
            "source_path": f"ops/probes/gha-write-{run}-a{attempt}.json",
            "main_head": snapshot["main_head"],
            "owner_id": request["owner_id"],
            "owner_epoch": request["owner_epoch"],
            "reserved_at": now, "run_id": run,
            "run_attempt": attempt, "mode": "BRANCH_ONLY",
            "phase": "PENDING_SOURCE_DISPATCH",
        }
        if not scoped_lease_migration_block(staged):
            raise ValueError("reservation failed to fence new writers")
        return reply("PROPOSE_CAS_OWNER_GHA_PROBE_RESERVATION",
                     expected_coordinator_ref=snapshot["coordinator_ref"],
                     state=staged)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return reply("WAIT_INVALID_OWNER_GHA_PROBE_REQUEST")
