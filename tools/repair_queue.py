"""Choose one bounded repair action from observed PR/CI facts; never manage schedules."""
import argparse
import json
import uuid
from check_auto_diff import is_worker_branch


def choose_action(policy, pulls, run_id):
    def result(action, **details):
        return {"action": action, "change_scheduler": False, **details}

    if policy.get("enabled") is not True:
        return result("DISABLED")
    if policy.get("mode") != "DRAFT_PR_ONLY":
        return result("DISABLED", reason="draft-only policy required")
    if str(uuid.UUID(run_id)) != run_id:
        raise ValueError("a canonical service run UUID is required")
    branch = policy["branch_prefix"] + run_id
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
    for pr in own:
        if pr.get("ci") != "success":
            return result("WAIT_CI", pr=pr["number"], branch=pr["branch"], open_prs=numbers)
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
    print(json.dumps(choose_action(policy, data["pulls"], data["run_id"]), ensure_ascii=False))


if __name__ == "__main__":
    main()
