#!/usr/bin/env python3
"""No-network no-overwrite exact artifact staging for OWNER's *future* Roblox Studio QA.

This only checks/gathers files. It never opens Studio, touches the current Place,
starts a Roblox session, changes Github/main/RC, or approves a public release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

PLACE = "TRAP_RAIDERS_S1_SIX_SAFE_UX_REVIEW.rbxlx"
GAME_SHA = "5b6f1c8fe1917ebe86ba243b5442c491120a14ca028e3ef1363a634cce884eb6"
GAME_BYTES = 157878
AUDIT = "SOURCE_AUDIT.json"
MANIFEST = "TRANSFER_MANIFEST.json"
STAGING_DIR = "P0D_S1_SIX_SAFE_QA_5b6f1c8fe191"
FILES = [PLACE, AUDIT, "STUDIO_QA_CARDS.md", "SCENARIOS_NOT_TESTED.json", "README.md"]

class Blocked(Exception):
    pass

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify(bundle: Path) -> dict:
    if not bundle.is_dir() or bundle.is_symlink():
        raise Blocked("BUNDLE_ROOT_INVALID")
    manifest_path = bundle / MANIFEST
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise Blocked("MANIFEST_MISSING_OR_SYMLINK")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as e:
        raise Blocked("MANIFEST_UNREADABLE") from e
    if manifest.get("format") != "P0D_S1_V6_OWNER_STUDIO_TRANSFER_V1" or manifest.get("place_sha256") != GAME_SHA:
        raise Blocked("MANIFEST_PROVENANCE_MISMATCH")
    hashes = manifest.get("files")
    if not isinstance(hashes, dict) or set(hashes) != set(FILES):
        raise Blocked("MANIFEST_FILE_SET_INVALID")
    for name in FILES:
        if name != Path(name).name or name.startswith("."):
            raise Blocked("UNSAFE_BUNDLE_NAME")
        path = bundle / name
        if path.is_symlink() or not path.is_file():
            raise Blocked("SOURCE_FILE_MISSING_OR_SYMLINK:" + name)
        raw = path.read_bytes()
        row = hashes[name]
        if not isinstance(row, dict) or type(row.get("bytes")) is not int or row["bytes"] != len(raw) or row.get("sha256") != sha256(raw):
            raise Blocked("SOURCE_FILE_DIGEST_MISMATCH:" + name)
    place = (bundle / PLACE).read_bytes()
    if len(place) != GAME_BYTES or sha256(place) != GAME_SHA:
        raise Blocked("PLACE_PIN_MISMATCH")
    audit = json.loads((bundle / AUDIT).read_text(encoding="utf-8"))
    if not all((audit.get("rbxlx_sha256") == GAME_SHA,
                audit.get("rbxlx_bytes") == GAME_BYTES,
                audit.get("scripts_byte_exact") == 21,
                audit.get("source_and_xml_integrity") == "PASS",
                audit.get("studio_multiplayer") == "NOT_TESTED",
                audit.get("real_mobile") == "NOT_TESTED",
                audit.get("owner_public_release_approval") is False,
                audit.get("official_original_RC_sha") == "1263a03701211a652b99b91d2339575dc8104eff")):
        raise Blocked("AUDIT_PROVENANCE_OR_STUDIO_STATUS_INVALID")
    # Independently recorded six-safe exact compiled source scope.
    if (audit.get("independent_CI_source_SHA") != "65785c2e3b9bc37a6962f9ace128fbfcbb670901"
        or audit.get("scripts_byte_exact") != 21
        or audit.get("local_adversarial_mutations_rejected") != 7
        or audit.get("script_classes") != {"Script":1,"LocalScript":3,"ModuleScript":17}):
        raise Blocked("SIX_SOURCE_EXACT_PROVENANCE_MISMATCH")
    scenarios = json.loads((bundle / "SCENARIOS_NOT_TESTED.json").read_text(encoding="utf-8"))
    if (scenarios.get("source_place_sha256") != GAME_SHA or
        scenarios.get("studio_tested") is not False or
        scenarios.get("owner_publish_approval") is not False or
        len(scenarios.get("scenarios", [])) != 30 or
        len({r.get("id") for r in scenarios["scenarios"]}) != 30 or
        any(r.get("status") != "NOT_TESTED" or r.get("evidence") != [] for r in scenarios["scenarios"])):
        raise Blocked("NOT_TESTED_SCENARIOS_INVALID")
    return {"status": "SOURCE_INSPECTION_PASS_NOT_STUDIO", "place_sha256":GAME_SHA,
            "bytes":GAME_BYTES,"files":len(FILES),"scenarios":30,
            "real_roblox_studio":"NOT_TESTED", "public_release_authorized":False}

def _protect_destination(destination: Path, bundle: Path) -> Path:
    if not destination.is_absolute() or not destination.is_dir():
        raise Blocked("DESTINATION_MUST_BE_EXISTING_ABSOLUTE_DIRECTORY")
    # Check every existing component rather than silently following a symlink.
    node = destination
    while True:
        if node.is_symlink():
            raise Blocked("DESTINATION_SYMLINK_FORBIDDEN")
        if node == node.parent:
            break
        node = node.parent
    target = destination / STAGING_DIR
    if target.exists() or target.is_symlink():
        raise Blocked("DESTINATION_ALREADY_EXISTS_REFUSE_OVERWRITE")
    if target.resolve(strict=False) == bundle.resolve():
        raise Blocked("DESTINATION_COLLIDES_WITH_BUNDLE")
    return target

def stage(bundle: Path, destination: Path) -> dict:
    receipt = verify(bundle)
    target = _protect_destination(destination, bundle)
    # exclusive mkdir and exclusive file writes: do not replace prior QA or PC files.
    try:
        target.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as e:
        raise Blocked("DESTINATION_ALREADY_EXISTS_REFUSE_OVERWRITE") from e
    for name in FILES + [MANIFEST]:
        with (bundle/name).open("rb") as src, (target/name).open("xb") as dst:
            shutil.copyfileobj(src, dst, length=65536)
    verified = verify(target)
    if verified["place_sha256"] != receipt["place_sha256"]:
        raise Blocked("COPIED_PLACE_DIGEST_MISMATCH")
    # Never generate PASS gameplay receipt. Exact original source receipt remains NOT_TESTED.
    return {"status":"ISOLATED_TEST_COPY_PREPARED_NOT_STUDIO", "copy":str(target),
            "rbxlx":str(target/PLACE),"no_existing_files_overwritten":True,
            "real_roblox_studio":"NOT_TESTED", "public_release_authorized":False}

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle",type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument("--prepare",action="store_true",help="Explicitly create an isolated NEW test copy, no overwrites")
    ap.add_argument("--destination",type=Path,help="Already-existing absolute parent directory for NEW test folder")
    args = ap.parse_args(argv)
    try:
        if args.prepare:
            if args.destination is None:
                raise Blocked("DESTINATION_REQUIRED_FOR_PREPARE")
            result = stage(args.bundle,args.destination)
        else:
            result = verify(args.bundle)
    except (Blocked, OSError, ValueError, TypeError, UnicodeError) as e:
        print(json.dumps({"status":"BLOCKED", "error":str(e),
                          "roblox_studio":"NOT_TESTED", "published":False},ensure_ascii=False))
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())
