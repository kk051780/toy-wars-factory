"""Read-only contract for current integration receipts; never write authority.

Caller data are UNTRUSTED even on PASS. A host must separately fetch fresh
GitHub evidence, authenticate its actor, own a fenced lease and obtain review.
This additive preflight is not installed as a GitHub writer or policy hook.
Historical snapshots may retain their old numeric fields; current receipts
must preserve detailed types and exact run/job bindings. Issue138 / Issue123.
"""
import json
import re

STATUS_PATHS = {"status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"}
FLAGS = ("write_allowed", "start_now_allowed", "takeover_allowed",
         "dispatch_allowed", "merge_allowed", "publish_allowed",
         "external_spend_allowed", "github_cas_performed", "safe_to_next_schedule")


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _integer(value):
    return type(value) is int and value > 0


def _sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _json(value):
    # Unlike Python equality, JSON distinguishes True, 1 and 1.0.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _history(rows):
    _need(type(rows) is list and rows and len(rows) <= 1000, "invalid history")
    _need(all(type(row) is dict and _integer(row.get("pr")) for row in rows),
          "detailed positive-integer PR entries required")
    _need(len({row["pr"] for row in rows}) == len(rows), "duplicate PR")
    return rows


def _distinct_new_adoption(old_rows, new_row):
    """Fail closed if an appended PR reuses any prior provider identity.

    Old ledger rows may be sparse or numeric-only, so only compare a prior
    value when it has the correct type. The *new* row must supply all five.
    This detects copied evidence even when the newly invented PR ID is unique.
    """
    fields = {"head": _sha, "merge_sha": _sha,
              "main_qa": _integer, "handoff": _integer,
              "main_after_handoff": _sha}
    for field, validator in fields.items():
        value = new_row.get(field)
        _need(validator(value), "new adoption lacks valid " + field)
        _need(not any(validator(prior.get(field)) and prior[field] == value
                      for prior in old_rows), "reused prior adoption " + field)
    # A GitHub run ID is globally scoped within a repository, NOT a separate
    # namespace for QA and handoff. Swapping roles must not renew old proof.
    def run_id(record, key):
        raw = record.get(key)
        if type(raw) is dict:
            raw = raw.get("id")
        return raw if _integer(raw) else None
    fresh = {new_row["main_qa"], new_row["handoff"]}
    _need(len(fresh) == 2, "QA and handoff reused one run")
    previous = {rid for row in old_rows for key in ("main_qa", "handoff")
                if (rid := run_id(row, key)) is not None}
    _need(not fresh.intersection(previous), "reused prior GitHub run across QA/handoff")


def _receipts(after, tail, repository, merge):
    seen_ids = set()
    for field, names in (("main_qa", {"offline", "compile_hold"}),
                         ("handoff", {"update"})):
        run = after[field]
        _need(type(run) is dict, "current receipt must be an object")
        _need(_integer(run.get("id")) and run["id"] == tail[field]
              and _integer(tail[field]), "wrong run ID")
        _need(_integer(run.get("attempt")), "invalid run attempt")
        _need(run.get("head") == merge and run.get("status") == "completed"
              and run.get("conclusion") == "success", "run not exact successful merge")
        _need(run.get("url") ==
              f"https://github.com/{repository}/actions/runs/{run['id']}", "foreign run URL")
        if field == "main_qa":
            summary = run.get("jobs")
            _need(type(summary) is dict and set(summary) == names
                  and all(x == "success" for x in summary.values()), "QA jobs dictionary")
            jobs = run.get("job_evidence")
        else:
            jobs = run.get("jobs")
        _need(type(jobs) is list and len(jobs) == len(names), "missing job evidence")
        seen_names = set()
        for job in jobs:
            _need(type(job) is dict and _integer(job.get("id"))
                  and job["id"] not in seen_ids, "invalid or duplicate job ID")
            seen_ids.add(job["id"])
            name = job.get("name")
            _need(type(name) is str and name in names
                  and name not in seen_names, "invalid or duplicate job name")
            seen_names.add(name)
            _need(_integer(job.get("run_id")) and job["run_id"] == run["id"]
                  and _integer(job.get("run_attempt"))
                  and job["run_attempt"] == run["attempt"], "job run/attempt mismatch")
            heads = [job[k] for k in ("head", "head_sha") if k in job]
            _need(heads and all(h == merge for h in heads)
                  and job.get("status") == "completed"
                  and job.get("conclusion") == "success", "job head/status mismatch")
        _need(seen_names == names, "missing named job")


