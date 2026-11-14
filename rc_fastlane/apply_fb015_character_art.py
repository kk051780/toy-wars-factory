#!/usr/bin/env python3
"""FB-015 Gorogan-only beast visuals; minions are owned by separate PR #374.

Adds one Studio-only LocalScript to the latest exact canonical 66 assembly.
The 66 original script bytes (including Game, Horde and Gorogan) remain intact.
A newly built private 67 is NOT the official RC nor OWNER-approved art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "features/owner372_art/FB015CharacterArt.client.luau"
DEST = "client/FB015CharacterArt.client.luau"
BLOB = "b9b2efbdbdf3cb9e1244826a9b68a4a8f45b8398"
FEATURE = "FB015_GOROGAN_BEAST_VISUAL_V2"


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    assert root.is_dir(), "ART_SOURCE_DIST_MISSING"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}


def source_safety() -> bytes:
    data = SOURCE.read_bytes()
    assert gitblob(data) == BLOB, "ART_SOURCE_CHANGED"
    src = data.decode("utf8")
    for token in (
        'if not RunService:IsStudio() then return end',
        'Gorogan_ServerRig', 'ObsidianChestPlate', 'BoulderPauldron_',
        'RuneEye_', 'ObsidianBackSpike_', 'FB015GoroganDamageSparks',
        'RUNESTONE_TITAN', 'WeldConstraint', 'MAX_BEASTS = 2',
        'CanCollide = false', 'CanQuery = false',
        'MAX_DECOR_PARTS = 64', 'MAX_BEASTS = 2',
    ):
        assert token in src, ("MISSING_ART_CONTRACT", token)
    for bad in ("FireServer(", "RemoteEvent", "OnServerEvent:Connect(",
                "TakeDamage(", "DataStoreService", "UpdateAsync(",
                "MarketplaceService", "TeleportService", "PromptProductPurchase("):
        assert bad not in src, ("VISUAL_HAS_FORBIDDEN_AUTHORITY", bad)
    return data


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FB015_ART_OFF_NO_WRITE_EXACT")
        return False
    candidate = source_safety()
    original = sources(dist)
    assert len(original) == 66, ("REQUIRES_OFFICIAL66", len(original))
    assert DEST not in original, "DUPLICATE_ART_CLIENT"
    assert "server/Game.server.luau" in original
    assert "server/MusouHorde.luau" in original
    assert "server/GoroganRigDriver.luau" in original
    pins = {p: gitblob(raw) for p, raw in sorted(original.items())}
    lp, fp = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    pj = dist / "default.project.json"
    a = json.loads(lp.read_text("utf8"))
    b = json.loads(fp.read_text("utf8"))
    project = json.loads(pj.read_text("utf8"))
    assert a["total_scripts"] == 66 and a["blobs"] == pins, "SOURCE_BASE_DRIFT"
    assert b["total_sources"] == 66 and b["source_gitblobs"] == pins, "FEATURE_BASE_DRIFT"
    assert FEATURE not in b["feature_flags"], "VISUAL_ALREADY_INCLUDED"
    clients = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert any(isinstance(x, dict) and x.get("$path") == "src/client/HUD.client.luau"
               for x in clients.values()), "MAIN_HUD_MISSING"
    assert "FB015CharacterArt" not in clients, "DUPLICATE_LOCAL_SCRIPT"
    clients["FB015CharacterArt"] = {"$path": "src/" + DEST}
    updated = {**original, DEST: candidate}
    pins2 = {p: gitblob(raw) for p, raw in sorted(updated.items())}
    assert len(updated) == 67
    assert all(updated[p] == raw for p, raw in original.items())
    receipt = {
        "feedback": "FB-015",
        "feature": FEATURE,
        "added_client_script": DEST,
        "source_count": 67,
        "original66_unchanged": True,
        "no_Game_Horde_Gorogan_Remote_Store_change": True,
        "original_scripts_sha": pins,
        "studio_visual_fun": "NOT_TESTED",
        "mobile_performance": "NOT_TESTED",
        "approval": "PREP_ONLY_NOT_RC",
        "rollback": "omit adapter; OFF writes nothing",
    }
    a["total_scripts"] = 67
    a["blobs"] = pins2
    a["rc_fb015_character_art"] = receipt
    b["total_sources"] = 67
    b["source_gitblobs"] = pins2
    b["feature_flags"][FEATURE] = True
    b["rc_fb015_character_art"] = receipt
    (dist / "src" / DEST).write_bytes(candidate)
    pj.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", "utf8")
    lp.write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", "utf8")
    fp.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", "utf8")
    assert sources(dist) == updated
    print("FB015_BEAST_ONLY_SOURCE_67_AND_BASE_66_IDENTICAL")
    return True


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--dist", type=Path, required=True)
    cli.add_argument("--enabled", choices=("true", "false"), required=True)
    args = cli.parse_args()
    apply(args.dist, args.enabled == "true")
