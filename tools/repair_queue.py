"""Choose one bounded repair action from observed PR/CI facts; never manage schedules."""
import argparse
from datetime import datetime
import json
from pathlib import PurePosixPath
import re
import uuid
from check_auto_diff import is_worker_branch

_NO_REVIEW_INPUT = object()

def _review_repairs(policy, pulls, requests, run_id):
    """Validate collector-normalized GitHub facts, not PR-body instructions.

    The caller must fetch the coordinator files independently at one real ref
    and bind author identities from accepted history/claim evidence. These JSON
    consistency checks do not authenticate caller-supplied provider strings.
    No network, writes, approval, lease acquisition or scheduler calls occur.
    """
    def check(condition):
        if not condition:
            raise ValueError("invalid review repair evidence")

    def sha(value):
        check(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value))

    def operation_id(value):
        check(isinstance(value, str) and str(uuid.UUID(value)) == value)

    def timestamp(value):
        check(isinstance(value, str))
        at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        check(at.tzinfo is not None)
        return at

    check(type(requests) is list)
    if not requests:
        return []
    repo = policy["repository"]
    check(isinstance(repo, str) and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo))
    integration = policy["integration"]
    check(integration["enabled"] is True)
    reviewer_task = integration["task_id"]
    worker_task = policy["task_id"]
    check(isinstance(worker_task, str) and worker_task)
    check(isinstance(reviewer_task, str) and reviewer_task and reviewer_task != worker_task)
    control = policy["coordination"]
    review_dir = str(PurePosixPath(control["state_path"]).parent / "reviews")
    snapshots, ids, numbers, branches, candidates = set(), set(), set(), set(), []

    def source(value, path):
        check(type(value) is dict and set(value) == {
            "provider", "repository", "branch", "path", "commit", "observed_at"})
        check(value["provider"] == "GitHub" and value["repository"] == repo)
        check(value["branch"] == control["branch"] and value["path"] == path)
        sha(value["commit"])
        return timestamp(value["observed_at"])

    for request in requests:
        check(type(request) is dict and set(request) == {
            "schema", "id", "kind", "priority", "repository", "pr", "branch",
            "head", "status", "assigned_role", "source", "review"})
        check(type(request["schema"]) is int and request["schema"] == 1)
        request_id, number, branch, head = (request[k] for k in ("id", "pr", "branch", "head"))
        check(isinstance(request_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", request_id))
        check(type(number) is int and number > 0)
        check(request_id not in ids and number not in numbers and branch not in branches)
        ids.add(request_id)
        numbers.add(number)
        branches.add(branch)
        check(request["kind"] in ("PR_REGRESSION", "PR_REGRESSION_UI_LAYOUT", "REVIEW_REQUEST_CHANGES"))
        check(request["status"] == "OPEN" and request["assigned_role"] == "WORKER" and request["priority"] == "P1")
        check(request["repository"] == repo and is_worker_branch(branch, policy))
        sha(head)
        observed = source(request["source"], integration["repair_requests"])
        snapshots.add(request["source"]["commit"])
        check(len(snapshots) == 1)

        matches = [pr for pr in pulls if pr.get("number") == number]
        check(len(matches) == 1)
        pr = matches[0]
        check(type(pr.get("number")) is int and pr["number"] == number)
        check(pr.get("repository") == repo and pr.get("base_repository") == repo)
        check(pr.get("state") == "open" and pr.get("merged") is False)
        check(pr.get("branch") == branch and pr.get("head") == head)
        check(pr.get("ci_head") == head)
        check(pr.get("author_task_id") == policy["task_id"])
        operation_id(pr.get("author_run_id"))

        review = request["review"]
        check(type(review) is dict and set(review) == {
            "schema", "repository", "pr", "branch", "head", "verdict",
            "reviewer_kind", "reviewer_task_id", "reviewer_run_id", "author_task_id",
            "author_run_id", "work_request_id", "reviewed_at", "source"})
        check(type(review["schema"]) is int and review["schema"] == 1)
        check(type(review["pr"]) is int and review["pr"] == number)
        check(review["repository"] == repo and review["branch"] == branch and review["head"] == head)
        check(review["verdict"] == "REQUEST_CHANGES" and review["work_request_id"] == request_id)
        check(review["reviewer_kind"] == "REVIEWER" and review["reviewer_task_id"] == reviewer_task)
        check(review["author_task_id"] == pr["author_task_id"] and review["author_run_id"] == pr["author_run_id"])
        operation_id(review["reviewer_run_id"])
        check(review["reviewer_task_id"] != review["author_task_id"])
        check(review["reviewer_run_id"] not in (review["author_run_id"], run_id))
        review_path = f"{review_dir}/PR{number:04d}_{head[:8]}.json"
        review_observed = source(review["source"], review_path)
        check(review["source"]["commit"] == request["source"]["commit"])
        check(timestamp(review["reviewed_at"]) <= min(observed, review_observed))
        candidates.append({"pr": number, "branch": branch, "head": head,
                           "request_id": request_id,
                           "reviewer_run_id": review["reviewer_run_id"]})
    return sorted(candidates, key=lambda item: item["pr"])


def choose_action(policy, pulls, run_id, trusted_review_requests=_NO_REVIEW_INPUT):
    def result(action, **details):
        return {"action": action, "change_scheduler": False, **details}

    if policy.get("enabled") is not True:
        return result("DISABLED")
    if policy.get("mode") != "DRAFT_PR_ONLY":
        return result("DISABLED", reason="draft-only policy required")
    if str(uuid.UUID(run_id)) != run_id:
        raise ValueError("a canonical service run UUID is required")
    branch = policy["branch_prefix"] + run_id
    if trusted_review_requests is not _NO_REVIEW_INPUT and (type(pulls) is not list or any(type(pr) is not dict for pr in pulls)):
        return result("WAIT_METADATA", reason="invalid review repair evidence")
    own = []
    seen = set()
    seen_branches = set()
    for pr in pulls:
        if not is_worker_branch(pr.get("branch"), policy):
            continue
        if pr.get("repository") != policy["repository"]:
            if pr.get("repository") is None:
                return result("WAIT_METADATA", reason="missing head repository")
            continue
        if pr.get("state") not in ("open", "closed"):
            return result("WAIT_METADATA", reason="missing PR state")
        if pr.get("state") == "closed":
            if pr["branch"] == branch:
                return result("ALREADY_RECORDED", branch=branch)
            continue
        number = pr.get("number")
        if (not isinstance(number, int) or isinstance(number, bool) or number < 1 or
                number in seen or pr["branch"] in seen_branches):
            return result("WAIT_METADATA", reason="invalid or duplicated PR number")
        seen.add(number)
        seen_branches.add(pr["branch"])
        own.append(pr)
    own.sort(key=lambda pr: pr["number"])
    numbers = [pr["number"] for pr in own]
    for pr in own:
        if pr.get("ci") in ("failure", "cancelled", "timed_out", "action_required"):
            return result("REPAIR_CI", pr=pr["number"], branch=pr["branch"], open_prs=numbers)
    repairs = []
    if trusted_review_requests is not _NO_REVIEW_INPUT:
        try:
            repairs = _review_repairs(policy, pulls, trusted_review_requests, run_id)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
            return result("WAIT_METADATA", reason="invalid review repair evidence", open_prs=numbers)
    for pr in own:
        if pr.get("ci") != "success":
            return result("WAIT_CI", pr=pr["number"], branch=pr["branch"], open_prs=numbers)
    if repairs:
        return result("REPAIR_REVIEW", **repairs[0], open_prs=numbers)
    if any(pr["branch"] == branch for pr in own):
        return result("ALREADY_RECORDED", branch=branch, open_prs=numbers)
    limit = policy["max_open_prs"]
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("positive max_open_prs required")
    if len(own) >= limit:
        return result("WAIT_REVIEW", open_prs=numbers, limit=limit)
    return result("START", branch=branch, base="main", open_prs=numbers, limit=limit)


def choose_system_action(policy, pulls, run_id):
    meta = policy["system_review"]
    scoped = {**policy, "enabled": meta["enabled"], "branch": None,
              "branch_prefix": meta["branch_prefix"], "max_open_prs": meta["max_open_prs"]}
    return choose_action(scoped, pulls, run_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="config/autonomous_repair.json")
    parser.add_argument("--input", required=True,
                        help="JSON with run_id and normalized pulls: number, branch, repository, state, ci")
    args = parser.parse_args()
    with open(args.policy, encoding="utf-8") as file:
        policy = json.load(file)
    with open(args.input, encoding="utf-8") as file:
        data = json.load(file)
    optional = ({"trusted_review_requests": data["trusted_review_requests"]}
                if "trusted_review_requests" in data else {})
    print(json.dumps(choose_action(policy, data["pulls"], data["run_id"], **optional), ensure_ascii=False))


if __name__ == "__main__":
    main()
