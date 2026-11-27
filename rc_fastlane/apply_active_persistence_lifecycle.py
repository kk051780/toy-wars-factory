"""Reuse the known active Game/HUD/Store persistence-lifecycle repairs."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_persistence_lifecycle"
ROUTES = {"server/Game.server.luau", "server/PersistentHatchStore.luau", "client/HUD.client.luau"}
FEATURE = "ACTIVE66_PERSISTENCE_LIFECYCLE_20261122"


def check(condition, name):
    if not condition:
        raise ValueError("ACTIVE_PERSISTENCE_" + name)


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    config = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = config["enabled"] if enabled_override is None else enabled_override
    check(type(enabled) is bool and profile == config["profile"], "CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    before = {name: gitblob(raw) for name, raw in original.items()}
    lock_path, feature_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, feature = (json.loads(path.read_bytes()) for path in (lock_path, feature_path))
    check(len(before) == lock["total_scripts"] == feature["total_sources"] == 67
          and before == lock["blobs"] == feature["source_gitblobs"]
          and lock["rc_active_h2_exit"]["after"] == before["server/Game.server.luau"], "CURRENT_GAME")
    raw = (PACKAGE / "persistence.json").read_bytes()
    check(hashlib.sha256(raw).hexdigest() == config["patch_sha256"], "PATCH_IDENTITY")
    edits, route_ids = json.loads(raw), config["routes"]
    check(set(edits) == set(route_ids) == ROUTES, "GAME_HUD_STORE_ONLY")
    selected = {}
    for name, identity in route_ids.items():
        check(before[name] == identity["before"], "ORIGINAL:" + name)
        candidate = patch(original[name].decode(), edits[name]).encode()
        check(gitblob(candidate) == identity["after"], "EXACT_RESULT:" + name)
        selected[name] = candidate
    game = selected["server/Game.server.luau"]
    check(game.count(b"remote.OnServerEvent:Connect(") == game.count(b"H2Score.deposit(") == 1
          and b"SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY" in game
          and b"pcall(SoloTeamBots.start," in game, "GAME_AND_MATCH_AUTHORITY")
    after = before | {name: gitblob(raw) for name, raw in selected.items()}
    receipt = {"feature": FEATURE, "routes": route_ids,
               "source_origins": config["source_origins"], "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    for name, candidate in selected.items():
        (dist / "src" / name).write_bytes(candidate)
    check(sources(dist) == original | selected, "ONLY_THREE_EXISTING_SOURCES")
    lock.update(blobs=after, rc_active_persistence_lifecycle=receipt)
    feature.update(source_gitblobs=after, rc_active_persistence_lifecycle=receipt)
    write_json(lock_path, lock)
    write_json(feature_path, feature)
    print("ACTIVE_RICH51_DURABLE_LIFECYCLE_EXACT_THREE_EXISTING_SOURCES_PASS")
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
            parser.error("--off-place is required to prove the exact current rollback")
        raw = args.off_place.read_bytes()
        measured = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        check(measured == config["off_place"], "OFF_PLACE_MISMATCH")
        print("ACTIVE_RICH51_LIFECYCLE_OFF_EXACT", json.dumps(measured))
    apply(args.dist, args.profile)
