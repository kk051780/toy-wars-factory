"""Decide exact-head integration under delegated authority and a separate review lease."""
import argparse
from datetime import timedelta
import json
from pathlib import Path
import re
from check_auto_diff import is_worker_branch, violations as game_scope_violations
from repair_control import canonical_id, instant, owns

STATUS_PATHS = {"status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"}
REVIEW_CHECKS = ("scope", "regression", "source_ledger", "protected_controls", "behavior")


def verified_manual_request(policy, lease, pr, review, main):
    """Fail-closed, immutable-head manual CONTROLLER review gate.

    The registered independent reviewer must re-fetch GitHub refs, compare the
    real changed-path/status list, and verify the historical claim commit.
    This pure decision layer checks the reviewer's bound evidence; it cannot
    independently authenticate a GitHub claim or CI receipt.
    """
    integration = policy.get("integration", {})
    settings = integration.get("manual_controller_reviews", {})
    branch = pr.get("branch")
    if settings.get("enabled") is not True or not isinstance(branch, str):
        return None, "SKIP_UNRELATED"
    prefix = settings.get("branch_prefix")
    if not isinstance(prefix, str) or len(prefix) < 12 or not branch.startswith(prefix):
        return None, "SKIP_UNRELATED"
    if not isinstance(pr.get("number"), int) or type(pr.get("number")) is bool:
        return None, "WAIT_MANUAL_REQUEST"
    candidates = lease.get("manual_review_requests", [])
    if not isinstance(candidates, list):
        return None, "WAIT_MANUAL_REQUEST"
    matches = [r for r in candidates if isinstance(r, dict) and
               r.get("number") == pr["number"] and r.get("branch") == branch]
    if len(matches) != 1:
        return None, "WAIT_MANUAL_REQUEST"
    request = matches[0]
    exact = {
        "repository": policy.get("repository"),
        "head": pr.get("head"),
        "base_main_sha": main.get("sha"),
        "reviewer_task_id": integration.get("task_id"),
        "kind": "CONTROLLER",
    }
    if any(request.get(k) != v for k, v in exact.items()):
        return None, "WAIT_MANUAL_REQUEST"
    if (not isinstance(request.get("claim_commit"), str) or
            not re.fullmatch(r"[0-9a-f]{40}", request["claim_commit"]) or
            type(request.get("epoch")) is not int or request["epoch"] <= 0):
        return None, "WAIT_MANUAL_REQUEST"
    try:
        canonical_id(request.get("owner_id"))
    except (ValueError, TypeError, AttributeError):
        return None, "WAIT_MANUAL_REQUEST"
    if (pr.get("author_task_id") is not None or
            pr.get("author_run_id") != request["owner_id"]):
        return None, "WAIT_AUTHOR_ID"
    # Reviewers must corroborate the real diff from GitHub. Merely describing
    # an allowed PR number in a PR body is never sufficient.
    entries = pr.get("changed_entries")
    if (not isinstance(entries, list) or not entries or
            any(not isinstance(x, (list, tuple)) or len(x) != 2 or
                not all(isinstance(y, str) for y in x) for x in entries)):
        return None, "WAIT_MANUAL_SCOPE"
    if game_scope_violations(entries, policy):
        return None, "WAIT_MANUAL_SCOPE"
    proof = review.get("manual_provenance")
    if not isinstance(proof, dict):
        return None, "WAIT_MANUAL_PROOF"
    proof_exact = {k: request.get(k) for k in
                   ("claim_commit", "epoch", "owner_id", "head", "base_main_sha", "branch")}
    if any(proof.get(k) != v for k, v in proof_exact.items()):
        return None, "WAIT_MANUAL_PROOF"
    if proof.get("changed_entries") != entries:
        return None, "WAIT_MANUAL_PROOF"
    for key in ("claim_commit_verified", "main_ancestry_verified",
                "github_diff_verified", "ledger_verified", "ci_jobs_verified"):
        if proof.get(key) is not True:
            return None, "WAIT_MANUAL_PROOF"
    return request, None


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
            lease.get("authorized_tasks", {}).get("REVIEWER") != integration["task_id"] or
            (lease.get("holder") or {}).get("task_id") != integration["task_id"] or
            not owns(lease, "REVIEWER", reviewer_id, review.get("lease_epoch"), now) or
            lease["holder"].get("work_branch") != "main"):
        return result("WAIT_LOCK", reason="current registered independent reviewer lease required")
    if any(not isinstance(main.get(key), str) or not re.fullmatch(r"[0-9a-f]{40}", main[key])
           for key in ("sha", "qa_head")):
        return result("WAIT_MAIN_CI", reason="canonical main and tested-main identities required")
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
    if pr.get("repository") != policy["repository"] or pr.get("state") != "open":
        return result("SKIP_UNRELATED")
    worker = is_worker_branch(branch, policy)
    manual_config = integration.get("manual_controller_reviews", {})
    manual_prefix = manual_config.get("branch_prefix")
    manual = (manual_config.get("enabled") is True and
              isinstance(manual_prefix, str) and len(manual_prefix) >= 12 and
              isinstance(branch, str) and branch.startswith(manual_prefix))
    if not (worker or meta or manual):
        return result("SKIP_UNRELATED")
    if manual:
        request, error = verified_manual_request(policy, lease, pr, review, main)
        if error is not None:
            return result(error, reason="manual CONTROLLER provenance or path scope not verified")
    else:
        author_task = policy["system_review"]["task_id"] if meta else policy["task_id"]
        if pr.get("author_task_id") != author_task:
            return result("WAIT_AUTHOR_ID")
        try:
            canonical_id(pr.get("author_run_id"))
        except (ValueError, TypeError, AttributeError):
            return result("WAIT_AUTHOR_ID", reason="canonical author run is required")
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
    if manual:
        if ci.get("scope_and_claim_gate") != "MANUAL_CONTROLLER_ATTESTED":
            return result("WAIT_CI", reason="independent manual claim and source-scope proof required")
    elif ci.get("scope_and_claim_gate") != "PASS" and not (grandfathered and ci.get("scope_and_claim_gate") == "GRANDFATHERED_EXACT_HEAD"):
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
