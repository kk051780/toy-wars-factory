"""P3 deterministic multi-game work proposals — NO task dispatch or GitHub writes.

User-supplied snapshots and signal JSON are UNTRUSTED. Even a selected
candidate is NOT proof of ownership, current CI, an acquired CAS lease or a
permission to call automations, publish, spend, approve or merge.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

from studio_autopilot.core import validate_project, InvalidProject

SHA = re.compile(r"[0-9a-f]{40}\Z")
EVENT_KEY = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
TRIGGERS = {"manual_go": 0, "repair": 1, "scheduled": 2}
STATES = {"PASS", "FAIL", "PENDING", "NOT_RUN"}


class UnsafePlan(ValueError):
    pass


def _exact(value, fields, name):
    if type(value) is not dict or set(value) != set(fields):
        raise UnsafePlan(name + " has invalid schema")
    return value


def _strict_int(x, minimum=0, maximum=1000000000):
    return type(x) is int and minimum <= x <= maximum


def _validated_games(projects):
    if type(projects) is not list or not 1 <= len(projects) <= 100:
        raise UnsafePlan("empty or excessive portfolio")
    ids, repos, refs, tasks, bound = set(), set(), set(), set(), []
    for raw in projects:
        try:
            project = validate_project(raw)
        except (InvalidProject, KeyError, TypeError) as exc:
            raise UnsafePlan("invalid project manifest") from exc
        game_id = project["game_id"]
        if game_id in ids:
            raise UnsafePlan("duplicate project ID")
        ids.add(game_id)
        if project["phase"] == "UNBOUND_TEMPLATE":
            continue
        repo, ref = project["repository"].casefold(), project["coordination_ref"].casefold()
        identities = set(project["roles"].values())
        if repo in repos or ref in refs or identities & tasks:
            raise UnsafePlan("cross-project repository/lease/task collision")
        repos.add(repo)
        refs.add(ref)
        tasks.update(identities)
        bound.append(project)
    return bound


def propose(projects, snapshots, signals, *, cycle, max_slots=1, occupied_slots=0):
    """Read-only fair shortlist. No decision here can authorize execution."""
    games = _validated_games(projects)
    if not _strict_int(cycle) or not _strict_int(max_slots, 1, 10) or not _strict_int(occupied_slots, 0, max_slots):
        raise UnsafePlan("invalid cycle or slot budget")
    if type(snapshots) is not dict or set(snapshots) != {g["game_id"] for g in games}:
        raise UnsafePlan("exactly one observation per active game required")
    if type(signals) is not list or len(signals) > 300:
        raise UnsafePlan("invalid signals")
    events = {}
    for signal in signals:
        _exact(signal, ("game_id", "trigger", "occurrence_key"), "signal")
        gid, trig, key = signal["game_id"], signal["trigger"], signal["occurrence_key"]
        if type(gid) is not str or gid not in snapshots or type(trig) is not str or trig not in TRIGGERS or \
                type(key) is not str or not EVENT_KEY.fullmatch(key):
            raise UnsafePlan("foreign, unbound or invalid trigger")
        events.setdefault(gid, set()).add(trig)
    candidates = []
    for project in games:
        gid = project["game_id"]
        row = _exact(snapshots[gid], ("repository", "main_sha", "qa_sha", "qa",
                           "lease_epoch", "holder", "open_prs", "last_served_cycle",
                           "live_read_claim"), "snapshot")
        if row["repository"] != project["repository"] or \
                not all(type(row[k]) is str and SHA.fullmatch(row[k]) for k in ("main_sha", "qa_sha")) or \
                type(row["qa"]) is not str or row["qa"] not in STATES or \
                not _strict_int(row["lease_epoch"]) or \
                not _strict_int(row["open_prs"], 0, 999999) or \
                not _strict_int(row["last_served_cycle"], -1, 1000000000) or \
                type(row["live_read_claim"]) is not bool or \
                (row["holder"] is not None and (type(row["holder"]) is not str or not row["holder"])):
            raise UnsafePlan("foreign or malformed project observation")
        if gid not in events:
            continue
        reasons = []
        if row["holder"] is not None:
            reasons.append("JOIN_EXISTING_LEASE")
        if row["main_sha"] != row["qa_sha"]:
            reasons.append("WAIT_CURRENT_MAIN_QA")
        if row["qa"] == "FAIL":
            reasons.append("REPAIR_MAIN_FIRST")
        elif row["qa"] != "PASS":
            reasons.append("WAIT_MAIN_QA")
        if row["open_prs"] >= project["safety"]["max_open_prs"]:
            reasons.append("WAIT_PR_CAPACITY")
        if not row["live_read_claim"]:
            reasons.append("VERIFY_LIVE_GITHUB_EVIDENCE")
        chosen = min(events[gid], key=lambda t: TRIGGERS[t])
        idempotency_key = sha256((":".join((gid,str(cycle),
                            str(row["lease_epoch"]),row["main_sha"]))).encode("ascii")).hexdigest()
        candidates.append({
            "game_id": gid, "repository": project["repository"],
            "author_task_id": project["roles"]["author"],
            "trigger": chosen, "coalesced": sorted(events[gid]),
            "epoch_observed": row["lease_epoch"], "sha_observed": row["main_sha"],
            "last_served_cycle": row["last_served_cycle"], "idempotency_key": idempotency_key,
            "issues": reasons,
            "candidate_only": True, "selected": False,
            "dispatch_allowed": False, "merge_allowed": False,
            "publish_allowed": False, "external_spend_allowed": False,
        })
    candidates.sort(key=lambda x: (bool(x["issues"]), x["last_served_cycle"],
                                  TRIGGERS[x["trigger"]], x["game_id"]))
    capacity = max_slots - occupied_slots
    count = 0
    for candidate in candidates:
        if not candidate["issues"] and count < capacity:
            candidate["selected"] = True
            count += 1
        elif not candidate["issues"]:
            candidate["issues"].append("WAIT_GLOBAL_FAIRNESS_CAPACITY")
    return {
        "schema": 1, "cycle": cycle,
        "mode": "READ_ONLY_UNTRUSTED_INPUT_NEVER_DISPATCH",
        "slots_total": max_slots, "slots_occupied": occupied_slots,
        "candidates": candidates,
        "execution": {"dispatch_allowed": False, "merge_allowed": False,
                      "publish_allowed": False, "external_spend_allowed": False},
    }


def main():
    """Pure local demonstration. Input file is never trusted to trigger work."""
    import argparse
    parser = argparse.ArgumentParser(description="Read-only P3 multi-game candidate planner")
    parser.add_argument("input_json")
    args = parser.parse_args()
    with open(args.input_json, encoding="utf-8") as f:
        request = json.load(f)
    _exact(request, ("projects", "snapshots", "signals", "cycle", "max_slots", "occupied_slots"), "request")
    print(json.dumps(propose(**request), sort_keys=True, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
