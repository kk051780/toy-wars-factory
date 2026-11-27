"""Select two fixed Active rich51 route scripts after the original WCS gate."""

import json
from pathlib import Path

from integrate import gitblob as blob, sources as selected_sources


ROOT = Path(__file__).resolve().parent
PACKET = ROOT / "features/active_sky_routes"
TARGETS = ("server/H1FunWorld.server.luau", "server/WCS_CrystalCanyon.server.luau")
SOURCE_COMMIT = "79123d35cd7afdd5f4f9941675bc2d2cf382ac4e"


def require(condition, reason):
    if not condition:
        raise ValueError("ACTIVE_SKY_ROUTES_" + reason)


def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    config = json.loads((PACKET / "source_lock.json").read_bytes())
    enabled = config["enabled"] if enabled_override is None else enabled_override
    require(type(enabled) is bool and config["profile"] == "rich51"
            and config["source_commit"] == SOURCE_COMMIT and tuple(config["routes"]) == TARGETS, "CONFIG")
    if not enabled:
        print("ACTIVE_SKY_ROUTES_OFF_ORIGINAL_WCS")
        return False
    selected = json.loads((ROOT / "ACTIVE.json").read_bytes())
    require(selected["active_profile"] == "rich51"
            and selected["source_profiles"]["rich51"]["source_commit"] == SOURCE_COMMIT
            and selected["active_source_commit"] == SOURCE_COMMIT, "FORMAL_SELECTION")
    before = selected_sources(dist)
    path = dist / "SOURCE_LOCK.json"
    lock = json.loads(path.read_bytes())
    before_blobs = {name: blob(raw) for name, raw in before.items()}
    require(len(before) == lock["total_scripts"] and before_blobs == lock["blobs"]
            and lock["rc_wcs_f01_c01_overlay"]["id"] == "WCS_F01_C01", "CURRENT_DIST")
    require(all(n in before for n in TARGETS), "ROUTES_MISSING")
    author = lock["rc_wcs_f01_c01_overlay"]["author_script_blob"]
    require(author == config["routes"][TARGETS[1]]["before"], "ORIGINAL_WCS_AUTHOR")
    project = json.loads((dist / "default.project.json").read_bytes())
    require(project["tree"]["ServerStorage"]["$attributes"]["P0D_RC_ENABLE_WCS_F01_C01"] is True,
            "ORIGINAL_WCS_FLAG")
    after = {}
    for name, identity in config["routes"].items():
        candidate = (PACKET / Path(name).name).read_bytes()
        require(identity["before"] == before_blobs[name] and identity["after"] == blob(candidate)
                and identity["after"] != identity["before"], "FIXED_SOURCE:" + name)
        after[name] = candidate
    feature_path = dist / "RC_FEATURE_LOCK.json"
    feature_lock = json.loads(feature_path.read_bytes()) if feature_path.exists() else None
    if feature_lock is not None:
        require(feature_lock["source_gitblobs"] == before_blobs
                and feature_lock["total_sources"] == len(before), "CURRENT_FEATURE_LOCK")
    after_blobs = before_blobs | {name: blob(raw) for name, raw in after.items()}
    receipt = {"feature": "GQ910_ACTIVE_SKY_ROUTES", "source_commit": SOURCE_COMMIT,
               "routes": config["routes"], "input_source_count": len(before),
               "only_existing_geometry_sources_replaced": True,
               "rollback": "Set features/active_sky_routes/source_lock.json enabled=false and rebuild.",
               "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    lock.update(blobs=after_blobs, rc_active_sky_routes=receipt)
    if feature_lock is not None:
        feature_lock.update(source_gitblobs=after_blobs, rc_active_sky_routes=receipt)
    for name, raw in after.items():
        (dist / "src" / name).write_bytes(raw)
    require(selected_sources(dist) == before | after, "ONLY_TWO_SOURCES")
    path.write_bytes(encode(lock))
    if feature_lock is not None:
        feature_path.write_bytes(encode(feature_lock))
    print("ACTIVE_SKY_ROUTES_RICH51_EXACT_TWO_EXISTING_SOURCES_PASS")
    return True
