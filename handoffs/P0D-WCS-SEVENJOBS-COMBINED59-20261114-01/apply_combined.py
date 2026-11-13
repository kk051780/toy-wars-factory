#!/usr/bin/env python3
"""Private 58 WCS + 7jobs --> 59 source composition. Never writes official RC.

Works from exact RC57+WCS source-locked candidate PR300, injects original
author #297 7jobs patch in a reversible *temporary dist*, preserving WCS
byte-for-byte. Author's patcher expects 57: WCS is temporarily set aside and
restored after the author patch. No canonical branch or Game authority copy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
WCS = "server/WCS_CrystalCanyon.server.luau"
JOBS = "server/SevenJobsRules.luau"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
AUTHOR_PIN = "2f5acfb10dfba0fad7b0245a68d16e500c744a61"
WCS_PIN = "7d2afad5e9b8df410ea0eb83ad962cf42ab98e71"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def srcs(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def save(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def apply(dist: Path, author: Path, enabled: bool) -> bool:
    dist, author = dist.resolve(), author.resolve()
    orig = srcs(dist)
    assert len(orig) == 58, ("EXPECTED_WCS58_BASE", len(orig))
    assert GAME in orig and HUD in orig and WCS in orig and JOBS not in orig
    assert blob(orig[WCS]) == WCS_PIN, "WCS_BASE_GIT_BLOB_DRIFT"
    assert 'GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")~=true' in orig[WCS].decode(), "NOT_FAIL_CLOSED_WCS"
    patcher = author / "tools" / "apply_seven_jobs.py"
    assert blob(patcher.read_bytes()) == AUTHOR_PIN, "SEVEN_JOBS_ORIGINAL_AUTHOR_DRIFT"
    assert (author / "patches/Game.patch.zlib.b64").is_file()
    assert (author / "patches/HUD.patch.zlib.b64").is_file()
    assert (author / "src/SevenJobsRules.luau").is_file()
    flags = json.loads((ROOT / "rc_fastlane/FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    assert flags["WCS_F01_C01"]["enabled"] is True
    assert type(flags["SEVEN_JOBS_PVE_V1"]["enabled"]) is bool
    assert flags["WCS_F01_C01"]["source"][0]["blob"] == WCS_PIN
    lock_path = dist / "SOURCE_LOCK.json"
    fl_path = dist / "RC_FEATURE_LOCK.json"
    before_lock = lock_path.read_bytes()
    before_fl = fl_path.read_bytes()
    lock = json.loads(before_lock)
    flock = json.loads(before_fl)
    assert lock["total_scripts"] == 58 and lock["blobs"] == {p:blob(b) for p,b in orig.items()}, "RC58_LOCK_DRIFT"
    assert flock["total_sources"] == 58, "RC58_FEATURE_LOCK_DRIFT"
    assert flock["source_gitblobs"] == {p:blob(b) for p,b in orig.items()}, "RC58_FEATURE_PINS_DRIFT"
    project = json.loads((dist/"default.project.json").read_text("utf8"))
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    assert project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["TrapRaidersHUD"]["$path"] == "src/client/HUD.client.luau"
    assert project["tree"]["ServerStorage"]["$attributes"]["P0D_RC_ENABLE_WCS_F01_C01"] is True
    if not enabled or not flags["SEVEN_JOBS_PVE_V1"]["enabled"]:
        assert srcs(dist) == orig
        assert lock_path.read_bytes() == before_lock and fl_path.read_bytes() == before_fl
        print("P0D_COMBINED_JOBS_OFF_WCS58_BYTE_EXACT_PASS")
        return False
    # Mutations below are limited to a disposable candidate source dist.
    wcs_file = dist/"src"/WCS
    receipt_path = dist/"P0D_SEVEN_JOBS_RECEIPT.json"
    existing_receipt = receipt_path.read_bytes() if receipt_path.exists() else None
    extra = None
    try:
        wcs_file.unlink()
        # Execute author code unchanged, pinned by Git blob, against original
        # 57 source bodies. It refuses unknown Game/HUD or duplicate Modules.
        subprocess.run([sys.executable, "-B", str(patcher), "--dist", str(dist)],
                       check=True, timeout=120)
        save(wcs_file, orig[WCS])
        result = srcs(dist)
        assert len(result) == 59, ("WANT_59_SOURCE", len(result))
        assert set(result) == set(orig) | {JOBS}, "UNEXPECTED_SOURCE"
        assert {p for p in orig if orig[p] != result[p]} == {GAME,HUD}, "ORIGINAL_BODY_DRIFT"
        assert all(result[p] == b for p,b in orig.items() if p not in (GAME,HUD))
        assert result[WCS] == orig[WCS], "WCS_SCRIPT_CHANGED"
        assert blob(result[JOBS]) == "a7253d36cb67df47d4ba65d35af212ed1eb7b5b2"
        core = result[GAME].decode()
        assert core.count("remote.OnServerEvent:Connect(") == 1
        assert core.count('remote.Name = "TrapRaidersS1Remote"') == 1
        assert 'GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")' in core
        assert "ScoutSpeciesPolicy" in core and "SavedPvePolicy.mergeWithEarned(" in core
        assert result["server/PersistentHatchStore.luau"] == orig["server/PersistentHatchStore.luau"]
        lock["total_scripts"] = 59
        lock["blobs"] = {p:blob(v) for p,v in sorted(result.items())}
        lock["rc_seven_jobs_combo_overlay"] = {
            "id":"SEVEN_JOBS_PVE_V1", "author_patcher_gitblob":AUTHOR_PIN,
            "original_58_count":58, "wcs_byte_identical":True,
            "changed_original_scripts":[GAME,HUD],"new_source":JOBS,
            "studio_only":True,"real_engine":"NOT_TESTED",
            "rollback":"Disable SEVEN_JOBS_PVE_V1 and rebuild WCS58"}
        flock["total_sources"] = 59
        flock["source_gitblobs"] = {p:blob(v) for p,v in sorted(result.items())}
        flock["feature_flags"]["SEVEN_JOBS_PVE_V1"] = True
        save(lock_path, (json.dumps(lock, ensure_ascii=False, indent=2)+"\n").encode())
        save(fl_path, (json.dumps(flock, ensure_ascii=False, indent=2)+"\n").encode())
        # Author's temporary receipt was for 57->58 without WCS: prevent
        # presenting that as final combined output.
        if receipt_path.exists():
            author_receipt = json.loads(receipt_path.read_text("utf8"))
            author_receipt["author_patcher_temporary_count"] = 58
            author_receipt["total_source_count"] = 59
            author_receipt["wcs_existing_script_retained"] = True
            author_receipt["official_rc_adopted"] = False
            author_receipt["native_luau"] = "NOT_TESTED_AT_RECEIPT_WRITE"
            save(receipt_path, (json.dumps(author_receipt, ensure_ascii=False, indent=2)+"\n").encode())
        print("P0D_WCS_SEVENJOBS_COMBINED59_SOURCE_EXACT_56_OF_58_UNMODIFIED_PASS")
        return True
    except Exception:
        # Fail closed; no leaked partial Game/HUD or missing WCS.
        current = srcs(dist)
        for p in set(current) - set(orig):
            (dist/"src"/p).unlink()
        for p,data in orig.items():
            save(dist/"src"/p, data)
        save(lock_path, before_lock)
        save(fl_path, before_fl)
        if existing_receipt is None and receipt_path.exists():
            receipt_path.unlink()
        elif existing_receipt is not None:
            save(receipt_path, existing_receipt)
        assert srcs(dist) == orig, "ROLLBACK_NOT_EXACT"
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--off-test", action="store_true")
    cli = parser.parse_args()
    apply(cli.dist, cli.author, not cli.off_test)
