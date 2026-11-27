"""Apply the existing #391 result recovery to rich51's original team spawn."""

import argparse
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_p0_results78 import NEW as AUTHORED_RECOVERY
from integrate import gitblob, sources


GAME = "server/Game.server.luau"
CONFIG = Path(__file__).resolve().parent / "features/active_results/source_lock.json"
MARKER = "            match.alarm = \"IDLE\"\n        end\n    end\n    -- Recovery uses the existing server-only authoritative tick."


def checked(condition, reason):
    if not condition:
        raise ValueError("ACTIVE_RESULTS_" + reason)


def patch_game(old):
    checked(old.count(MARKER) == 1 and old.count("remote.OnServerEvent:Connect(") == 1, "AUTHORITY_ANCHOR")
    jump = """            local endedRound = match.serial
            for _, p in ipairs(Players:GetPlayers()) do
                local team=getTeamName(p)
                if team=="RED" or team=="BLUE" then
                    local alive,root=healthy(p)
                    if alive and root then
                        root.AssemblyLinearVelocity=Vector3.zero
                        root.AssemblyAngularVelocity=Vector3.zero
"""
    recovery = AUTHORED_RECOVERY.replace("LobbyIsland.spawn(team)", "map.teams[team].spawn + Vector3.new(0, 2, 0)")
    recovery = recovery.replace(
        "-- #391 authored Game recovery: the existing CharacterAdded\n"
        "                        -- handler places this player on the physical lobby island.",
        "-- #391 recovery: the existing CharacterAdded uses the same team spawn.",
    )
    recovery = recovery.replace(
        'if p.Parent~=Players or match.phase~="LOBBY" then return end',
        'if p.Parent~=Players or match.phase~="LOBBY" or match.serial~=endedRound then return end\n'
        '                            local currentTeam=getTeamName(p)\n'
        '                            if currentTeam~="RED" and currentTeam~="BLUE" then return end',
    )
    suffix = "\n                end\n            end\n"
    start, rest = MARKER.split("\n", 1)
    amended = old.replace(MARKER, start + "\n" + jump + recovery + suffix + rest, 1)
    checked(amended.count("remote.OnServerEvent:Connect(") == 1 and amended.count("H2Score.deposit(") == 1,
            "SINGLE_GAME_AUTHORITY")
    return amended


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    config = json.loads(CONFIG.read_bytes())
    enabled = config["enabled"] if enabled_override is None else enabled_override
    checked(type(enabled) is bool and config["profile"] == profile, "CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    before = {path: gitblob(raw) for path, raw in original.items()}
    paths = (dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json")
    lock, features = (json.loads(path.read_bytes()) for path in paths)
    checked(len(before) == lock["total_scripts"] == features["total_sources"] == 66
            and before == lock["blobs"] == features["source_gitblobs"]
            and lock["rc_active_ready"]["feature"] == "P0D_ACTIVE_VOLUNTARY_READY"
            and before[GAME] == config["before"], "CURRENT_READY_SOURCE")
    amended = patch_game(original[GAME].decode()).encode()
    checked(gitblob(amended) == config["after"], "EXACT_GAME_RESULT")
    (dist / "src" / GAME).write_bytes(amended)
    checked(sources(dist) == original | {GAME: amended}, "GAME_ONLY")
    after = before | {GAME: config["after"]}
    receipt = {"feature": "GQ910_ACTIVE_RESULTS_RETURN_391", "source": GAME,
               "parent_game_blob": config["before"], "game_blob": config["after"],
               "source_issue": config["source_issue"], "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    lock.update(blobs=after, rc_active_results=receipt)
    features.update(source_gitblobs=after, rc_active_results=receipt)
    for path, value in zip(paths, (lock, features)):
        write_json(path, value)
    print("ACTIVE_RESULTS_RICH51_EXACT_GAME_ONLY_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile)
