"""Independent READ-ONLY metadata consistency gate for future TWF witness runs.

All inputs are untrusted snapshots unless supplied by an independently authenticated
GitHub reader; even positive results never approve a PR or authenticate log content.
No network, tokens, writes, job dispatch or Roblox operations.
"""
from __future__ import annotations
import re
import uuid

REPO = "kk051780/toy-wars-factory"
REPO_ID = 1431683395
ACTOR = "kk051780"
WORKFLOW = ".github/workflows/twf-controller-claim-witness.yml"
WORKFLOW_REF = f"{REPO}/{WORKFLOW}@refs/heads/main"
TEST_STEP = "Fail closed on foreign claim, preexisting source branch, or partial API"
HEX = re.compile(r"[0-9a-f]{40}\Z")
SOURCE = re.compile(r"controller/protected-system-([0-9a-f-]{36})\Z")

class OriginHold(ValueError):
    pass


def must(value: bool, reason: str) -> None:
    if not value:
        raise OriginHold(reason)


def sha(value) -> bool:
    return type(value) is str and bool(HEX.fullmatch(value))


def positive(value) -> bool:
    return type(value) is int and value > 0


def canonical_owner(branch) -> bool:
    if type(branch) is not str:
        return False
    match = SOURCE.fullmatch(branch)
    if not match:
        return False
    try:
        value = match.group(1)
        ident = uuid.UUID(value)
        return str(ident) == value and ident.version in range(1, 9)
    except (ValueError, TypeError, AttributeError):
        return False


def require_candidate(candidate, accepted_main_sha: str, expected_run_id: int) -> dict:
    """Keep the original witness observation strictly NON-authorizing."""
    must(type(candidate) is dict, "CANDIDATE_TYPE")
    must(sha(accepted_main_sha) and positive(expected_run_id), "TRUSTED_INPUT_SHAPE")
    report = candidate.get("reported_actions_origin_untrusted")
    must(type(report) is dict, "ORIGIN_LABELS_MISSING")
    must(candidate.get("status") == "CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY" and
         sha(candidate.get("claim_sha")) and
         candidate.get("main_sha") == accepted_main_sha and
         positive(candidate.get("epoch")) and
         canonical_owner(candidate.get("source_branch")), "CANDIDATE_SCOPE")
    for field in ("provider_authenticated", "independent_review_authorized",
                  "merge_authorized", "roblox_post_authorized"):
        must(candidate.get(field) is False, "FORGED_CANDIDATE_AUTHORITY")
    must(report.get("repository") == REPO and report.get("repository_id") == str(REPO_ID) and
         report.get("workflow_ref") == WORKFLOW_REF and report.get("workflow_sha") == accepted_main_sha and
         report.get("source_main_sha") == accepted_main_sha and
         report.get("job_id") == "witness" and
         type(report.get("run_id")) is int and report["run_id"] == expected_run_id and
         type(report.get("run_attempt")) is int and report["run_attempt"] == 1 and
         report.get("claim_sha") == candidate["claim_sha"] and
         report.get("source_branch") == candidate["source_branch"] and
         type(report.get("epoch")) is int and report["epoch"] == candidate["epoch"], "RUN_LABELS_NOT_BOUND")
    for field in ("provider_authenticated", "job_log_attested", "may_review_or_merge", "may_write_or_publish"):
        must(report.get(field) is False, "FORGED_RUN_AUTHORITY")
    must(candidate.get("provider_witness_id") == "MUST_BIND_TO_AUTHENTICATED_WORKFLOW_RUN_AND_JOB", "PRETENDED_PROVIDER_CERT")
    return report


def verify_original_run_job_metadata(candidate, *, accepted_main_sha: str,
                                     expected_run_id: int, expected_job_id: int,
                                     original_run, original_job_page) -> dict:
    """Check provider-shaped run/job snapshots supplied by an independent reviewer.

    Passing does not authenticate the transport, trust the candidate's log content,
    prove claim-to-first-push order, or grant review/merge permission. A separate
    registered reviewer must fetch original GitHub run and job and inspect log data.
    """
    report = require_candidate(candidate, accepted_main_sha, expected_run_id)
    must(positive(expected_job_id), "EXPECTED_JOB_ID")
    r = original_run
    must(type(r) is dict and type(r.get("repository")) is dict and
         type(r["repository"].get("id")) is int and r["repository"]["id"] == REPO_ID and
         r["repository"].get("full_name") == REPO and
         type(r.get("id")) is int and r["id"] == expected_run_id and
         type(r.get("run_attempt")) is int and r["run_attempt"] == 1 and r.get("event") == "workflow_dispatch" and
         r.get("path") == WORKFLOW and r.get("head_sha") == accepted_main_sha and
         r.get("head_branch") == "main" and r.get("status") == "completed" and
         r.get("conclusion") == "success" and
         type(r.get("actor")) is dict and r["actor"].get("login") == ACTOR and
         type(r.get("triggering_actor")) is dict and r["triggering_actor"].get("login") == ACTOR,
         "ORIGINAL_RUN_SCOPE_MISMATCH")
    page = original_job_page
    must(type(page) is dict and type(page.get("total_count")) is int and
         page["total_count"] == 1 and type(page.get("jobs")) is list and
         len(page["jobs"]) == 1, "ORIGINAL_JOB_PAGE_MISMATCH")
    j = page["jobs"][0]
    must(type(j) is dict and type(j.get("id")) is int and j["id"] == expected_job_id and
         type(j.get("run_id")) is int and j["run_id"] == expected_run_id and
         type(j.get("run_attempt")) is int and j["run_attempt"] == 1 and
         j.get("name") == "witness" and j.get("head_sha") == accepted_main_sha and
         j.get("status") == "completed" and j.get("conclusion") == "success" and
         type(j.get("steps")) is list and len(j["steps"]) > 0 and len(j["steps"]) <= 30,
         "ORIGINAL_JOB_SCOPE_MISMATCH")
    names = set()
    executed = 0
    for step in j["steps"]:
        must(type(step) is dict and type(step.get("name")) is str and
             step["name"] not in names and
             step.get("conclusion") in ("success", "skipped"), "ORIGINAL_STEP_INVALID")
        names.add(step["name"])
        if step["name"] == TEST_STEP:
            must(step.get("status") == "completed" and step["conclusion"] == "success", "WITNESS_STEP_NOT_EXECUTED")
            executed += 1
    must(executed == 1, "WITNESS_STEP_MISSING")
    return {
        "status": "ORIGINAL_RUN_JOB_METADATA_CONSISTENT_CANDIDATE_ONLY",
        "repository": REPO,
        "workflow": WORKFLOW,
        "accepted_main_sha": accepted_main_sha,
        "run_id": expected_run_id,
        "job_id": expected_job_id,
        "claim_sha": candidate["claim_sha"],
        "source_branch": candidate["source_branch"],
        "epoch": candidate["epoch"],
        "metadata_fields_consistent": True,
        "trusted_provider_transport_authenticated": False,
        "witness_log_line_authenticated": False,
        "claim_before_source_push_proven": False,
        "independent_review_authorized": False,
        "merge_authorized": False,
        "source_write_authorized": False,
        "roblox_publish_authorized": False,
    }
