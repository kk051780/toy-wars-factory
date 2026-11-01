"""Fail-closed STRUCTURAL native GitHub review preflight.

NO GitHub API, tokens, callbacks, native approvals, merge or reviewer identity
are created here. The external, independent trusted reviewer must obtain all
fields from genuine current GitHub REST responses. A caller-created JSON
object is never proof of real provider provenance or merge eligibility.
"""
from datetime import datetime, timezone, timedelta
import re

SOURCE = "GITHUB_LIVE_PR_REVIEWS_AND_PERMISSIONS"
PERMISSIONS = frozenset(("write", "maintain", "admin"))
USER_TYPES = frozenset(("User", "Bot"))
REVIEW_STATES = frozenset(("APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"))
SHA = re.compile(r"[0-9a-f]{40}\Z")


def _instant(value):
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _login(value):
    if type(value) is not str or not (1 <= len(value) <= 120):
        return None
    if any(ch.isspace() or ord(ch) < 33 for ch in value):
        return None
    return value.casefold()


def verified_native_approval(policy, main, pr, reviewer, now):
    """Check a snapshot's consistency only. NOT an authenticated GitHub read."""
    if any(type(x) is not dict for x in (policy, main, pr, reviewer)):
        return False
    doc = reviewer.get("native_approval")
    if type(doc) is not dict or set(doc) != {
        "source", "repository", "pr_number", "head_sha", "base_main_sha",
        "author_login", "last_pusher_login", "last_push_at", "observed_at",
        "complete", "reviews"}:
        return False
    if doc["source"] != SOURCE or doc["complete"] is not True:
        return False
    repo = policy.get("repository")
    branch = main.get("branch_protection")
    if type(repo) is not str or type(branch) is not dict:
        return False
    required = branch.get("required_approving_review_count")
    if type(required) is not int or not (1 <= required <= 6):
        return False
    number = pr.get("number")
    sha = pr.get("head")
    base = main.get("sha")
    if type(number) is not int or number <= 0:
        return False
    if type(sha) is not str or type(base) is not str or SHA.fullmatch(sha) is None or SHA.fullmatch(base) is None:
        return False
    if (doc["repository"] != repo or doc["pr_number"] != number or
            doc["head_sha"] != sha or doc["base_main_sha"] != base):
        return False
    author = _login(pr.get("author_login"))
    pusher = _login(pr.get("last_pusher_login"))
    if not author or not pusher:
        return False
    if _login(doc["author_login"]) != author or _login(doc["last_pusher_login"]) != pusher:
        return False
    last_push = _instant(pr.get("last_push_at"))
    current = _instant(now)
    observed = _instant(doc.get("observed_at"))
    if (last_push is None or observed is None or current is None or
            doc["last_push_at"] != pr["last_push_at"] or
            last_push > observed or observed > current or
            current - observed > timedelta(hours=1)):
        return False
    reviews = doc.get("reviews")
    # A complete paginated history may exceed a single GitHub REST page.
    # Never truncate unknown adverse decisions; reject implausibly large input.
    if type(reviews) is not list or not (required <= len(reviews) <= 10_000):
        return False
    seen_ids = set()
    effective = {}
    previous_at = None
    for entry in reviews:
        if type(entry) is not dict or set(entry) != {
            "id", "state", "commit_id", "submitted_at", "user", "reviewer_permission"
        }:
            return False
        user = entry.get("user")
        if type(user) is not dict or set(user) != {"login", "type"}:
            return False
        login, submitted = _login(user.get("login")), _instant(entry.get("submitted_at"))
        rid, state, commit_id = entry.get("id"), entry.get("state"), entry.get("commit_id")
        permission = entry.get("reviewer_permission")
        if (type(rid) is not int or rid <= 0 or rid in seen_ids or not login or
                type(user["type"]) is not str or user["type"] not in USER_TYPES or
                type(state) is not str or state not in REVIEW_STATES or
                type(commit_id) is not str or SHA.fullmatch(commit_id) is None or
                type(permission) is not str or
                permission not in ("read", "triage", *PERMISSIONS) or
                submitted is None or submitted > observed or
                (previous_at is not None and submitted < previous_at)):
            return False
        seen_ids.add(rid)
        previous_at = submitted
        # COMMENTED has no decisive vote; never erase a prior valid approval.
        if state == "COMMENTED":
            continue
        # The author and last pusher can never contribute decisive review votes.
        if login in (author, pusher) and state in ("APPROVED", "CHANGES_REQUESTED"):
            return False
        # Last decisive state per reviewer wins; stale/latest unqualified approval
        # must not silently revive a previously approved decision.
        effective[login] = (
            state if (state != "APPROVED" or
                      (commit_id == sha and submitted >= last_push and
                       permission in PERMISSIONS)) else "UNQUALIFIED"
        )
        if state == "CHANGES_REQUESTED" and permission not in PERMISSIONS:
            return False
    # A different reviewer's still-effective request for changes blocks.
    if "CHANGES_REQUESTED" in effective.values():
        return False
    return sum(value == "APPROVED" for value in effective.values()) >= required
