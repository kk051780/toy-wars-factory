"""Mount the existing #479 undead squad on the selected rich51 role ability."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_undead_squad"
GAME = "server/Game.server.luau"
SQUAD = "server/UndeadSquad.luau"
HORDE = "server/MusouHorde.luau"
ROLE_RULES = "server/SevenJobsRules.luau"
FEATURE = "FB026_UNDEAD_SIEGE_ACTIVE_V1"


def require(condition, label):
    if not condition:
        raise ValueError("ACTIVE_UNDEAD_SQUAD_" + label)


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    pins = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = pins["enabled"] if enabled_override is None else enabled_override
    require(type(enabled) is bool and pins["profile"] == profile and pins["feature"] == FEATURE, "CONFIG")
    if not enabled:
        return False

    before = sources(dist)
    blobs = {path: gitblob(raw) for path, raw in before.items()}
    lock_path, feature_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, feature_lock = (json.loads(path.read_bytes()) for path in (lock_path, feature_path))
    routes = pins["routes"]
    require(len(blobs) == lock["total_scripts"] == feature_lock["total_sources"] == 68
            and blobs == lock["blobs"] == feature_lock["source_gitblobs"]
            and set(routes) == {GAME, SQUAD} and SQUAD not in before
            and blobs[GAME] == routes[GAME]["before"]
            and lock["rc_active_confirmed_hit"]["routes"][GAME]["after"] == blobs[GAME]
            and blobs[HORDE] == pins["horde"] and blobs[ROLE_RULES] == pins["role_rules"],
            "CURRENT_ACTIVE_INPUTS")
    adapter = (PACKAGE / "adapter.json").read_bytes()
    require(hashlib.sha256(adapter).hexdigest() == pins["adapter_sha256"], "ADAPTER_IDENTITY")
    original_module = (PACKAGE / "UndeadSquad.luau").read_bytes()
    require(gitblob(original_module) == pins["source_origin"]["module_git_blob"], "ORIGINAL_MODULE")
    edits = json.loads(adapter)
    game = patch(before[GAME].decode("utf-8"), edits["game"]).encode("utf-8")
    module = patch(original_module.decode("utf-8"), edits["squad"]).encode("utf-8")
    require(gitblob(module) == routes[SQUAD]["after"], "SQUAD_OUTPUT")
    require(gitblob(game) == routes[GAME]["after"]
            and game.count(b"remote.OnServerEvent:Connect(") == 1
            and game.count(b"SevenJobs.Undead.cast(player,{") == 1, "GAME_AUTHORITY")
    changes = {GAME: game, SQUAD: module}
    for name, raw in changes.items():
        (dist / "src" / name).write_bytes(raw)
    require(sources(dist) == before | changes, "EXACT_SOURCE_VECTOR")
    output_blobs = blobs | {name: gitblob(raw) for name, raw in changes.items()}
    receipt = {"feature": FEATURE, "design_id": pins["design_id"], "routes": routes,
               "source_origin": pins["source_origin"], "studio_only": True,
               "off_place": pins["off_place"], "engine": "NOT_TESTED"}
    lock.update(total_scripts=len(output_blobs), blobs=output_blobs, rc_active_undead_squad=receipt)
    feature_lock.update(total_sources=len(output_blobs), source_gitblobs=output_blobs,
                        rc_active_undead_squad=receipt)
    write_json(lock_path, lock)
    write_json(feature_path, feature_lock)
    print("ACTIVE_UNDEAD_SQUAD_EXACT_GAME_AND_ORIGINAL_MODULE_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    parser.add_argument("--off-place", type=Path)
    args = parser.parse_args()
    pins = json.loads((PACKAGE / "source_lock.json").read_bytes())
    if args.profile == pins["profile"] and pins["enabled"] is True:
        if args.off_place is None:
            parser.error("--off-place is required for enabled rich51")
        off = args.off_place.read_bytes()
        require({"bytes": len(off), "sha256": hashlib.sha256(off).hexdigest()} == pins["off_place"],
                "IMMEDIATE_OFF_PLACE")
        print("ACTIVE_UNDEAD_SQUAD_IMMEDIATE_OFF_EXACT", json.dumps(pins["off_place"]))
    apply(args.dist, args.profile)
