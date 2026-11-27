"""Apply the existing #391 result recovery to rich51's original team spawn."""

import argparse
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_core_round_ready import once
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
    defer = "                        task.defer(function()"
    checked(AUTHORED_RECOVERY.count(defer) == 1, "AUTHOR_RECOVERY_ANCHOR")
    recovery = AUTHORED_RECOVERY.split(defer, 1)[0].replace(
        "LobbyIsland.spawn(team)", "map.teams[team].spawn + Vector3.new(0, 2, 0)"
    ).split("                        -- #391", 1)[0] + """                        -- CharacterAdded uses this same team spawn.
                        lobbyRecoveryRound[p] = endedRound
                        task.defer(function()
                            if lobbyRecoveryRound[p] ~= endedRound then return end
                            if p.Parent == Players and match.phase == "LOBBY" and match.serial == endedRound then
                                local currentTeam = getTeamName(p)
                                if (currentTeam == "RED" or currentTeam == "BLUE") and not healthy(p) then
                                    local ok,err=pcall(function() p:LoadCharacter() end)
                                    if not ok then warn("P0D_LOBBY_RESPAWN_FAIL",err) end
                                end
                            end
                            if lobbyRecoveryRound[p] == endedRound then lobbyRecoveryRound[p] = nil end
                        end)
                    end"""
    suffix = "\n                end\n            end\n"
    start, rest = MARKER.split("\n", 1)
    amended = old.replace(MARKER, start + "\n" + jump + recovery + suffix + rest, 1)
    roster = "local roundReady: {[Player]: boolean} = {}"
    amended = once(amended, roster, roster + "\nlocal lobbyRecoveryRound: {[Player]: number} = {}")
    amended = once(amended, "if roundReady[player] ~= true then return false end",
                   "if roundReady[player] ~= true or lobbyRecoveryRound[player] ~= nil then return false end")
    phase = '    if match.phase ~= "LOBBY" and match.phase ~= "COUNTDOWN" then return end'
    amended = once(amended, phase, phase + "\n"
                   "    if data.ready and (lobbyRecoveryRound[player] ~= nil or not healthy(player)) then return end")
    leave = "    roundReady[player] = nil"
    amended = once(amended, leave, leave + "\n    lobbyRecoveryRound[player] = nil")
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
