"""P0 staged, NON-AUTHORIZING GitHub merge action reservation.

A trusted host must authenticate task/run, own the GitHub connection, bind
provider merge+readback to a persisted coordinator reservation, and handle
ambiguous outcomes. This module only builds and tests candidate CAS state.
It has NO GitHub client, no secrets, no hosted authority and no merge callback.
No 'success' outcome here permits a real provider operation.
"""
from copy import deepcopy
from datetime import timedelta
import re
from repair_control import (canonical_id, instant, owns, validate,
                            scoped_lease_migration_block)

SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
REQUEST_KEYS = {"action_id", "reviewer_run_id", "reviewer_task_id",
                "holder_epoch", "pr_number", "pr_head", "main_head"}
SNAPSHOT_KEYS = {"repository", "main_head", "pr_head", "ref_sha", "state"}


def reply(action, **details):
    return {"action": action, "may_execute": False,
            "provider_authenticated": False, "provider_write_proven": False,
            "real_two_writers": False, **details}


def proposed_reservation(snapshot, request, now):
    """Build one immutable reservation; NEVER a source-write/merge permit."""
    try:
        if type(snapshot) is not dict or set(snapshot) != SNAPSHOT_KEYS:
            raise ValueError("invalid snapshot")
        if type(request) is not dict or set(request) != REQUEST_KEYS:
            raise ValueError("invalid request")
        if (type(snapshot["repository"]) is not str or
                not REPO.fullmatch(snapshot["repository"]) or
                any(type(snapshot[k]) is not str or not SHA.fullmatch(snapshot[k])
                    for k in ("main_head", "pr_head", "ref_sha"))):
            raise ValueError("invalid provider refs")
        state = snapshot["state"]
        validate(state)
        if scoped_lease_migration_block(state):
            return reply("WAIT_ACTION_OR_MIGRATION")
        if state.get("pending_provider_action") is not None:
            return reply("WAIT_ACTION_IN_FLIGHT")
        for key in ("action_id", "reviewer_run_id"):
            canonical_id(request[key])
        if (type(request["reviewer_task_id"]) is not str or
                not request["reviewer_task_id"] or
                type(request["holder_epoch"]) is not int or
                type(request["pr_number"]) is not int or request["pr_number"] < 1 or
                request["pr_head"] != snapshot["pr_head"] or
                request["main_head"] != snapshot["main_head"]):
            raise ValueError("request identity or refs changed")
        holder = state.get("holder")
        when = instant(now)
        if (type(holder) is not dict or holder.get("kind") != "REVIEWER" or
                holder.get("work_branch") != "main" or
                holder.get("task_id") != request["reviewer_task_id"] or
                holder.get("owner_id") != request["reviewer_run_id"] or
                holder.get("epoch") != request["holder_epoch"] or
                state.get("authorized_tasks", {}).get("REVIEWER") !=
                request["reviewer_task_id"] or
                when < instant(holder["acquired_at"]) or
                not owns(state, "REVIEWER", request["reviewer_run_id"],
                         request["holder_epoch"], now)):
            return reply("WAIT_AUTHENTIC_REVIEWER_HOLDER")
        result = deepcopy(state)
        result["pending_provider_action"] = {
            "schema": 1, "action_id": request["action_id"], "kind": "MERGE",
            "repository": snapshot["repository"],
            "pr_number": request["pr_number"],
            "pr_head": request["pr_head"], "main_head": request["main_head"],
            "reviewer_run_id": request["reviewer_run_id"],
            "reviewer_task_id": request["reviewer_task_id"],
            "holder_epoch": request["holder_epoch"], "reserved_at": now}
        # No change to holder epoch: CAS commit ref + unique action_id fence
        # this reservation. The matching reviewer remains the exclusive owner.
        if not scoped_lease_migration_block(result):
            raise ValueError("reservation does not block legacy writes")
        return reply("PROPOSE_CAS_RESERVATION", state=result,
                     expected_sha=snapshot["ref_sha"], request=deepcopy(request),
                     requested_at=now)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return reply("WAIT_INVALID_OR_STALE_REQUEST")


def apply_once(snapshot, proposal, *, read, cas, clock):
    """One injected fake-host coordinator CAS; never calls GitHub merge."""
    def wait(code, attempted=False):
        return reply(code, cas_attempted=attempted)

    if type(proposal) is not dict or proposal.get("action") != "PROPOSE_CAS_RESERVATION":
        return wait("WAIT_NO_PROPOSAL")
    try:
        a, b = read(), read()
        if a != b or a != snapshot:
            raise ValueError("read drift")
        when = instant(clock())
        started = instant(proposal["requested_at"])
        if not started <= when <= started + timedelta(seconds=30):
            raise ValueError("expired proposal")
        holder = snapshot["state"]["holder"]
        if when >= instant(holder["expires_at"]):
            raise ValueError("owner expired")
        freshly = proposed_reservation(snapshot, proposal["request"],
                                       proposal["requested_at"])
        if (freshly.get("action") != "PROPOSE_CAS_RESERVATION" or
                proposal["expected_sha"] != snapshot["ref_sha"] or
                proposal["state"] != freshly["state"]):
            raise ValueError("proposal mutated")
    except Exception:
        return wait("WAIT_PRE_CAS_DRIFT")
    try:
        ack = cas(proposal["expected_sha"], deepcopy(proposal["state"]))
    except Exception:
        # Unknown outcome: never retry, never clear the reservation by expiry.
        return wait("WAIT_CAS_ACK_UNKNOWN", True)
    if type(ack) is not str or not SHA.fullmatch(ack) or ack == proposal["expected_sha"]:
        return wait("WAIT_CAS_CONFLICT_OR_BAD_ACK", True)
    try:
        a, b = read(), read()
        if (a != b or type(a) is not dict or
                a.get("ref_sha") != ack or
                a.get("state") != proposal["state"] or
                a.get("repository") != snapshot["repository"] or
                a.get("main_head") != snapshot["main_head"] or
                a.get("pr_head") != snapshot["pr_head"]):
            raise ValueError("post-read drift")
    except Exception:
        return wait("WAIT_CAS_READBACK_UNCONFIRMED", True)
    # An actual merge requires a separately reviewed, authenticated host
    # adapter that retains the reservation across its provider operation.
    return wait("MOCK_RESERVATION_READBACK_NO_PROVIDER_ACTION", True)
