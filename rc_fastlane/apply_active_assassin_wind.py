"""Restore the existing #476 wind action for the selected ACTIVE assassin."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_assassin_wind"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
RULES = "server/S1RaiderWindRules.luau"
FEATURE = "FB020_ASSASSIN_WIND_ACTIVE_V1"


def require(condition, label):
    if not condition:
        raise ValueError("ACTIVE_ASSASSIN_WIND_" + label)


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    pins = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = pins["enabled"] if enabled_override is None else enabled_override
    require(type(enabled) is bool and pins["profile"] == profile and pins["feature"] == FEATURE, "CONFIG")
    if not enabled:
        return False
    before = sources(dist)
    identities = {path: gitblob(raw) for path, raw in before.items()}
    source_path, feature_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    source_lock, feature_lock = (json.loads(path.read_bytes()) for path in (source_path, feature_path))
    require(len(identities) == source_lock["total_scripts"] == feature_lock["total_sources"] == 69
            and identities == source_lock["blobs"] == feature_lock["source_gitblobs"]
            and identities[RULES] == pins["rules_git_blob"]
            and source_lock["rc_active_undead_squad"]["routes"][GAME]["after"] == identities[GAME]
            and source_lock["rc_active_confirmed_hit"]["routes"][HUD]["after"] == identities[HUD],
            "CURRENT_PROFILE")
    original = (PACKAGE / "original_wind_patch.py").read_bytes()
    require(gitblob(original) == pins["source_origin"]["patch_git_blob"], "AUTHOR_PROVENANCE")
    adapter = (PACKAGE / "adapter.json").read_bytes()
    require(hashlib.sha256(adapter).hexdigest() == pins["adapter_sha256"], "ADAPTER_IDENTITY")
    edits, routes = json.loads(adapter), pins["routes"]
    require(set(edits) == set(routes) == {GAME, HUD}, "EXACT_TWO_ROUTES")
    changes = {}
    for path, route in routes.items():
        require(identities[path] == route["before"], "INPUT:" + path)
        body = patch(before[path].decode("utf-8"), edits[path]).encode("utf-8")
        require(gitblob(body) == route["after"], "OUTPUT:" + path)
        changes[path] = body
    require(changes[GAME].count(b"remote.OnServerEvent:Connect(") == 1
            and changes[HUD].count(b'action("WIND_BURST", nil)') == 2,
            "EXISTING_REMOTE_AND_TWO_INPUTS")
    for path, raw in changes.items():
        (dist / "src" / path).write_bytes(raw)
    require(sources(dist) == before | changes, "SELECTED_ROUTE_INVARIANCE")
    identities.update({path: route["after"] for path, route in routes.items()})
    receipt = {"feature": FEATURE, "routes": routes, "rules_git_blob": pins["rules_git_blob"],
               "source_origin": pins["source_origin"], "studio_alias_only": True,
               "off_place": pins["off_place"], "engine": "NOT_TESTED"}
    source_lock.update(blobs=identities, rc_active_assassin_wind=receipt)
    feature_lock.update(source_gitblobs=identities, rc_active_assassin_wind=receipt)
    write_json(source_path, source_lock)
    write_json(feature_path, feature_lock)
    print("ACTIVE_WIND_EXACT_GAME_HUD_EXISTING_RULES_PASS")
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
        print("ACTIVE_WIND_IMMEDIATE_OFF_EXACT", json.dumps(pins["off_place"]))
    apply(args.dist, args.profile)
