#!/usr/bin/env python3
"""Read-only integrity/security preflight for locked, NON-RUNNABLE S1 D07+D08 source stage.

No network, no Roblox, no source writes. Exact PUBLIC_SOURCE_V1 and Git blob check.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT_KEYS = {"files", "format", "game_id", "packet_id", "public_source_allowed", "work_id"}
ENTRY_KEYS = {"path", "sha256", "size"}
EXPECTED = {
    "CanonicalEventBridge.luau", "ChaosEventCore.luau",
    "TrustedGoroganActivationMapper.luau", "GoroganServerAICore.luau",
    "GoroganAttackReceiptWindow.luau", "GoroganDamageBoundary.luau",
    "GoroganRigDriver.luau", "GoroganCombinedRuntime.luau",
    "GoroganClientAdapter.client.luau", "GoroganVisualPolicy.luau",
    "GoroganVisualPrefab.luau",
}
FORBIDDEN = ("GoroganServerRuntime.luau", "CanonicalEventServerAdapter.server.luau", "Smoke.server.luau")
SHA = re.compile(r"^[0-9a-f]{64}$")
BLOB = re.compile(r"^[0-9a-f]{40}$")


def read_json(file: Path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(file.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))


def safe_file(root: Path, rel: str) -> bytes:
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/") or "\x00" in rel:
        raise ValueError("INVALID_PATH")
    if any(p in ("", ".", "..") or p.startswith(".") for p in rel.split("/")):
        raise ValueError("PATH_TRAVERSAL_OR_HIDDEN")
    file = root / rel
    if file.is_symlink() or not file.is_file():
        raise ValueError("MISSING_OR_SYMLINK:" + rel)
    return file.read_bytes()


def stage_verify(root: Path) -> dict:
    lock = read_json(root / "SOURCE_LOCK.json")
    if lock.get("format") != "P0D_S1_D07_D08_SOURCE_STAGE_LOCK_V1" or lock.get("game_id") != "TRAP_RAIDERS":
        raise ValueError("WRONG_SOURCE_LOCK")
    if lock.get("status") != "PUBLIC_SOURCE_STAGED_ONLY_NOT_EXECUTABLE_RC":
        raise ValueError("FALSE_RELEASE_READY")
    if lock.get("base_s1_game_sha") != "35d7d0525388e885aac8281eff2315a59831e0cf":
        raise ValueError("BASE_NOT_PINNED")
    units = lock.get("selected")
    if not isinstance(units, list) or len(units) != 11:
        raise ValueError("INVALID_SELECTION_COUNT")
    seen, blob_seen = set(), set()
    for unit in units:
        name, side = unit["filename"], unit["side"]
        rel = unit["staged_path"]
        if name not in EXPECTED or name in FORBIDDEN or name in seen:
            raise ValueError("DUPLICATE_OR_UNSELECTED_MODULE")
        if side not in ("server", "client") or rel != f"staged/src/{side}/{name}":
            raise ValueError("WRONG_SERVER_CLIENT_MOUNT")
        if (side == "client") != (name in {
            "GoroganClientAdapter.client.luau", "GoroganVisualPolicy.luau", "GoroganVisualPrefab.luau"}):
            raise ValueError("SCRIPT_SIDE_VIOLATION")
        if not isinstance(unit.get("source_commit"), str) or not BLOB.fullmatch(unit["source_commit"]):
            raise ValueError("MISSING_SOURCE_COMMIT")
        if not SHA.fullmatch(unit["sha256"]) or not BLOB.fullmatch(unit["git_blob"]):
            raise ValueError("BAD_SOURCE_DIGEST")
        data = safe_file(root, rel)
        if len(data) != unit["size"] or hashlib.sha256(data).hexdigest() != unit["sha256"]:
            raise ValueError("SOURCE_BYTE_TAMPER:" + name)
        git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if git_blob != unit["git_blob"]:
            raise ValueError("SOURCE_GIT_BLOB_TAMPER:" + name)
        data.decode("utf-8", "strict")
        seen.add(name)
        blob_seen.add(rel)
    if seen != EXPECTED or len(blob_seen) != 11:
        raise ValueError("INCOMPLETE_SELECTION")
    # Explicitly assert the existing approved mapper is the ONLY boundary.
    p = (root / "staged/src/server")
    bridge = (p / "CanonicalEventBridge.luau").read_text()
    combined = (p / "GoroganCombinedRuntime.luau").read_text()
    mapper = (p / "TrustedGoroganActivationMapper.luau").read_text()
    visual = (root / "staged/src/client/GoroganClientAdapter.client.luau").read_text()
    if not ('phase = event.event' in bridge and 'validUntil = event.untilAt' in bridge
            and 'activation.event~="ACTIVATE"' in combined
            and 'local endAt=activation.untilAt' in combined
            and 'untilAt = envelope.validUntil' in mapper
            and 'self.attestedActivation == activation' in mapper):
        raise ValueError("D08_D07_AUTHORITY_BRIDGE_CONTRACT_CHANGED")
    if "TRAP_BossVisualEvent" not in visual:
        raise ValueError("CLIENT_VISUAL_REMOTE_CONTRACT_CHANGED")
    manifest = read_json(root / "BUILD_MANIFEST.json")
    if set(manifest) != ROOT_KEYS or manifest.get("format") != "P0D_PUBLIC_SOURCE_V1" or manifest.get("public_source_allowed") is not True:
        raise ValueError("PUBLIC_MANIFEST_SCHEMA")
    if manifest.get("packet_id") != lock.get("packet_id") or manifest.get("game_id") != lock.get("game_id"):
        raise ValueError("PUBLIC_MANIFEST_IDENTITY")
    listed = manifest.get("files")
    if not isinstance(listed, list) or len(listed) != 15:
        raise ValueError("PUBLIC_MANIFEST_ENTRY_COUNT")
    prev = ""
    files = set()
    for row in listed:
        if not isinstance(row, dict) or set(row) != ENTRY_KEYS or not SHA.fullmatch(row["sha256"]) or type(row["size"]) is not int:
            raise ValueError("PUBLIC_MANIFEST_BAD_ENTRY")
        rel = row["path"]
        if prev and rel <= prev:
            raise ValueError("UNSORTED_OR_DUPLICATE_PUBLIC_ENTRIES")
        prev = rel
        data = safe_file(root, rel)
        if len(data) != row["size"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("PUBLIC_MANIFEST_BYTE_TAMPER:" + rel)
        files.add(rel)
    if not blob_seen.issubset(files):
        raise ValueError("STAGE_FILES_MISSING_FROM_PUBLIC_MANIFEST")
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    if actual != files | {"BUILD_MANIFEST.json"}:
        raise ValueError("UNTRACKED_OR_MISSING_PUBLIC_FILE")
    # Only a selection/transport PASS; no effective Game or Studio test.
    return {"status": "PASS_11_ORIGINAL_SOURCE_STAGE_ONLY_NOT_RUNNABLE_RC",
            "verified_original_luau": 11, "manifest_files": 15,
            "game_assembled": False, "studio_tested": False,
            "release_approved": False}


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("usage: verify_source_stage.py <SOURCE_STAGE_ROOT>", file=sys.stderr)
        return 2
    try:
        report = stage_verify(Path(argv[0]))
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError, UnicodeError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_SOURCE_STAGE", "error": str(exc),
                          "studio_tested": False, "release_approved": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
