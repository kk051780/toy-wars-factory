#!/usr/bin/env python3
"""Manual-only, read-only GitHub-hosted execution adapter for PR164 cadence audit.

This script is dormant until a separately reviewed owner-manual workflow is
merged on default main. It authenticates live REST responses *during that run*
but cannot prove a future provider execution by inspecting standalone files.
No write/dispatch/merge/retry, model calls, money, or Roblox use.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from urllib import request, error

from tools import system_actions_schedule_collector as collector
from tools import system_actions_schedule_cadence as cadence

REPO = "kk051780/toy-wars-factory"
REPO_ID = 1431683395
ACTOR = "kk051780"
WORKFLOW = ".github/workflows/twf-readonly-cadence-audit.yml"
CONSENT = "I_AUTHORIZE_READ_ONLY_SCHEDULE_AUDIT"
API_ROOT = f"https://api.github.com/repos/{REPO}"
BINDING = {"repository": REPO, "workflows": [
    {"path": ".github/workflows/handoff-sync.yml", "minute_offsets": [13, 33, 53], "branch": "main"},
    {"path": ".github/workflows/loop-watchdog.yml", "minute_offsets": [7, 27, 47], "branch": "main"},
]}
SHA = re.compile(r"[0-9a-f]{40}\Z")
SCHEDULE_URL = re.compile(re.escape(API_ROOT) + r"/actions/runs\?event=schedule&per_page=100&page=(?:[1-9]|10)\Z")
RUN_URL = re.compile(re.escape(API_ROOT) + r"/actions/runs/[1-9][0-9]{0,17}\Z")

class HostError(ValueError):
    """Fixed diagnostics, never provider bodies or secrets."""


def deny(test, code):
    if not test:
        raise HostError(code)


def validated_context(env):
    required = ("GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_ACTOR",
                "GITHUB_TRIGGERING_ACTOR", "GITHUB_EVENT_NAME", "GITHUB_REF",
                "GITHUB_WORKFLOW_REF", "GITHUB_SHA", "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT", "PROBE_CONSENT")
    deny(type(env) is dict and all(type(env.get(key)) is str for key in required),
         "INVALID_HOST_CONTEXT")
    deny(env["GITHUB_REPOSITORY"] == REPO and
         env["GITHUB_REPOSITORY_ID"] == str(REPO_ID) and
         env["GITHUB_ACTOR"] == ACTOR and env["GITHUB_TRIGGERING_ACTOR"] == ACTOR and
         env["GITHUB_EVENT_NAME"] == "workflow_dispatch" and
         env["GITHUB_REF"] == "refs/heads/main" and
         env["GITHUB_WORKFLOW_REF"] == f"{REPO}/{WORKFLOW}@refs/heads/main" and
         env["PROBE_CONSENT"] == CONSENT and
         bool(SHA.fullmatch(env["GITHUB_SHA"])) and
         bool(re.fullmatch(r"[1-9][0-9]{0,17}",env["GITHUB_RUN_ID"])) and
         env["GITHUB_RUN_ATTEMPT"] == "1", "UNAUTHORIZED_HOST_CONTEXT")
    return {"main_sha": env["GITHUB_SHA"], "run_id": int(env["GITHUB_RUN_ID"])}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubReader:
    """Token only accompanies 100% fixed-host GET URLs; no redirect following."""
    def __init__(self, token, opener=None):
        deny(type(token) is str and bool(token) and len(token) <= 4096,
             "TOKEN_UNAVAILABLE")
        self._token = token
        self._open = opener if opener is not None else request.build_opener(NoRedirect).open

    def __call__(self, url):
        deny(type(url) is str and (url in (
            f"{API_ROOT}/git/ref/heads/main",) or
            RUN_URL.fullmatch(url) is not None or
            SCHEDULE_URL.fullmatch(url) is not None), "URL_NOT_ALLOWLISTED")
        req = request.Request(url,method="GET",headers={
            "Authorization":"Bearer "+self._token,
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"twf-readonly-cadence-audit"})
        try:
            with self._open(req,timeout=12) as response:
                code=response.getcode()
                if code != 200:
                    raise HostError("GITHUB_NON_200")
                raw=response.read(2_000_001)
                deny(len(raw)<=2_000_000,"GITHUB_RESPONSE_TOO_LARGE")
                obj=json.loads(raw)
                deny(type(obj) is dict,"INVALID_GITHUB_RESPONSE")
                return obj
        except HostError:
            raise
        except (error.HTTPError,error.URLError,TimeoutError,OSError,UnicodeError,ValueError):
            raise HostError("READ_ONLY_GITHUB_GET_FAILED") from None


def assert_manual_run(reader, scope):
    main=reader(f"{API_ROOT}/git/ref/heads/main")
    deny(main.get("object",{}).get("sha")==scope["main_sha"],"MAIN_SHA_CHANGED")
    run=reader(f"{API_ROOT}/actions/runs/{scope['run_id']}")
    deny(type(run.get("id")) is int and run["id"]==scope["run_id"] and
         run.get("event")=="workflow_dispatch" and
         run.get("path")==WORKFLOW and
         run.get("run_attempt")==1 and
         run.get("head_sha")==scope["main_sha"] and
         run.get("head_branch")=="main" and
         type(run.get("repository")) is dict and
         run["repository"].get("id")==REPO_ID and
         type(run.get("head_repository")) is dict and
         run["head_repository"].get("id")==REPO_ID and
         type(run.get("actor")) is dict and run["actor"].get("login")==ACTOR and
         type(run.get("triggering_actor")) is dict and
         run["triggering_actor"].get("login")==ACTOR,
         "MANUAL_RUN_LINEAGE_UNVERIFIED")


def validate_current_cron_sources(root):
    """Check exact source minute offsets, but do not claim historic enablement."""
    for row in BINDING["workflows"]:
        path = root / row["path"]
        deny(path.is_file() and not path.is_symlink(),"CRON_SOURCE_UNAVAILABLE")
        try:
            source=path.read_text(encoding="utf8")
        except (OSError,UnicodeError):
            raise HostError("CRON_SOURCE_UNAVAILABLE") from None
        deny(len(source.encode("utf8")) <= 30000,"CRON_SOURCE_TOO_LARGE")
        minutes=",".join(str(x) for x in row["minute_offsets"])
        expected=f"- cron: '{minutes} * * * *'"
        # Watchdog's source uses double quotes; both forms allowed but exact schedule only.
        if row["path"].endswith("loop-watchdog.yml"):
            expected=f'- cron: "{minutes} * * * *"'
        found=[line.strip() for line in source.splitlines()
               if re.fullmatch(r"\s*-\s*cron:\s*.*",line)]
        deny(found==[expected] and "  schedule:" in source,
             "CURRENT_CRON_SOURCE_DRIFT")


def execute(reader,env,*,root,clock):
    """Pure orchestration: all live GETs injected to facilitate no-network tests."""
    scope=validated_context(env)
    deny(callable(reader) and callable(clock),"INVALID_HOST_READER")
    validate_current_cron_sources(root)
    assert_manual_run(reader,scope)
    now=clock()
    deny(isinstance(now,datetime) and now.tzinfo is not None,"INVALID_CLOCK")
    now=now.astimezone(timezone.utc)
    end=now.replace(minute=0,second=0,microsecond=0)
    start=end-timedelta(hours=48)
    observed_at=now.isoformat()
    summary=collector.collect_and_analyze(reader,expected_repository=REPO,
        binding=BINDING,observed_at=observed_at,
        window_start=start.isoformat(),window_end=end.isoformat())
    # Don't turn a trust-boundary limitation into a false attestation of a schedule.
    summary.update({
        "status":"OWNER_MANUAL_READ_ONLY_PROBE_NOT_AUTOMATED_SCHEDULER",
        "run_id":scope["run_id"],
        "source_main_sha":scope["main_sha"],
        "host_gets_executed":True,
        "current_cron_source_checked":True,
        "historical_cron_source_authenticated":False,
        "automatic_ai_coding_verified":False,
        "provider_authenticated_outside_job":False,
    })
    return summary


def main():
    try:
        token=os.environ.get("GITHUB_TOKEN","")
        result=execute(GitHubReader(token),dict(os.environ),root=Path.cwd(),
                       clock=lambda:datetime.now(timezone.utc))
        safe=json.dumps(result,ensure_ascii=False,sort_keys=True)
        print(safe)
        summary=os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary,"a",encoding="utf8") as f:
                f.write("### Owner-manual read-only schedule audit\n\n")
                f.write("This job reads GitHub schedules and does NOT run AI, write a branch, or publish Roblox.\n\n")
                for path,item in sorted(result["workflows"].items()):
                    f.write(f"- {path}: observed {item['observed_schedule_runs']} / nominal {item['configured_cron_slots']} (cause UNKNOWN)\n")
    except (HostError,cadence.CadenceError) as e:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(e),"may_write":False,"may_ai":False}))
        raise SystemExit(2)
    except Exception:
        print(json.dumps({"status":"FAIL_CLOSED","reason":"UNEXPECTED_ERROR","may_write":False,"may_ai":False}))
        raise SystemExit(2)

if __name__=="__main__":
    main()