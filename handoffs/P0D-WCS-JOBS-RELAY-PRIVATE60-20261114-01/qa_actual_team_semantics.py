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
# Hard fail when game team source or client target selection drifts.
assert "if player.Team == teamInstances.RED then return \"RED\" end" in game
assert "if player.Team == teamInstances.BLUE then return \"BLUE\" end" in game
assert "player.Team = teamInstances[name]" in game
assert "player.Team = teamInstances[move.to]" in game
assert "team = getTeamName(player)" in game
assert 'other.Team.Name==s.team' in block or 'other.Team.Name == s.team' in block
assert 'type(s.team)~="string"' in block or "type(s.team) ~= \"string\"" in block
assert "local function applyClassicEggRelay(player: Player, data)" in game
assert "team=getTeamName(player)" in game
assert "team=getTeamName(target)" in game
assert "otherRoot" in block and "horizontal<=8" in block and "math.abs(delta.Y)<=4" in block
print("P0D_ACTUAL60_GAME_HUD_RELAY_TEAM_CONTRACT_PASS")
print("P0D_ACTUAL_60_GAME_HUD_TEAM_CONTRACT_DIAGNOSTIC_DONE")
