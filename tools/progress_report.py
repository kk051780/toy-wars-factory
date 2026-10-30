#!/usr/bin/env python3
"""Deterministic evidence snapshot validation; no live GitHub approval is inferred."""
import argparse
import json
from pathlib import Path

REPO = "https://github.com/kk051780/toy-wars-factory/pull/"
VALID = {"verified", "pending", "blocked"}

# Snapshot of independently checked *merged* PR evidence, as of 2026-10-29 (protected Issue113 candidate).
# Each new verification must separately update this pinned registry after checking
# current GitHub merged state and exact-head QA; a draft PR URL alone never qualifies.
APPROVED_MERGED_PR = {
    "A01": 1,
    "A02": 32,
    "A03": 34,
    "A04": 38,
    "A05": 37,
    "A06": 41,
    "A07": 43,
    "A08": 45,
    "A09": 75,
    "A10": 84,
    "A11": 108,
    "G01": 1,
    "G02": 32,
    "G03": 40,
    "G04": 35,
    "G05": 32,
    "G06": 30,
    "G07": 45,
}


# Immutable accepted 2026-10-25 evidence: no change to original 57% record is permitted.
HISTORIC_FIRST_RECONCILIATION = json.loads("{\"date\":\"2026-10-25\",\"main_verified\":\"f728fa525d8b409ef2a08a3da59e4ae7e73e27b1\",\"reason\":\"One separate reviewer merged PR45 with exact-head CI and both post-merge QA jobs successful; generated-status-only descendant verified\",\"first_run\":\"ed0fc89e-e310-8326-989c-25380dc1467e\",\"pr\":45,\"post_merge_qa\":\"https://github.com/kk051780/toy-wars-factory/actions/runs/40157791404\",\"previous_scores\":{\"automation\":49,\"game\":34},\"new_scores\":{\"automation\":57,\"game\":38},\"still_pending\":[\"A09\",\"A10\",\"A11\",\"A12\",\"A13\",\"A14\",\"A15\",\"G08\",\"G09\",\"G10\",\"G11\",\"G12\",\"G13\",\"G14\",\"G15\",\"G16\",\"G17\",\"G18\"]}")
# Independently checked 2026-10-29 candidate evidence: exact historical/current anchors.
PINNED_76_RECONCILIATION = json.loads("{\"date\":\"2026-10-29\",\"scope\":\"PROTECTED_CONTROLLER_DRAFT_INDEPENDENT_AUDIT_PENDING\",\"manual_work_id\":\"a2beea1b-8ed0-42da-ba08-4ddbc8688ad0\",\"claim_epoch\":240,\"base_main\":\"221bc53ce118f5242777c13649f437d18078dcc4\",\"old\":{\"automation\":57,\"game\":38},\"proposed\":{\"automation\":76,\"game\":38},\"evidence\":[{\"id\":\"A09\",\"pr\":75,\"head_ci\":40402147994,\"main_fail\":40340954729,\"main_success\":40404466932,\"handoff\":40404467227,\"caveat\":\"CONTROLLER-assisted repair, not universal unattended repair\"},{\"id\":\"A10\",\"pr\":84,\"head_ci\":40499824467,\"main_success\":40501279576,\"handoff\":40501279630,\"caveat\":\"one registered META cycle only\"},{\"id\":\"A11\",\"pr\":108,\"failed_ci\":[40760602268,40760892777],\"head_ci\":40761307293,\"main_success\":40763962202,\"handoff\":40763962162,\"caveat\":\"bounded WORKER PR repair\"}],\"not_counted\":[\"A12\",\"A13\",\"A14\",\"A15\"],\"holds_preserved\":true}")
PINNED_SOURCE_MAIN_SHA = "221bc53ce118f5242777c13649f437d18078dcc4"

def summarize(data):
    if data.get("schema") != 1: raise ValueError("wrong schema")
    records = data.get("reconciliations")
    if type(records) is not list or not records or records[0] != HISTORIC_FIRST_RECONCILIATION:
        raise ValueError("historic 57% reconciliation was changed, removed or reordered")
    if len(records) != 2 or records[1] != PINNED_76_RECONCILIATION:
        raise ValueError("current 76% reconciliation was changed, removed or appended")
    if data.get("source_main_sha") != PINNED_SOURCE_MAIN_SHA or records[1].get("base_main") != PINNED_SOURCE_MAIN_SHA:
        raise ValueError("progress evidence source main SHA is not independently pinned")
    result = {}
    for track in data["tracks"]:
        ms = track["milestones"]
        if len({m["id"] for m in ms}) != len(ms): raise ValueError("duplicate milestone")
        if sum(m["weight"] for m in ms) != 100: raise ValueError("weights must sum 100")
        for m in ms:
            if type(m["weight"]) is not int or m["weight"] <= 0 or m["state"] not in VALID:
                raise ValueError("bad milestone data")
            if m["state"] == "verified":
                # Fail closed on a draft/unreviewed PR, even if it has a valid URL shape.
                approved = APPROVED_MERGED_PR.get(m["id"])
                if approved is None or m.get("evidence") != REPO + str(approved):
                    raise ValueError("unreviewed or mismatched merged-PR completion evidence")
            if m["state"] != "verified" and (m.get("evidence") or not m.get("next")):
                raise ValueError("incomplete milestone cannot claim verification")
        result[track["id"]] = {"pct": sum(m["weight"] for m in ms if m["state"] == "verified"),
                               "done": sum(m["state"] == "verified" for m in ms),
                               "total": len(ms)}
    if set(result) != {"automation", "game"}: raise ValueError("missing tracks")
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(Path("config/progress_milestones.json").read_text(encoding="utf-8"))
    result = summarize(data)
    if args.check:
        doc = Path("docs/PROGRESS_DASHBOARD.md").read_text(encoding="utf-8")
        for track in data["tracks"]:
            row = result[track["id"]]
            if f"**{row['pct']}%**" not in doc or f"{row['done']}/{row['total']}" not in doc:
                raise SystemExit("dashboard is out of sync")
    for track in data["tracks"]:
        x = result[track["id"]]
        print(f"{track['name_ja']}: {x['pct']}% ({x['done']}/{x['total']} milestones)")
if __name__ == "__main__": main()
