#!/usr/bin/env python3
"""Offline source ZIP locator for legacy TRAP RAIDERS progression and meteor packets.

Independent of the D14/D16 locator and the 21-pack Windows intake tool.
This NEVER decrypts, guesses keys, edits source, accesses Roblox Studio,
or scans outside an owner-specified folder.
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
import zipfile

PACKETS = {
    "v42-prototype": {
        "file": "TRAP_RAIDERS_v42_chat_lead_handoff.zip",
        "bytes": 11142,
        "sha256": "aac7efd9e2cd46ca0f2683b9f4f54ca40480aa00bebd1c4b0d72d6fd01ea1173",
        "lineage": "progression", "priority": "superseded",
    },
    "v42.1-progress": {
        "file": "TRAP_RAIDERS_v42_1_chat_lead_implementation.zip",
        "bytes": 37764,
        "sha256": "60b5c43d949064ce36da87b7c9c2eb2a6e0aa27064f33008d54f8509c8bd4364",
        "lineage": "progression", "priority": "superseded_by_v42.2",
    },
    "v42.2-progress-ui": {
        "file": "TRAP_RAIDERS_v42_2.zip", "bytes": 43777,
        "sha256": "8b9fe213c5ef90d8d0ce47099df2f33af0472488848200944d7164ca416bb44f",
        "lineage": "progression", "priority": "latest_archive_reference",
    },
    "v43b-meteor": {
        "file": "TRAP_RAIDERS_v43B_ChatLead.zip", "bytes": 10963,
        "sha256": "78986ca4c85494cd99417ef2bcdbcd7d9cf294c910fcaffb00fb8dfc35bc2723",
        "lineage": "meteor", "priority": "event_candidate_single_chooser_only",
    },
}
MAX_ZIP_BYTES = 25_000_000
MAX_FILE_BYTES = 2_000_000
MAX_UNCOMPRESSED = 10_000_000
MAX_MEMBERS = 250
ALLOWED_SUFFIX = {".luau", ".lua", ".py", ".json", ".md", ".txt", ".csv", ".yaml", ".yml", ".toml"}


class Rejected(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 260:
        raise Rejected("invalid path")
    if name.startswith("/") or "\\" in name or ":" in name or "\x00" in name or name.endswith("/"):
        raise Rejected("absolute, windows or noncanonical path")
    segs = PurePosixPath(name).parts
    if not segs or any(x in ("", ".", "..") or x.startswith(".") for x in segs):
        raise Rejected("hidden/traversal path")
    if "/".join(segs) != name or PurePosixPath(name).suffix.lower() not in ALLOWED_SUFFIX:
        raise Rejected("non-source or noncanonical path")
    return name


def inspect_zip(archive: Path, packet_id: str, overrides: dict | None = None) -> dict[str, bytes]:
    index = PACKETS if overrides is None else overrides
    info = index.get(packet_id)
    if info is None:
        raise Rejected("packet not in pinned legacy catalog")
    if archive.is_symlink() or not archive.is_file():
        raise Rejected("archive missing or symlink")
    if archive.name != info["file"]:
        raise Rejected("wrong original filename")
    size = archive.stat().st_size
    if size != info["bytes"] or size > MAX_ZIP_BYTES:
        raise Rejected("original archive byte size mismatch")
    if sha(archive.read_bytes()) != info["sha256"]:
        raise Rejected("original zip SHA-256 mismatch")
    files = {}
    lower_paths = set()
    total = 0
    try:
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            if len(members) < 2 or len(members) > MAX_MEMBERS:
                raise Rejected("archive member count unexpected")
            for m in members:
                if m.is_dir():
                    continue
                name = canonical(m.filename)
                if name.casefold() in lower_paths:
                    raise Rejected("duplicate/case-colliding member")
                lower_paths.add(name.casefold())
                if m.flag_bits & 1:
                    raise Rejected("encrypted ZIP member is not keyless")
                if stat.S_IFMT(m.external_attr >> 16) == stat.S_IFLNK:
                    raise Rejected("symlink ZIP member")
                if m.file_size > MAX_FILE_BYTES:
                    raise Rejected("oversize source member")
                total += m.file_size
                if total > MAX_UNCOMPRESSED:
                    raise Rejected("uncompressed size cap exceeded")
                data = z.read(m)
                if len(data) != m.file_size:
                    raise Rejected("decompressed size mismatch")
                try:
                    data.decode("utf-8", errors="strict")
                except UnicodeDecodeError as err:
                    raise Rejected("binary/non-UTF8 member rejected") from err
                files[name] = data
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError) as err:
        raise Rejected("corrupt/inaccessible ZIP") from err
    if not files:
        raise Rejected("no source files")
    return files


def scan(folder: Path) -> list[dict]:
    if not folder.is_dir() or folder.is_symlink():
        raise Rejected("scan folder missing or symlink")
    answer = []
    for k, v in PACKETS.items():
        p = folder / v["file"]
        row = {"packet_id": k, "filename": v["file"], "lineage": v["lineage"],
               "priority": v["priority"], "expected_sha256": v["sha256"]}
        if not p.exists():
            row["state"] = "MISSING_ORIGINAL"
        else:
            try:
                row["source_count"] = len(inspect_zip(p, k))
                row["state"] = "ORIGINAL_ZIP_SHA_VERIFIED_NOT_GITHUB_SOURCE"
            except Rejected as err:
                row["state"] = "SOURCE_REJECTED"
                row["reason"] = str(err)
        answer.append(row)
    return answer


def stage(archive: Path, packet_id: str, output: Path) -> dict:
    files = inspect_zip(archive, packet_id)
    if output.exists() or output.is_symlink():
        raise Rejected("output must not already exist")
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise Rejected("existing non-symlink output parent required")
    output.mkdir(mode=0o700)
    for name, data in sorted(files.items()):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as f:
            f.write(data)
    return {"packet_id": packet_id, "source_count": len(files),
            "staging": "ORIGINAL_ZIP_STAGED_NOT_GITHUB_DELIVERED_NOT_STUDIO",
            "source_shas": {name: sha(b) for name, b in sorted(files.items())}}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("scan", help="check only four known names in one selected folder")
    s.add_argument("--folder", type=Path, required=True)
    v = sub.add_parser("verify", help="check expected filename,size,SHA + unencrypted source archive")
    v.add_argument("--zip", type=Path, required=True)
    v.add_argument("--packet-id", choices=sorted(PACKETS), required=True)
    t = sub.add_parser("stage", help="stage to a NEW folder only; never auto-merge")
    t.add_argument("--zip", type=Path, required=True)
    t.add_argument("--packet-id", choices=sorted(PACKETS), required=True)
    t.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        if args.command == "scan":
            obj = scan(args.folder)
        elif args.command == "verify":
            content = inspect_zip(args.zip, args.packet_id)
            obj = {"packet_id": args.packet_id, "source_count": len(content),
                   "state": "ORIGINAL_ZIP_SHA_VERIFIED_NOT_GITHUB_SOURCE"}
        else:
            obj = stage(args.zip, args.packet_id, args.output)
        print(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (Rejected, OSError) as err:
        print("KEYLESS_SOURCE_BLOCKED: " + str(err), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
