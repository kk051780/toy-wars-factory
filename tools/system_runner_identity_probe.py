"""Read-only GitHub Actions run-context consistency probe; NEVER actor attestation.
No chat task identity, lease, job dispatch, GitHub write or release authority.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
import re
import sys
from urllib.request import Request, build_opener, HTTPRedirectHandler

REPO = "kk051780/toy-wars-factory"
WORKFLOW = ".github/workflows/twf-runner-identity-probe.yml"
SHA = re.compile(r"[0-9a-f]{40}\Z")
ID = re.compile(r"[1-9][0-9]{0,18}\Z")

class NotVerified(ValueError):
    """Fixed safe error code, never raw provider response or credential."""

class _NoRedirect(HTTPRedirectHandler):
    """Never follow redirects while carrying scoped GitHub bearer credentials."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Neither destination URL nor secret token may enter an exception string.
        raise NotVerified("REDIRECT_REFUSED")

_SAFE_OPEN = build_opener(_NoRedirect()).open

def require(ok, code):
    if not ok:
        raise NotVerified(code)

def exact_int(x, minimum=1):
    return type(x) is int and minimum <= x <= 2**63-1

def parse_json(payload):
    require(type(payload) is str and len(payload.encode("utf-8")) <= 262144, "INVALID_RESPONSE")
    def no_dupes(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    try:
        return json.loads(payload, object_pairs_hook=no_dupes,
                          parse_constant=lambda _: require(False, "NONFINITE_JSON"))
    except (json.JSONDecodeError, UnicodeError, RecursionError):
        raise NotVerified("INVALID_JSON") from None

def check(context, run, branch):
    """Consistency of caller-supplied structures only, NEVER provenance."""
    require(type(context) is dict, "INVALID_CONTEXT")
    fields = {"repository", "run_id", "run_attempt", "ref", "sha", "event_name", "workflow_ref"}
    require(set(context) == fields and all(type(context[k]) is str for k in fields), "INVALID_CONTEXT")
    require(context["repository"] == REPO, "FOREIGN_REPO")
    require(context["event_name"] == "workflow_dispatch", "FOREIGN_EVENT")
    require(context["ref"] == "refs/heads/main", "FOREIGN_REF")
    require(context["workflow_ref"] == f"{REPO}/{WORKFLOW}@refs/heads/main", "FOREIGN_WORKFLOW")
    require(bool(SHA.fullmatch(context["sha"])), "INVALID_HEAD")
    require(bool(ID.fullmatch(context["run_id"])) and bool(ID.fullmatch(context["run_attempt"])), "INVALID_RUN_ID")
    rid, attempt = int(context["run_id"]), int(context["run_attempt"])
    require(exact_int(rid) and exact_int(attempt), "INVALID_RUN_ID")
    require(type(run) is dict and type(run.get("repository")) is dict, "MISSING_RUN")
    require(run["repository"].get("full_name") == REPO, "FOREIGN_RUN_REPO")
    require(type(run.get("id")) is int and run.get("id") == rid, "WRONG_RUN")
    require(type(run.get("run_attempt")) is int and run.get("run_attempt") == attempt, "WRONG_ATTEMPT")
    require(run.get("event") == "workflow_dispatch", "WRONG_RUN_EVENT")
    require(run.get("head_branch") == "main", "WRONG_RUN_BRANCH")
    require(run.get("path") == WORKFLOW, "WRONG_RUN_WORKFLOW")
    require(run.get("head_sha") == context["sha"], "WRONG_RUN_HEAD")
    require(run.get("status") == "in_progress", "RUN_NOT_IN_PROGRESS")
    require(exact_int(run.get("workflow_id")), "INVALID_WORKFLOW_ID")
    require(type(branch) is dict and type(branch.get("commit")) is dict, "MISSING_MAIN")
    require(branch.get("name") == "main", "WRONG_MAIN_BRANCH")
    require(branch["commit"].get("sha") == context["sha"], "MAIN_MOVED")
    return {"schema": 1,
            "status": "CONSISTENT_LOCAL_GITHUB_ACTIONS_VIEW_NOT_PORTABLE_ATTESTATION",
            "repository": REPO, "workflow_path": WORKFLOW, "run_id": rid,
            "run_attempt": attempt, "source_sha": context["sha"],
            "observation_time_utc": datetime.now(timezone.utc).isoformat(),
            "github_api_consistent": True,
            "current_chatgpt_run_attested": False, "external_verifier_attested": False,
            "cas_performed": False, "may_write": False, "may_dispatch": False,
            "may_merge": False, "may_publish": False, "may_spend": False, "may_retry": False}

def github_get(path, token):
    require(type(token) is str and bool(token), "MISSING_TOKEN")
    require(path == f"/repos/{REPO}/branches/main" or bool(re.fullmatch(
        rf"/repos/{re.escape(REPO)}/actions/runs/[1-9][0-9]{{0,18}}", path)), "UNSCOPED_GET")
    req = Request("https://api.github.com" + path,
                  headers={"Accept": "application/vnd.github+json",
                           "Authorization": "Bearer " + token,
                           "X-GitHub-Api-Version": "2022-11-28",
                           "User-Agent": "twf-runner-identity-readonly"})
    try:
        with _SAFE_OPEN(req, timeout=12) as response:
            require(response.status == 200, "GET_NOT_OK")
            payload = response.read(262145)
    except Exception:
        raise NotVerified("GET_UNAVAILABLE") from None
    require(len(payload) <= 262144, "INVALID_RESPONSE")
    try:
        return parse_json(payload.decode("utf-8", "strict"))
    except UnicodeDecodeError:
        raise NotVerified("INVALID_RESPONSE") from None

def main():
    keys = ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_REF",
            "GITHUB_SHA", "GITHUB_EVENT_NAME", "GITHUB_WORKFLOW_REF")
    fields = ("repository", "run_id", "run_attempt", "ref", "sha", "event_name", "workflow_ref")
    context = dict(zip(fields, [os.environ.get(k, "") for k in keys]))
    try:
        require(context["repository"] == REPO and context["ref"] == "refs/heads/main" and
                context["event_name"] == "workflow_dispatch" and
                context["workflow_ref"] == f"{REPO}/{WORKFLOW}@refs/heads/main" and
                bool(SHA.fullmatch(context["sha"])) and bool(ID.fullmatch(context["run_id"])) and
                bool(ID.fullmatch(context["run_attempt"])), "INVALID_LOCAL_CONTEXT")
        token = os.environ.get("GH_TOKEN", "")
        run_path = f"/repos/{REPO}/actions/runs/{context['run_id']}"
        run = github_get(run_path, token)
        branch = github_get(f"/repos/{REPO}/branches/main", token)
        receipt = check(context, run, branch)
        reread = github_get(run_path, token)
        require(reread.get("id") == run.get("id") and
                reread.get("head_sha") == run.get("head_sha") and
                reread.get("run_attempt") == run.get("run_attempt") and
                reread.get("status") in ("in_progress", "completed"), "RUN_CHANGED")
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return 0
    except NotVerified as exc:
        print(json.dumps({"schema": 1, "status": "NOT_VERIFIED", "reason": str(exc),
                          "may_write": False, "may_dispatch": False}), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
