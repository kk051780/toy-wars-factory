"""Manual-only, owner-controlled GitHub Actions isolated write capability probe.

NOT a ChatGPT Automations identity bridge, AI agent, or production source writer.
Only a reviewed workflow on default main can invoke this with its ephemeral token.
The acquired coordinator epoch is always released by its own owner if possible;
loss of process/network can still orphan a lease and must NOT be auto-recovered.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
from datetime import datetime, timezone
import json
import os
import re
import sys
import uuid
from urllib import request, error
from typing import Callable

from repair_control import acquire, owns, release, validate

REPO = "kk051780/toy-wars-factory"
REPO_ID = 1431683395
ACTOR = "kk051780"
WORKFLOW = ".github/workflows/twf-actions-write-capability-probe.yml"
CONTROL_REF = "twf-repair-coordinator"
CONTROL_PATH = "ops/REPAIR_COORDINATOR.json"
CONSENT = "I_AUTHORIZE_ISOLATED_DRAFT_PR_ONLY"
HEX = re.compile(r"[0-9a-f]{40}\Z")


class ProbeError(Exception):
    """No raw network error or secret permitted in the user-facing diagnostic."""
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def valid_sha(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def checked_context(env: dict, live_run: dict, live_main: str):
    """Live API data is only authoritative inside a trusted GitHub-hosted job."""
    required = ("GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_ACTOR",
                "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_WORKFLOW_REF",
                "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_TRIGGERING_ACTOR", "GITHUB_SHA", "PROBE_CONSENT")
    if any(not isinstance(env.get(key), str) for key in required):
        raise ProbeError("CONTEXT_MISSING")
    if (env["GITHUB_REPOSITORY"] != REPO or env["GITHUB_REPOSITORY_ID"] != str(REPO_ID) or
            env["GITHUB_ACTOR"] != ACTOR or env["GITHUB_TRIGGERING_ACTOR"] != ACTOR or env["GITHUB_EVENT_NAME"] != "workflow_dispatch" or
            env["GITHUB_REF"] != "refs/heads/main" or
            env["GITHUB_WORKFLOW_REF"] != f"{REPO}/{WORKFLOW}@refs/heads/main" or
            env["PROBE_CONSENT"] != CONSENT):
        raise ProbeError("CONTEXT_DENIED")
    run_id, attempt = env["GITHUB_RUN_ID"], env["GITHUB_RUN_ATTEMPT"]
    if (not re.fullmatch(r"[1-9][0-9]{0,17}", run_id) or
            attempt != "1" or
            not valid_sha(env["GITHUB_SHA"]) or not valid_sha(live_main)):
        raise ProbeError("INVALID_SOURCE_LINEAGE")
    if not isinstance(live_run, dict) or (
        live_run.get("id") != int(run_id) or live_run.get("run_attempt") != int(attempt) or
        live_run.get("event") != "workflow_dispatch" or
        live_run.get("path") != WORKFLOW or
        live_run.get("head_repository", {}).get("id") != REPO_ID or
        live_run.get("actor", {}).get("login") != ACTOR or
        live_run.get("triggering_actor", {}).get("login") != ACTOR or
        live_run.get("head_branch") != "main" or
        live_run.get("head_sha") != env["GITHUB_SHA"] or live_main != env["GITHUB_SHA"]):
        raise ProbeError("LIVE_RUN_LINEAGE_MISMATCH")
    branch = f"controller/gha-write-probe-{run_id}-a{attempt}"
    owner = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{REPO}:{WORKFLOW}:{run_id}:{attempt}"))
    return {"owner":owner, "branch":branch, "main":live_main,
            "run_id":int(run_id), "attempt":int(attempt)}


class _RejectRedirects(request.HTTPRedirectHandler):
    """Keep Authorization on the original GitHub API origin only.

    urllib's normal HTTPRedirectHandler copies Authorization on redirect,
    including cross-origin 301/302/303/307/308. The privileged workflow
    never needs redirects for its fixed REST API paths.
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeError("GITHUB_REDIRECT_DENIED")


