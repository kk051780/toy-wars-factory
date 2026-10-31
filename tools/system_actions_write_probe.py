"""Manual-only, owner-controlled GitHub Actions isolated write capability probe.

NOT a ChatGPT Automations identity bridge, AI agent, or production source writer.
Only a reviewed workflow on default main can invoke this with its ephemeral token.
The acquired coordinator epoch is always released by its own owner if possible;
loss of process/network can still orphan a lease and must NOT be auto-recovered.
"""
from __future__ import annotations

import base64
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


class GitHubAPI:
    """Fixed-host REST transport, bounded source and sanitized error codes."""
    def __init__(self, token: str, transport: Callable | None = None):
        if not token:
            raise ProbeError("TOKEN_ABSENT")
        self._token = token
        self._transport = transport or request.urlopen

    def call(self, method: str, suffix: str, body=None):
        if (method not in ("GET", "POST", "PATCH", "PUT") or
                not isinstance(suffix, str) or
                not suffix.startswith("/") or ".." in suffix or
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
    if sha_ref(api, CONTROL_REF) != newsha or state_at(api, newsha) != newstate:
        raise ProbeError("CONTROL_CAS_READBACK_UNCONFIRMED")
    return newsha


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
    claim = cas_state(api,prevref,plan["state"])
    epoch = plan["state"]["epoch"]
    pr = None
    failure = None
    try:
        # Revalidate and ensure the exclusive owner remains ourselves before source write.
        before=sha_ref(api,CONTROL_REF)
        live=state_at(api,before)
        if before!=claim or not owns(live,"CONTROLLER",scope["owner"],epoch,now()):
            raise ProbeError("LEASE_LOST")
        pr=create_branch_probe(api,scope)
    except ProbeError as exc:
        failure=str(exc)
    finally:
        try:
            current=sha_ref(api,CONTROL_REF)
            st=state_at(api,current)
            if not owns(st,"CONTROLLER",scope["owner"],epoch,now()):
                raise ProbeError("RELEASE_NOT_OWNED")
            nxt=release(st,"CONTROLLER",scope["owner"],epoch,now())
            # Even on failure, only this exact owner/epoch is released.
            cas_state(api,current,nxt)
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