#!/usr/bin/env python3
"""Isolated P0-D HUD clean optional source overlay on compiled canonical66.

A-lane PREP candidate; only B may intake into official RC after real QA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "features/p0_hud_clean/BattleHUDGovernor.client.luau"
BLOB = "20536bc52b108edf94564013e2900aa25bd3aaf3"
FEATURE = "P0D_HUD_CLEAR_COMBAT_V1"
DEST = "client/BattleHUDGovernor.client.luau"


def blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def read_src(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("P0D_HUD_CLEAN_OFF_NO_MUTATION")
        return False
    code = SOURCE.read_bytes()
    assert blob(code) == BLOB, "CANDIDATE_SOURCE_DRIFT"
    text = code.decode("utf8")
    assert 'if not RunService:IsStudio() then return end' in text
    assert 'TrapRaidersS1Remote' in text and 'TrapRaidersS1HUD' in text
    assert 'BattleSelfHPNumerical' in text
    assert 'statusLabel.Visible = false' in text
    assert 'statusLabel.Visible = true' in text
    for forbidden in ('Instance.new("RemoteEvent")', 'FireServer(',
                      'TakeDamage(', 'DataStoreService', 'MarketplaceService'):
        assert forbidden not in text, forbidden
    before = read_src(dist)
    assert len(before) == 66, ("REQUIRES_CANONICAL66", len(before))
    assert DEST not in before, "HUD_DUPLICATE"
    assert 'server/Game.server.luau' in before
    assert 'client/HUD.client.luau' in before
    lp = dist / "SOURCE_LOCK.json"
    fp = dist / "RC_FEATURE_LOCK.json"
    lock = json.loads(lp.read_text("utf8"))
    f = json.loads(fp.read_text("utf8"))
    pins = {p: blob(v) for p, v in sorted(before.items())}
    assert lock["total_scripts"] == 66 and lock["blobs"] == pins
    assert f["total_sources"] == 66 and f["source_gitblobs"] == pins
    assert FEATURE not in f["feature_flags"]
    project = dist / "default.project.json"
    cfg = json.loads(project.read_text("utf8"))
    starter = cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert any(v.get("$path") == "src/client/HUD.client.luau"
               for v in starter.values() if isinstance(v, dict))
    assert "BattleHUDGovernor" not in starter
    starter["BattleHUDGovernor"] = {"$path": "src/" + DEST}
    after = {**before, DEST: code}
    updated = {p: blob(v) for p, v in sorted(after.items())}
    assert len(after) == 67
    assert all(after[p] == old for p, old in before.items())
    lock["total_scripts"] = 67
    lock["blobs"] = updated
    lock["rc_battle_hud_governor"] = {
        "id": FEATURE, "new_client": DEST,
        "original66_byte_identical": True,
        "no_Game_Store_Remote_change": True,
        "display": "minimal numeric castle+player HP, timer, egg score; optional overlays suppressed during battle",
        "owner_fun": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "rollback": "omit this overlay to keep exact prior canonical66",
    }
    f["total_sources"] = 67
    f["source_gitblobs"] = updated
    f["feature_flags"][FEATURE] = True
    (dist / "src" / DEST).write_bytes(code)
    project.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    fp.write_text(json.dumps(f, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    assert read_src(dist) == after
    print("P0D_HUD_CLEAN_67_SOURCE_EXACT_ORIGINAL66_UNCHANGED_PASS")
    return True

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dist", type=Path, required=True)
    cli.add_argument("--enabled", required=True, choices=("true", "false"))
    args = cli.parse_args()
    apply(args.dist, args.enabled == "true")