class GitHubAPI:
    """Fixed-host REST transport, bounded source and sanitized error codes."""
    def __init__(self, token: str, transport: Callable | None = None):
        if not token:
            raise ProbeError("TOKEN_ABSENT")
        self._token = token
        # The default urllib opener forwards Authorization on redirects.
        # No redirects are permitted for this bearer-bearing GitHub API client.
        # Dependency-injected transports are for offline testing only.
        self._transport = (transport if transport is not None
                           else request.build_opener(_RejectRedirects()).open)

    def call(self, method: str, suffix: str, body=None):
        if (method not in ("GET", "POST", "PATCH", "PUT") or
                not isinstance(suffix, str) or
                not suffix.startswith("/") or
                (".." in suffix and not (method == "GET" and
                    re.fullmatch(r"/compare/[0-9a-f]{40}\.\.\.[0-9a-f]{40}", suffix))) or
                not re.fullmatch(r"/[A-Za-z0-9_./?=&-]+", suffix)):
            raise ProbeError("INVALID_API_PATH")
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf8")
        req = request.Request("https://api.github.com/repos/"+REPO+suffix,
            data=data, method=method, headers={
            "Authorization": "Bearer "+self._token,
            "Accept": "application/vnd.github+json",
            "Content-Type":"application/json",
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"toy-wars-isolated-write-probe"})
        try:
            with self._transport(req, timeout=12) as resp:
                raw = resp.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ProbeError("RESPONSE_TOO_LARGE")
                row = json.loads(raw)
                if not isinstance(row, dict):
                    raise ProbeError("RESPONSE_INVALID")
                return row
        except error.HTTPError as exc:
            raise ProbeError("GITHUB_HTTP_"+str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError):
            raise ProbeError("GITHUB_TRANSPORT_FAILED") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ProbeError("RESPONSE_INVALID") from None


def sha_ref(api, name):
    res = api.call("GET", f"/git/ref/heads/{name}")
    val = res.get("object", {}).get("sha")
    if not valid_sha(val):
        raise ProbeError("REF_INVALID")
    return val


def state_at(api, refsha):
    row = api.call("GET", f"/contents/{CONTROL_PATH}?ref={refsha}")
    if row.get("encoding") != "base64" or row.get("type") != "file":
        raise ProbeError("STATE_BLOB_INVALID")
    try:
        decoded = base64.b64decode("".join(row["content"].split()), validate=True)
        obj = json.loads(decoded)
        if not isinstance(obj, dict):
            raise ValueError()
        validate(obj)
    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
        raise ProbeError("STATE_INVALID") from None
    return obj


def cas_state(api, oldref, newstate):
    """Immutable old-parent, non-force fast-forward + exact postwrite reread."""
    commit = api.call("GET", f"/git/commits/{oldref}")
    base_tree = commit.get("tree", {}).get("sha")
    if not valid_sha(base_tree):
        raise ProbeError("CONTROL_TREE_INVALID")
    blob = api.call("POST", "/git/blobs", {"content":json.dumps(newstate,indent=2)+"\n", "encoding":"utf-8"})
    tree = api.call("POST", "/git/trees", {"base_tree":base_tree,"tree":[{
        "path":CONTROL_PATH,"mode":"100644","type":"blob","sha":blob.get("sha")}]})
    fresh = api.call("POST", "/git/commits", {"message":"coordination: fenced manual GitHub Actions capability probe",
        "tree":tree.get("sha"),"parents":[oldref]})
    newsha = fresh.get("sha")
    if not valid_sha(newsha):
        raise ProbeError("CONTROL_NEW_COMMIT_INVALID")
    api.call("PATCH", f"/git/refs/heads/{CONTROL_REF}", {"sha":newsha,"force":False})
    # Reconfirm the live ref after reading state; a concurrent ref move
    # must not be acknowledged as an owned coordinator lease.
    if (sha_ref(api, CONTROL_REF) != newsha or
            state_at(api, newsha) != newstate or
            sha_ref(api, CONTROL_REF) != newsha):
        raise ProbeError("CONTROL_CAS_READBACK_UNCONFIRMED")
    return newsha



