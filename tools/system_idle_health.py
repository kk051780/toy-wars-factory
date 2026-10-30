"""PR-less A12 diagnostics over the accepted service observer, never authority.

Matching JSON, digests or callbacks are not provider authentication. No Git
write, task launch, notification, automatic recovery or main-QA claim exists.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools import system_service_observer as service
from tools import system_runtime_alerts as runtime

github = service.github
need, moment, EvidenceError = github.need, github.moment, github.EvidenceError
REPORT = {"schema", "mode", "verification", "origin", "game_id", "repository", "main_sha",
          "observed_at", "coordinator", "services", "get_trace", "peek_trace", "operation_evidence",
          "missing_triage_inputs", "triage", "authority"}
OUTPUT = {"schema", "mode", "verification", "game_id", "repository", "main_qa", "delivery",
          "a12_verified", "operation_cause", "state", "frame", "authority"}


def _project(projects, binding):
    need(type(binding) is dict and set(binding) == service.FIELDS, "INVALID_IDLE_BINDING")
    need(github.integer(binding["max_record_age_seconds"]) and binding["max_record_age_seconds"] <= 172800 and
         github.integer(binding["coordinator_epoch"], 0), "INVALID_IDLE_LIMITS")
    for key in ("main_sha", "coordinator_sha", "coordinator_blob_sha"):
        github.sha(binding[key])
    need(type(binding["manifest_path"]) is str and github.re.fullmatch(
        r"studio_autopilot/projects/[A-Za-z0-9_]+[.]json", binding["manifest_path"]), "INVALID_MANIFEST")
    games = service.scheduler._validated_games(deepcopy(projects))
    chosen = [p for p in games if p["game_id"] == binding["game_id"]]
    need(len(chosen) == 1, "UNKNOWN_PROJECT")
    return chosen[0]


def _output(project, frame, previous=None):
    if previous is not None:
        need(type(previous) is dict and set(previous) == OUTPUT and previous["mode"] == "PR_LESS_READ_ONLY" and
             previous["verification"] == "NOT_VERIFIED" and previous["main_qa"] == "MAIN_QA_NOT_CHECKED" and
             previous["delivery"] == "NOT_ATTEMPTED" and previous["a12_verified"] is False and
             previous["operation_cause"] == "INDETERMINATE" and
             all(previous[k] == project[k] for k in ("game_id", "repository")), "INVALID_PRIOR_IDLE_REPORT")
        runtime._denied(previous["authority"])
    frame = runtime.reconcile(None if previous is None else previous["frame"], frame)
    state = ("INDETERMINATE" if any(a["identity"]["kind"] in ("CONNECTOR_UNAVAILABLE", "INDETERMINATE")
             for a in frame["alerts"]) else "ATTENTION_REQUIRED" if frame["alerts"] else "OBSERVED_HEALTHY")
    return {"schema": 1, "mode": "PR_LESS_READ_ONLY", "verification": "NOT_VERIFIED",
            "game_id": project["game_id"], "repository": project["repository"], "main_qa": "MAIN_QA_NOT_CHECKED",
            "delivery": "NOT_ATTEMPTED", "a12_verified": False, "operation_cause": "INDETERMINATE",
            "state": state, "frame": frame, "authority": deepcopy(service.DENIED)}


def classify(projects, binding, report, thresholds, observed_at, previous=None):
    """Pure supplied-data validation. NOT_VERIFIED is never upgraded by hashes."""
    try:
        return _classify(projects, binding, deepcopy(report), runtime._rules(thresholds), moment(observed_at), previous)
    except EvidenceError:
        raise
    except Exception:
        raise EvidenceError("INVALID_IDLE_OBSERVATION") from None


def _classify(projects, b, r, rules, now, previous):
    p = _project(projects, b)
    need(type(r) is dict and set(r) == REPORT and type(r["schema"]) is int and r["schema"] == 1 and
         r["mode"] == "ADVISORY_ONLY" and r["verification"] == "NOT_VERIFIED" and
         r["game_id"] == p["game_id"] and r["repository"] == p["repository"] and r["main_sha"] == b["main_sha"],
         "UNBOUND_IDLE_REPORT")
    runtime._denied(r["authority"])
    at = moment(r["observed_at"])
    need(at <= now and (now-at).total_seconds() <= rules["max_observation_age_seconds"], "STALE_IDLE_OBSERVATION")
    frame, seen, safe = runtime._frame(p, rules, now), set(), {}
    need(type(r["services"]) is dict and set(r["services"]) == set(service.ROLES) and
         type(r["peek_trace"]) is list and len(r["peek_trace"]) == 6, "MISSING_OR_DUPLICATE_ROLES")
    for role in service.ROLES:
        row = r["services"][role]
        raw = {"automations": [{"id": row["task_id"], "is_enabled": row["is_enabled"], "run_details":
               {"last_run": row["last_run"], "latest_result": row["latest_result_metadata"]}}]}
        checked = service.snapshot(json.dumps(raw), p["roles"][role], now, b["max_record_age_seconds"])
        need(checked == row, "CONTRADICTORY_SERVICE_STATE")
        ids = {row["last_run"]["id"]}
        if row["latest_result_metadata"]: ids.add(row["latest_result_metadata"]["run_id"])
        need(not seen & ids, "DUPLICATE_SERVICE_RUN")
        seen.update(ids); safe[role] = row
        traces = [t for t in r["peek_trace"] if t.get("task_id") == p["roles"][role]]
        digest = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        need(len(traces) == 2 and all(t.get("method") == "PEEK" and t.get("metadata_sha256") == digest and
             at <= moment(t["observed_at"]) <= now for t in traces), "UNBOUND_PEEK_TRACE")
        age = int((now-moment(row["last_run"]["started_at"])).total_seconds())
        state = {"FAILED": "OBSERVED_FAILED", "NO_UPDATE": "OBSERVED_NO_UPDATE",
                 "CURRENT_RESULT_MISSING": "STALE_OR_NO_RESULT", "COMPLETED_WITH_CURRENT_RESULT": "OBSERVED_COMPLETED"}.get(
                     row["observation_state"], row["observation_state"])
        if state == "IN_PROGRESS":
            state = "STALE_OR_NO_RESULT" if age > rules["service_timeout_seconds"][role] else "IN_PROGRESS_NOT_YET_STALE"
        subject = {"role": role, "task_id": row["task_id"], "run_id": row["last_run"]["id"]}
        frame["services"].append({**subject, "state": state, "age_seconds": age,
                                  "latest_result_binding": row["latest_result_binding"]})
        if state in runtime.KINDS:
            runtime._add(frame, state, subject, ["task/" + row["task_id"] + "/run/" + subject["run_id"]])
    coord = r["coordinator"]
    need(coord["ref_sha"] == b["coordinator_sha"] and coord["blob_sha"] == b["coordinator_blob_sha"] and
         type(coord["epoch"]) is int and coord["epoch"] == b["coordinator_epoch"], "WRONG_COORDINATOR")
    h = coord["holder"]
    if h is not None:
        need(h["kind"] in (*service.ROLES.values(), "CONTROLLER", "DISPATCH") and
             type(h["epoch"]) is int and h["epoch"] == coord["epoch"], "INVALID_HOLDER")
        service.run_id(h["owner_id"])
        acquired, expires = moment(h["acquired_at"]), moment(h["expires_at"])
        need(acquired <= at and 0 < (expires-acquired).total_seconds() <= 1800, "INVALID_LEASE")
        state = "ACTIVE_LEASE" if now < expires else "EXPIRED_LEASE_UNRELEASED"
        frame["lease"] = {"state": state, "epoch": h["epoch"], "owner_run_id": h["owner_id"]}
        for role, kind in service.ROLES.items():
            if h["kind"] == kind: need(h["task_id"] == p["roles"][role], "WRONG_HOLDER_TASK")
            if h["owner_id"] == safe[role]["last_run"]["id"]:
                need(h["kind"] == kind, "HOLDER_ROLE_COLLISION")
                # UUID equality is identity only, not a valid claim timeline.
                # Keep expiry evidence; uncertain provider/binding data never looks healthy.
                if moment(safe[role]["last_run"]["started_at"]) > acquired:
                    runtime._add(frame, "CONNECTOR_UNAVAILABLE", {"game_id": p["game_id"]},
                                 ["task/" + p["roles"][role] + "/run/" + h["owner_id"],
                                  p["repository"] + "/git/" + b["coordinator_sha"] + "/blob/" + b["coordinator_blob_sha"]])
                if safe[role]["last_run"]["recorded_status"] in service.TERMINAL:
                    subject = {"role": role, "task_id": p["roles"][role], "run_id": h["owner_id"]}
                    if not any(a["identity"]["subject"] == subject and a["identity"]["kind"] == "STALE_OR_NO_RESULT" for a in frame["alerts"]):
                        runtime._add(frame, "STALE_OR_NO_RESULT", subject, ["task/" + p["roles"][role] + "/run/" + h["owner_id"]])
        if state == "EXPIRED_LEASE_UNRELEASED":
            runtime._add(frame, state, {"epoch": h["epoch"], "owner_run_id": h["owner_id"]},
                         [p["repository"] + "/git/" + b["coordinator_sha"] + "/blob/" + b["coordinator_blob_sha"]])
    prefix = "https://api.github.com/repos/" + p["repository"]
    trace = r["get_trace"]
    need(type(trace) is list and trace and all(t.get("method") == "GET" and type(t.get("url")) is str and
         (t["url"] == prefix or t["url"].startswith(prefix + "/git/") and
          github.re.fullmatch(r"/(?:ref/heads/[A-Za-z0-9_-]+|commits/[0-9a-f]{40}|trees/[0-9a-f]{40}[?]recursive=1|blobs/[0-9a-f]{40})",t["url"][len(prefix + "/git"):])) and
         type(t.get("body_sha256")) is str and github.re.fullmatch(r"[0-9a-f]{64}", t["body_sha256"]) and
         at <= moment(t["observed_at"]) <= now for t in trace), "INVALID_GET_TRACE")
    required = {prefix + "/git/ref/heads/main", prefix + "/git/ref/heads/" + p["coordination_ref"],
                prefix + "/git/blobs/" + b["coordinator_blob_sha"]}
    need(required <= {t["url"] for t in trace}, "MISSING_PINNED_GET")
    need(r["operation_evidence"]["status"] == "OPERATION_EVIDENCE_UNAVAILABLE" and
         r["operation_evidence"]["verification"] == "NOT_VERIFIED", "FAKE_HOST_RECEIPT")
    return _output(p, frame, previous)


def observe(projects, binding, thresholds, get, peek, clock, previous=None):
    """PR-less accepted observer invocation; detector outages never look healthy."""
    p, rules, now = _project(projects, binding), runtime._rules(thresholds), moment(clock())
    try:
        def checked_peek(task):
            response = peek(task)
            need(type(response) is service.PeekResponse and response.ok is True, "PEEK_REJECTED")
            envelope = github.loads(response.text)
            layers = [envelope]
            if type(envelope) is dict and "structuredContent" in envelope:
                need("automations" not in envelope, "AMBIGUOUS_PEEK")
                layers.append(envelope["structuredContent"])
            need(all(type(x) is dict and x.get("isError", False) is False and x.get("status") != "ERROR" and
                     x.get("error_code") is None for x in layers), "PEEK_ERROR")
            return response
        report = service.observe(projects, binding, get, checked_peek, clock)
        return classify(projects, binding, report, rules, clock(), previous)
    except Exception:
        frame = runtime._frame(p, rules, now)
        runtime._add(frame, "CONNECTOR_UNAVAILABLE", {"game_id": p["game_id"]},
                     ["INDETERMINATE_PROVIDER_OR_BINDING_FAILURE"])
        return _output(p, frame, previous)
