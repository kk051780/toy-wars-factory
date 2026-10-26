"""Read-only incident triage. JSON is evidence, never execution authority.

Collectors must obtain envelopes directly from the configured providers. Provider
names/locators are checked against a separately trusted config; they are not a
signature and cannot authenticate an arbitrary caller-supplied JSON document.
No network, scheduler, Git mutation, recovery, or raw-error logging occurs here.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import uuid


class InvalidEvidence(ValueError):
    pass


def require(condition):
    if not condition:
        raise InvalidEvidence()


def timestamp(value):
    require(isinstance(value, str))
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(moment.tzinfo is not None)
    return moment.astimezone(timezone.utc)


def run_uuid(value):
    require(isinstance(value, str) and str(uuid.UUID(value)) == value)
    return value


def sha(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value))
    return value


def positive(value):
    require(type(value) is int and value > 0)
    return value


def result(state, reason, *, claim=False, next_schedule=False):
    # Output only constants and booleans. Never echo input, paths, errors, tokens,
    # provider-controlled status strings, or exception messages.
    return {"schema": 1, "state": state, "reason": reason,
            "claim_verified": claim, "safe_to_next_schedule": next_schedule,
            "start_now_allowed": False, "takeover_allowed": False,
            "write_authorized": False}


def classify(evidence, config, now):
    """Deterministic diagnosis; even a positive result grants no write permission."""
    try:
        return _classify(evidence, config, timestamp(now))
    except (InvalidEvidence, KeyError, TypeError, ValueError, AttributeError, OverflowError):
        return result("INDETERMINATE", "INVALID_OR_MISSING_EVIDENCE")


def _classify(e, c, now):
    require(type(e) is dict and type(c) is dict and type(e["schema"]) is int and e["schema"] == 1)
    repository, task, branch = c["repository"], c["task_id"], c["control_branch"]
    require(isinstance(repository, str) and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository))
    require(isinstance(task, str) and re.fullmatch(r"[A-Za-z0-9_-]+", task))
    require(isinstance(branch, str) and branch and not any(x in branch for x in ("..", "\\", "\n", "\r")))
    max_age, max_lease = positive(c["max_age_seconds"]), positive(c["max_lease_seconds"])
    jobs = c["required_jobs"]
    require(type(jobs) is list and jobs and len(jobs) == len(set(jobs)))
    require(all(isinstance(j, str) and j for j in jobs))
    run = run_uuid(e["run_id"])
    require(e["repository"] == repository and e["task_id"] == task)
    observed = {}

    def envelope(name, kind, locator):
        item = e[name]
        source = item["source"]
        require(source["provider"] == c["providers"][kind])
        require(source["kind"] == kind and source["locator"] == locator)
        at = timestamp(source["observed_at"])
        require(0 <= (now - at).total_seconds() <= max_age)
        observed[name] = at
        require(type(item["data"]) is dict)
        return item["data"]

    def service(name, service_task, service_run):
        data = envelope(name, "service", "task/" + service_task)
        require(data["task_id"] == service_task)
        record = data["last_run"]
        require(run_uuid(record["id"]) == service_run)
        started = timestamp(record["started_at"])
        require(started <= observed[name])
        state = record["recorded_status"]
        require(state in ("in_progress", "completed", "failed", "no_update"))
        end = record["completed_at"]
        if state == "in_progress":
            require(end is None)
        else:
            require(started <= timestamp(end) <= observed[name])
        report = data.get("latest_result")
        if report is not None:
            require(report["run_id"] == service_run)
            require(started <= timestamp(report["created_at"]) <= observed[name])
        return data

    svc = service("service", task, run)
    lock = envelope("lock", "lock", repository + "/git/ref/heads/" + branch)
    require(lock["repository"] == repository and lock["branch"] == branch)
    ref = sha(lock["head"])
    epoch = lock["epoch"]
    require(type(epoch) is int and epoch >= 0)
    holder = lock["holder"]
    if holder is not None:
        run_uuid(holder["owner_id"])
        require(isinstance(holder["work_branch"], str) and holder["work_branch"])
        require(holder["task_id"] is None or isinstance(holder["task_id"], str))
        require(type(holder["epoch"]) is int and holder["epoch"] == epoch and epoch > 0)
        require(holder["kind"] in ("WORKER", "META", "REVIEWER", "CONTROLLER", "DISPATCH"))
        if holder["kind"] in ("WORKER", "META", "REVIEWER"):
            require(holder["task_id"] == c["registered_tasks"][holder["kind"]])
        acquired, expires = timestamp(holder["acquired_at"]), timestamp(holder["expires_at"])
        require(acquired <= observed["lock"] and 0 < (expires - acquired).total_seconds() <= max_lease)

    pr = envelope("pr", "pr", repository + "/pulls/" + str(positive(e["pr"]["data"]["number"])))
    require(pr["repository"] == repository and pr["state"] == "open")
    require(isinstance(pr["branch"], str) and pr["branch"] == e["work_branch"])
    head, base = sha(pr["head"]), sha(pr["base"])
    producer = run_uuid(pr["producing_run_id"])
    ci = envelope("ci", "ci", repository + "/actions/runs/" + str(positive(e["ci"]["data"]["id"])))
    require(ci["repository"] == repository and ci["pr_number"] == pr["number"])
    sha(ci["head"])
    sha(ci["base"])
    require(type(ci["attempt"]) is int and ci["attempt"] > 0)
    require(ci["id"] == positive(pr["latest_qa_run_id"]) and ci["attempt"] == positive(pr["latest_qa_attempt"]))
    require(ci["status"] in ("queued", "in_progress", "completed"))
    require(ci["conclusion"] in (None, "success", "failure", "cancelled", "skipped", "timed_out", "neutral", "action_required", "stale"))
    require((ci["status"] == "completed") == (ci["conclusion"] is not None))
    require(type(ci["jobs"]) is list)
    seen = set()
    for job in ci["jobs"]:
        require(isinstance(job["name"], str) and job["name"] not in seen)
        require(positive(job["run_id"]) == ci["id"] and positive(job["attempt"]) == ci["attempt"] and job["head"] == ci["head"])
        seen.add(job["name"])
        require(job["status"] in ("queued", "in_progress", "completed"))
        require(job["conclusion"] in (None, "success", "failure", "cancelled", "skipped", "timed_out", "neutral", "action_required", "stale"))
        require((job["status"] == "completed") == (job["conclusion"] is not None))

    op = None
    if e.get("operation") is not None:
        op = envelope("operation", "operation", repository + "/git/ref/heads/" + branch)
        require(op["repository"] == repository and op["branch"] == branch)
        require(op["task_id"] == task and op["run_id"] == run)
        require(op["stage"] in ("create_tree", "create_commit", "update_ref"))
        require(op["outcome"] in ("success", "failure"))
        op_at = timestamp(op["at"])
        require(timestamp(svc["last_run"]["started_at"]) <= op_at <= observed["operation"] <= observed["lock"])
        if svc["last_run"]["completed_at"] is not None:
            require(op_at <= timestamp(svc["last_run"]["completed_at"]))
        require(op["force"] is False and sha(op["parent_sha"]) == sha(op["expected_sha"]))
        require(op["parent_shas"] == [op["expected_sha"]])
        if op["outcome"] == "failure":
            if op["layer"] == "host" and op["code"] in ("HOST_WRITE_DENIED", "SAFETY_CHECK_REJECTED"):
                return result("HOST_WRITE_DENIED", "PROVIDER_HOST_REJECTION_OBSERVED")
            if (op["layer"] == "github" and op["stage"] == "update_ref" and
                    op["code"] == "EXPECTED_SHA_MISMATCH" and ref != op["expected_sha"]):
                return result("REF_RACE", "EXPECTED_REF_CHANGED_REREAD_REQUIRED")
            return result("INDETERMINATE", "UNRECOGNIZED_OPERATION_FAILURE")
        require(op["code"] == "OK" and op["layer"] == "github")
        sha(op["commit_sha"])

    if holder is not None:
        if now < expires:
            verified = bool(op and op["stage"] == "update_ref" and ref == op["commit_sha"] and
                            acquired <= op_at and
                            holder["owner_id"] == run and holder["task_id"] == task and
                            holder["work_branch"] == e["work_branch"] and
                            type(op.get("epoch")) is int and op["epoch"] == epoch)
            return result("ACTIVE_LEASE", "JOIN_EXISTING_WRITER", claim=verified)
        # Expiry is never an authenticated end receipt. Only the exact owner
        # service run ending after this acquisition can identify an orphan.
        if holder["kind"] in ("WORKER", "META", "REVIEWER"):
            owner = service("holder_service", holder["task_id"], holder["owner_id"])
            record = owner["last_run"]
            if (record["recorded_status"] != "in_progress" and
                    timestamp(record["started_at"]) <= acquired and
                    acquired <= timestamp(record["completed_at"]) <= observed["lock"]):
                return result("WRITER_EXITED_WITHOUT_RELEASE", "EXACT_OWNER_TERMINAL_EVIDENCE_RECOVERY_REVIEW_REQUIRED")
        return result("INDETERMINATE", "EXPIRY_IS_NOT_TAKEOVER_EVIDENCE")
    if op is not None:
        return result("INDETERMINATE", "COMMIT_OR_REF_RESPONSE_WITHOUT_CONFIRMED_CLAIM")
    report = svc.get("latest_result") or {}
    if report.get("reported_state") == "BLOCKED_HOST_WRITE":
        return result("INDETERMINATE", "HOST_WRITE_REPORTED_RAW_PROVIDER_ERROR_UNAVAILABLE")
    if svc["last_run"]["recorded_status"] == "in_progress":
        return result("INDETERMINATE", "SERVICE_IN_PROGRESS_DO_NOT_START_DUPLICATE")
    if svc["last_run"]["recorded_status"] != "completed":
        return result("INDETERMINATE", "SERVICE_NOT_SUCCESSFULLY_COMPLETED")
    if producer != run or ci["head"] != head or ci["base"] != base:
        return result("INDETERMINATE", "RUN_OR_HEAD_OR_BASE_QA_BINDING_MISMATCH")
    if ci["status"] != "completed":
        return result("WAIT_CI", "EXACT_RUN_HEAD_QA_PENDING")
    if (ci["conclusion"] != "success" or not set(jobs).issubset(seen) or
            any(j["status"] != "completed" or j["conclusion"] != "success" for j in ci["jobs"])):
        return result("INDETERMINATE", "QA_FAILED_OR_INCOMPLETE")
    return result("SAFE_TO_NEXT_SCHEDULE", "TERMINAL_IDLE_EXACT_RUN_HEAD_QA_SUCCESS", next_schedule=True)


def load_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out)
            out[key] = value
        return out
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(InvalidEvidence()))


def main(argv=None):
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise InvalidEvidence()

    try:
        parser = SafeParser(description=__doc__)
        parser.add_argument("--evidence", required=True, help="JSON file, or - for stdin")
        parser.add_argument("--config", required=True, help="separately trusted collector binding config")
        parser.add_argument("--now", required=True, help="explicit timezone-aware observation clock")
        args = parser.parse_args(argv)
        require(args.config != "-")
        verdict = classify(load_json(args.evidence), load_json(args.config), args.now)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        verdict = result("INDETERMINATE", "INVALID_OR_MISSING_EVIDENCE")
    print(json.dumps(verdict, sort_keys=True))
    return 2 if verdict["state"] == "INDETERMINATE" else 0


if __name__ == "__main__":
    sys.exit(main())
