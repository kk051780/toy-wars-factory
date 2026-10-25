#!/usr/bin/env python3
"""Deterministic evidence snapshot validation; no live GitHub approval is inferred."""
import argparse
import json
from pathlib import Path

REPO = "https://github.com/kk051780/toy-wars-factory/pull/"
VALID = {"verified", "pending", "blocked"}

def summarize(data):
    if data.get("schema") != 1: raise ValueError("wrong schema")
    result = {}
    for track in data["tracks"]:
        ms = track["milestones"]
        if len({m["id"] for m in ms}) != len(ms): raise ValueError("duplicate milestone")
        if sum(m["weight"] for m in ms) != 100: raise ValueError("weights must sum 100")
        for m in ms:
            if type(m["weight"]) is not int or m["weight"] <= 0 or m["state"] not in VALID:
                raise ValueError("bad milestone data")
            if m["state"] == "verified" and not m.get("evidence", "").startswith(REPO):
                raise ValueError("completion needs GitHub PR evidence")
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
