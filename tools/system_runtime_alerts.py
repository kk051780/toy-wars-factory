"""Bounded A12 diagnostics over accepted read-only observers; no alert sender.

Caller JSON, matching digests and a Python callback never authenticate origin.
The host must separately attest connected calls. Reconciliation is provisional,
not a lease recovery, delivery receipt or permission to launch any service.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools import system_provider_transport as transport
from tools import system_incident_observer as incident
from tools import system_service_observer as service
from tools import system_github_evidence as github

EvidenceError, need, moment = github.EvidenceError, github.need, github.moment
DENIED = deepcopy(service.DENIED)
RULES = {"service_timeout_seconds", "ci_timeout_seconds", "max_observation_age_seconds", "replay_window_seconds"}
KINDS = {"OBSERVED_FAILED", "OBSERVED_NO_UPDATE", "STALE_OR_NO_RESULT", "SERVICE_DISABLED",
         "CURRENT_RESULT_REQUIRES_ATTENTION", "CI_TIMEOUT", "MAIN_QA_FAILED", "PR_QA_FAILED",
         "EXPIRED_LEASE_UNRELEASED", "CONNECTOR_UNAVAILABLE", "INDETERMINATE"}
IDENTITY = {"game_id", "repository", "kind", "subject"}
ALERT = {"id", "identity", "first_seen", "last_seen", "repeats", "status", "recovered", "evidence", "action"}
FRAME = {"schema", "mode", "verification", "game_id", "repository", "roles", "observed_at",
         "thresholds", "services", "lease", "ci", "alerts", "recovery_candidates", "authority",
         "delivery", "operation_cause", "a12_verified"}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _rules(value):
    need(type(value) is dict and set(value) == RULES, "INVALID_THRESHOLDS")
    bounds = value["service_timeout_seconds"]
    need(type(bounds) is dict and set(bounds) == set(service.ROLES) and
         all(github.integer(x, 60) and x <= 86400 for x in bounds.values()), "INVALID_THRESHOLDS")
    for key, lo, hi in (("ci_timeout_seconds", 60, 86400), ("max_observation_age_seconds", 1, 120),
                        ("replay_window_seconds", 1, 172800)):
        need(github.integer(value[key], lo) and value[key] <= hi, "INVALID_THRESHOLDS")
    return deepcopy(value)


def _project(projects, binding):
    games = service.scheduler._validated_games(deepcopy(projects))
    need(type(binding) is dict and set(binding) == {"github", "max_record_age_seconds", "max_window_seconds"},
         "INVALID_BINDING")
    b = binding["github"]
    need(type(b) is dict and set(b) == github.BINDING, "INVALID_BINDING")
    chosen = [p for p in games if p["game_id"] == b["game_id"]]
    need(len(chosen) == 1, "UNKNOWN_PROJECT")
    return chosen[0], b


def _frame(project, thresholds, now):
    return {"schema": 1, "mode": "READ_ONLY_A12_DIAGNOSTIC", "verification": "NOT_VERIFIED",
            "game_id": project["game_id"], "repository": project["repository"],
            "roles": deepcopy(project["roles"]), "observed_at": now.isoformat(), "thresholds": thresholds,
            "services": [], "lease": None, "ci": [], "alerts": [], "recovery_candidates": [],
            "authority": deepcopy(DENIED), "delivery": "NOT_ATTEMPTED",
            "operation_cause": "INDETERMINATE", "a12_verified": False}


def _add(frame, kind, subject, evidence):
    identity = {"game_id": frame["game_id"], "repository": frame["repository"], "kind": kind, "subject": subject}
    frame["alerts"].append({"id": _digest(identity), "identity": identity,
        "first_seen": frame["observed_at"], "last_seen": frame["observed_at"], "repeats": 1,
        "status": "OPEN", "recovered": False, "evidence": evidence,
        "action": "REGISTERED_REVIEW_REQUIRED_NO_RETRY_OR_TAKEOVER"})


def _denied(value):
    need(type(value) is dict and value == DENIED and all(v is False for v in value.values()), "FORGED_AUTHORITY")


def _ci(ci, expected_head, now):
    need(type(ci) is dict and github.integer(ci.get("id")) and github.integer(ci.get("attempt")) and
         ci.get("head") == expected_head, "WRONG_CI_BINDING")
    github.sha(expected_head)
    created, updated = moment(ci["created_at"]), moment(ci["updated_at"])
    need(created <= updated <= now, "INVALID_CI_CLOCK")
    jobs = ci.get("jobs")
    need(type(jobs) is list and len(jobs) == 2 and
         {j.get("name") for j in jobs} == {"offline", "compile_hold"}, "MISSING_OR_DUPLICATE_JOBS")
    ids = set()
    conclusions = {"success", "failure", "neutral", "cancelled", "skipped", "timed_out",
                   "action_required", "stale", "startup_failure"}
    for row in [ci] + jobs:
        status, conclusion = row.get("status"), row.get("conclusion")
        need(status in ("queued", "in_progress", "completed") and
             ((status == "completed" and conclusion in conclusions) or
              (status != "completed" and conclusion is None)), "CONTRADICTORY_CI_STATE")
    for job in jobs:
        need(github.integer(job.get("id")) and job["id"] not in ids and
             job.get("run_id") == ci["id"] and type(job["run_id"]) is int and
             job.get("run_attempt") == ci["attempt"] and type(job["run_attempt"]) is int and
             job.get("head_sha") == expected_head, "WRONG_JOB_BINDING")
        ids.add(job["id"])
    qa = ("PENDING" if ci["status"] != "completed" else "PASS" if ci["conclusion"] == "success" and
          all(j["status"] == "completed" and j["conclusion"] == "success" for j in jobs) else "FAIL")
    need(ci.get("qa") == qa, "CONTRADICTORY_QA")
    return qa, int((now-created).total_seconds())


def classify(projects, binding, report, thresholds, now):
    """Validate supplied observer output; remains NOT_VERIFIED even if valid."""
    try:
        return _classify(projects, binding, deepcopy(report), _rules(thresholds), moment(now))
    except EvidenceError:
        raise
    except Exception:
        raise EvidenceError("INVALID_A12_OBSERVATION") from None


def _classify(projects, binding, r, rules, now):
    p, b = _project(projects, binding)
    need(type(r) is dict and r.get("schema") == 1 and r.get("mode") == "ADVISORY_ONLY" and
         r.get("verification") == "NOT_VERIFIED" and r.get("game_id") == p["game_id"] and
         r.get("repository") == p["repository"] and r.get("main_sha") == b["main_sha"], "FOREIGN_OR_FAKE_REPORT")
    need(not (set(r) & {"provider_verified", "provider", "authenticated", "source_authentication"}), "FAKE_ATTESTATION")
    _denied(r["authority"])
    start, finish = moment(r["started_at"]), moment(r["finished_at"])
    need(start <= finish <= now and (finish-start).total_seconds() <= binding["max_window_seconds"] <= 120 and
         (now-finish).total_seconds() <= rules["max_observation_age_seconds"], "STALE_OR_FUTURE_OBSERVATION")
    frame = _frame(p, rules, now)
    need(type(r["services"]) is dict and set(r["services"]) == set(service.ROLES), "MISSING_OR_DUPLICATE_ROLE")
    seen, safe = set(), {}
    for role in service.ROLES:
        row = r["services"][role]
        raw = {"automations": [{"id": row["task_id"], "is_enabled": row["is_enabled"],
               "run_details": {"last_run": row["last_run"], "latest_result": row["latest_result_metadata"]}}]}
        checked = service.snapshot(json.dumps(raw), p["roles"][role], now, binding["max_record_age_seconds"])
        need(checked == row, "CONTRADICTORY_SERVICE_METADATA")
        ids = {row["last_run"]["id"]}
        if row["latest_result_metadata"]:
            ids.add(row["latest_result_metadata"]["run_id"])
        need(not seen & ids, "CROSS_ROLE_RUN_REUSE")
        seen.update(ids)
        safe[role] = checked
        traces = [t for t in r["peek_trace"] if t.get("task_id") == p["roles"][role]]
        need(len(traces) == 3 and all(t.get("method") == "PEEK" and t.get("metadata_sha256") ==
             hashlib.sha256(json.dumps(checked, sort_keys=True).encode()).hexdigest() and
             start <= moment(t["observed_at"]) <= finish for t in traces), "UNBOUND_SERVICE_TRACE")
        run = row["last_run"]
        age = int((now-moment(run["started_at"])).total_seconds())
        observed = row["observation_state"]
        state = {"FAILED": "OBSERVED_FAILED", "NO_UPDATE": "OBSERVED_NO_UPDATE",
                 "COMPLETED_WITH_CURRENT_RESULT": "OBSERVED_COMPLETED",
                 "CURRENT_RESULT_MISSING": "STALE_OR_NO_RESULT"}.get(observed, observed)
        if observed == "IN_PROGRESS":
            state = "STALE_OR_NO_RESULT" if age > rules["service_timeout_seconds"][role] else "IN_PROGRESS_NOT_YET_STALE"
        need(state in KINDS | {"OBSERVED_COMPLETED", "IN_PROGRESS_NOT_YET_STALE"}, "UNKNOWN_SERVICE_STATE")
        subject = {"role": role, "task_id": row["task_id"], "run_id": run["id"]}
        frame["services"].append({**subject, "state": state, "age_seconds": age,
                                  "latest_result_binding": row["latest_result_binding"]})
        if state in KINDS:
            _add(frame, state, subject, ["task/" + row["task_id"] + "/run/" + run["id"]])
    need(len(r["peek_trace"]) == 9, "DUPLICATE_PEEK_TRACE")
    coordinator = r["coordinator"]
    need(coordinator["ref_sha"] == b["coordinator_sha"] and coordinator["blob_sha"] == b["coordinator_blob_sha"] and
         type(coordinator["epoch"]) is int and coordinator["epoch"] == b["coordinator_epoch"], "WRONG_COORDINATOR")
    holder = coordinator["holder"]
    if holder is not None:
        need(holder["kind"] in (*service.ROLES.values(), "CONTROLLER", "DISPATCH") and
             type(holder["epoch"]) is int and holder["epoch"] == coordinator["epoch"], "WRONG_HOLDER")
        service.run_id(holder["owner_id"])
        acquired, expires = moment(holder["acquired_at"]), moment(holder["expires_at"])
        need(acquired <= start and 0 < (expires-acquired).total_seconds() <= 1800, "INVALID_LEASE")
        for role, kind in service.ROLES.items():
            if holder["kind"] == kind:
                need(holder["task_id"] == p["roles"][role], "WRONG_HOLDER_TASK")
            if holder["owner_id"] == safe[role]["last_run"]["id"]:
                need(holder["kind"] == kind, "HOLDER_ROLE_COLLISION")
        state = "ACTIVE_LEASE" if now < expires else "EXPIRED_LEASE_UNRELEASED"
        frame["lease"] = {"state": state, "epoch": holder["epoch"], "owner_run_id": holder["owner_id"]}
        if state in KINDS:
            _add(frame, state, {"epoch": holder["epoch"], "owner_run_id": holder["owner_id"]},
                 [p["repository"] + "/git/" + b["coordinator_sha"] + "/blob/" + b["coordinator_blob_sha"]])
    pr = r["pr"]
    need(pr["state"] == "open" and type(pr["number"]) is int and pr["number"] == b["pr_number"] and
         pr["head"] == b["pr_head_sha"] and pr["base"] == b["pr_base_sha"] and
         pr["branch"].endswith(b["author_run_id"]) and b["author_role"] in ("author", "meta"), "WRONG_PR")
    service.run_id(b["author_run_id"])
    need(pr["ci"]["id"] == b["ci_run_id"] and pr["ci"]["attempt"] == b["ci_attempt"], "STALE_PR_CI")
    prefix = "https://api.github.com/repos/" + p["repository"]
    paths = {"/git/ref/heads/main", "/git/ref/heads/" + p["coordination_ref"],
             "/pulls/" + str(pr["number"])}
    for name, ci, head in (("main", r["main_ci"], r["main_ci"]["head"]), ("pr", pr["ci"], pr["head"])):
        qa, age = _ci(ci, head, now)
        if name == "main":
            changes = r["status_only"]
            need(type(changes) is list and len(changes) == len(set(changes)) and
                 set(changes) <= {"status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"} and
                 ((head == b["main_sha"] and not changes) or head != b["main_sha"] and changes and qa == "PASS"),
                 "UNPROVEN_MAIN_QA")
            if head != b["main_sha"]:
                paths.add("/compare/" + head + "..." + b["main_sha"])
        state = "QA_PASS" if qa == "PASS" else ("MAIN_QA_FAILED" if name == "main" else "PR_QA_FAILED")
        if qa == "PENDING":
            # Accepted observer has no attempt-specific start timestamp. Never
            # mistake original created_at for the start of a later rerun.
            state = ("INDETERMINATE" if ci["attempt"] != 1 else "CI_TIMEOUT" if age > rules["ci_timeout_seconds"]
                     else "CI_RUNNING_IN_WINDOW")
        subject = {"target": name, "head": head, "run_id": ci["id"], "attempt": ci["attempt"]}
        if name == "pr":
            subject.update(pr_number=pr["number"], author_role=b["author_role"],
                           task_id=p["roles"][b["author_role"]], producing_run_id=b["author_run_id"])
        frame["ci"].append({**subject, "state": state, "age_seconds": age})
        paths.add(f"/actions/runs/{ci['id']}/attempts/{ci['attempt']}/jobs?per_page=100")
        paths.add("/actions/runs/" + str(ci["id"]) if name == "pr" else
                  "/actions/runs?branch=main&event=push&per_page=100")
        if state in KINDS:
            _add(frame, state, subject, [prefix + "/actions/runs/" + str(ci["id"])])
    trace = r["get_trace"]
    need(type(trace) is list and trace and all(t.get("method") == "GET" and
         type(t.get("url")) is str and (t["url"] == prefix or t["url"].startswith(prefix + "/")) and
         type(t.get("body_sha256")) is str and github.re.fullmatch(r"[0-9a-f]{64}", t["body_sha256"]) and
         start <= moment(t["observed_at"]) <= finish for t in trace), "INVALID_GET_TRACE")
    need({prefix + x for x in paths}.issubset({t["url"] for t in trace}), "MISSING_BOUND_TRACE")
    need(r["operation_evidence"]["status"] == "OPERATION_EVIDENCE_UNAVAILABLE" and
         r["operation_evidence"]["verification"] == "NOT_VERIFIED", "FAKE_OPERATION_RECEIPT")
    frame["alerts"].sort(key=lambda a: a["id"])
    return frame


def _validate_frame(frame, now):
    need(type(frame) is dict and set(frame) == FRAME and type(frame["schema"]) is int and frame["schema"] == 1 and
         frame["mode"] == "READ_ONLY_A12_DIAGNOSTIC" and frame["verification"] == "NOT_VERIFIED" and
         frame["delivery"] == "NOT_ATTEMPTED" and frame["operation_cause"] == "INDETERMINATE" and
         frame["a12_verified"] is False, "INVALID_PRIOR_STATE")
    _denied(frame["authority"])
    _rules(frame["thresholds"])
    roles = frame["roles"]
    need(type(roles) is dict and set(roles) == set(service.ROLES) and
         all(type(t) is str and github.re.fullmatch(r"[0-9a-f]{32}", t) for t in roles.values()) and
         len(set(roles.values())) == 3 and type(frame["game_id"]) is str and
         github.re.fullmatch(r"[A-Za-z0-9_-]+", frame["game_id"]) and
         type(frame["repository"]) is str and github.re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", frame["repository"]),
         "INVALID_FRAME_SCOPE")
    need(type(frame["services"]) is list and len(frame["services"]) in (0, 3) and
         type(frame["ci"]) is list and len(frame["ci"]) in (0, 2), "INVALID_FRAME_OBSERVATIONS")
    for row in frame["services"]:
        need(type(row) is dict and set(row) == {"role", "task_id", "run_id", "state", "age_seconds", "latest_result_binding"} and
             row["role"] in roles and row["task_id"] == roles[row["role"]] and
             row["state"] in KINDS | {"OBSERVED_COMPLETED", "IN_PROGRESS_NOT_YET_STALE"} and
             github.integer(row["age_seconds"], 0) and row["latest_result_binding"] in ("MISSING", "PREVIOUS_RUN", "CURRENT_RUN"),
             "INVALID_FRAME_SERVICE")
        service.run_id(row["run_id"])
    need(len({r["role"] for r in frame["services"]}) == len(frame["services"]), "DUPLICATE_FRAME_SERVICE")
    for row in frame["ci"]:
        fields = {"target", "head", "run_id", "attempt", "state", "age_seconds"}
        need(type(row) is dict and row.get("target") in ("main", "pr"), "INVALID_FRAME_CI")
        if row["target"] == "pr": fields |= {"pr_number", "author_role", "task_id", "producing_run_id"}
        need(set(row) == fields and row["state"] in ("QA_PASS", "CI_RUNNING_IN_WINDOW", "CI_TIMEOUT", "MAIN_QA_FAILED", "PR_QA_FAILED", "INDETERMINATE") and
             github.integer(row["age_seconds"], 0), "INVALID_FRAME_CI")
        _subject({k: v for k, v in row.items() if k not in ("state", "age_seconds")}, "CI_TIMEOUT", frame)
    need(len({r["target"] for r in frame["ci"]}) == len(frame["ci"]), "DUPLICATE_FRAME_CI")
    if frame["lease"] is not None:
        lease = frame["lease"]
        need(type(lease) is dict and set(lease) == {"state", "epoch", "owner_run_id"} and
             lease["state"] in ("ACTIVE_LEASE", "EXPIRED_LEASE_UNRELEASED"), "INVALID_FRAME_LEASE")
        _subject({k: v for k, v in lease.items() if k != "state"}, "EXPIRED_LEASE_UNRELEASED", frame)
    at = moment(frame["observed_at"])
    need(at <= now and (now-at).total_seconds() <= frame["thresholds"]["replay_window_seconds"], "REPLAY_WINDOW_EXCEEDED")
    need(type(frame["alerts"]) is list and len(frame["alerts"]) <= 100 and
         type(frame["recovery_candidates"]) is list and len(frame["recovery_candidates"]) <= 100, "INVALID_ALERTS")
    seen = set()
    for alert in frame["alerts"] + frame["recovery_candidates"]:
        need(type(alert) is dict and set(alert) == ALERT and alert["recovered"] is False and
             alert["status"] in ("OPEN", "UNVERIFIED_RECOVERY_CANDIDATE", "RECOVERY_UNASSESSABLE") and
             alert["action"] == "REGISTERED_REVIEW_REQUIRED_NO_RETRY_OR_TAKEOVER", "FORGED_RECOVERY")
        ident = alert["identity"]
        need(type(ident) is dict and set(ident) == IDENTITY and ident["kind"] in KINDS and
             ident["game_id"] == frame["game_id"] and ident["repository"] == frame["repository"] and
             type(ident["subject"]) is dict and alert["id"] == _digest(ident) and alert["id"] not in seen,
             "DUPLICATE_OR_FORGED_ALERT")
        seen.add(alert["id"])
        need(moment(alert["first_seen"]) <= moment(alert["last_seen"]) <= at and
             github.integer(alert["repeats"]) and type(alert["evidence"]) is list and len(alert["evidence"]) <= 8 and
             all(_safe_evidence(x, frame) for x in alert["evidence"]), "INVALID_ALERT_HISTORY")
        need((alert in frame["alerts"]) == (alert["status"] == "OPEN"), "CONTRADICTORY_ALERT_LIST")
        _subject(ident["subject"], ident["kind"], frame)


def _safe_evidence(text, frame):
    if type(text) is not str or len(text) > 512:
        return False
    repo = github.re.escape(frame["repository"])
    return bool(text == "INDETERMINATE_PROVIDER_OR_BINDING_FAILURE" or
                github.re.fullmatch(r"task/[0-9a-f]{32}/run/[0-9a-f-]{36}", text) or
                github.re.fullmatch(repo + r"/git/[0-9a-f]{40}/blob/[0-9a-f]{40}", text) or
                github.re.fullmatch(r"https://api[.]github[.]com/repos/" + repo + r"/actions/runs/[0-9]+", text))


def _subject(subject, kind, frame):
    need(type(subject) is dict, "INVALID_ALERT_SUBJECT")
    if kind == "CONNECTOR_UNAVAILABLE":
        need(subject == {"game_id": frame["game_id"]}, "INVALID_ALERT_SUBJECT")
    elif kind == "EXPIRED_LEASE_UNRELEASED":
        need(set(subject) == {"epoch", "owner_run_id"} and github.integer(subject["epoch"], 0), "INVALID_ALERT_SUBJECT")
        service.run_id(subject["owner_run_id"])
    elif kind in ("CI_TIMEOUT", "MAIN_QA_FAILED", "PR_QA_FAILED", "INDETERMINATE"):
        fields = {"target", "head", "run_id", "attempt"}
        need(subject.get("target") in ("main", "pr"), "INVALID_CI_SUBJECT")
        if subject["target"] == "pr":
            fields |= {"pr_number", "author_role", "task_id", "producing_run_id"}
            need(subject["author_role"] in ("author", "meta") and
                 subject["task_id"] == frame["roles"][subject["author_role"]] and github.integer(subject["pr_number"]), "FOREIGN_PRIOR_TASK")
            service.run_id(subject["producing_run_id"])
        need(set(subject) == fields and github.integer(subject["run_id"]) and github.integer(subject["attempt"]), "INVALID_CI_SUBJECT")
        github.sha(subject["head"])
    else:
        need(set(subject) == {"role", "task_id", "run_id"} and subject["role"] in frame["roles"] and
             subject["task_id"] == frame["roles"][subject["role"]], "FOREIGN_PRIOR_TASK")
        service.run_id(subject["run_id"])


def reconcile(previous, current):
    """Pure provisional dedup; prior JSON is never authenticated persistence."""
    now = moment(current["observed_at"])
    _validate_frame(current, now)
    need(not current["recovery_candidates"], "CURRENT_MUST_BE_FRESH_OBSERVATION")
    out = deepcopy(current)
    if previous is None:
        return out
    _validate_frame(previous, now)
    need(all(previous[k] == current[k] for k in ("game_id", "repository", "roles", "thresholds")), "FOREIGN_PRIOR_STATE")
    need(moment(previous["observed_at"]) < now, "REPLAYED_OR_BACKWARD_OBSERVATION")
    prior = {a["id"]: a for a in previous["alerts"] + previous["recovery_candidates"]}
    current_ids = {a["id"] for a in current["alerts"]}
    for alert in out["alerts"]:
        if alert["id"] in prior:
            old = prior[alert["id"]]
            alert.update(first_seen=old["first_seen"], repeats=old["repeats"] + 1)
    uncertain = any(a["identity"]["kind"] in ("CONNECTOR_UNAVAILABLE", "INDETERMINATE") for a in current["alerts"])
    for key, old in sorted(prior.items()):
        if key not in current_ids:
            candidate = deepcopy(old)
            candidate["status"] = "RECOVERY_UNASSESSABLE" if uncertain else "UNVERIFIED_RECOVERY_CANDIDATE"
            out["recovery_candidates"].append(candidate)
    need(len(out["alerts"]) + len(out["recovery_candidates"]) <= 100, "ALERT_CAPACITY_EXCEEDED")
    return out


def observe(projects, binding, thresholds, get, peek, clock, *, previous=None):
    """Run the accepted transport/incident code; external host attests live use."""
    p, _ = _project(projects, binding)
    rules = _rules(thresholds)
    started = moment(clock())
    try:
        result = transport.observe(projects, binding, get, peek, clock, collector="incident")
        frame = classify(projects, binding, result["observation"], rules, clock())
    except Exception:
        # 403/404, unknown exception, ref/head drift or missing jobs cannot be
        # diagnosed as host write denial. Never echo the raw exception/body.
        frame = _frame(p, rules, started)
        _add(frame, "CONNECTOR_UNAVAILABLE", {"game_id": p["game_id"]},
             ["INDETERMINATE_PROVIDER_OR_BINDING_FAILURE"])
    return reconcile(previous, frame)


def main():
    try:
        class Parser(argparse.ArgumentParser):
            def error(self, message):
                raise EvidenceError("INVALID_REQUEST")
        parser = Parser(description=__doc__)
        parser.add_argument("--request", required=True)
        row = github.loads(Path(parser.parse_args().request).read_text(encoding="utf-8"))
        need(type(row) is dict and set(row) == {"projects", "binding", "thresholds", "previous"}, "INVALID_REQUEST")
        def call(method, key, value):
            print(json.dumps({"method": method, key: value}), flush=True)
            response = github.loads(sys.stdin.readline())
            need(type(response) is dict and set(response) == ({"status", "body"} if method == "GET" else {"ok", "body"}), "INVALID_RESPONSE")
            return (github.Response(response["status"], response["body"]) if method == "GET" else
                    service.PeekResponse(response["ok"], response["body"]))
        result = observe(row["projects"], row["binding"], row["thresholds"],
                         lambda u: call("GET", "url", u), lambda t: call("PEEK", "task_id", t),
                         lambda: datetime.now(timezone.utc).isoformat(), previous=row["previous"])
        print(json.dumps({"result": result}, sort_keys=True), flush=True)
        return 0
    except Exception:
        print(json.dumps({"state": "INDETERMINATE", "verification": "NOT_VERIFIED", "authority": DENIED}), flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
