"""Read-only, caller-supplied GitHub Actions CI triage; never execution authority.

Pure contract for one known workflow and exact PR HEAD. It does not fetch GitHub,
verify the caller's provenance, approve a workflow, dispatch, merge or publish.
A trusted service must bind its live GET results, run identities and source ref.
"""
import json
import re

SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
COMPLETE = {"success", "failure", "action_required", "cancelled", "timed_out",
            "neutral", "skipped", "stale", "startup_failure"}
IN_PROGRESS = {"queued", "in_progress"}
APPROVAL = {"requested", "waiting", "pending"}
JOBS = {"offline", "compile_hold"}
MAX_PAYLOAD = 100_000


def _result(verdict, run_id=None):
    return {"verdict": verdict, "run_id": run_id,
            "authority": "READ_ONLY_UNTRUSTED_SNAPSHOT",
            "provider_attested": False, "write_allowed": False,
            "dispatch_allowed": False, "merge_allowed": False,
            "publish_allowed": False, "independent_review_complete": False}


def _positive_int(v):
    return type(v) is int and v > 0


def _sha(v):
    return type(v) is str and SHA.fullmatch(v) is not None


def _classify(status, conclusion):
    if type(status) is not str or (conclusion is not None and type(conclusion) is not str):
        return "BLOCK_MALFORMED"
    if status in APPROVAL:
        return "WAIT_WORKFLOW_APPROVAL" if conclusion is None else "BLOCK_MALFORMED"
    if status in IN_PROGRESS:
        return "WAIT_CI" if conclusion is None else "BLOCK_MALFORMED"
    if status != "completed" or conclusion not in COMPLETE:
        return "BLOCK_MALFORMED"
    if conclusion == "action_required":
        return "WAIT_WORKFLOW_APPROVAL"
    if conclusion != "success":
        return "BLOCK_CI_FAILURE"
    return "QA_CANDIDATE_GREEN"


def assess(repository, expected_head, expected_workflow_id, run, jobs):
    """Classify a single externally supplied run+jobs snapshot without grants."""
    if (type(repository) is not str or REPO.fullmatch(repository) is None
            or not _sha(expected_head) or not _positive_int(expected_workflow_id)
            or type(run) is not dict):
        return _result("BLOCK_MALFORMED")
    rid, attempt = run.get("id"), run.get("run_attempt")
    if (not _positive_int(rid) or not _positive_int(attempt)
            or not _sha(run.get("head_sha"))):
        return _result("BLOCK_MALFORMED")
    if type(run.get("repository")) is not dict or run["repository"].get("full_name") != repository:
        return _result("BLOCK_REPO_MISMATCH", rid)
    if run["head_sha"] != expected_head:
        return _result("BLOCK_SOURCE_MISMATCH", rid)
    if run.get("event") != "pull_request":
        return _result("BLOCK_EVENT_MISMATCH", rid)
    if (type(run.get("workflow_id")) is not int or run["workflow_id"] != expected_workflow_id
            or run.get("name") != "Toy Wars bootstrap offline QA"):
        return _result("BLOCK_WORKFLOW_MISMATCH", rid)
    run_verdict = _classify(run.get("status"), run.get("conclusion"))
    if run_verdict != "QA_CANDIDATE_GREEN":
        return _result(run_verdict, rid)
    if type(jobs) is not list or len(jobs) != len(JOBS):
        return _result("BLOCK_JOBS_MISMATCH", rid)
    names, ids = set(), set()
    statuses = []
    for job in jobs:
        if (type(job) is not dict or not _positive_int(job.get("id")) or
                not _positive_int(job.get("run_id")) or
                job.get("run_id") != rid or job.get("run_attempt") != attempt or
                type(job.get("run_attempt")) is not int or
                job.get("head_sha") != expected_head or
                type(job.get("name")) is not str or job.get("name") not in JOBS):
            return _result("BLOCK_JOBS_MISMATCH", rid)
        if job["name"] in names or job["id"] in ids:
            return _result("BLOCK_JOBS_MISMATCH", rid)
        names.add(job["name"]); ids.add(job["id"])
        statuses.append(_classify(job.get("status"), job.get("conclusion")))
    if names != JOBS:
        return _result("BLOCK_JOBS_MISMATCH", rid)
    if "BLOCK_MALFORMED" in statuses:
        return _result("BLOCK_JOBS_MISMATCH", rid)
    if "WAIT_WORKFLOW_APPROVAL" in statuses:
        return _result("WAIT_WORKFLOW_APPROVAL", rid)
    if "BLOCK_CI_FAILURE" in statuses:
        return _result("BLOCK_CI_FAILURE", rid)
    if "WAIT_CI" in statuses:
        return _result("WAIT_CI", rid)
    return _result("QA_CANDIDATE_GREEN", rid)


def _unique_pairs(pairs):
    obj={}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON object key")
        obj[key]=value
    return obj


def assess_with_payload(repository, expected_head, expected_workflow_id, payload):
    """Strict JSON transport wrapper: duplicate keys and unbounded input blocked."""
    if type(payload) is not str:
        return _result("BLOCK_MALFORMED")
    try:
        if len(payload.encode("utf-8")) > MAX_PAYLOAD:
            return _result("BLOCK_MALFORMED")
        packet=json.loads(payload, object_pairs_hook=_unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite number")))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return _result("BLOCK_MALFORMED")
    if type(packet) is not dict or set(packet) != {"run", "jobs"}:
        return _result("BLOCK_MALFORMED")
    return assess(repository, expected_head, expected_workflow_id,
                  packet["run"], packet["jobs"])
