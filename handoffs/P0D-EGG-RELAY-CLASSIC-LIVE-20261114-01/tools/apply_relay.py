#!/usr/bin/env python3
"""Fail-closed PRE-FLIGHT ONLY original-Game/HUD patch for unpublished RC.
The sole #220 RC writer must adopt in canonical RC after genuine native/Rojo QA.
No Game, Store, Remote or public place is created here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = "EGG_RELAY_CLASSIC_V1"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
POLICY = "server/EggRelayPolicy.luau"

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()

def patch(data: str, ops: list[dict]) -> str:
    for index, entry in enumerate(ops):
        anchor = entry["anchor"]
        assert type(anchor) is str and type(entry["replace"]) is str
        assert anchor and data.count(anchor) == 1, ("ANCHOR_DRIFT", index, anchor[:100])
        data = data.replace(anchor, entry["replace"], 1)
    return data

def source_bodies(src: Path) -> dict[str, bytes]:
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def run(dist: Path, policy: Path) -> None:
    spec = json.loads((ROOT / "PATCH_OPS.json").read_text(encoding="utf8"))
    assert spec["feature_id"] == FEATURE
    assert spec["rc_integrated"] is False and spec["real_studio"] == "NOT_TESTED"
    assert len(spec["game_ops"]) == 9 and len(spec["hud_ops"]) == 6

    # Stage all inputs and validate original RC authority/locks BEFORE writes.
    src = dist / "src"
    bodies = source_bodies(src)
    assert GAME in bodies and HUD in bodies and POLICY not in bodies
    assert len(bodies) in (2, 56), ("UNSUPPORTED_BASE_SOURCE_COUNT", len(bodies))
    pins = {p: blob(data) for p, data in bodies.items()}
    lock_file = dist / "SOURCE_LOCK.json"
    assert lock_file.is_file(), "MISSING_ORIGINAL_SOURCE_LOCK"
    lock = json.loads(lock_file.read_text(encoding="utf8"))
    assert lock.get("total_scripts") == len(bodies), "STALE_SOURCE_COUNT"
    assert lock.get("blobs") == pins, "SOURCE_LOCK_MISMATCH"
    receipt_file = dist / "RC_FEATURE_LOCK.json"
    receipt = None
    if receipt_file.exists():
        receipt = json.loads(receipt_file.read_text(encoding="utf8"))
        assert receipt.get("total_sources") == len(bodies), "STALE_FEATURE_COUNT"
        assert receipt.get("source_gitblobs") == pins, "FEATURE_LOCK_MISMATCH"
        assert FEATURE not in receipt.get("feature_flags", {}), "FEATURE_DUPLICATE_ADMISSION"

    raw_policy = policy.read_bytes()
    assert blob(raw_policy) == spec["source_policy_gitblob"], "POLICY_BLOB_DRIFT"
    before_game = bodies[GAME].decode("utf8")
    before_hud = bodies[HUD].decode("utf8")
    assert before_game.count('remote.OnServerEvent:Connect(') == 1
    assert before_game.count('remote.Name = "TrapRaidersS1Remote"') == 1
    assert before_hud.count("local seq = 0") == 1
    assert "local function applyClassicEggRelay" not in before_game

    after_game = patch(before_game, spec["game_ops"])
    after_hud = patch(before_hud, spec["hud_ops"])
    assert after_game.count('remote.OnServerEvent:Connect(') == 1
    assert after_game.count('remote.Name = "TrapRaidersS1Remote"') == 1
    assert after_game.count("H2Score.deposit(") == before_game.count("H2Score.deposit(")
    assert after_game.count("match.scores[team] += 1") == before_game.count("match.scores[team] += 1")
    assert after_game.count("match.eggOwners[egg]=target") == 1
    assert after_game.count("carry[target]=egg") == 1
    assert after_game.count("workspace:Raycast(rootA.Position, direction, rayParams)") == 1
    assert after_game.count("local now = os.clock()") == 1, "RELAY_MUST_USE_MONOTONIC_CLOCK"
    assert 'or EXPERIMENTAL_FIVE_EGG_MODE' in after_game, "H2_NOT_ATOMICALLY_SUPPORTED"
    assert after_hud.count("local seq = 0") == 1
    assert after_hud.count("relayButton.MouseButton1Click:Connect(fireClassicEggRelay)") == 1
    assert after_hud.count('KeyCode.H') == 1
    assert 'EGG_RELAY' in after_hud and 'EGG_RELAY' in after_game

    # Stage the full final source inventory before any on-disk changes.
    after = dict(bodies)
    after[GAME] = after_game.encode("utf8")
    after[HUD] = after_hud.encode("utf8")
    after[POLICY] = raw_policy
    assert len(after) == len(bodies) + 1
    assert sorted(k for k in bodies if bodies[k] != after[k]) == [HUD, GAME]
    assert sorted(set(after) - set(bodies)) == [POLICY]
    target_pins = {p: blob(raw) for p, raw in sorted(after.items())}
    lock["blobs"] = target_pins
    lock["total_scripts"] = len(after)
    lock["relay_classic_preview"] = {
        "feature_id": FEATURE,
        "stage": "SOURCE_CANDIDATE_NOT_OFFICIAL_RC",
        "five_egg_mode": "NOT_SUPPORTED",
        "engine_studio": "NOT_TESTED",
        "rollback": "omit patch and rebuild original current RC",
    }
    if receipt is not None:
        receipt["total_sources"] = len(after)
        receipt["source_gitblobs"] = target_pins
        receipt.setdefault("feature_flags", {})[FEATURE] = True
        receipt["relay_stage"] = "SOURCE_CANDIDATE_NOT_ENGINE_TESTED"

    # All expected, deterministic failures are above this point. Do not mutate
    # the original working dist if policy SHA, anchors or either lock is wrong.
    (src / GAME).write_bytes(after[GAME])
    (src / HUD).write_bytes(after[HUD])
    (src / POLICY).write_bytes(after[POLICY])
    lock_file.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if receipt is not None:
        receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("P0D_EGG_RELAY_CLASSIC_PREFLIGHT_PATCH_APPLIED_NOT_ENGINE_VERIFIED")

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dist", type=Path, required=True)
    cli.add_argument("--policy", type=Path, required=True)
    args = cli.parse_args()
    run(args.dist, args.policy)
