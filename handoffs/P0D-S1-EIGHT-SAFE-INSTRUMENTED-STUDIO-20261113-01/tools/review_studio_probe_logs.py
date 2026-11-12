#!/usr/bin/env python3
"""Convert three OWNER-captured real Studio Output logs to observation-only JSON.

No script can certify real physical Studio, two independent clients, network
timing or smartphone UX from uploaded text. All manual QA statuses remain
NOT_TESTED; owner/sole integrator must review the actual evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

PREFIX = "P0D_STUDIO_PROBE_V1"
STATUS = "OBSERVED_ONLY_NOT_STUDIO_PASS"
PHASES = ("LOBBY", "COUNTDOWN", "ACTIVE", "RESULTS")
REQUIRED_MANUAL_CASES = (
    "OFF-01","OFF-02","OFF-03","ST-01","ST-02",
    "LB-01","LB-02","LB-03","LB-04",
    "GM-01","GM-02","GM-03","GM-04","GM-05","GM-06","GM-07",
    "GM-08","GM-09","GM-10","GM-11","GM-12","GM-13",
    "NW-01","NW-02","NW-03","NW-04",
    "UX-01","UX-02","UX-03","UX-04","UX-05",
    "OPS-01","OPS-02","OPS-03",
)
RECORD_PATTERN = re.compile(
    r"P0D_STUDIO_PROBE_V1\s+(CLIENT|SERVER)\s+(.*)"
)
TOKEN_PATTERN = re.compile(r"(?<!\w)([a-z][a-z0-9_]*)=([^\s]+)")
MAX_CAPTURED_LINES = 20000
MAX_OWN_RAW_LOG_BYTES = 15 * 1024 * 1024


def collect(raw: bytes, expected: str) -> dict:
    if len(raw) > MAX_OWN_RAW_LOG_BYTES:
        raise ValueError("PROBE_LOG_OVER_SIZE_15MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as ex:
        raise ValueError("PROBE_LOG_NOT_UTF8") from ex
    events, invalid = [], 0
    for line in text.splitlines():
        found = RECORD_PATTERN.search(line)
        if not found:
            continue
        kind, data = found.group(1), found.group(2)
        if kind != expected:
            invalid += 1
            continue
        raw_tokens = dict(TOKEN_PATTERN.findall(data))
        event = {
            "category": kind,
            "kind": raw_tokens.get("kind", "UNSPECIFIED"),
            "phase": raw_tokens.get("phase", ""),
            "team": raw_tokens.get("team", ""),
            "reason": raw_tokens.get("reason", ""),
            "serial": raw_tokens.get("serial", ""),
            "red": raw_tokens.get("red", ""),
            "blue": raw_tokens.get("blue", ""),
        }
        # Preserve only whitelisted, short fields. Never include possible names,
        # userIds, paths, chat text, IPs or unfiltered raw Output.
        for key in event:
            if len(event[key]) > 50:
                event[key] = event[key][:50]
        events.append(event)
        if len(events) > MAX_CAPTURED_LINES:
            raise ValueError("PROBE_TOO_MANY_LOG_LINES")
    if invalid:
        raise ValueError("PROBE_OUTPUT_MIXED_SERVER_CLIENT_STREAMS")
    if not events:
        raise ValueError("NO_PINNED_PROBE_LINES_PRESENT")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "records": len(events),
        "events": events,
    }


def summarize(server: dict, red: dict, blue: dict):
    logs = {"server": server, "RED": red, "BLUE": blue}
    if len({logs[k]["sha256"] for k in logs}) != 3:
        raise ValueError("SERVER_AND_TWO_CLIENT_LOGS_MUST_BE_DISTINCT")
    for name in ("RED","BLUE"):
        events=logs[name]["events"]
        if not any(e["kind"] == "START" for e in events):
            raise ValueError("CLIENT_MISSING_STUDIO_ONLY_PROBE_START_" + name)
        if not any(e["team"] == name and e["kind"] == "PHASE" for e in events):
            raise ValueError("CLIENT_HAS_NO_SEPARATE_TEAM_PHASE_" + name)
    if not any(e["kind"] == "MAP_CHECK" for e in server["events"]):
        raise ValueError("SERVER_MISSING_MAP_CHECK")
    warnings=[]
    for name,block in logs.items():
        for e in block["events"]:
            if ("WARN" in e["kind"] or "UNEXPECTED" in e["kind"]
                or e["kind"] in ("UI_INCOMPLETE","UI_NOT_READY")):
                warnings.append({
                    "source":name,"kind":e["kind"],"reason":e["reason"]
                })
    counts={}
    for name,block in logs.items():
        counter=Counter(e["kind"] for e in block["events"])
        counts[name]=dict(sorted(counter.items()))
    phases={}
    for name in ("RED","BLUE"):
        phases[name]={
            p:any(e["phase"]==p and e["kind"]=="PHASE"
                  for e in logs[name]["events"]) for p in PHASES
        }
    return {
        "format":"P0D_S1_EIGHT_SAFE_STUDIO_READONLY_OBSERVATIONS_V1",
        "game_id":"TRAP_RAIDERS",
        "release_id":"P0D-S1-KIDS-RC01",
        "status":STATUS,
        "source_logs_provenance":"USER_SUPPLIED_UNVERIFIED_TEXT",
        "separate_log_files_supplied":3,
        "log_sha256":{n:v["sha256"] for n,v in logs.items()},
        "record_counts":{n:v["records"] for n,v in logs.items()},
        "event_counts":counts,
        "client_phases_observed":phases,
        "passive_warnings":warnings,
        "manual_case_statuses":[{"case_id":case,"status":"NOT_TESTED"}
                                for case in REQUIRED_MANUAL_CASES],
        "manual_case_pass_count":0,
        "physical_two_client_certified":False,
        "real_mobile_certified":False,
        "human_ux_certified":False,
        "owner_release_approval":False,
        "publish_approved":False,
        "note":"These are observation counts only, not tamper-proof Studio or phone evidence. Owner must independently inspect real Studio screenshots/video and submit signed manual case receipts to sole #220 integrator.",
    }


def process(server_file: Path, red_file: Path, blue_file: Path):
    paths=(server_file,red_file,blue_file)
    if len({p.resolve() for p in paths})!=3:
        raise ValueError("SERVER_AND_CLIENT_LOGS_MUST_BE_SEPARATE_FILES")
    return summarize(
        collect(server_file.read_bytes(),"SERVER"),
        collect(red_file.read_bytes(),"CLIENT"),
        collect(blue_file.read_bytes(),"CLIENT"),
    )


def write_once(path: Path, data: dict):
    if path.exists():
        raise ValueError("EVIDENCE_REPORT_EXISTING_FILE_REFUSE_OVERWRITE")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf8") as f:
        json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--server-log",type=Path,required=True)
    ap.add_argument("--red-client-log",type=Path,required=True)
    ap.add_argument("--blue-client-log",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    data=process(a.server_log,a.red_client_log,a.blue_client_log)
    write_once(a.output,data)
    print("P0D_STUDIO_PROBE_THREE_SEPARATE_LOGS_PARSED")
    print("P0D_STUDIO_PROBE_MANUAL_34_CASES_NOT_TESTED")
    print("P0D_STUDIO_PROBE_OBSERVED_ONLY_NOT_RELEASE_READY")
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,ValueError,UnicodeError) as ex:
        print("P0D_STUDIO_PROBE_LOG_PROCESSING_BLOCKED "+str(ex),file=sys.stderr)
        sys.exit(2)
