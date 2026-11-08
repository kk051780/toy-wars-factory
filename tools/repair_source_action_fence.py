"""P0 manual fenced SOURCE_UPDATE_PROBE; non-authorizing state proposals.

The real connected GitHub tool execution MUST be externally hosted and
record the coordinator CAS, exact branch CAS and ref readback before calling
reconcile_probe. This code is pure/read-only and has no GitHub credentials.
Fake callbacks or receipts CANNOT prove provider authentication or unlock
unattended writes. Never use for main branch/merge/publish.
"""
from copy import deepcopy
from datetime import timedelta
import re
from repair_control import (canonical_id, instant, validate,
                            scoped_lease_migration_block)

SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
WORK = "P0_ISSUE123_PR203_SOURCE_ACTION_PROBE"
FILE = "history/C10010_real_source_action_probe.json"
SNAPSHOT_KEYS = {"repository", "coordinator_ref", "main_head",
                 "work_branch", "source_head", "state"}
REQ_KEYS = {"operation_id", "owner_id", "owner_epoch", "work_id",
            "source_path", "before_head", "after_head"}


def reply(action, **kwargs):
    return {"action": action, "may_write": False, "may_merge": False,
            "provider_authenticated": False, "host_action_fence_verified": False,
            "real_parallel": False, **kwargs}


def _validate(snapshot, request):
    if type(snapshot) is not dict or set(snapshot) != SNAPSHOT_KEYS:
        raise ValueError("source snapshot shape")
    if type(request) is not dict or set(request) != REQ_KEYS:
        raise ValueError("source request shape")
    state = validate(snapshot["state"])
    if (type(snapshot["repository"]) is not str or
            not REPO.fullmatch(snapshot["repository"]) or
            any(type(snapshot[k]) is not str or not SHA.fullmatch(snapshot[k])
                for k in ("coordinator_ref", "main_head", "source_head")) or
            type(snapshot["work_branch"]) is not str or
            not snapshot["work_branch"].startswith("controller/p0-") or
            snapshot["work_branch"] == "twf-repair-coordinator"):
        raise ValueError("invalid connected Git ref bindings")
    canonical_id(request["operation_id"])
    canonical_id(request["owner_id"])
    if (type(request["owner_epoch"]) is not int or
            request["work_id"] != WORK or request["source_path"] != FILE or
            request["before_head"] != snapshot["source_head"] or
            type(request["after_head"]) is not str or
            not SHA.fullmatch(request["after_head"]) or
            request["after_head"] == request["before_head"]):
        raise ValueError("invalid scoped operation binding")
    return state


def propose_probe(snapshot, request, now):
    """Build a coordinator CAS proposal; never a provider write permit."""
    try:
        state = _validate(snapshot, request)
        if scoped_lease_migration_block(state):
            return reply("WAIT_EXISTING_ACTION_OR_MIGRATION")
        if state.get("parallel_write_migration", "LEGACY_ONLY") != "LEGACY_ONLY":
            return reply("WAIT_MIGRATION")
        holder = state.get("holder")
        at = instant(now)
        if (type(holder) is not dict or holder.get("kind") != "CONTROLLER" or
                holder.get("owner_id") != request["owner_id"] or
                holder.get("epoch") != request["owner_epoch"] or
                holder.get("task_id") is not None or
                holder.get("work_branch") != snapshot["work_branch"] or
                holder.get("base_main_sha") != snapshot["main_head"] or
                at < instant(holder["acquired_at"]) or
                at >= instant(holder["expires_at"])):
            return reply("WAIT_NOT_LIVE_CONTROLLER")
        next_state = deepcopy(state)
        next_state["pending_source_action"] = {
            "schema": 1, "operation_id": request["operation_id"],
            "kind": "SOURCE_UPDATE_PROBE", "repository": snapshot["repository"],
            "work_branch": snapshot["work_branch"], "work_id": WORK,
            "source_path": FILE, "before_head": request["before_head"],
            "after_head": request["after_head"], "main_head": snapshot["main_head"],
            "owner_id": request["owner_id"], "owner_epoch": request["owner_epoch"],
            "reserved_at": now}
        if not scoped_lease_migration_block(next_state):
            raise ValueError("staged action must fence new legacy work")
        return reply("PROPOSE_CAS_SOURCE_ACTION", state=next_state,
                     expected_coordinator_ref=snapshot["coordinator_ref"],
                     request=deepcopy(request), prepared_at=now)
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return reply("WAIT_INVALID_SOURCE_PROPOSAL")


def reconcile_probe(snapshot, request, *, source_ref_first, source_ref_second,
                    now):
    """Non-authorizing cleanup candidate, only for two matching ref readbacks.

    The values MUST be obtained from actual GitHub calls by a trusted host;
    Python cannot authenticate their provenance. Drift/uncertainty = HOLD.
    """
    try:
        state = _validate({**snapshot,
                           "source_head": request["before_head"]}, request)
        action = state.get("pending_source_action")
        if type(action) is not dict:
            return reply("WAIT_NO_PENDING_ACTION")
        if not scoped_lease_migration_block(state):
            raise ValueError("action failed to block legacy writes")
        if (any(action.get(a) != b for a, b in (
                ("operation_id", request["operation_id"]),
                ("owner_id", request["owner_id"]),
                ("owner_epoch", request["owner_epoch"]),
                ("before_head", request["before_head"]),
                ("after_head", request["after_head"]),
                ("work_branch", snapshot["work_branch"]),
                ("main_head", snapshot["main_head"]),
                ("repository", snapshot["repository"]))) or
                type(source_ref_first) is not str or
                source_ref_first != request["after_head"] or
                source_ref_second != source_ref_first):
            return reply("WAIT_UNVERIFIED_GIT_READBACK")
        if instant(now) < instant(action["reserved_at"]):
            raise ValueError("future settlement")
        next_state = deepcopy(state)
        next_state.pop("pending_source_action")
        next_state["last_source_action_probe"] = {
            "kind": "SOURCE_UPDATE_PROBE_CONNECTED_READBACK_ONLY",
            "operation_id": request["operation_id"],
            "work_branch": snapshot["work_branch"], "source_path": FILE,
            "before_head": request["before_head"],
            "after_head": request["after_head"],
            "source_ref_readback_twice": True,
            "verified_at": now, "host_actor_attested": False,
            "independent_review": False, "real_parallel": False}
        return reply("PROPOSE_CAS_RECONCILIATION", state=next_state,
                     expected_coordinator_ref=snapshot["coordinator_ref"])
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return reply("WAIT_INVALID_SETTLEMENT")
