"""Decide exact-head integration under delegated authority and a separate review lease."""
import argparse
from datetime import timedelta
import json
from pathlib import Path
import re
from check_auto_diff import is_worker_branch
from repair_control import canonical_id, instant, owns

STATUS_PATHS = {"status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"}
REVIEW_CHECKS = ("scope", "regression", "source_ledger", "protected_controls", "behavior")


def decide(policy, main, pr, review, lease, now):
    def result(action, **details):
        return {"action": action, "requires_owner_reply": False, **details}
    authority = policy.get("approval_authority", {})
    integration = policy.get("integration", {})
    if (not integration.get("enabled") or not policy.get("automatic_merge_authorized") or
            authority.get("decision_owner") != "ASSISTANT" or authority.get("owner_reply_required") is not False):
        return result("DISABLED", reason="standing delegated integration authority is required")
    reviewer_id = review.get("reviewer_run_id")
    try:
        canonical_id(reviewer_id)
    except (ValueError, TypeError, AttributeError):
        return result("WAIT_REVIEW", reason="canonical reviewer run required")
    if (review.get("reviewer_task_id") != integration["task_id"] or
            not owns(lease, "REVIEWER", reviewer_id, review.get("lease_epoch"), now) or
            lease["holder"].get("work_branch") != "main"):
        return result("WAIT_LOCK", reason="current registered independent reviewer lease required")
    if main.get("qa_conclusion") in ("failure", "cancelled", "timed_out", "action_required"):
        return result("REPAIR_MAIN", main=main.get("sha"), ci=main.get("qa_url"))
    if main.get("qa_conclusion") != "success":
        return result("WAIT_MAIN_CI")
    if main.get("qa_head") != main.get("sha"):
        comparison = main.get("comparison_since_qa", {})
        if (comparison.get("verified") is not True or comparison.get("status") != "ahead" or
                not set(comparison.get("paths", [])).issubset(STATUS_PATHS)):
            return result("WAIT_MAIN_CI", reason="only verified generated-status descendants may reuse main QA")
    branch = pr.get("branch", "")
    meta_prefix = policy["system_review"]["branch_prefix"]
    meta = branch.startswith(meta_prefix)
    if meta:
        try:
            canonical_id(branch[len(meta_prefix):])
        except (ValueError, TypeError):
            return result("SKIP_UNRELATED")
    if (pr.get("repository") != policy["repository"] or pr.get("state") != "open" or
            not (is_worker_branch(branch, policy) or meta)):
        return result("SKIP_UNRELATED")
    author_task = policy["system_review"]["task_id"] if meta else policy["task_id"]
    if pr.get("author_task_id") != author_task:
        return result("WAIT_AUTHOR_ID")
    if (review.get("reviewer_task_id") == pr.get("author_task_id") or
            reviewer_id == pr.get("author_run_id")):
        return result("WAIT_INDEPENDENT_REVIEW", reason="author cannot approve its own work")
    head = pr.get("head", "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        return result("WAIT_METADATA")
    ci = pr.get("ci", {})
    if ci.get("head") != head:
        return result("WAIT_CI", reason="old-head CI is not evidence")
    if ci.get("conclusion") in ("failure", "cancelled", "timed_out", "action_required"):
        return result("REPAIR_CI", pr=pr["number"], branch=branch)
    if ci.get("conclusion") != "success" or ci.get("required_jobs_passed") is not True:
        return result("WAIT_CI")
    grandfathered = any(x["branch"] == branch and x["head"] == head for x in policy["coordination"].get("grandfathered_pr_heads", []))
    if ci.get("scope_and_claim_gate") != "PASS" and not (grandfathered and ci.get("scope_and_claim_gate") == "GRANDFATHERED_EXACT_HEAD"):
        return result("WAIT_CI", reason="trusted scope/claim gate required")
    if pr.get("mergeable") is not True:
        return result("WAIT_METADATA", reason="wait for mergeability; never force")
    if review.get("head") != head or review.get("base_main_sha") != main.get("sha"):
        return result("WAIT_REVIEW", reason="review current head against current main")
    try:
        reviewed_at = instant(review["reviewed_at"])
        current = instant(now)
    except (KeyError, ValueError, TypeError):
        return result("WAIT_REVIEW")
    if reviewed_at > current or current - reviewed_at > timedelta(hours=1):
        return result("WAIT_REVIEW", reason="review is stale")
    if review.get("verdict") != "APPROVE" or review.get("blockers"):
        return result("REQUEST_CHANGES", pr=pr["number"], blockers=review.get("blockers", []))
    if any(review.get("checks", {}).get(name) is not True for name in REVIEW_CHECKS):
        return result("WAIT_REVIEW", reason="all review dimensions need evidence")
    return result("MERGE", pr=pr["number"], expected_head_sha=head,
                  review_base_sha=main["sha"], merge_method="merge",
                  post_merge_qa_required=True, roblox_publish_authorized=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="config/autonomous_repair.json")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    policy = json.loads(Path(args.policy).read_text())
    data = json.loads(Path(args.input).read_text())
    print(json.dumps(decide(policy, **data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
