#!/usr/bin/env python3
"""Compose source-exact native Luau VM test for RaidAlerts intent/cursor.
No mutable game source; the whole original ModuleScript executes in Luau VM.
The Roblox render function is defined but not invoked outside Studio.
"""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]
def build():
    module=(ROOT/"EGGRUMBLE_RaidAlerts.luau").read_text(encoding="utf-8")
    spec=(ROOT/"tests/EGGRUMBLE_RaidAlerts.spec.luau").read_text(encoding="utf-8")
    return (
        "local Alerts=(function()\n"+module+"\nend)()\n"
        +"local run=(function()\n"+spec+"\nend)()\n"
        +"assert(run(Alerts))\nprint('RAID_ALERTS_NATIVE_LUAU_PASS')\n"
    )
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    Path(args.out).write_text(build(),encoding="utf-8")