def verify_created_probe(api, scope, number):
    """Require independent exact Git GET readbacks after a draft-PR write.

    Readbacks bind the new branch commit, one-file diff, exact Git blob
    and still-open draft PR to the original main. This validates API
    consistency, NOT provider identity outside the reviewed Actions host.
    """
    if type(number) is not int or number < 1:
        raise ProbeError("PR_RESPONSE_UNVERIFIED")
    main_sha, branch = scope.get("main"), scope.get("branch")
    run_id, attempt = scope.get("run_id"), scope.get("attempt")
    if (not valid_sha(main_sha) or
            type(run_id) is not int or run_id < 1 or type(attempt) is not int or attempt != 1 or
            branch != f"controller/gha-write-probe-{run_id}-a{attempt}"):
        raise ProbeError("PROBE_SCOPE_INVALID")
    filename = f"ops/probes/gha-write-{run_id}-a{attempt}.json"
    expected = {"schema":1,"kind":"OWNER_MANUAL_GHA_CAPABILITY_PROBE_ONLY",
                "source_main_sha":main_sha,"github_run_id":run_id,
                "run_attempt":attempt,"status":"NO_AI_NO_GAME_CHANGE"}
    expected_raw = (json.dumps(expected,sort_keys=True)+"\n").encode("utf8")

    if sha_ref(api,"main") != main_sha:
        raise ProbeError("MAIN_CHANGED_AFTER_WRITE")
    branch_sha = sha_ref(api,branch)
    if branch_sha == main_sha:
        raise ProbeError("BRANCH_NOT_CHANGED")
    commit = api.call("GET",f"/git/commits/{branch_sha}")
    parents = commit.get("parents")
    if (commit.get("sha") != branch_sha or type(parents) is not list or
            len(parents) != 1 or type(parents[0]) is not dict or parents[0].get("sha") != main_sha):
        raise ProbeError("BRANCH_PARENT_UNVERIFIED")
    diff = api.call("GET",f"/compare/{main_sha}...{branch_sha}")
    changed = diff.get("files")
    if (diff.get("status") != "ahead" or
            type(diff.get("ahead_by")) is not int or diff["ahead_by"] != 1 or
            type(diff.get("behind_by")) is not int or diff["behind_by"] != 0 or
            type(diff.get("total_commits")) is not int or diff["total_commits"] != 1 or
            type(changed) is not list or len(changed) != 1 or
            type(changed[0]) is not dict or
            changed[0].get("filename") != filename or changed[0].get("status") != "added"):
        raise ProbeError("BRANCH_DIFF_UNVERIFIED")
    file = api.call("GET",f"/contents/{filename}?ref={branch_sha}")
    if (file.get("type") != "file" or file.get("encoding") != "base64" or
            type(file.get("size")) is not int or file["size"] != len(expected_raw)):
        raise ProbeError("PROBE_FILE_UNVERIFIED")
    try:
        raw = base64.b64decode("".join(file["content"].split()),validate=True)
    except (TypeError,KeyError,ValueError,binascii.Error,AttributeError):
        raise ProbeError("PROBE_FILE_UNVERIFIED") from None
    git_blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if raw != expected_raw or file.get("sha") != git_blob:
        raise ProbeError("PROBE_FILE_UNVERIFIED")
    pr = api.call("GET",f"/pulls/{number}")
    h,b = pr.get("head"),pr.get("base")
    if (type(pr.get("number")) is not int or pr["number"] != number or
            pr.get("state") != "open" or pr.get("draft") is not True or
            type(h) is not dict or type(b) is not dict or
            h.get("ref") != branch or h.get("sha") != branch_sha or
            type(h.get("repo")) is not dict or h["repo"].get("full_name") != REPO or
            b.get("ref") != "main" or b.get("sha") != main_sha or
            type(b.get("repo")) is not dict or b["repo"].get("full_name") != REPO):
        raise ProbeError("DRAFT_PR_READBACK_UNVERIFIED")
    if sha_ref(api,"main") != main_sha or sha_ref(api,branch) != branch_sha:
        raise ProbeError("REF_MOVED_DURING_READBACK")
    return number



