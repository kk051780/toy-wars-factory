"""Select the authored physical Studio lobby on the active rich51 game."""

import argparse
import hashlib
import json
from pathlib import Path

import apply_fb007_lobby as author
from apply_active_ready import write_json
from apply_core_round_ready import once
from apply_p0_lobby_rebalance78 import patch_game as relocate_rebalance
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_safe_lobby"
FEATURE = author.FEATURE
GAME, TRAINING, ISLAND = author.GAME, author.V4, author.DEST


def check(condition, name):
    if not condition:
        raise ValueError("ACTIVE_SAFE_LOBBY_" + name)


def patch_game(game, spectator_helper):
    # The authored overlay predates #391. Leave one result recovery path.
    text = relocate_rebalance(author.patch_game(game))
    duplicated = "            -- Move real players to the separated lobby AFTER result display.\n"
    start, rest = text.split(duplicated, 1)
    winner = '            match.winner = ""\n'
    text = start + winner + rest.split(winner, 1)[1]
    text = once(text, "root.CFrame=map.teams[team].spawn + Vector3.new(0, 2, 0)\n"
                      "                    elseif (team==",
                "root.CFrame=if RunService:IsStudio() then LobbyIsland.spawn(team)\n"
                "                            else map.teams[team].spawn + Vector3.new(0, 2, 0)\n"
                "                    elseif (team==")
    text = once(text, '    map.model:SetAttribute("P0D_PHASE",match.phase)\n',
                '    if RunService:IsStudio() then map.model:SetAttribute("P0D_PHASE",match.phase) end\n')
    text = once(text, 'if (match.phase=="ACTIVE" and (position.Y < -30',
                'if ((not RunService:IsStudio() or match.phase=="ACTIVE") and (position.Y < -30')
    text = once(text, "                    root.CFrame = map.teams[getTeamName(entrant)].spawn + Vector3.new(0, 2, 0)\n",
                "                    root.CFrame = if RunService:IsStudio() then LobbyIsland.spawn(getTeamName(entrant))\n"
                "                        else map.teams[getTeamName(entrant)].spawn + Vector3.new(0, 2, 0)\n")
    assign = "local function assignSpawn(player: Player, character: Model)\n"
    text = once(text, assign, spectator_helper + "\n" + assign)
    old = """                else map.teams[team].spawn + Vector3.new(0, 2, 0)
        end
        stopWind(player) -- no burst survives respawn or a new Humanoid"""
    text = once(text, old, old.replace(
        "\n        end\n",
        '\n        elseif RunService:IsStudio() and player:GetAttribute("P0D_LateJoinSpectator")==true then\n'
        '            placeSpectatorSpawn(player,character,root,hum)\n        end\n'))
    old = '''local v4Locations={
    BEAST={56,-15},WEAPON={56,15},
    MAGIC={54,-49},ZOMBIE={54,49},
    VEHICLE={74,-49},BUILDING={74,49},
}
local function v4OnHomePad(player: Player): string?
    if match.phase=="RESULTS" or carry[player]~=nil then return nil end
    local alive,root=healthy(player)
    local team=getTeamName(player)
    if not alive or not root or (team~="RED" and team~="BLUE") then return nil end
    if math.abs(root.Position.Y-1)>10 then return nil end
    local sign=if team=="RED" then -1 else 1
    for _,skill in ipairs(V4XP.SKILLS) do
        local coord=v4Locations[skill]
        local dx=root.Position.X-sign*coord[1]
        local dz=root.Position.Z-coord[2]'''
    new = '''local function v4OnHomePad(player: Player): string?
    if match.phase~="LOBBY" or carry[player]~=nil then return nil end
    local alive,root=healthy(player)
    local team=getTeamName(player)
    if not alive or not root or (team~="RED" and team~="BLUE") then return nil end
    if math.abs(root.Position.Y-45)>10 then return nil end
    for _,skill in ipairs(V4XP.SKILLS) do
        local coord=LobbyIsland.padPosition(team,skill)
        local dx=root.Position.X-coord.X
        local dz=root.Position.Z-coord.Z'''
    text = once(text, old, new)
    check(text.count('remote.OnServerEvent:Connect(') == text.count('H2Score.deposit(') == 1
          and text.count('lobbyRecoveryRound[p] = endedRound') == 1
          and text.count('local function assignSpawn(') == 1
          and text.count('pcall(SoloTeamBots.start,') == 1
          and 'SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY' in text
          and 'equipNotice[player]==notice and persistenceState[player]=="SAVE_FAILED"' in text,
          "SOLE_GAME_AND_PREVIOUS_GUARDS")
    return text


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    config = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = config["enabled"] if enabled_override is None else enabled_override
    check(type(enabled) is bool and config["profile"] == profile, "CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    before = {name: gitblob(raw) for name, raw in original.items()}
    lock_path, feature_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, feature = (json.loads(path.read_bytes()) for path in (lock_path, feature_path))
    check(len(before) == lock["total_scripts"] == feature["total_sources"] == 67
          and before == lock["blobs"] == feature["source_gitblobs"]
          and lock["rc_active_persistence_lifecycle"]["routes"][GAME]["after"] == before[GAME]
          and ISLAND not in before, "CURRENT_ACTIVE")
    helper = (PACKAGE / "spectator_placement.luau").read_bytes()
    check(hashlib.sha256(helper).hexdigest() == config["placement_sha256"], "EXACT_PLACEMENT")
    selected = {GAME: patch_game(original[GAME].decode(), helper.decode()).encode(),
                TRAINING: author.patch_v4(original[TRAINING].decode()).encode(),
                ISLAND: author.MODULE.read_bytes()}
    after = before | {name: gitblob(raw) for name, raw in selected.items()}
    config_routes = config["routes"]
    check(set(selected) == set(config_routes) and gitblob(selected[ISLAND]) == author.MODULE_BLOB
          and all(config_routes[route] == {"before": before.get(route), "after": after[route]}
                  for route in selected), "EXACT_RUNTIME_SOURCES")
    project = json.loads((dist / "default.project.json").read_bytes())
    target = project["tree"]["ServerScriptService"]["TrapRaidersS1"]
    check(target["$path"] == "src/server" and "LobbyDojoIsland" not in target, "PROJECT_ROUTE")
    for name, raw in selected.items():
        (dist / "src" / name).write_bytes(raw)
    check(sources(dist) == original | selected, "GAME_TRAINING_AND_ONE_MODULE_ONLY")
    receipt = {"feature": FEATURE, "routes": config_routes, "source_origins": config["source_origins"],
               "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    lock.update(blobs=after, total_scripts=68, rc_active_safe_lobby=receipt)
    feature.update(source_gitblobs=after, total_sources=68, rc_active_safe_lobby=receipt)
    write_json(lock_path, lock)
    write_json(feature_path, feature)
    print("ACTIVE_RICH51_PHYSICAL_LOBBY_EXACT_68_SOURCES_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    parser.add_argument("--off-place", type=Path)
    args = parser.parse_args()
    config = json.loads((PACKAGE / "source_lock.json").read_bytes())
    if args.profile == config["profile"] and config["enabled"] is True:
        if args.off_place is None:
            parser.error("--off-place is required to prove the exact rollback")
        raw = args.off_place.read_bytes()
        measured = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        check(measured == config["off_place"], "OFF_PLACE_MISMATCH")
        print("ACTIVE_RICH51_SAFE_LOBBY_OFF_EXACT", json.dumps(measured))
    apply(args.dist,args.profile)
