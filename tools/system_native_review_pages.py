"""Bounded review-page normalization for a separate, trusted GitHub GET host.

PURE READ ONLY. Fetch and permissions are caller-supplied, NOT authenticated
GitHub proof. The module does not perform network access, obtain credentials,
approve reviews, dispatch jobs, merge code, or attest data completeness.
"""
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

MAX_PAGES = 100
MAX_REVIEWS = 10000
REVIEW_STATES = frozenset(("APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED", "PENDING"))
ROLES = frozenset(("read", "triage", "write", "maintain", "admin"))
LINK_ENTRY = re.compile(r'^<([^<>]+)>; rel="([a-z]+)"$')
REPO = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')
COMMIT_SHA = re.compile(r'^[0-9a-f]{40}$')
LOGIN = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?(?:\[bot\])?$')
ISO_TIME = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$')


class PageError(ValueError):
    """Fixed safe diagnostic; never expose secrets or raw service messages."""
    pass


def next_review_page(header, repo, pr_number, current):
    """Require exact same-repository GitHub API link, sequential next page."""
    if header is None or header == "":
        return None
    if type(header) is not str or len(header) > 16000:
        raise PageError("LINK_INVALID")
    links = {}
    expected = "/repos/" + repo + "/pulls/" + str(pr_number) + "/reviews"
    for piece in header.split(","):
        match = LINK_ENTRY.fullmatch(piece.strip())
        if match is None:
            raise PageError("LINK_MALFORMED")
        url, rel = match.groups()
        if rel in links or rel not in ("next", "last", "first", "prev"):
            raise PageError("LINK_DUPLICATE_OR_UNKNOWN")
        try:
            parts = urlsplit(url)
            if (parts.scheme != "https" or parts.netloc != "api.github.com" or
                    parts.path != expected or parts.username is not None or
                    parts.password is not None or parts.fragment):
                raise PageError("LINK_WRONG_ORIGIN_OR_SCOPE")
            query = parse_qs(parts.query, strict_parsing=True)
            if (set(query) != {"per_page", "page"} or query["per_page"] != ["100"] or
                    len(query["page"]) != 1):
                raise PageError("LINK_QUERY_INVALID")
            s = query["page"][0]
            if re.fullmatch(r"[1-9][0-9]{0,3}", s) is None:
                raise PageError("LINK_QUERY_INVALID")
            page = int(s)
        except ValueError as exc:
            if isinstance(exc, PageError):
                raise
            raise PageError("LINK_QUERY_INVALID") from None
        links[rel] = page
    nxt = links.get("next")
    if nxt is not None and nxt != current + 1:
        raise PageError("LINK_SKIP_OR_LOOP")
    if "prev" in links and links["prev"] != current - 1:
        raise PageError("LINK_PREV_MISMATCH")
    if "first" in links and links["first"] != 1:
        raise PageError("LINK_FIRST_MISMATCH")
    if "last" in links:
        last = links["last"]
        if (last < current or (nxt is not None and last < nxt) or
                (nxt is None and last != current)):
            raise PageError("LINK_LAST_MISMATCH")
    if nxt is not None and nxt > MAX_PAGES:
        raise PageError("TOO_MANY_PAGES")
    return nxt


def collect_pages(fetch, repo, pr_number, permissions):
    """Normalize <=100 pages via strictly scoped supplied GET-only callback.

    fetch(path) returns dict with keys: status, body, link.
    Permissions are caller-supplied and must be verified separately.
    This result intentionally lacks source/complete attestation fields.
    """
    if (not callable(fetch) or type(repo) is not str or
            REPO.fullmatch(repo) is None or type(pr_number) is not int or
            pr_number < 1 or type(permissions) is not dict or
            any(type(k) is not str or k != k.casefold() or type(v) is not str or v not in ROLES
                for k, v in permissions.items())):
        raise PageError("INVALID_INPUT")
    seen, result, page, previous = set(), [], 1, None
    for _ in range(MAX_PAGES):
        path = ("/repos/" + repo + "/pulls/" + str(pr_number) +
                "/reviews?per_page=100&page=" + str(page))
        reply = fetch(path)
        if (type(reply) is not dict or set(reply) != {"status", "body", "link"} or
                type(reply["status"]) is not int or reply["status"] != 200):
            raise PageError("NOT_VERIFIED_200")
        rows = reply["body"]
        if type(rows) is not list or len(rows) > 100:
            raise PageError("PAGE_TOO_LARGE_OR_NOT_LIST")
        for row in rows:
            if type(row) is not dict:
                raise PageError("REVIEW_NOT_OBJECT")
            user = row.get("user")
            if (type(user) is not dict or type(user.get("login")) is not str or
                    user.get("type") not in ("User", "Bot")):
                raise PageError("REVIEW_ACTOR_INVALID")
            login, rid, state = user["login"], row.get("id"), row.get("state")
            if (type(rid) is not int or rid <= 0 or rid in seen or
                    type(state) is not str or state not in REVIEW_STATES or
                    LOGIN.fullmatch(login) is None or
                    login.casefold() not in permissions):
                raise PageError("REVIEW_INVALID_OR_MISSING_ROLE")
            commit = row.get("commit_id")
            if type(commit) is not str or COMMIT_SHA.fullmatch(commit) is None:
                raise PageError("REVIEW_COMMIT_INVALID")
            submitted = row.get("submitted_at")
            if state == "PENDING":
                if submitted is not None:
                    raise PageError("PENDING_HAS_SUBMISSION")
            else:
                if type(submitted) is not str or ISO_TIME.fullmatch(submitted) is None:
                    raise PageError("SUBMITTED_INVALID")
                try:
                    instant = datetime.fromisoformat(submitted.replace("Z", "+00:00"))
                    if instant.tzinfo is None or instant.utcoffset() is None:
                        raise ValueError("timezone required")
                    instant = instant.astimezone(timezone.utc)
                except (ValueError, OverflowError):
                    raise PageError("SUBMITTED_INVALID") from None
                if previous is not None and instant < previous:
                    raise PageError("PAGE_CHRONOLOGY_CHANGED")
                previous = instant
            result.append({"id": rid, "state": state,
                           "commit_id": row.get("commit_id"),
                           "submitted_at": submitted,
                           "user": {"login": login, "type": user["type"]},
                           "reviewer_permission": permissions[login.casefold()]})
            seen.add(rid)
            if len(result) > MAX_REVIEWS:
                raise PageError("TOTAL_REVIEW_LIMIT")
        nxt = next_review_page(reply["link"], repo, pr_number, page)
        if nxt is None:
            return {"repository": repo, "pr_number": pr_number,
                    "reviews": result, "pages_read": page,
                    "provider_authenticated": False, "complete_not_attested": True}
        if len(rows) != 100:
            raise PageError("SHORT_PAGE_WITH_NEXT")
        page = nxt
    raise PageError("PAGE_LIMIT_EXCEEDED")
