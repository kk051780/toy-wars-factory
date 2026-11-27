"""Select the existing #395/#397 mode eligibility fix in playable rich51."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_mode_start"
ROUTES = {"server/Game.server.luau", "client/HUD.client.luau"}


def check(condition, name):
    if not condition:
        raise ValueError("ACTIVE_MODE_START_" + name)


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    config = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = config["enabled"] if enabled_override is None else enabled_override
    check(type(enabled) is bool and profile == config["profile"], "CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    before = {name: gitblob(body) for name, body in original.items()}
    lock_path, feature_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, feature = (json.loads(path.read_bytes()) for path in (lock_path, feature_path))
    check(len(before) == lock["total_scripts"] == feature["total_sources"] == 66
          and before == lock["blobs"] == feature["source_gitblobs"]
          and lock["rc_active_results"]["feature"] == "GQ910_ACTIVE_RESULTS_RETURN_391", "CURRENT_GAME")
    raw = (PACKAGE / "mode_vote.json").read_bytes()
    check(hashlib.sha256(raw).hexdigest() == config["patch_sha256"], "PATCH_IDENTITY")
    edits, routes = json.loads(raw), config["routes"]
    check(set(edits) == set(routes) == ROUTES, "GAME_AND_HUD_ONLY")
    selected = {}
    for name, identity in routes.items():
        check(before[name] == identity["before"], "ORIGINAL:" + name)
        candidate = patch(original[name].decode(), edits[name]).encode()
        check(gitblob(candidate) == identity["after"], "EXACT_RESULT:" + name)
        selected[name] = candidate
    for name, candidate in selected.items():
        (dist / "src" / name).write_bytes(candidate)
    check(sources(dist) == original | selected, "ONLY_TWO_EXISTING_SOURCES")
    after = before | {name: gitblob(raw) for name, raw in selected.items()}
    receipt = {"feature": "GQ910_ACTIVE_MODE_START_397", "routes": routes,
               "source_origins": config["source_origins"], "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    lock.update(blobs=after, rc_active_mode_start=receipt)
    feature.update(source_gitblobs=after, rc_active_mode_start=receipt)
    write_json(lock_path, lock)
    write_json(feature_path, feature)
    print("ACTIVE_RICH51_MODE_ELIGIBILITY_EXACT_GAME_AND_HUD_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile)
