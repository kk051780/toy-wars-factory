"""Decide exact-head integration under delegated authority and a separate review lease."""
import argparse
import fnmatch
import hashlib
from datetime import timedelta
import json
from pathlib import Path, PurePosixPath
import re
from check_auto_diff import is_worker_branch
from repair_control import canonical_id, instant, owns

STATUS_PATHS = {"status/CHAT_HANDOFF.md", "status/LATEST_STATE.json"}
REVIEW_CHECKS = ("scope", "regression", "source_ledger", "protected_controls", "behavior")


def manual_game_scope_violations(entries, policy):
    """Manual game PRs need changed source + NEW regression + NEW history.
    No docs, workflows, policy, executable scripts, deletions or duplicate paths.
    """
    errors = []
    paths = set()
    has_source = has_test = has_history = False
    for status, path in entries:
        if path in paths:
            errors.append("duplicate changed path")
        paths.add(path)
        parts = PurePosixPath(path).parts
        if (not path or path.startswith("/") or "\\" in path or ".." in parts or
                "." in parts or "//" in path):
            errors.append("unsafe changed path")
            continue
        if status == "M" and path in policy["source_paths"]:
            has_source = True
        elif (status == "A" and PurePosixPath(path).parent.as_posix() == "tests/auto" and
              fnmatch.fnmatchcase(path, policy["new_native_test_pattern"])):
            has_test = True
        elif (status == "A" and PurePosixPath(path).parent.as_posix() == "history" and
              fnmatch.fnmatchcase(path, policy["new_history_pattern"])):
            has_history = True
        else:
            errors.append("manual scope does not allow " + status + " " + path)
    if not (has_source and has_test and has_history):
        errors.append("manual game PR requires source + new native regression + new history")
    return errors


def _strict_json_pairs(items):
    result = {}
    for name, value in items:
        if name in result:
            raise ValueError("duplicate key in provider snapshot")
        result[name] = value
    return result


def _git_blob_sha(raw):
    content = raw.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") +
                        b"\x00" + content).hexdigest()


