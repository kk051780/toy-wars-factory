"""Read-only, repo-bound service observation; no scheduling or recovery grants.

The trusted host supplies existing GitHub GET and automation PEEK capabilities.
Neither a callback nor stdin JSON authenticates its origin. Only the host can
attest an actual connected execution, separately from this NOT_VERIFIED output.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# The accepted v2 CLI imports its legacy sibling as a standalone tool.
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from studio_autopilot import scheduler
from tools import system_github_evidence as github
from tools import system_host_write_triage_v2 as triage

EvidenceError = github.EvidenceError
need, loads, moment = github.need, github.loads, github.moment
FIELDS = {"game_id", "manifest_path", "main_sha", "coordinator_sha",
          "coordinator_blob_sha", "coordinator_epoch", "max_record_age_seconds"}
ROLES = {"author": "WORKER", "meta": "META", "reviewer": "REVIEWER"}
TERMINAL = {"completed", "failed", "no_update"}
DENIED = {key: False for key in ("write_allowed", "start_now_allowed", "takeover_allowed",
          "dispatch_allowed", "merge_allowed", "publish_allowed", "external_spend_allowed",
          "safe_to_next_schedule")}


@dataclass(frozen=True)
class PeekResponse:
    ok: bool
    text: str


def run_id(value):
    try:
        need(type(value) is str and str(uuid.UUID(value)) == value, "INVALID_SERVICE_RUN_ID")
    except (ValueError, TypeError, AttributeError):
        raise EvidenceError("INVALID_SERVICE_RUN_ID") from None
    return value


def project_binding(projects, b, get, clock):
    need(type(b) is dict and set(b) == FIELDS, "INVALID_BINDING")
    need(github.integer(b["max_record_age_seconds"]) and b["max_record_age_seconds"] <= 172800 and
         github.integer(b["coordinator_epoch"], 0), "INVALID_OBSERVATION_LIMIT")
    games = scheduler._validated_games(deepcopy(projects))
    selected = [p for p in games if p["game_id"] == b["game_id"]]
    need(len(selected) == 1, "UNKNOWN_PROJECT")
    project = selected[0]
    need(type(b["manifest_path"]) is str and github.re.fullmatch(
        r"studio_autopilot/projects/[A-Za-z0-9_]+[.]json", b["manifest_path"]), "INVALID_MANIFEST_PATH")
    for key in ("main_sha", "coordinator_sha", "coordinator_blob_sha"):
        github.sha(b[key])
    r = github.Reader(project["repository"], get, clock)
    repository = r.read("")
    need(repository.get("full_name") == project["repository"] and
         repository.get("fork") is False, "FOREIGN_REPOSITORY")
    r.ref("main", b["main_sha"])
    r.ref(project["coordination_ref"], b["coordinator_sha"])
    tree = r.tree(b["main_sha"])
    need(r.blob(tree, b["manifest_path"]) == project, "MANIFEST_NOT_BOUND_TO_MAIN")
    policy = r.blob(tree, "config/autonomous_repair.json")
    roles = {kind: project["roles"][role] for role, kind in ROLES.items()}
    need(policy.get("repository") == project["repository"] and policy.get("queue_version", 0) >= 4 and
         policy.get("task_id") == roles["WORKER"] and
         policy.get("system_review", {}).get("task_id") == roles["META"] and
         policy.get("integration", {}).get("task_id") == roles["REVIEWER"], "ROLE_POLICY_MISMATCH")
    state = r.blob(r.tree(b["coordinator_sha"]), "ops/REPAIR_COORDINATOR.json", b["coordinator_blob_sha"])
    need(type(state.get("schema")) is int and state["schema"] == 1 and
         state.get("task_id") == roles["WORKER"] and state.get("authorized_tasks") == roles and
         type(state.get("epoch")) is int and state["epoch"] == b["coordinator_epoch"], "WRONG_EPOCH_OR_ROLE")
    holder = state.get("holder")
    if holder is not None:
        need(type(holder) is dict and holder.get("kind") in (*roles, "CONTROLLER", "DISPATCH") and
             type(holder.get("epoch")) is int and holder["epoch"] == state["epoch"], "INVALID_HOLDER")
        run_id(holder.get("owner_id"))
        acquired, expires = moment(holder["acquired_at"]), moment(holder["expires_at"])
        need(acquired <= r.started and 0 < (expires-acquired).total_seconds() <= 1800, "INVALID_LEASE_TIME")
        if holder["kind"] in roles:
            need(holder.get("task_id") == roles[holder["kind"]], "HOLDER_WRONG_TASK")
        # Never emit arbitrary holder fields or treat expiry as a recovery grant.
        holder = {key: holder.get(key) for key in ("kind", "owner_id", "task_id", "epoch",
                                                   "acquired_at", "expires_at")}
    return project, r, holder


def snapshot(raw, task, now, max_age):
    """Validate provider lifecycle metadata, discard all prose and unknown data."""
    envelope = loads(raw)
    need(type(envelope) is dict, "INVALID_PEEK_SCHEMA")
    # Actual connector responses may contain one structuredContent wrapper.
    if "structuredContent" in envelope:
        envelope = envelope["structuredContent"]
    need(type(envelope) is dict and type(envelope.get("automations")) is list and
         len(envelope["automations"]) == 1, "MISSING_OR_DUPLICATE_SERVICE")
    service = envelope["automations"][0]
    need(type(service) is dict and service.get("id") == task and
         type(service.get("is_enabled")) is bool, "WRONG_SERVICE_TASK")
    details = service.get("run_details")
    need(type(details) is dict and type(details.get("last_run")) is dict, "NO_SERVICE_RUN")
    last = details["last_run"]
    current_id = run_id(last.get("id"))
    status = last.get("recorded_status")
    need(type(status) is str and status in TERMINAL | {"in_progress"}, "UNKNOWN_SERVICE_STATUS")
    start, scheduled = moment(last["started_at"]), moment(last["scheduled_for"])
    need(start <= now and (now-start).total_seconds() <= max_age, "STALE_OR_FUTURE_SERVICE_RUN")
    completed = last.get("completed_at")
    if status == "in_progress":
        need(completed is None, "ACTIVE_SERVICE_HAS_COMPLETION")
    else:
        need(completed is not None and start <= moment(completed) <= now, "INVALID_SERVICE_COMPLETION")
    # scheduled_for is scheduling intent, not an event: manual runs can start
    # early. Do not equate it with started_at or require scheduled <= started.
    safe_last = {"id": current_id, "recorded_status": status, "scheduled_for": scheduled.isoformat(),
                 "started_at": start.isoformat(),
                 "completed_at": None if completed is None else moment(completed).isoformat()}
    report = details.get("latest_result")
    binding, safe_result = "MISSING", None
    if report is not None:
        need(type(report) is dict, "INVALID_SERVICE_RESULT")
        report_id = run_id(report.get("run_id"))
        created, finished = moment(report["created_at"]), moment(report["completed_at"])
        report_scheduled = moment(report["scheduled_for"])
        need(created <= finished <= now, "INVALID_RESULT_TIME")
        for field in ("is_failure_message", "requires_user_action"):
            need(type(report.get(field)) is bool, "INVALID_RESULT_FLAGS")
        if report_id == current_id:
            need(status in TERMINAL and start <= created and
                 finished == moment(completed) and report_scheduled == scheduled, "CURRENT_RESULT_LIFECYCLE_MISMATCH")
            binding = "CURRENT_RUN"
        else:
            need(finished <= start, "PRIOR_RESULT_OVERLAPS_CURRENT_RUN")
            binding = "PREVIOUS_RUN"
        safe_result = {"run_id": report_id, "created_at": created.isoformat(),
                       "completed_at": finished.isoformat(), "scheduled_for": report_scheduled.isoformat(),
                       "is_failure_message": report["is_failure_message"],
                       "requires_user_action": report["requires_user_action"]}
    if not service["is_enabled"]:
        observed = "SERVICE_DISABLED"
    elif status == "in_progress":
        observed = "IN_PROGRESS"
    elif status in ("failed", "no_update"):
        observed = status.upper()
    elif binding != "CURRENT_RUN":
        observed = "CURRENT_RESULT_MISSING"
    elif safe_result["is_failure_message"] or safe_result["requires_user_action"]:
        observed = "CURRENT_RESULT_REQUIRES_ATTENTION"
    else:
        observed = "COMPLETED_WITH_CURRENT_RESULT"
    return {"task_id": task, "is_enabled": service["is_enabled"], "last_run": safe_last,
            "latest_result_binding": binding, "latest_result_metadata": safe_result,
            "observation_state": observed}


def observe(projects, binding, get, peek, clock):
    try:
        return _observe(projects, binding, get, peek, clock)
    except EvidenceError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, IndexError, OverflowError):
        raise EvidenceError("MALFORMED_SERVICE_EVIDENCE") from None


def _observe(projects, b, get, peek, clock):
    project, reader, holder = project_binding(projects, b, get, clock)
    trace = []
    def read_service(task):
        at = moment(clock())
        need(reader.started <= at and (at-reader.started).total_seconds() <= 120, "OBSERVATION_WINDOW_EXCEEDED")
        try:
            response = peek(task)
        except Exception:
            raise EvidenceError("PEEK_UNAVAILABLE") from None
        finished = moment(clock())
        need(at <= finished and (finished-reader.started).total_seconds() <= 120, "OBSERVATION_WINDOW_EXCEEDED")
        need(type(response) is PeekResponse and response.ok is True, "PEEK_REJECTED")
        safe = snapshot(response.text, task, finished, b["max_record_age_seconds"])
        trace.append({"method": "PEEK", "task_id": task, "observed_at": finished.isoformat(),
                      "metadata_sha256": hashlib.sha256(json.dumps(safe, sort_keys=True).encode()).hexdigest()})
        return safe
    services = {role: read_service(project["roles"][role]) for role in ROLES}
    seen = set()
    for role, service in services.items():
        ids = {service["last_run"]["id"]}
        if service["latest_result_metadata"]:
            ids.add(service["latest_result_metadata"]["run_id"])
        need(not seen & ids, "CROSS_ROLE_RUN_REUSE")
        seen.update(ids)
    holder_binding = "NO_HOLDER_OBSERVED"
    if holder is not None:
        holder_binding = "UNRESOLVED_OWNER_RUN"
        for role, kind in ROLES.items():
            observed_run = services[role]["last_run"]["id"]
            if holder["owner_id"] == observed_run:
                need(holder["kind"] == kind, "HOLDER_RUN_ROLE_COLLISION")
                holder_binding = "MATCHED_CURRENT_SERVICE_RUN"
    # A previous result can never finish the current holder or waive a fence.
    for role in ROLES:
        need(read_service(project["roles"][role]) == services[role], "SERVICE_CHANGED_DURING_OBSERVATION")
    reader.ref("main", b["main_sha"])
    reader.ref(project["coordination_ref"], b["coordinator_sha"])
    # Full triage inputs do not exist here. Invoke the accepted v2 validator
    # with absent evidence/config; never synthesize PR/QA/operation placeholders.
    verdict = triage.classify({}, {}, clock())
    need(verdict["state"] == "INDETERMINATE", "UNEXPECTED_TRIAGE_AUTHORITY")
    return {"schema": 1, "mode": "ADVISORY_ONLY", "verification": "NOT_VERIFIED",
            "origin": "HOST_CAPABILITIES_REQUIRE_EXTERNAL_EXECUTION_ATTESTATION",
            "game_id": project["game_id"], "repository": project["repository"],
            "main_sha": b["main_sha"], "observed_at": reader.started.isoformat(),
            "coordinator": {"ref_sha": b["coordinator_sha"], "blob_sha": b["coordinator_blob_sha"],
                            "epoch": b["coordinator_epoch"], "holder": holder,
                            "holder_service_binding": holder_binding},
            "services": services, "get_trace": reader.trace, "peek_trace": trace,
            "operation_evidence": {"status": "OPERATION_EVIDENCE_UNAVAILABLE", "verification": "NOT_VERIFIED",
                                   "service_prose_used_as_operation_receipt": False},
            "missing_triage_inputs": ["original_operation_receipt", "exact_pr_and_qa_observation"],
            "triage": verdict, "authority": deepcopy(DENIED)}


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise EvidenceError("INVALID_REQUEST")
    try:
        parser = SafeParser(description=__doc__)
        parser.add_argument("--request", required=True)
        args = parser.parse_args()
        request = loads(Path(args.request).read_text(encoding="utf-8"))
        need(type(request) is dict and set(request) == {"projects", "binding"}, "INVALID_REQUEST")
        def call(method, key, value):
            print(json.dumps({"method": method, key: value}), flush=True)
            response = loads(sys.stdin.readline())
            fields = {"status", "body"} if method == "GET" else {"ok", "body"}
            need(type(response) is dict and set(response) == fields, "INVALID_TRANSPORT_RESPONSE")
            return (github.Response(response["status"], response["body"]) if method == "GET" else
                    PeekResponse(response["ok"], response["body"]))
        result = observe(request["projects"], request["binding"], lambda url: call("GET", "url", url),
                         lambda task: call("PEEK", "task_id", task),
                         lambda: datetime.now(timezone.utc).isoformat())
        print(json.dumps({"result": result}, sort_keys=True), flush=True)
        return 0
    except Exception as exc:
        reason = str(exc) if isinstance(exc, EvidenceError) else "INVALID_OR_UNAVAILABLE_SERVICE_EVIDENCE"
        print(json.dumps({"verification": "NOT_VERIFIED", "reason": reason, "authority": DENIED}), flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