def _comparison(comparison, merge, main):
    _need(type(comparison) is dict
          and comparison.get("base_commit", {}).get("sha") == merge, "wrong comparison base")
    ahead, behind, total = (comparison.get(k) for k in
                            ("ahead_by", "behind_by", "total_commits"))
    _need(type(behind) is int and behind == 0, "diverged comparison")
    _need(comparison.get("status") == "ahead" and _integer(ahead)
          and type(total) is int and total == ahead, "unknown descendant comparison")
    commits, files = comparison.get("commits"), comparison.get("files")
    _need(type(commits) is list and len(commits) == total
          and all(type(c) is dict and _sha(c.get("sha")) for c in commits)
          and commits[-1]["sha"] == main, "comparison does not reach latest main")
    _need(type(files) is list and 0 < len(files) <= len(STATUS_PATHS)
          and all(type(f) is dict and f.get("filename") in STATUS_PATHS
                  and f.get("status") in {"modified", "added"} for f in files),
          "non-status or unavailable main diff")
    _need(len({f["filename"] for f in files}) == len(files), "duplicate comparison path")


def check_transition(before, after, *, repository, comparison):
    """Check a post-handoff record transition, without mutating any input.

    Full bounded GitHub comparison data are required for a generated-status
    descendant. Missing/partial/other states block conservatively, not recover.
    No fixed game/PR number or historical entry count is assumed. This is
    neither a reader migration for old snapshots nor a provider authenticator.
    """
    result = {"mode": "READ_ONLY_CONTRACT", "verification": "NOT_VERIFIED",
              **dict.fromkeys(FLAGS, False)}
    try:
        _need(type(before) is dict and type(after) is dict, "objects required")
        _json(before), _json(after), _json(comparison)
        _need(type(repository) is str and re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", repository)
              and repository.split("/")[1] not in {".", ".."}
              and not repository.lower().endswith(".git"), "repository binding required")
        _need(before.get("repository") == after.get("repository") == repository,
              "repository mismatch")
        _need(type(before.get("schema")) is int and before["schema"] == 1
              and type(after.get("schema")) is int and after["schema"] == 1, "unknown schema")
        _need(set(before) <= set(after), "old root key deleted")
        old, new = _history(before["merged_prs"]), _history(after["merged_prs"])
        _need(len(new) - len(old) in (0, 1)
              and _json(new[:len(old)]) == _json(old), "historical entries changed")
        for key in ("historical_snapshot", "previous_snapshot", "compatibility_repair", "normalizer"):
            if key in before:
                _need(_json(before[key]) == _json(after[key]), "historical snapshot changed")
        if len(new) == len(old) + 1:
            _distinct_new_adoption(old, new[-1])
        tail, review = new[-1], after["latest_review"]
        merge, main = tail["merge_sha"], tail["main_after_handoff"]
        _need(_sha(tail.get("head")) and _sha(merge) and _sha(main), "canonical tail required")
        _need(type(review) is dict and type(review.get("pr")) is int
              and review["pr"] == tail["pr"] and review.get("head") == tail["head"]
              and review.get("merge_sha") == merge, "stale latest review")
        _need(after.get("merge_sha") == after.get("main_after_merge") == merge
              and after.get("main_after_handoff") == after.get("latest_main_sha") == main,
              "root/tail main binding mismatch")
        _receipts(after, tail, repository, merge)
        _comparison(comparison, merge, main)
        return {**result, "status": "CONTRACT_PASS_UNTRUSTED_EVIDENCE",
                "historical_rows_preserved": len(old), "appended_rows": len(new)-len(old)}
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as ex:
        return {**result, "status": "BLOCKED_LEDGER_CONTRACT", "reason": str(ex)}