def verified_manual_git_receipts(request, pr, review, claim_state):
    """Check cross-binding of GitHub-fetched evidence.

    API transport AUTHENTICITY remains the responsibility of the registered
    independent REVIEWER. JSON contents and claimed commit SHA are not a
    cryptographic provider signature; reviewer must fetch immutable objects
    through authenticated GitHub access, not from a PR body or author input.
    """
    evidence = review.get("manual_git_evidence")
    if not isinstance(evidence, dict):
        return False
    receipt = evidence.get("claim")
    first = evidence.get("first_commit")
    run = evidence.get("workflow_run")
    jobs = evidence.get("jobs")
    comparison = evidence.get("comparison")
    lineage = evidence.get("first_commit_to_head")
    if not all(isinstance(x, dict) for x in (receipt, first, run, comparison, lineage)):
        return False
    if (receipt.get("repository") != request["repository"] or
            receipt.get("sha") != request["claim_commit"] or
            not isinstance(receipt.get("state_file"), str) or
            not re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("state_blob_sha"))) or
            _git_blob_sha(receipt["state_file"]) != receipt["state_blob_sha"]):
        return False
    # Authenticated reviewer must supply parent and branch ancestry from GitHub.
    parent = evidence.get("claim_parent")
    relation = evidence.get("claim_to_control_ref")
    if not isinstance(parent, dict) or not isinstance(relation, dict):
        return False
    if (not re.fullmatch(r"[0-9a-f]{40}", str(parent.get("sha"))) or
            receipt.get("parents") != [parent["sha"]] or
            not isinstance(parent.get("state_file"), str) or
            _git_blob_sha(parent["state_file"]) != parent.get("state_blob_sha") or
            receipt.get("changed_entries") != [["M", "ops/REPAIR_COORDINATOR.json"]] or
            relation.get("base") != receipt["sha"] or
            not re.fullmatch(r"[0-9a-f]{40}", str(relation.get("head"))) or
            relation.get("status") not in ("ahead", "identical") or
            relation.get("behind_by") != 0 or
            relation.get("head") != evidence.get("current_coordinator_head")):
        return False
    try:
        prior = json.loads(parent["state_file"], object_pairs_hook=_strict_json_pairs)
        fetched = json.loads(receipt["state_file"], object_pairs_hook=_strict_json_pairs)
        if fetched != claim_state or not isinstance(prior, dict):
            return False
        if (prior.get("holder") is not None or
                type(prior.get("epoch")) is not int or
                prior["epoch"] + 1 != claim_state.get("epoch") or
                parent.get("repository") != request["repository"]):
            return False
        # Only epoch and holder may change during a lease acquisition.
        expected = dict(prior)
        expected["epoch"] = prior["epoch"] + 1
        expected["holder"] = claim_state["holder"]
        if fetched != expected:
            return False
        created = instant(first["committer_date"])
        acquired = instant(claim_state["holder"]["acquired_at"])
        expiry = instant(claim_state["holder"]["expires_at"])
        opened = instant(pr["created_at"])
    except (KeyError, ValueError, TypeError, AttributeError):
        return False
    # Claim must precede author work; the PR must be opened during the
    # same active controller lease. Equality with acquire is rejected.
    if not (acquired < created <= opened < expiry):
        return False
    if (first.get("sha") != request.get("author_first_commit") or
            first.get("sha") != pr.get("first_commit_sha") or
            first.get("parents") != [request["base_main_sha"]] or
            not re.fullmatch(r"[0-9a-f]{40}", str(first.get("sha")))):
        return False
    # The independent reviewer fetches GitHub compare(first...head).
    # When first==head, identical is expected; otherwise head must be a
    # descendant of the alleged first commit (behind_by=0).
    if (lineage.get("base") != first["sha"] or
            lineage.get("head") != request["head"] or
            lineage.get("status") != ("identical" if first["sha"] == request["head"] else "ahead") or
            lineage.get("behind_by") != 0):
        return False
    if (type(request.get("ci_run")) is not int or request["ci_run"] <= 0 or
            run.get("id") != request["ci_run"] or
            run.get("head_sha") != request["head"] or
            run.get("status") != "completed" or run.get("conclusion") != "success" or
            run.get("event") not in ("push", "pull_request") or
            run.get("path") != ".github/workflows/bootstrap-quality.yml"):
        return False
    if (not isinstance(jobs, list) or len(jobs) != 2 or
            {j.get("name") for j in jobs if isinstance(j, dict)} != {"offline", "compile_hold"} or
            any(not isinstance(j, dict) or j.get("status") != "completed" or
                j.get("conclusion") != "success" or
                type(j.get("id")) is not int or j["id"] <= 0 or
                j.get("run_id") != request["ci_run"] for j in jobs) or
            len({j["id"] for j in jobs}) != 2):
        return False
    if (comparison.get("base") != request["base_main_sha"] or
            comparison.get("head") != request["head"] or
            comparison.get("behind_by") != 0 or
            comparison.get("entries") != pr.get("changed_entries")):
        return False
    return True


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
    # A PR number is globally unique even if one entry lies about its branch.
    matches = [r for r in candidates if isinstance(r, dict) and
               r.get("number") == pr["number"]]
    if len(matches) != 1 or matches[0].get("branch") != branch:
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
    if manual_game_scope_violations(entries, policy):
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
    # Independently fetched *immutable claim commit* snapshot must match the
    # exact branch. A merely similar/prefix branch name is not enough.
    snapshot = proof.get("claim_state")
    if not isinstance(snapshot, dict) or snapshot.get("epoch") != request["epoch"]:
        return None, "WAIT_MANUAL_PROOF"
    claimed = snapshot.get("holder")
    if not isinstance(claimed, dict) or any(claimed.get(k) != v for k, v in {
        "kind": "CONTROLLER", "owner_id": request["owner_id"],
        "epoch": request["epoch"], "work_branch": branch,
        "base_main_sha": request["base_main_sha"]}.items()):
        return None, "WAIT_MANUAL_PROOF"
    try:
        claimed_at = instant(claimed["acquired_at"])
        expiry = instant(claimed["expires_at"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return None, "WAIT_MANUAL_PROOF"
    if (expiry <= claimed_at or expiry - claimed_at > timedelta(minutes=30) or
            not verified_manual_git_receipts(request, pr, review, snapshot)):
        return None, "WAIT_MANUAL_PROOF"
    for key in ("claim_commit_verified", "main_ancestry_verified",
                "github_diff_verified", "ledger_verified", "ci_jobs_verified"):
        if proof.get(key) is not True:
            return None, "WAIT_MANUAL_PROOF"
    return request, None



def verified_branch_protection(main, policy):
    """Fail-closed live-GitHub-protection evidence contract, NOT an attestation.

    A separate trusted REVIEWER must actually fetch current main branch details
    AND effective branch protection/rulesets from GitHub, then bind these
    fields to the exact main SHA. A PR author, JSON body or local assertion
    must NEVER populate this evidence. This pure function cannot establish
    provider provenance by itself; subsequent merge still needs live checks.
    """
    if type(main) is not dict or type(policy) is not dict:
        return False
    p = main.get("branch_protection")
    if type(p) is not dict:
        return False
    if (p.get("source") != "GITHUB_LIVE_BRANCH_AND_PROTECTION"
            or p.get("repository") != policy.get("repository")
            or p.get("branch") != "main"
            or p.get("head_sha") != main.get("sha")
            or p.get("protected") is not True
            or p.get("require_pull_request") is not True
            or p.get("force_pushes_allowed") is not False
            or p.get("deletions_allowed") is not False
            or p.get("admin_bypass_allowed") is not False):
        return False
    checks = p.get("required_status_checks")
    return (type(checks) is list
            and all(type(x) is str for x in checks)
            and {"offline", "compile_hold"}.issubset(set(checks)))


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
    if not verified_branch_protection(main, policy):
        return result("WAIT_BRANCH_PROTECTION",
                      reason="trusted current-main protection and required PR/CI rules not verified")
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
