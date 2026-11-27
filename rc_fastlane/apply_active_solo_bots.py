"""Select the existing FB005 five-bot rehearsal in the active rich51 Game."""

import argparse
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_core_round_ready import once
from apply_fb005_solo_bots import patch_game as author_game
from apply_p0_round_epoch78 import EPOCH_GUARD
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_solo_bots"
GAME = "server/Game.server.luau"
BOT = "server/SoloTeamBots.luau"
READY_RESET = ('    -- Every finished match must require a NEW, voluntary READY event.\n'
               '    for _, player in ipairs(Players:GetPlayers()) do roundReady[player] = false end\n')


def check(condition, name):
    if not condition:
        raise ValueError("ACTIVE_SOLO_BOTS_" + name)


def patch_game(source):
    body = author_game(once(source, READY_RESET, ""))
    stop = '    match.phase = "RESULTS"\n    SoloTeamBots.stop()\n'
    body = once(body, stop, stop + READY_RESET)
    tick = "    match.serial += 1\n"
    body = once(body, tick, tick + "    local startupSerial=match.serial\n")
    load = ("        p:LoadCharacter()\n    end\n"
            "    -- All previous epoch egg carriers were cleaned above while OLD mode was active.")
    body = once(body, load, load.replace("\n    -- All", "\n" + EPOCH_GUARD + "    -- All", 1))
    body = once(body,
                'if match.phase=="ACTIVE" and #Players:GetPlayers()==1 then\n'
                '                local player=Players:GetPlayers()[1]',
                'local roster=eligibleSoloPlayers()\n'
                '            if match.phase=="ACTIVE" and match.serial==startupSerial and #roster==1 then\n'
                '                local player=roster[1]')
    body = once(body, 'if match.phase=="ACTIVE" and studioSoloRoundStarted\n'
                     '                        and #Players:GetPlayers()==1 then',
                'if match.phase=="ACTIVE" and match.serial==startupSerial and studioSoloRoundStarted\n'
                '                        and #eligibleSoloPlayers()==1 then')
    body = once(body, '        if not EXPERIMENTAL_FIVE_EGG_MODE then\n'
                     '            local ok,err=pcall(SoloTeamBots.tick,now)',
                '        if RunService:IsStudio() and studioSoloRoundStarted and not EXPERIMENTAL_FIVE_EGG_MODE then\n'
                '            local ok,err=pcall(SoloTeamBots.tick,now)')
    body = once(body, 'if studioSoloRoundStarted and match.phase=="ACTIVE"\n'
                     '                    and #Players:GetPlayers()==1 then',
                'if studioSoloRoundStarted and match.phase=="ACTIVE"\n'
                '                    and #eligibleSoloPlayers()==1 then')
    check(body.count(READY_RESET) == 1 and body.count("remote.OnServerEvent:Connect(") == 1
          and body.count("H2Score.deposit(") == 1 and body.count("lobbyRecoveryRound[player]") == 3,
          "SOLE_GAME_AUTHORITY")
    return body


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    spec = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = spec["enabled"] if enabled_override is None else enabled_override
    check(type(enabled) is bool and spec["profile"] == profile, "CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    before = {path: gitblob(raw) for path, raw in original.items()}
    lock_path, features_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, features = (json.loads(path.read_bytes()) for path in (lock_path, features_path))
    check(len(before) == lock["total_scripts"] == features["total_sources"] == 66
          and before == lock["blobs"] == features["source_gitblobs"]
          and lock["rc_active_mode_start"]["feature"] == "GQ910_ACTIVE_MODE_START_397"
          and before[GAME] == spec["before_game"] and BOT not in original, "CURRENT_ACTIVE")
    game = patch_game(original[GAME].decode()).encode()
    bot = (PACKAGE / "SoloTeamBots.luau").read_bytes()
    check(gitblob(game) == spec["after_game"] and gitblob(bot) == spec["bot_blob"], "EXACT_AUTHOR_AND_GAME")
    project_path = dist / "default.project.json"
    project = json.loads(project_path.read_bytes())
    server = project["tree"]["ServerScriptService"]["TrapRaidersS1"]
    check(server.get("$path") == "src/server" and "SoloTeamBots" not in server, "PROJECT_MODULE_ROUTE")
    (dist / "src" / GAME).write_bytes(game)
    (dist / "src" / BOT).write_bytes(bot)
    check(sources(dist) == original | {GAME: game, BOT: bot}, "GAME_AND_BOT_ONLY")
    after = before | {GAME: spec["after_game"], BOT: spec["bot_blob"]}
    receipt = {"feature": "GQ910_ACTIVE_SOLO_TEAM_BOTS", "actor_module": BOT,
               "studio_classic_only": True, "maximum_bots": 5, "studio": "NOT_TESTED_ON_CURRENT_SHA",
               "source_origins": spec["source_origins"], "game_before": spec["before_game"],
               "game_after": spec["after_game"], "bot_blob": spec["bot_blob"]}
    lock.update(total_scripts=67, blobs=after, rc_active_solo_bots=receipt)
    features.update(total_sources=67, source_gitblobs=after, rc_active_solo_bots=receipt)
    write_json(lock_path, lock)
    write_json(features_path, features)
    print("ACTIVE_RICH51_SOLO_CLASSIC_EXISTING_BOT_FIVE_SOURCE_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile)
