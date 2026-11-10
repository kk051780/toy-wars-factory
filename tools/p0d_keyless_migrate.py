#!/usr/bin/env python3
"""P0-D OWNER-local, keyless legacy ZIP migration.

No network, no decryption, no secret scanning, no GitHub upload, no Roblox Studio.
A known original ZIP is required for every converted packet; its recorded SHA256
is always checked BEFORE any data are accepted. Unavailable source stays blocked.
Python 3.10+ stdlib only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import shutil
import zipfile

ID_RE = re.compile(r"[A-Za-z0-9_-]{3,110}\Z")
SHA_RE = re.compile(r"[a-f0-9]{64}\Z")
REGISTRY_SCHEMA = "P0D_KEYLESS_MIGRATION_REGISTRY_V1"
RECEIPT_SCHEMA = "P0D_KEYLESS_BATCH_RECEIPT_V1"
RECEIPT_NAME = "KEYLESS_RECEIPT.json"
MAX_SOURCE_BYTES = 512 * 1024 * 1024
MAX_MEMBER_BYTES = 128 * 1024 * 1024
MAX_PACKET_FILES = 3000
MAX_TOTAL_UNPACKED = 1024 * 1024 * 1024
MAX_COMPRESS_RATIO = 500
FIXED_DATE = (2026, 11, 10, 0, 0, 0)


class MigrationError(Exception):
    pass


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_registry(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != REGISTRY_SCHEMA or data.get("game_id") != "TRAP_RAIDERS" or data.get("work_id") != "p0d-siege-v19":
        raise MigrationError("REGISTRY_CONTRACT_INVALID")
    packets = data.get("packets")
    if not isinstance(packets, list) or not packets or len(packets) > 200:
        raise MigrationError("PACKET_REGISTRY_INVALID")
    ids = set()
    for p in packets:
        pid = p.get("packet_id")
        if not isinstance(pid, str) or not ID_RE.fullmatch(pid) or pid in ids:
            raise MigrationError("DUPLICATE_OR_UNSAFE_PACKET_ID")
        ids.add(pid)
        if not isinstance(p.get("original_zip_sha256"), str) or not SHA_RE.fullmatch(p["original_zip_sha256"]):
            raise MigrationError(f"PACKET_SHA_MISSING: {pid}")
        if p.get("status") in ("SUPERSEDED", "WITHDRAWN"):
            continue  # retained in metadata, never accepted in output
        if not isinstance(p.get("source_commit", ""), str):
            raise MigrationError("BAD_PUBLIC_SOURCE_COMMIT")
    return packets


def check_member_name(name: str) -> str:
    # ZIP member paths must be platform-independent and safe for Windows.
    if not isinstance(name, str) or not name or len(name) > 240 or "\\" in name or "\x00" in name:
        raise MigrationError("UNSAFE_SOURCE_MEMBER_NAME")
    if name.startswith("/") or re.match(r"^[a-zA-Z]:", name):
        raise MigrationError("UNSAFE_SOURCE_ABSOLUTE_MEMBER")
    norm = PurePosixPath(name)
    parts = norm.parts
    if any(x in ("", ".", "..") or ":" in x or x.endswith(" ") or x.endswith(".") for x in parts):
        raise MigrationError("UNSAFE_SOURCE_TRAVERSAL_OR_WINDOWS_MEMBER")
    if any(x.upper().split(".")[0] in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"} for x in parts):
        raise MigrationError("UNSAFE_RESERVED_WINDOWS_MEMBER")
    return str(norm)


def read_original_zip(original: Path, expected_sha: str) -> list[tuple[str, bytes]]:
    if original.is_symlink() or not original.is_file():
        raise MigrationError("ORIGINAL_NOT_A_REAL_FILE")
    if original.stat().st_size > MAX_SOURCE_BYTES:
        raise MigrationError("ORIGINAL_ARCHIVE_TOO_LARGE")
    actual = sha_file(original)
    if actual != expected_sha:
        raise MigrationError(f"ORIGINAL_ZIP_SHA_MISMATCH: expected {expected_sha}, actual {actual}")
    try:
        with zipfile.ZipFile(original, "r", allowZip64=False) as z:
            infos = z.infolist()
            if not 1 <= len(infos) <= MAX_PACKET_FILES:
                raise MigrationError("ORIGINAL_ZIP_ENTRY_COUNT_INVALID")
            result = []
            names_casefold = set()
            total = 0
            for info in infos:
                if info.is_dir():
                    check_member_name(info.filename.rstrip("/"))
                    continue
                name = check_member_name(info.filename)
                fold = name.casefold()
                if fold in names_casefold:
                    raise MigrationError("DUPLICATE_OR_CASE_COLLIDING_SOURCE_MEMBER")
                names_casefold.add(fold)
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise MigrationError("SOURCE_SYMLINK_MEMBER")
                if info.flag_bits & 1:
                    raise MigrationError("ENCRYPTED_SOURCE_ZIP_NEEDS_ORIGINAL_PLAINTEXT")
                if info.file_size > MAX_MEMBER_BYTES:
                    raise MigrationError("ORIGINAL_MEMBER_TOO_LARGE")
                if info.file_size > 0 and (info.file_size / max(info.compress_size, 1)) > MAX_COMPRESS_RATIO:
                    raise MigrationError("SOURCE_ZIP_BOMB_RATIO")
                total += info.file_size
                if total > MAX_TOTAL_UNPACKED:
                    raise MigrationError("SOURCE_ARCHIVE_TOO_LARGE_UNPACKED")
                raw = z.read(info)
                if len(raw) != info.file_size:
                    raise MigrationError("SOURCE_MEMBER_BAD_SIZE")
                result.append((name, raw))
            if not result:
                raise MigrationError("ORIGINAL_EMPTY_ZIP")
            return result
    except (zipfile.BadZipFile, EOFError) as exc:
        raise MigrationError("ORIGINAL_BAD_ZIP") from exc


def get_source_path(inbox: Path, packet_id: str) -> Path:
    # No file-system search: exact name in one folder, controlled by OWNER.
    return inbox / (packet_id + ".zip")


def status_report(registry: list[dict], inbox: Path, deep: bool) -> dict:
    statuses = []
    for p in registry:
        pid = p["packet_id"]
        src = get_source_path(inbox, pid)
        if p.get("status") in ("SUPERSEDED", "WITHDRAWN"):
            state = "SUPERSEDED_DO_NOT_PACKAGE"
        elif not src.exists():
            state = "BLOCKED_SOURCE_NOT_PRESENT"
        else:
            try:
                if src.is_symlink() or sha_file(src) != p["original_zip_sha256"]:
                    state = "BLOCKED_SOURCE_SHA_MISMATCH"
                elif deep:
                    read_original_zip(src, p["original_zip_sha256"])
                    state = "READY_ORIGINAL_SHA_AND_ZIP_PASS"
                else:
                    state = "READY_ORIGINAL_SHA_PASS_ONLY"
            except (MigrationError, OSError):
                state = "BLOCKED_UNSAFE_SOURCE_ZIP"
        statuses.append({"packet_id": pid, "feature_id": p.get("feature_id"), "state": state, "source_filename": src.name,
                         "original_zip_sha256": p["original_zip_sha256"]})
    return {"schema": "P0D_KEYLESS_MIGRATION_STATUS_V1", "summary": {
                "total": len(statuses),
                "ready": sum(s["state"].startswith("READY") for s in statuses),
                "blocked": sum(s["state"].startswith("BLOCKED") for s in statuses),
                "superseded": sum(s["state"].startswith("SUPERSEDED") for s in statuses)},
            "packets": statuses}


def json_bytes(obj: dict) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def add_zip_bytes(z: zipfile.ZipFile, name: str, content: bytes):
    info = zipfile.ZipInfo(name, FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o100644 << 16)
    z.writestr(info, content, compresslevel=6)


def package_originals(registry: list[dict], inbox: Path, output: Path, require_all: bool) -> dict:
    if output.exists():
        raise MigrationError("OUTPUT_EXISTS_NO_OVERWRITE")
    if not inbox.is_dir() or inbox.is_symlink():
        raise MigrationError("OWNER_INBOX_MISSING_OR_SYMLINK")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise MigrationError("OUTPUT_PARENT_MISSING_OR_SYMLINK")
    converted = []
    pending = []
    by_packet = []
    out_names = {RECEIPT_NAME.casefold()}
    total_bytes = 0
    for p in registry:
        pid = p["packet_id"]
        if p.get("status") in ("SUPERSEDED", "WITHDRAWN"):
            pending.append({"packet_id": pid, "state": "SUPERSEDED_DO_NOT_PACKAGE"})
            continue
        path = get_source_path(inbox, pid)
        if not path.exists():
            pending.append({"packet_id": pid, "state": "BLOCKED_SOURCE_NOT_PRESENT"})
            continue
        try:
            items = read_original_zip(path, p["original_zip_sha256"])
        except (MigrationError, OSError) as e:
            pending.append({"packet_id": pid, "state": "BLOCKED_SOURCE_INVALID", "reason": str(e)[:130]})
            continue
        converted.append({"packet_id": pid, "feature_id": p.get("feature_id", ""),
                         "original_zip_sha256": p["original_zip_sha256"],
                         "source_commit": p.get("source_commit", ""), "files": len(items)})
        for rel, raw in items:
            name = "packets/" + pid + "/" + rel
            if name.casefold() in out_names:
                raise MigrationError("BUNDLE_MEMBER_CASE_COLLISION")
            out_names.add(name.casefold())
            total_bytes += len(raw)
            if total_bytes > MAX_TOTAL_UNPACKED:
                raise MigrationError("BUNDLE_TOO_LARGE")
            by_packet.append((name, raw))
    if require_all and pending:
        raise MigrationError(f"STRICT_ALL_FAILED: {len(pending)} missing/superseded/unsafe originals")
    if not converted:
        raise MigrationError("NO_VERIFIED_ORIGINAL_ZIPS_TO_PACKAGE")
    receipt = {"schema": RECEIPT_SCHEMA, "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19",
               "transport": "OWNER_LOCAL_ONLY_NO_KEY", "is_partial": bool(pending), "converted": converted,
               "pending": pending, "members": [{"path": name, "sha256": digest(raw), "size": len(raw)}
                                           for name, raw in by_packet],
               "note": "Only owner-verified original ZIP data; no encrypted source was decrypted or fetched. Do not place this unencrypted commercial ZIP on public GitHub."}
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".tmp", prefix=".p0d_", delete=False) as f:
            temp_path = Path(f.name)
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as z:
            for name, raw in by_packet:
                add_zip_bytes(z, name, raw)
            add_zip_bytes(z, RECEIPT_NAME, json_bytes(receipt))
        outer = sha_file(temp_path)
        os.link(temp_path, output)  # fail if destination created concurrently; no replacement
        return {"status": "BUNDLE_CREATED_OWNER_LOCAL_ONLY", "output": str(output), "sha256": outer,
                "bytes": output.stat().st_size, "converted": [p["packet_id"] for p in converted], "pending": pending}
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def verify_bundle(bundle: Path, expected_sha: str, registry: list[dict]) -> dict:
    if not SHA_RE.fullmatch(expected_sha):
        raise MigrationError("EXPECTED_BUNDLE_SHA_INVALID")
    if bundle.is_symlink() or not bundle.is_file() or bundle.stat().st_size > MAX_SOURCE_BYTES:
        raise MigrationError("BUNDLE_MISSING_OR_TOO_LARGE")
    if sha_file(bundle) != expected_sha:
        raise MigrationError("BUNDLE_SHA_MISMATCH")
    known = {p["packet_id"]: p for p in registry}
    with zipfile.ZipFile(bundle, "r", allowZip64=False) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(x.casefold() for x in names)) or RECEIPT_NAME not in names:
            raise MigrationError("BUNDLE_DUPLICATE_OR_NO_RECEIPT")
        for info in infos:
            check_member_name(info.filename)
            if info.is_dir() or (info.external_attr >> 16) & 0o170000 == stat.S_IFLNK or info.flag_bits & 1:
                raise MigrationError("BUNDLE_UNSAFE_MEMBER")
        rec = json.loads(z.read(RECEIPT_NAME))
        if rec.get("schema") != RECEIPT_SCHEMA or rec.get("game_id") != "TRAP_RAIDERS" or rec.get("work_id") != "p0d-siege-v19":
            raise MigrationError("BUNDLE_RECEIPT_SCHEMA_INVALID")
        entries = rec.get("members")
        if not isinstance(entries, list) or len(entries) > MAX_PACKET_FILES * 200:
            raise MigrationError("BUNDLE_MEMBER_REGISTRY_INVALID")
        if sorted(x["path"] for x in entries) != sorted(x for x in names if x != RECEIPT_NAME):
            raise MigrationError("BUNDLE_MEMBER_SET_MISMATCH")
        approved_ids = set()
        for pkt in rec.get("converted", []):
            pid = pkt["packet_id"]
            if pid not in known or known[pid].get("status") in ("WITHDRAWN", "SUPERSEDED"):
                raise MigrationError("UNKNOWN_OR_SUPERSEDED_PACKET")
            if pkt["original_zip_sha256"] != known[pid]["original_zip_sha256"]:
                raise MigrationError("SOURCE_ZIP_SHA_NOT_IN_REGISTRY")
            if pid in approved_ids:
                raise MigrationError("BUNDLE_DUPLICATE_PACKET")
            approved_ids.add(pid)
        total = 0
        for e in entries:
            pid = e["path"].split("/")[1] if e["path"].startswith("packets/") else None
            if pid not in approved_ids or not SHA_RE.fullmatch(e["sha256"]):
                raise MigrationError("UNREGISTERED_MEMBER_OR_BAD_SHA")
            info = z.getinfo(e["path"])
            if info.file_size != e["size"] or info.file_size > MAX_MEMBER_BYTES:
                raise MigrationError("BUNDLE_MEMBER_SIZE_MISMATCH")
            total += info.file_size
            if total > MAX_TOTAL_UNPACKED:
                raise MigrationError("BUNDLE_TOO_LARGE_UNPACKED")
            if digest(z.read(info)) != e["sha256"]:
                raise MigrationError("BUNDLE_MEMBER_SHA_MISMATCH")
        return {"status": "KEYLESS_BUNDLE_VERIFIED", "packets": sorted(approved_ids), "members": len(entries),
                "partial": rec.get("is_partial", True), "pending_count": len(rec.get("pending", []))}


def stage_bundle(bundle: Path, expected_sha: str, registry: list[dict], stage_root: Path) -> dict:
    verdict = verify_bundle(bundle, expected_sha, registry)
    if stage_root.is_symlink():
        raise MigrationError("STAGE_ROOT_IS_SYMLINK")
    stage_root.mkdir(parents=True, exist_ok=True)
    target = stage_root / ("batch_" + expected_sha[:16])
    if target.exists():
        raise MigrationError("STAGE_ALREADY_EXISTS_NO_OVERWRITE")
    tmp = Path(tempfile.mkdtemp(dir=stage_root, prefix=".incoming_"))
    try:
        # Read only exact receipt-listed paths. No ZIP extractall(), no arbitrary overwrite.
        if sha_file(bundle) != expected_sha:
            raise MigrationError("BUNDLE_CHANGED_BEFORE_STAGE")
        with zipfile.ZipFile(bundle, "r", allowZip64=False) as z:
            receipt = json.loads(z.read(RECEIPT_NAME))
            for item in receipt["members"]:
                rel = PurePosixPath(item["path"])
                check_member_name(item["path"])
                dest = tmp.joinpath(*rel.parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    raise MigrationError("STAGE_DUPLICATE_FILE")
                data = z.read(item["path"])
                if digest(data) != item["sha256"]:
                    raise MigrationError("STAGE_MEMBER_SHA_CHANGED")
                with dest.open("xb") as f:
                    f.write(data)
            (tmp / RECEIPT_NAME).write_bytes(json_bytes(receipt))
        # Do not modify live game source. Parent target precondition enforced above.
        if target.exists():
            raise MigrationError("STAGE_RACE_TARGET_EXISTS")
        tmp.rename(target)
        verdict["stage"] = str(target)
        return verdict
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def cli(argv=None) -> int:
    ap = argparse.ArgumentParser(description="P0-D OWNER-local keyless package migration (never decrypts nor uploads)")
    ap.add_argument("command", choices=["status", "pack", "verify"])
    ap.add_argument("--registry", required=True, type=Path)
    ap.add_argument("--inbox", type=Path, help="Fixed owner-local folder of original <packet_id>.zip files")
    ap.add_argument("--output", type=Path, help="Owner-local output ZIP (no overwrite)")
    ap.add_argument("--bundle", type=Path, help="Keyless ZIP to verify")
    ap.add_argument("--sha256", help="Expected keyless bundle SHA256 (provided out-of-band / public-safe manifest)")
    ap.add_argument("--stage", type=Path, help="Stage verified data into a NEW isolated subfolder (never game source)")
    ap.add_argument("--strict-all", action="store_true", help="Fail if any registered original is not present/approved")
    args = ap.parse_args(argv)
    try:
        ps = read_registry(args.registry)
        if args.command in ("status", "pack") and not args.inbox:
            raise MigrationError("INBOX_REQUIRED")
        if args.command == "status":
            result = status_report(ps, args.inbox, deep=True)
        elif args.command == "pack":
            if not args.output:
                raise MigrationError("OUTPUT_REQUIRED")
            result = package_originals(ps, args.inbox, args.output, args.strict_all)
        else:
            if not args.bundle or not args.sha256:
                raise MigrationError("BUNDLE_AND_SHA_REQUIRED")
            result = stage_bundle(args.bundle, args.sha256, ps, args.stage) if args.stage else verify_bundle(args.bundle, args.sha256, ps)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (MigrationError, OSError, ValueError, KeyError, zipfile.BadZipFile) as e:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(cli())