class _PerWriteLeaseFence:
    """Recheck the one live CONTROLLER lease immediately before each source write.

    This narrows the non-atomic GET/POST race; it cannot make three GitHub REST
    mutations transactional. A write is consumed BEFORE sending its request, so
    an ambiguous response does not trigger a duplicate mutation.
    """
    def __init__(self, api, scope, epoch, claim_ref):
        self._api = api
        self._scope = scope
        self._epoch = epoch
        self._claim_ref = claim_ref
        run_id, attempt = scope["run_id"], scope["attempt"]
        filename = f"ops/probes/gha-write-{run_id}-a{attempt}.json"
        self._mutations = (("POST", "/git/refs"),
                           ("PUT", "/contents/" + filename),
                           ("POST", "/pulls"))
        self._index = 0

    def _check_live(self):
        if sha_ref(self._api, CONTROL_REF) != self._claim_ref:
            raise ProbeError("SOURCE_LEASE_REF_MOVED")
        state = state_at(self._api, self._claim_ref)
        if sha_ref(self._api, CONTROL_REF) != self._claim_ref:
            raise ProbeError("SOURCE_LEASE_CHANGED_DURING_READ")
        scope = self._scope
        if not owns(state, "CONTROLLER", scope["owner"], self._epoch, now()):
            raise ProbeError("SOURCE_LEASE_NOT_OWNED")
        holder = state.get("holder")
        if (not isinstance(holder, dict) or
                holder.get("kind") != "CONTROLLER" or
                holder.get("owner_id") != scope["owner"] or
                holder.get("epoch") != self._epoch or
                holder.get("task_id") is not None or
                holder.get("work_branch") != scope["branch"] or
                holder.get("base_main_sha") != scope["main"]):
            raise ProbeError("SOURCE_LEASE_SCOPE_CHANGED")
        if sha_ref(self._api, "main") != scope["main"]:
            raise ProbeError("SOURCE_MAIN_CHANGED")
        if sha_ref(self._api, CONTROL_REF) != self._claim_ref:
            raise ProbeError("SOURCE_LEASE_MOVED_BEFORE_WRITE")

    def call(self, method, path, body=None):
        if method == "GET":
            return self._api.call(method, path, body)
        if (self._index >= len(self._mutations) or
                (method, path) != self._mutations[self._index]):
            raise ProbeError("SOURCE_WRITE_NOT_IN_ALLOWED_ORDER")
        # A policy or network error must never become a retry of this mutation.
        self._check_live()
        self._index += 1
        return self._api.call(method, path, body)



