"""Read-only, bounded GitHub Actions schedule-run pagination adapter.

Only an external connected host can authenticate its GET calls. This module
receives an injectable callable that may be fake: matching JSON, URL fields,
run IDs and checksums do NOT prove provider identity. It never makes network
requests, modifies GitHub, dispatches a job, sends an alert or grants authority.

Separate source-history review is still required to establish whether an
historical cron expression was enabled for the whole requested time window.
"""
from __future__ import annotations

from math import ceil
from typing import Callable

from tools import system_actions_schedule_cadence as cadence

PER_PAGE = 100
MAX_PAGES = 10
PROVENANCE = "HOST_GET_CALLBACK_INPUT_NOT_AUTHENTICATED"


def need(value, reason):
    cadence.need(value, reason)


def normalize(row, repository: str, approved_paths: set[str]):
    """Only forward fixed allowlisted run keys, not untrusted GitHub metadata."""
    need(type(row) is dict, "INVALID_RAW_RUN")
    rid = row.get("id")
    need(type(rid) is int and 1 <= rid < 2**63, "INVALID_RAW_RUN")
    repo = row.get("repository")
    head_repo = row.get("head_repository")
    need(type(repo) is dict and type(head_repo) is dict and
         repo.get("full_name") == repository and
         head_repo.get("full_name") == repository, "FOREIGN_SOURCE_REPOSITORY")
    # The original API response binds the canonical run URI to the same repo/run.
    # This is a consistency check on untrusted data, NOT cryptographic proof.
    url = f"https://api.github.com/repos/{repository}/actions/runs/{rid}"
    need(row.get("url") == url, "WRONG_RUN_URL")
    path = row.get("path")
    need(type(path) is str and path in approved_paths, "FOREIGN_WORKFLOW")
    # GitHub workflow reruns reuse the same run ID with run_attempt > 1;
    # do not silently count a manual rerun as original cron delivery.
    need(type(row.get("run_attempt")) is int and row["run_attempt"] == 1,
         "RETRIED_RUN_AMBIGUITY")
    return {key: row.get(key) for key in (
        "id", "event", "path", "head_branch", "head_sha", "run_attempt",
        "created_at", "status", "conclusion")}


def collect_and_analyze(get: Callable, *, expected_repository: str,
                        binding: dict, observed_at: str, window_start: str,
                        window_end: str) -> dict:
    """Accept a host-supplied GET callback; classify data but authenticate NOTHING.

    Calls only fixed GET /actions/runs?event=schedule&per_page=100&page=N
    under the host-expected repository. Caller-controlled policy cannot redirect
    the callback to another repository. A complete stable total_count and each
    full page are mandatory; page drift, source mismatches and GET errors fail.
    """
    need(callable(get), "SOURCE_READER_MISSING")
    need(type(binding) is dict and set(binding) == {"repository", "workflows"},
         "INVALID_BINDING")
    repository = binding["repository"]
    need(type(expected_repository) is str and cadence.REPO.fullmatch(expected_repository)
         and type(repository) is str and repository == expected_repository,
         "REPOSITORY_BINDING_MISMATCH")
    policy = binding["workflows"]
    need(type(policy) is list and 1 <= len(policy) <= 8,
         "INVALID_WORKFLOWS")
    approved = set()
    for item in policy:
        need(type(item) is dict and set(item) == {"path", "minute_offsets", "branch"} and
             type(item["path"]) is str and cadence.PATH.fullmatch(item["path"]) and
             item["path"] not in approved and item["branch"] == "main",
             "INVALID_WORKFLOW")
        cadence.minute_tuple(item["minute_offsets"])
        approved.add(item["path"])
    start, end, observed = map(cadence.instant, (window_start, window_end, observed_at))
    need(start < end <= observed and
         3600 <= (end-start).total_seconds() <= 31*86400, "INVALID_WINDOW")

    def fetch(page):
        url = (f"https://api.github.com/repos/{repository}/actions/runs"
               f"?event=schedule&per_page={PER_PAGE}&page={page}")
        try:
            data = get(url)
        except Exception:
            raise cadence.CadenceError("SOURCE_GET_FAILED") from None
        need(type(data) is dict and "total_count" in data and
             "workflow_runs" in data and type(data["workflow_runs"]) is list,
             "INVALID_PROVIDER_PAGE")
        return data

    first = fetch(1)
    total = first["total_count"]
    need(type(total) is int and 0 <= total <= PER_PAGE*MAX_PAGES,
         "INVALID_OR_UNBOUNDED_TOTAL")
    pages = max(1, ceil(total/PER_PAGE))
    def read_complete_pass(first_page=None):
        records, seen_ids = [], set()
        for page in range(1, pages+1):
            result = first_page if page == 1 and first_page is not None else fetch(page)
            need(type(result["total_count"]) is int and result["total_count"] == total,
                 "PAGE_COUNT_CHANGED")
            rows = result["workflow_runs"]
            expected = min(PER_PAGE, max(0, total-(page-1)*PER_PAGE))
            need(len(rows) == expected, "INCOMPLETE_PAGE")
            for row in rows:
                item = normalize(row, repository, approved)
                need(item["id"] not in seen_ids, "PAGINATION_DUPLICATE_RUN")
                seen_ids.add(item["id"])
                records.append(item)
        need(len(records) == total, "INCOMPLETE_RESULT_PAGES")
        return records

    # REST pagination does NOT provide an immutable snapshot token. Repeat the
    # entire bounded walk and refuse inconsistent pages (including equal-count
    # reorder, insert+delete, or changing terminal outcomes). This is an extra
    # reproducibility check, NOT provider identity or an atomic API snapshot.
    original = read_complete_pass(first)
    confirmation = read_complete_pass()
    need(original == confirmation, "PAGINATION_SNAPSHOT_CHANGED")
    frame = {"schema":1, "repository":repository, "observed_at":observed_at,
             "window_start":window_start,"window_end":window_end,
             "total_count":total, "runs":original}
    summary = cadence.analyze(frame, binding)
    # Synthetic callback or replayed JSON can be forged. This is deliberately
    # still non-authoritative even after structural verification succeeds.
    summary["collection_method"] = PROVENANCE
    summary["read_pages"] = pages
    summary["get_requests"] = pages * 2
    summary["stable_two_pass_comparison"] = True
    summary["run_count_in_pages"] = len(original)
    summary["historical_cron_source_authenticated"] = False
    summary["origin_run_details_authenticated"] = False
    return summary