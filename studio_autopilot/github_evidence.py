"""P2: authenticated, GET-only GitHub facts for exactly one bound game.

No provider calls, Roblox access, GitHub writes, authorization or dispatch.
Untrusted observations from the P1 planner never become permission to execute.
"""
import argparse
import base64
import binascii
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from studio_autopilot.core import InvalidProject, SHA, validate_project

API_ORIGIN = "https://api.github.com"
CHECKS = ("offline", "compile_hold")
MAX_BYTES = 1048576


class EvidenceUnavailable(ValueError):
    """Ambiguity, unavailable authorization or mismatched data: fail closed."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EvidenceUnavailable("redirect blocked")


def _fetch_https(url, token):
    req = urllib.request.Request(
        url,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "studio-autopilot-evidence/0.2"},
        method="GET",
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=8) as response:
            if response.status != 200:
                raise EvidenceUnavailable("GitHub HTTP status was not 200")
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise EvidenceUnavailable("oversized response")
    except EvidenceUnavailable:
        raise
    except urllib.error.HTTPError as exc:
        raise EvidenceUnavailable("GitHub HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError):
        raise EvidenceUnavailable("GitHub API network unavailable") from None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise EvidenceUnavailable("invalid API JSON") from None
    if type(value) is not dict:
        raise EvidenceUnavailable("unexpected API JSON type")
    return value


class GitHubReadOnlyClient:
    """Single-repo, fixed-origin GETs. Token never appears in evidence output."""

    def __init__(self, repository, token, *, http_fetch=None):
        if type(repository) is not str or re.fullmatch(
                r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
            raise EvidenceUnavailable("invalid repository selection")
        if type(token) is not str or not token:
            raise EvidenceUnavailable("missing scoped token")
        self.repository = repository
        self._token = token
        self._fetch = http_fetch if http_fetch is not None else _fetch_https
        self._origin = API_ORIGIN + "/repos/" + repository + "/"

    def get(self, path):
        if (type(path) is not str or not path or path.startswith("/") or
                "://" in path or "\\" in path or ".." in path or
                "\n" in path or "\r" in path or "#" in path):
            raise EvidenceUnavailable("invalid API subpath")
        result = self._fetch(self._origin + path, self._token)
        if type(result) is not dict:
            raise EvidenceUnavailable("invalid API document")
        return result


def _sha(value):
    if type(value) is not str or SHA.fullmatch(value) is None:
        raise EvidenceUnavailable("invalid exact SHA")
    return value


def _ref(client, branch):
    if type(branch) is not str or re.fullmatch(r"[a-z][a-z0-9-]*", branch) is None:
        raise EvidenceUnavailable("unsupported branch")
    record = client.get("git/ref/heads/" + branch)
    if record.get("ref") != "refs/heads/" + branch or type(record.get("object")) is not dict:
        raise EvidenceUnavailable("branch identity mismatch")
    return _sha(record["object"].get("sha"))


def _checks(client, commit_sha):
    records = client.get("commits/" + _sha(commit_sha) + "/check-runs?per_page=100")
    items = records.get("check_runs")
    count = records.get("total_count")
    if (type(items) is not list or type(count) is not int or
            count != len(items) or count > 100):
        raise EvidenceUnavailable("incomplete/ambiguous check-run page")
    if any(type(item) is not dict or item.get("head_sha") != commit_sha for item in items):
        raise EvidenceUnavailable("foreign/stale check-run SHA")
    matches = []
    for name in CHECKS:
        named = [x for x in items if x.get("name") == name]
        passed = (len(named) == 1 and named[0].get("status") == "completed" and
                  named[0].get("conclusion") == "success")
        matches.append({"name": name, "status": "PASS" if passed else "HOLD"})
    return {"status": "PASS" if all(x["status"] == "PASS" for x in matches)
            else "HOLD_EXACT_HEAD_CHECKS", "required": matches}


def _coordinator(client, sha, roles):
    # The contents ref is the OBSERVED COMMIT, not a moving branch.
    result = client.get("contents/ops/REPAIR_COORDINATOR.json?ref=" + _sha(sha))
    if result.get("encoding") != "base64" or type(result.get("content")) is not str:
        raise EvidenceUnavailable("missing coordinator contents")
    try:
        data = base64.b64decode(result["content"], validate=False)
        if len(data) > 131072:
            raise EvidenceUnavailable("coordinator content exceeds bound")
        state = json.loads(data.decode("utf-8"))
    except (ValueError, binascii.Error, UnicodeError):
        raise EvidenceUnavailable("invalid coordinator document") from None
    if type(state) is not dict or type(state.get("epoch")) is not int:
        raise EvidenceUnavailable("invalid coordinator epoch")
    tasks = state.get("authorized_tasks")
    if type(tasks) is not dict or any(
            tasks.get(label) != roles[role]
            for role, label in (("author", "WORKER"), ("reviewer", "REVIEWER"), ("meta", "META"))):
        raise EvidenceUnavailable("registered task identities mismatch project")
    if "holder" not in state:
        raise EvidenceUnavailable("missing shared lease state")
    holder = state["holder"]
    if holder is not None and (type(holder) is not dict or
                               type(holder.get("kind")) is not str or
                               type(holder.get("owner_id")) is not str):
        raise EvidenceUnavailable("invalid lease holder")
    return {"sha": sha, "epoch": state["epoch"],
            "lease_observation": "IDLE_AT_READ" if holder is None else "OCCUPIED_AT_READ",
            "task_identities_match": True}


def _pr(client, number, repo, main_sha):
    if type(number) is not int or not 1 <= number <= 10000000:
        raise EvidenceUnavailable("invalid PR number")
    data = client.get("pulls/" + str(number))
    head, base = data.get("head"), data.get("base")
    if data.get("number") != number or type(head) is not dict or type(base) is not dict:
        raise EvidenceUnavailable("invalid PR structure")
    if (type(head.get("repo")) is not dict or type(base.get("repo")) is not dict or
            head["repo"].get("full_name") != repo or
            base["repo"].get("full_name") != repo or base.get("ref") != "main"):
        raise EvidenceUnavailable("cross-repo/fork PR or wrong base refused")
    h, b = _sha(head.get("sha")), _sha(base.get("sha"))
    if type(data.get("draft")) is not bool or data.get("state") not in ("open", "closed"):
        raise EvidenceUnavailable("invalid PR state")
    return {"number": number, "head": h, "base": b,
            "base_matches_main": b == main_sha, "draft": data["draft"],
            "state": data["state"], "checks": _checks(client, h)}


def collect(project, client, *, pr_number=None):
    """Retrieve current GitHub REST state; output is NEVER execution authority."""
    project = validate_project(project)
    if project["phase"] != "BOUND_OBSERVE":
        raise EvidenceUnavailable("unbound template cannot read game repository")
    if type(client) is not GitHubReadOnlyClient or client.repository != project["repository"]:
        raise EvidenceUnavailable("foreign/replaced repository client")
    repo = project["repository"]
    main_sha = _ref(client, "main")
    coord_sha = _ref(client, project["coordination_ref"])
    main_checks = _checks(client, main_sha)
    coordinator = _coordinator(client, coord_sha, project["roles"])
    pr = _pr(client, pr_number, repo, main_sha) if pr_number is not None else None
    # Conservative race detection. These are not permission tickets or CAS locks.
    if _ref(client, "main") != main_sha or _ref(client, project["coordination_ref"]) != coord_sha:
        raise EvidenceUnavailable("GitHub references moved while reading")
    if pr is not None:
        reread = client.get("pulls/" + str(pr_number))
        if (type(reread.get("head")) is not dict or
                reread["head"].get("sha") != pr["head"] or
                type(reread.get("base")) is not dict or
                reread["base"].get("sha") != pr["base"]):
            raise EvidenceUnavailable("PR head/base moved while reading")
    return {"schema": 1, "game_id": project["game_id"], "repository": repo,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": "AUTHENTICATED_GITHUB_API_READ_ONLY",
            "main": {"sha": main_sha, "checks": main_checks},
            "coordinator": coordinator, "pr": pr,
            "execution": {"dispatch_allowed": False, "merge_allowed": False,
                          "publish_allowed": False, "spending_allowed": False},
            "scope": "LIVE_REPOSITORY_METADATA_ONLY_NO_ENGINE_OR_PLAYTEST"}


def main():
    parser = argparse.ArgumentParser(description="Get live GitHub metadata with read-only permissions.")
    parser.add_argument("--project", default="studio_autopilot/projects/toy_wars.json")
    parser.add_argument("--pr", type=int, default=None)
    args = parser.parse_args()
    try:
        path = Path(args.project)
        if (path.is_absolute() or path.suffix != ".json" or
                not path.as_posix().startswith("studio_autopilot/projects/") or
                ".." in path.parts or path.is_symlink()):
            raise EvidenceUnavailable("invalid project manifest path")
        project = validate_project(json.loads(path.read_text(encoding="utf-8")))
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        if repo != project["repository"]:
            raise EvidenceUnavailable("Actions repo identity differs from configured game")
        token = os.environ.get("GITHUB_TOKEN", "")
        result = collect(project, GitHubReadOnlyClient(repo, token), pr_number=args.pr)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    except (EvidenceUnavailable, InvalidProject, ValueError, UnicodeError, OSError) as exc:
        parser.exit(2, "EVIDENCE_HOLD: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
