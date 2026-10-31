"""Read-only GitHub Actions cron-vs-observed-run advisory.

Trusted callers must independently collect ORIGINAL GitHub run pages and retrieve
workflows from a trusted Git ref. This module does NOT authenticate caller JSON;
it never starts, writes, merges, publishes, spends, retries or changes schedule.

The ratio here is observed run count / theoretical cron slots, NOT a proven
GitHub 'drop rate': delays, gaps in workflow enablement, API omissions or source
history can explain the difference. Do not use it as unattended task identity.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
PATH = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
DENIED = {name: False for name in (
    "provider_authenticated", "schedule_delivery_guaranteed", "may_write",
    "may_dispatch", "may_retry", "may_takeover", "may_merge", "may_publish",
    "may_start_ai", "may_spend", "may_notify")}

class CadenceError(ValueError):
    """Fixed codes only; no original provider input or exception content."""

def need(test, code):
    if not test:
        raise CadenceError(code)

def instant(text):
    need(type(text) is str and len(text) <= 45, "INVALID_TIME")
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise CadenceError("INVALID_TIME") from None
    need(value.tzinfo is not None, "INVALID_TIME")
    return value.astimezone(timezone.utc)

def minute_tuple(value):
    need(type(value) is list and 1 <= len(value) <= 12 and
         all(type(n) is int and 0 <= n <= 59 for n in value), "INVALID_CRON")
    need(value == sorted(set(value)), "INVALID_CRON")
    return tuple(value)

def expected_slots(start, end, minutes):
    # UTC minute boundaries; bounded input to at most 31 days.
    cursor = start.replace(second=0, microsecond=0)
    if cursor < start:
        cursor += timedelta(minutes=1)
    total = 0
    while cursor < end:
        if cursor.minute in minutes:
            total += 1
        cursor += timedelta(minutes=1)
    return total

def analyze(frame, binding):
    """Return non-authorizing diagnostics from strict *untrusted* normalized GET data.

    Frame: {schema,repository,observed_at,window_start,window_end,total_count,runs}
    Binding: {repository,workflows:[{path,minute_offsets,branch}...]}
    Runs: {id,event,path,head_branch,head_sha,run_attempt,created_at,
           status,conclusion}. A host must separately attest the original GitHub
    GET and historical schedule source; matching data is not authentication.
    """
    need(type(frame) is dict and set(frame) == {
        "schema","repository","observed_at","window_start","window_end","total_count","runs"},
         "INVALID_FRAME")
    need(type(binding) is dict and set(binding) == {"repository", "workflows"}, "INVALID_BINDING")
    repo = frame["repository"]
    need(type(repo) is str and REPO.fullmatch(repo) and repo == binding["repository"],
         "WRONG_REPOSITORY")
    need(type(frame["schema"]) is int and frame["schema"] == 1, "INVALID_SCHEMA")
    seen_paths = set()
    workflows = binding["workflows"]
    need(type(workflows) is list and 1 <= len(workflows) <= 8, "INVALID_WORKFLOWS")
    policy = {}
    for item in workflows:
        need(type(item) is dict and set(item) == {"path", "minute_offsets", "branch"},
             "INVALID_WORKFLOW")
        path, branch = item["path"], item["branch"]
        need(type(path) is str and PATH.fullmatch(path) and path not in seen_paths and
             type(branch) is str and branch == "main", "INVALID_WORKFLOW")
        seen_paths.add(path)
        policy[path] = minute_tuple(item["minute_offsets"])
    start, end, observed = map(instant,
            (frame["window_start"],frame["window_end"],frame["observed_at"]))
    need(start < end <= observed and timedelta(hours=1) <= end-start <= timedelta(days=31),
         "INVALID_WINDOW")
    runs = frame["runs"]
    total = frame["total_count"]
    need(type(runs) is list and len(runs) <= 3000 and type(total) is int and
         0 <= total <= 3000, "INVALID_PAGE_SIZE")
    # Caller must provide every page and top-level returned total_count; even
    # when they match, this is a *claim*, never source authentication.
    need(len(runs) == total, "INCOMPLETE_RESULT_PAGES")
    selected = {path: [] for path in seen_paths}
    seen_ids = set()
    for row in runs:
        need(type(row) is dict and set(row) == {
            "id","event","path","head_branch","head_sha","run_attempt",
            "created_at","status","conclusion"}, "INVALID_RUN")
        rid = row["id"]
        need(type(rid) is int and 0 < rid < 2**63 and rid not in seen_ids,
             "INVALID_RUN_ID")
        seen_ids.add(rid)
        need(row["event"] == "schedule" and type(row["path"]) is str and
             row["path"] in policy and row["head_branch"] == "main" and
             type(row["head_sha"]) is str and SHA.fullmatch(row["head_sha"]),
             "FOREIGN_OR_INVALID_RUN")
        need(type(row["run_attempt"]) is int and 1 <= row["run_attempt"] <= 100,
             "INVALID_ATTEMPT")
        need(row["status"] in ("queued", "in_progress", "completed", "waiting", "pending") and
             row["conclusion"] in (None, "success", "failure", "cancelled", "skipped", "neutral",
                                  "timed_out", "action_required"), "INVALID_RUN_STATUS")
        need((row["status"] == "completed") == (row["conclusion"] is not None),
             "INCONSISTENT_TERMINAL_STATE")
        created = instant(row["created_at"])
        need(created <= observed, "FUTURE_RUN")
        if start <= created < end:
            selected[row["path"]].append((created, row["conclusion"]))
    output = {}
    for path, minutes in sorted(policy.items()):
        events = sorted(selected[path], key=lambda x: x[0])
        n_slots = expected_slots(start, end, minutes)
        gaps = [(events[i][0] - events[i-1][0]).total_seconds()/60
                for i in range(1, len(events))]
        statuses = {"completed_success": sum(c == "success" for _,c in events),
                    "completed_non_success": sum(c is not None and c != "success" for _,c in events),
                    "nonterminal": sum(c is None for _,c in events)}
        output[path] = {
            "configured_cron_slots": n_slots,
            "observed_schedule_runs": len(events),
            "observed_over_nominal_slots": (round(len(events)/n_slots, 4) if n_slots else None),
            "longest_observed_interrun_gap_minutes": (round(max(gaps), 2) if gaps else None),
            "shortest_observed_interrun_gap_minutes": (round(min(gaps), 2) if gaps else None),
            "outcomes": statuses,
            "status": ("INSUFFICIENT_WINDOW" if n_slots < 6 else
                       "FEWER_RUNS_THAN_NOMINAL_SLOTS" if len(events) < n_slots else
                       "OBSERVED_RUN_COUNT_AT_OR_ABOVE_NOMINAL"),
        }
    return {
        "schema":1, "repository":repo, "window_start":start.isoformat(),
        "window_end":end.isoformat(),"reported_total_count":total,
        "source_verification":"UNTRUSTED_INPUT_ONLY", "drop_cause":"UNKNOWN",
        "drop_rate":None, "workflows":output,"authority":dict(DENIED),
    }

def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, "DUPLICATE_JSON_KEY")
        out[key] = value
    return out

def _no_nonfinite(value):
    raise CadenceError("NONFINITE_JSON")

def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        raise SystemExit("USAGE: python system_actions_schedule_cadence.py FRAME.json BINDING.json")
    try:
        frame_raw = Path(args[0]).read_bytes()
        bind_raw = Path(args[1]).read_bytes()
        need(len(frame_raw) <= 2_000_000 and len(bind_raw) <= 100_000,
             "INPUT_TOO_LARGE")
        frame=json.loads(frame_raw,object_pairs_hook=_no_duplicates,parse_constant=_no_nonfinite)
        binding=json.loads(bind_raw,object_pairs_hook=_no_duplicates,parse_constant=_no_nonfinite)
        print(json.dumps(analyze(frame,binding),sort_keys=True))
    except CadenceError as exc:
        print(json.dumps({"status":"FAIL_CLOSED","code":str(exc),"authority":DENIED}))
        raise SystemExit(2)
    except Exception:
        print(json.dumps({"status":"FAIL_CLOSED","code":"INVALID_INPUT","authority":DENIED}))
        raise SystemExit(2)
if __name__ == "__main__":
    main()