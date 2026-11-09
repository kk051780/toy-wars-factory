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
# This is a single PR203 probe, not a generic writer capability.
PROBE_REPOSITORY = "kk051780/toy-wars-factory"
PROBE_BRANCH = "controller/p0-legacy-shadow-compat-20261108-76116caf"
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
    if (snapshot["repository"] != PROBE_REPOSITORY or
            any(type(snapshot[k]) is not str or not SHA.fullmatch(snapshot[k])
                for k in ("coordinator_ref", "main_head", "source_head")) or
            snapshot["work_branch"] != PROBE_BRANCH):
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



def inspect_interrupted_probe(snapshot_first, snapshot_second, request, *,
                              source_heads, pr_heads, main_heads,
                              target_parent, now):
    """Read-only cross-chat recovery classification; NEVER performs a write.

    Caller MUST independently fetch two genuine coordinator snapshots, two
    GitHub source ref observations, PR heads, main refs and target commit
    parent from connected providers. These injected values are UNTRUSTED
    inside Python. A matching result is NOT a provider attestation, release
    grant, write retry, or proof the original ChatGPT run terminated.
    """
    def stop(code, **extra):
        # "reason" is evidence metadata, never the positional action code.
        # Keep them distinct: duplicate kwargs must not collapse a valid HOLD.
        return reply(code, may_retry=False, may_release=False, **extra)

    try:
        if (type(snapshot_first) is not dict or
                type(snapshot_second) is not dict or
                snapshot_first != snapshot_second or
                set(snapshot_first) != SNAPSHOT_KEYS):
            return stop("WAIT_COORDINATOR_REF_DRIFT")
        if type(request) is not dict or set(request) != REQ_KEYS:
            raise ValueError("request schema")
        snap = snapshot_first
        state = validate(snap["state"])
        canonical_id(request["operation_id"])
        canonical_id(request["owner_id"])
        if (snap["repository"] != PROBE_REPOSITORY or
                snap["work_branch"] != PROBE_BRANCH or
                any(type(snap[k]) is not str or not SHA.fullmatch(snap[k])
                    for k in ("coordinator_ref", "main_head", "source_head")) or
                type(request["owner_epoch"]) is not int or
                request["work_id"] != WORK or request["source_path"] != FILE or
                any(type(request[k]) is not str or not SHA.fullmatch(request[k])
                    for k in ("before_head", "after_head")) or
                request["before_head"] == request["after_head"] or
                type(source_heads) not in (list, tuple) or
                type(pr_heads) not in (list, tuple) or
                type(main_heads) not in (list, tuple) or
                len(source_heads) != 2 or len(pr_heads) != 2 or
                len(main_heads) != 2 or
                any(type(v) is not str or not SHA.fullmatch(v)
                    for v in (*source_heads, *pr_heads, *main_heads)) or
                type(target_parent) is not str or
                not SHA.fullmatch(target_parent)):
            raise ValueError("ref or request shape")
        if main_heads[0] != main_heads[1] or main_heads[0] != snap["main_head"]:
            return stop("WAIT_MAIN_CHANGED")
        if source_heads[0] != source_heads[1] or source_heads[0] != snap["source_head"]:
            return stop("WAIT_SOURCE_REF_DRIFT")
        if pr_heads[0] != pr_heads[1] or pr_heads[0] != source_heads[0]:
            return stop("WAIT_PR_HEAD_CHANGED")
        if target_parent != request["before_head"]:
            return stop("WAIT_TARGET_PARENT_MISMATCH")
        current = instant(now)
        scoped_lease_migration_block(state)  # malformed nested state fails closed
        pending = state.get("pending_source_action")
        if pending is None:
            audit = state.get("last_source_action_probe")
            if (type(audit) is dict and
                    audit.get("operation_id") == request["operation_id"] and
                    audit.get("before_head") == request["before_head"] and
                    audit.get("after_head") == request["after_head"] and
                    audit.get("work_branch") == snap["work_branch"] and
                    source_heads[0] == request["after_head"]):
                return stop("ALREADY_RECONCILED_NO_REPLAY",
                            evidence="coordinator audit plus ref observation")
            return stop("WAIT_NO_PERSISTED_MATCHING_ACTION")
        expected_action = {
            "schema": 1, "operation_id": request["operation_id"],
            "kind": "SOURCE_UPDATE_PROBE",
            "repository": snap["repository"],
            "work_branch": snap["work_branch"],
            "work_id": WORK, "source_path": FILE,
            "before_head": request["before_head"],
            "after_head": request["after_head"],
            "main_head": snap["main_head"],
            "owner_id": request["owner_id"],
            "owner_epoch": request["owner_epoch"],
        }
        for key, value in expected_action.items():
            if pending.get(key) != value:
                return stop("WAIT_FOREIGN_OR_CHANGED_ACTION")
        holder = state.get("holder")
        if (type(holder) is not dict or holder.get("kind") != "CONTROLLER" or
                holder.get("owner_id") != request["owner_id"] or
                holder.get("epoch") != request["owner_epoch"] or
                holder.get("work_branch") != snap["work_branch"] or
                holder.get("base_main_sha") != snap["main_head"]):
            return stop("WAIT_CHANGED_OWNER")
        reserved_at = instant(pending["reserved_at"])
        if current < reserved_at:
            return stop("WAIT_CLOCK_REGRESSION")
        if current >= instant(holder["expires_at"]):
            return stop("WAIT_SERVICE_TERMINATION_ATTESTATION",
                        reason="lease expiry alone cannot prove host termination")
        if source_heads[0] == request["before_head"]:
            return stop("WAIT_UNCERTAIN_NOT_APPLIED_DO_NOT_RETRY",
                        reason="in-flight old-head read cannot prove no pending provider call")
        if source_heads[0] == request["after_head"]:
            return stop("CANDIDATE_OWNER_RECONCILE_ONLY",
                        reason="requires genuine provider ref+PR+main readback and live owner CAS",
                        coordinator_ref=snap["coordinator_ref"])
        return stop("WAIT_FOREIGN_SOURCE_UPDATE")
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return stop("WAIT_INVALID_RECOVERY_EVIDENCE")