def create_branch_probe(api, scope):
    """Only one immutable non-sensitive file on an isolated branch, NEVER main."""
    if sha_ref(api, "main") != scope["main"]:
        raise ProbeError("MAIN_CHANGED")
    api.call("POST", "/git/refs", {"ref":"refs/heads/"+scope["branch"],"sha":scope["main"]})
    filename = f"ops/probes/gha-write-{scope['run_id']}-a{scope['attempt']}.json"
    body = {"schema":1,"kind":"OWNER_MANUAL_GHA_CAPABILITY_PROBE_ONLY",
            "source_main_sha":scope["main"],"github_run_id":scope["run_id"],
            "run_attempt":scope["attempt"],"status":"NO_AI_NO_GAME_CHANGE"}
    api.call("PUT", f"/contents/{filename}", {"message":"probe: isolated owner-manual write only",
        "branch":scope["branch"],"content":base64.b64encode((json.dumps(body,sort_keys=True)+"\n").encode()).decode()})
    pr = api.call("POST", "/pulls", {"title":"[PROBE ONLY] Owner-manual GitHub Actions branch/PR permission",
        "head":scope["branch"],"base":"main","draft":True,
        "body":"Non-production, no game files, no AI inference, no merge authorization. Confirm separate reviewer and delete only by authorized owner after audit."})
    if type(pr.get("number")) is not int or pr["number"] < 1:
        raise ProbeError("PR_RESPONSE_UNVERIFIED")
    return pr["number"]


def run(api, env):
    """The only write pathway; fail closed before authority and release own lease."""
    if env.get("PROBE_CONSENT") != CONSENT:
        raise ProbeError("CONSENT_MISSING")
    live_run = api.call("GET", f"/actions/runs/{env.get('GITHUB_RUN_ID', 'invalid')}")
    main = sha_ref(api, "main")
    scope = checked_context(env, live_run, main)
    prevref = sha_ref(api, CONTROL_REF)
    state = state_at(api, prevref)
    plan = acquire(state,"CONTROLLER",scope["owner"],now(),base_main_sha=main,work_branch=scope["branch"])
    if plan.get("action") != "ACQUIRE" or not plan.get("write"):
        return {"status":"WAIT_COORDINATOR","pr":None,"wrote":False}
    epoch = plan["state"]["epoch"]
    claim = None
    pr = None
    failure = None
    # Start cleanup BEFORE attempting the remote claim. An unacknowledged PATCH
    # may have written our lease even when cas_state fails during readback.
    try:
        claim = cas_state(api,prevref,plan["state"])
        # Revalidate and ensure the exclusive owner remains ourselves before source write.
        before=sha_ref(api,CONTROL_REF)
        live=state_at(api,before)
        if before!=claim or not owns(live,"CONTROLLER",scope["owner"],epoch,now()):
            raise ProbeError("LEASE_LOST")
        source_api = api
        try:
            api = _PerWriteLeaseFence(source_api, scope, epoch, claim)
            pr=create_branch_probe(api,scope)
        finally:
            # The verifier and release use the original trusted transport.
            api = source_api
        verify_created_probe(api,scope,pr)
    except ProbeError as exc:
        failure=str(exc)
    finally:
        try:
            current=sha_ref(api,CONTROL_REF)
            st=state_at(api,current)
            if owns(st,"CONTROLLER",scope["owner"],epoch,now()):
                # The owner, epoch and current expiry must match exactly.
                # No expiry-only or foreign-run lease recovery is permitted.
                nxt=release(st,"CONTROLLER",scope["owner"],epoch,now())
                cas_state(api,current,nxt)
            elif claim is not None:
                # A confirmed claim without our current ownership is unsafe.
                raise ProbeError("RELEASE_NOT_OWNED")
            # If claim failed and we do NOT own the current ref, do not write.
            # Report the original claim failure, never claim a successful run.
        except ProbeError:
            raise ProbeError("RELEASE_UNCONFIRMED") from None
    if failure:
        raise ProbeError(failure)
    return {"status":"DRAFT_PR_CREATED_NOT_MERGED", "pr":pr, "wrote":True}


def main():
    try:
        outcome=run(GitHubAPI(os.getenv("GITHUB_TOKEN", "")),dict(os.environ))
        print(json.dumps(outcome,sort_keys=True))
    except ProbeError as exc:
        # No traceback, raw service response, or credential in job logs.
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc),"merge":False,"publish":False}))
        raise SystemExit(1)
    except Exception:
        print(json.dumps({"status":"FAIL_CLOSED","reason":"UNEXPECTED_ERROR","merge":False,"publish":False}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()