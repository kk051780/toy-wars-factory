#!/usr/bin/env python3
"""Inspect actual composed Game/HUD team contract without assuming Player.Team exists.
This is diagnostic QA for source-verified but engine-untested private preview.
"""
from pathlib import Path
import argparse,re
p=argparse.ArgumentParser()
p.add_argument("--dist",required=True,type=Path)
a=p.parse_args()
game=(a.dist/"src/server/Game.server.luau").read_text("utf8")
hud=(a.dist/"src/client/HUD.client.luau").read_text("utf8")
assert game.count("local function applyClassicEggRelay")==1
assert hud.count("local function nearestRelayTeammate")==1
server_patterns=[
    r"\.Team\s*=",r"\.TeamColor\s*=",r"GetTeamName",r"getTeamName",
    r"teamOf\[",r"Team\s*=",r"\.Team\b",r"SetAttribute\(\s*[\"']Team",
    r"CreateTeam",r"Teams:",
]
shown=0
for i,line in enumerate(game.splitlines(),1):
    if any(re.search(k,line) for k in server_patterns):
        if shown<80:
            print("GAME_TEAM_LINE",i,line.strip()[:170])
        shown+=1
print("GAME_TEAM_MATCH_COUNT",shown)
block=hud.split("local function nearestRelayTeammate()",1)[1].split("local function fireClassicEggRelay()",1)[0]
print("HUD_TEAM_SELECTION_1",len(re.findall(r"other\.Team",block)))
print("HUD_MATCHES_SNAPSHOT_TEAM",bool(re.search(r"other\.Team\.Name\s*==\s*s\.team",block)))
print("SERVER_PLAYER_TEAM_ASSIGNMENTS",len(re.findall(r"\b\w+\.Team\s*=",game)))
print("SERVER_TEAM_COLOR_ASSIGNMENTS",len(re.findall(r"\b\w+\.TeamColor\s*=",game)))
print("P0D_ACTUAL_60_GAME_HUD_TEAM_CONTRACT_DIAGNOSTIC_DONE")
