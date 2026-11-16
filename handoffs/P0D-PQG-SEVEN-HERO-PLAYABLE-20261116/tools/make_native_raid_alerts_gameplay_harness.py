#!/usr/bin/env python3
"""Build original CastleMatchRules + RaidAlerts from source, then native gameplay
scenario. No fake event fixtures. No Studio claim. No game source changes.
"""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
def build():
    rules=(ROOT/"EGGRUMBLE_CastleMatchRules.luau").read_text(encoding="utf-8")
    alerts=(ROOT/"EGGRUMBLE_RaidAlerts.luau").read_text(encoding="utf-8")
    tests=(ROOT/"tests/EGGRUMBLE_RaidAlertsGameplay.spec.luau").read_text(encoding="utf-8")
    assert rules.rstrip().endswith("return M"),"Rules source unexpected"
    assert alerts.rstrip().endswith("return Alerts"),"Alert source unexpected"
    return ("local Rules=(function()\n"+rules+"\nend)()\n"+
            "local Alerts=(function()\n"+alerts+"\nend)()\n"+
            "local run=(function()\n"+tests+"\nend)()\n"+
            "assert(run(Rules,Alerts))\n"+
            "print('AUTHORITATIVE_RAID_ALERTS_GAMEPLAY_PASS')\n")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    Path(args.out).write_text(build(),encoding="utf-8")
