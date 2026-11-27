"""Select the existing voluntary READY and first-minute HUD for playable rich51."""

import argparse
import json
from pathlib import Path

from apply_core_round_ready import patch_game, patch_hud
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "features/active_ready"
TARGETS = ("client/HUD.client.luau", "server/Game.server.luau", "shared/FirstMinuteModel.luau")


def require(condition, reason):
    if not condition:
        raise ValueError("ACTIVE_READY_" + reason)


def write_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    config = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = config["enabled"] if enabled_override is None else enabled_override
    require(type(enabled) is bool and config["profile"] == profile and tuple(config["routes"]) == TARGETS, "CONFIG")
    if not enabled:
        return False
    active = json.loads((ROOT / "ACTIVE.json").read_bytes())
    require(active["active_profile"] == profile and active["active_source_commit"] == config["source_commit"],
            "PROFILE")
    original = sources(dist)
    before = {name: gitblob(raw) for name, raw in original.items()}
    lock_path = dist / "SOURCE_LOCK.json"
    feature_path = dist / "RC_FEATURE_LOCK.json"
    lock, feature = (json.loads(path.read_bytes()) for path in (lock_path, feature_path))
    require(len(original) == lock["total_scripts"] == feature["total_sources"] == 66
            and before == lock["blobs"] == feature["source_gitblobs"]
            and feature["feature_flags"]["TWIN_BOND_PVE_COMPANION_V1"] is True, "CURRENT_AUTHORED_STAGE")
    context = json.loads((PACKAGE / "coach_spectator_layout.json").read_bytes())
    require(tuple(context) == TARGETS and all(before.get(name) == row["before"]
            for name, row in config["routes"].items()), "ORIGINAL_READY_INPUTS")
    prepared = {
        TARGETS[0]: patch_hud(original[TARGETS[0]].decode()),
        TARGETS[1]: patch_game(original[TARGETS[1]].decode()),
        TARGETS[2]: original[TARGETS[2]].decode(),
    }
    selected = {}
    for name, row in config["routes"].items():
        variant = patch(prepared[name], context[name]).encode()
        require(gitblob(variant) == row["after"] and row["before"] != row["after"], "EXACT_SOURCE:" + name)
        selected[name] = variant
    authority = selected["server/Game.server.luau"]
    require(authority.count(b"remote.OnServerEvent:Connect(") == 1 and authority.count(b"H2Score.deposit(") == 1,
            "SINGLE_GAME_AUTHORITY")
    hud = selected["client/HUD.client.luau"].decode()
    require(hud.count('{"NINJA","🥷 暗殺者","影刃"}') == 1 and "🥷 忍者" not in hud, "ASSASSIN_LABEL_COMPATIBILITY")
    after = before | {name: gitblob(raw) for name, raw in selected.items()}
    receipt = {"feature": "P0D_ACTIVE_VOLUNTARY_READY", "source_commit": config["source_commit"],
               "routes": config["routes"], "compiled_source_count": 66,
               "rollback": "Set features/active_ready/source_lock.json enabled=false and rebuild.",
               "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    for name, raw in selected.items():
        (dist / "src" / name).write_bytes(raw)
    require(sources(dist) == original | selected, "ONLY_THREE_SOURCES")
    lock.update(blobs=after, rc_active_ready=receipt)
    feature.update(source_gitblobs=after, rc_active_ready=receipt)
    write_json(lock_path, lock)
    write_json(feature_path, feature)
    print("ACTIVE_VOLUNTARY_READY_RICH51_EXACT_THREE_EXISTING_SOURCES_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile)
