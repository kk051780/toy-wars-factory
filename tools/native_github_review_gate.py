"""Fail-closed STRUCTURAL native GitHub review preflight.

NO GitHub API, tokens, callbacks, native approvals, merge or reviewer identity
are created here. The external, independent trusted reviewer must obtain all
fields from genuine current GitHub REST responses. A caller-created JSON
object is never proof of real provider provenance or merge eligibility.
"""
from datetime import datetime, timezone, timedelta

SOURCE = "GITHUB_LIVE_PR_REVIEWS_AND_PERMISSIONS"
PERMISSIONS = frozenset(("write", "maintain", "admin"))
USER_TYPES = frozenset(("User", "Bot"))


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
    if type(sha) is not str or type(base) is not str or len(sha) != 40 or len(base) != 40:
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
    if type(reviews) is not list or not (required <= len(reviews) <= 100):
        return False
    ids, actors = set(), set()
    for entry in reviews:
        if type(entry) is not dict or set(entry) != {
            "id", "state", "commit_id", "submitted_at", "user", "reviewer_permission"}:
            return False
        identity = entry.get("user")
        if type(identity) is not dict or set(identity) != {"login", "type"}:
            return False
        login = _login(identity["login"])
        review_at = _instant(entry["submitted_at"])
        rid = entry["id"]
        if (type(rid) is not int or rid <= 0 or rid in ids or not login or
                login == author or login == pusher or login in actors or
                identity["type"] not in USER_TYPES or
                entry["state"] != "APPROVED" or entry["commit_id"] != sha or
                type(entry["reviewer_permission"]) is not str or
                entry["reviewer_permission"] not in PERMISSIONS or
                review_at is None or not last_push <= review_at <= observed):
            return False
        ids.add(rid)
        actors.add(login)
    return len(actors) >= required
