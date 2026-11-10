#!/usr/bin/env python3
"""P0-D public-source handoff v1: deterministic, source-only manifest guard.

Offline integrity + obvious secret-pattern guard. Not a malware scanner, authorizer,
or Roblox Studio QA certificate. Python standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

FORMAT = "P0D_PUBLIC_SOURCE_V1"
GAME = "TRAP_RAIDERS"
WORK = "p0d-siege-v19"
MANIFEST = "BUILD_MANIFEST.json"
MAX_FILES = 250
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".luau", ".lua", ".py", ".md", ".json", ".txt", ".csv", ".toml", ".yml", ".yaml"}
HEX_SHA = re.compile(r"^[a-f0-9]{64}$")
PACKET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{4,100}$")
HIGH_CONFIDENCE_SECRETS = [
    ("private-key-block", re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("github-personal-token", re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("github-fine-grained-token", re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("openai-like-api-token", re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b")),
    ("aws-access-key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
]


class PackError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 260:
        raise PackError("invalid path")
    if "\\" in name or "\x00" in name or ":" in name or name.startswith("/"):
        raise PackError("unsafe file path")
    parts = PurePosixPath(name).parts
    if any(x in (".", "..", "") or x.startswith(".") for x in parts):
        raise PackError("hidden/traversal path")
    if name != "/".join(parts) or name.endswith("/"):
        raise PackError("noncanonical path")
    if PurePosixPath(name).suffix.lower() not in ALLOWED_SUFFIXES:
        raise PackError("non-source extension")
    if parts[-1].lower() in {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}:
        raise PackError("credential-like filename")
    return name


def gather(root: Path) -> list[dict]:
    if root.is_symlink() or not root.is_dir():
        raise PackError("source directory absent or symlink")
    entries = []
    total = 0
    names = set()
    for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
        for d in dirs:
            path = Path(base) / d
            if path.is_symlink():
                raise PackError("directory symlink rejected")
            rel = path.relative_to(root).as_posix()
            safe_relative(rel + "/__directory__.md")
        for f in files:
            path = Path(base) / f
            if path.is_symlink() or not path.is_file():
                raise PackError("nonregular/symlink file rejected")
            rel = path.relative_to(root).as_posix()
            if rel == MANIFEST:
                continue
            safe_relative(rel)
            lower = rel.casefold()
            if lower in names:
                raise PackError("case-insensitive path collision")
            names.add(lower)
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise PackError("file exceeds size cap")
            total += size
            if total > MAX_TOTAL_BYTES:
                raise PackError("total payload exceeds cap")
            content = path.read_bytes()
            try:
                content.decode("utf-8", errors="strict")
            except UnicodeDecodeError as e:
                raise PackError("non-UTF8 or binary file rejected") from e
            for label, pattern in HIGH_CONFIDENCE_SECRETS:
                if pattern.search(content):
                    raise PackError(f"secret pattern {label} detected in {rel}")
            entries.append({"path": rel, "size": len(content), "sha256": digest(content)})
            if len(entries) > MAX_FILES:
                raise PackError("file count cap")
    if not entries:
        raise PackError("empty source pack")
    return sorted(entries, key=lambda x: x["path"])


def build(root: Path, packet_id: str) -> dict:
    if not isinstance(packet_id, str) or not PACKET.fullmatch(packet_id):
        raise PackError("invalid packet ID")
    return {"format": FORMAT, "game_id": GAME, "work_id": WORK,
            "packet_id": packet_id, "public_source_allowed": True,
            "files": gather(root)}


def serialized(manifest: dict) -> bytes:
    return (json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def verify(root: Path, expected_packet: str | None = None) -> dict:
    mpath = root / MANIFEST
    if mpath.is_symlink() or not mpath.is_file() or mpath.stat().st_size > 300_000:
        raise PackError("missing/unsafe manifest")
    raw = mpath.read_bytes()
    try:
        doc = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(PackError("nonfinite JSON")),
                         object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise PackError("malformed manifest") from e
    if not isinstance(doc, dict) or set(doc) != {"format", "game_id", "work_id", "packet_id", "public_source_allowed", "files"}:
        raise PackError("manifest schema mismatch")
    if doc["format"] != FORMAT or doc["game_id"] != GAME or doc["work_id"] != WORK or doc["public_source_allowed"] is not True:
        raise PackError("identity/public scope mismatch")
    if not isinstance(doc["packet_id"], str) or not PACKET.fullmatch(doc["packet_id"]):
        raise PackError("packet ID invalid")
    if expected_packet is not None and doc["packet_id"] != expected_packet:
        raise PackError("packet ID differs from expected")
    if not isinstance(doc["files"], list):
        raise PackError("files is not array")
    for item in doc["files"]:
        if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
            raise PackError("file entry schema invalid")
        safe_relative(item["path"])
        if type(item["size"]) is not int or item["size"] < 0 or item["size"] > MAX_FILE_BYTES:
            raise PackError("invalid file size")
        if not isinstance(item["sha256"], str) or not HEX_SHA.fullmatch(item["sha256"]):
            raise PackError("invalid file hash")
    actual = build(root, doc["packet_id"])
    if serialized(doc) != raw:
        raise PackError("noncanonical manifest encoding")
    if actual != doc:
        raise PackError("manifest missing, extra, or mismatched content")
    return {"status": "PUBLIC_SOURCE_SHA_VERIFIED_NOT_STUDIO", "packet_id": doc["packet_id"],
            "file_count": len(doc["files"]), "manifest_sha256": digest(raw)}


def no_duplicates(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PackError("duplicate JSON key")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write canonical manifest after secret and path scan")
    b.add_argument("--root", type=Path, required=True)
    b.add_argument("--packet-id", required=True)
    v = sub.add_parser("verify", help="verify all files against manifest; no execution")
    v.add_argument("--root", type=Path, required=True)
    v.add_argument("--packet-id", required=True)
    args = p.parse_args(argv)
    try:
        if args.cmd == "build":
            doc = build(args.root, args.packet_id)
            dest = args.root / MANIFEST
            if dest.is_symlink():
                raise PackError("manifest symlink forbidden")
            dest.write_bytes(serialized(doc))
            print(json.dumps(verify(args.root, args.packet_id), ensure_ascii=False))
        else:
            print(json.dumps(verify(args.root, args.packet_id), ensure_ascii=False))
    except (PackError, OSError) as e:
        print(f"PUBLIC_HANDOFF_BLOCKED: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
