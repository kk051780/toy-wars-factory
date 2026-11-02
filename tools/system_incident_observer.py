"""Join scoped GitHub and service observations, with no execution authority.

Only a trusted host's external call trace can attest a live execution. Callbacks,
stdin, matching hashes and this module's output are NOT origin authentication.
No credentials, network client, task mutation, Git writes or retry loop exist.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from studio_autopilot import core
from tools import system_github_evidence as github
from tools import system_service_observer as service
from tools import system_host_write_triage_v2 as triage

EvidenceError, need = github.EvidenceError, github.need
DENIED = deepcopy(service.DENIED)


def _projection(report):
    return {k: v for k, v in report.items()
            if k not in ("observed_at", "get_trace", "peek_trace")}


def _triage(project, g, s, binding, now):
    """Adapt collected metadata to the accepted v2; never invent an operation."""
    role = binding["author_role"]
    svc = s["services"][role]
    task, run = project["roles"][role], svc["last_run"]["id"]
    repo, branch = project["repository"], project["coordination_ref"]
    kinds = {"service": "EXISTING_SERVICE_PEEK", "lock": "SCOPED_GITHUB_GET",
             "pr": "SCOPED_GITHUB_GET", "ci": "SCOPED_GITHUB_GET"}
    def at(path):
        return [x["observed_at"] for x in g["trace"] if x["url"].endswith(path)][-1]
    def envelope(kind, locator, data, observed):
        return {"source": {"kind": kind, "provider": kinds[kind],
                           "locator": locator, "observed_at": observed}, "data": data}
    def service_envelope(row, task_id):
        observed = [x["observed_at"] for x in s["peek_trace"] if x["task_id"] == task_id][-1]
        report = row["latest_result_metadata"] if row["latest_result_binding"] == "CURRENT_RUN" else None
        return envelope("service", "task/" + task_id,
                        {"task_id": task_id, "last_run": row["last_run"], "latest_result": report}, observed)
    pr, ci = g["pr"], g["pr"]["ci"]
    evidence = {"schema": 1, "repository": repo, "task_id": task, "run_id": run,
        "work_branch": pr["branch"], "service": service_envelope(svc, task),
        "lock": envelope("lock", repo + "/git/ref/heads/" + branch,
            {"repository": repo, "branch": branch, "head": g["coordinator"]["ref_sha"],
             "epoch": g["coordinator"]["epoch"], "holder": g["coordinator"]["holder"]},
            at("/git/ref/heads/" + branch)),
        "pr": envelope("pr", repo + "/pulls/" + str(pr["number"]),
            {"repository": repo, "number": pr["number"], "state": pr["state"], "branch": pr["branch"],
             "head": pr["head"], "base": pr["base"], "producing_run_id": binding["author_run_id"],
             "latest_qa_run_id": ci["id"], "latest_qa_attempt": ci["attempt"]}, at("/pulls/" + str(pr["number"]))),
        "ci": envelope("ci", repo + "/actions/runs/" + str(ci["id"]),
            {"repository": repo, "pr_number": pr["number"], "id": ci["id"], "attempt": ci["attempt"],
             "head": ci["head"], "base": pr["base"], "status": ci["status"], "conclusion": ci["conclusion"],
             "jobs": [{"name": j["name"], "run_id": j["run_id"], "attempt": j["run_attempt"],
                       "head": j["head_sha"], "status": j["status"], "conclusion": j["conclusion"]}
                      for j in ci["jobs"]]}, at("/actions/runs/" + str(ci["id"])))}
    holder = g["coordinator"]["holder"]
    if holder is not None:
        for r, kind in service.ROLES.items():
            current = s["services"][r]
            if (holder["kind"] == kind and holder["owner_id"] == current["last_run"]["id"] and
                    holder["task_id"] == project["roles"][r]):
                evidence["holder_service"] = service_envelope(current, project["roles"][r])
    config = {"repository": repo, "task_id": task, "control_branch": branch,
              "max_age_seconds": 120, "max_lease_seconds": 1800,
              "required_jobs": ["offline", "compile_hold"], "providers": kinds,
              "registered_tasks": {kind: project["roles"][r] for r, kind in service.ROLES.items()}}
    verdict = triage.classify(evidence, config, now)
    # Successful service/QA alone cannot establish health or an operation result.
    if verdict["state"] == "SAFE_TO_NEXT_SCHEDULE":
        verdict = triage.legacy.result("INDETERMINATE", "ORIGINAL_OPERATION_EVIDENCE_UNAVAILABLE")
    return verdict


def observe(projects, binding, get, peek, clock):
    try:
        return _observe(projects, deepcopy(binding), get, peek, clock)
    except EvidenceError:
        raise
    except Exception:
        raise EvidenceError("INVALID_OR_UNAVAILABLE_INCIDENT_EVIDENCE") from None


def _observe(projects, b, get, peek, clock):
    need(type(b) is dict and set(b) == {"github", "max_record_age_seconds", "max_window_seconds"}, "INVALID_INCIDENT_BINDING")
    need(type(b["github"]) is dict and set(b["github"]) == github.BINDING, "INVALID_BINDING")
    need(github.integer(b["max_window_seconds"]) and b["max_window_seconds"] <= 120, "INVALID_WINDOW")
    start = previous = github.moment(clock())
    def bounded_clock():
        nonlocal previous
        current = github.moment(clock())
        need(previous <= current and (current-start).total_seconds() <= b["max_window_seconds"], "INCIDENT_WINDOW_EXCEEDED")
        previous = current
        return current.isoformat()
    games = service.scheduler._validated_games(deepcopy(projects))
    selected = [p for p in games if p["game_id"] == b["github"]["game_id"]]
    need(len(selected) == 1, "UNKNOWN_PROJECT")
    project, pins = selected[0], b["github"]
    prefix = "https://api.github.com/repos/" + project["repository"]
    mutable, immutable, trace, cache_hits = {}, {}, [], []
    def checked_get(url):
        bounded_clock()
        need(type(url) is str and url.startswith(prefix + "/") or url == prefix, "FOREIGN_GET")
        path = url[len(prefix):]
        need(path == "" or re.fullmatch(r"/git/(?:ref/heads/[A-Za-z0-9_-]+|commits/[0-9a-f]{40}|trees/[0-9a-f]{40}[?]recursive=1|blobs/[0-9a-f]{40})", path) or
             re.fullmatch(r"/pulls/[0-9]+", path) or re.fullmatch(r"/actions/runs(?:/[0-9]+(?:/attempts/[0-9]+/jobs[?]per_page=100)?|[?](?:head_sha=[0-9a-f]{40}&event=pull_request|branch=main&event=push)&per_page=100)", path) or
             re.fullmatch(r"/compare/[0-9a-f]{40}[.]{3}[0-9a-f]{40}", path), "UNSCOPED_GET")
        # Only content-addressed Git objects may be reused within this call.
        # Mutable refs, PRs, runs and jobs ALWAYS reach the host again. Readers
        # still validate each object's pins/blob hash. A cache is not provenance.
        object_path = bool(re.fullmatch(r"/git/(?:commits/[0-9a-f]{40}|trees/[0-9a-f]{40}[?]recursive=1|blobs/[0-9a-f]{40})", path))
        if object_path and url in immutable:
            cache_hits.append({"url": url, "reused_at": bounded_clock(), "origin": "SAME_CALL_IMMUTABLE_OBJECT_CACHE"})
            return immutable[url]
        response = get(url)
        at = bounded_clock()
        need(type(response) is github.Response and type(response.status) is int and response.status == 200, "GET_REJECTED")
        if object_path:
            immutable[url] = response
        is_mutable = path == "" or path.startswith(("/git/ref/", "/pulls/", "/actions/"))
        if is_mutable:
            value = github.loads(response.text)
            if url in mutable:
                need(value == mutable[url], "CROSS_CHANNEL_GITHUB_DRIFT")
            else:
                mutable[url] = value
        trace.append({"method": "GET", "url": url, "observed_at": at,
                      "body_sha256": hashlib.sha256(response.text.encode()).hexdigest()})
        return response
    def checked_peek(task):
        bounded_clock()
        need(task in project["roles"].values(), "FOREIGN_TASK")
        response = peek(task)
        bounded_clock()
        return response
    sb = {k: pins[k] for k in service.FIELDS if k != "max_record_age_seconds"}
    sb["max_record_age_seconds"] = b["max_record_age_seconds"]
    before = service.observe(games, sb, checked_get, checked_peek, bounded_clock)
    report = github.collect(games, pins, checked_get, bounded_clock)
    # The accepted service observer already reads every role twice. Add one
    # final read after GitHub/QA, rather than repeating all immutable bindings
    # and a fourth peek. Every service thus has THREE actual reads, all inside
    # one window. No earlier metadata is presented as a new provider response.
    after = deepcopy(before)
    after["peek_trace"] = []
    for role in service.ROLES:
        task = project["roles"][role]
        response = checked_peek(task)
        at = bounded_clock()
        need(type(response) is service.PeekResponse and response.ok is True, "PEEK_REJECTED")
        safe = service.snapshot(response.text, task, github.moment(at), b["max_record_age_seconds"])
        after["services"][role] = safe
        after["peek_trace"].append({"method": "PEEK", "task_id": task, "observed_at": at,
            "metadata_sha256": hashlib.sha256(json.dumps(safe, sort_keys=True).encode()).hexdigest()})
    need(_projection(before) == _projection(after), "CROSS_CHANNEL_SERVICE_DRIFT")
    # Reread mutable GETs including BOTH attempt job lists. An unchanged run
    # object does not make a changed job list safe. Immutable blobs need no replay.
    for url in tuple(mutable):
        checked_get(url)
    finished = bounded_clock()
    producing_run, author_role = pins["author_run_id"], pins["author_role"]
    for r, row in after["services"].items():
        ids = {row["last_run"]["id"]}
        if row["latest_result_metadata"]:
            ids.add(row["latest_result_metadata"]["run_id"])
        need(r == author_role or producing_run not in ids, "PR_AUTHOR_RUN_ROLE_COLLISION")
    author = after["services"][author_role]
    association = ("CURRENT_SERVICE_RUN" if producing_run == author["last_run"]["id"] else
                   "PREVIOUS_RESULT_RUN" if author["latest_result_metadata"] and producing_run == author["latest_result_metadata"]["run_id"] else
                   "HISTORICAL_PR_AUTHOR_NOT_CURRENT_SERVICE")
    advisory = github.advisory(games, report)
    h = after["coordinator"]["holder"]
    obs = {"repository": project["repository"], "main_head": report["main_sha"],
           "main_qa_head": report["main_sha"] if report["status_only"] else report["main_ci"]["head"],
           "main_qa": {"PASS": "success", "FAIL": "failure"}.get(report["main_ci"]["qa"], "pending"),
           "lease": None if h is None else {"kind": h["kind"], "owner_run_id": h["owner_id"], "epoch": h["epoch"]},
           "open_prs": [{"head_sha": report["pr"]["head"], "ci_head_sha": report["pr"]["ci"]["head"],
                         "ci": {"PASS": "success", "FAIL": "failure"}.get(report["pr"]["ci"]["qa"], "pending")}]}
    for role, name in (("author", "worker"), ("meta", "meta"), ("reviewer", "reviewer")):
        obs[name + "_run"] = after["services"][role]["last_run"]["recorded_status"]
    advisory["core"] = core.evaluate(project, obs)
    verdict = _triage(project, report, after, pins, finished)
    advisory["triage"] = verdict
    return {"schema": 1, "mode": "ADVISORY_ONLY", "verification": "NOT_VERIFIED",
            "origin": "EXTERNAL_HOST_EXECUTION_ATTESTATION_REQUIRED", "game_id": project["game_id"],
            "repository": project["repository"], "started_at": start.isoformat(), "finished_at": finished,
            "main_sha": report["main_sha"], "main_ci": report["main_ci"], "status_only": report["status_only"],
            "coordinator": after["coordinator"], "pr": report["pr"], "services": after["services"],
            "pr_author_service_binding": association, "get_trace": trace,
            "immutable_cache_hits": cache_hits,
            "peek_trace": before["peek_trace"] + after["peek_trace"],
            "operation_evidence": after["operation_evidence"], "advisory": advisory,
            "missing_triage_inputs": ["original_operation_receipt"], "authority": deepcopy(DENIED),
            "consistency": "BOUNDED_REREADS_NOT_ATOMIC_SNAPSHOT_OR_PORTABLE_PROOF"}


def main():
    try:
        class SafeParser(argparse.ArgumentParser):
            def error(self, message):
                raise EvidenceError("INVALID_REQUEST")
        parser = SafeParser(description=__doc__)
        parser.add_argument("--request", required=True)
        request = github.loads(Path(parser.parse_args().request).read_text(encoding="utf-8"))
        need(type(request) is dict and set(request) == {"projects", "binding"}, "INVALID_REQUEST")
        def call(method, key, value):
            print(json.dumps({"method": method, key: value}), flush=True)
            row = github.loads(sys.stdin.readline())
            need(type(row) is dict and set(row) == ({"status", "body"} if method == "GET" else {"ok", "body"}), "INVALID_TRANSPORT_RESPONSE")
            return github.Response(row["status"], row["body"]) if method == "GET" else service.PeekResponse(row["ok"], row["body"])
        result = observe(request["projects"], request["binding"], lambda url: call("GET", "url", url),
                         lambda task: call("PEEK", "task_id", task), lambda: datetime.now(timezone.utc).isoformat())
        print(json.dumps({"result": result}, sort_keys=True), flush=True)
        return 0
    except Exception:
        # No arbitrary exception message, provider body, prompt or request is logged.
        code = "INCIDENT_OBSERVATION_REJECTED"
        print(json.dumps({"verification": "NOT_VERIFIED", "reason": code, "authority": DENIED}), flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
