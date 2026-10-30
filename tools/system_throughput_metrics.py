"""Read-only, non-authenticating per-role throughput metrics for Studio Autopilot.

This pure function does not authenticate provider observations. A trusted host must
bind its own GitHub GET and Automations PEEK results. No writes, scheduling,
retries, lease mutation, AI usage, or publication can originate from this file.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import uuid

VALID_STATUSES = frozenset({"completed", "failed", "no_update", "in_progress"})
ROLES = frozenset({"WORKER", "META", "REVIEWER"})
SHA = re.compile(r"[0-9a-f]{40}\Z")
DENIED = {key: False for key in (
    "write_allowed", "start_now_allowed", "takeover_allowed", "dispatch_allowed",
    "merge_allowed", "publish_allowed", "external_spend_allowed")}


class MetricsError(ValueError):
    """Only fixed safe codes are emitted; never echo provider/private data."""


def require(valid, code):
    if not valid:
        raise MetricsError(code)


def instant(value):
    require(type(value) is str, "INVALID_TIME")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise MetricsError("INVALID_TIME") from None
    require(dt.tzinfo is not None, "INVALID_TIME")
    return dt.astimezone(timezone.utc)


def canonical_uuid(value):
    require(type(value) is str, "INVALID_RUN_ID")
    try:
        require(str(uuid.UUID(value)) == value, "INVALID_RUN_ID")
    except ValueError:
        raise MetricsError("INVALID_RUN_ID") from None


def canonical_task_id(value):
    require(type(value) is str, "INVALID_TASK_ID")
    if re.fullmatch(r"[0-9a-f]{32}", value):
        return
    raise MetricsError("INVALID_TASK_ID")


def overlap_union_seconds(start, end, intervals):
    """Union of strictly observed foreign lease intersections; no implied WAIT.

    Incomplete release receipts are deliberately excluded and flagged separately.
    """
    windows = sorted((max(start, a), min(end, b)) for a, b in intervals
                     if a < end and b > start)
    total = 0.0
    merged_end = None
    for left, right in windows:
        if merged_end is None or left > merged_end:
            total += (right - left).total_seconds()
            merged_end = right
        elif right > merged_end:
            total += (right - merged_end).total_seconds()
            merged_end = right
    return round(total, 3)


def recovery_record_matches(lookup, request, roles, run_index, released):
    """Match a host-read record; this is NOT a provider authenticator.

    Only a trusted host may supply the read-only lookup capability, backed by
    independently fetched claim/release lineage and same-attempt terminal data.
    CLI JSON cannot supply it. Returned JSON flags never confer authentication.
    A synthetic lookup in tests proves classification only, never live recovery.
    """
    if not callable(lookup):
        return False
    try:
        record = lookup(deepcopy(request))
        actor_keys = {"kind", "recoverer_role", "recoverer_task_id", "recoverer_run_id"}
        if (type(record) is not dict or set(record) != set(request) | actor_keys or
                record["kind"] != "INDEPENDENT_TERMINAL_RECOVERY" or
                any(type(record[k]) is not type(v) or record[k] != v
                    for k, v in request.items())):
            return False
        role, rid = record["recoverer_role"], record["recoverer_run_id"]
        if (type(role) is not str or role not in roles or
                record["recoverer_task_id"] != roles[role] or
                type(rid) is not str or rid == request["owner_run_id"] or
                (role, rid) not in run_index):
            return False
        started, ended, _status, _result = run_index[(role, rid)]
        return started <= released and (ended is None or released <= ended)
    except Exception:
        # Denial, transport errors, absent ACK/history and malformed receipts
        # cannot turn into a verified recovery or disclose host error payloads.
        return False


def build(snapshot, *, binding, recovery_lookup=None):
    """Summarize provider-shaped data without claiming trusted provenance.

    An independent host-supplied binding pins project/repository/main/roles;
    both binding and snapshots are data, never a provider authentication proof.
    Input refs/epochs are structural anchors only until independently fetched.
    For post-terminal releases, optional recovery_lookup(request) is a narrowly
    scoped HOST READ capability, not a write/send/credential callback. Its input
    and exact return contract are constructed below. No callback => UNKNOWN;
    matched host records still do not grant provider verification or authority.
    All recovered intervals are excluded from owner lease-time reports. Their
    full exclusive interval may contribute foreign temporal overlap only with a
    matching host record; missing provenance remains UNKNOWN, never zero WAIT.
    Summary percentiles remain unavailable without six genuine unforced cycles
    and postmerge evidence; this pure module cannot establish those facts.

    Schema: {schema, project_id, repository, main_sha, observed_at, roles,
             runs:[{role, task_id, run_id, scheduled_for, started_at,
                    completed_at, recorded_status, current_result_run_id,
                    current_result_created_at}],
             coordinator:[{role, owner_run_id, acquired_at, released_at,
                           epoch, claim_ref, release_ref}]}

    A result for a *different* run cannot count as a fresh completed report. An
    otherwise completed service can be counted as lifecycle-completed without
    inventing an actual source change or a successful game implementation.
    """
    require(type(snapshot) is dict and set(snapshot) == {
        "schema", "project_id", "repository", "main_sha", "observed_at",
        "roles", "runs", "coordinator"}, "INVALID_FRAME")
    require(type(snapshot["schema"]) is int and snapshot["schema"] == 1,
            "INVALID_SCHEMA")
    require(type(snapshot["project_id"]) is str and
            re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", snapshot["project_id"]),
            "INVALID_PROJECT")
    require(type(snapshot["repository"]) is str and re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", snapshot["repository"]),
        "INVALID_REPOSITORY")
    require(type(snapshot["main_sha"]) is str and SHA.fullmatch(snapshot["main_sha"]),
            "INVALID_SHA")
    require(type(binding) is dict and set(binding) == {
        "project_id", "repository", "main_sha", "roles"}, "INVALID_BINDING")
    require(all(snapshot[key] == binding[key] for key in binding),
            "FOREIGN_PROJECT_BINDING")
    observed = instant(snapshot["observed_at"])
    roles = snapshot["roles"]
    require(type(roles) is dict and set(roles) == ROLES, "INVALID_ROLES")
    for task_id in roles.values():
        canonical_task_id(task_id)
    require(len(set(roles.values())) == 3, "DUPLICATE_TASK")
    runs = snapshot["runs"]
    leases = snapshot["coordinator"]
    require(type(runs) is list and len(runs) <= 5000 and type(leases) is list and
            len(leases) <= 5000, "INVALID_LENGTH")
    run_index = {}
    seen_run_ids = set()
    windows = []
    for run in runs:
        require(type(run) is dict and set(run) == {"role", "task_id", "run_id",
                "scheduled_for", "started_at", "completed_at", "recorded_status",
                "current_result_run_id", "current_result_created_at"}, "INVALID_RUN")
        role = run["role"]
        require(type(role) is str and role in ROLES and run["task_id"] == roles[role], "WRONG_TASK_ROLE")
        rid = run["run_id"]
        canonical_uuid(rid)
        key = (role, rid)
        require(rid not in seen_run_ids, "DUPLICATE_RUN")
        seen_run_ids.add(rid)
        scheduled = instant(run["scheduled_for"])
        started = instant(run["started_at"])
        require(scheduled <= observed and started <= observed, "FUTURE_RUN")
        status = run["recorded_status"]
        require(type(status) is str and status in VALID_STATUSES, "INVALID_STATUS")
        ended = run["completed_at"]
        if status == "in_progress":
            require(ended is None, "INVALID_TERMINAL_TIME")
        else:
            ended = instant(ended)
            require(started <= ended <= observed, "INVALID_TERMINAL_TIME")
        current = run["current_result_run_id"]
        created = run["current_result_created_at"]
        if current is not None:
            canonical_uuid(current)
            created = instant(created)
            require(created <= observed, "FUTURE_RESULT")
        else:
            require(created is None, "RESULT_WITHOUT_RUN")
        fresh = (current == rid and status in ("completed", "failed") and
                 started <= created <= ended)
        result_binding = ("NO_RESULT" if current is None else
                          "PREVIOUS_RUN" if current != rid else
                          "CURRENT_RUN" if fresh else "STALE_SAME_RUN_RESULT")
        run_index[key] = (started, ended, status, current)
        windows.append({"role": role, "run_id": rid, "status": status,
                        "start_offset_sec": round((started - scheduled).total_seconds(), 3),
                        "elapsed_sec": round((ended-started).total_seconds(), 3) if ended else None,
                        "fresh_result": fresh,
                        "terminal_elapsed_seconds": round((ended-started).total_seconds(), 3) if ended else "UNKNOWN",
                        "schedule_jitter_seconds": round((started-scheduled).total_seconds(), 3),
                        "latest_result_binding": result_binding})
    occupied = {key: 0.0 for key in run_index}
    confirmed_lease_windows = []
    unknown_lease_windows = []
    post_terminal_unknown = set()
    recovered_records = set()
    unreleased = set()
    lease_classifications = []
    seen_leases = set()
    seen_epochs = set()
    for lease in leases:
        require(type(lease) is dict and set(lease) == {"role", "owner_run_id",
                "acquired_at", "released_at", "epoch", "claim_ref", "release_ref"}, "INVALID_LEASE")
        role, rid = lease["role"], lease["owner_run_id"]
        require(type(role) is str and role in ROLES, "INVALID_LEASE_ROLE")
        epoch = lease["epoch"]
        require(type(epoch) is int and epoch > 0 and epoch not in seen_epochs,
                "INVALID_LEASE_EPOCH")
        seen_epochs.add(epoch)
        require(type(lease["claim_ref"]) is str and SHA.fullmatch(lease["claim_ref"]),
                "INVALID_CLAIM_REF")
        release_ref = lease["release_ref"]
        require((lease["released_at"] is None and release_ref is None) or
                (lease["released_at"] is not None and type(release_ref) is str and
                 SHA.fullmatch(release_ref) and release_ref != lease["claim_ref"]),
                "INVALID_RELEASE_REF")
        canonical_uuid(rid)
        key = (role, rid)
        require(key in run_index, "ORPHAN_LEASE_OBSERVATION")
        require(key not in seen_leases, "DUPLICATE_LEASE")
        seen_leases.add(key)
        acquired, released = instant(lease["acquired_at"]), lease["released_at"]
        start, end, _status, _ = run_index[key]
        require(start <= acquired <= observed and (end is None or acquired <= end),
                "INVALID_LEASE_TIME")
        if released is not None:
            released = instant(released)
            require(acquired <= released <= observed, "INVALID_LEASE_TIME")
        if released is not None and end is not None and released > end:
            request = {"project_id": snapshot["project_id"],
                       "repository": snapshot["repository"], "main_sha": snapshot["main_sha"],
                       "owner_role": role, "owner_task_id": roles[role], "owner_run_id": rid,
                       "owner_started_at": start.isoformat(), "owner_completed_at": end.isoformat(),
                       "epoch": epoch, "claim_ref": lease["claim_ref"], "release_ref": release_ref,
                       "acquired_at": acquired.isoformat(), "released_at": released.isoformat()}
            if recovery_record_matches(recovery_lookup, request, roles, run_index, released):
                recovered_records.add(key)
                occupied[key] = 0.0  # Never count recovery lag/interval as owner work.
                confirmed_lease_windows.append((role, acquired, released))
                classification = "HOST_BOUND_RECOVERY_RECORD_NOT_PROVIDER_ATTESTATION"
            else:
                post_terminal_unknown.add(key)
                occupied[key] = None
                unknown_lease_windows.append((role, acquired, released))
                classification = "UNKNOWN_RECOVERY_PROVENANCE"
            lease_classifications.append({"role": role, "owner_run_id": rid,
                                          "epoch": epoch, "classification": classification})
            continue
        # Do not infer release from a completed service; missing receipt stays UNKNOWN.
        if released is None:
            occupied[key] = None
            unreleased.add(key)
            unknown_lease_windows.append((role, acquired, None))
            continue
        require(occupied[key] is not None, "INVALID_LEASE_ORDER")
        occupied[key] += (released-acquired).total_seconds()
        confirmed_lease_windows.append((role, acquired, released))
    # This project has one exclusive coordinator lease at a time.  Two
    # completed lease windows with overlapping ownership are invalid input,
    # not evidence of parallel progress or confirmed blocking.
    ordered_leases = sorted(confirmed_lease_windows, key=lambda item: item[1])
    for previous, current in zip(ordered_leases, ordered_leases[1:]):
        require(previous[2] <= current[1], "OVERLAPPING_EXCLUSIVE_LEASES")
    out = {}
    for role in sorted(ROLES):
        match = [w for w in windows if w["role"] == role]
        terminal = [w for w in match if w["status"] != "in_progress"]
        elapsed = [w["elapsed_sec"] for w in terminal]
        offsets = [w["start_offset_sec"] for w in match]
        live = [w for w in match if w["status"] == "in_progress"]
        # Only confirmed foreign lease intervals can support a bounded overlap.
        # This measures temporal co-presence, NOT a lock-wait result or lost time.
        overlap_sum = 0.0
        overlapped_runs = 0
        incomplete_foreign_runs = 0
        for w in terminal:
            started = run_index[(role, w["run_id"])][0]
            ended = run_index[(role, w["run_id"])][1]
            foreign = [(a, b) for other, a, b in confirmed_lease_windows if other != role]
            overlap = overlap_union_seconds(started, ended, foreign)
            overlap_sum += overlap
            overlapped_runs += overlap > 0
            incomplete_foreign_runs += any(other != role and a < ended and
                                           (b is None or b > started)
                                           for other, a, b in unknown_lease_windows)
        out[role] = {
            "task_id": roles[role], "observed_runs": len(match),
            "terminal_runs": len(terminal), "in_progress": len(live),
            "failed_runs": sum(w["status"] == "failed" for w in terminal),
            "no_update_runs": sum(w["status"] == "no_update" for w in terminal),
            "completed_runs": sum(w["status"] == "completed" for w in terminal),
            "fresh_result_runs": sum(w["fresh_result"] for w in terminal),
            "elapsed_seconds_sum": round(sum(elapsed), 3),
            "elapsed_p50_seconds": None,
            "elapsed_p90_seconds": None,
            "schedule_offset_p50_seconds": None,
            "summary_statistics": "NOT_VERIFIED_REQUIRES_SIX_UNFORCED_RUNS_AND_POSTMERGE_EVIDENCE",
            "lease_seconds_reported": round(sum(value for (r, _), value in occupied.items()
                                                  if r == role and value is not None), 3),
            "lease_unreleased_unknown_count": sum(r == role for r, _ in unreleased),
            "lease_unknown_count": sum(value is None for (r, _), value in occupied.items() if r == role),
            "post_terminal_release_unknown_count": sum(r == role for r, _ in post_terminal_unknown),
            "host_bound_recovery_record_count": sum(r == role for r, _ in recovered_records),
            "foreign_lease_overlap_seconds_reported": round(overlap_sum, 3),
            "foreign_lease_overlap_seconds": "UNKNOWN" if incomplete_foreign_runs or live else round(overlap_sum, 3),
            "foreign_lease_overlap_terminal_runs": overlapped_runs,
            "foreign_lease_incomplete_terminal_runs": incomplete_foreign_runs,
            "wait_reason": "NOT_VERIFIED",
            "productive_source_changes": "NOT_VERIFIED",
            "merge_acceptance": "NOT_VERIFIED",
            "actual_user_delivery": "NOT_VERIFIED",
        }
    return {"schema": 1, "mode": "READ_ONLY_THROUGHPUT_METRICS",
            "verification": "NOT_VERIFIED", "project_id": snapshot["project_id"],
            "repository": snapshot["repository"], "main_sha": snapshot["main_sha"],
            "observed_at": observed.isoformat(), "roles": out, "runs": windows,
            "authority": dict(DENIED), "lease_classifications": lease_classifications,
            "limitations": ["HOST_PROVIDER_AUTHENTICATION_REQUIRED",
                            "SOURCE_CHANGES_NOT_INFERRED_FROM_PROSE",
                            "MISSING_LEASE_RELEASE_IS_NOT_SUCCESS",
                            "BILLABLE_MINUTES_UNKNOWN",
                            "LEASE_OVERLAP_NOT_CAUSAL_WAIT_PROOF",
                            "RECOVERY_LOOKUP_IS_HOST_CAPABILITY_NOT_JSON_ATTESTATION",
                            "RECOVERED_INTERVAL_EXCLUDED_FROM_OWNER_LEASE_TIME"]}


def unique_pairs(pairs):
    output = {}
    for key, value in pairs:
        require(key not in output, "DUPLICATE_JSON_KEY")
        output[key] = value
    return output


def reject_constant(_):
    raise MetricsError("NONFINITE_JSON")


def main():
    import sys
    try:
        raw = sys.stdin.read(2_000_001)
        require(len(raw.encode()) <= 2_000_000, "INPUT_TOO_LARGE")
        envelope = json.loads(raw, object_pairs_hook=unique_pairs,
                              parse_constant=reject_constant)
        require(type(envelope) is dict and set(envelope) == {"snapshot", "binding"},
                "INVALID_ENVELOPE")
        result = build(envelope["snapshot"], binding=envelope["binding"])
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (MetricsError, ValueError, TypeError, KeyError, OverflowError):
        print(json.dumps({"error": "INVALID_OR_UNVERIFIED_INPUT", "authority": DENIED}))
        sys.exit(2)


if __name__ == "__main__":
    main()
