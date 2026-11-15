#!/usr/bin/env python3
"""Source-exact, additive Rojo staging of the *real* P0D-031 Roblox Lua source.

This is a PREP artifact, never an authorized writer to the canonical RC branch.
The output is a separate dist tree chosen by the integration team.
"""
import argparse
import hashlib
import json
from pathlib import Path

FEATURE_NAME = "P0DSkyFeather"
FEATURE_FILE = "P0DSkyFeather.server.luau"
DEST = f"server/{FEATURE_FILE}"


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    return {p.relative_to(dist / "src").as_posix(): p.read_bytes()
            for p in sorted((dist / "src").rglob("*.luau"))}


def stage(dist: Path, feature: Path) -> dict:
    """Stage only after verifying 100% current source lock; no implicit overwrite."""
    config_path = dist / "default.project.json"
    lock_path = dist / "SOURCE_LOCK.json"
    config = json.loads(config_path.read_text(encoding="utf8"))
    lock = json.loads(lock_path.read_text(encoding="utf8"))
    before = sources(dist)
    if not before or lock.get("total_scripts") != len(before):
        raise ValueError("SOURCE_COUNT_MISMATCH")
    exact = {name: blob(raw) for name, raw in sorted(before.items())}
    if exact != lock.get("blobs"):
        raise ValueError("SOURCE_LOCK_MISMATCH")
    if "server/Game.server.luau" not in before or sum(
            k == "server/Game.server.luau" for k in before) != 1:
        raise ValueError("GAME_OWNER_MISSING")
    if DEST in before:
        raise ValueError("FEATURE_ALREADY_STAGED")
    server = config["tree"].get("ServerScriptService")
    if not isinstance(server, dict) or FEATURE_NAME in server:
        raise ValueError("ROJO_SERVER_NAMESPACE_CONFLICT")
    raw = feature.read_bytes()
    source = raw.decode("utf8")
    must = ("ProximityPrompt", "Tool", "tool.Activated:Connect",
            "LinearVelocity", "Players.PlayerRemoving", "script:GetAttribute(\"EnablePrivatePreview\")")
    if not all(x in source for x in must):
        raise ValueError("MISSING_PLAYABLE_FLIGHT_INTERFACE")
    forbidden = ("OnServerEvent:Connect", "Instance.new(\"RemoteEvent\")",
                 "TakeDamage(", "DataStoreService", "MarketplaceService",
                 "UpdateAsync(", "GetDataStore(")
    if any(x in source for x in forbidden):
        raise ValueError("AUTHORITY_COLLISION")
    # All validation precedes the first write.
    destination = dist / "src" / DEST
    if destination.exists():
        raise ValueError("DEST_EXISTS")
    destination.write_bytes(raw)
    server[FEATURE_NAME] = {"$path": f"src/{DEST}"}
    after = sources(dist)
    if len(after) != len(before) + 1 or any(after[k] != v for k, v in before.items()):
        raise AssertionError("ORIGINAL_SOURCE_MUTATED")
    if sum(k == "server/Game.server.luau" for k in after) != 1:
        raise AssertionError("SECOND_GAME_OWNER")
    lock["total_scripts"] = len(after)
    lock["blobs"] = {name: blob(data) for name, data in sorted(after.items())}
    lock["p0d031_private_stage"] = {
        "feature_id": "P0D-031",
        "new_source": DEST,
        "new_blob": blob(raw),
        "prior_script_count": len(before),
        "original_scripts_byte_exact": True,
        "engine_proof": "NOT_TESTED",
        "activation": "Studio or explicitly enabled private server only",
    }
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return {"state": "PRIVATE_SOURCE_STAGED_NOT_RC_INTEGRATED",
            "original_count": len(before), "total": len(after),
            "source_blob": blob(raw), "source_bytes": len(raw),
            "existing_byte_exact": True, "native_luau": "NOT_RUN", "studio": "NOT_RUN"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", type=Path, required=True)
    p.add_argument("--feature", type=Path, default=Path(__file__).with_name(FEATURE_FILE))
    a = p.parse_args()
    print(json.dumps(stage(a.dist, a.feature), ensure_ascii=False, indent=2))
